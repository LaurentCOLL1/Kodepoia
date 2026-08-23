from __future__ import annotations

import json
import math
import os
import re
import threading
import time
import uuid
from dataclasses import dataclass, replace
from enum import StrEnum
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
from .workflow import (
    ModelResolutionSet,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowParameterKind,
    WorkflowValidator,
)

_RUN_SCHEMA = "kodepoia.comfy-run-manifest"
_RUN_VERSION = 1
_SAFE_RUN_RE = re.compile(r"^run_[0-9a-f]{32}$")
_SAFE_PROMPT_RE = re.compile(r"^kp_[0-9a-f]{32}$")
_SAFE_CLIENT_RE = re.compile(r"^kc_[0-9a-f]{32}$")
_SAFE_WORKFLOW_RE = re.compile(r"^wf_[0-9a-f]{32}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_MAX_REQUIRED_OUTPUTS = 4096
_MAX_OUTPUT_REFS = 100000
_MAX_MANIFEST_REVISIONS = 100000
_MAX_AUDIT_FIELDS = 4096
_MAX_AUDIT_TEXT = 4096


class ComfySubmissionOutcome(StrEnum):
    NOT_ATTEMPTED = "not_attempted"
    ATTEMPTING = "attempting"
    ACCEPTED = "accepted"
    AMBIGUOUS = "ambiguous"
    RECOVERED = "recovered"


@dataclass(frozen=True, slots=True)
class ComfyExecutionBudget:
    max_poll_attempts: int = 64
    poll_interval_seconds: float = 0.0
    max_wait_seconds: float = 120.0
    ambiguous_reconcile_attempts: int = 8
    ambiguous_reconcile_interval_seconds: float = 0.05

    def __post_init__(self) -> None:
        if isinstance(self.max_poll_attempts, bool) or not 1 <= self.max_poll_attempts <= 10000:
            raise ValueError("max_poll_attempts must be between 1 and 10000")
        if not 0 <= self.poll_interval_seconds <= 30:
            raise ValueError("poll_interval_seconds must be between 0 and 30")
        if not 0 < self.max_wait_seconds <= 86400:
            raise ValueError("max_wait_seconds must be between 0 and 86400")
        if isinstance(self.ambiguous_reconcile_attempts, bool) or not 1 <= self.ambiguous_reconcile_attempts <= 256:
            raise ValueError("ambiguous_reconcile_attempts must be between 1 and 256")
        if not 0 <= self.ambiguous_reconcile_interval_seconds <= 30:
            raise ValueError("ambiguous_reconcile_interval_seconds must be between 0 and 30")


@dataclass(frozen=True, slots=True)
class ComfyRunManifest:
    run_id: str
    revision: int
    previous_manifest_digest_sha256: str | None
    prompt_id: str
    client_id: str
    state: ComfyRunState
    submission_outcome: ComfySubmissionOutcome
    definition_id: str
    definition_digest_sha256: str
    capability_identity_sha256: str
    capability_endpoint: str
    comfyui_version: str | None
    python_version: str | None
    model_resolution_digest_sha256: str
    model_resolution_evidence_json: str
    instance_digest_sha256: str
    prompt_digest_sha256: str
    parameter_values: tuple[tuple[str, Any], ...]
    input_bindings: tuple[tuple[str, Any], ...]
    seed_values: tuple[tuple[str, int], ...]
    required_output_node_ids: tuple[str, ...]
    submission_attempts: int
    submission_response_digest_sha256: str | None
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

    def model_resolution_evidence(self) -> dict[str, Any]:
        value = json.loads(self.model_resolution_evidence_json)
        if not isinstance(value, dict):
            raise ComfyProtocolError("Run manifest model resolution evidence must be an object")
        return value

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "revision": self.revision,
            "previous_manifest_digest_sha256": self.previous_manifest_digest_sha256,
            "prompt_id": self.prompt_id,
            "client_id": self.client_id,
            "state": self.state.value,
            "submission_outcome": self.submission_outcome.value,
            "definition_id": self.definition_id,
            "definition_digest_sha256": self.definition_digest_sha256,
            "capability_identity_sha256": self.capability_identity_sha256,
            "capability_endpoint": self.capability_endpoint,
            "comfyui_version": self.comfyui_version,
            "python_version": self.python_version,
            "model_resolution_digest_sha256": self.model_resolution_digest_sha256,
            "model_resolution_evidence": self.model_resolution_evidence(),
            "instance_digest_sha256": self.instance_digest_sha256,
            "prompt_digest_sha256": self.prompt_digest_sha256,
            "parameter_values": {key: value for key, value in self.parameter_values},
            "input_bindings": {key: value for key, value in self.input_bindings},
            "seed_values": {key: value for key, value in self.seed_values},
            "required_output_node_ids": list(self.required_output_node_ids),
            "submission_attempts": self.submission_attempts,
            "submission_response_digest_sha256": self.submission_response_digest_sha256,
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
    """Atomic current pointer plus immutable append-only manifest revisions."""

    def __init__(self, root: Path | str) -> None:
        raw_root = Path(root)
        if raw_root.exists() and raw_root.is_symlink():
            raise ComfyProtocolError("Comfy run store root must not be a symlink")
        raw_root.mkdir(parents=True, exist_ok=True)
        self.root = raw_root.resolve()
        self.revision_root = self.root / ".revisions"
        if self.revision_root.exists() and self.revision_root.is_symlink():
            raise ComfyProtocolError("Comfy run revision root must not be a symlink")
        self.revision_root.mkdir(parents=True, exist_ok=True)

    def save(self, manifest: ComfyRunManifest) -> Path:
        _validate_manifest(manifest)
        current_path = self._current_path(manifest.run_id)
        existing: ComfyRunManifest | None = None
        if current_path.exists():
            if current_path.is_symlink():
                raise ComfyProtocolError("Comfy run current manifest path must not be a symlink")
            existing = self._read_manifest(current_path)
            if existing.manifest_digest_sha256 == manifest.manifest_digest_sha256:
                return current_path
            if manifest.revision != existing.revision + 1:
                raise ComfyProtocolError("Comfy run manifest revision is not append-only")
            if manifest.previous_manifest_digest_sha256 != existing.manifest_digest_sha256:
                raise ComfyProtocolError("Comfy run manifest previous digest does not match current head")
        elif manifest.revision != 0 or manifest.previous_manifest_digest_sha256 is not None:
            raise ComfyProtocolError("Initial Comfy run manifest must start at revision zero")

        revision_dir = self._revision_dir(manifest.run_id)
        if revision_dir.exists() and revision_dir.is_symlink():
            raise ComfyProtocolError("Comfy run revision directory must not be a symlink")
        revision_dir.mkdir(parents=True, exist_ok=True)
        revision_name = f"{manifest.revision:08d}-{manifest.manifest_digest_sha256}.json"
        revision_path = (revision_dir / revision_name).resolve(strict=False)
        if not revision_path.is_relative_to(revision_dir.resolve()):
            raise ComfyProtocolError("Comfy run revision path escapes its root")
        data = canonical_json_bytes(manifest.envelope())
        if revision_path.exists():
            if revision_path.is_symlink() or revision_path.read_bytes() != data:
                raise ComfyProtocolError("Existing Comfy run revision conflicts with immutable evidence")
        else:
            with revision_path.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        self._write_current(manifest, current_path)
        return current_path

    def load(self, run_id: str) -> ComfyRunManifest:
        path = self._current_path(run_id)
        if path.is_symlink():
            raise ComfyProtocolError("Comfy run current manifest path must not be a symlink")
        try:
            return self._read_manifest(path)
        except FileNotFoundError as exc:
            raise KeyError(f"Unknown Comfy run: {run_id}") from exc

    def revisions(self, run_id: str) -> tuple[ComfyRunManifest, ...]:
        revision_dir = self._revision_dir(run_id)
        if revision_dir.is_symlink():
            raise ComfyProtocolError("Comfy run revision directory must not be a symlink")
        try:
            entries = sorted(revision_dir.iterdir(), key=lambda item: item.name)
        except FileNotFoundError as exc:
            raise KeyError(f"Unknown Comfy run revisions: {run_id}") from exc
        if len(entries) > _MAX_MANIFEST_REVISIONS:
            raise ComfyProtocolError("Comfy run revision count exceeds accepted bound")
        manifests: list[ComfyRunManifest] = []
        previous: ComfyRunManifest | None = None
        for entry in entries:
            if entry.is_symlink() or not entry.is_file():
                raise ComfyProtocolError("Comfy run revision store contains an unsafe entry")
            manifest = self._read_manifest(entry)
            expected_name = f"{manifest.revision:08d}-{manifest.manifest_digest_sha256}.json"
            if entry.name != expected_name:
                raise ComfyProtocolError("Comfy run revision filename does not match manifest evidence")
            if previous is None:
                if manifest.revision != 0 or manifest.previous_manifest_digest_sha256 is not None:
                    raise ComfyProtocolError("Comfy run revision chain does not start at zero")
            else:
                if manifest.revision != previous.revision + 1:
                    raise ComfyProtocolError("Comfy run revision chain contains a gap")
                if manifest.previous_manifest_digest_sha256 != previous.manifest_digest_sha256:
                    raise ComfyProtocolError("Comfy run revision chain digest is broken")
            manifests.append(manifest)
            previous = manifest
        if not manifests:
            raise KeyError(f"Unknown Comfy run revisions: {run_id}")
        return tuple(manifests)

    def recover(self, run_id: str) -> ComfyRunManifest:
        latest = self.revisions(run_id)[-1]
        self._write_current(latest, self._current_path(run_id))
        return latest

    def _write_current(self, manifest: ComfyRunManifest, path: Path) -> None:
        temp = self.root / f".{manifest.run_id}.{uuid.uuid4().hex}.tmp"
        data = canonical_json_bytes(manifest.envelope())
        try:
            with temp.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            if temp.is_symlink():
                raise ComfyProtocolError("Comfy run manifest staging path became a symlink")
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)

    def _read_manifest(self, path: Path) -> ComfyRunManifest:
        raw = path.read_bytes()
        if len(raw) > 16 * 1024 * 1024:
            raise ComfyProtocolError("Comfy run manifest exceeds accepted byte bound")
        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ComfyProtocolError("Comfy run manifest is invalid JSON") from exc
        if not isinstance(document, dict):
            raise ComfyProtocolError("Comfy run manifest root must be an object")
        payload = parse_envelope(document, expected_schema=_RUN_SCHEMA)
        manifest = _manifest_from_payload(payload)
        _validate_manifest(manifest)
        return manifest

    def _current_path(self, run_id: str) -> Path:
        safe = _safe_run_id(run_id)
        path = (self.root / f"{safe}.json").resolve(strict=False)
        if not path.is_relative_to(self.root):
            raise ComfyProtocolError("Comfy run current manifest path escapes store root")
        return path

    def _revision_dir(self, run_id: str) -> Path:
        safe = _safe_run_id(run_id)
        path = (self.revision_root / safe).resolve(strict=False)
        if not path.is_relative_to(self.revision_root.resolve()):
            raise ComfyProtocolError("Comfy run revision directory escapes store root")
        return path


class ComfyExecutionService:
    """Exactly-one POST per logical run with poll-authoritative terminal reconciliation."""

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
        required_output_node_ids: tuple[str, ...] | None = None,
    ) -> ComfyRunManifest:
        self._verify_preflight(definition, snapshot, resolutions, instance)
        required = _required_output_nodes(
            tuple(sorted({item.node_id for item in definition.output_slots}))
            if required_output_node_ids is None
            else required_output_node_ids
        )
        run_id = f"run_{uuid.uuid4().hex}"
        prompt_id = f"kp_{uuid.uuid4().hex}"
        client_id = f"kc_{uuid.uuid4().hex}"
        model_evidence = canonical_json_bytes(resolutions.canonical_without_digest()).decode("utf-8")
        seeds = _seed_values(definition, instance)
        manifest = _seal(
            ComfyRunManifest(
                run_id=run_id,
                revision=0,
                previous_manifest_digest_sha256=None,
                prompt_id=prompt_id,
                client_id=client_id,
                state=ComfyRunState.PREPARED,
                submission_outcome=ComfySubmissionOutcome.NOT_ATTEMPTED,
                definition_id=definition.definition_id,
                definition_digest_sha256=definition.definition_digest_sha256,
                capability_identity_sha256=snapshot.identity_sha256,
                capability_endpoint=snapshot.endpoint,
                comfyui_version=snapshot.comfyui_version,
                python_version=snapshot.python_version,
                model_resolution_digest_sha256=resolutions.digest_sha256,
                model_resolution_evidence_json=model_evidence,
                instance_digest_sha256=instance.instance_digest_sha256,
                prompt_digest_sha256=canonical_sha256(instance.prompt()),
                parameter_values=tuple(instance.parameter_values),
                input_bindings=tuple(instance.input_bindings),
                seed_values=seeds,
                required_output_node_ids=required,
                submission_attempts=0,
                submission_response_digest_sha256=None,
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
        if manifest.terminal or manifest.state is not ComfyRunState.PREPARED:
            return manifest
        if cancel_event is not None and cancel_event.is_set():
            return self._persist_transition(manifest, ComfyRunState.CANCELLED)
        if manifest.submission_outcome in {ComfySubmissionOutcome.ATTEMPTING, ComfySubmissionOutcome.AMBIGUOUS}:
            return self._reconcile_ambiguous_or_raise(manifest, instance, limits, cancel_event)
        if manifest.submission_outcome in {ComfySubmissionOutcome.ACCEPTED, ComfySubmissionOutcome.RECOVERED}:
            return self._advance_to_queued(manifest)
        if manifest.submission_attempts != 0:
            raise ComfyProtocolError("Prepared run has inconsistent submission attempt evidence")

        attempting = _evolve(
            manifest,
            submission_attempts=1,
            submission_outcome=ComfySubmissionOutcome.ATTEMPTING,
        )
        self.store.save(attempting)
        try:
            response = self.client.submit_prompt(
                instance.prompt(),
                prompt_id=attempting.prompt_id,
                client_id=attempting.client_id,
                correlation=attempting.correlation(),
            )
        except ComfySubmissionAmbiguousError:
            ambiguous = _evolve(attempting, submission_outcome=ComfySubmissionOutcome.AMBIGUOUS)
            self.store.save(ambiguous)
            return self._reconcile_ambiguous_or_raise(ambiguous, instance, limits, cancel_event)
        except ComfyUnavailableError as exc:
            ambiguous = _evolve(attempting, submission_outcome=ComfySubmissionOutcome.AMBIGUOUS)
            self.store.save(ambiguous)
            raise ComfySubmissionAmbiguousError(
                "Prompt POST could not be proven side-effect free; automatic resubmission is forbidden"
            ) from exc

        accepted = _evolve(
            attempting,
            submission_outcome=ComfySubmissionOutcome.ACCEPTED,
            submission_response_digest_sha256=response.response_digest_sha256,
        )
        self.store.save(accepted)
        return self._advance_to_queued(accepted)

    def reconcile_once(self, run_id: str, instance: WorkflowInstance) -> ComfyRunManifest:
        manifest = self.store.load(run_id)
        self._verify_instance_binding(manifest, instance)
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

        current = _update_if_changed(manifest, self.store, queue_digest_sha256=queue.digest_sha256)
        if history.present:
            current = self._mark_recovered_if_needed(current)
            current = self._validate_history(current, history)
            if is_terminal_run_state(history.state):
                return self._apply_terminal_history(current, history)
            if history.state is ComfyRunState.RUNNING:
                return self._advance_to_running(current)
        if in_running:
            current = self._mark_recovered_if_needed(current)
            return self._advance_to_running(current)
        if in_pending:
            current = self._mark_recovered_if_needed(current)
            return self._advance_to_queued(current)
        if current.submission_outcome is ComfySubmissionOutcome.ATTEMPTING:
            current = _evolve(current, submission_outcome=ComfySubmissionOutcome.AMBIGUOUS)
            self.store.save(current)
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
        active_types = {
            "execution_start",
            "executing",
            "progress",
            "executed",
            "execution_cached",
            "progress_state",
            "progress_text",
        }
        current = manifest
        if event.prompt_id == manifest.prompt_id and event.event_type.value in active_types:
            current = self._mark_recovered_if_needed(current)
            current = self._advance_to_running(current)
        fraction = event.progress_fraction
        if fraction is not None:
            progress = current.progress_fraction
            normalized = fraction if progress is None else max(progress, fraction)
            current = _update_if_changed(current, self.store, progress_fraction=normalized)
        return current

    def _reconcile_ambiguous_or_raise(
        self,
        manifest: ComfyRunManifest,
        instance: WorkflowInstance,
        budget: ComfyExecutionBudget,
        cancel_event: threading.Event | None,
    ) -> ComfyRunManifest:
        current = manifest
        started = time.monotonic()
        for index in range(budget.ambiguous_reconcile_attempts):
            if cancel_event is not None and cancel_event.is_set():
                break
            current = self.reconcile_once(current.run_id, instance)
            if current.state is not ComfyRunState.PREPARED or current.submission_outcome is ComfySubmissionOutcome.RECOVERED:
                return current
            if time.monotonic() - started >= budget.max_wait_seconds:
                break
            if index + 1 < budget.ambiguous_reconcile_attempts and budget.ambiguous_reconcile_interval_seconds:
                if cancel_event is not None:
                    if cancel_event.wait(budget.ambiguous_reconcile_interval_seconds):
                        break
                else:
                    time.sleep(budget.ambiguous_reconcile_interval_seconds)
        raise ComfySubmissionAmbiguousError(
            "Prompt submission remains ambiguous after bounded idempotent queue/history reconciliation; resubmission is forbidden"
        )

    def _validate_history(self, manifest: ComfyRunManifest, history: ComfyExecutionHistory) -> ComfyRunManifest:
        if history.prompt_id != manifest.prompt_id:
            raise ComfyProtocolError("History prompt_id does not match run manifest")
        if history.prompt_digest_sha256 != manifest.prompt_digest_sha256:
            raise ComfyProtocolError("History prompt digest does not match submitted workflow instance")
        correlation = dict(history.correlation)
        for key, expected in manifest.correlation().items():
            if correlation.get(key) != expected:
                raise ComfyProtocolError("History correlation metadata does not match run manifest")
        return _update_if_changed(manifest, self.store, history_digest_sha256=history.digest_sha256)

    def _apply_terminal_history(self, manifest: ComfyRunManifest, history: ComfyExecutionHistory) -> ComfyRunManifest:
        if history.state is ComfyRunState.SUCCEEDED:
            available_nodes = {item.node_id for item in history.output_references}
            missing = set(manifest.required_output_node_ids) - available_nodes
            if missing:
                raise ComfyProtocolError(
                    f"ComfyUI success history is missing required output references: {sorted(missing)!r}"
                )
            current = self._advance_to_running(manifest)
            current = _update_if_changed(
                current,
                self.store,
                output_references=history.output_references,
                progress_fraction=1.0,
            )
            return self._persist_transition(current, ComfyRunState.SUCCEEDED)
        if history.state in {ComfyRunState.FAILED, ComfyRunState.CANCELLED}:
            return self._persist_transition(manifest, history.state)
        raise ComfyProtocolError("Non-terminal history cannot be applied as terminal evidence")

    def _mark_recovered_if_needed(self, manifest: ComfyRunManifest) -> ComfyRunManifest:
        if manifest.submission_outcome not in {ComfySubmissionOutcome.ATTEMPTING, ComfySubmissionOutcome.AMBIGUOUS}:
            return manifest
        updated = _evolve(manifest, submission_outcome=ComfySubmissionOutcome.RECOVERED)
        self.store.save(updated)
        return updated

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
        if manifest.state is state:
            return manifest
        if not can_transition_run_state(manifest.state, state):
            raise ComfyProtocolError(
                f"Impossible run manifest transition: {manifest.state.value} -> {state.value}"
            )
        updated = _evolve(manifest, state=state)
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
        if resolutions.capability_identity_sha256 != snapshot.identity_sha256:
            raise ComfyGovernanceError("Model resolutions were produced against a different capability snapshot")
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
            "capability_endpoint": snapshot.endpoint,
            "comfyui_version": snapshot.comfyui_version,
            "python_version": snapshot.python_version,
            "model_resolution_digest_sha256": resolutions.digest_sha256,
            "model_resolution_evidence_json": canonical_json_bytes(resolutions.canonical_without_digest()).decode("utf-8"),
            "instance_digest_sha256": instance.instance_digest_sha256,
            "prompt_digest_sha256": canonical_sha256(instance.prompt()),
            "parameter_values": tuple(instance.parameter_values),
            "input_bindings": tuple(instance.input_bindings),
            "seed_values": _seed_values(definition, instance),
        }
        for field_name, value in expected.items():
            if getattr(manifest, field_name) != value:
                raise ComfyGovernanceError(f"Run manifest {field_name} does not match current execution evidence")

    @staticmethod
    def _verify_instance_binding(manifest: ComfyRunManifest, instance: WorkflowInstance) -> None:
        if manifest.instance_digest_sha256 != instance.instance_digest_sha256:
            raise ComfyGovernanceError("Run manifest is bound to a different workflow instance")
        if canonical_sha256(instance.prompt()) != manifest.prompt_digest_sha256:
            raise ComfyGovernanceError("Workflow instance prompt changed after run preparation")
        if tuple(instance.parameter_values) != manifest.parameter_values or tuple(instance.input_bindings) != manifest.input_bindings:
            raise ComfyGovernanceError("Workflow instance audit values changed after run preparation")


def _instance_digest(instance: WorkflowInstance) -> str:
    payload = instance.canonical()
    payload.pop("instance_digest_sha256", None)
    return canonical_sha256(payload)


def _seed_values(definition: WorkflowDefinition, instance: WorkflowInstance) -> tuple[tuple[str, int], ...]:
    values = dict(instance.parameter_values)
    seeds: list[tuple[str, int]] = []
    for spec in definition.parameters:
        if spec.kind is WorkflowParameterKind.SEED:
            value = values.get(spec.name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ComfyGovernanceError("Workflow seed evidence is invalid")
            seeds.append((spec.name, value))
    return tuple(sorted(seeds))


def _required_output_nodes(values: tuple[str, ...]) -> tuple[str, ...]:
    if len(values) > _MAX_REQUIRED_OUTPUTS:
        raise ValueError("required output node count exceeds accepted bound")
    result: list[str] = []
    for value in values:
        result.append(_safe_text(value, "required output node ID", 128))
    if len(set(result)) != len(result):
        raise ValueError("required output node IDs must be unique")
    return tuple(sorted(result))


def _safe_run_id(value: str) -> str:
    if not isinstance(value, str) or not _SAFE_RUN_RE.fullmatch(value):
        raise ValueError("run_id must be a generated R9.5 run identifier")
    return value


def _safe_text(value: Any, field_name: str, maximum: int, *, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or not value or len(value) > maximum or _CONTROL_RE.search(value):
        raise ComfyProtocolError(f"{field_name} must be a non-empty bounded string without controls")
    return value


def _safe_digest(value: Any, field_name: str, *, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or not _HEX64_RE.fullmatch(value):
        raise ComfyProtocolError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _safe_scalar(value: Any, field_name: str) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        return _safe_text(value, field_name, _MAX_AUDIT_TEXT)
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise ComfyProtocolError(f"{field_name} must be a finite JSON scalar")


def _safe_scalar_pairs(values: tuple[tuple[str, Any], ...], field_name: str) -> tuple[tuple[str, Any], ...]:
    if len(values) > _MAX_AUDIT_FIELDS:
        raise ComfyProtocolError(f"{field_name} exceeds accepted field bound")
    result: list[tuple[str, Any]] = []
    for item in values:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ComfyProtocolError(f"{field_name} entries must be key/value pairs")
        key, value = item
        normalized_key = _safe_text(key, f"{field_name} key", 128)
        result.append((normalized_key, _safe_scalar(value, f"{field_name} value")))
    result.sort(key=lambda item: item[0])
    if len({key for key, _ in result}) != len(result):
        raise ComfyProtocolError(f"{field_name} keys must be unique")
    return tuple(result)


def _seal(manifest: ComfyRunManifest) -> ComfyRunManifest:
    _safe_run_id(manifest.run_id)
    if not _SAFE_PROMPT_RE.fullmatch(manifest.prompt_id):
        raise ComfyProtocolError("Run manifest prompt_id is invalid")
    if not _SAFE_CLIENT_RE.fullmatch(manifest.client_id):
        raise ComfyProtocolError("Run manifest client_id is invalid")
    if not _SAFE_WORKFLOW_RE.fullmatch(manifest.definition_id):
        raise ComfyProtocolError("Run manifest definition_id is invalid")
    if isinstance(manifest.revision, bool) or not isinstance(manifest.revision, int) or manifest.revision < 0:
        raise ComfyProtocolError("Run manifest revision is invalid")
    if manifest.revision == 0 and manifest.previous_manifest_digest_sha256 is not None:
        raise ComfyProtocolError("Initial run manifest cannot have a previous digest")
    if manifest.revision > 0:
        _safe_digest(manifest.previous_manifest_digest_sha256, "previous manifest digest")
    for field_name in (
        "definition_digest_sha256",
        "capability_identity_sha256",
        "model_resolution_digest_sha256",
        "instance_digest_sha256",
        "prompt_digest_sha256",
    ):
        _safe_digest(getattr(manifest, field_name), field_name)
    for field_name in ("submission_response_digest_sha256", "queue_digest_sha256", "history_digest_sha256"):
        _safe_digest(getattr(manifest, field_name), field_name, allow_none=True)
    _safe_text(manifest.capability_endpoint, "capability endpoint", 2048)
    _safe_text(manifest.comfyui_version, "ComfyUI version", 256, allow_none=True)
    _safe_text(manifest.python_version, "Python version", 1024, allow_none=True)
    try:
        model_evidence = json.loads(manifest.model_resolution_evidence_json)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ComfyProtocolError("Run manifest model resolution evidence is invalid JSON") from exc
    if not isinstance(model_evidence, dict):
        raise ComfyProtocolError("Run manifest model resolution evidence must be an object")
    canonical_model_json = canonical_json_bytes(model_evidence).decode("utf-8")
    if canonical_model_json != manifest.model_resolution_evidence_json:
        raise ComfyProtocolError("Run manifest model resolution evidence must be canonical JSON")
    if canonical_sha256(model_evidence) != manifest.model_resolution_digest_sha256:
        raise ComfyProtocolError("Run manifest model resolution evidence digest does not match")
    parameter_values = _safe_scalar_pairs(tuple(manifest.parameter_values), "parameter values")
    input_bindings = _safe_scalar_pairs(tuple(manifest.input_bindings), "input bindings")
    seed_values_raw = _safe_scalar_pairs(tuple(manifest.seed_values), "seed values")
    seed_values: list[tuple[str, int]] = []
    for key, value in seed_values_raw:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ComfyProtocolError("Run manifest seed values must be non-negative integers")
        seed_values.append((key, value))
    required = _required_output_nodes(tuple(manifest.required_output_node_ids))
    if isinstance(manifest.submission_attempts, bool) or manifest.submission_attempts not in {0, 1}:
        raise ComfyProtocolError("Run manifest submission_attempts must be 0 or 1")
    if manifest.submission_attempts == 0 and manifest.submission_outcome is not ComfySubmissionOutcome.NOT_ATTEMPTED:
        raise ComfyProtocolError("Run manifest has submission outcome without an attempted POST")
    if manifest.submission_attempts == 1 and manifest.submission_outcome is ComfySubmissionOutcome.NOT_ATTEMPTED:
        raise ComfyProtocolError("Run manifest attempted POST has missing submission outcome")
    if manifest.state in {ComfyRunState.QUEUED, ComfyRunState.RUNNING, ComfyRunState.SUCCEEDED, ComfyRunState.FAILED} and manifest.submission_attempts != 1:
        raise ComfyProtocolError("Submitted run state requires exactly one POST attempt")
    if manifest.progress_fraction is not None:
        if not isinstance(manifest.progress_fraction, (int, float)) or isinstance(manifest.progress_fraction, bool):
            raise ComfyProtocolError("Run manifest progress_fraction must be numeric")
        if not math.isfinite(float(manifest.progress_fraction)) or not 0.0 <= float(manifest.progress_fraction) <= 1.0:
            raise ComfyProtocolError("Run manifest progress_fraction is invalid")
    if len(manifest.output_references) > _MAX_OUTPUT_REFS:
        raise ComfyProtocolError("Run manifest output reference count exceeds accepted bound")
    for reference in manifest.output_references:
        if reference.prompt_id != manifest.prompt_id:
            raise ComfyProtocolError("Run manifest output reference belongs to a different prompt")
    normalized = replace(
        manifest,
        parameter_values=parameter_values,
        input_bindings=input_bindings,
        seed_values=tuple(seed_values),
        required_output_node_ids=required,
        manifest_digest_sha256="",
    )
    return replace(normalized, manifest_digest_sha256=canonical_sha256(normalized.canonical_without_digest()))


def _validate_manifest(manifest: ComfyRunManifest) -> None:
    sealed = _seal(manifest)
    if sealed.manifest_digest_sha256 != manifest.manifest_digest_sha256:
        raise ComfyProtocolError("Comfy run manifest digest does not match canonical evidence")


def _evolve(manifest: ComfyRunManifest, **changes: Any) -> ComfyRunManifest:
    draft = replace(
        manifest,
        revision=manifest.revision + 1,
        previous_manifest_digest_sha256=manifest.manifest_digest_sha256,
        manifest_digest_sha256="",
        **changes,
    )
    return _seal(draft)


def _update_if_changed(manifest: ComfyRunManifest, store: ComfyRunStore, **changes: Any) -> ComfyRunManifest:
    if all(getattr(manifest, key) == value for key, value in changes.items()):
        return manifest
    updated = _evolve(manifest, **changes)
    store.save(updated)
    return updated


def _manifest_from_payload(payload: dict[str, Any]) -> ComfyRunManifest:
    expected = {
        "run_id",
        "revision",
        "previous_manifest_digest_sha256",
        "prompt_id",
        "client_id",
        "state",
        "submission_outcome",
        "definition_id",
        "definition_digest_sha256",
        "capability_identity_sha256",
        "capability_endpoint",
        "comfyui_version",
        "python_version",
        "model_resolution_digest_sha256",
        "model_resolution_evidence",
        "instance_digest_sha256",
        "prompt_digest_sha256",
        "parameter_values",
        "input_bindings",
        "seed_values",
        "required_output_node_ids",
        "submission_attempts",
        "submission_response_digest_sha256",
        "progress_fraction",
        "queue_digest_sha256",
        "history_digest_sha256",
        "output_references",
        "manifest_digest_sha256",
    }
    if set(payload) != expected:
        raise ComfyProtocolError("Comfy run manifest payload fields are invalid")
    try:
        state = ComfyRunState(payload["state"])
        submission_outcome = ComfySubmissionOutcome(payload["submission_outcome"])
    except (TypeError, ValueError) as exc:
        raise ComfyProtocolError("Comfy run manifest state/outcome is invalid") from exc
    model_evidence = payload["model_resolution_evidence"]
    parameter_values = payload["parameter_values"]
    input_bindings = payload["input_bindings"]
    seed_values = payload["seed_values"]
    required = payload["required_output_node_ids"]
    refs = payload["output_references"]
    if not isinstance(model_evidence, dict):
        raise ComfyProtocolError("Comfy run model resolution evidence has invalid shape")
    if not isinstance(parameter_values, dict) or not isinstance(input_bindings, dict) or not isinstance(seed_values, dict):
        raise ComfyProtocolError("Comfy run audit maps have invalid shape")
    if not isinstance(required, list) or not isinstance(refs, list):
        raise ComfyProtocolError("Comfy run manifest arrays have invalid shape")
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
        revision=payload["revision"],
        previous_manifest_digest_sha256=payload["previous_manifest_digest_sha256"],
        prompt_id=payload["prompt_id"],
        client_id=payload["client_id"],
        state=state,
        submission_outcome=submission_outcome,
        definition_id=payload["definition_id"],
        definition_digest_sha256=payload["definition_digest_sha256"],
        capability_identity_sha256=payload["capability_identity_sha256"],
        capability_endpoint=payload["capability_endpoint"],
        comfyui_version=payload["comfyui_version"],
        python_version=payload["python_version"],
        model_resolution_digest_sha256=payload["model_resolution_digest_sha256"],
        model_resolution_evidence_json=canonical_json_bytes(model_evidence).decode("utf-8"),
        instance_digest_sha256=payload["instance_digest_sha256"],
        prompt_digest_sha256=payload["prompt_digest_sha256"],
        parameter_values=tuple(parameter_values.items()),
        input_bindings=tuple(input_bindings.items()),
        seed_values=tuple(seed_values.items()),
        required_output_node_ids=tuple(required),
        submission_attempts=payload["submission_attempts"],
        submission_response_digest_sha256=payload["submission_response_digest_sha256"],
        progress_fraction=payload["progress_fraction"],
        queue_digest_sha256=payload["queue_digest_sha256"],
        history_digest_sha256=payload["history_digest_sha256"],
        output_references=tuple(output_references),
        manifest_digest_sha256=payload["manifest_digest_sha256"],
    )
    _validate_manifest(manifest)
    return manifest
