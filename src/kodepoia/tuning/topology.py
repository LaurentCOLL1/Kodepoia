from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Mapping

from .contracts import (
    ResourceRequest,
    TrainingBackend,
    TuningRuntimeError,
    canonical_sha256,
)

TOPOLOGY_SCHEMA = "kodepoia.v2.4.1.accelerator-topology"
TOPOLOGY_SCHEMA_VERSION = 1
_MAX_DEVICES = 64
_MAX_BYTES = 1 << 60
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SAFE_PROVIDER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+@/-]{0,127}$")


class TopologyDisposition(StrEnum):
    READY = "ready"
    MISMATCH = "mismatch"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


def _bounded_bytes(label: str, value: int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= _MAX_BYTES:
        raise TuningRuntimeError(f"{label} must be a non-negative bounded integer or null")
    return value


@dataclass(frozen=True, slots=True)
class ProviderAcceleratorRequest:
    provider: str
    shape: str
    expected_backend: TrainingBackend
    expected_device_count: int | None = None
    expected_name_contains: str | None = None

    def __post_init__(self) -> None:
        provider = self.provider.strip()
        shape = self.shape.strip()
        if _SAFE_PROVIDER.fullmatch(provider) is None:
            raise TuningRuntimeError("provider must be a bounded safe identifier")
        if _SAFE_PROVIDER.fullmatch(shape) is None:
            raise TuningRuntimeError("provider accelerator shape must be a bounded safe identifier")
        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "shape", shape)
        object.__setattr__(self, "expected_backend", TrainingBackend(self.expected_backend))
        if self.expected_backend is TrainingBackend.CPU:
            raise TuningRuntimeError("accelerator provider request cannot target cpu")
        count = self.expected_device_count
        if count is not None and (
            isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= _MAX_DEVICES
        ):
            raise TuningRuntimeError(f"expected_device_count must be in [1, {_MAX_DEVICES}] or null")
        marker = self.expected_name_contains
        if marker is not None:
            marker = marker.strip()
            if not marker or len(marker) > 64:
                raise TuningRuntimeError("expected_name_contains must be a non-empty bounded string")
            object.__setattr__(self, "expected_name_contains", marker)

    def to_dict(self) -> dict[str, object]:
        return {
            "expected_backend": self.expected_backend.value,
            "expected_device_count": self.expected_device_count,
            "expected_name_contains": self.expected_name_contains,
            "provider": self.provider,
            "shape": self.shape,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


@dataclass(frozen=True, slots=True)
class AcceleratorDevice:
    backend_type: TrainingBackend
    index: int
    name: str
    vram_free_bytes: int | None
    vram_total_bytes: int | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "backend_type", TrainingBackend(self.backend_type))
        if self.backend_type is TrainingBackend.CPU:
            raise TuningRuntimeError("accelerator device cannot use cpu backend")
        if isinstance(self.index, bool) or not isinstance(self.index, int) or not 0 <= self.index < _MAX_DEVICES:
            raise TuningRuntimeError(f"accelerator device index must be in [0, {_MAX_DEVICES - 1}]")
        name = self.name.strip()
        if not name or len(name) > 512:
            raise TuningRuntimeError("accelerator device name must be a non-empty bounded string")
        object.__setattr__(self, "name", name)
        free_bytes = _bounded_bytes("vram_free_bytes", self.vram_free_bytes)
        total_bytes = _bounded_bytes("vram_total_bytes", self.vram_total_bytes)
        if total_bytes == 0:
            raise TuningRuntimeError("vram_total_bytes must be positive or null")
        if free_bytes is not None and total_bytes is not None and free_bytes > total_bytes:
            raise TuningRuntimeError("vram_free_bytes cannot exceed vram_total_bytes")

    def to_dict(self) -> dict[str, object]:
        return {
            "backend_type": self.backend_type.value,
            "index": self.index,
            "name": self.name,
            "vram_free_bytes": self.vram_free_bytes,
            "vram_total_bytes": self.vram_total_bytes,
        }


@dataclass(frozen=True, slots=True)
class ObservedAcceleratorTopology:
    backend_type: TrainingBackend
    devices: tuple[AcceleratorDevice, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "backend_type", TrainingBackend(self.backend_type))
        if self.backend_type is TrainingBackend.CPU:
            raise TuningRuntimeError("observed accelerator topology cannot use cpu backend")
        devices = tuple(self.devices)
        object.__setattr__(self, "devices", devices)
        if not 1 <= len(devices) <= _MAX_DEVICES:
            raise TuningRuntimeError(f"accelerator topology must contain [1, {_MAX_DEVICES}] devices")
        if any(device.backend_type is not self.backend_type for device in devices):
            raise TuningRuntimeError("accelerator topology mixes backend types")
        indexes = tuple(device.index for device in devices)
        if indexes != tuple(range(len(devices))):
            raise TuningRuntimeError("accelerator device indexes must be unique, ordered and contiguous")

    @property
    def device_count(self) -> int:
        return len(self.devices)

    def to_dict(self) -> dict[str, object]:
        return {
            "backend_type": self.backend_type.value,
            "device_count": self.device_count,
            "devices": [device.to_dict() for device in self.devices],
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


@dataclass(frozen=True, slots=True)
class AcceleratorTopologyReport:
    disposition: TopologyDisposition
    request_digest: str
    backend: TrainingBackend
    provider_request: ProviderAcceleratorRequest | None
    observed: ObservedAcceleratorTopology | None
    blockers: tuple[str, ...] = ()
    stderr: str = ""
    schema: str = TOPOLOGY_SCHEMA
    schema_version: int = TOPOLOGY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "disposition", TopologyDisposition(self.disposition))
        object.__setattr__(self, "backend", TrainingBackend(self.backend))
        if not _DIGEST.fullmatch(self.request_digest):
            raise TuningRuntimeError("request_digest must be 64 lowercase hex characters")
        blockers = tuple(sorted(set(self.blockers)))
        if any(not blocker for blocker in blockers):
            raise TuningRuntimeError("topology blockers must be non-empty strings")
        object.__setattr__(self, "blockers", blockers)
        object.__setattr__(self, "stderr", str(self.stderr)[:8192])
        if self.observed is not None and self.observed.backend_type is not self.backend:
            raise TuningRuntimeError("observed topology backend does not match requested backend")
        if self.disposition is TopologyDisposition.READY and (self.observed is None or blockers):
            raise TuningRuntimeError("ready topology report requires observed topology and no blockers")
        if self.disposition is TopologyDisposition.MISMATCH and (self.observed is None or not blockers):
            raise TuningRuntimeError("mismatch topology report requires observed topology and blockers")

    @property
    def topology_digest(self) -> str | None:
        return None if self.observed is None else self.observed.digest

    @property
    def provider_request_digest(self) -> str | None:
        return None if self.provider_request is None else self.provider_request.digest

    def descriptor(self) -> dict[str, object]:
        return {
            "backend": self.backend.value,
            "blockers": list(self.blockers),
            "disposition": self.disposition.value,
            "observed": None if self.observed is None else self.observed.to_dict(),
            "provider_request": (
                None if self.provider_request is None else self.provider_request.to_dict()
            ),
            "provider_request_digest": self.provider_request_digest,
            "request_digest": self.request_digest,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "stderr": self.stderr,
            "topology_digest": self.topology_digest,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.descriptor())

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "report_digest": self.digest}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )


@dataclass(frozen=True, slots=True)
class SingleGpuSelection:
    topology_digest: str | None
    requested_ordinal: int
    device: AcceleratorDevice | None
    resources: ResourceRequest
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.topology_digest is not None and _DIGEST.fullmatch(self.topology_digest) is None:
            raise TuningRuntimeError("topology_digest must be 64 lowercase hex characters or null")
        if (
            isinstance(self.requested_ordinal, bool)
            or not isinstance(self.requested_ordinal, int)
            or not 0 <= self.requested_ordinal < _MAX_DEVICES
        ):
            raise TuningRuntimeError(f"requested_ordinal must be in [0, {_MAX_DEVICES - 1}]")
        object.__setattr__(self, "blockers", tuple(sorted(set(self.blockers))))

    @property
    def ready(self) -> bool:
        return self.device is not None and not self.blockers

    def descriptor(self) -> dict[str, object]:
        return {
            "blockers": list(self.blockers),
            "device": None if self.device is None else self.device.to_dict(),
            "ready": self.ready,
            "requested_ordinal": self.requested_ordinal,
            "resources": self.resources.to_dict(),
            "strategy": "single_gpu",
            "topology_digest": self.topology_digest,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.descriptor())

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "selection_digest": self.digest}


def topology_from_worker_payload(
    payload: Mapping[str, object],
    *,
    expected_backend: TrainingBackend,
) -> ObservedAcceleratorTopology:
    allowed = {"backend_type", "device_count", "devices"}
    if set(payload) != allowed:
        raise TuningRuntimeError("worker topology evidence has unsupported or missing fields")
    backend = TrainingBackend(str(payload["backend_type"]))
    expected_backend = TrainingBackend(expected_backend)
    if backend is not expected_backend:
        raise TuningRuntimeError("worker topology backend does not match requested backend")
    device_count = payload["device_count"]
    if isinstance(device_count, bool) or not isinstance(device_count, int):
        raise TuningRuntimeError("worker topology device_count must be an integer")
    raw_devices = payload["devices"]
    if not isinstance(raw_devices, list):
        raise TuningRuntimeError("worker topology devices must be a list")
    if device_count != len(raw_devices):
        raise TuningRuntimeError("worker topology device_count does not match device list")
    devices: list[AcceleratorDevice] = []
    for raw in raw_devices:
        if not isinstance(raw, dict):
            raise TuningRuntimeError("worker topology device must be an object")
        expected = {
            "backend_type",
            "index",
            "name",
            "vram_free_bytes",
            "vram_total_bytes",
        }
        if set(raw) != expected:
            raise TuningRuntimeError("worker topology device has unsupported or missing fields")
        devices.append(
            AcceleratorDevice(
                backend_type=TrainingBackend(str(raw["backend_type"])),
                index=int(raw["index"]),
                name=str(raw["name"]),
                vram_free_bytes=raw["vram_free_bytes"],  # type: ignore[arg-type]
                vram_total_bytes=raw["vram_total_bytes"],  # type: ignore[arg-type]
            )
        )
    return ObservedAcceleratorTopology(backend_type=backend, devices=tuple(devices))


def provider_request_blockers(
    request: ProviderAcceleratorRequest | None,
    observed: ObservedAcceleratorTopology,
) -> tuple[str, ...]:
    if request is None:
        return ()
    blockers: list[str] = []
    if request.expected_backend is not observed.backend_type:
        blockers.append("provider_backend_mismatch")
    if (
        request.expected_device_count is not None
        and request.expected_device_count != observed.device_count
    ):
        blockers.append("provider_device_count_mismatch")
    marker = request.expected_name_contains
    if marker is not None and any(marker.casefold() not in device.name.casefold() for device in observed.devices):
        blockers.append("provider_device_name_mismatch")
    return tuple(sorted(blockers))


def evaluate_single_gpu_selection(
    report: AcceleratorTopologyReport,
    *,
    ordinal: int,
    resources: ResourceRequest,
) -> SingleGpuSelection:
    blockers = list(report.blockers)
    device: AcceleratorDevice | None = None
    if report.disposition is not TopologyDisposition.READY or report.observed is None:
        blockers.append("topology_not_ready")
    else:
        device = next((item for item in report.observed.devices if item.index == ordinal), None)
        if device is None:
            blockers.append("selected_device_missing")
        else:
            free_bytes = device.vram_free_bytes
            total_bytes = device.vram_total_bytes
            if free_bytes is None or total_bytes is None:
                blockers.append("vram_budget_unknown")
            else:
                policy_total = (
                    total_bytes
                    if resources.vram_total_limit_bytes is None
                    else min(total_bytes, resources.vram_total_limit_bytes)
                )
                required = resources.vram_required_free_bytes
                if required > policy_total:
                    blockers.append("vram_budget_exceeded")
                elif min(free_bytes, policy_total) < required:
                    blockers.append("vram_current_free_insufficient")
    return SingleGpuSelection(
        topology_digest=report.topology_digest,
        requested_ordinal=ordinal,
        device=device,
        resources=resources,
        blockers=tuple(blockers),
    )
