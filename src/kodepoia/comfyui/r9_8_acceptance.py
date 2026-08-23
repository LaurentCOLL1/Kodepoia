from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

from kodepoia.assets.vcs import AssetVcsService, VcsFileState
from kodepoia.brain.ollama import OllamaClient
from kodepoia.core.audit import AuditLog
from kodepoia.kodecode.workspace import WorkspaceBoundary

from .client import ComfyUIClient
from .contracts import ComfyCapabilityState, ComfyRunState
from .errors import ComfyGovernanceError, ComfyProtocolError
from .execution import ComfyExecutionBudget, ComfyExecutionService, ComfyRunStore
from .inventory import ComfyCapabilityInventory
from .lifecycle import ComfyLifecycleAuditStore, ComfyLifecycleService
from .resources import (
    ComfyVramTelemetryAdapter,
    GpuAdmissionDecision,
    GpuResourceCoordinator,
    GpuResourceProfile,
    OllamaCoexistenceState,
    OllamaMemoryAdapter,
    WorkflowMemoryObservation,
)
from .serialization import canonical_sha256, make_envelope, parse_envelope
from .workflow import (
    GovernedModelResolver,
    WorkflowCatalog,
    WorkflowValidator,
    _safe_model_token,
)

_EVIDENCE_SCHEMA = "kodepoia.comfy-vram-evidence"
_EVIDENCE_VERSION = 1
_MAX_EVIDENCE_BYTES = 16 * 1024 * 1024
_MAX_R98_MODELS_PER_TYPE = 250_000
_MIB = 1024 * 1024


class _R98WorkflowCapabilityInventory(ComfyCapabilityInventory):
    """Strict R9.3 inventory scoped to one governed R9.4 workflow.

    ComfyUI's discovery routes are global. Unrelated custom nodes or model files may
    expose malformed metadata/tokens, especially OS-native path separators on Windows.
    R9.8 therefore narrows discovery before applying the unchanged strict R9.3
    normalizers: only node classes used by the governed graph and only exact model
    tokens declared by its requirements (or explicitly selected) are considered.
    Anything actually used by the workflow remains strict and fail-closed.
    """

    def __init__(
        self,
        client: ComfyUIClient,
        node_classes: tuple[str, ...],
        model_targets: Mapping[str, tuple[str, ...]] | None = None,
    ) -> None:
        super().__init__(client)
        if not node_classes:
            raise ComfyGovernanceError("R9.8 workflow must contain at least one node class")
        self._node_classes = frozenset(node_classes)
        targets: dict[str, frozenset[str]] = {}
        for model_type, tokens in (model_targets or {}).items():
            if not isinstance(model_type, str) or not model_type:
                raise ComfyGovernanceError("R9.8 model target type must be a non-empty string")
            normalized = frozenset(_safe_model_token(token) for token in tokens)
            if normalized:
                targets[model_type] = normalized
        self._model_targets = targets

    def _object_info(self) -> dict[str, Any]:
        raw = super()._object_info()
        return {
            class_type: raw[class_type]
            for class_type in sorted(self._node_classes)
            if class_type in raw
        }

    def _model_types(self) -> tuple[str, ...]:
        available = super()._model_types()
        return tuple(item for item in available if item in self._model_targets)

    def _models(self, model_type: str) -> tuple[str, ...]:
        targets = self._model_targets.get(model_type)
        if not targets:
            return ()
        raw = self.client._http.get_json_value(f"/models/{quote(model_type, safe='')}")
        if not isinstance(raw, list) or len(raw) > _MAX_R98_MODELS_PER_TYPE:
            raise ComfyProtocolError("ComfyUI targeted model inventory must be a bounded array")
        selected = tuple(
            sorted(
                item
                for item in raw
                if isinstance(item, str) and item in targets
            )
        )
        if len(set(selected)) != len(selected):
            raise ComfyProtocolError(
                f"ComfyUI targeted model inventory {model_type!r} contains duplicate tokens"
            )
        return selected


@dataclass(frozen=True, slots=True)
class R98LocalAcceptanceEvidence:
    candidate_head: str
    status: str
    endpoint: str
    capability_identity_sha256: str | None
    comfyui_version: str | None
    device: dict[str, Any] | None
    resource_profile: dict[str, Any]
    scheduler_trace: dict[str, Any] | None
    workflow_definition_id: str | None
    workflow_instance_digest_sha256: str | None
    run_id: str | None
    run_manifest_digest_sha256: str | None
    output_sha256: str | None
    output_length: int | None
    memory_observation: dict[str, Any] | None
    terminal_cleanup: dict[str, Any] | None
    ollama_state: str
    ollama_reason: str
    ollama_restored: tuple[str, ...]
    resource_audit_relative_path: str
    resource_audit_valid: bool
    lifecycle_audit_valid: bool
    failure_reason: str | None
    evidence_digest_sha256: str

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "candidate_head": self.candidate_head,
            "status": self.status,
            "endpoint": self.endpoint,
            "capability_identity_sha256": self.capability_identity_sha256,
            "comfyui_version": self.comfyui_version,
            "device": self.device,
            "resource_profile": self.resource_profile,
            "scheduler_trace": self.scheduler_trace,
            "workflow_definition_id": self.workflow_definition_id,
            "workflow_instance_digest_sha256": self.workflow_instance_digest_sha256,
            "run_id": self.run_id,
            "run_manifest_digest_sha256": self.run_manifest_digest_sha256,
            "output_sha256": self.output_sha256,
            "output_length": self.output_length,
            "memory_observation": self.memory_observation,
            "terminal_cleanup": self.terminal_cleanup,
            "ollama_state": self.ollama_state,
            "ollama_reason": self.ollama_reason,
            "ollama_restored": list(self.ollama_restored),
            "resource_audit_relative_path": self.resource_audit_relative_path,
            "resource_audit_valid": self.resource_audit_valid,
            "lifecycle_audit_valid": self.lifecycle_audit_valid,
            "failure_reason": self.failure_reason,
        }

    def payload(self) -> dict[str, Any]:
        return {
            **self.canonical_without_digest(),
            "evidence_digest_sha256": self.evidence_digest_sha256,
        }

    def envelope(self) -> dict[str, Any]:
        return make_envelope(
            schema=_EVIDENCE_SCHEMA,
            version=_EVIDENCE_VERSION,
            payload=self.payload(),
        )


@dataclass(frozen=True, slots=True)
class R98AcceptanceRequest:
    candidate_head: str
    endpoint: str
    workflow_root: Path
    workflow_file: str
    model_selections: tuple[tuple[str, str], ...]
    parameters: tuple[tuple[str, Any], ...]
    input_bindings: tuple[tuple[str, Any], ...]
    estimate_mib: int
    reserve_mib: int
    headroom_mib: int
    total_limit_mib: int | None
    device_index: int
    ollama_url: str
    approved_ollama_unloads: tuple[str, ...]
    restore_ollama: bool
    max_wait_seconds: float
    poll_interval_seconds: float

    def profile(self) -> GpuResourceProfile:
        return GpuResourceProfile(
            estimate_bytes=_mib(self.estimate_mib, "estimate_mib"),
            reserve_bytes=_mib(self.reserve_mib, "reserve_mib"),
            headroom_bytes=_mib(self.headroom_mib, "headroom_mib"),
            device_index=self.device_index,
            total_limit_bytes=(
                None
                if self.total_limit_mib is None
                else _mib(self.total_limit_mib, "total_limit_mib")
            ),
        )


class R98LocalAcceptance:
    """Authoritative local R9.8 gate over one explicit R9.4 workflow on one exact Git head."""

    def __init__(self, workspace: Path | str) -> None:
        self.root = Path(workspace).resolve(strict=False)
        self.boundary = WorkspaceBoundary(self.root)

    def run(self, request: R98AcceptanceRequest) -> R98LocalAcceptanceEvidence:
        self._verify_repository(request.candidate_head)
        workflow_root = self._confined_existing_dir(request.workflow_root)
        profile = request.profile()

        catalog = WorkflowCatalog.load_files(workflow_root, (request.workflow_file,))
        definitions = catalog.definitions()
        if len(definitions) != 1:
            raise ComfyGovernanceError("R9.8 local acceptance requires exactly one explicit workflow")
        definition = definitions[0]
        node_classes = tuple(
            sorted(
                {
                    node["class_type"]
                    for node in definition.graph().values()
                    if isinstance(node, dict) and isinstance(node.get("class_type"), str)
                }
            )
        )
        if len(node_classes) != len({node.get("class_type") for node in definition.graph().values()}):
            raise ComfyGovernanceError("R9.8 governed workflow contains invalid node class metadata")

        selections = _unique_pairs(request.model_selections, "model selection")
        model_target_sets: dict[str, set[str]] = {}
        for requirement in definition.model_requirements:
            targets = set(requirement.accepted_tokens)
            requested = selections.get(requirement.requirement_id)
            if requested is not None:
                targets.add(_safe_model_token(requested))
            if not targets:
                raise ComfyGovernanceError(
                    "R9.8 local acceptance requires accepted_tokens or an explicit --model "
                    f"selection for model requirement {requirement.requirement_id!r}"
                )
            model_target_sets.setdefault(requirement.model_type, set()).update(targets)
        model_targets = {
            model_type: tuple(sorted(tokens))
            for model_type, tokens in sorted(model_target_sets.items())
        }

        client = ComfyUIClient(request.endpoint)
        capability = _R98WorkflowCapabilityInventory(
            client,
            node_classes,
            model_targets,
        ).capture()
        if capability.state is not ComfyCapabilityState.CURRENT:
            raise ComfyGovernanceError(
                f"R9.8 requires a CURRENT ComfyUI capability snapshot, got {capability.state.value}"
            )

        parameters = _unique_pairs(request.parameters, "parameter")
        inputs = _unique_pairs(request.input_bindings, "input binding")
        resolutions = GovernedModelResolver().resolve(
            definition,
            capability,
            selections=selections,
        )
        instance = WorkflowValidator().instantiate(
            definition,
            capability,
            resolutions,
            parameters=parameters,
            input_bindings=inputs,
        )

        evidence_root = self.boundary.resolve(".kodepoia/evidence/r9-8")
        evidence_root.mkdir(parents=True, exist_ok=True)
        run_store = ComfyRunStore(evidence_root / "runs")
        lifecycle_audit = ComfyLifecycleAuditStore(evidence_root / "lifecycle")
        lifecycle = ComfyLifecycleService(client, run_store, lifecycle_audit)
        resource_audit_path = evidence_root / "resource-audit.jsonl"
        resource_audit = AuditLog(resource_audit_path)

        ollama = OllamaMemoryAdapter(OllamaClient(request.ollama_url))
        telemetry = ComfyVramTelemetryAdapter(client)
        coordinator = GpuResourceCoordinator(
            telemetry,
            lifecycle,
            ollama=ollama,
            audit_log=resource_audit,
        )

        ollama_before = ollama.sample()
        ollama_reason = _ollama_reason(ollama_before.state, bool(ollama_before.models))
        trace = coordinator.admit_with_cleanup(
            profile,
            approved_ollama_unloads=request.approved_ollama_unloads,
        )
        if trace.final.decision is not GpuAdmissionDecision.ADMIT:
            raise ComfyGovernanceError(
                f"R9.8 scheduler did not admit the bounded generation: {trace.final.decision.value}"
            )

        execution = ComfyExecutionService(client, run_store)
        manifest = execution.prepare(definition, capability, resolutions, instance)
        budget = ComfyExecutionBudget(
            max_poll_attempts=max(
                2,
                min(
                    10000,
                    int(request.max_wait_seconds / max(request.poll_interval_seconds, 0.01)) + 2,
                ),
            ),
            poll_interval_seconds=0.0,
            max_wait_seconds=request.max_wait_seconds,
            ambiguous_reconcile_attempts=8,
            ambiguous_reconcile_interval_seconds=min(
                0.5,
                max(0.01, request.poll_interval_seconds),
            ),
        )

        memory_samples: list[int] = [
            self._free_bytes(telemetry.sample(), request.device_index)
        ]
        current = execution.submit(
            manifest.run_id,
            definition,
            capability,
            resolutions,
            instance,
            budget=budget,
        )
        started = time.monotonic()
        while not current.terminal and time.monotonic() - started < request.max_wait_seconds:
            if request.poll_interval_seconds:
                time.sleep(request.poll_interval_seconds)
            current = execution.reconcile_once(current.run_id, instance)
            memory_samples.append(self._free_bytes(telemetry.sample(), request.device_index))
        if current.state is not ComfyRunState.SUCCEEDED:
            raise ComfyGovernanceError(
                f"R9.8 bounded generation did not succeed: {current.state.value}"
            )
        if not current.output_references:
            raise ComfyProtocolError("R9.8 successful generation has no output reference")

        first_output = client.retrieve_output(current.output_references[0])
        if not first_output:
            raise ComfyProtocolError("R9.8 generated output is empty")
        output_sha256 = hashlib.sha256(first_output).hexdigest()
        memory_samples.append(self._free_bytes(telemetry.sample(), request.device_index))
        observation = WorkflowMemoryObservation.create(
            definition.definition_id,
            tuple(memory_samples),
            oom_observed=False,
        )

        terminal_cleanup = lifecycle.cleanup_terminal_run(
            current.run_id,
            settle_seconds=min(2.0, max(0.0, request.poll_interval_seconds)),
        )
        after_cleanup = telemetry.sample()
        memory_samples.append(self._free_bytes(after_cleanup, request.device_index))

        restored: tuple[str, ...] = ()
        if request.restore_ollama and trace.ollama_unloaded:
            restored = coordinator.restore_prior_ollama(trace)

        lifecycle_loaded = lifecycle_audit.load(current.run_id)
        lifecycle_valid = bool(lifecycle_loaded.events) and all(
            event.event_digest_sha256 for event in lifecycle_loaded.events
        )
        resource_valid = resource_audit.verify()
        device = after_cleanup.device(request.device_index)
        if device is None:
            raise ComfyProtocolError("R9.8 device disappeared after terminal cleanup")
        if not resource_valid or not lifecycle_valid:
            raise ComfyProtocolError("R9.8 audit chain validation failed")

        return _seal_evidence(
            candidate_head=request.candidate_head,
            status="pass",
            endpoint=client.endpoint.origin,
            capability_identity_sha256=capability.identity_sha256,
            comfyui_version=capability.comfyui_version,
            device=device.canonical(),
            resource_profile=profile.canonical(),
            scheduler_trace=trace.canonical(),
            workflow_definition_id=definition.definition_id,
            workflow_instance_digest_sha256=instance.instance_digest_sha256,
            run_id=current.run_id,
            run_manifest_digest_sha256=current.manifest_digest_sha256,
            output_sha256=output_sha256,
            output_length=len(first_output),
            memory_observation=observation.canonical(),
            terminal_cleanup=terminal_cleanup.canonical(),
            ollama_state=ollama_before.state.value,
            ollama_reason=ollama_reason,
            ollama_restored=restored,
            resource_audit_relative_path=self.boundary.relative(resource_audit_path).replace("\\", "/"),
            resource_audit_valid=resource_valid,
            lifecycle_audit_valid=lifecycle_valid,
            failure_reason=None,
        )

    def _verify_repository(self, expected_head: str) -> None:
        if not _is_sha(expected_head):
            raise ValueError("candidate_head must be a lowercase 40-character Git SHA")
        status = AssetVcsService(self.boundary).repository_status()
        if status.head_sha != expected_head:
            raise ComfyGovernanceError(
                f"R9.8 candidate head mismatch: expected {expected_head}, got {status.head_sha}"
            )
        dirty = tuple(item for item in status.files if item.state is not VcsFileState.IGNORED)
        if dirty:
            raise ComfyGovernanceError(
                "R9.8 local acceptance requires a clean repository worktree/index"
            )

    def _confined_existing_dir(self, requested: Path) -> Path:
        path = requested if requested.is_absolute() else self.root / requested
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(self.root) or not resolved.is_dir() or resolved.is_symlink():
            raise ComfyGovernanceError(
                "R9.8 workflow root must be a non-symlink directory inside the workspace"
            )
        return resolved

    @staticmethod
    def _free_bytes(snapshot: Any, device_index: int) -> int:
        device = snapshot.device(device_index)
        if device is None:
            raise ComfyProtocolError("R9.8 requested device telemetry is unavailable")
        return device.vram_free_bytes


def write_r98_evidence(
    workspace: Path | str,
    output: str,
    evidence: R98LocalAcceptanceEvidence,
) -> Path:
    root = Path(workspace).resolve(strict=False)
    boundary = WorkspaceBoundary(root)
    requested = Path(output)
    if requested.is_absolute():
        raise ComfyGovernanceError("R9.8 evidence output must be workspace-relative")
    destination = boundary.resolve(requested)
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(
        evidence.envelope(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8") + b"\n"
    if len(data) > _MAX_EVIDENCE_BYTES:
        raise ComfyProtocolError("R9.8 evidence exceeds accepted byte bound")
    temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}")
    try:
        temporary.write_bytes(data)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def load_r98_evidence(path: Path | str) -> R98LocalAcceptanceEvidence:
    raw = Path(path).read_bytes()
    if len(raw) > _MAX_EVIDENCE_BYTES:
        raise ComfyProtocolError("R9.8 evidence exceeds accepted byte bound")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ComfyProtocolError("R9.8 evidence is invalid JSON") from exc
    if not isinstance(document, dict):
        raise ComfyProtocolError("R9.8 evidence root must be an object")
    payload = parse_envelope(document, expected_schema=_EVIDENCE_SCHEMA)
    return _evidence_from_payload(payload)


def _evidence_from_payload(payload: dict[str, Any]) -> R98LocalAcceptanceEvidence:
    expected = {
        "candidate_head",
        "status",
        "endpoint",
        "capability_identity_sha256",
        "comfyui_version",
        "device",
        "resource_profile",
        "scheduler_trace",
        "workflow_definition_id",
        "workflow_instance_digest_sha256",
        "run_id",
        "run_manifest_digest_sha256",
        "output_sha256",
        "output_length",
        "memory_observation",
        "terminal_cleanup",
        "ollama_state",
        "ollama_reason",
        "ollama_restored",
        "resource_audit_relative_path",
        "resource_audit_valid",
        "lifecycle_audit_valid",
        "failure_reason",
        "evidence_digest_sha256",
    }
    if set(payload) != expected:
        raise ComfyProtocolError("R9.8 evidence payload fields are invalid")
    evidence = R98LocalAcceptanceEvidence(
        candidate_head=str(payload["candidate_head"]),
        status=str(payload["status"]),
        endpoint=str(payload["endpoint"]),
        capability_identity_sha256=_optional_string(payload["capability_identity_sha256"]),
        comfyui_version=_optional_string(payload["comfyui_version"]),
        device=_optional_dict(payload["device"]),
        resource_profile=_required_dict(payload["resource_profile"], "resource_profile"),
        scheduler_trace=_optional_dict(payload["scheduler_trace"]),
        workflow_definition_id=_optional_string(payload["workflow_definition_id"]),
        workflow_instance_digest_sha256=_optional_string(payload["workflow_instance_digest_sha256"]),
        run_id=_optional_string(payload["run_id"]),
        run_manifest_digest_sha256=_optional_string(payload["run_manifest_digest_sha256"]),
        output_sha256=_optional_string(payload["output_sha256"]),
        output_length=(
            None if payload["output_length"] is None else int(payload["output_length"])
        ),
        memory_observation=_optional_dict(payload["memory_observation"]),
        terminal_cleanup=_optional_dict(payload["terminal_cleanup"]),
        ollama_state=str(payload["ollama_state"]),
        ollama_reason=str(payload["ollama_reason"]),
        ollama_restored=tuple(str(item) for item in payload["ollama_restored"]),
        resource_audit_relative_path=str(payload["resource_audit_relative_path"]),
        resource_audit_valid=bool(payload["resource_audit_valid"]),
        lifecycle_audit_valid=bool(payload["lifecycle_audit_valid"]),
        failure_reason=_optional_string(payload["failure_reason"]),
        evidence_digest_sha256=str(payload["evidence_digest_sha256"]),
    )
    _validate_evidence(evidence)
    return evidence


def _validate_evidence(evidence: R98LocalAcceptanceEvidence) -> None:
    if not _is_sha(evidence.candidate_head):
        raise ComfyProtocolError("R9.8 evidence candidate head is invalid")
    if evidence.status not in {"pass", "fail"}:
        raise ComfyProtocolError("R9.8 evidence status is invalid")
    if evidence.ollama_state not in {item.value for item in OllamaCoexistenceState}:
        raise ComfyProtocolError("R9.8 Ollama evidence state is invalid")
    expected = canonical_sha256(evidence.canonical_without_digest())
    if evidence.evidence_digest_sha256 != expected:
        raise ComfyProtocolError("R9.8 evidence digest is invalid")
    if evidence.status == "pass":
        required = (
            evidence.capability_identity_sha256,
            evidence.device,
            evidence.scheduler_trace,
            evidence.workflow_definition_id,
            evidence.workflow_instance_digest_sha256,
            evidence.run_id,
            evidence.run_manifest_digest_sha256,
            evidence.output_sha256,
            evidence.output_length,
            evidence.memory_observation,
            evidence.terminal_cleanup,
        )
        if any(item is None for item in required):
            raise ComfyProtocolError("R9.8 passing evidence omits required proof")
        if not evidence.resource_audit_valid or not evidence.lifecycle_audit_valid:
            raise ComfyProtocolError("R9.8 passing evidence requires valid audit chains")
        if evidence.failure_reason is not None:
            raise ComfyProtocolError("R9.8 passing evidence cannot carry a failure reason")


def _seal_evidence(**kwargs: Any) -> R98LocalAcceptanceEvidence:
    draft = R98LocalAcceptanceEvidence(**kwargs, evidence_digest_sha256="")
    evidence = R98LocalAcceptanceEvidence(
        **kwargs,
        evidence_digest_sha256=canonical_sha256(draft.canonical_without_digest()),
    )
    _validate_evidence(evidence)
    return evidence


def _unique_pairs(items: tuple[tuple[str, Any], ...], label: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ComfyGovernanceError(f"Duplicate {label}: {key}")
        result[key] = value
    return result


def _mib(value: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value * _MIB


def _is_sha(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(ch in "0123456789abcdef" for ch in value)
    )


def _ollama_reason(state: OllamaCoexistenceState, models_present: bool) -> str:
    if state is OllamaCoexistenceState.TESTED and models_present:
        return "one or more pre-existing running Ollama models were observed"
    if state is OllamaCoexistenceState.N_A:
        return "no Ollama model was already loaded; no model was loaded or downloaded for this gate"
    return "loopback Ollama was unavailable; ComfyUI GPU acceptance continued without fabricating coexistence"


def _optional_string(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_dict(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    return _required_dict(value, "optional object")


def _required_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ComfyProtocolError(f"R9.8 evidence {field} must be an object")
    return dict(value)
