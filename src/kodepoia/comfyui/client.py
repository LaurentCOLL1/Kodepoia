from __future__ import annotations

import re
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from .boundary import ComfyEndpoint
from .contracts import ComfyCapabilityState, ComfyOutputReference, ComfyRunState, ComfyTransportLimits
from .errors import ComfyProtocolError, ComfyUnavailableError
from .events import ComfyEventSequence, ComfyProtocolEvent, parse_event_frame
from .serialization import canonical_sha256
from .transport import _FixedHTTPTransport, _WebSocketClosed, _WebSocketConnection

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_PROMPT_ID_MAX = 128
_CLIENT_ID_MAX = 128
_MAX_QUEUE_ITEMS = 100000
_MAX_HISTORY_OUTPUT_NODES = 10000
_ALLOWED_OUTPUT_STORAGE_TYPES = frozenset({"output", "temp"})


@dataclass(frozen=True, slots=True)
class ComfySystemSnapshot:
    comfyui_version: str | None
    python_version: str | None
    device_count: int
    digest_sha256: str


@dataclass(frozen=True, slots=True)
class ComfyQueueSnapshot:
    running_prompt_ids: tuple[str, ...]
    pending_prompt_ids: tuple[str, ...]
    queue_remaining: int | None
    digest_sha256: str


@dataclass(frozen=True, slots=True)
class ComfyHistorySnapshot:
    prompt_id: str
    present: bool
    state: ComfyRunState
    output_node_ids: tuple[str, ...]
    digest_sha256: str


@dataclass(frozen=True, slots=True)
class ComfyProbeSnapshot:
    endpoint: str
    system: ComfyCapabilityState
    features: ComfyCapabilityState
    prompt_metadata: ComfyCapabilityState
    queue: ComfyCapabilityState
    history: ComfyCapabilityState
    system_digest_sha256: str
    feature_digest_sha256: str
    queue_digest_sha256: str
    history_digest_sha256: str

    def canonical(self) -> dict[str, object]:
        return {
            "endpoint": self.endpoint,
            "system": self.system.value,
            "features": self.features.value,
            "prompt_metadata": self.prompt_metadata.value,
            "queue": self.queue.value,
            "history": self.history.value,
            "system_digest_sha256": self.system_digest_sha256,
            "feature_digest_sha256": self.feature_digest_sha256,
            "queue_digest_sha256": self.queue_digest_sha256,
            "history_digest_sha256": self.history_digest_sha256,
        }


class ComfyUIClient:
    """Fixed local ComfyUI protocol client. No arbitrary route/method surface is exposed."""

    def __init__(
        self,
        endpoint: ComfyEndpoint | str = "http://127.0.0.1:8188",
        *,
        limits: ComfyTransportLimits | None = None,
    ) -> None:
        self.endpoint = endpoint if isinstance(endpoint, ComfyEndpoint) else ComfyEndpoint.parse(endpoint)
        self.limits = limits or ComfyTransportLimits()
        self._http = _FixedHTTPTransport(self.endpoint, self.limits)

    def system_stats(self) -> ComfySystemSnapshot:
        data = self._http.get_json("/system_stats")
        system = data.get("system", {})
        devices = data.get("devices", [])
        if not isinstance(system, dict) or not isinstance(devices, list):
            raise ComfyProtocolError("ComfyUI system_stats shape is invalid")
        if len(devices) > 1024:
            raise ComfyProtocolError("ComfyUI system_stats device list is implausibly large")
        comfyui_version = _optional_bounded_string(system.get("comfyui_version"), "comfyui_version", 256)
        python_version = _optional_bounded_string(system.get("python_version"), "python_version", 1024)
        return ComfySystemSnapshot(
            comfyui_version=comfyui_version,
            python_version=python_version,
            device_count=len(devices),
            digest_sha256=canonical_sha256(data),
        )

    def features(self) -> dict[str, Any]:
        return self._http.get_json("/features")

    def prompt_metadata(self) -> dict[str, Any]:
        return self._http.get_json("/prompt")

    def queue(self) -> ComfyQueueSnapshot:
        queue_data = self._http.get_json("/queue")
        prompt_data = self._http.get_json("/prompt")
        running = _queue_prompt_ids(queue_data.get("queue_running"), field_name="queue_running")
        pending = _queue_prompt_ids(queue_data.get("queue_pending"), field_name="queue_pending")
        queue_remaining = _queue_remaining(prompt_data)
        return ComfyQueueSnapshot(
            running_prompt_ids=running,
            pending_prompt_ids=pending,
            queue_remaining=queue_remaining,
            digest_sha256=canonical_sha256({"queue": queue_data, "prompt": prompt_data}),
        )

    def history(self, prompt_id: str) -> ComfyHistorySnapshot:
        normalized_prompt = _bounded_identifier(prompt_id, "prompt_id")
        data = self._http.get_json(f"/history/{normalized_prompt}")
        if normalized_prompt not in data:
            return ComfyHistorySnapshot(
                prompt_id=normalized_prompt,
                present=False,
                state=ComfyRunState.UNKNOWN,
                output_node_ids=(),
                digest_sha256=canonical_sha256(data),
            )
        item = data[normalized_prompt]
        if not isinstance(item, dict):
            raise ComfyProtocolError("ComfyUI history item must be an object")
        state = _history_state(item)
        output_node_ids = _history_output_nodes(item)
        return ComfyHistorySnapshot(
            prompt_id=normalized_prompt,
            present=True,
            state=state,
            output_node_ids=output_node_ids,
            digest_sha256=canonical_sha256(data),
        )

    def history_index(self) -> dict[str, Any]:
        return self._http.get_json("/history")

    def retrieve_output(self, reference: ComfyOutputReference) -> bytes:
        if reference.storage_type not in _ALLOWED_OUTPUT_STORAGE_TYPES:
            raise ComfyProtocolError("R9.2 output retrieval accepts only output/temp storage types")
        return self._http.get_bytes(
            "/view",
            query={
                "filename": reference.server_filename,
                "subfolder": reference.server_subfolder,
                "type": reference.storage_type,
            },
        )

    def reconcile_prompt_state(self, prompt_id: str) -> ComfyRunState:
        normalized_prompt = _bounded_identifier(prompt_id, "prompt_id")
        queue = self.queue()
        if normalized_prompt in queue.running_prompt_ids:
            return ComfyRunState.RUNNING
        if normalized_prompt in queue.pending_prompt_ids:
            return ComfyRunState.QUEUED
        history = self.history(normalized_prompt)
        return history.state if history.present else ComfyRunState.UNKNOWN

    def iter_events(
        self,
        client_id: str,
        *,
        expected_prompt_id: str | None = None,
        cancel_event: threading.Event | None = None,
        max_reconnects: int = 2,
        backoff_seconds: tuple[float, ...] = (0.05, 0.2, 0.5),
    ) -> Iterator[ComfyProtocolEvent]:
        normalized_client = _bounded_identifier(client_id, "client_id", maximum=_CLIENT_ID_MAX)
        tracked_prompt = (
            _bounded_identifier(expected_prompt_id, "expected_prompt_id")
            if expected_prompt_id is not None
            else None
        )
        if isinstance(max_reconnects, bool) or not isinstance(max_reconnects, int) or not 0 <= max_reconnects <= 8:
            raise ValueError("max_reconnects must be an integer between 0 and 8")
        if not backoff_seconds or len(backoff_seconds) > 8:
            raise ValueError("backoff_seconds must contain between 1 and 8 entries")
        if any(delay < 0 or delay > 30 for delay in backoff_seconds):
            raise ValueError("backoff_seconds entries must be between 0 and 30 seconds")

        sequence = ComfyEventSequence(tracked_prompt) if tracked_prompt is not None else None
        started = time.monotonic()
        reconnects = 0
        while True:
            if _cancelled(cancel_event):
                return
            if time.monotonic() - started >= self.limits.total_timeout_seconds:
                raise ComfyUnavailableError("ComfyUI WebSocket operation exceeded the total time budget")
            connection: _WebSocketConnection | None = None
            try:
                connection = _WebSocketConnection.connect(
                    self.endpoint,
                    self.limits,
                    client_id=normalized_client,
                )
                while True:
                    if _cancelled(cancel_event):
                        return
                    message = connection.recv_message()
                    if isinstance(message, bytes):
                        # Binary preview frames are bounded by the transport but are not R9.2 protocol events.
                        continue
                    event = parse_event_frame(message, max_bytes=self.limits.max_websocket_frame_bytes)
                    if sequence is not None and event.prompt_id is not None:
                        sequence.observe(event)
                    yield event
            except (_WebSocketClosed, ComfyUnavailableError):
                if reconnects >= max_reconnects:
                    raise
                reconnects += 1
                delay = backoff_seconds[min(reconnects - 1, len(backoff_seconds) - 1)]
                if not _wait_or_cancel(cancel_event, delay):
                    return
            finally:
                if connection is not None:
                    connection.close()

    def probe(self) -> ComfyProbeSnapshot:
        system = self.system_stats()
        features = self.features()
        prompt = self.prompt_metadata()
        queue = self.queue()
        history = self.history_index()
        return ComfyProbeSnapshot(
            endpoint=self.endpoint.origin,
            system=ComfyCapabilityState.CURRENT,
            features=ComfyCapabilityState.CURRENT,
            prompt_metadata=ComfyCapabilityState.CURRENT,
            queue=ComfyCapabilityState.CURRENT,
            history=ComfyCapabilityState.CURRENT,
            system_digest_sha256=system.digest_sha256,
            feature_digest_sha256=canonical_sha256(features),
            queue_digest_sha256=queue.digest_sha256,
            history_digest_sha256=canonical_sha256(history),
        )


def _bounded_identifier(value: str, field_name: str, *, maximum: int = _PROMPT_ID_MAX) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum or _CONTROL_RE.search(value):
        raise ValueError(f"{field_name} must be a non-empty bounded string without controls")
    return value


def _optional_bounded_string(value: Any, field_name: str, maximum: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > maximum or _CONTROL_RE.search(value):
        raise ComfyProtocolError(f"{field_name} must be a bounded string when present")
    return value


def _queue_prompt_ids(raw: Any, *, field_name: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ComfyProtocolError(f"{field_name} must be an array")
    if len(raw) > _MAX_QUEUE_ITEMS:
        raise ComfyProtocolError(f"{field_name} exceeds the accepted queue-item bound")
    prompt_ids: list[str] = []
    for entry in raw:
        if not isinstance(entry, (list, tuple)) or len(entry) < 2:
            raise ComfyProtocolError(f"{field_name} contains an invalid queue entry")
        prompt_value = entry[1]
        if not isinstance(prompt_value, str):
            raise ComfyProtocolError(f"{field_name} prompt_id must be a string")
        prompt_ids.append(_bounded_identifier(prompt_value, f"{field_name} prompt_id"))
    return tuple(prompt_ids)


def _queue_remaining(prompt_data: dict[str, Any]) -> int | None:
    exec_info = prompt_data.get("exec_info")
    if exec_info is None:
        return None
    if not isinstance(exec_info, dict):
        raise ComfyProtocolError("ComfyUI prompt exec_info must be an object")
    value = exec_info.get("queue_remaining")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ComfyProtocolError("ComfyUI queue_remaining must be a non-negative integer")
    return value


def _history_state(item: dict[str, Any]) -> ComfyRunState:
    status = item.get("status")
    if status is None:
        return ComfyRunState.UNKNOWN
    if not isinstance(status, dict):
        raise ComfyProtocolError("ComfyUI history status must be an object")
    status_string = status.get("status_str")
    completed = status.get("completed")
    if status_string is not None and not isinstance(status_string, str):
        raise ComfyProtocolError("ComfyUI history status_str must be a string")
    if completed is not None and not isinstance(completed, bool):
        raise ComfyProtocolError("ComfyUI history completed must be boolean")
    normalized = status_string.lower() if isinstance(status_string, str) else ""
    if completed is True and normalized in {"success", "completed"}:
        return ComfyRunState.SUCCEEDED
    if normalized in {"error", "failed"}:
        return ComfyRunState.FAILED
    if normalized in {"interrupted", "cancelled", "canceled"}:
        return ComfyRunState.CANCELLED
    if completed is True:
        return ComfyRunState.UNKNOWN
    return ComfyRunState.RUNNING if completed is False else ComfyRunState.UNKNOWN


def _history_output_nodes(item: dict[str, Any]) -> tuple[str, ...]:
    outputs = item.get("outputs", {})
    if not isinstance(outputs, dict):
        raise ComfyProtocolError("ComfyUI history outputs must be an object")
    if len(outputs) > _MAX_HISTORY_OUTPUT_NODES:
        raise ComfyProtocolError("ComfyUI history output-node count exceeds the accepted bound")
    result: list[str] = []
    for node_id in outputs:
        if not isinstance(node_id, str):
            raise ComfyProtocolError("ComfyUI history output node IDs must be strings")
        result.append(_bounded_identifier(node_id, "history output node_id"))
    return tuple(sorted(result))


def _cancelled(cancel_event: threading.Event | None) -> bool:
    return cancel_event is not None and cancel_event.is_set()


def _wait_or_cancel(cancel_event: threading.Event | None, delay: float) -> bool:
    if delay <= 0:
        return not _cancelled(cancel_event)
    if cancel_event is None:
        time.sleep(delay)
        return True
    return not cancel_event.wait(delay)
