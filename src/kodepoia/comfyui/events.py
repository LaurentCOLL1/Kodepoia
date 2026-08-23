from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .contracts import ComfyRunState, can_transition_run_state
from .errors import ComfyProtocolError, ComfyResourceError
from .serialization import canonical_sha256

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_MAX_EVENT_TYPE_LENGTH = 96
_MAX_IDENTIFIER_LENGTH = 128
_MAX_MESSAGE_LENGTH = 4096
_MAX_CACHED_NODES = 10000


class ComfyEventType(StrEnum):
    STATUS = "status"
    EXECUTION_START = "execution_start"
    EXECUTING = "executing"
    PROGRESS = "progress"
    EXECUTED = "executed"
    EXECUTION_ERROR = "execution_error"
    EXECUTION_INTERRUPTED = "execution_interrupted"
    EXECUTION_CACHED = "execution_cached"
    EXECUTION_SUCCESS = "execution_success"
    PROGRESS_STATE = "progress_state"
    PROGRESS_TEXT = "progress_text"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ComfyProtocolEvent:
    event_type: ComfyEventType
    raw_type: str
    prompt_id: str | None
    node_id: str | None
    progress_value: float | None
    progress_max: float | None
    cached_nodes: tuple[str, ...]
    message: str | None
    payload_sha256: str

    @property
    def progress_fraction(self) -> float | None:
        if self.progress_value is None or self.progress_max is None:
            return None
        return self.progress_value / self.progress_max


def _bounded_text(value: Any, *, field_name: str, maximum: int, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ComfyProtocolError(f"{field_name} must be a non-empty bounded string")
    if _CONTROL_RE.search(value):
        raise ComfyProtocolError(f"{field_name} must not contain control characters")
    return value


def _optional_identifier(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ComfyProtocolError(f"{field_name} must be a string/integer identifier or null")
    return _bounded_text(str(value), field_name=field_name, maximum=_MAX_IDENTIFIER_LENGTH)


def _optional_progress(value: Any, maximum: Any) -> tuple[float | None, float | None]:
    if value is None and maximum is None:
        return None, None
    if isinstance(value, bool) or isinstance(maximum, bool):
        raise ComfyProtocolError("progress value/max must be numeric")
    if not isinstance(value, (int, float)) or not isinstance(maximum, (int, float)):
        raise ComfyProtocolError("progress value/max must be numeric")
    value_float = float(value)
    maximum_float = float(maximum)
    if not math.isfinite(value_float) or not math.isfinite(maximum_float):
        raise ComfyProtocolError("progress value/max must be finite")
    if maximum_float <= 0 or value_float < 0 or value_float > maximum_float:
        raise ComfyProtocolError("progress value/max are outside the accepted range")
    return value_float, maximum_float


def _cached_nodes(data: dict[str, Any]) -> tuple[str, ...]:
    raw = data.get("nodes")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ComfyProtocolError("execution_cached nodes must be an array")
    if len(raw) > _MAX_CACHED_NODES:
        raise ComfyResourceError("execution_cached node list exceeds the R9.2 bound")
    result: list[str] = []
    for node in raw:
        identifier = _optional_identifier(node, field_name="cached node id")
        if identifier is None:
            raise ComfyProtocolError("cached node id must not be null")
        result.append(identifier)
    return tuple(result)


def parse_event_frame(frame: str | bytes, *, max_bytes: int) -> ComfyProtocolEvent:
    if isinstance(frame, str):
        encoded = frame.encode("utf-8")
    elif isinstance(frame, bytes):
        encoded = frame
    else:
        raise TypeError("frame must be str or bytes")
    if len(encoded) > max_bytes:
        raise ComfyResourceError("ComfyUI WebSocket message exceeds the accepted byte bound")
    try:
        decoded = json.loads(encoded.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ComfyProtocolError("ComfyUI WebSocket message is not valid UTF-8 JSON") from exc
    if not isinstance(decoded, dict):
        raise ComfyProtocolError("ComfyUI WebSocket event must be a JSON object")

    raw_type = _bounded_text(
        decoded.get("type"),
        field_name="event type",
        maximum=_MAX_EVENT_TYPE_LENGTH,
    )
    assert raw_type is not None
    data = decoded.get("data", {})
    if not isinstance(data, dict):
        raise ComfyProtocolError("ComfyUI WebSocket event data must be an object")

    try:
        event_type = ComfyEventType(raw_type)
    except ValueError:
        event_type = ComfyEventType.UNKNOWN

    prompt_id = _optional_identifier(data.get("prompt_id"), field_name="prompt_id")
    node_id = _optional_identifier(
        data.get("node", data.get("node_id")),
        field_name="node_id",
    )
    progress_value: float | None = None
    progress_max: float | None = None
    if event_type is ComfyEventType.PROGRESS:
        progress_value, progress_max = _optional_progress(data.get("value"), data.get("max"))

    cached_nodes = _cached_nodes(data) if event_type is ComfyEventType.EXECUTION_CACHED else ()
    message_value = data.get("exception_message", data.get("message", data.get("text")))
    message: str | None = None
    if message_value is not None:
        message = _bounded_text(
            message_value,
            field_name="event message",
            maximum=_MAX_MESSAGE_LENGTH,
            allow_none=True,
        )

    return ComfyProtocolEvent(
        event_type=event_type,
        raw_type=raw_type,
        prompt_id=prompt_id,
        node_id=node_id,
        progress_value=progress_value,
        progress_max=progress_max,
        cached_nodes=cached_nodes,
        message=message,
        payload_sha256=canonical_sha256(decoded),
    )


_PROMPT_ACTIVE_EVENTS = frozenset(
    {
        ComfyEventType.EXECUTION_START,
        ComfyEventType.EXECUTING,
        ComfyEventType.PROGRESS,
        ComfyEventType.EXECUTED,
        ComfyEventType.EXECUTION_CACHED,
        ComfyEventType.PROGRESS_STATE,
        ComfyEventType.PROGRESS_TEXT,
    }
)


@dataclass(slots=True)
class ComfyEventSequence:
    """Validate prompt-scoped WS ordering without treating WS as completion authority."""

    prompt_id: str
    state: ComfyRunState = ComfyRunState.UNKNOWN

    def observe(self, event: ComfyProtocolEvent) -> ComfyRunState:
        if event.prompt_id is None:
            return self.state
        if event.prompt_id != self.prompt_id:
            raise ComfyProtocolError("WebSocket event prompt_id does not match the tracked prompt")

        target = self.state
        if event.event_type is ComfyEventType.EXECUTION_START:
            target = ComfyRunState.RUNNING
        elif event.event_type in _PROMPT_ACTIVE_EVENTS:
            target = ComfyRunState.RUNNING
        elif event.event_type is ComfyEventType.EXECUTION_ERROR:
            target = ComfyRunState.FAILED
        elif event.event_type is ComfyEventType.EXECUTION_INTERRUPTED:
            target = ComfyRunState.CANCELLED
        elif event.event_type is ComfyEventType.EXECUTION_SUCCESS:
            target = ComfyRunState.SUCCEEDED

        if target != self.state and not can_transition_run_state(self.state, target):
            raise ComfyProtocolError(
                f"Impossible ComfyUI WebSocket state transition: {self.state.value} -> {target.value}"
            )
        self.state = target
        return self.state
