from __future__ import annotations

import re
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Any

from .client import (
    ComfyExecutionHistory,
    ComfyHistorySnapshot,
    ComfyPromptSubmission,
    ComfyQueueSnapshot,
    ComfyUIClient,
)
from .errors import ComfyProtocolError
from .events import ComfyProtocolEvent

_LOGICAL_PROMPT_RE = re.compile(r"^kp_([0-9a-f]{32})$")


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
    The accepted ComfyUI transport, endpoint boundary, budgets and route set are reused.
    """

    def submit_prompt(
        self,
        prompt: Mapping[str, Any],
        *,
        prompt_id: str,
        client_id: str,
        correlation: Mapping[str, str],
    ) -> ComfyPromptSubmission:
        wire_id = logical_prompt_id_to_wire(prompt_id)
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
