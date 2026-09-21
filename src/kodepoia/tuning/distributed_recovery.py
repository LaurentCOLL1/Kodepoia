from __future__ import annotations

import contextlib
import hashlib
import json
import math
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.core.sandbox import ProcessSandbox, SandboxResult

from .contracts import TuningRuntimeError, canonical_sha256
from .distributed import (
    DISTRIBUTED_LAUNCH_POLICY,
    DistributedExecutionPlan,
    DistributedExecutionState,
    DistributedRankEvidence,
    DistributedRankState,
    DistributedTrainingReport,
    build_distributed_execution_plan,
)
from .runtime import HostResourceProbe, redact_runtime_text
from .strategy import ExecutionStrategyPlan, StrategyBenchmarkReport
from .training import CheckpointRecord, TrainingPlan, TrainingReport, TrainingRunner

DISTRIBUTED_CHECKPOINT_SCHEMA = "kodepoia.v2.4.4.distributed-checkpoint-manifest"
DISTRIBUTED_CHECKPOINT_SCHEMA_VERSION = 1
DISTRIBUTED_RECOVERY_PLAN_SCHEMA = "kodepoia.v2.4.4.distributed-recovery-plan"
DISTRIBUTED_RECOVERY_PLAN_SCHEMA_VERSION = 1
DISTRIBUTED_RECOVERY_REPORT_SCHEMA = "kodepoia.v2.4.4.distributed-recovery-report"
DISTRIBUTED_RECOVERY_REPORT_SCHEMA_VERSION = 1
DISTRIBUTED_RECOVERY_WORKER_CONFIG_SCHEMA = "kodepoia.v2.4.4.distributed-recovery-worker-config"
DISTRIBUTED_RECOVERY_WORKER_CONFIG_SCHEMA_VERSION = 1

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+@-]{0,511}$")
_MAX_CAPTURE_CHARS = 8192


def _require_digest(label: str, value: str) -> str:
    if _HEX64.fullmatch(value) is None:
        raise TuningRuntimeError(f"{label} must be 64 lowercase hex characters")
    return value


def _safe_ref(label: str, value: str) -> str:
    value = value.strip()
    if _SAFE_REF.fullmatch(value) is None or ".." in value.split("/"):
        raise TuningRuntimeError(f"{label} must be a bounded safe identifier")
    return value


def _inside(root: Path, value: str) -> Path:
    path = (root / value).resolve(strict=False)
    if path != root and root not in path.parents:
        raise TuningRuntimeError("distributed recovery path escapes training root")
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bounded_loss(label: str, value: float | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TuningRuntimeError(f"{label} must be numeric or null")
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise TuningRuntimeError(f"{label} must be finite and non-negative")
    return value


@dataclass(frozen=True, slots=True)
class DistributedCheckpointManifest:
    source_run_id: str
    source_report_digest: str
    execution_plan_digest: str
    canonical_training_report_digest: str
    training_plan_digest: str
    strategy_plan_digest: str
    benchmark_report_digest: str
    topology_digest: str
    world_size: int
    device_ordinals: tuple[int, int]
    checkpoint_id: str
    step: int
    checkpoint_metadata_path: str
    checkpoint_metadata_digest: str
    checkpoint_artifact_path: str
    checkpoint_artifact_digest: str
    rank_evidence_digests: tuple[str, str]
    canonical_rank: int = 0
    schema: str = DISTRIBUTED_CHECKPOINT_SCHEMA
    schema_version: int = DISTRIBUTED_CHECKPOINT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_run_id", _safe_ref("source_run_id", self.source_run_id))
        object.__setattr__(self, "checkpoint_id", _safe_ref("checkpoint_id", self.checkpoint_id))
        object.__setattr__(
            self,
            "checkpoint_metadata_path",
            _safe_ref("checkpoint_metadata_path", self.checkpoint_metadata_path),
        )
        object.__setattr__(
            self,
            "checkpoint_artifact_path",
            _safe_ref("checkpoint_artifact_path", self.checkpoint_artifact_path),
        )
        for label in (
            "source_report_digest",
            "execution_plan_digest",
            "canonical_training_report_digest",
            "training_plan_digest",
            "strategy_plan_digest",
            "benchmark_report_digest",
            "topology_digest",
            "checkpoint_metadata_digest",
            "checkpoint_artifact_digest",
        ):
            _require_digest(label, getattr(self, label))
        if self.world_size != 2:
            raise TuningRuntimeError("distributed checkpoint world_size must be 2")
        ordinals = tuple(self.device_ordinals)
        object.__setattr__(self, "device_ordinals", ordinals)
        if len(ordinals) != 2 or ordinals != tuple(sorted(set(ordinals))):
            raise TuningRuntimeError("distributed checkpoint device ordinals must contain two unique values")
        if isinstance(self.step, bool) or not isinstance(self.step, int) or self.step < 1:
            raise TuningRuntimeError("distributed checkpoint step must be positive")
        digests = tuple(self.rank_evidence_digests)
        object.__setattr__(self, "rank_evidence_digests", digests)
        if len(digests) != 2:
            raise TuningRuntimeError("distributed checkpoint requires exactly two rank evidence digests")
        for value in digests:
            _require_digest("rank_evidence_digest", value)
        if self.canonical_rank != 0:
            raise TuningRuntimeError("distributed checkpoint canonical rank must be zero")

    def descriptor(self) -> dict[str, object]:
        return {
            "benchmark_report_digest": self.benchmark_report_digest,
            "canonical_rank": self.canonical_rank,
            "canonical_training_report_digest": self.canonical_training_report_digest,
            "checkpoint_artifact_digest": self.checkpoint_artifact_digest,
            "checkpoint_artifact_path": self.checkpoint_artifact_path,
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_metadata_digest": self.checkpoint_metadata_digest,
            "checkpoint_metadata_path": self.checkpoint_metadata_path,
            "device_ordinals": list(self.device_ordinals),
            "execution_plan_digest": self.execution_plan_digest,
            "rank_evidence_digests": list(self.rank_evidence_digests),
            "schema": self.schema,
            "schema_version": self.schema_version,
            "source_report_digest": self.source_report_digest,
            "source_run_id": self.source_run_id,
            "step": self.step,
            "strategy_plan_digest": self.strategy_plan_digest,
            "topology_digest": self.topology_digest,
            "training_plan_digest": self.training_plan_digest,
            "world_size": self.world_size,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.descriptor())

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "manifest_digest": self.digest}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_distributed_checkpoint_manifest(
    root: Path,
    training_plan: TrainingPlan,
    strategy_plan: ExecutionStrategyPlan,
    benchmark_report: StrategyBenchmarkReport,
    source_report: DistributedTrainingReport,
    *,
    checkpoint_id: str,
) -> DistributedCheckpointManifest:
    root = root.resolve(strict=False)
    execution = build_distributed_execution_plan(training_plan, strategy_plan, benchmark_report)
    if source_report.state is not DistributedExecutionState.COMPLETED:
        raise TuningRuntimeError("checkpoint lineage requires a completed distributed source report")
    if source_report.execution_plan_digest != execution.digest:
        raise TuningRuntimeError("checkpoint source execution plan lineage mismatch")
    if source_report.training_plan_digest != training_plan.digest:
        raise TuningRuntimeError("checkpoint source TrainingPlan lineage mismatch")
    if source_report.strategy_plan_digest != strategy_plan.digest:
        raise TuningRuntimeError("checkpoint source strategy lineage mismatch")
    if source_report.benchmark_report_digest != benchmark_report.digest:
        raise TuningRuntimeError("checkpoint source benchmark lineage mismatch")
    if source_report.topology_digest != execution.topology_digest:
        raise TuningRuntimeError("checkpoint source topology lineage mismatch")
    if source_report.canonical_training_report_digest is None:
        raise TuningRuntimeError("checkpoint source lacks canonical training report evidence")
    ranks = tuple(source_report.rank_evidence)
    if tuple(item.rank for item in ranks) != (0, 1):
        raise TuningRuntimeError("checkpoint source requires complete two-rank evidence")
    if any(item.state is not DistributedRankState.COMPLETED for item in ranks):
        raise TuningRuntimeError("checkpoint source rank evidence is incomplete")
    for item in ranks:
        if item.execution_plan_digest != execution.digest:
            raise TuningRuntimeError("checkpoint source rank execution lineage mismatch")

    run_dir = root / "distributed-runs" / source_report.run_id
    canonical_path = run_dir / "canonical-worker-output.json"
    output = json.loads(canonical_path.read_text(encoding="utf-8"))
    if ranks[0].canonical_output_digest != canonical_sha256(output):
        raise TuningRuntimeError("checkpoint source canonical output digest mismatch")
    raw_checkpoints = output.get("checkpoints")
    if not isinstance(raw_checkpoints, list):
        raise TuningRuntimeError("checkpoint source canonical output has no checkpoint list")
    matches = [
        CheckpointRecord.from_dict(item)
        for item in raw_checkpoints
        if isinstance(item, Mapping) and str(item.get("checkpoint_id")) == checkpoint_id
    ]
    if len(matches) != 1:
        raise TuningRuntimeError("checkpoint source must contain exactly one requested checkpoint")
    checkpoint = matches[0]
    if checkpoint.plan_digest != training_plan.digest:
        raise TuningRuntimeError("checkpoint TrainingPlan lineage mismatch")
    if checkpoint.step >= training_plan.sft.max_steps:
        raise TuningRuntimeError("distributed resume checkpoint must precede max_steps")
    artifact = _inside(root, checkpoint.artifact_path)
    if not artifact.is_file() or _sha256(artifact) != checkpoint.artifact_digest:
        raise TuningRuntimeError("distributed checkpoint artifact digest mismatch")
    metadata = artifact.parent / "checkpoint.json"
    metadata_payload = json.loads(metadata.read_text(encoding="utf-8"))
    if metadata_payload != checkpoint.to_dict():
        raise TuningRuntimeError("distributed checkpoint metadata does not match canonical checkpoint")
    metadata_digest = _sha256(metadata)
    rank_digests = tuple(canonical_sha256(item.to_dict()) for item in ranks)
    return DistributedCheckpointManifest(
        source_run_id=source_report.run_id,
        source_report_digest=source_report.digest,
        execution_plan_digest=execution.digest,
        canonical_training_report_digest=source_report.canonical_training_report_digest,
        training_plan_digest=training_plan.digest,
        strategy_plan_digest=strategy_plan.digest,
        benchmark_report_digest=benchmark_report.digest,
        topology_digest=execution.topology_digest,
        world_size=2,
        device_ordinals=execution.device_ordinals,
        checkpoint_id=checkpoint.checkpoint_id,
        step=checkpoint.step,
        checkpoint_metadata_path=metadata.relative_to(root).as_posix(),
        checkpoint_metadata_digest=metadata_digest,
        checkpoint_artifact_path=checkpoint.artifact_path,
        checkpoint_artifact_digest=checkpoint.artifact_digest,
        rank_evidence_digests=(rank_digests[0], rank_digests[1]),
    )


@dataclass(frozen=True, slots=True)
class DistributedRecoveryPlan:
    execution_plan_digest: str
    checkpoint_manifest_digest: str
    source_report_digest: str
    training_plan_digest: str
    strategy_plan_digest: str
    benchmark_report_digest: str
    topology_digest: str
    world_size: int
    device_ordinals: tuple[int, int]
    checkpoint_id: str
    checkpoint_step: int
    checkpoint_metadata_path: str
    checkpoint_metadata_digest: str
    checkpoint_artifact_path: str
    checkpoint_artifact_digest: str
    launcher_policy: str = DISTRIBUTED_LAUNCH_POLICY
    resume_authorized: bool = True
    schema: str = DISTRIBUTED_RECOVERY_PLAN_SCHEMA
    schema_version: int = DISTRIBUTED_RECOVERY_PLAN_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for label in (
            "execution_plan_digest",
            "checkpoint_manifest_digest",
            "source_report_digest",
            "training_plan_digest",
            "strategy_plan_digest",
            "benchmark_report_digest",
            "topology_digest",
            "checkpoint_metadata_digest",
            "checkpoint_artifact_digest",
        ):
            _require_digest(label, getattr(self, label))
        if self.world_size != 2:
            raise TuningRuntimeError("distributed recovery world_size must be 2")
        ordinals = tuple(self.device_ordinals)
        object.__setattr__(self, "device_ordinals", ordinals)
        if len(ordinals) != 2 or ordinals != tuple(sorted(set(ordinals))):
            raise TuningRuntimeError("distributed recovery requires two unique sorted device ordinals")
        object.__setattr__(self, "checkpoint_id", _safe_ref("checkpoint_id", self.checkpoint_id))
        object.__setattr__(
            self,
            "checkpoint_metadata_path",
            _safe_ref("checkpoint_metadata_path", self.checkpoint_metadata_path),
        )
        object.__setattr__(
            self,
            "checkpoint_artifact_path",
            _safe_ref("checkpoint_artifact_path", self.checkpoint_artifact_path),
        )
        if (
            isinstance(self.checkpoint_step, bool)
            or not isinstance(self.checkpoint_step, int)
            or self.checkpoint_step < 1
        ):
            raise TuningRuntimeError("distributed recovery checkpoint step must be positive")
        if self.launcher_policy != DISTRIBUTED_LAUNCH_POLICY:
            raise TuningRuntimeError("distributed recovery launcher policy mismatch")
        if self.resume_authorized is not True:
            raise TuningRuntimeError("V2.4.4 recovery plan must explicitly authorize resume")

    def descriptor(self) -> dict[str, object]:
        return {
            "benchmark_report_digest": self.benchmark_report_digest,
            "checkpoint_artifact_digest": self.checkpoint_artifact_digest,
            "checkpoint_artifact_path": self.checkpoint_artifact_path,
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_manifest_digest": self.checkpoint_manifest_digest,
            "checkpoint_metadata_digest": self.checkpoint_metadata_digest,
            "checkpoint_metadata_path": self.checkpoint_metadata_path,
            "checkpoint_step": self.checkpoint_step,
            "device_ordinals": list(self.device_ordinals),
            "execution_plan_digest": self.execution_plan_digest,
            "launcher_policy": self.launcher_policy,
            "resume_authorized": self.resume_authorized,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "source_report_digest": self.source_report_digest,
            "strategy_plan_digest": self.strategy_plan_digest,
            "topology_digest": self.topology_digest,
            "training_plan_digest": self.training_plan_digest,
            "world_size": self.world_size,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.descriptor())

    @property
    def run_id(self) -> str:
        return f"dist-recovery-{self.digest[:20]}"

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "recovery_plan_digest": self.digest}


def build_distributed_recovery_plan(
    training_plan: TrainingPlan,
    strategy_plan: ExecutionStrategyPlan,
    benchmark_report: StrategyBenchmarkReport,
    manifest: DistributedCheckpointManifest,
) -> DistributedRecoveryPlan:
    execution = build_distributed_execution_plan(training_plan, strategy_plan, benchmark_report)
    expected = {
        "execution_plan_digest": execution.digest,
        "training_plan_digest": training_plan.digest,
        "strategy_plan_digest": strategy_plan.digest,
        "benchmark_report_digest": benchmark_report.digest,
        "topology_digest": execution.topology_digest,
    }
    for label, value in expected.items():
        if getattr(manifest, label) != value:
            raise TuningRuntimeError(f"recovery checkpoint {label} mismatch")
    if manifest.world_size != 2 or manifest.device_ordinals != execution.device_ordinals:
        raise TuningRuntimeError("recovery checkpoint topology/world-size identity mismatch")
    if manifest.step >= training_plan.sft.max_steps:
        raise TuningRuntimeError("recovery checkpoint is already at or beyond max_steps")
    return DistributedRecoveryPlan(
        execution_plan_digest=execution.digest,
        checkpoint_manifest_digest=manifest.digest,
        source_report_digest=manifest.source_report_digest,
        training_plan_digest=training_plan.digest,
        strategy_plan_digest=strategy_plan.digest,
        benchmark_report_digest=benchmark_report.digest,
        topology_digest=execution.topology_digest,
        world_size=2,
        device_ordinals=execution.device_ordinals,
        checkpoint_id=manifest.checkpoint_id,
        checkpoint_step=manifest.step,
        checkpoint_metadata_path=manifest.checkpoint_metadata_path,
        checkpoint_metadata_digest=manifest.checkpoint_metadata_digest,
        checkpoint_artifact_path=manifest.checkpoint_artifact_path,
        checkpoint_artifact_digest=manifest.checkpoint_artifact_digest,
    )


@dataclass(frozen=True, slots=True)
class DistributedRecoveryRankEvidence:
    rank_evidence: DistributedRankEvidence
    recovery_plan_digest: str
    checkpoint_manifest_digest: str
    resumed_from_checkpoint_id: str
    resumed_from_step: int

    def __post_init__(self) -> None:
        _require_digest("recovery_plan_digest", self.recovery_plan_digest)
        _require_digest("checkpoint_manifest_digest", self.checkpoint_manifest_digest)
        object.__setattr__(
            self,
            "resumed_from_checkpoint_id",
            _safe_ref("resumed_from_checkpoint_id", self.resumed_from_checkpoint_id),
        )
        if (
            isinstance(self.resumed_from_step, bool)
            or not isinstance(self.resumed_from_step, int)
            or self.resumed_from_step < 1
        ):
            raise TuningRuntimeError("resumed_from_step must be positive")

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> DistributedRecoveryRankEvidence:
        return cls(
            rank_evidence=DistributedRankEvidence.from_dict(value),
            recovery_plan_digest=str(value["recovery_plan_digest"]),
            checkpoint_manifest_digest=str(value["checkpoint_manifest_digest"]),
            resumed_from_checkpoint_id=str(value["resumed_from_checkpoint_id"]),
            resumed_from_step=int(value["resumed_from_step"]),
        )

    @property
    def rank(self) -> int:
        return self.rank_evidence.rank

    def to_dict(self) -> dict[str, object]:
        return {
            **self.rank_evidence.to_dict(),
            "checkpoint_manifest_digest": self.checkpoint_manifest_digest,
            "recovery_plan_digest": self.recovery_plan_digest,
            "resumed_from_checkpoint_id": self.resumed_from_checkpoint_id,
            "resumed_from_step": self.resumed_from_step,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


@dataclass(frozen=True, slots=True)
class DistributedRecoveryReport:
    recovery_plan_digest: str
    checkpoint_manifest_digest: str
    source_report_digest: str
    execution_plan_digest: str
    training_plan_digest: str
    strategy_plan_digest: str
    benchmark_report_digest: str
    topology_digest: str
    run_id: str
    state: DistributedExecutionState
    world_size: int
    device_ordinals: tuple[int, int]
    canonical_rank: int
    rank_evidence: tuple[DistributedRecoveryRankEvidence, ...]
    canonical_training_report_digest: str | None
    adapter_path: str | None
    adapter_digest: str | None
    completed_steps: int
    train_loss: float | None
    eval_loss: float | None
    resumed_from_checkpoint_id: str
    resumed_from_step: int
    blockers: tuple[str, ...] = ()
    stderr: str = ""
    process_group_managed: bool = True
    resume_authorized: bool = True
    schema: str = DISTRIBUTED_RECOVERY_REPORT_SCHEMA
    schema_version: int = DISTRIBUTED_RECOVERY_REPORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for label in (
            "recovery_plan_digest",
            "checkpoint_manifest_digest",
            "source_report_digest",
            "execution_plan_digest",
            "training_plan_digest",
            "strategy_plan_digest",
            "benchmark_report_digest",
            "topology_digest",
        ):
            _require_digest(label, getattr(self, label))
        object.__setattr__(self, "run_id", _safe_ref("run_id", self.run_id))
        object.__setattr__(self, "state", DistributedExecutionState(self.state))
        if self.world_size != 2:
            raise TuningRuntimeError("distributed recovery report world_size must be 2")
        if tuple(self.device_ordinals) != tuple(sorted(set(self.device_ordinals))):
            raise TuningRuntimeError("distributed recovery report device ordinals must be unique and sorted")
        if self.canonical_rank != 0:
            raise TuningRuntimeError("distributed recovery canonical rank must be zero")
        ranks = tuple(self.rank_evidence)
        object.__setattr__(self, "rank_evidence", ranks)
        if self.canonical_training_report_digest is not None:
            _require_digest("canonical_training_report_digest", self.canonical_training_report_digest)
        if self.adapter_digest is not None:
            _require_digest("adapter_digest", self.adapter_digest)
        if self.adapter_path is not None:
            object.__setattr__(self, "adapter_path", _safe_ref("adapter_path", self.adapter_path))
        if isinstance(self.completed_steps, bool) or self.completed_steps < 0:
            raise TuningRuntimeError("completed_steps must be non-negative")
        object.__setattr__(self, "train_loss", _bounded_loss("train_loss", self.train_loss))
        object.__setattr__(self, "eval_loss", _bounded_loss("eval_loss", self.eval_loss))
        object.__setattr__(
            self,
            "resumed_from_checkpoint_id",
            _safe_ref("resumed_from_checkpoint_id", self.resumed_from_checkpoint_id),
        )
        if self.resumed_from_step < 1:
            raise TuningRuntimeError("resumed_from_step must be positive")
        blockers = tuple(sorted(set(self.blockers)))
        object.__setattr__(self, "blockers", blockers)
        if self.process_group_managed is not True or self.resume_authorized is not True:
            raise TuningRuntimeError("V2.4.4 recovery requires managed process group and explicit resume")
        if self.state is DistributedExecutionState.COMPLETED:
            if tuple(item.rank for item in ranks) != (0, 1):
                raise TuningRuntimeError("completed recovery requires both rank evidences")
            if any(item.rank_evidence.state is not DistributedRankState.COMPLETED for item in ranks):
                raise TuningRuntimeError("completed recovery requires every rank completed")
            if self.canonical_training_report_digest is None or self.adapter_digest is None:
                raise TuningRuntimeError("completed recovery requires canonical training evidence")
            if blockers:
                raise TuningRuntimeError("completed recovery cannot contain blockers")

    def descriptor(self) -> dict[str, object]:
        return {
            "adapter_digest": self.adapter_digest,
            "adapter_path": self.adapter_path,
            "benchmark_report_digest": self.benchmark_report_digest,
            "blockers": list(self.blockers),
            "canonical_rank": self.canonical_rank,
            "canonical_training_report_digest": self.canonical_training_report_digest,
            "checkpoint_manifest_digest": self.checkpoint_manifest_digest,
            "completed_steps": self.completed_steps,
            "device_ordinals": list(self.device_ordinals),
            "eval_loss": self.eval_loss,
            "execution_plan_digest": self.execution_plan_digest,
            "process_group_managed": self.process_group_managed,
            "rank_evidence": [item.to_dict() for item in self.rank_evidence],
            "recovery_plan_digest": self.recovery_plan_digest,
            "resume_authorized": self.resume_authorized,
            "resumed_from_checkpoint_id": self.resumed_from_checkpoint_id,
            "resumed_from_step": self.resumed_from_step,
            "run_id": self.run_id,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "source_report_digest": self.source_report_digest,
            "state": self.state.value,
            "stderr": self.stderr,
            "strategy_plan_digest": self.strategy_plan_digest,
            "topology_digest": self.topology_digest,
            "train_loss": self.train_loss,
            "training_plan_digest": self.training_plan_digest,
            "world_size": self.world_size,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.descriptor())

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "report_digest": self.digest}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


class RecoverySandbox(Protocol):
    def run_process_group(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: Mapping[str, str] | None = None,
    ) -> SandboxResult: ...


class _RecoveryCanonicalWorkerValidator(TrainingRunner):
    def validate(
        self,
        plan: TrainingPlan,
        output: object,
        resumed_from: str,
        stderr: str,
    ) -> TrainingReport:
        return self._validate_worker_report(plan, output, resumed_from, stderr)


class DistributedRecoveryRunner:
    """V2.4.4 recovery over the accepted V2.4.3 two-rank launcher boundary."""

    def __init__(
        self,
        root: Path,
        *,
        kill_switch: KillSwitch | None = None,
        sandbox: RecoverySandbox | None = None,
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

    def resume(
        self,
        training_plan: TrainingPlan,
        strategy_plan: ExecutionStrategyPlan,
        benchmark_report: StrategyBenchmarkReport,
        manifest: DistributedCheckpointManifest,
    ) -> DistributedRecoveryReport:
        recovery = build_distributed_recovery_plan(
            training_plan,
            strategy_plan,
            benchmark_report,
            manifest,
        )
        execution = build_distributed_execution_plan(
            training_plan,
            strategy_plan,
            benchmark_report,
        )
        self._validate_manifest_files(manifest, training_plan)
        blockers = self._budget_blockers(execution)
        if blockers:
            return self._terminal(recovery, DistributedExecutionState.BUDGET_BLOCKED, blockers=blockers)

        run_dir = self.root / "distributed-recovery-runs" / recovery.run_id
        if run_dir.exists() and any(run_dir.iterdir()):
            raise TuningRuntimeError("distributed recovery run directory must be empty before launch")
        trainer_run_dir = run_dir / "r15-9"
        evidence_dir = run_dir / "rank-evidence"
        run_dir.mkdir(parents=True, exist_ok=True)
        evidence_dir.mkdir(parents=True, exist_ok=True)
        canonical_output = run_dir / "canonical-worker-output.json"
        checkpoint_path = _inside(self.root, manifest.checkpoint_metadata_path)

        worker_payload = training_plan.worker_payload(self.root, trainer_run_dir, checkpoint_path)
        worker_payload["sft"] = {
            **dict(worker_payload["sft"]),
            "train_batch_size": execution.per_device_batch_size,
            "gradient_accumulation_steps": execution.gradient_accumulation_steps,
        }
        worker_payload["seeds"] = {
            **dict(worker_payload["seeds"]),
            "data_seed": execution.shared_sampler_seed,
        }
        config = {
            "canonical_output_path": canonical_output.relative_to(self.root).as_posix(),
            "checkpoint_manifest": manifest.to_dict(),
            "evidence_dir": evidence_dir.relative_to(self.root).as_posix(),
            "execution_plan": execution.to_dict(),
            "recovery_plan": recovery.to_dict(),
            "schema": DISTRIBUTED_RECOVERY_WORKER_CONFIG_SCHEMA,
            "schema_version": DISTRIBUTED_RECOVERY_WORKER_CONFIG_SCHEMA_VERSION,
            "training_worker": worker_payload,
        }
        config_path = run_dir / "launch-config.json"
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        with contextlib.suppress(OSError):
            config_path.chmod(0o600)

        argv = [
            sys.executable,
            "-m",
            "torch.distributed.run",
            "--standalone",
            "--nnodes=1",
            "--nproc-per-node=2",
            "--max-restarts=0",
            "--module",
            "kodepoia.tuning.distributed_worker",
            config_path.relative_to(self.root).as_posix(),
        ]
        env = {"CUDA_VISIBLE_DEVICES": ",".join(str(item) for item in execution.device_ordinals)}
        try:
            result = self.sandbox.run_process_group(
                argv,
                cwd=self.root,
                timeout=float(training_plan.timeout_seconds),
                env=env,
            )
        except RuntimeError as exc:
            state = (
                DistributedExecutionState.CANCELLED
                if self.kill_switch.triggered
                else DistributedExecutionState.FAILED
            )
            return self._terminal(
                recovery,
                state,
                stderr=redact_runtime_text(str(exc))[:_MAX_CAPTURE_CHARS],
            )
        finally:
            config_path.unlink(missing_ok=True)

        stderr = redact_runtime_text(result.stderr)[:_MAX_CAPTURE_CHARS]
        if result.timed_out:
            return self._terminal(recovery, DistributedExecutionState.TIMED_OUT, stderr=stderr)
        if result.cancelled:
            return self._terminal(recovery, DistributedExecutionState.CANCELLED, stderr=stderr)
        if result.returncode != 0:
            return self._terminal(
                recovery,
                DistributedExecutionState.FAILED,
                blockers=("rank_group_failed",),
                stderr=stderr,
                rank_evidence=self._read_available_rank_evidence(recovery, evidence_dir),
            )

        try:
            ranks = self._validate_rank_evidence(recovery, execution, evidence_dir)
            output = json.loads(canonical_output.read_text(encoding="utf-8"))
            if ranks[0].rank_evidence.canonical_output_digest != canonical_sha256(output):
                raise TuningRuntimeError("recovery canonical worker output digest mismatch")
            canonical = _RecoveryCanonicalWorkerValidator(
                self.root,
                kill_switch=self.kill_switch,
                resource_probe=self.resource_probe,
            ).validate(training_plan, output, recovery.checkpoint_id, stderr)
            if canonical.resumed_from != recovery.checkpoint_id:
                raise TuningRuntimeError("canonical recovery report lost checkpoint lineage")
            return DistributedRecoveryReport(
                recovery_plan_digest=recovery.digest,
                checkpoint_manifest_digest=recovery.checkpoint_manifest_digest,
                source_report_digest=recovery.source_report_digest,
                execution_plan_digest=recovery.execution_plan_digest,
                training_plan_digest=training_plan.digest,
                strategy_plan_digest=strategy_plan.digest,
                benchmark_report_digest=benchmark_report.digest,
                topology_digest=recovery.topology_digest,
                run_id=recovery.run_id,
                state=DistributedExecutionState.COMPLETED,
                world_size=2,
                device_ordinals=recovery.device_ordinals,
                canonical_rank=0,
                rank_evidence=ranks,
                canonical_training_report_digest=canonical.digest,
                adapter_path=canonical.adapter_path,
                adapter_digest=canonical.adapter_digest,
                completed_steps=canonical.completed_steps,
                train_loss=canonical.train_loss,
                eval_loss=canonical.eval_loss,
                resumed_from_checkpoint_id=recovery.checkpoint_id,
                resumed_from_step=recovery.checkpoint_step,
            )
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            return self._terminal(
                recovery,
                DistributedExecutionState.FAILED,
                blockers=("distributed_recovery_evidence_invalid",),
                stderr=redact_runtime_text(f"{stderr}\n{exc}")[:_MAX_CAPTURE_CHARS],
                rank_evidence=self._read_available_rank_evidence(recovery, evidence_dir),
            )

    def _validate_manifest_files(
        self,
        manifest: DistributedCheckpointManifest,
        training_plan: TrainingPlan,
    ) -> None:
        metadata = _inside(self.root, manifest.checkpoint_metadata_path)
        artifact = _inside(self.root, manifest.checkpoint_artifact_path)
        if not metadata.is_file() or _sha256(metadata) != manifest.checkpoint_metadata_digest:
            raise TuningRuntimeError("recovery checkpoint metadata digest mismatch")
        if not artifact.is_file() or _sha256(artifact) != manifest.checkpoint_artifact_digest:
            raise TuningRuntimeError("recovery checkpoint artifact digest mismatch")
        record = CheckpointRecord.from_dict(json.loads(metadata.read_text(encoding="utf-8")))
        if record.checkpoint_id != manifest.checkpoint_id or record.step != manifest.step:
            raise TuningRuntimeError("recovery checkpoint metadata identity mismatch")
        if record.plan_digest != training_plan.digest:
            raise TuningRuntimeError("recovery checkpoint TrainingPlan lineage mismatch")
        if (
            record.artifact_path != manifest.checkpoint_artifact_path
            or record.artifact_digest != manifest.checkpoint_artifact_digest
        ):
            raise TuningRuntimeError("recovery checkpoint artifact lineage mismatch")

    def _budget_blockers(self, execution: DistributedExecutionPlan) -> tuple[str, ...]:
        host = self.resource_probe.sample(self.root)
        blockers: list[str] = []
        if execution.host_storage_required_bytes > 0:
            if host.disk_free_bytes is None:
                blockers.append("storage_budget_unknown")
            elif host.disk_free_bytes < execution.host_storage_required_bytes:
                blockers.append("storage_budget_exceeded")
        if execution.host_ram_required_bytes > 0:
            if host.ram_free_bytes is None:
                blockers.append("ram_budget_unknown")
            elif host.ram_free_bytes < execution.host_ram_required_bytes:
                blockers.append("ram_budget_exceeded")
        return tuple(sorted(blockers))

    def _read_available_rank_evidence(
        self,
        recovery: DistributedRecoveryPlan,
        evidence_dir: Path,
    ) -> tuple[DistributedRecoveryRankEvidence, ...]:
        records: list[DistributedRecoveryRankEvidence] = []
        for rank in range(2):
            path = evidence_dir / f"rank-{rank:05d}.json"
            if not path.is_file():
                continue
            try:
                record = DistributedRecoveryRankEvidence.from_dict(
                    json.loads(path.read_text(encoding="utf-8"))
                )
            except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
            if record.recovery_plan_digest == recovery.digest:
                records.append(record)
        return tuple(sorted(records, key=lambda item: item.rank))

    def _validate_rank_evidence(
        self,
        recovery: DistributedRecoveryPlan,
        execution: DistributedExecutionPlan,
        evidence_dir: Path,
    ) -> tuple[DistributedRecoveryRankEvidence, DistributedRecoveryRankEvidence]:
        records = self._read_available_rank_evidence(recovery, evidence_dir)
        if tuple(item.rank for item in records) != (0, 1):
            raise TuningRuntimeError("distributed recovery did not produce exactly two rank evidences")
        limits = dict(execution.device_vram_limits)
        for rank, record in enumerate(records):
            base = record.rank_evidence
            expected_seed = execution.rank_seeds[rank]
            if base.state is not DistributedRankState.COMPLETED:
                raise TuningRuntimeError("distributed recovery rank did not complete")
            if base.execution_plan_digest != execution.digest:
                raise TuningRuntimeError("recovery rank execution lineage mismatch")
            if base.training_plan_digest != execution.training_plan_digest:
                raise TuningRuntimeError("recovery rank TrainingPlan lineage mismatch")
            if base.strategy_plan_digest != execution.strategy_plan_digest:
                raise TuningRuntimeError("recovery rank strategy lineage mismatch")
            if base.topology_digest != execution.topology_digest:
                raise TuningRuntimeError("recovery rank topology lineage mismatch")
            if base.world_size != 2 or base.local_rank != rank:
                raise TuningRuntimeError("recovery rank/local-rank evidence mismatch")
            if base.device_ordinal != execution.device_ordinals[rank]:
                raise TuningRuntimeError("recovery rank device ordinal evidence mismatch")
            if (
                base.seed != expected_seed.seed
                or base.data_seed != expected_seed.data_seed
                or base.shared_sampler_seed != execution.shared_sampler_seed
            ):
                raise TuningRuntimeError("recovery rank seed evidence mismatch")
            if base.peak_vram_bytes is not None and base.peak_vram_bytes > limits[base.device_ordinal]:
                raise TuningRuntimeError("recovery rank peak VRAM exceeds selected device total")
            if record.checkpoint_manifest_digest != recovery.checkpoint_manifest_digest:
                raise TuningRuntimeError("recovery rank checkpoint manifest mismatch")
            if (
                record.resumed_from_checkpoint_id != recovery.checkpoint_id
                or record.resumed_from_step != recovery.checkpoint_step
            ):
                raise TuningRuntimeError("recovery rank checkpoint lineage mismatch")
        return (records[0], records[1])

    def _terminal(
        self,
        recovery: DistributedRecoveryPlan,
        state: DistributedExecutionState,
        *,
        blockers: tuple[str, ...] = (),
        stderr: str = "",
        rank_evidence: tuple[DistributedRecoveryRankEvidence, ...] = (),
    ) -> DistributedRecoveryReport:
        return DistributedRecoveryReport(
            recovery_plan_digest=recovery.digest,
            checkpoint_manifest_digest=recovery.checkpoint_manifest_digest,
            source_report_digest=recovery.source_report_digest,
            execution_plan_digest=recovery.execution_plan_digest,
            training_plan_digest=recovery.training_plan_digest,
            strategy_plan_digest=recovery.strategy_plan_digest,
            benchmark_report_digest=recovery.benchmark_report_digest,
            topology_digest=recovery.topology_digest,
            run_id=recovery.run_id,
            state=state,
            world_size=2,
            device_ordinals=recovery.device_ordinals,
            canonical_rank=0,
            rank_evidence=rank_evidence,
            canonical_training_report_digest=None,
            adapter_path=None,
            adapter_digest=None,
            completed_steps=0,
            train_loss=None,
            eval_loss=None,
            resumed_from_checkpoint_id=recovery.checkpoint_id,
            resumed_from_step=recovery.checkpoint_step,
            blockers=blockers or (state.value,),
            stderr=stderr,
        )
