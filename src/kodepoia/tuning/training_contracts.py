from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from .contracts import DTypeName, QuantizationMode, TrainingBackend, canonical_json, canonical_sha256

TRAINING_PLAN_SCHEMA = "kodepoia.r15.9.training-plan"
TRAINING_RUN_SCHEMA = "kodepoia.r15.9.training-run"
TRAINING_SCHEMA_VERSION = 1
TRAINING_POLICY_VERSION = "r15.9-training-v1"
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+@-]{0,511}$")


class TrainingPlanError(ValueError):
    """Invalid or unsafe R15.9 training plan."""


class DatasetFormat(StrEnum):
    TEXT = "text"
    PROMPT_COMPLETION = "prompt_completion"
    CONVERSATIONAL = "conversational"


class TrainingEngine(StrEnum):
    FIXTURE = "fixture"
    TRL_PEFT = "trl_peft"


class TrainingRunState(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    BUDGET_BLOCKED = "budget_blocked"
    UNSUPPORTED = "unsupported"


def _digest(label: str, value: str) -> str:
    value = value.strip().lower()
    if _DIGEST.fullmatch(value) is None:
        raise TrainingPlanError(f"{label} must be 64 lowercase hex characters")
    return value


def _ref(label: str, value: str) -> str:
    value = value.strip()
    if _SAFE_REF.fullmatch(value) is None or ".." in value.split("/"):
        raise TrainingPlanError(f"{label} must be a bounded safe identifier")
    return value


def _positive_int(label: str, value: int, *, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise TrainingPlanError(f"{label} must be in [1, {maximum}]")
    return value


def _nonnegative_int(label: str, value: int, *, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise TrainingPlanError(f"{label} must be in [0, {maximum}]")
    return value


def _relative_path(label: str, value: str) -> str:
    raw = value.strip().replace("\\", "/")
    path = Path(raw)
    if not raw or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise TrainingPlanError(f"{label} must be a normalized relative path")
    return path.as_posix()


@dataclass(frozen=True, slots=True)
class LoraPlan:
    rank: int = 16
    alpha: int = 32
    dropout: float = 0.05
    target_modules: tuple[str, ...] | str = "all-linear"
    bias: str = "none"

    def __post_init__(self) -> None:
        _positive_int("rank", self.rank, maximum=4096)
        _positive_int("alpha", self.alpha, maximum=65536)
        if isinstance(self.dropout, bool) or not isinstance(self.dropout, (int, float)):
            raise TrainingPlanError("dropout must be numeric")
        if not math.isfinite(float(self.dropout)) or not 0.0 <= float(self.dropout) < 1.0:
            raise TrainingPlanError("dropout must be in [0, 1)")
        if self.bias not in {"none", "all", "lora_only"}:
            raise TrainingPlanError("bias is invalid")
        targets = self.target_modules
        if isinstance(targets, str):
            if targets != "all-linear":
                raise TrainingPlanError("string target_modules must be all-linear")
        else:
            if not targets or len(targets) > 256:
                raise TrainingPlanError("target_modules must be non-empty and bounded")
            cleaned = tuple(_ref("target_module", item) for item in targets)
            if len(cleaned) != len(set(cleaned)):
                raise TrainingPlanError("target_modules must be unique")
            object.__setattr__(self, "target_modules", cleaned)

    def to_dict(self) -> dict[str, object]:
        targets: object = self.target_modules
        if isinstance(targets, tuple):
            targets = list(targets)
        return {
            "alpha": self.alpha,
            "bias": self.bias,
            "dropout": float(self.dropout),
            "rank": self.rank,
            "target_modules": targets,
        }


@dataclass(frozen=True, slots=True)
class SFTPlan:
    max_steps: int = 4
    checkpoint_every_steps: int = 2
    batch_size: int = 1
    gradient_accumulation_steps: int = 1
    context_length: int = 256
    learning_rate: float = 2e-4
    assistant_only_loss: bool = False
    completion_only_loss: bool | None = None
    gradient_checkpointing: bool = False
    packing: bool = False

    def __post_init__(self) -> None:
        _positive_int("max_steps", self.max_steps, maximum=10_000_000)
        _positive_int("checkpoint_every_steps", self.checkpoint_every_steps, maximum=self.max_steps)
        _positive_int("batch_size", self.batch_size, maximum=65536)
        _positive_int("gradient_accumulation_steps", self.gradient_accumulation_steps, maximum=65536)
        _positive_int("context_length", self.context_length, maximum=1_048_576)
        if isinstance(self.learning_rate, bool) or not isinstance(self.learning_rate, (int, float)):
            raise TrainingPlanError("learning_rate must be numeric")
        if not math.isfinite(float(self.learning_rate)) or not 0.0 < float(self.learning_rate) <= 10.0:
            raise TrainingPlanError("learning_rate must be in (0, 10]")

    def to_dict(self) -> dict[str, object]:
        return {
            "assistant_only_loss": self.assistant_only_loss,
            "batch_size": self.batch_size,
            "checkpoint_every_steps": self.checkpoint_every_steps,
            "completion_only_loss": self.completion_only_loss,
            "context_length": self.context_length,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "gradient_checkpointing": self.gradient_checkpointing,
            "learning_rate": float(self.learning_rate),
            "max_steps": self.max_steps,
            "packing": self.packing,
        }


@dataclass(frozen=True, slots=True)
class TrainingBudget:
    disk_limit_bytes: int = 1 << 30
    ram_limit_bytes: int = 4 << 30
    vram_limit_bytes: int = 0
    timeout_seconds: float = 120.0

    def __post_init__(self) -> None:
        _positive_int("disk_limit_bytes", self.disk_limit_bytes, maximum=1 << 60)
        _positive_int("ram_limit_bytes", self.ram_limit_bytes, maximum=1 << 60)
        _nonnegative_int("vram_limit_bytes", self.vram_limit_bytes, maximum=1 << 60)
        if isinstance(self.timeout_seconds, bool) or not isinstance(self.timeout_seconds, (int, float)):
            raise TrainingPlanError("timeout_seconds must be numeric")
        if not math.isfinite(float(self.timeout_seconds)) or not 0.05 <= float(self.timeout_seconds) <= 7 * 24 * 3600:
            raise TrainingPlanError("timeout_seconds is outside accepted bound")

    def to_dict(self) -> dict[str, object]:
        return {
            "disk_limit_bytes": self.disk_limit_bytes,
            "ram_limit_bytes": self.ram_limit_bytes,
            "timeout_seconds": float(self.timeout_seconds),
            "vram_limit_bytes": self.vram_limit_bytes,
        }


@dataclass(frozen=True, slots=True)
class TrainingPlan:
    source_sha: str
    base_model_ref: str
    base_revision: str
    base_model_digest: str
    tokenizer_ref: str
    tokenizer_digest: str
    dataset_manifest_digest: str
    train_split_digest: str
    train_path: str
    validation_split_digest: str | None = None
    validation_path: str | None = None
    dataset_format: DatasetFormat = DatasetFormat.PROMPT_COMPLETION
    engine: TrainingEngine = TrainingEngine.FIXTURE
    backend: TrainingBackend = TrainingBackend.CPU
    dtype: DTypeName = DTypeName.FLOAT32
    quantization: QuantizationMode = QuantizationMode.NONE
    seed: int = 3407
    data_seed: int = 3407
    lora: LoraPlan = field(default_factory=LoraPlan)
    sft: SFTPlan = field(default_factory=SFTPlan)
    budget: TrainingBudget = field(default_factory=TrainingBudget)

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_sha", _digest("source_sha", self.source_sha))
        object.__setattr__(self, "base_model_ref", _ref("base_model_ref", self.base_model_ref))
        object.__setattr__(self, "base_revision", _ref("base_revision", self.base_revision))
        object.__setattr__(self, "base_model_digest", _digest("base_model_digest", self.base_model_digest))
        object.__setattr__(self, "tokenizer_ref", _ref("tokenizer_ref", self.tokenizer_ref))
        object.__setattr__(self, "tokenizer_digest", _digest("tokenizer_digest", self.tokenizer_digest))
        object.__setattr__(self, "dataset_manifest_digest", _digest("dataset_manifest_digest", self.dataset_manifest_digest))
        object.__setattr__(self, "train_split_digest", _digest("train_split_digest", self.train_split_digest))
        object.__setattr__(self, "train_path", _relative_path("train_path", self.train_path))
        if self.validation_split_digest is not None:
            object.__setattr__(self, "validation_split_digest", _digest("validation_split_digest", self.validation_split_digest))
        if self.validation_path is not None:
            object.__setattr__(self, "validation_path", _relative_path("validation_path", self.validation_path))
        if (self.validation_split_digest is None) != (self.validation_path is None):
            raise TrainingPlanError("validation digest and path must be provided together")
        if self.validation_path == self.train_path:
            raise TrainingPlanError("validation split cannot be the training path")
        object.__setattr__(self, "dataset_format", DatasetFormat(self.dataset_format))
        object.__setattr__(self, "engine", TrainingEngine(self.engine))
        object.__setattr__(self, "backend", TrainingBackend(self.backend))
        object.__setattr__(self, "dtype", DTypeName(self.dtype))
        object.__setattr__(self, "quantization", QuantizationMode(self.quantization))
        _nonnegative_int("seed", self.seed, maximum=2**31 - 1)
        _nonnegative_int("data_seed", self.data_seed, maximum=2**31 - 1)
        if self.engine is TrainingEngine.FIXTURE:
            if self.backend is not TrainingBackend.CPU or self.quantization is not QuantizationMode.NONE:
                raise TrainingPlanError("fixture engine is CPU/non-quantized only")
        if self.quantization is QuantizationMode.BNB_NF4 and self.engine is not TrainingEngine.TRL_PEFT:
            raise TrainingPlanError("NF4 requires the TRL/PEFT engine")
        if self.dataset_format is not DatasetFormat.CONVERSATIONAL and self.sft.assistant_only_loss:
            raise TrainingPlanError("assistant_only_loss requires conversational data")
        if self.dataset_format is not DatasetFormat.PROMPT_COMPLETION and self.sft.completion_only_loss is True:
            raise TrainingPlanError("completion_only_loss=true requires prompt-completion data")

    def to_dict(self) -> dict[str, object]:
        return {
            "backend": self.backend.value,
            "base_model_digest": self.base_model_digest,
            "base_model_ref": self.base_model_ref,
            "base_revision": self.base_revision,
            "budget": self.budget.to_dict(),
            "data_seed": self.data_seed,
            "dataset_format": self.dataset_format.value,
            "dataset_manifest_digest": self.dataset_manifest_digest,
            "dtype": self.dtype.value,
            "engine": self.engine.value,
            "lora": self.lora.to_dict(),
            "quantization": self.quantization.value,
            "seed": self.seed,
            "sft": self.sft.to_dict(),
            "source_sha": self.source_sha,
            "tokenizer_digest": self.tokenizer_digest,
            "tokenizer_ref": self.tokenizer_ref,
            "train_path": self.train_path,
            "train_split_digest": self.train_split_digest,
            "validation_path": self.validation_path,
            "validation_split_digest": self.validation_split_digest,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256({"policy": TRAINING_POLICY_VERSION, "plan": self.to_dict()})

    def worker_payload(self, *, output_dir: str, resume_checkpoint: str | None = None) -> dict[str, object]:
        return {
            "output_dir": _relative_path("output_dir", output_dir),
            "plan": self.to_dict(),
            "plan_digest": self.digest,
            "resume_checkpoint": None if resume_checkpoint is None else _relative_path("resume_checkpoint", resume_checkpoint),
        }


@dataclass(frozen=True, slots=True)
class CheckpointRecord:
    plan_digest: str
    step: int
    base_model_digest: str
    tokenizer_digest: str
    dataset_manifest_digest: str
    train_split_digest: str
    checkpoint_path: str
    state_digest: str

    def __post_init__(self) -> None:
        for label in ("plan_digest", "base_model_digest", "tokenizer_digest", "dataset_manifest_digest", "train_split_digest", "state_digest"):
            object.__setattr__(self, label, _digest(label, getattr(self, label)))
        _nonnegative_int("step", self.step, maximum=10_000_000)
        object.__setattr__(self, "checkpoint_path", _relative_path("checkpoint_path", self.checkpoint_path))

    def to_dict(self) -> dict[str, object]:
        return {
            "base_model_digest": self.base_model_digest,
            "checkpoint_path": self.checkpoint_path,
            "dataset_manifest_digest": self.dataset_manifest_digest,
            "plan_digest": self.plan_digest,
            "state_digest": self.state_digest,
            "step": self.step,
            "tokenizer_digest": self.tokenizer_digest,
            "train_split_digest": self.train_split_digest,
        }


@dataclass(frozen=True, slots=True)
class TrainingRunReport:
    state: TrainingRunState
    plan_digest: str
    source_sha: str
    run_id: str
    adapter_path: str | None
    adapter_digest: str | None
    checkpoint: CheckpointRecord | None
    train_loss: float | None
    eval_loss: float | None
    steps_completed: int
    packages: tuple[tuple[str, str | None], ...] = ()
    blockers: tuple[str, ...] = ()
    stderr: str = ""
    schema: str = TRAINING_RUN_SCHEMA
    schema_version: int = TRAINING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_digest", _digest("plan_digest", self.plan_digest))
        object.__setattr__(self, "source_sha", _digest("source_sha", self.source_sha))
        if not re.fullmatch(r"[0-9a-f]{16}", self.run_id):
            raise TrainingPlanError("run_id must be 16 lowercase hex characters")
        if self.adapter_path is not None:
            object.__setattr__(self, "adapter_path", _relative_path("adapter_path", self.adapter_path))
        if self.adapter_digest is not None:
            object.__setattr__(self, "adapter_digest", _digest("adapter_digest", self.adapter_digest))
        if (self.adapter_path is None) != (self.adapter_digest is None):
            raise TrainingPlanError("adapter path and digest must be present together")
        _nonnegative_int("steps_completed", self.steps_completed, maximum=10_000_000)
        if self.train_loss is not None and not math.isfinite(self.train_loss):
            raise TrainingPlanError("train_loss must be finite")
        if self.eval_loss is not None and not math.isfinite(self.eval_loss):
            raise TrainingPlanError("eval_loss must be finite")
        names = [name for name, _ in self.packages]
        if names != sorted(names) or len(names) != len(set(names)):
            raise TrainingPlanError("packages must be unique and sorted")

    def descriptor(self) -> dict[str, object]:
        return {
            "adapter_digest": self.adapter_digest,
            "adapter_path": self.adapter_path,
            "blockers": list(self.blockers),
            "checkpoint": None if self.checkpoint is None else self.checkpoint.to_dict(),
            "eval_loss": self.eval_loss,
            "packages": {name: version for name, version in self.packages},
            "plan_digest": self.plan_digest,
            "run_id": self.run_id,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "state": self.state.value,
            "stderr": self.stderr,
            "steps_completed": self.steps_completed,
            "train_loss": self.train_loss,
        }

    @property
    def digest(self) -> str:
        return hashlib.sha256(canonical_json(self.descriptor()).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "report_digest": self.digest}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
