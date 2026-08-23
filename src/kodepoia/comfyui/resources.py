from __future__ import annotations

import math
import threading
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from urllib.parse import urlparse

from kodepoia.brain.ollama import OllamaClient
from kodepoia.exceptions import BrainUnavailable

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

    @property
    def primary(self) -> ComfyDeviceMemory | None:
        return self.devices[0] if self.devices else None


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


@dataclass(frozen=True, slots=True)
class GpuResourceProfile:
    estimate_bytes: int
    reserve_bytes: int
    headroom_bytes: int
    device_index: int = 0

    def __post_init__(self) -> None:
        for name, value in (
            ("estimate_bytes", self.estimate_bytes),
            ("reserve_bytes", self.reserve_bytes),
            ("headroom_bytes", self.headroom_bytes),
            ("device_index", self.device_index),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if any(value > _MAX_BYTES for value in (self.estimate_bytes, self.reserve_bytes, self.headroom_bytes)):
            raise ValueError("GPU resource byte values exceed the accepted bound")

    @property
    def required_free_bytes(self) -> int:
        return self.estimate_bytes + self.reserve_bytes + self.headroom_bytes

    def canonical(self) -> dict[str, int]:
        return {
            "estimate_bytes": self.estimate_bytes,
            "reserve_bytes": self.reserve_bytes,
            "headroom_bytes": self.headroom_bytes,
            "device_index": self.device_index,
            "required_free_bytes": self.required_free_bytes,
        }


@dataclass(frozen=True, slots=True)
class GpuAdmissionResult:
    decision: GpuAdmissionDecision
    reason: str
    profile: GpuResourceProfile
    telemetry_digest_sha256: str | None
    total_bytes: int | None
    free_bytes: int | None
    effective_free_bytes: int | None
    digest_sha256: str

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "profile": self.profile.canonical(),
            "telemetry_digest_sha256": self.telemetry_digest_sha256,
            "total_bytes": self.total_bytes,
            "free_bytes": self.free_bytes,
            "effective_free_bytes": self.effective_free_bytes,
        }


@dataclass(frozen=True, slots=True)
class GpuCleanupTrace:
    initial: GpuAdmissionResult
    ollama_before: OllamaMemorySnapshot | None
    ollama_unloaded: tuple[str, ...]
    comfy_cleanup: ComfyFreeMemoryEvidence | None
    telemetry_after: ComfyVramSnapshot | None
    final: GpuAdmissionResult
    digest_sha256: str

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "initial": {**self.initial.canonical_without_digest(), "digest_sha256": self.initial.digest_sha256},
            "ollama_before": (
                {**self.ollama_before.canonical_without_digest(), "digest_sha256": self.ollama_before.digest_sha256}
                if self.ollama_before is not None
                else None
            ),
            "ollama_unloaded": list(self.ollama_unloaded),
            "comfy_cleanup": self.comfy_cleanup.canonical() if self.comfy_cleanup is not None else None,
            "telemetry_after": (
                {**self.telemetry_after.canonical_without_digest(), "digest_sha256": self.telemetry_after.digest_sha256}
                if self.telemetry_after is not None
                else None
            ),
            "final": {**self.final.canonical_without_digest(), "digest_sha256": self.final.digest_sha256},
        }


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
        for position, raw in enumerate(devices):
            if not isinstance(raw, dict):
                raise ComfyProtocolError("ComfyUI system_stats device entry must be an object")
            name = _bounded_text(raw.get("name"), "device name", 512)
            backend = _bounded_text(raw.get("type", "unknown"), "device type", 128)
            index = _nonnegative_int(raw.get("index", position), "device index")
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
        for item in raw:
            name = _bounded_text(item.get("name") or item.get("model"), "Ollama model name", 512)
            size_vram = _bounded_bytes(item.get("size_vram", 0), "Ollama size_vram")
            expires_at = _optional_text(item.get("expires_at"), 256)
            models.append(OllamaRunningModelMemory(name, size_vram, expires_at))
        state = OllamaCoexistenceState.TESTED if models else OllamaCoexistenceState.N_A
        return _seal_ollama(self.client.base_url, state, tuple(sorted(models, key=lambda item: item.name)))

    def unload_approved(self, snapshot: OllamaMemorySnapshot, approved_names: tuple[str, ...]) -> tuple[str, ...]:
        approved = set(approved_names)
        present = {item.name for item in snapshot.models}
        unknown = approved - present
        if unknown:
            raise ComfyGovernanceError("Approved Ollama unload list contains a model not present in the captured workload")
        unloaded: list[str] = []
        for model in snapshot.models:
            if model.name not in approved:
                continue
            self.client.unload(model.name)
            unloaded.append(model.name)
        return tuple(unloaded)

    def restore_explicit(self, names: tuple[str, ...]) -> None:
        for name in names:
            _bounded_text(name, "Ollama restore model name", 512)
            self.client.preload(name, keep_alive="2m")


class GpuAdmissionPolicy:
    def decide(self, snapshot: ComfyVramSnapshot | None, profile: GpuResourceProfile) -> GpuAdmissionResult:
        if snapshot is None or profile.device_index >= len(snapshot.devices):
            return _seal_admission(
                GpuAdmissionDecision.UNKNOWN,
                "VRAM telemetry for the requested device is unavailable",
                profile,
                None,
                None,
                None,
                None,
            )
        device = snapshot.devices[profile.device_index]
        total = device.vram_total_bytes
        free = device.vram_free_bytes
        required = profile.required_free_bytes
        effective = max(0, free - profile.reserve_bytes - profile.headroom_bytes)
        if required > total:
            decision = GpuAdmissionDecision.REJECT
            reason = "job estimate plus reserve/headroom exceeds total device VRAM"
        elif free >= required:
            decision = GpuAdmissionDecision.ADMIT
            reason = "measured free VRAM satisfies estimate plus reserve/headroom"
        else:
            decision = GpuAdmissionDecision.DEFER
            reason = "current free VRAM is insufficient; bounded cleanup and remeasurement may help"
        return _seal_admission(decision, reason, profile, snapshot.digest_sha256, total, free, effective)


class GpuResourceCoordinator:
    """Lease-serialized VRAM admission with typed cleanup ordering and exact remeasurement."""

    def __init__(
        self,
        telemetry: ComfyVramTelemetryAdapter,
        lifecycle: ComfyLifecycleService,
        *,
        ollama: OllamaMemoryAdapter | None = None,
        policy: GpuAdmissionPolicy | None = None,
    ) -> None:
        self.telemetry = telemetry
        self.lifecycle = lifecycle
        self.ollama = ollama
        self.policy = policy or GpuAdmissionPolicy()
        self._lease = threading.Lock()

    def evaluate(self, profile: GpuResourceProfile) -> tuple[ComfyVramSnapshot, GpuAdmissionResult]:
        snapshot = self.telemetry.sample()
        return snapshot, self.policy.decide(snapshot, profile)

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
            )
            return _seal_trace(final, None, (), None, None, final)
        try:
            before = self.telemetry.sample()
            initial = self.policy.decide(before, profile)
            if initial.decision in {GpuAdmissionDecision.ADMIT, GpuAdmissionDecision.REJECT, GpuAdmissionDecision.UNKNOWN}:
                return _seal_trace(initial, None, (), None, before, initial)

            ollama_before: OllamaMemorySnapshot | None = None
            unloaded: tuple[str, ...] = ()
            if self.ollama is not None:
                ollama_before = self.ollama.sample()
                if approved_ollama_unloads and ollama_before.state is OllamaCoexistenceState.TESTED:
                    unloaded = self.ollama.unload_approved(ollama_before, approved_ollama_unloads)

            cleanup = self.lifecycle.request_free_memory()
            after = self.telemetry.sample()
            final = self.policy.decide(after, profile)
            return _seal_trace(initial, ollama_before, unloaded, cleanup, after, final)
        except (ComfyProtocolError, ComfyUnavailableError, BrainUnavailable):
            unknown = _seal_admission(
                GpuAdmissionDecision.UNKNOWN,
                "resource cleanup or remeasurement could not be proven",
                profile,
                None,
                None,
                None,
                None,
            )
            return _seal_trace(unknown, None, (), None, None, unknown)
        finally:
            self._lease.release()


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
            "workflow_definition_id": _bounded_text(workflow_definition_id, "workflow definition id", 128),
            "starting_free_bytes": start,
            "minimum_free_bytes": minimum,
            "ending_free_bytes": ending,
            "observed_peak_delta_bytes": peak,
            "oom_observed": bool(oom_observed),
        }
        return cls(**payload, digest_sha256=canonical_sha256(payload))

    def updated_estimate(self, previous_estimate_bytes: int) -> int:
        previous = _bounded_bytes(previous_estimate_bytes, "previous estimate")
        observed = self.observed_peak_delta_bytes
        # OOM can only increase evidence-based estimates; it never relaxes reserves or forces admission.
        if self.oom_observed:
            observed = max(observed, min(_MAX_BYTES, previous + max(64 * 1024 * 1024, previous // 10)))
        return max(previous, observed)


def _seal_ollama(base_url: str, state: OllamaCoexistenceState, models: tuple[OllamaRunningModelMemory, ...]) -> OllamaMemorySnapshot:
    payload = {"base_url": base_url, "state": state.value, "models": [item.canonical() for item in models]}
    return OllamaMemorySnapshot(base_url, state, models, canonical_sha256(payload))


def _seal_admission(
    decision: GpuAdmissionDecision,
    reason: str,
    profile: GpuResourceProfile,
    telemetry_digest: str | None,
    total: int | None,
    free: int | None,
    effective: int | None,
) -> GpuAdmissionResult:
    draft = GpuAdmissionResult(decision, reason, profile, telemetry_digest, total, free, effective, "")
    return GpuAdmissionResult(
        decision,
        reason,
        profile,
        telemetry_digest,
        total,
        free,
        effective,
        canonical_sha256(draft.canonical_without_digest()),
    )


def _seal_trace(
    initial: GpuAdmissionResult,
    ollama_before: OllamaMemorySnapshot | None,
    unloaded: tuple[str, ...],
    cleanup: ComfyFreeMemoryEvidence | None,
    after: ComfyVramSnapshot | None,
    final: GpuAdmissionResult,
) -> GpuCleanupTrace:
    draft = GpuCleanupTrace(initial, ollama_before, unloaded, cleanup, after, final, "")
    return GpuCleanupTrace(
        initial,
        ollama_before,
        unloaded,
        cleanup,
        after,
        final,
        canonical_sha256(draft.canonical_without_digest()),
    )


def _bounded_text(value: Any, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(ch) < 32 for ch in value):
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
