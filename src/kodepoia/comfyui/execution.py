from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from .client import ComfyExecutionHistory, ComfyUIClient
from .contracts import ComfyOutputReference, ComfyRunState, can_transition_run_state, is_terminal_run_state
from .errors import (
    ComfyGovernanceError,
    ComfyProtocolError,
    ComfySubmissionAmbiguousError,
    ComfyUnavailableError,
)
from .events import ComfyProtocolEvent
from .inventory import ComfyCapabilitySnapshot
from .serialization import canonical_json_bytes, canonical_sha256, make_envelope, parse_envelope
from .workflow import ModelResolutionSet, WorkflowDefinition, WorkflowInstance, WorkflowValidator

_RUN_SCHEMA = "kodepoia.comfy-run-manifest"
_RUN_VERSION = 1
_SAFE_RUN_RE = re.compile(r"^run_[0-9a-f]{32}$")
_SAFE_PROMPT_RE = re.compile(r"^kp_[0-9a-f]{32}$")
_SAFE_CLIENT_RE = re.compile(r"^kc_[0-9a-f]{32}$")
_MAX_REQUIRED_OUTPUTS = 4096
_MAX_OUTPUT_REFS = 100000


@dataclass(frozen=True, slots=True)
class ComfyExecutionBudget:
    max_submission_attempts: int = 2
    max_poll_attempts: int = 64
    poll_interval_seconds: float = 0.0
    max_wait_seconds: float = 120.0

    def __post_init__(self) -> None:
        if isinstance(self.max_submission_attempts, bool) or not 1 <= self.max_submission_attempts <= 2:
            raise ValueError("max_submission_attempts must be 1 or 2")
        if isinstance(self.max_poll_attempts, bool) or not 1 <= self.max_poll_attempts <= 10000:
            raise ValueError("max_poll_attempts must be between 1 and 10000")
        if not 0 <= self.poll_interval_seconds <= 30:
            raise ValueError("poll_interval_seconds must be between 0 and 30")
        if not 0 < self.max_wait_seconds <= 86400:
            raise ValueError("max_wait_seconds must be between 0 and 86400")


@dataclass(frozen=True, slots=True)
class ComfyRunManifest:
    run_id: str
    prompt_id: str
    client_id: str
    state: ComfyRunState
    definition_id: str
    definition_digest_sha256: str
    capability_identity_sha256: str
    model_resolution_digest_sha256: str
    instance_digest_sha256: str
    prompt_digest_sha256: str
    required_output_node_ids: tuple[str, ...]
    submission_attempts: int
    progress_fraction: float | None
    queue_digest_sha256: str | None
    history_digest_sha256: str | None
    output_references: tuple[ComfyOutputReference, ...]
    manifest_digest_sha256: str

    @property
    def terminal(self) -> bool:
        return is_terminal_run_state(self.state)

    def correlation(self) -> dict[str, str]:
        return {
            "run_id": self.run_id,
            "instance_digest_sha256": self.instance_digest_sha256,
            "definition_id": self.definition_id,
        }

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "prompt_id": self.prompt_id,
            "client_id": self.client_id,
            "state": self.state.value,
            "definition_id": self.definition_id,
            "definition_digest_sha256": self.definition_digest_sha256,
            "capability_identity_sha256": self.capability_identity_sha256,
            "model_resolution_digest_sha256": self.model_resolution_digest_sha256,
            "instance_digest_sha256": self.instance_digest_sha256,
            "prompt_digest_sha256": self.prompt_digest_sha256,
            "required_output_node_ids": list(self.required_output_node_ids),
            "submission_attempts": self.submission_attempts,
            "progress_fraction": self.progress_fraction,
            "queue_digest_sha256": self.queue_digest_sha256,
            "history_digest_sha256": self.history_digest_sha256,
            "output_references": [item.canonical() for item in self.output_references],
        }

    def payload(self) -> dict[str, Any]:
        payload = self.canonical_without_digest()
        payload["manifest_digest_sha256"] = self.manifest_digest_sha256
        return payload

    def envelope(self) -> dict[str, Any]:
        return make_envelope(schema=_RUN_SCHEMA, version=_RUN_VERSION, payload=self.payload())


class ComfyRunStore:
    """Root-confined atomic durable run manifests; one explicit file per generated run ID."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise ComfyProtocolError("Comfy run store root must not be a symlink")

    def save(self, manifest: ComfyRunManifest) -> Path:
        self._validate_manifest(manifest)
        path = self._path(manifest.run_id)
        if path.exists() and path.is_symlink():
            raise ComfyProtocolError("Comfy run manifest path must not be a symlink")
        temp = self.root / f".{manifest.run_id}.{uuid.uuid4().hex}.tmp"
        document = canonical_json_bytes(manifest.envelope())
        try:
            with temp.open("xb") as handle:
                handle.write(document)
                handle.flush()
                os.fsync(handle.fileno())
            if temp.is_symlink():
                raise ComfyProtocolError("Comfy run manifest staging path became a symlink")
            os.replace(temp, path)
        finally:
            if temp.exists():
                temp.unlink()
        return path

    def load(self, run_id: str) -> ComfyRunManifest:
        path = self._path(run_id)
        if path.is_symlink():
            raise ComfyProtocolError("Comfy run manifest path must not be a symlink")
        try:
            raw = path.read_bytes()
        except FileNotFoundError as exc:
            raise KeyError(f"Unknown Comfy run: {run_id}") from exc
        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ComfyProtocolError("Comfy run manifest is invalid JSON") from exc
        if not isinstance(document, dict):
            raise ComfyProtocolError("Comfy run manifest root must be an object")
        payload = parse_envelope(document, expected_schema=_RUN_SCHEMA)
        manifest = _manifest_from_payload(payload)
        self._validate_manifest(manifest)
        return manifest

    def _path(self, run_id: str) -> Path:
        if not isinstance(run_id, str) or not _SAFE_RUN_RE.fullmatch(run_id):
            raise ValueError("run_id must be a generated R9.5 run identifier")
        path = (self.root / f"{run_id}.json").resolve(strict=False)
        if not path.is_relative_to(self.root):
            raise ComfyProtocolError("Comfy run manifest path escapes store root")
        return path

    @staticmethod
    def _validate_manifest(manifest: ComfyRunManifest) -> None:
        expected = canonical_sha256(manifest.canonical_without_digest())
        if expected != manifest.manifest_digest_sha256:
            raise ComfyProtocolError("Comfy run manifest digest does not match canonical evidence")


class ComfyExecutionService:
    """Durable exactly-once-per-run submission and poll-authoritative reconciliation."""

    def __init__(self, client: ComfyUIClient, store: ComfyRunStore) -> None:
        self.client = client
        self.store = store

    def prepare(
        self,
        definition: WorkflowDefinition,
        snapshot: ComfyCapabilitySnapshot,
        resolutions: ModelResolutionSet,
        instance: WorkflowInstance,
        *,
        required_output_node_ids: tuple[str, ...] = (),
    ) -> ComfyRunManifest:
        self._verify_preflight(definition, snapshot, resolutions, instance)
        required = _required_output_nodes(required_output_node_ids)
        run_id = f"run_{uuid.uuid4().hex}"
        prompt_id = f"kp_{uuid.uuid4().hex}"
        client_id = f"kc_{uuid.uuid4().hex}"
        manifest = _seal(
            ComfyRunManifest(
                run_id=run_id,
                prompt_id=prompt_id,
                client_id=client_id,
                state=ComfyRunState.PREPARED,
                definition_id=definition.definition_id,
                definition_digest_sha256=definition.definition_digest_sha256,
                capability_identity_sha256=snapshot.identity_sha256,
                model_resolution_digest_sha256=resolutions.digest_sha256,
                instance_digest_sha256=instance.instance_digest_sha256,
                prompt_digest_sha256=canonical_sha256(instance.prompt()),
                required_output_node_ids=required,
                submission_attempts=0,
                progress_fraction=None,
                queue_digest_sha256=None,
                history_digest_sha256=None,
                output_references=(),
                manifest_digest_sha256="",
            )
        )
        self.store.save(manifest)
        return manifest

    def submit(
        self,
        run_id: str,
        definition: WorkflowDefinition,
        snapshot: ComfyCapabilitySnapshot,
        resolutions: ModelResolutionSet,
        instance: WorkflowInstance,
        *,
        budget: ComfyExecutionBudget | None = None,
        cancel_event: threading.Event | None = None,
    ) -> ComfyRunManifest:
        limits = budget or ComfyExecutionBudget()
        manifest = self.store.load(run_id)
        self._verify_manifest_bindings(manifest, definition, snapshot, resolutions, instance)
        if manifest.state is not ComfyRunState.PREPARED:
            return manifest
        if cancel_event is not None and cancel_event.is_set():
            return self._persist_transition(manifest, ComfyRunState.CANCELLED)
        if manifest.submission_attempts >= limits.max_submission_attempts:
            raise ComfyUnavailableError("Comfy run exhausted its bounded submission attempts")

        current = manifest
        while current.submission_attempts < limits.max_submission_attempts:
            # Persist the attempt before any side effect; a crash can never forget that POST may have happened.
            current = _seal(replace(current, submission_attempts=current.submission_attempts + 1))
            self.store.save(current)
            try:
                self.client.submit_prompt(
                    instance.prompt(),
                    prompt_id=current.prompt_id,
                    client_id=current.client_id,
                    correlation=current.correlation(),
                )
            except ComfySubmissionAmbiguousError:
                reconciled = self._reconcile_presence(current, instance)
                if reconciled.state is not ComfyRunState.PREPARED:
                    return reconciled
                current = reconciled
                if current.submission_attempts >= limits.max_submission_attempts:
                    raise ComfyUnavailableError(
                        "Prompt submission remained ambiguous after bounded queue/history reconciliation"
                    )
                continue
            return self._persist_transition(current, ComfyRunState.QUEUED)
        raise ComfyUnavailableError("Comfy run exhausted its bounded submission attempts")

    def reconcile_once(self, run_id: str, instance: WorkflowInstance) -> ComfyRunManifest:
        manifest = self.store.load(run_id)
        if manifest.instance_digest_sha256 != instance.instance_digest_sha256:
            raise ComfyGovernanceError("Run manifest is bound to a different workflow instance")
        if canonical_sha256(instance.prompt()) != manifest.prompt_digest_sha256:
            raise ComfyGovernanceError("Workflow instance prompt changed after run preparation")
        if manifest.terminal:
            return manifest

        queue = self.client.queue()
        history = self.client.execution_history(manifest.prompt_id)
        in_running = manifest.prompt_id in queue.running_prompt_ids
        in_pending = manifest.prompt_id in queue.pending_prompt_ids
        if in_running and in_pending:
            raise ComfyProtocolError("ComfyUI queue reports prompt as both running and pending")
        if history.present and is_terminal_run_state(history.state) and (in_running or in_pending):
            raise ComfyProtocolError("ComfyUI terminal history contradicts active queue evidence")

        current = _seal(replace(manifest, queue_digest_sha256=queue.digest_sha256))
        self.store.save(current)
        if history.present:
            current = self._validate_history(current, history)
            if is_terminal_run_state(history.state):
                return self._apply_terminal_history(current, history)
            if history.state is ComfyRunState.RUNNING:
                return self._advance_to_running(current)
        if in_running:
            return self._advance_to_running(current)
        if in_pending:
            return self._advance_to_queued(current)
        return current

    def wait(
        self,
        run_id: str,
        instance: WorkflowInstance,
        *,
        budget: ComfyExecutionBudget | None = None,
        cancel_event: threading.Event | None = None,
    ) -> ComfyRunManifest:
        limits = budget or ComfyExecutionBudget()
        started = time.monotonic()
        current = self.store.load(run_id)
        for _ in range(limits.max_poll_attempts):
            if current.terminal:
                return current
            if cancel_event is not None and cancel_event.is_set():
                # R9.5 cancellation is cooperative monitoring cancellation only once submitted.
                return current
            if time.monotonic() - started >= limits.max_wait_seconds:
                return current
            current = self.reconcile_once(run_id, instance)
            if current.terminal:
                return current
            if limits.poll_interval_seconds:
                if cancel_event is not None:
                    if cancel_event.wait(limits.poll_interval_seconds):
                        return current
                else:
                    time.sleep(limits.poll_interval_seconds)
        return current

    def observe_event(self, run_id: str, event: ComfyProtocolEvent) -> ComfyRunManifest:
        manifest = self.store.load(run_id)
        if event.prompt_id is not None and event.prompt_id != manifest.prompt_id:
            raise ComfyProtocolError("WebSocket event prompt_id does not match run manifest")
        if manifest.terminal:
            return manifest
        fraction = event.progress_fraction
        progress = manifest.progress_fraction
        if fraction is not None:
            progress = fraction if progress is None else max(progress, fraction)
        state = manifest.state
        if event.prompt_id == manifest.prompt_id and event.event_type.value in {
            "execution_start",
            "executing",
            "progress",
            "executed",
            "execution_cached",
            "progress_state",
            "progress_text",
        }:
            if state is ComfyRunState.PREPARED:
                state = ComfyRunState.QUEUED
            if state is ComfyRunState.QUEUED:
                state = ComfyRunState.RUNNING
        # Terminal WS events are hints only; polling/history remains authoritative.
        updated = _seal(replace(manifest, state=state, progress_fraction=progress))
        self.store.save(updated)
        return updated

    def _reconcile_presence(self, manifest: ComfyRunManifest, instance: WorkflowInstance) -> ComfyRunManifest:
        queue = self.client.queue()
        history = self.client.execution_history(manifest.prompt_id)
        current = _seal(replace(manifest, queue_digest_sha256=queue.digest_sha256))
        self.store.save(current)
        if history.present:
            current = self._validate_history(current, history)
            if is_terminal_run_state(history.state):
                return self._apply_terminal_history(current, history)
            if history.state is ComfyRunState.RUNNING:
                return self._advance_to_running(current)
        if manifest.prompt_id in queue.running_prompt_ids:
            return self._advance_to_running(current)
        if manifest.prompt_id in queue.pending_prompt_ids:
            return self._advance_to_queued(current)
        return current

    def _validate_history(
        self,
        manifest: ComfyRunManifest,
        history: ComfyExecutionHistory,
    ) -> ComfyRunManifest:
        if history.prompt_id != manifest.prompt_id:
            raise ComfyProtocolError("History prompt_id does not match run manifest")
        if history.prompt_digest_sha256 != manifest.prompt_digest_sha256:
            raise ComfyProtocolError("History prompt digest does not match submitted workflow instance")
        correlation = dict(history.correlation)
        for key, expected in manifest.correlation().items():
            if correlation.get(key) != expected:
                raise ComfyProtocolError("History correlation metadata does not match run manifest")
        updated = _seal(replace(manifest, history_digest_sha256=history.digest_sha256))
        self.store.save(updated)
        return updated

    def _apply_terminal_history(
        self,
        manifest: ComfyRunManifest,
        history: ComfyExecutionHistory,
    ) -> ComfyRunManifest:
        if history.state is ComfyRunState.SUCCEEDED:
            available_nodes = {item.node_id for item in history.output_references}
            missing = set(manifest.required_output_node_ids) - available_nodes
            if missing:
                raise ComfyProtocolError(
                    f"ComfyUI success history is missing required output references: {sorted(missing)!r}"
                )
            current = self._advance_to_running(manifest)
            current = _seal(replace(current, output_references=history.output_references))
            self.store.save(current)
            return self._persist_transition(current, ComfyRunState.SUCCEEDED)
        if history.state in {ComfyRunState.FAILED, ComfyRunState.CANCELLED}:
            current = self._advance_to_running(manifest)
            return self._persist_transition(current, history.state)
        raise ComfyProtocolError("Non-terminal history cannot be applied as terminal evidence")

    def _advance_to_queued(self, manifest: ComfyRunManifest) -> ComfyRunManifest:
        if manifest.state is ComfyRunState.PREPARED:
            return self._persist_transition(manifest, ComfyRunState.QUEUED)
        return manifest

    def _advance_to_running(self, manifest: ComfyRunManifest) -> ComfyRunManifest:
        current = self._advance_to_queued(manifest)
        if current.state is ComfyRunState.QUEUED:
            return self._persist_transition(current, ComfyRunState.RUNNING)
        return current

    def _persist_transition(self, manifest: ComfyRunManifest, state: ComfyRunState) -> ComfyRunManifest:
        if not can_transition_run_state(manifest.state, state):
            raise ComfyProtocolError(
                f"Impossible run manifest transition: {manifest.state.value} -> {state.value}"
            )
        updated = _seal(replace(manifest, state=state))
        self.store.save(updated)
        return updated

    @staticmethod
    def _verify_preflight(
        definition: WorkflowDefinition,
        snapshot: ComfyCapabilitySnapshot,
        resolutions: ModelResolutionSet,
        instance: WorkflowInstance,
    ) -> None:
        WorkflowValidator().validate(definition, snapshot)
        expected_resolution = canonical_sha256(resolutions.canonical_without_digest())
        if expected_resolution != resolutions.digest_sha256 or not resolutions.ready:
            raise ComfyGovernanceError("Model resolution evidence is stale, tampered or unresolved")
        if instance.definition_id != definition.definition_id:
            raise ComfyGovernanceError("Workflow instance definition ID is stale")
        if instance.definition_digest_sha256 != definition.definition_digest_sha256:
            raise ComfyGovernanceError("Workflow instance definition digest is stale")
        if instance.capability_identity_sha256 != snapshot.identity_sha256:
            raise ComfyGovernanceError("Workflow instance capability snapshot is stale")
        if instance.model_resolution_digest_sha256 != resolutions.digest_sha256:
            raise ComfyGovernanceError("Workflow instance model resolution is stale")
        expected_instance = _instance_digest(instance)
        if expected_instance != instance.instance_digest_sha256:
            raise ComfyGovernanceError("Workflow instance digest does not match canonical evidence")

    @classmethod
    def _verify_manifest_bindings(
        cls,
        manifest: ComfyRunManifest,
        definition: WorkflowDefinition,
        snapshot: ComfyCapabilitySnapshot,
        resolutions: ModelResolutionSet,
        instance: WorkflowInstance,
    ) -> None:
        cls._verify_preflight(definition, snapshot, resolutions, instance)
        expected = {
            "definition_id": definition.definition_id,
            "definition_digest_sha256": definition.definition_digest_sha256,
            "capability_identity_sha256": snapshot.identity_sha256,
            "model_resolution_digest_sha256": resolutions.digest_sha256,
            "instance_digest_sha256": instance.instance_digest_sha256,
            "prompt_digest_sha256": canonical_sha256(instance.prompt()),
        }
        for field_name, value in expected.items():
            if getattr(manifest, field_name) != value:
                raise ComfyGovernanceError(f"Run manifest {field_name} does not match current execution evidence")


def _instance_digest(instance: WorkflowInstance) -> str:
    payload = instance.canonical()
    payload.pop("instance_digest_sha256", None)
    return canonical_sha256(payload)


def _required_output_nodes(values: tuple[str, ...]) -> tuple[str, ...]:
    if len(values) > _MAX_REQUIRED_OUTPUTS:
        raise ValueError("required output node count exceeds accepted bound")
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value or len(value) > 128 or any(ord(ch) < 32 for ch in value):
            raise ValueError("required output node IDs must be bounded non-empty strings")
        result.append(value)
    if len(set(result)) != len(result):
        raise ValueError("required output node IDs must be unique")
    return tuple(sorted(result))


def _seal(manifest: ComfyRunManifest) -> ComfyRunManifest:
    if not _SAFE_RUN_RE.fullmatch(manifest.run_id):
        raise ComfyProtocolError("Run manifest run_id is invalid")
    if not _SAFE_PROMPT_RE.fullmatch(manifest.prompt_id):
        raise ComfyProtocolError("Run manifest prompt_id is invalid")
    if not _SAFE_CLIENT_RE.fullmatch(manifest.client_id):
        raise ComfyProtocolError("Run manifest client_id is invalid")
    if isinstance(manifest.submission_attempts, bool) or not 0 <= manifest.submission_attempts <= 2:
        raise ComfyProtocolError("Run manifest submission_attempts is invalid")
    if manifest.progress_fraction is not None and not 0.0 <= manifest.progress_fraction <= 1.0:
        raise ComfyProtocolError("Run manifest progress_fraction is invalid")
    if len(manifest.output_references) > _MAX_OUTPUT_REFS:
        raise ComfyProtocolError("Run manifest output reference count exceeds accepted bound")
    draft = replace(manifest, manifest_digest_sha256="")
    return replace(draft, manifest_digest_sha256=canonical_sha256(draft.canonical_without_digest()))


def _manifest_from_payload(payload: dict[str, Any]) -> ComfyRunManifest:
    expected = {
        "run_id",
        "prompt_id",
        "client_id",
        "state",
        "definition_id",
        "definition_digest_sha256",
        "capability_identity_sha256",
        "model_resolution_digest_sha256",
        "instance_digest_sha256",
        "prompt_digest_sha256",
        "required_output_node_ids",
        "submission_attempts",
        "progress_fraction",
        "queue_digest_sha256",
        "history_digest_sha256",
        "output_references",
        "manifest_digest_sha256",
    }
    if set(payload) != expected:
        raise ComfyProtocolError("Comfy run manifest payload fields are invalid")
    required = payload["required_output_node_ids"]
    refs = payload["output_references"]
    if not isinstance(required, list) or not isinstance(refs, list):
        raise ComfyProtocolError("Comfy run manifest arrays have invalid shape")
    try:
        state = ComfyRunState(payload["state"])
    except (TypeError, ValueError) as exc:
        raise ComfyProtocolError("Comfy run manifest state is invalid") from exc
    output_references: list[ComfyOutputReference] = []
    for raw in refs:
        if not isinstance(raw, dict) or set(raw) != {
            "prompt_id",
            "node_id",
            "output_index",
            "server_filename",
            "server_subfolder",
            "storage_type",
        }:
            raise ComfyProtocolError("Comfy run output reference fields are invalid")
        try:
            output_references.append(ComfyOutputReference(**raw))
        except (TypeError, ValueError) as exc:
            raise ComfyProtocolError("Comfy run output reference is invalid") from exc
    manifest = ComfyRunManifest(
        run_id=payload["run_id"],
        prompt_id=payload["prompt_id"],
        client_id=payload["client_id"],
        state=state,
        definition_id=payload["definition_id"],
        definition_digest_sha256=payload["definition_digest_sha256"],
        capability_identity_sha256=payload["capability_identity_sha256"],
        model_resolution_digest_sha256=payload["model_resolution_digest_sha256"],
        instance_digest_sha256=payload["instance_digest_sha256"],
        prompt_digest_sha256=payload["prompt_digest_sha256"],
        required_output_node_ids=_required_output_nodes(tuple(required)),
        submission_attempts=payload["submission_attempts"],
        progress_fraction=payload["progress_fraction"],
        queue_digest_sha256=payload["queue_digest_sha256"],
        history_digest_sha256=payload["history_digest_sha256"],
        output_references=tuple(output_references),
        manifest_digest_sha256=payload["manifest_digest_sha256"],
    )
    # Validate structural fields without replacing the persisted digest.
    sealed = _seal(manifest)
    if sealed.manifest_digest_sha256 != manifest.manifest_digest_sha256:
        raise ComfyProtocolError("Comfy run manifest digest does not match canonical evidence")
    return manifest
