from __future__ import annotations

import contextlib
import json
import math
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.core.sandbox import ProcessSandbox, SandboxResult

from .contracts import TuningRuntimeError, canonical_sha256
from .runtime import HostResourceProbe, redact_runtime_text
from .strategy import (
    ExecutionStrategyPlan,
    StrategyBenchmarkDisposition,
    StrategyBenchmarkReport,
    StrategyKind,
)
from .training import (
    TrainingAuthorization,
    TrainingMode,
    TrainingPlan,
    TrainingReport,
    TrainingRunner,
)

DISTRIBUTED_EXECUTION_SCHEMA = "kodepoia.v2.4.3.distributed-execution-plan"
DISTRIBUTED_EXECUTION_SCHEMA_VERSION = 1
DISTRIBUTED_REPORT_SCHEMA = "kodepoia.v2.4.3.distributed-training-report"
DISTRIBUTED_REPORT_SCHEMA_VERSION = 1
DISTRIBUTED_WORKER_CONFIG_SCHEMA = "kodepoia.v2.4.3.distributed-worker-config"
DISTRIBUTED_WORKER_CONFIG_SCHEMA_VERSION = 1
DISTRIBUTED_LAUNCH_POLICY = "torchrun-standalone-two-rank-v1"

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+@-]{0,511}$")
_MAX_CAPTURE_CHARS = 8192
_MAX_BYTES = 1 << 60


class DistributedExecutionState(StrEnum):
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    FAILED = "failed"
    BUDGET_BLOCKED = "budget_blocked"


class DistributedRankState(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


def _require_digest(label: str, value: str) -> str:
    if _HEX64.fullmatch(value) is None:
        raise TuningRuntimeError(f"{label} must be 64 lowercase hex characters")
    return value


def _safe_ref(label: str, value: str) -> str:
    value = value.strip()
    if _SAFE_REF.fullmatch(value) is None or ".." in value.split("/"):
        raise TuningRuntimeError(f"{label} must be a bounded safe identifier")
    return value


def _bounded_int(label: str, value: int, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise TuningRuntimeError(f"{label} must be an integer in [{minimum}, {maximum}]")
    return value


def _bounded_float_or_none(label: str, value: float | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TuningRuntimeError(f"{label} must be numeric or null")
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise TuningRuntimeError(f"{label} must be finite and non-negative")
    return value


@dataclass(frozen=True, slots=True)
class DistributedRankSeed:
    rank: int
    seed: int
    data_seed: int

    def __post_init__(self) -> None:
        _bounded_int("rank", self.rank, minimum=0, maximum=1)
        _bounded_int("seed", self.seed, minimum=0, maximum=2**31 - 1)
        _bounded_int("data_seed", self.data_seed, minimum=0, maximum=2**31 - 1)

    def to_dict(self) -> dict[str, int]:
        return {"data_seed": self.data_seed, "rank": self.rank, "seed": self.seed}


@dataclass(frozen=True, slots=True)
class DistributedExecutionPlan:
    training_plan_digest: str
    strategy_plan_digest: str
    benchmark_report_digest: str
    topology_report_digest: str
    topology_digest: str
    world_size: int
    device_ordinals: tuple[int, int]
    device_vram_limits: tuple[tuple[int, int], tuple[int, int]]
    host_ram_required_bytes: int
    host_storage_required_bytes: int
    per_device_batch_size: int
    gradient_accumulation_steps: int
    effective_global_batch_size: int
    rank_seeds: tuple[DistributedRankSeed, DistributedRankSeed]
    shared_sampler_seed: int
    canonical_rank: int = 0
    launcher_policy: str = DISTRIBUTED_LAUNCH_POLICY
    resume_authorized: bool = False
    schema: str = DISTRIBUTED_EXECUTION_SCHEMA
    schema_version: int = DISTRIBUTED_EXECUTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for label in (
            "training_plan_digest",
            "strategy_plan_digest",
            "benchmark_report_digest",
            "topology_report_digest",
            "topology_digest",
        ):
            _require_digest(label, getattr(self, label))
        if self.world_size != 2:
            raise TuningRuntimeError("V2.4.3 distributed execution requires world_size=2")
        ordinals = tuple(self.device_ordinals)
        object.__setattr__(self, "device_ordinals", ordinals)
        if len(ordinals) != 2 or ordinals != tuple(sorted(set(ordinals))):
            raise TuningRuntimeError("V2.4.3 device_ordinals must contain two unique sorted ordinals")
        limits = tuple(self.device_vram_limits)
        object.__setattr__(self, "device_vram_limits", limits)
        if tuple(item[0] for item in limits) != ordinals:
            raise TuningRuntimeError("device_vram_limits must exactly match selected ordinals")
        for ordinal, value in limits:
            _bounded_int("device ordinal", ordinal, minimum=0, maximum=63)
            _bounded_int("device VRAM limit", value, minimum=1, maximum=_MAX_BYTES)
        for label in ("host_ram_required_bytes", "host_storage_required_bytes"):
            _bounded_int(label, getattr(self, label), minimum=0, maximum=_MAX_BYTES)
        _bounded_int("per_device_batch_size", self.per_device_batch_size, minimum=1, maximum=65536)
        _bounded_int(
            "gradient_accumulation_steps",
            self.gradient_accumulation_steps,
            minimum=1,
            maximum=65536,
        )
        expected_batch = (
            self.per_device_batch_size
            * self.gradient_accumulation_steps
            * self.world_size
        )
        if self.effective_global_batch_size != expected_batch:
            raise TuningRuntimeError("distributed effective global batch identity is invalid")
        seeds = tuple(self.rank_seeds)
        object.__setattr__(self, "rank_seeds", seeds)
        if tuple(item.rank for item in seeds) != (0, 1):
            raise TuningRuntimeError("distributed rank seeds must cover ranks 0 and 1 exactly")
        _bounded_int("shared_sampler_seed", self.shared_sampler_seed, minimum=0, maximum=2**31 - 1)
        if self.canonical_rank != 0:
            raise TuningRuntimeError("V2.4.3 canonical rank must be zero")
        if self.launcher_policy != DISTRIBUTED_LAUNCH_POLICY:
            raise TuningRuntimeError("unsupported distributed launcher policy")
        if self.resume_authorized is not False:
            raise TuningRuntimeError("distributed resume remains unauthorized until V2.4.4")

    def descriptor(self) -> dict[str, object]:
        return {
            "benchmark_report_digest": self.benchmark_report_digest,
            "canonical_rank": self.canonical_rank,
            "device_ordinals": list(self.device_ordinals),
            "device_vram_limits": [
                {"ordinal": ordinal, "total_vram_bytes": value}
                for ordinal, value in self.device_vram_limits
            ],
            "effective_global_batch_size": self.effective_global_batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "host_ram_required_bytes": self.host_ram_required_bytes,
            "host_storage_required_bytes": self.host_storage_required_bytes,
            "launcher_policy": self.launcher_policy,
            "per_device_batch_size": self.per_device_batch_size,
            "rank_seeds": [item.to_dict() for item in self.rank_seeds],
            "resume_authorized": self.resume_authorized,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "shared_sampler_seed": self.shared_sampler_seed,
            "strategy_plan_digest": self.strategy_plan_digest,
            "topology_digest": self.topology_digest,
            "topology_report_digest": self.topology_report_digest,
            "training_plan_digest": self.training_plan_digest,
            "world_size": self.world_size,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.descriptor())

    @property
    def run_id(self) -> str:
        return f"dist-{self.digest[:20]}"

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "execution_plan_digest": self.digest}


def build_distributed_execution_plan(
    training_plan: TrainingPlan,
    strategy_plan: ExecutionStrategyPlan,
    benchmark_report: StrategyBenchmarkReport,
) -> DistributedExecutionPlan:
    if training_plan.authorization is not TrainingAuthorization.TRAIN:
        raise TuningRuntimeError("V2.4.3 distributed execution requires governed TRAIN authorization")
    if training_plan.mode not in {TrainingMode.SFT, TrainingMode.QLORA}:
        raise TuningRuntimeError("V2.4.3 distributed execution accepts only real SFT or QLoRA")
    if training_plan.dataset.train_path is None or training_plan.dataset.validation_path is None:
        raise TuningRuntimeError("V2.4.3 requires explicit governed dataset paths")
    if strategy_plan.strategy is not StrategyKind.REPLICATED_DATA_PARALLEL:
        raise TuningRuntimeError("V2.4.3 requires replicated_data_parallel strategy")
    if strategy_plan.world_size != 2 or len(strategy_plan.device_ordinals) != 2:
        raise TuningRuntimeError("V2.4.3 requires exactly two selected devices")
    if strategy_plan.training_plan_digest != training_plan.digest:
        raise TuningRuntimeError("strategy TrainingPlan lineage mismatch")
    if benchmark_report.disposition is not StrategyBenchmarkDisposition.QUALIFIED:
        raise TuningRuntimeError("replicated strategy requires qualified V2.4.2 benchmark evidence")
    if benchmark_report.blockers:
        raise TuningRuntimeError("qualified benchmark evidence must not contain blockers")
    if benchmark_report.training_plan_digest != training_plan.digest:
        raise TuningRuntimeError("benchmark TrainingPlan lineage mismatch")
    if benchmark_report.topology_digest != strategy_plan.topology_digest:
        raise TuningRuntimeError("benchmark topology lineage mismatch")
    if benchmark_report.effective_global_batch_size != strategy_plan.effective_global_batch_size:
        raise TuningRuntimeError("benchmark effective global batch mismatch")
    if benchmark_report.candidate.strategy_plan_digest != strategy_plan.digest:
        raise TuningRuntimeError("benchmark candidate strategy lineage mismatch")
    if not benchmark_report.candidate.run_integrity or not benchmark_report.candidate.checkpoint_integrity:
        raise TuningRuntimeError("benchmark candidate integrity is not accepted")

    expected_seeds = tuple(
        DistributedRankSeed(
            rank=rank,
            seed=training_plan.seeds.seed + rank,
            data_seed=training_plan.seeds.data_seed + rank,
        )
        for rank in range(2)
    )
    observed_seeds = tuple(
        DistributedRankSeed(rank=item.rank, seed=item.seed, data_seed=item.data_seed)
        for item in strategy_plan.rank_seeds
    )
    if observed_seeds != expected_seeds:
        raise TuningRuntimeError("strategy rank/data seed lineage mismatch")

    return DistributedExecutionPlan(
        training_plan_digest=training_plan.digest,
        strategy_plan_digest=strategy_plan.digest,
        benchmark_report_digest=benchmark_report.digest,
        topology_report_digest=strategy_plan.topology_report_digest,
        topology_digest=strategy_plan.topology_digest,
        world_size=2,
        device_ordinals=(strategy_plan.device_ordinals[0], strategy_plan.device_ordinals[1]),
        device_vram_limits=(
            (
                strategy_plan.device_budgets[0].ordinal,
                strategy_plan.device_budgets[0].observed_total_vram_bytes,
            ),
            (
                strategy_plan.device_budgets[1].ordinal,
                strategy_plan.device_budgets[1].observed_total_vram_bytes,
            ),
        ),
        host_ram_required_bytes=strategy_plan.host_ram_required_bytes,
        host_storage_required_bytes=strategy_plan.host_storage_required_bytes,
        per_device_batch_size=strategy_plan.per_device_batch_size,
        gradient_accumulation_steps=strategy_plan.gradient_accumulation_steps,
        effective_global_batch_size=strategy_plan.effective_global_batch_size,
        rank_seeds=expected_seeds,  # type: ignore[arg-type]
        shared_sampler_seed=training_plan.seeds.data_seed,
    )


@dataclass(frozen=True, slots=True)
class DistributedRankEvidence:
    execution_plan_digest: str
    training_plan_digest: str
    strategy_plan_digest: str
    topology_digest: str
    rank: int
    local_rank: int
    world_size: int
    device_ordinal: int
    seed: int
    data_seed: int
    shared_sampler_seed: int
    state: DistributedRankState
    completed_steps: int
    train_loss: float | None
    eval_loss: float | None
    peak_vram_bytes: int | None
    canonical_output_digest: str | None = None
    failure_type: str | None = None

    def __post_init__(self) -> None:
        for label in (
            "execution_plan_digest",
            "training_plan_digest",
            "strategy_plan_digest",
            "topology_digest",
        ):
            _require_digest(label, getattr(self, label))
        _bounded_int("rank", self.rank, minimum=0, maximum=1)
        _bounded_int("local_rank", self.local_rank, minimum=0, maximum=1)
        if self.world_size != 2:
            raise TuningRuntimeError("rank evidence world_size must be 2")
        _bounded_int("device_ordinal", self.device_ordinal, minimum=0, maximum=63)
        _bounded_int("seed", self.seed, minimum=0, maximum=2**31 - 1)
        _bounded_int("data_seed", self.data_seed, minimum=0, maximum=2**31 - 1)
        _bounded_int("shared_sampler_seed", self.shared_sampler_seed, minimum=0, maximum=2**31 - 1)
        object.__setattr__(self, "state", DistributedRankState(self.state))
        _bounded_int("completed_steps", self.completed_steps, minimum=0, maximum=10_000_000)
        object.__setattr__(self, "train_loss", _bounded_float_or_none("train_loss", self.train_loss))
        object.__setattr__(self, "eval_loss", _bounded_float_or_none("eval_loss", self.eval_loss))
        if self.peak_vram_bytes is not None:
            _bounded_int("peak_vram_bytes", self.peak_vram_bytes, minimum=0, maximum=_MAX_BYTES)
        if self.canonical_output_digest is not None:
            _require_digest("canonical_output_digest", self.canonical_output_digest)
        if self.failure_type is not None:
            object.__setattr__(self, "failure_type", _safe_ref("failure_type", self.failure_type))
        if self.rank == 0 and self.state is DistributedRankState.COMPLETED:
            if self.canonical_output_digest is None:
                raise TuningRuntimeError("completed rank zero must bind canonical output digest")
        elif self.canonical_output_digest is not None:
            raise TuningRuntimeError("only completed rank zero may bind canonical output digest")

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> DistributedRankEvidence:
        return cls(
            execution_plan_digest=str(value["execution_plan_digest"]),
            training_plan_digest=str(value["training_plan_digest"]),
            strategy_plan_digest=str(value["strategy_plan_digest"]),
            topology_digest=str(value["topology_digest"]),
            rank=int(value["rank"]),
            local_rank=int(value["local_rank"]),
            world_size=int(value["world_size"]),
            device_ordinal=int(value["device_ordinal"]),
            seed=int(value["seed"]),
            data_seed=int(value["data_seed"]),
            shared_sampler_seed=int(value["shared_sampler_seed"]),
            state=DistributedRankState(str(value["state"])),
            completed_steps=int(value["completed_steps"]),
            train_loss=None if value.get("train_loss") is None else float(value["train_loss"]),
            eval_loss=None if value.get("eval_loss") is None else float(value["eval_loss"]),
            peak_vram_bytes=(
                None if value.get("peak_vram_bytes") is None else int(value["peak_vram_bytes"])
            ),
            canonical_output_digest=(
                None
                if value.get("canonical_output_digest") is None
                else str(value["canonical_output_digest"])
            ),
            failure_type=None if value.get("failure_type") is None else str(value["failure_type"]),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "canonical_output_digest": self.canonical_output_digest,
            "completed_steps": self.completed_steps,
            "data_seed": self.data_seed,
            "device_ordinal": self.device_ordinal,
            "eval_loss": self.eval_loss,
            "execution_plan_digest": self.execution_plan_digest,
            "failure_type": self.failure_type,
            "local_rank": self.local_rank,
            "peak_vram_bytes": self.peak_vram_bytes,
            "rank": self.rank,
            "seed": self.seed,
            "shared_sampler_seed": self.shared_sampler_seed,
            "state": self.state.value,
            "strategy_plan_digest": self.strategy_plan_digest,
            "topology_digest": self.topology_digest,
            "train_loss": self.train_loss,
            "training_plan_digest": self.training_plan_digest,
            "world_size": self.world_size,
        }


@dataclass(frozen=True, slots=True)
class DistributedTrainingReport:
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
    rank_evidence: tuple[DistributedRankEvidence, ...]
    canonical_training_report_digest: str | None
    adapter_path: str | None
    adapter_digest: str | None
    completed_steps: int
    train_loss: float | None
    eval_loss: float | None
    blockers: tuple[str, ...] = ()
    stderr: str = ""
    process_group_managed: bool = True
    resume_authorized: bool = False
    schema: str = DISTRIBUTED_REPORT_SCHEMA
    schema_version: int = DISTRIBUTED_REPORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for label in (
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
            raise TuningRuntimeError("distributed report world_size must be 2")
        if tuple(self.device_ordinals) != tuple(sorted(set(self.device_ordinals))):
            raise TuningRuntimeError("distributed report device ordinals must be unique and sorted")
        if self.canonical_rank != 0:
            raise TuningRuntimeError("distributed report canonical rank must be zero")
        ranks = tuple(self.rank_evidence)
        object.__setattr__(self, "rank_evidence", ranks)
        if self.canonical_training_report_digest is not None:
            _require_digest("canonical_training_report_digest", self.canonical_training_report_digest)
        if self.adapter_path is not None:
            object.__setattr__(self, "adapter_path", _safe_ref("adapter_path", self.adapter_path))
        if self.adapter_digest is not None:
            _require_digest("adapter_digest", self.adapter_digest)
        _bounded_int("completed_steps", self.completed_steps, minimum=0, maximum=10_000_000)
        object.__setattr__(self, "train_loss", _bounded_float_or_none("train_loss", self.train_loss))
        object.__setattr__(self, "eval_loss", _bounded_float_or_none("eval_loss", self.eval_loss))
        blockers = tuple(sorted(set(self.blockers)))
        object.__setattr__(self, "blockers", blockers)
        if not isinstance(self.process_group_managed, bool) or self.process_group_managed is not True:
            raise TuningRuntimeError("V2.4.3 reports require managed process-group execution")
        if self.resume_authorized is not False:
            raise TuningRuntimeError("distributed resume remains unauthorized until V2.4.4")
        if self.state is DistributedExecutionState.COMPLETED:
            if tuple(item.rank for item in ranks) != (0, 1):
                raise TuningRuntimeError("completed distributed report requires both rank evidences")
            if any(item.state is not DistributedRankState.COMPLETED for item in ranks):
                raise TuningRuntimeError("completed distributed report requires every rank completed")
            if self.canonical_training_report_digest is None or self.adapter_digest is None:
                raise TuningRuntimeError("completed distributed report requires canonical training evidence")
            if blockers:
                raise TuningRuntimeError("completed distributed report cannot contain blockers")

    def descriptor(self) -> dict[str, object]:
        return {
            "adapter_digest": self.adapter_digest,
            "adapter_path": self.adapter_path,
            "benchmark_report_digest": self.benchmark_report_digest,
            "blockers": list(self.blockers),
            "canonical_rank": self.canonical_rank,
            "canonical_training_report_digest": self.canonical_training_report_digest,
            "completed_steps": self.completed_steps,
            "device_ordinals": list(self.device_ordinals),
            "eval_loss": self.eval_loss,
            "execution_plan_digest": self.execution_plan_digest,
            "process_group_managed": self.process_group_managed,
            "rank_evidence": [item.to_dict() for item in self.rank_evidence],
            "resume_authorized": self.resume_authorized,
            "run_id": self.run_id,
            "schema": self.schema,
            "schema_version": self.schema_version,
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


class DistributedSandbox(Protocol):
    def run_process_group(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: Mapping[str, str] | None = None,
    ) -> SandboxResult: ...


class _CanonicalWorkerValidator(TrainingRunner):
    def validate(self, plan: TrainingPlan, output: object, stderr: str) -> TrainingReport:
        return self._validate_worker_report(plan, output, None, stderr)


class DistributedTrainingRunner:
    """V2.4.3 fixed two-rank launcher over the accepted R15.9 worker semantics."""

    def __init__(
        self,
        root: Path,
        *,
        kill_switch: KillSwitch | None = None,
        sandbox: DistributedSandbox | None = None,
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

    def run(
        self,
        training_plan: TrainingPlan,
        strategy_plan: ExecutionStrategyPlan,
        benchmark_report: StrategyBenchmarkReport,
    ) -> DistributedTrainingReport:
        execution = build_distributed_execution_plan(
            training_plan,
            strategy_plan,
            benchmark_report,
        )
        blockers = self._budget_blockers(execution)
        if blockers:
            return self._terminal(execution, DistributedExecutionState.BUDGET_BLOCKED, blockers=blockers)

        run_dir = self.root / "distributed-runs" / execution.run_id
        if run_dir.exists() and any(run_dir.iterdir()):
            raise TuningRuntimeError("distributed run directory must be empty before launch")
        trainer_run_dir = run_dir / "r15-9"
        evidence_dir = run_dir / "rank-evidence"
        run_dir.mkdir(parents=True, exist_ok=True)
        evidence_dir.mkdir(parents=True, exist_ok=True)
        canonical_output = run_dir / "canonical-worker-output.json"

        worker_payload = training_plan.worker_payload(self.root, trainer_run_dir, None)
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
            "evidence_dir": evidence_dir.relative_to(self.root).as_posix(),
            "execution_plan": execution.to_dict(),
            "schema": DISTRIBUTED_WORKER_CONFIG_SCHEMA,
            "schema_version": DISTRIBUTED_WORKER_CONFIG_SCHEMA_VERSION,
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
                execution,
                state,
                stderr=redact_runtime_text(str(exc))[:_MAX_CAPTURE_CHARS],
            )
        finally:
            config_path.unlink(missing_ok=True)

        stderr = redact_runtime_text(result.stderr)[:_MAX_CAPTURE_CHARS]
        if result.timed_out:
            return self._terminal(execution, DistributedExecutionState.TIMED_OUT, stderr=stderr)
        if result.cancelled:
            return self._terminal(execution, DistributedExecutionState.CANCELLED, stderr=stderr)
        if result.returncode != 0:
            return self._terminal(
                execution,
                DistributedExecutionState.FAILED,
                blockers=("rank_group_failed",),
                stderr=stderr,
                rank_evidence=self._read_available_rank_evidence(execution, evidence_dir),
            )

        try:
            ranks = self._validate_rank_evidence(execution, strategy_plan, evidence_dir)
            output = json.loads(canonical_output.read_text(encoding="utf-8"))
            expected_output_digest = ranks[0].canonical_output_digest
            if expected_output_digest != canonical_sha256(output):
                raise TuningRuntimeError("canonical worker output digest mismatch")
            canonical = _CanonicalWorkerValidator(
                self.root,
                kill_switch=self.kill_switch,
                resource_probe=self.resource_probe,
            ).validate(training_plan, output, stderr)
            return DistributedTrainingReport(
                execution_plan_digest=execution.digest,
                training_plan_digest=training_plan.digest,
                strategy_plan_digest=strategy_plan.digest,
                benchmark_report_digest=benchmark_report.digest,
                topology_digest=execution.topology_digest,
                run_id=execution.run_id,
                state=DistributedExecutionState.COMPLETED,
                world_size=2,
                device_ordinals=execution.device_ordinals,
                canonical_rank=0,
                rank_evidence=ranks,
                canonical_training_report_digest=canonical.digest,
                adapter_path=canonical.adapter_path,
                adapter_digest=canonical.adapter_digest,
                completed_steps=canonical.completed_steps,
                train_loss=canonical.train_loss,
                eval_loss=canonical.eval_loss,
            )
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            return self._terminal(
                execution,
                DistributedExecutionState.FAILED,
                blockers=("distributed_evidence_invalid",),
                stderr=redact_runtime_text(f"{stderr}\n{exc}")[:_MAX_CAPTURE_CHARS],
                rank_evidence=self._read_available_rank_evidence(execution, evidence_dir),
            )

    def _budget_blockers(self, plan: DistributedExecutionPlan) -> tuple[str, ...]:
        host = self.resource_probe.sample(self.root)
        blockers: list[str] = []
        if plan.host_storage_required_bytes > 0:
            if host.disk_free_bytes is None:
                blockers.append("storage_budget_unknown")
            elif host.disk_free_bytes < plan.host_storage_required_bytes:
                blockers.append("storage_budget_exceeded")
        if plan.host_ram_required_bytes > 0:
            if host.ram_free_bytes is None:
                blockers.append("ram_budget_unknown")
            elif host.ram_free_bytes < plan.host_ram_required_bytes:
                blockers.append("ram_budget_exceeded")
        return tuple(sorted(blockers))

    def _read_available_rank_evidence(
        self,
        execution: DistributedExecutionPlan,
        evidence_dir: Path,
    ) -> tuple[DistributedRankEvidence, ...]:
        records: list[DistributedRankEvidence] = []
        for rank in range(2):
            path = evidence_dir / f"rank-{rank:05d}.json"
            if not path.is_file():
                continue
            try:
                record = DistributedRankEvidence.from_dict(
                    json.loads(path.read_text(encoding="utf-8"))
                )
            except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
            if record.execution_plan_digest == execution.digest:
                records.append(record)
        return tuple(sorted(records, key=lambda item: item.rank))

    def _validate_rank_evidence(
        self,
        execution: DistributedExecutionPlan,
        strategy: ExecutionStrategyPlan,
        evidence_dir: Path,
    ) -> tuple[DistributedRankEvidence, DistributedRankEvidence]:
        records = self._read_available_rank_evidence(execution, evidence_dir)
        if tuple(item.rank for item in records) != (0, 1):
            raise TuningRuntimeError("distributed launch did not produce exactly two rank evidences")
        limits = dict(execution.device_vram_limits)
        for rank, record in enumerate(records):
            expected_seed = execution.rank_seeds[rank]
            if record.state is not DistributedRankState.COMPLETED:
                raise TuningRuntimeError("distributed rank did not complete")
            if record.training_plan_digest != execution.training_plan_digest:
                raise TuningRuntimeError("rank TrainingPlan lineage mismatch")
            if record.strategy_plan_digest != strategy.digest:
                raise TuningRuntimeError("rank strategy lineage mismatch")
            if record.topology_digest != execution.topology_digest:
                raise TuningRuntimeError("rank topology lineage mismatch")
            if record.world_size != 2 or record.local_rank != rank:
                raise TuningRuntimeError("rank/local-rank evidence mismatch")
            if record.device_ordinal != execution.device_ordinals[rank]:
                raise TuningRuntimeError("rank device ordinal evidence mismatch")
            if (
                record.seed != expected_seed.seed
                or record.data_seed != expected_seed.data_seed
                or record.shared_sampler_seed != execution.shared_sampler_seed
            ):
                raise TuningRuntimeError("rank seed evidence mismatch")
            if record.peak_vram_bytes is not None and record.peak_vram_bytes > limits[record.device_ordinal]:
                raise TuningRuntimeError("rank peak VRAM exceeds selected device total")
        return (records[0], records[1])

    def _terminal(
        self,
        execution: DistributedExecutionPlan,
        state: DistributedExecutionState,
        *,
        blockers: tuple[str, ...] = (),
        stderr: str = "",
        rank_evidence: tuple[DistributedRankEvidence, ...] = (),
    ) -> DistributedTrainingReport:
        return DistributedTrainingReport(
            execution_plan_digest=execution.digest,
            training_plan_digest=execution.training_plan_digest,
            strategy_plan_digest=execution.strategy_plan_digest,
            benchmark_report_digest=execution.benchmark_report_digest,
            topology_digest=execution.topology_digest,
            run_id=execution.run_id,
            state=state,
            world_size=2,
            device_ordinals=execution.device_ordinals,
            canonical_rank=0,
            rank_evidence=rank_evidence,
            canonical_training_report_digest=None,
            adapter_path=None,
            adapter_digest=None,
            completed_steps=0,
            train_loss=None,
            eval_loss=None,
            blockers=blockers or (state.value,),
            stderr=stderr,
        )
