from __future__ import annotations

import copy
import re
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .client import (
    ComfyExecutionHistory,
    ComfyHistorySnapshot,
    ComfyPromptSubmission,
    ComfyQueueSnapshot,
    ComfyUIClient,
)
from .errors import ComfyProtocolError
from .events import ComfyProtocolEvent
from .serialization import canonical_sha256

_LOGICAL_PROMPT_RE = re.compile(r"^kp_([0-9a-f]{32})$")
_MAX_DIFF_NODE_IDS = 16


def logical_prompt_id_to_wire(prompt_id: str) -> str:
    """Map frozen R9.5 logical prompt identity onto current ComfyUI's UUID wire contract."""
    if not isinstance(prompt_id, str):
        raise TypeError("prompt_id must be a string")
    match = _LOGICAL_PROMPT_RE.fullmatch(prompt_id)
    if match is None:
        raise ComfyProtocolError("R9.8 wire adapter requires a frozen R9.5 kp_<32hex> prompt_id")
    return str(uuid.UUID(hex=match.group(1)))


def wire_prompt_id_to_logical(prompt_id: str) -> str:
    """Map a canonical UUID returned by ComfyUI back to frozen R9.5 logical identity."""
    if not isinstance(prompt_id, str):
        raise TypeError("prompt_id must be a string")
    logical_match = _LOGICAL_PROMPT_RE.fullmatch(prompt_id)
    if logical_match is not None:
        # Legacy ComfyUI accepted the logical token directly; preserve compatibility.
        return prompt_id
    try:
        parsed = uuid.UUID(prompt_id)
    except (ValueError, AttributeError) as exc:
        raise ComfyProtocolError("ComfyUI returned a prompt_id outside the accepted logical/UUID forms") from exc
    if str(parsed) != prompt_id.lower():
        raise ComfyProtocolError("ComfyUI returned a non-canonical UUID prompt_id")
    return f"kp_{parsed.hex}"


class R98WireComfyUIClient(ComfyUIClient):
    """R9.8 compatibility facade preserving R9.5 logical IDs while using UUIDs on the wire.

    Current ComfyUI validates caller-provided prompt_id as a canonical UUID. R9.5
    intentionally froze logical IDs as kp_<32hex>. This facade changes only the wire
    representation and maps queue/history evidence back before it reaches manifests.

    Current ComfyUI also runs on-prompt handlers and node replacement processing before
    the queued prompt is persisted into history. The R9.5 prompt digest remains strict:
    this facade accepts only history changes that are provably limited to per-node
    non-executable `_meta` dictionaries. Any class, input, node-set or other structural
    change remains fail-closed with a bounded value-free diagnostic.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._r98_submitted_prompts: dict[str, dict[str, Any]] = {}

    def submit_prompt(
        self,
        prompt: Mapping[str, Any],
        *,
        prompt_id: str,
        client_id: str,
        correlation: Mapping[str, str],
    ) -> ComfyPromptSubmission:
        wire_id = logical_prompt_id_to_wire(prompt_id)
        expected_prompt = _clone_prompt(prompt)
        self._r98_submitted_prompts[prompt_id] = expected_prompt
        submitted = super().submit_prompt(
            prompt,
            prompt_id=wire_id,
            client_id=client_id,
            correlation=correlation,
        )
        if wire_prompt_id_to_logical(submitted.prompt_id) != prompt_id:
            raise ComfyProtocolError("ComfyUI wire prompt_id does not map back to the logical run prompt_id")
        return replace(submitted, prompt_id=prompt_id)

    def queue(self) -> ComfyQueueSnapshot:
        snapshot = super().queue()
        return replace(
            snapshot,
            running_prompt_ids=tuple(wire_prompt_id_to_logical(item) for item in snapshot.running_prompt_ids),
            pending_prompt_ids=tuple(wire_prompt_id_to_logical(item) for item in snapshot.pending_prompt_ids),
        )

    def history(self, prompt_id: str) -> ComfyHistorySnapshot:
        wire_id = logical_prompt_id_to_wire(prompt_id)
        snapshot = super().history(wire_id)
        return replace(snapshot, prompt_id=prompt_id)

    def execution_history(self, prompt_id: str) -> ComfyExecutionHistory:
        wire_id = logical_prompt_id_to_wire(prompt_id)
        history = super().execution_history(wire_id)
        if history.present:
            expected_prompt = self._r98_submitted_prompts.get(prompt_id)
            if expected_prompt is not None:
                stored_prompt = self._stored_history_prompt(wire_id)
                expected_digest = canonical_sha256(expected_prompt)
                observed_digest = canonical_sha256(stored_prompt)
                if observed_digest != expected_digest:
                    expected_semantic = _strip_metadata_only(expected_prompt)
                    stored_semantic = _strip_metadata_only(stored_prompt)
                    if canonical_sha256(stored_semantic) != canonical_sha256(expected_semantic):
                        raise ComfyProtocolError(
                            "ComfyUI stored prompt differs structurally from the submitted R9.4 instance: "
                            + _prompt_diff_summary(expected_semantic, stored_semantic)
                        )
                    # Preserve frozen R9.5 logical prompt identity when ComfyUI changed only
                    # non-executable node metadata. The raw history digest remains separately
                    # bound by history.digest_sha256.
                    history = replace(history, prompt_digest_sha256=expected_digest)
        references = tuple(replace(item, prompt_id=prompt_id) for item in history.output_references)
        return replace(history, prompt_id=prompt_id, output_references=references)

    def iter_events(
        self,
        client_id: str,
        *,
        expected_prompt_id: str | None = None,
        cancel_event: Any = None,
        max_reconnects: int = 2,
        backoff_seconds: tuple[float, ...] = (0.05, 0.2, 0.5),
    ) -> Iterator[ComfyProtocolEvent]:
        wire_id = logical_prompt_id_to_wire(expected_prompt_id) if expected_prompt_id is not None else None
        for event in super().iter_events(
            client_id,
            expected_prompt_id=wire_id,
            cancel_event=cancel_event,
            max_reconnects=max_reconnects,
            backoff_seconds=backoff_seconds,
        ):
            if event.prompt_id is None:
                yield event
                continue
            logical_id = wire_prompt_id_to_logical(event.prompt_id)
            yield replace(event, prompt_id=logical_id)

    def _stored_history_prompt(self, wire_id: str) -> dict[str, Any]:
        data = self._http.get_json(f"/history/{quote(wire_id, safe='')}")
        item = data.get(wire_id)
        if not isinstance(item, dict):
            raise ComfyProtocolError("ComfyUI history item disappeared during R9.8 prompt reconciliation")
        raw = item.get("prompt")
        if not isinstance(raw, (list, tuple)) or len(raw) < 4:
            raise ComfyProtocolError("ComfyUI history prompt tuple is missing canonical prompt evidence")
        stored_id = raw[1]
        stored_prompt = raw[2]
        if stored_id != wire_id or not isinstance(stored_prompt, dict):
            raise ComfyProtocolError("ComfyUI history prompt evidence changed during R9.8 reconciliation")
        return copy.deepcopy(stored_prompt)


@contextmanager
def r98_wire_client_scope() -> Iterator[None]:
    """Inject the wire adapter only into the authoritative R9.8 local gate, then restore it."""
    from . import r9_8_acceptance

    previous = r9_8_acceptance.ComfyUIClient
    r9_8_acceptance.ComfyUIClient = R98WireComfyUIClient
    try:
        yield
    finally:
        r9_8_acceptance.ComfyUIClient = previous


def run_r98_wire_compatible_acceptance(workspace: Path, request: Any) -> Any:
    """Run the local gate with scoped UUID-wire compatibility and no persistent monkeypatch."""
    from .r9_8_acceptance import R98LocalAcceptance

    with r98_wire_client_scope():
        return R98LocalAcceptance(workspace).run(request)


def _clone_prompt(prompt: Mapping[str, Any]) -> dict[str, Any]:
    cloned = copy.deepcopy(dict(prompt))
    if not cloned or not all(isinstance(key, str) for key in cloned):
        raise ComfyProtocolError("R9.8 submitted prompt must be a non-empty string-keyed object")
    return cloned


def _strip_metadata_only(prompt: Mapping[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for node_id, raw_node in prompt.items():
        if not isinstance(node_id, str) or not isinstance(raw_node, Mapping):
            raise ComfyProtocolError("R9.8 prompt reconciliation requires string-keyed node objects")
        unknown = set(raw_node) - {"class_type", "inputs", "_meta"}
        if unknown:
            raise ComfyProtocolError(
                "ComfyUI stored prompt contains unsupported node fields during R9.8 reconciliation"
            )
        class_type = raw_node.get("class_type")
        inputs = raw_node.get("inputs")
        if not isinstance(class_type, str) or not isinstance(inputs, Mapping):
            raise ComfyProtocolError("R9.8 prompt reconciliation requires class_type and inputs")
        metadata = raw_node.get("_meta")
        if metadata is not None and not isinstance(metadata, Mapping):
            raise ComfyProtocolError("ComfyUI node _meta must be an object when present")
        normalized[node_id] = {
            "class_type": class_type,
            "inputs": copy.deepcopy(dict(inputs)),
        }
    return normalized


def _prompt_diff_summary(expected: Mapping[str, Any], observed: Mapping[str, Any]) -> str:
    expected_ids = set(expected)
    observed_ids = set(observed)
    shared = sorted(expected_ids & observed_ids)
    class_changed: list[str] = []
    input_keys_changed: list[str] = []
    input_values_changed: list[str] = []
    for node_id in shared:
        expected_node = expected[node_id]
        observed_node = observed[node_id]
        if expected_node.get("class_type") != observed_node.get("class_type"):
            class_changed.append(node_id)
        expected_inputs = expected_node.get("inputs", {})
        observed_inputs = observed_node.get("inputs", {})
        if set(expected_inputs) != set(observed_inputs):
            input_keys_changed.append(node_id)
        elif canonical_sha256(dict(expected_inputs)) != canonical_sha256(dict(observed_inputs)):
            input_values_changed.append(node_id)
    return (
        f"added_nodes={_bounded_ids(observed_ids - expected_ids)}, "
        f"removed_nodes={_bounded_ids(expected_ids - observed_ids)}, "
        f"class_changed={_bounded_ids(class_changed)}, "
        f"input_keys_changed={_bounded_ids(input_keys_changed)}, "
        f"input_values_changed={_bounded_ids(input_values_changed)}"
    )


def _bounded_ids(values: Any) -> list[str]:
    safe = sorted(str(value)[:64] for value in values)
    return safe[:_MAX_DIFF_NODE_IDS]
