from __future__ import annotations

import contextlib
import hashlib
import json
import math
import platform
import re
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.core.sandbox import ProcessSandbox, SandboxResult

from .contracts import QuantizationMode, ResourceRequest, SeedConfig, canonical_sha256
from .runtime import HostResourceProbe, redact_runtime_text

TRAINING_SCHEMA = "kodepoia.r15.9.training-run"
TRAINING_SCHEMA_VERSION = 1
TRAINING_POLICY_VERSION = "r15.9-training-v1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+@-]{0,511}$")
_MAX_CAPTURE_CHARS = 8192


class TrainingError(ValueError):
    """Base error for R15.9 training contracts and orchestration."""


class TrainingMode(StrEnum):
    FIXTURE_SFT = "fixture_sft"
    SFT = "sft"
    QLORA = "qlora"


class TrainingAuthorization(StrEnum):
    FIXTURE = "fixture"
    TRAIN = "train"


class TrainingRunState(StrEnum):
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    FAILED = "failed"
    BUDGET_BLOCKED = "budget_blocked"
    UNSUPPORTED = "unsupported"


def _require_digest(label: str, value: str) -> str:
    if _HEX64.fullmatch(value) is None:
        raise TrainingError(f"{label} must be 64 lowercase hex characters")
    return value


def _safe_ref(label: str, value: str) -> str:
    value = value.strip()
    if _SAFE_REF.fullmatch(value) is None or ".." in value.split("/"):
        raise TrainingError(f"{label} must be a bounded safe identifier")
    return value


def _bounded_int(label: str, value: int, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise TrainingError(f"{label} must be an integer in [{minimum}, {maximum}]")
    return value


def _bounded_float(label: str, value: float, *, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TrainingError(f"{label} must be numeric")
    value = float(value)
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise TrainingError(f"{label} must be finite in [{minimum}, {maximum}]")
    return value


@dataclass(frozen=True, slots=True)
class ModelBinding:
    model_ref: str
    model_revision: str
    model_digest: str
    tokenizer_ref: str
    tokenizer_revision: str
    tokenizer_digest: str
    assistant_mask_capable: bool | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "model_ref", _safe_ref("model_ref", self.model_ref))
        object.__setattr__(self, "model_revision", _safe_ref("model_revision", self.model_revision))
        object.__setattr__(self, "tokenizer_ref", _safe_ref("tokenizer_ref", self.tokenizer_ref))
        object.__setattr__(
            self,
            "tokenizer_revision",
            _safe_ref("tokenizer_revision", self.tokenizer_revision),
        )
        _require_digest("model_digest", self.model_digest)
        _require_digest("tokenizer_digest", self.tokenizer_digest)
        if self.assistant_mask_capable is not None and not isinstance(self.assistant_mask_capable, bool):
            raise TrainingError("assistant_mask_capable must be bool or null")

    def to_dict(self) -> dict[str, object]:
        return {
            "assistant_mask_capable": self.assistant_mask_capable,
            "model_digest": self.model_digest,
            "model_ref": self.model_ref,
            "model_revision": self.model_revision,
            "tokenizer_digest": self.tokenizer_digest,
            "tokenizer_ref": self.tokenizer_ref,
            "tokenizer_revision": self.tokenizer_revision,
        }


@dataclass(frozen=True, slots=True)
class DatasetBinding:
    dataset_id: str
    dataset_digest: str
    manifest_digest: str
    train_export_digest: str
    validation_export_digest: str
    train_rows: int
    validation_rows: int
    format: str = "prompt_completion"
    train_path: str | None = None
    validation_path: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "dataset_id", _safe_ref("dataset_id", self.dataset_id))
        for name in (
            "dataset_digest",
            "manifest_digest",
            "train_export_digest",
            "validation_export_digest",
        ):
            _require_digest(name, getattr(self, name))
        _bounded_int("train_rows", self.train_rows, minimum=1, maximum=10_000_000_000)
        _bounded_int("validation_rows", self.validation_rows, minimum=1, maximum=10_000_000_000)
        if self.format not in {"text", "prompt_completion", "conversational"}:
            raise TrainingError("dataset format must be text, prompt_completion or conversational")
        if self.train_export_digest == self.validation_export_digest:
            raise TrainingError("train and validation exports must be distinct")
        for name in ("train_path", "validation_path"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _safe_ref(name, value))
        if (self.train_path is None) != (self.validation_path is None):
            raise TrainingError("train_path and validation_path must be provided together")
        if self.train_path is not None and self.train_path == self.validation_path:
            raise TrainingError("train and validation paths must be distinct")

    def to_dict(self, *, include_paths: bool = False) -> dict[str, object]:
        payload: dict[str, object] = {
            "dataset_digest": self.dataset_digest,
            "dataset_id": self.dataset_id,
            "format": self.format,
            "manifest_digest": self.manifest_digest,
            "train_export_digest": self.train_export_digest,
            "train_rows": self.train_rows,
            "validation_export_digest": self.validation_export_digest,
            "validation_rows": self.validation_rows,
        }
        if include_paths:
            payload.update({"train_path": self.train_path, "validation_path": self.validation_path})
        return payload


@dataclass(frozen=True, slots=True)
class LoraTrainingConfig:
    rank: int = 8
    alpha: int = 16
    dropout: float = 0.0
    target_modules: tuple[str, ...] = ("all-linear",)

    def __post_init__(self) -> None:
        _bounded_int("rank", self.rank, minimum=1, maximum=4096)
        _bounded_int("alpha", self.alpha, minimum=1, maximum=65536)
        _bounded_float("dropout", self.dropout, minimum=0.0, maximum=1.0)
        if not self.target_modules or tuple(sorted(set(self.target_modules))) != self.target_modules:
            raise TrainingError("target_modules must be non-empty, unique and sorted")
        for target in self.target_modules:
            _safe_ref("target_module", target)
        if "all-linear" in self.target_modules and len(self.target_modules) != 1:
            raise TrainingError("all-linear cannot be combined with explicit target modules")

    def to_dict(self) -> dict[str, object]:
        return {
            "alpha": self.alpha,
            "dropout": float(self.dropout),
            "rank": self.rank,
            "target_modules": list(self.target_modules),
        }


@dataclass(frozen=True, slots=True)
class SFTTrainingConfig:
    max_steps: int = 4
    train_batch_size: int = 1
    eval_batch_size: int = 1
    gradient_accumulation_steps: int = 1
    context_length: int = 256
    learning_rate: float = 2e-4
    checkpoint_steps: int = 2
    eval_steps: int = 2
    gradient_checkpointing: bool = False
    completion_only_loss: bool = True
    assistant_only_loss: bool = False
    full_determinism: bool = True
    optimizer: str = "adamw_torch"
    scheduler: str = "linear"

    def __post_init__(self) -> None:
        _bounded_int("max_steps", self.max_steps, minimum=1, maximum=10_000_000)
        _bounded_int("train_batch_size", self.train_batch_size, minimum=1, maximum=65536)
        _bounded_int("eval_batch_size", self.eval_batch_size, minimum=1, maximum=65536)
        _bounded_int(
            "gradient_accumulation_steps",
            self.gradient_accumulation_steps,
            minimum=1,
            maximum=65536,
        )
        _bounded_int("context_length", self.context_length, minimum=8, maximum=1_048_576)
        _bounded_float("learning_rate", self.learning_rate, minimum=1e-12, maximum=10.0)
        _bounded_int("checkpoint_steps", self.checkpoint_steps, minimum=1, maximum=self.max_steps)
        _bounded_int("eval_steps", self.eval_steps, minimum=1, maximum=self.max_steps)
        object.__setattr__(self, "optimizer", _safe_ref("optimizer", self.optimizer))
        object.__setattr__(self, "scheduler", _safe_ref("scheduler", self.scheduler))

    def to_dict(self) -> dict[str, object]:
        return {
            "assistant_only_loss": self.assistant_only_loss,
            "checkpoint_steps": self.checkpoint_steps,
            "completion_only_loss": self.completion_only_loss,
            "context_length": self.context_length,
            "eval_batch_size": self.eval_batch_size,
            "eval_steps": self.eval_steps,
            "full_determinism": self.full_determinism,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "gradient_checkpointing": self.gradient_checkpointing,
            "learning_rate": float(self.learning_rate),
            "max_steps": self.max_steps,
            "optimizer": self.optimizer,
            "scheduler": self.scheduler,
            "train_batch_size": self.train_batch_size,
        }


@dataclass(frozen=True, slots=True)
class TrainingPlan:
    mode: TrainingMode
    authorization: TrainingAuthorization
    model: ModelBinding
    dataset: DatasetBinding
    lora: LoraTrainingConfig = LoraTrainingConfig()
    sft: SFTTrainingConfig = SFTTrainingConfig()
    quantization: QuantizationMode = QuantizationMode.NONE
    seeds: SeedConfig = SeedConfig()
    resources: ResourceRequest = ResourceRequest()
    timeout_seconds: float = 300.0
    capability_report_digest: str | None = None
    fixture_authorization: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", TrainingMode(self.mode))
        object.__setattr__(self, "authorization", TrainingAuthorization(self.authorization))
        object.__setattr__(self, "quantization", QuantizationMode(self.quantization))
        _bounded_float("timeout_seconds", self.timeout_seconds, minimum=0.05, maximum=86_400.0)
        if self.capability_report_digest is not None:
            _require_digest("capability_report_digest", self.capability_report_digest)
        if self.mode is TrainingMode.FIXTURE_SFT:
            if self.authorization is not TrainingAuthorization.FIXTURE:
                raise TrainingError("fixture_sft requires fixture authorization")
            if self.fixture_authorization != "repository-owned-r15.9-fixture":
                raise TrainingError("fixture_sft requires the repository-owned fixture authorization")
            if self.quantization is not QuantizationMode.NONE:
                raise TrainingError("fixture_sft does not claim 4-bit capability")
        else:
            if self.authorization is not TrainingAuthorization.TRAIN:
                raise TrainingError("real SFT/QLoRA requires a governed TRAIN authorization")
            if self.capability_report_digest is None:
                raise TrainingError("real SFT/QLoRA requires an R15.8 capability report digest")
            if self.dataset.train_path is None:
                raise TrainingError("real SFT/QLoRA requires explicit governed train/validation paths")
        if self.mode is TrainingMode.QLORA and self.quantization is not QuantizationMode.BNB_NF4:
            raise TrainingError("QLoRA requires capability-probed NF4 quantization")
        if self.mode is TrainingMode.SFT and self.quantization is not QuantizationMode.NONE:
            raise TrainingError("non-QLoRA SFT must not silently enable quantization")
        if self.sft.assistant_only_loss:
            if self.dataset.format != "conversational":
                raise TrainingError("assistant_only_loss requires a conversational dataset")
            if self.model.assistant_mask_capable is not True:
                raise TrainingError("assistant_only_loss requires verified generation-mask capability")
        if self.sft.completion_only_loss and self.dataset.format != "prompt_completion":
            raise TrainingError("completion_only_loss requires a prompt_completion dataset")

    def descriptor(self) -> dict[str, object]:
        return {
            "authorization": self.authorization.value,
            "capability_report_digest": self.capability_report_digest,
            "dataset": self.dataset.to_dict(),
            "fixture_authorization": self.fixture_authorization,
            "lora": self.lora.to_dict(),
            "mode": self.mode.value,
            "model": self.model.to_dict(),
            "policy_version": TRAINING_POLICY_VERSION,
            "quantization": self.quantization.value,
            "resources": self.resources.to_dict(),
            "seeds": self.seeds.to_dict(),
            "sft": self.sft.to_dict(),
            "timeout_seconds": float(self.timeout_seconds),
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.descriptor())

    @property
    def run_id(self) -> str:
        return f"train-{self.digest[:20]}"

    def worker_payload(self, root: Path, run_dir: Path, resume_checkpoint: Path | None) -> dict[str, object]:
        payload = self.descriptor()
        payload.update(
            {
                "dataset_paths": self.dataset.to_dict(include_paths=True),
                "plan_digest": self.digest,
                "resume_checkpoint": (
                    None if resume_checkpoint is None else str(resume_checkpoint.relative_to(root))
                ),
                "run_dir": str(run_dir.relative_to(root)),
                "schema": TRAINING_SCHEMA,
                "schema_version": TRAINING_SCHEMA_VERSION,
            }
        )
        return payload


@dataclass(frozen=True, slots=True)
class CheckpointRecord:
    checkpoint_id: str
    plan_digest: str
    step: int
    artifact_path: str
    artifact_digest: str
    train_loss: float
    eval_loss: float

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> CheckpointRecord:
        record = cls(
            checkpoint_id=str(value["checkpoint_id"]),
            plan_digest=str(value["plan_digest"]),
            step=int(value["step"]),
            artifact_path=str(value["artifact_path"]),
            artifact_digest=str(value["artifact_digest"]),
            train_loss=float(value["train_loss"]),
            eval_loss=float(value["eval_loss"]),
        )
        _safe_ref("checkpoint_id", record.checkpoint_id)
        _require_digest("checkpoint plan_digest", record.plan_digest)
        _require_digest("checkpoint artifact_digest", record.artifact_digest)
        _bounded_int("checkpoint step", record.step, minimum=1, maximum=10_000_000)
        _bounded_float("checkpoint train_loss", record.train_loss, minimum=0.0, maximum=1e12)
        _bounded_float("checkpoint eval_loss", record.eval_loss, minimum=0.0, maximum=1e12)
        return record

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_digest": self.artifact_digest,
            "artifact_path": self.artifact_path,
            "checkpoint_id": self.checkpoint_id,
            "eval_loss": self.eval_loss,
            "plan_digest": self.plan_digest,
            "step": self.step,
            "train_loss": self.train_loss,
        }


@dataclass(frozen=True, slots=True)
class TrainingReport:
    plan_digest: str
    run_id: str
    state: TrainingRunState
    adapter_path: str | None
    adapter_digest: str | None
    checkpoints: tuple[CheckpointRecord, ...]
    completed_steps: int
    train_loss: float | None
    eval_loss: float | None
    train_rows: int
    validation_rows: int
    optimized_splits: tuple[str, ...]
    framework_versions: tuple[tuple[str, str | None], ...]
    resumed_from: str | None
    blockers: tuple[str, ...] = ()
    stderr: str = ""
    schema: str = TRAINING_SCHEMA
    schema_version: int = TRAINING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_digest("plan_digest", self.plan_digest)
        _safe_ref("run_id", self.run_id)
        if self.adapter_digest is not None:
            _require_digest("adapter_digest", self.adapter_digest)
        if self.adapter_path is not None:
            _safe_ref("adapter_path", self.adapter_path)
        if tuple(sorted(set(self.optimized_splits))) != self.optimized_splits:
            raise TrainingError("optimized_splits must be unique and sorted")
        if self.state is TrainingRunState.COMPLETED and self.optimized_splits != ("train",):
            raise TrainingError("completed training must optimize only the train split")
        names = [name for name, _ in self.framework_versions]
        if names != sorted(names) or len(names) != len(set(names)):
            raise TrainingError("framework_versions must be unique and sorted")

    def descriptor(self) -> dict[str, object]:
        return {
            "adapter_digest": self.adapter_digest,
            "adapter_path": self.adapter_path,
            "blockers": list(self.blockers),
            "checkpoints": [item.to_dict() for item in self.checkpoints],
            "completed_steps": self.completed_steps,
            "eval_loss": self.eval_loss,
            "framework_versions": {name: version for name, version in self.framework_versions},
            "optimized_splits": list(self.optimized_splits),
            "plan_digest": self.plan_digest,
            "resumed_from": self.resumed_from,
            "run_id": self.run_id,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "state": self.state.value,
            "stderr": self.stderr,
            "train_loss": self.train_loss,
            "train_rows": self.train_rows,
            "validation_rows": self.validation_rows,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.descriptor())

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "report_digest": self.digest}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


class TrainingSandbox(Protocol):
    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: Mapping[str, str] | None = None,
    ) -> SandboxResult: ...


class TrainingRunner:
    """Structured R15.9 launcher using ProcessSandbox/KillSwitch and immutable lineage."""

    def __init__(
        self,
        root: Path,
        *,
        kill_switch: KillSwitch | None = None,
        sandbox: TrainingSandbox | None = None,
        resource_probe: HostResourceProbe | None = None,
    ) -> None:
        self.root = root.resolve(strict=False)
        self.root.mkdir(parents=True, exist_ok=True)
        self.kill_switch = kill_switch or GLOBAL_KILL_SWITCH
        self.sandbox = sandbox or ProcessSandbox(
            self.root,
            allowed_executables={Path(sys.executable).name},
            kill_switch=self.kill_switch,
        )
        self.resource_probe = resource_probe or HostResourceProbe()

    def run(self, plan: TrainingPlan, *, resume_checkpoint: str | None = None) -> TrainingReport:
        blocked = self._budget_blockers(plan)
        if blocked:
            return self._terminal(plan, TrainingRunState.BUDGET_BLOCKED, blockers=blocked)

        checkpoint_path: Path | None = None
        resumed_from: str | None = None
        if resume_checkpoint is not None:
            checkpoint_path = self._inside(resume_checkpoint)
            checkpoint = self._load_checkpoint(checkpoint_path)
            if checkpoint.plan_digest != plan.digest:
                raise TrainingError("resume checkpoint plan lineage does not match TrainingPlan")
            if checkpoint.step >= plan.sft.max_steps:
                raise TrainingError("resume checkpoint is already at or beyond max_steps")
            resumed_from = checkpoint.checkpoint_id

        run_dir = self.root / "tuning-runs" / plan.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        payload = plan.worker_payload(self.root, run_dir, checkpoint_path)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            prefix="r15_9_",
            dir=self.root,
            delete=False,
        ) as handle:
            config_path = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        try:
            with contextlib.suppress(OSError):
                config_path.chmod(0o600)
            argv = [sys.executable, "-m", "kodepoia.tuning.train_worker", config_path.name]
            result = self.sandbox.run(
                argv,
                cwd=self.root,
                timeout=float(plan.timeout_seconds),
                env={},
            )
        except RuntimeError as exc:
            state = TrainingRunState.CANCELLED if self.kill_switch.triggered else TrainingRunState.FAILED
            return self._terminal(plan, state, stderr=redact_runtime_text(str(exc)))
        finally:
            config_path.unlink(missing_ok=True)

        stderr = redact_runtime_text(result.stderr)[:_MAX_CAPTURE_CHARS]
        if result.timed_out:
            return self._terminal(plan, TrainingRunState.TIMED_OUT, stderr=stderr)
        if result.cancelled:
            return self._terminal(plan, TrainingRunState.CANCELLED, stderr=stderr)
        if result.returncode != 0:
            return self._terminal(plan, TrainingRunState.FAILED, stderr=stderr)
        try:
            output = json.loads(result.stdout)
            return self._validate_worker_report(plan, output, resumed_from, stderr)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError) as exc:
            combined = redact_runtime_text(f"{stderr}\n{exc}")[:_MAX_CAPTURE_CHARS]
            return self._terminal(plan, TrainingRunState.FAILED, stderr=combined)

    def _budget_blockers(self, plan: TrainingPlan) -> tuple[str, ...]:
        host = self.resource_probe.sample(self.root)
        blockers: list[str] = []
        if plan.resources.disk_required_bytes > 0:
            if host.disk_free_bytes is None:
                blockers.append("storage_budget_unknown")
            elif host.disk_free_bytes < plan.resources.disk_required_bytes:
                blockers.append("storage_budget_exceeded")
        if plan.resources.ram_required_bytes > 0:
            if host.ram_free_bytes is None:
                blockers.append("ram_budget_unknown")
            elif host.ram_free_bytes < plan.resources.ram_required_bytes:
                blockers.append("ram_budget_exceeded")
        return tuple(sorted(blockers))

    def _inside(self, value: str) -> Path:
        path = (self.root / value).resolve(strict=False)
        if path != self.root and self.root not in path.parents:
            raise TrainingError("checkpoint path escapes training root")
        return path

    def _load_checkpoint(self, path: Path) -> CheckpointRecord:
        payload = json.loads(path.read_text(encoding="utf-8"))
        record = CheckpointRecord.from_dict(payload)
        artifact = self._inside(record.artifact_path)
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != record.artifact_digest:
            raise TrainingError("resume checkpoint artifact digest mismatch")
        return record

    def _validate_worker_report(
        self,
        plan: TrainingPlan,
        output: object,
        resumed_from: str | None,
        stderr: str,
    ) -> TrainingReport:
        if not isinstance(output, dict):
            raise TrainingError("training worker output must be an object")
        expected = {
            "adapter_digest",
            "adapter_path",
            "checkpoints",
            "completed_steps",
            "eval_loss",
            "framework_versions",
            "optimized_splits",
            "plan_digest",
            "train_loss",
            "train_rows",
            "validation_rows",
        }
        if set(output) != expected:
            raise TrainingError("training worker output fields do not match contract")
        if output["plan_digest"] != plan.digest:
            raise TrainingError("training worker plan digest mismatch")
        adapter_path = self._inside(str(output["adapter_path"]))
        adapter_digest = _require_digest("adapter_digest", str(output["adapter_digest"]))
        if hashlib.sha256(adapter_path.read_bytes()).hexdigest() != adapter_digest:
            raise TrainingError("adapter artifact digest mismatch")
        checkpoints_raw = output["checkpoints"]
        if not isinstance(checkpoints_raw, list):
            raise TrainingError("checkpoints must be a list")
        checkpoints = tuple(CheckpointRecord.from_dict(item) for item in checkpoints_raw)
        for checkpoint in checkpoints:
            if checkpoint.plan_digest != plan.digest:
                raise TrainingError("checkpoint lineage mismatch")
            artifact = self._inside(checkpoint.artifact_path)
            if hashlib.sha256(artifact.read_bytes()).hexdigest() != checkpoint.artifact_digest:
                raise TrainingError("checkpoint artifact digest mismatch")
        versions_raw = output["framework_versions"]
        if not isinstance(versions_raw, dict):
            raise TrainingError("framework_versions must be an object")
        versions = tuple(
            sorted(
                (str(name), None if version is None else str(version))
                for name, version in versions_raw.items()
            )
        )
        optimized = tuple(str(item) for item in output["optimized_splits"])
        report = TrainingReport(
            plan_digest=plan.digest,
            run_id=plan.run_id,
            state=TrainingRunState.COMPLETED,
            adapter_path=str(adapter_path.relative_to(self.root)),
            adapter_digest=adapter_digest,
            checkpoints=checkpoints,
            completed_steps=int(output["completed_steps"]),
            train_loss=float(output["train_loss"]),
            eval_loss=float(output["eval_loss"]),
            train_rows=int(output["train_rows"]),
            validation_rows=int(output["validation_rows"]),
            optimized_splits=tuple(sorted(optimized)),
            framework_versions=versions,
            resumed_from=resumed_from,
            stderr=stderr,
        )
        if report.completed_steps != plan.sft.max_steps:
            raise TrainingError("training worker did not reach declared max_steps")
        if (
            report.train_rows != plan.dataset.train_rows
            or report.validation_rows != plan.dataset.validation_rows
        ):
            raise TrainingError("training worker dataset row evidence mismatch")
        return report

    def _terminal(
        self,
        plan: TrainingPlan,
        state: TrainingRunState,
        *,
        blockers: tuple[str, ...] = (),
        stderr: str = "",
    ) -> TrainingReport:
        return TrainingReport(
            plan_digest=plan.digest,
            run_id=plan.run_id,
            state=state,
            adapter_path=None,
            adapter_digest=None,
            checkpoints=(),
            completed_steps=0,
            train_loss=None,
            eval_loss=None,
            train_rows=plan.dataset.train_rows,
            validation_rows=plan.dataset.validation_rows,
            optimized_splits=(),
            framework_versions=(("python", platform.python_version()),),
            resumed_from=None,
            blockers=blockers or (state.value,),
            stderr=stderr,
        )
