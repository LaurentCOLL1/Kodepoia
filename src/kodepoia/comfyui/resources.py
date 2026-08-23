from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from urllib.parse import urlparse

from kodepoia.brain.ollama import OllamaClient
from kodepoia.core.audit import AuditLog
from kodepoia.exceptions import BrainUnavailable
from kodepoia.quality.budget import BudgetMetric, BudgetObservation
from kodepoia.quality.health import HealthDimension, HealthMetric, HealthStatus

from .client import ComfyUIClient
from .errors import ComfyGovernanceError, ComfyProtocolError, ComfyUnavailableError
from .lifecycle import ComfyFreeMemoryEvidence, ComfyLifecycleService
from .serialization import canonical_sha256

_MAX_DEVICES = 64
_MAX_OLLAMA_MODELS = 256
_MAX_BYTES = 1 << 60
_LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})


class GpuAdmissionDecision(StrEnum):
    ADMIT = "admit"
    DEFER = "defer"
    REJECT = "reject"
    UNKNOWN = "unknown"


class OllamaCoexistenceState(StrEnum):
    TESTED = "tested"
    N_A = "n/a"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class ComfyDeviceMemory:
    name: str
    backend_type: str
    index: int
    vram_total_bytes: int
    vram_free_bytes: int
    torch_vram_total_bytes: int | None
    torch_vram_free_bytes: int | None

    def canonical(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "backend_type": self.backend_type,
            "index": self.index,
            "vram_total_bytes": self.vram_total_bytes,
            "vram_free_bytes": self.vram_free_bytes,
            "torch_vram_total_bytes": self.torch_vram_total_bytes,
            "torch_vram_free_bytes": self.torch_vram_free_bytes,
        }


@dataclass(frozen=True, slots=True)
class ComfyVramSnapshot:
    endpoint: str
    comfyui_version: str | None
    python_version: str | None
    devices: tuple[ComfyDeviceMemory, ...]
    digest_sha256: str

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "comfyui_version": self.comfyui_version,
            "python_version": self.python_version,
            "devices": [item.canonical() for item in self.devices],
        }

    def canonical(self) -> dict[str, Any]:
        return {**self.canonical_without_digest(), "digest_sha256": self.digest_sha256}

    @property
    def primary(self) -> ComfyDeviceMemory | None:
        return self.devices[0] if self.devices else None

    def device(self, device_index: int) -> ComfyDeviceMemory | None:
        matches = tuple(item for item in self.devices if item.index == device_index)
        if len(matches) > 1:
            raise ComfyProtocolError("ComfyUI VRAM telemetry contains duplicate device indexes")
        return matches[0] if matches else None


@dataclass(frozen=True, slots=True)
class OllamaRunningModelMemory:
    name: str
    size_vram_bytes: int
    expires_at: str | None

    def canonical(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "size_vram_bytes": self.size_vram_bytes,
            "expires_at": self.expires_at,
        }


@dataclass(frozen=True, slots=True)
class OllamaMemorySnapshot:
    base_url: str
    state: OllamaCoexistenceState
    models: tuple[OllamaRunningModelMemory, ...]
    digest_sha256: str

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "state": self.state.value,
            "models": [item.canonical() for item in self.models],
        }

    def canonical(self) -> dict[str, Any]:
        return {**self.canonical_without_digest(), "digest_sha256": self.digest_sha256}


@dataclass(frozen=True, slots=True)
class GpuResourceProfile:
    estimate_bytes: int
    reserve_bytes: int
    headroom_bytes: int
    device_index: int = 0
    total_limit_bytes: int | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("estimate_bytes", self.estimate_bytes),
            ("reserve_bytes", self.reserve_bytes),
            ("headroom_bytes", self.headroom_bytes),
            ("device_index", self.device_index),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        bounded = (self.estimate_bytes, self.reserve_bytes, self.headroom_bytes)
        if any(value > _MAX_BYTES for value in bounded):
            raise ValueError("GPU resource byte values exceed the accepted bound")
        if self.total_limit_bytes is not None:
            if (
                isinstance(self.total_limit_bytes, bool)
                or not isinstance(self.total_limit_bytes, int)
                or self.total_limit_bytes <= 0
                or self.total_limit_bytes > _MAX_BYTES
            ):
                raise ValueError("total_limit_bytes must be a positive bounded integer or None")

    @property
    def required_free_bytes(self) -> int:
        required = self.estimate_bytes + self.reserve_bytes + self.headroom_bytes
        if required > _MAX_BYTES:
            raise ValueError("GPU required free bytes exceed the accepted bound")
        return required

    def canonical(self) -> dict[str, Any]:
        return {
            "estimate_bytes": self.estimate_bytes,
            "reserve_bytes": self.reserve_bytes,
            "headroom_bytes": self.headroom_bytes,
            "device_index": self.device_index,
            "total_limit_bytes": self.total_limit_bytes,
            "required_free_bytes": self.required_free_bytes,
        }


@dataclass(frozen=True, slots=True)
class GpuAdmissionResult:
    decision: GpuAdmissionDecision
    reason: str
    profile: GpuResourceProfile
    telemetry_digest_sha256: str | None
    measured_total_bytes: int | None
    policy_total_bytes: int | None
    measured_free_bytes: int | None
    effective_free_bytes: int | None
    digest_sha256: str

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "profile": self.profile.canonical(),
            "telemetry_digest_sha256": self.telemetry_digest_sha256,
            "measured_total_bytes": self.measured_total_bytes,
            "policy_total_bytes": self.policy_total_bytes,
            "measured_free_bytes": self.measured_free_bytes,
            "effective_free_bytes": self.effective_free_bytes,
        }

    def canonical(self) -> dict[str, Any]:
        return {**self.canonical_without_digest(), "digest_sha256": self.digest_sha256}


@dataclass(frozen=True, slots=True)
class GpuCleanupTrace:
    initial: GpuAdmissionResult
    telemetry_before: ComfyVramSnapshot | None
    ollama_before: OllamaMemorySnapshot | None
    ollama_unloaded: tuple[str, ...]
    comfy_cleanup: ComfyFreeMemoryEvidence | None
    telemetry_after: ComfyVramSnapshot | None
    final: GpuAdmissionResult
    digest_sha256: str

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "initial": self.initial.canonical(),
            "telemetry_before": self.telemetry_before.canonical() if self.telemetry_before else None,
            "ollama_before": self.ollama_before.canonical() if self.ollama_before else None,
            "ollama_unloaded": list(self.ollama_unloaded),
            "comfy_cleanup": self.comfy_cleanup.canonical() if self.comfy_cleanup else None,
            "telemetry_after": self.telemetry_after.canonical() if self.telemetry_after else None,
            "final": self.final.canonical(),
        }

    def canonical(self) -> dict[str, Any]:
        return {**self.canonical_without_digest(), "digest_sha256": self.digest_sha256}


class ComfyVramTelemetryAdapter:
    """Normalize the fixed ComfyUI /system_stats device memory evidence into bytes."""

    def __init__(self, client: ComfyUIClient) -> None:
        self.client = client

    def sample(self) -> ComfyVramSnapshot:
        data = self.client._http.get_json("/system_stats")
        system = data.get("system", {})
        devices = data.get("devices", [])
        if not isinstance(system, dict) or not isinstance(devices, list) or len(devices) > _MAX_DEVICES:
            raise ComfyProtocolError("ComfyUI system_stats device telemetry shape is invalid")
        normalized: list[ComfyDeviceMemory] = []
        indexes: set[int] = set()
        for position, raw in enumerate(devices):
            if not isinstance(raw, dict):
                raise ComfyProtocolError("ComfyUI system_stats device entry must be an object")
            name = _bounded_text(raw.get("name"), "device name", 512)
            backend = _bounded_text(raw.get("type", "unknown"), "device type", 128)
            index = _nonnegative_int(raw.get("index", position), "device index")
            if index in indexes:
                raise ComfyProtocolError("ComfyUI system_stats contains duplicate device indexes")
            indexes.add(index)
            total = _bounded_bytes(raw.get("vram_total"), "vram_total")
            free = _bounded_bytes(raw.get("vram_free"), "vram_free")
            if free > total:
                raise ComfyProtocolError("ComfyUI reports free VRAM greater than total VRAM")
            torch_total = _optional_bytes(raw.get("torch_vram_total"), "torch_vram_total")
            torch_free = _optional_bytes(raw.get("torch_vram_free"), "torch_vram_free")
            if torch_total is not None and torch_free is not None and torch_free > torch_total:
                raise ComfyProtocolError("ComfyUI reports torch free VRAM greater than torch total VRAM")
            normalized.append(
                ComfyDeviceMemory(
                    name=name,
                    backend_type=backend,
                    index=index,
                    vram_total_bytes=total,
                    vram_free_bytes=free,
                    torch_vram_total_bytes=torch_total,
                    torch_vram_free_bytes=torch_free,
                )
            )
        payload = {
            "endpoint": self.client.endpoint.origin,
            "comfyui_version": _optional_text(system.get("comfyui_version"), 256),
            "python_version": _optional_text(system.get("python_version"), 1024),
            "devices": [item.canonical() for item in normalized],
        }
        return ComfyVramSnapshot(
            endpoint=self.client.endpoint.origin,
            comfyui_version=payload["comfyui_version"],
            python_version=payload["python_version"],
            devices=tuple(normalized),
            digest_sha256=canonical_sha256(payload),
        )


class OllamaMemoryAdapter:
    """Reuse accepted R3 OllamaClient for running-model VRAM evidence and explicit unload/restore."""

    def __init__(self, client: OllamaClient) -> None:
        parsed = urlparse(client.base_url)
        if parsed.scheme not in {"http", "https"} or (parsed.hostname or "").lower() not in _LOOPBACK:
            raise ComfyGovernanceError("R9.8 Ollama coexistence accepts loopback Ollama only")
        self.client = client

    def sample(self) -> OllamaMemorySnapshot:
        try:
            raw = self.client.running_models()
        except BrainUnavailable:
            return _seal_ollama(self.client.base_url, OllamaCoexistenceState.UNAVAILABLE, ())
        if len(raw) > _MAX_OLLAMA_MODELS:
            raise ComfyProtocolError("Ollama running-model list exceeds accepted bound")
        models: list[OllamaRunningModelMemory] = []
        names: set[str] = set()
        for item in raw:
            name = _bounded_text(item.get("name") or item.get("model"), "Ollama model name", 512)
            if name in names:
                raise ComfyProtocolError("Ollama running-model list contains duplicate model names")
            names.add(name)
            size_vram = _bounded_bytes(item.get("size_vram", 0), "Ollama size_vram")
            expires_at = _optional_text(item.get("expires_at"), 256)
            models.append(OllamaRunningModelMemory(name, size_vram, expires_at))
        state = OllamaCoexistenceState.TESTED if models else OllamaCoexistenceState.N_A
        return _seal_ollama(self.client.base_url, state, tuple(sorted(models, key=lambda item: item.name)))

    def unload_approved(
        self,
        snapshot: OllamaMemorySnapshot,
        approved_names: tuple[str, ...],
    ) -> tuple[str, ...]:
        approved = set(approved_names)
        if len(approved) != len(approved_names):
            raise ComfyGovernanceError("Approved Ollama unload list contains duplicates")
        present = {item.name for item in snapshot.models}
        unknown = approved - present
        if unknown:
            raise ComfyGovernanceError(
                "Approved Ollama unload list contains a model not present in the captured workload"
            )
        unloaded: list[str] = []
        for model in snapshot.models:
            if model.name not in approved:
                continue
            self.client.unload(model.name)
            unloaded.append(model.name)
        return tuple(unloaded)

    def restore_explicit(self, names: tuple[str, ...]) -> None:
        if len(set(names)) != len(names):
            raise ComfyGovernanceError("Ollama restore list contains duplicates")
        for name in names:
            _bounded_text(name, "Ollama restore model name", 512)
            self.client.preload(name, keep_alive="2m")


class GpuAdmissionPolicy:
    def decide(
        self,
        snapshot: ComfyVramSnapshot | None,
        profile: GpuResourceProfile,
    ) -> GpuAdmissionResult:
        if snapshot is None:
            return _seal_admission(
                GpuAdmissionDecision.UNKNOWN,
                "VRAM telemetry for the requested device is unavailable",
                profile,
                None,
                None,
                None,
                None,
                None,
            )
        device = snapshot.device(profile.device_index)
        if device is None:
            return _seal_admission(
                GpuAdmissionDecision.UNKNOWN,
                "VRAM telemetry for the requested device is unavailable",
                profile,
                snapshot.digest_sha256,
                None,
                None,
                None,
                None,
            )
        measured_total = device.vram_total_bytes
        policy_total = (
            measured_total
            if profile.total_limit_bytes is None
            else min(measured_total, profile.total_limit_bytes)
        )
        measured_free = device.vram_free_bytes
        policy_free = min(measured_free, policy_total)
        required = profile.required_free_bytes
        effective = max(0, policy_free - profile.reserve_bytes - profile.headroom_bytes)
        if required > policy_total:
            decision = GpuAdmissionDecision.REJECT
            reason = "job estimate plus reserve/headroom exceeds configured/measured device VRAM"
        elif policy_free >= required:
            decision = GpuAdmissionDecision.ADMIT
            reason = "measured free VRAM satisfies estimate plus reserve/headroom"
        else:
            decision = GpuAdmissionDecision.DEFER
            reason = "current free VRAM is insufficient; bounded cleanup and remeasurement may help"
        return _seal_admission(
            decision,
            reason,
            profile,
            snapshot.digest_sha256,
            measured_total,
            policy_total,
            measured_free,
            effective,
        )


class GpuResourceCoordinator:
    """Lease-serialized VRAM admission with typed cleanup ordering and exact remeasurement."""

    def __init__(
        self,
        telemetry: ComfyVramTelemetryAdapter,
        lifecycle: ComfyLifecycleService,
        *,
        ollama: OllamaMemoryAdapter | None = None,
        policy: GpuAdmissionPolicy | None = None,
        audit_log: AuditLog | None = None,
    ) -> None:
        self.telemetry = telemetry
        self.lifecycle = lifecycle
        self.ollama = ollama
        self.policy = policy or GpuAdmissionPolicy()
        self.audit_log = audit_log
        self._lease = threading.Lock()

    def evaluate(self, profile: GpuResourceProfile) -> tuple[ComfyVramSnapshot, GpuAdmissionResult]:
        snapshot = self.telemetry.sample()
        result = self.policy.decide(snapshot, profile)
        self._audit("evaluate", result.decision.value, {"result": result.canonical()})
        return snapshot, result

    def admit_with_cleanup(
        self,
        profile: GpuResourceProfile,
        *,
        approved_ollama_unloads: tuple[str, ...] = (),
    ) -> GpuCleanupTrace:
        if not self._lease.acquire(blocking=False):
            final = _seal_admission(
                GpuAdmissionDecision.DEFER,
                "GPU resource domain already has an active admission lease",
                profile,
                None,
                None,
                None,
                None,
                None,
            )
            trace = _seal_trace(final, None, None, (), None, None, final)
            self._audit("admit", final.decision.value, {"trace": trace.canonical()})
            return trace
        before: ComfyVramSnapshot | None = None
        initial: GpuAdmissionResult | None = None
        ollama_before: OllamaMemorySnapshot | None = None
        unloaded: tuple[str, ...] = ()
        cleanup: ComfyFreeMemoryEvidence | None = None
        after: ComfyVramSnapshot | None = None
        try:
            before = self.telemetry.sample()
            initial = self.policy.decide(before, profile)
            if initial.decision in {
                GpuAdmissionDecision.ADMIT,
                GpuAdmissionDecision.REJECT,
                GpuAdmissionDecision.UNKNOWN,
            }:
                trace = _seal_trace(initial, before, None, (), None, before, initial)
                self._audit("admit", initial.decision.value, {"trace": trace.canonical()})
                return trace

            if self.ollama is not None:
                ollama_before = self.ollama.sample()
                if approved_ollama_unloads:
                    if ollama_before.state is not OllamaCoexistenceState.TESTED:
                        raise ComfyGovernanceError(
                            "Explicit Ollama unload requires a captured TESTED running workload"
                        )
                    unloaded = self.ollama.unload_approved(
                        ollama_before,
                        approved_ollama_unloads,
                    )
                    self._audit(
                        "ollama_unload",
                        "requested",
                        {"models": list(unloaded), "snapshot": ollama_before.canonical()},
                    )

            cleanup = self.lifecycle.request_free_memory()
            after = self.telemetry.sample()
            final = self.policy.decide(after, profile)
            trace = _seal_trace(
                initial,
                before,
                ollama_before,
                unloaded,
                cleanup,
                after,
                final,
            )
            self._audit("admit", final.decision.value, {"trace": trace.canonical()})
            return trace
        except (ComfyProtocolError, ComfyUnavailableError, BrainUnavailable):
            unknown = _seal_admission(
                GpuAdmissionDecision.UNKNOWN,
                "resource cleanup or remeasurement could not be proven",
                profile,
                before.digest_sha256 if before is not None else None,
                None,
                None,
                None,
                None,
            )
            trace = _seal_trace(
                initial or unknown,
                before,
                ollama_before,
                unloaded,
                cleanup,
                after,
                unknown,
            )
            self._audit("admit", unknown.decision.value, {"trace": trace.canonical()})
            return trace
        finally:
            self._lease.release()

    def restore_prior_ollama(self, trace: GpuCleanupTrace) -> tuple[str, ...]:
        """Opt-in restoration limited exactly to workloads unloaded by this trace."""
        if not trace.ollama_unloaded:
            return ()
        if self.ollama is None:
            raise ComfyGovernanceError("Ollama restoration requested without an Ollama adapter")
        self.ollama.restore_explicit(trace.ollama_unloaded)
        self._audit(
            "ollama_restore",
            "requested",
            {"models": list(trace.ollama_unloaded), "trace_digest_sha256": trace.digest_sha256},
        )
        return trace.ollama_unloaded

    def _audit(self, action: str, outcome: str, details: dict[str, Any]) -> None:
        if self.audit_log is None:
            return
        self.audit_log.append(
            category="comfyui.vram",
            action=action,
            actor="kodepoia",
            outcome=outcome,
            details=details,
        )


@dataclass(frozen=True, slots=True)
class WorkflowMemoryObservation:
    workflow_definition_id: str
    starting_free_bytes: int
    minimum_free_bytes: int
    ending_free_bytes: int
    observed_peak_delta_bytes: int
    oom_observed: bool
    digest_sha256: str

    @classmethod
    def create(
        cls,
        workflow_definition_id: str,
        samples: tuple[int, ...],
        *,
        oom_observed: bool = False,
    ) -> "WorkflowMemoryObservation":
        if not samples:
            raise ValueError("workflow memory observation requires at least one sample")
        checked = tuple(_bounded_bytes(item, "workflow VRAM sample") for item in samples)
        start = checked[0]
        minimum = min(checked)
        ending = checked[-1]
        peak = max(0, start - minimum)
        payload = {
            "workflow_definition_id": _bounded_text(
                workflow_definition_id,
                "workflow definition id",
                128,
            ),
            "starting_free_bytes": start,
            "minimum_free_bytes": minimum,
            "ending_free_bytes": ending,
            "observed_peak_delta_bytes": peak,
            "oom_observed": bool(oom_observed),
        }
        return cls(**payload, digest_sha256=canonical_sha256(payload))

    def canonical(self) -> dict[str, Any]:
        return {
            "workflow_definition_id": self.workflow_definition_id,
            "starting_free_bytes": self.starting_free_bytes,
            "minimum_free_bytes": self.minimum_free_bytes,
            "ending_free_bytes": self.ending_free_bytes,
            "observed_peak_delta_bytes": self.observed_peak_delta_bytes,
            "oom_observed": self.oom_observed,
            "digest_sha256": self.digest_sha256,
        }

    def updated_estimate(self, previous_estimate_bytes: int) -> int:
        previous = _bounded_bytes(previous_estimate_bytes, "previous estimate")
        observed = self.observed_peak_delta_bytes
        # OOM can only increase evidence-based estimates; it never relaxes reserves or forces admission.
        if self.oom_observed:
            observed = max(
                observed,
                min(_MAX_BYTES, previous + max(64 * 1024 * 1024, previous // 10)),
            )
        return max(previous, observed)


def vram_budget_observation(snapshot: ComfyVramSnapshot, *, device_index: int = 0) -> BudgetObservation:
    device = snapshot.device(device_index)
    if device is None:
        raise ComfyProtocolError("Cannot emit VRAM budget observation for an unavailable device")
    used_mb = (device.vram_total_bytes - device.vram_free_bytes) / (1024 * 1024)
    return BudgetObservation(
        metric=BudgetMetric.VRAM_MB,
        value=used_mb,
        source="R9.8 ComfyUI /system_stats",
        details={
            "device_index": device.index,
            "backend_type": device.backend_type,
            "telemetry_digest_sha256": snapshot.digest_sha256,
        },
    )


def vram_health_metric(result: GpuAdmissionResult) -> HealthMetric:
    if result.decision is GpuAdmissionDecision.UNKNOWN:
        return HealthMetric(
            dimension=HealthDimension.MEMORY,
            status=HealthStatus.UNKNOWN,
            score=None,
            summary=result.reason,
            source="R9.8 GPU admission",
            details={"admission_digest_sha256": result.digest_sha256},
        )
    if result.decision is GpuAdmissionDecision.REJECT:
        return HealthMetric(
            dimension=HealthDimension.MEMORY,
            status=HealthStatus.FAIL,
            score=0.0,
            summary=result.reason,
            source="R9.8 GPU admission",
            blocking=True,
            details={"admission_digest_sha256": result.digest_sha256},
        )
    if result.decision is GpuAdmissionDecision.DEFER:
        return HealthMetric(
            dimension=HealthDimension.MEMORY,
            status=HealthStatus.WARN,
            score=60.0,
            summary=result.reason,
            source="R9.8 GPU admission",
            details={"admission_digest_sha256": result.digest_sha256},
        )
    return HealthMetric(
        dimension=HealthDimension.MEMORY,
        status=HealthStatus.PASS,
        score=100.0,
        summary=result.reason,
        source="R9.8 GPU admission",
        details={"admission_digest_sha256": result.digest_sha256},
    )


def _seal_ollama(
    base_url: str,
    state: OllamaCoexistenceState,
    models: tuple[OllamaRunningModelMemory, ...],
) -> OllamaMemorySnapshot:
    payload = {
        "base_url": base_url,
        "state": state.value,
        "models": [item.canonical() for item in models],
    }
    return OllamaMemorySnapshot(base_url, state, models, canonical_sha256(payload))


def _seal_admission(
    decision: GpuAdmissionDecision,
    reason: str,
    profile: GpuResourceProfile,
    telemetry_digest: str | None,
    measured_total: int | None,
    policy_total: int | None,
    measured_free: int | None,
    effective: int | None,
) -> GpuAdmissionResult:
    draft = GpuAdmissionResult(
        decision,
        reason,
        profile,
        telemetry_digest,
        measured_total,
        policy_total,
        measured_free,
        effective,
        "",
    )
    return GpuAdmissionResult(
        decision,
        reason,
        profile,
        telemetry_digest,
        measured_total,
        policy_total,
        measured_free,
        effective,
        canonical_sha256(draft.canonical_without_digest()),
    )


def _seal_trace(
    initial: GpuAdmissionResult,
    before: ComfyVramSnapshot | None,
    ollama_before: OllamaMemorySnapshot | None,
    unloaded: tuple[str, ...],
    cleanup: ComfyFreeMemoryEvidence | None,
    after: ComfyVramSnapshot | None,
    final: GpuAdmissionResult,
) -> GpuCleanupTrace:
    draft = GpuCleanupTrace(
        initial,
        before,
        ollama_before,
        unloaded,
        cleanup,
        after,
        final,
        "",
    )
    return GpuCleanupTrace(
        initial,
        before,
        ollama_before,
        unloaded,
        cleanup,
        after,
        final,
        canonical_sha256(draft.canonical_without_digest()),
    )


def _bounded_text(value: Any, field: str, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(ch) < 32 for ch in value)
    ):
        raise ComfyProtocolError(f"{field} must be a bounded printable string")
    return value


def _optional_text(value: Any, maximum: int) -> str | None:
    if value is None:
        return None
    return _bounded_text(value, "optional text", maximum)


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ComfyProtocolError(f"{field} must be a non-negative integer")
    return value


def _bounded_bytes(value: Any, field: str) -> int:
    result = _nonnegative_int(value, field)
    if result > _MAX_BYTES:
        raise ComfyProtocolError(f"{field} exceeds the accepted byte bound")
    return result


def _optional_bytes(value: Any, field: str) -> int | None:
    return None if value is None else _bounded_bytes(value, field)
