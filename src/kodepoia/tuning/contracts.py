from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

CAPABILITY_SCHEMA = "kodepoia.r15.8.training-runtime-capability"
CAPABILITY_SCHEMA_VERSION = 1
RUNTIME_POLICY_VERSION = "r15.8-training-runtime-v1"
_SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+@-]{0,511}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_MAX_BYTES = 1 << 60


class TuningRuntimeError(ValueError):
    """Base error for R15.8 training-runtime contracts."""


class TrainingBackend(StrEnum):
    CPU = "cpu"
    CUDA = "cuda"
    ROCM = "rocm"


class CapabilityState(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class RuntimeDisposition(StrEnum):
    READY = "ready"
    UNSUPPORTED = "unsupported"
    BUDGET_BLOCKED = "budget_blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class DTypeName(StrEnum):
    FLOAT32 = "float32"
    FLOAT16 = "float16"
    BFLOAT16 = "bfloat16"


class QuantizationMode(StrEnum):
    NONE = "none"
    BNB_NF4 = "bnb_nf4"


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _bounded_bytes(label: str, value: int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= _MAX_BYTES:
        raise TuningRuntimeError(f"{label} must be a non-negative bounded integer or null")
    return value


def _safe_ref(label: str, value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if _SAFE_REF.fullmatch(value) is None or ".." in value.split("/"):
        raise TuningRuntimeError(f"{label} must be a bounded safe local/model identifier")
    return value


@dataclass(frozen=True, slots=True)
class SeedConfig:
    seed: int = 3407
    data_seed: int = 3407

    def __post_init__(self) -> None:
        for name, value in (("seed", self.seed), ("data_seed", self.data_seed)):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2**31 - 1:
                raise TuningRuntimeError(f"{name} must be an integer in [0, 2^31-1]")

    def to_dict(self) -> dict[str, int]:
        return {"data_seed": self.data_seed, "seed": self.seed}


@dataclass(frozen=True, slots=True)
class ResourceRequest:
    disk_required_bytes: int = 0
    ram_required_bytes: int = 0
    vram_estimate_bytes: int = 0
    vram_reserve_bytes: int = 0
    vram_headroom_bytes: int = 0
    vram_total_limit_bytes: int | None = None

    def __post_init__(self) -> None:
        for name in (
            "disk_required_bytes",
            "ram_required_bytes",
            "vram_estimate_bytes",
            "vram_reserve_bytes",
            "vram_headroom_bytes",
            "vram_total_limit_bytes",
        ):
            _bounded_bytes(name, getattr(self, name))
        if self.vram_total_limit_bytes == 0:
            raise TuningRuntimeError("vram_total_limit_bytes must be positive or null")
        if self.vram_required_free_bytes > _MAX_BYTES:
            raise TuningRuntimeError("combined VRAM requirement exceeds accepted bound")

    @property
    def vram_required_free_bytes(self) -> int:
        return self.vram_estimate_bytes + self.vram_reserve_bytes + self.vram_headroom_bytes

    def to_dict(self) -> dict[str, int | None]:
        return {
            "disk_required_bytes": self.disk_required_bytes,
            "ram_required_bytes": self.ram_required_bytes,
            "vram_estimate_bytes": self.vram_estimate_bytes,
            "vram_headroom_bytes": self.vram_headroom_bytes,
            "vram_required_free_bytes": self.vram_required_free_bytes,
            "vram_reserve_bytes": self.vram_reserve_bytes,
            "vram_total_limit_bytes": self.vram_total_limit_bytes,
        }


@dataclass(frozen=True, slots=True)
class RuntimeRequest:
    backend: TrainingBackend = TrainingBackend.CPU
    dtype: DTypeName = DTypeName.FLOAT32
    quantization: QuantizationMode = QuantizationMode.NONE
    seeds: SeedConfig = SeedConfig()
    resources: ResourceRequest = ResourceRequest()
    timeout_seconds: float = 60.0
    model_ref: str | None = None
    model_revision: str | None = None
    tokenizer_ref: str | None = None
    model_load_dry_run: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "backend", TrainingBackend(self.backend))
        object.__setattr__(self, "dtype", DTypeName(self.dtype))
        object.__setattr__(self, "quantization", QuantizationMode(self.quantization))
        if isinstance(self.timeout_seconds, bool) or not isinstance(self.timeout_seconds, (int, float)):
            raise TuningRuntimeError("timeout_seconds must be numeric")
        if not math.isfinite(float(self.timeout_seconds)) or not 0.05 <= float(self.timeout_seconds) <= 3600:
            raise TuningRuntimeError("timeout_seconds must be in [0.05, 3600]")
        object.__setattr__(self, "model_ref", _safe_ref("model_ref", self.model_ref))
        object.__setattr__(self, "model_revision", _safe_ref("model_revision", self.model_revision))
        object.__setattr__(self, "tokenizer_ref", _safe_ref("tokenizer_ref", self.tokenizer_ref))
        if self.model_load_dry_run and self.model_ref is None:
            raise TuningRuntimeError("model_load_dry_run requires model_ref")
        if self.quantization is QuantizationMode.BNB_NF4 and self.backend is TrainingBackend.CPU:
            raise TuningRuntimeError("bnb_nf4 requires an accelerator backend probe")

    def to_dict(self) -> dict[str, object]:
        return {
            "backend": self.backend.value,
            "dtype": self.dtype.value,
            "model_load_dry_run": self.model_load_dry_run,
            "model_ref": self.model_ref,
            "model_revision": self.model_revision,
            "quantization": self.quantization.value,
            "resources": self.resources.to_dict(),
            "seeds": self.seeds.to_dict(),
            "timeout_seconds": float(self.timeout_seconds),
            "tokenizer_ref": self.tokenizer_ref,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256({"policy": RUNTIME_POLICY_VERSION, "request": self.to_dict()})

    def worker_payload(self, action: str) -> dict[str, object]:
        if action not in {"probe", "model_load"}:
            raise TuningRuntimeError("worker action must be probe or model_load")
        return {
            "action": action,
            "backend": self.backend.value,
            "dtype": self.dtype.value,
            "model_ref": self.model_ref if action == "model_load" else None,
            "model_revision": self.model_revision if action == "model_load" else None,
            "quantization": self.quantization.value,
            "seeds": self.seeds.to_dict(),
            "tokenizer_ref": self.tokenizer_ref if action == "model_load" else None,
        }


@dataclass(frozen=True, slots=True)
class ResourcePreflight:
    disk_free_bytes: int | None
    ram_free_bytes: int | None
    vram_free_bytes: int | None
    vram_total_bytes: int | None
    blockers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "blockers": list(self.blockers),
            "disk": {
                "metric": "storage_mb",
                "free_bytes": self.disk_free_bytes,
            },
            "ram": {
                "metric": "ram_mb",
                "free_bytes": self.ram_free_bytes,
            },
            "vram": {
                "metric": "vram_mb",
                "free_bytes": self.vram_free_bytes,
                "total_bytes": self.vram_total_bytes,
            },
        }


@dataclass(frozen=True, slots=True)
class CapabilityReport:
    disposition: RuntimeDisposition
    request_digest: str
    backend: TrainingBackend
    backend_capability: CapabilityState
    dtype_supported: bool | None
    four_bit_supported: bool | None
    packages: tuple[tuple[str, str | None], ...]
    python_version: str
    torch_backend_version: str | None
    device: Mapping[str, object] | None
    resources: ResourcePreflight
    seed_applied: bool | None
    model_load: CapabilityState | None
    blockers: tuple[str, ...]
    stderr: str = ""
    schema: str = CAPABILITY_SCHEMA
    schema_version: int = CAPABILITY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not _DIGEST.fullmatch(self.request_digest):
            raise TuningRuntimeError("request_digest must be 64 lowercase hex characters")
        names = [name for name, _ in self.packages]
        if names != sorted(names) or len(names) != len(set(names)):
            raise TuningRuntimeError("package evidence must be unique and sorted")

    def descriptor(self) -> dict[str, object]:
        return {
            "backend": self.backend.value,
            "backend_capability": self.backend_capability.value,
            "blockers": list(self.blockers),
            "device": None if self.device is None else dict(self.device),
            "disposition": self.disposition.value,
            "dtype_supported": self.dtype_supported,
            "four_bit_supported": self.four_bit_supported,
            "model_load": None if self.model_load is None else self.model_load.value,
            "packages": {name: version for name, version in self.packages},
            "python_version": self.python_version,
            "request_digest": self.request_digest,
            "resources": self.resources.to_dict(),
            "schema": self.schema,
            "schema_version": self.schema_version,
            "seed_applied": self.seed_applied,
            "stderr": self.stderr,
            "torch_backend_version": self.torch_backend_version,
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
