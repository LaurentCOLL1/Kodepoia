from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .client import ComfyUIClient
from .contracts import ComfyRunState, is_terminal_run_state
from .errors import (
    ComfyGovernanceError,
    ComfyProtocolError,
    ComfySubmissionAmbiguousError,
    ComfyUnavailableError,
)
from .execution import ComfyExecutionBudget, ComfyExecutionService, ComfyRunManifest, ComfyRunStore
from .serialization import canonical_json_bytes, canonical_sha256, make_envelope, parse_envelope

_AUDIT_SCHEMA = "kodepoia.comfy-lifecycle-audit"
_AUDIT_VERSION = 1
_SAFE_RUN_RE = re.compile(r"^run_[0-9a-f]{32}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_MAX_EVENTS = 10000


class ComfyLifecycleAction(StrEnum):
    NONE = "none"
    JOB_CANCEL = "job_cancel"
    QUEUE_DELETE = "queue_delete"
    TARGETED_INTERRUPT = "targeted_interrupt"
    RECOVER = "recover"
    FREE_REQUEST = "free_request"


class ComfyLifecycleOutcome(StrEnum):
    NOOP = "noop"
    DISPATCHED = "dispatched"
    RECONCILED = "reconciled"
    AMBIGUOUS = "ambiguous"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class ComfyLifecycleEvent:
    sequence: int
    action: ComfyLifecycleAction
    outcome: ComfyLifecycleOutcome
    observed_state: ComfyRunState
    request_digest_sha256: str | None
    response_digest_sha256: str | None
    previous_event_digest_sha256: str | None
    event_digest_sha256: str

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "action": self.action.value,
            "outcome": self.outcome.value,
            "observed_state": self.observed_state.value,
            "request_digest_sha256": self.request_digest_sha256,
            "response_digest_sha256": self.response_digest_sha256,
            "previous_event_digest_sha256": self.previous_event_digest_sha256,
        }

    def canonical(self) -> dict[str, Any]:
        value = self.canonical_without_digest()
        value["event_digest_sha256"] = self.event_digest_sha256
        return value


@dataclass(frozen=True, slots=True)
class ComfyLifecycleAudit:
    run_id: str
    run_manifest_digest_sha256: str
    endpoint: str
    events: tuple[ComfyLifecycleEvent, ...]
    audit_digest_sha256: str

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_manifest_digest_sha256": self.run_manifest_digest_sha256,
            "endpoint": self.endpoint,
            "events": [event.canonical() for event in self.events],
        }

    def payload(self) -> dict[str, Any]:
        value = self.canonical_without_digest()
        value["audit_digest_sha256"] = self.audit_digest_sha256
        return value

    def envelope(self) -> dict[str, Any]:
        return make_envelope(schema=_AUDIT_SCHEMA, version=_AUDIT_VERSION, payload=self.payload())


@dataclass(frozen=True, slots=True)
class ComfyFreeMemoryEvidence:
    endpoint: str
    unload_models: bool
    free_memory: bool
    request_digest_sha256: str
    before_system_digest_sha256: str
    after_system_digest_sha256: str
    request_acknowledged: bool
    reclaimed_bytes: None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "unload_models": self.unload_models,
            "free_memory": self.free_memory,
            "request_digest_sha256": self.request_digest_sha256,
            "before_system_digest_sha256": self.before_system_digest_sha256,
            "after_system_digest_sha256": self.after_system_digest_sha256,
            "request_acknowledged": self.request_acknowledged,
            "reclaimed_bytes": None,
        }


class ComfyLifecycleAuditStore:
    """Atomic tamper-evident per-run lifecycle audit with an append-only hash chain."""

    def __init__(self, root: Path | str) -> None:
        raw = Path(root)
        if raw.exists() and raw.is_symlink():
            raise ComfyProtocolError("Comfy lifecycle audit root must not be a symlink")
        raw.mkdir(parents=True, exist_ok=True)
        self.root = raw.resolve()

    def append(
        self,
        manifest: ComfyRunManifest,
        *,
        action: ComfyLifecycleAction,
        outcome: ComfyLifecycleOutcome,
        observed_state: ComfyRunState,
        request_digest_sha256: str | None = None,
        response_digest_sha256: str | None = None,
    ) -> ComfyLifecycleAudit:
        try:
            audit = self.load(manifest.run_id)
        except KeyError:
            audit = _seal_audit(
                ComfyLifecycleAudit(
                    run_id=manifest.run_id,
                    run_manifest_digest_sha256=manifest.manifest_digest_sha256,
                    endpoint=manifest.capability_endpoint,
                    events=(),
                    audit_digest_sha256="",
                )
            )
        if audit.endpoint != manifest.capability_endpoint:
            raise ComfyProtocolError("Lifecycle audit endpoint conflicts with run manifest")
        if len(audit.events) >= _MAX_EVENTS:
            raise ComfyProtocolError("Lifecycle audit event bound exceeded")
        previous = audit.events[-1].event_digest_sha256 if audit.events else None
        draft = ComfyLifecycleEvent(
            sequence=len(audit.events),
            action=action,
            outcome=outcome,
            observed_state=observed_state,
            request_digest_sha256=request_digest_sha256,
            response_digest_sha256=response_digest_sha256,
            previous_event_digest_sha256=previous,
            event_digest_sha256="",
        )
        event = replace(draft, event_digest_sha256=canonical_sha256(draft.canonical_without_digest()))
        updated = _seal_audit(
            replace(
                audit,
                run_manifest_digest_sha256=manifest.manifest_digest_sha256,
                events=audit.events + (event,),
                audit_digest_sha256="",
            )
        )
        self._write(updated)
        return updated

    def load(self, run_id: str) -> ComfyLifecycleAudit:
        path = self._path(run_id)
        if path.is_symlink():
            raise ComfyProtocolError("Comfy lifecycle audit path must not be a symlink")
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise KeyError(run_id) from exc
        except json.JSONDecodeError as exc:
            raise ComfyProtocolError("Comfy lifecycle audit is invalid JSON") from exc
        if not isinstance(document, dict):
            raise ComfyProtocolError("Comfy lifecycle audit root must be an object")
        payload = parse_envelope(document, expected_schema=_AUDIT_SCHEMA)
        audit = _audit_from_payload(payload)
        _validate_audit(audit)
        return audit

    def _write(self, audit: ComfyLifecycleAudit) -> None:
        path = self._path(audit.run_id)
        temporary = self.root / f".{audit.run_id}.{uuid.uuid4().hex}.tmp"
        data = canonical_json_bytes(audit.envelope())
        try:
            with temporary.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def _path(self, run_id: str) -> Path:
        if not isinstance(run_id, str) or not _SAFE_RUN_RE.fullmatch(run_id):
            raise ValueError("run_id must be a generated R9 run identifier")
        path = (self.root / f"{run_id}.json").resolve(strict=False)
        if not path.is_relative_to(self.root):
            raise ComfyProtocolError("Comfy lifecycle audit path escapes root")
        return path


class ComfyLifecycleService:
    """Bounded targeted cancellation, restart recovery and conservative memory cleanup."""

    def __init__(
        self,
        client: ComfyUIClient,
        run_store: ComfyRunStore,
        audit_store: ComfyLifecycleAuditStore | None = None,
    ) -> None:
        self.client = client
        self.run_store = run_store
        self.execution = ComfyExecutionService(client, run_store)
        self.audit = audit_store or ComfyLifecycleAuditStore(run_store.root / ".lifecycle")

    def cancel(
        self,
        run_id: str,
        instance: Any,
        *,
        budget: ComfyExecutionBudget | None = None,
        cancel_event: threading.Event | None = None,
    ) -> ComfyRunManifest:
        manifest = self.run_store.load(run_id)
        self._verify_origin(manifest)
        if is_terminal_run_state(manifest.state):
            self.audit.append(
                manifest,
                action=ComfyLifecycleAction.NONE,
                outcome=ComfyLifecycleOutcome.NOOP,
                observed_state=manifest.state,
            )
            return manifest

        current = self.execution.reconcile_once(run_id, instance)
        if is_terminal_run_state(current.state):
            self.audit.append(
                current,
                action=ComfyLifecycleAction.NONE,
                outcome=ComfyLifecycleOutcome.RECONCILED,
                observed_state=current.state,
            )
            return current

        queue = self.client.queue()
        running = current.prompt_id in queue.running_prompt_ids
        pending = current.prompt_id in queue.pending_prompt_ids
        if running and pending:
            raise ComfyProtocolError("Prompt cannot be both running and pending during cancellation")
        if not running and not pending:
            self.audit.append(
                current,
                action=ComfyLifecycleAction.NONE,
                outcome=ComfyLifecycleOutcome.NOOP,
                observed_state=current.state,
                response_digest_sha256=queue.digest_sha256,
            )
            return self.execution.reconcile_once(run_id, instance)

        request = {"job_id": current.prompt_id}
        request_digest = canonical_sha256(request)
        action = ComfyLifecycleAction.JOB_CANCEL
        response_digest: str | None = None
        try:
            response = self.client._http.post_json(
                f"/api/jobs/{quote(current.prompt_id, safe='')}/cancel",
                {},
            )
            if set(response) != {"cancelled"} or not isinstance(response["cancelled"], bool):
                raise ComfyProtocolError("ComfyUI job-cancel response shape is invalid")
            response_digest = canonical_sha256(response)
        except ComfyProtocolError as exc:
            if "status 404" not in str(exc):
                raise
            if pending:
                action = ComfyLifecycleAction.QUEUE_DELETE
                request = {"delete": [current.prompt_id]}
                request_digest = canonical_sha256(request)
                self._post_empty("/queue", request)
            else:
                # Legacy /interrupt is global in upstream ComfyUI. Sending a prompt_id body does
                # not make it targeted, so using it would risk interrupting another prompt.
                action = ComfyLifecycleAction.TARGETED_INTERRUPT
                self.audit.append(
                    current,
                    action=action,
                    outcome=ComfyLifecycleOutcome.UNSUPPORTED,
                    observed_state=current.state,
                    request_digest_sha256=request_digest,
                )
                raise ComfyGovernanceError(
                    "Running-job cancellation is unsupported by this ComfyUI version without the targeted job-cancel API"
                ) from exc
        except (ComfySubmissionAmbiguousError, ComfyUnavailableError):
            self.audit.append(
                current,
                action=action,
                outcome=ComfyLifecycleOutcome.AMBIGUOUS,
                observed_state=current.state,
                request_digest_sha256=request_digest,
            )
            raise

        self.audit.append(
            current,
            action=action,
            outcome=ComfyLifecycleOutcome.DISPATCHED,
            observed_state=current.state,
            request_digest_sha256=request_digest,
            response_digest_sha256=response_digest,
        )
        limits = budget or ComfyExecutionBudget(
            max_poll_attempts=16,
            poll_interval_seconds=0.01,
            max_wait_seconds=10,
        )
        result = self.execution.wait(run_id, instance, budget=limits, cancel_event=cancel_event)
        self.audit.append(
            result,
            action=ComfyLifecycleAction.RECOVER,
            outcome=(
                ComfyLifecycleOutcome.RECONCILED
                if is_terminal_run_state(result.state)
                else ComfyLifecycleOutcome.AMBIGUOUS
            ),
            observed_state=result.state,
        )
        return result

    def recover(self, run_id: str, instance: Any) -> ComfyRunManifest:
        try:
            manifest = self.run_store.load(run_id)
        except ComfyProtocolError:
            manifest = self.run_store.recover(run_id)
        self._verify_origin(manifest)
        if is_terminal_run_state(manifest.state):
            self.audit.append(
                manifest,
                action=ComfyLifecycleAction.RECOVER,
                outcome=ComfyLifecycleOutcome.NOOP,
                observed_state=manifest.state,
            )
            return manifest
        try:
            result = self.execution.reconcile_once(run_id, instance)
        except (ComfyUnavailableError, ComfySubmissionAmbiguousError):
            self.audit.append(
                manifest,
                action=ComfyLifecycleAction.RECOVER,
                outcome=ComfyLifecycleOutcome.AMBIGUOUS,
                observed_state=manifest.state,
            )
            raise
        self.audit.append(
            result,
            action=ComfyLifecycleAction.RECOVER,
            outcome=(
                ComfyLifecycleOutcome.RECONCILED
                if result.state != manifest.state
                else ComfyLifecycleOutcome.NOOP
            ),
            observed_state=result.state,
        )
        return result

    def request_free_memory(
        self,
        *,
        known_run_ids: tuple[str, ...] = (),
        unload_models: bool = True,
        free_memory: bool = True,
        settle_seconds: float = 0.0,
    ) -> ComfyFreeMemoryEvidence:
        if not unload_models and free_memory:
            raise ComfyGovernanceError(
                "free_memory without unload_models is rejected because ComfyUI may unload implicitly"
            )
        if not unload_models and not free_memory:
            raise ValueError("At least one cleanup request must be enabled")
        if not 0 <= settle_seconds <= 30:
            raise ValueError("settle_seconds must be between 0 and 30 seconds")

        manifests: list[ComfyRunManifest] = []
        for run_id in known_run_ids:
            manifest = self.run_store.load(run_id)
            self._verify_origin(manifest)
            if not is_terminal_run_state(manifest.state):
                self.audit.append(
                    manifest,
                    action=ComfyLifecycleAction.FREE_REQUEST,
                    outcome=ComfyLifecycleOutcome.BLOCKED,
                    observed_state=manifest.state,
                )
                raise ComfyGovernanceError(
                    "Free-memory request is blocked while a known Kodepoia run is non-terminal"
                )
            manifests.append(manifest)

        before = self.client.system_stats()
        request = {"unload_models": bool(unload_models), "free_memory": bool(free_memory)}
        request_digest = canonical_sha256(request)
        try:
            self._post_empty("/free", request)
            if settle_seconds:
                time.sleep(settle_seconds)
            after = self.client.system_stats()
        except (ComfySubmissionAmbiguousError, ComfyUnavailableError):
            for manifest in manifests:
                self.audit.append(
                    manifest,
                    action=ComfyLifecycleAction.FREE_REQUEST,
                    outcome=ComfyLifecycleOutcome.AMBIGUOUS,
                    observed_state=manifest.state,
                    request_digest_sha256=request_digest,
                )
            raise

        response_digest = canonical_sha256(
            {
                "request_acknowledged": True,
                "before_system_digest_sha256": before.digest_sha256,
                "after_system_digest_sha256": after.digest_sha256,
                "reclaimed_bytes": None,
            }
        )
        for manifest in manifests:
            self.audit.append(
                manifest,
                action=ComfyLifecycleAction.FREE_REQUEST,
                outcome=ComfyLifecycleOutcome.RECONCILED,
                observed_state=manifest.state,
                request_digest_sha256=request_digest,
                response_digest_sha256=response_digest,
            )

        return ComfyFreeMemoryEvidence(
            endpoint=self.client.endpoint.origin,
            unload_models=bool(unload_models),
            free_memory=bool(free_memory),
            request_digest_sha256=request_digest,
            before_system_digest_sha256=before.digest_sha256,
            after_system_digest_sha256=after.digest_sha256,
            request_acknowledged=True,
            reclaimed_bytes=None,
        )

    def cleanup_terminal_run(
        self,
        run_id: str,
        *,
        settle_seconds: float = 0.0,
    ) -> ComfyFreeMemoryEvidence:
        manifest = self.run_store.load(run_id)
        self._verify_origin(manifest)
        if not is_terminal_run_state(manifest.state):
            self.audit.append(
                manifest,
                action=ComfyLifecycleAction.FREE_REQUEST,
                outcome=ComfyLifecycleOutcome.BLOCKED,
                observed_state=manifest.state,
            )
            raise ComfyGovernanceError("Cleanup is allowed only after a terminal run state")
        return self.request_free_memory(
            known_run_ids=(run_id,),
            unload_models=True,
            free_memory=True,
            settle_seconds=settle_seconds,
        )

    def _post_empty(self, path: str, document: dict[str, Any]) -> None:
        if path not in {"/queue", "/free"}:
            raise ComfyGovernanceError("Lifecycle operation is outside the fixed accepted route set")
        body = canonical_json_bytes(document)
        payload = self.client._http._post_target(
            path,
            body=body,
            max_bytes=self.client.limits.max_json_bytes,
        )
        if payload.body not in {b"", b"{}", b"null"}:
            try:
                decoded = json.loads(payload.body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ComfyProtocolError("ComfyUI lifecycle acknowledgement is malformed") from exc
            if decoded not in ({}, None):
                raise ComfyProtocolError(
                    "ComfyUI lifecycle acknowledgement contains unexpected data"
                )

    def _verify_origin(self, manifest: ComfyRunManifest) -> None:
        if manifest.capability_endpoint != self.client.endpoint.origin:
            raise ComfyGovernanceError("Lifecycle client origin does not match run manifest")


def _seal_audit(audit: ComfyLifecycleAudit) -> ComfyLifecycleAudit:
    if not _SAFE_RUN_RE.fullmatch(audit.run_id):
        raise ComfyProtocolError("Lifecycle audit run ID is invalid")
    if not _HEX64_RE.fullmatch(audit.run_manifest_digest_sha256):
        raise ComfyProtocolError("Lifecycle run-manifest digest is invalid")
    if not audit.endpoint or len(audit.endpoint) > 2048:
        raise ComfyProtocolError("Lifecycle endpoint is invalid")
    if len(audit.events) > _MAX_EVENTS:
        raise ComfyProtocolError("Lifecycle audit event bound exceeded")
    previous: str | None = None
    for index, event in enumerate(audit.events):
        if event.sequence != index or event.previous_event_digest_sha256 != previous:
            raise ComfyProtocolError("Lifecycle event chain is broken")
        for digest in (
            event.request_digest_sha256,
            event.response_digest_sha256,
            event.previous_event_digest_sha256,
        ):
            if digest is not None and not _HEX64_RE.fullmatch(digest):
                raise ComfyProtocolError("Lifecycle event digest field is invalid")
        expected = canonical_sha256(event.canonical_without_digest())
        if event.event_digest_sha256 != expected:
            raise ComfyProtocolError("Lifecycle event digest is invalid")
        previous = event.event_digest_sha256
    normalized = replace(audit, audit_digest_sha256="")
    return replace(
        normalized,
        audit_digest_sha256=canonical_sha256(normalized.canonical_without_digest()),
    )


def _validate_audit(audit: ComfyLifecycleAudit) -> None:
    sealed = _seal_audit(audit)
    if sealed.audit_digest_sha256 != audit.audit_digest_sha256:
        raise ComfyProtocolError("Lifecycle audit digest is invalid")


def _audit_from_payload(payload: dict[str, Any]) -> ComfyLifecycleAudit:
    expected = {
        "run_id",
        "run_manifest_digest_sha256",
        "endpoint",
        "events",
        "audit_digest_sha256",
    }
    if set(payload) != expected or not isinstance(payload["events"], list):
        raise ComfyProtocolError("Lifecycle audit payload fields are invalid")
    events: list[ComfyLifecycleEvent] = []
    for item in payload["events"]:
        if not isinstance(item, dict):
            raise ComfyProtocolError("Lifecycle audit event must be an object")
        try:
            events.append(
                ComfyLifecycleEvent(
                    sequence=item["sequence"],
                    action=ComfyLifecycleAction(item["action"]),
                    outcome=ComfyLifecycleOutcome(item["outcome"]),
                    observed_state=ComfyRunState(item["observed_state"]),
                    request_digest_sha256=item["request_digest_sha256"],
                    response_digest_sha256=item["response_digest_sha256"],
                    previous_event_digest_sha256=item["previous_event_digest_sha256"],
                    event_digest_sha256=item["event_digest_sha256"],
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ComfyProtocolError("Lifecycle audit event fields are invalid") from exc
    try:
        audit = ComfyLifecycleAudit(
            run_id=payload["run_id"],
            run_manifest_digest_sha256=payload["run_manifest_digest_sha256"],
            endpoint=payload["endpoint"],
            events=tuple(events),
            audit_digest_sha256=payload["audit_digest_sha256"],
        )
    except (KeyError, TypeError) as exc:
        raise ComfyProtocolError("Lifecycle audit fields are invalid") from exc
    _validate_audit(audit)
    return audit
