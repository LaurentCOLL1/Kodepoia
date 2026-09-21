from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .contracts import SeedConfig, TuningRuntimeError, canonical_sha256
from .topology import AcceleratorTopologyReport, TopologyDisposition
from .training import TrainingPlan

STRATEGY_PLAN_SCHEMA = "kodepoia.v2.4.2.execution-strategy-plan"
STRATEGY_PLAN_SCHEMA_VERSION = 1
STRATEGY_BENCHMARK_SCHEMA = "kodepoia.v2.4.2.strategy-benchmark"
STRATEGY_BENCHMARK_SCHEMA_VERSION = 1
MIN_REPLICATED_THROUGHPUT_SPEEDUP_RATIO = 1.25
MAX_EVAL_LOSS_REGRESSION = 0.0

_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_MAX_BYTES = 1 << 60
_MAX_BATCH = 65_536
_MAX_WORLD_SIZE = 64
_MAX_SEED = 2**31 - 1


class StrategyKind(StrEnum):
    SINGLE_GPU = "single_gpu"
    REPLICATED_DATA_PARALLEL = "replicated_data_parallel"


class StrategyBenchmarkDisposition(StrEnum):
    QUALIFIED = "qualified"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


def _require_digest(label: str, value: str) -> str:
    if _DIGEST.fullmatch(value) is None:
        raise TuningRuntimeError(f"{label} must be 64 lowercase hex characters")
    return value


def _bounded_int(label: str, value: int, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise TuningRuntimeError(f"{label} must be an integer in [{minimum}, {maximum}]")
    return value


def _bounded_float(label: str, value: float, *, minimum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TuningRuntimeError(f"{label} must be numeric")
    value = float(value)
    if not math.isfinite(value) or value < minimum:
        raise TuningRuntimeError(f"{label} must be finite and >= {minimum}")
    return value


@dataclass(frozen=True, slots=True)
class DeviceStrategyBudget:
    ordinal: int
    required_free_vram_bytes: int
    observed_free_vram_bytes: int
    observed_total_vram_bytes: int

    def __post_init__(self) -> None:
        _bounded_int("ordinal", self.ordinal, minimum=0, maximum=_MAX_WORLD_SIZE - 1)
        for label, value in (
            ("required_free_vram_bytes", self.required_free_vram_bytes),
            ("observed_free_vram_bytes", self.observed_free_vram_bytes),
            ("observed_total_vram_bytes", self.observed_total_vram_bytes),
        ):
            _bounded_int(label, value, minimum=0, maximum=_MAX_BYTES)
        if self.observed_total_vram_bytes == 0:
            raise TuningRuntimeError("observed_total_vram_bytes must be positive")
        if self.observed_free_vram_bytes > self.observed_total_vram_bytes:
            raise TuningRuntimeError("observed free VRAM cannot exceed total VRAM")
        if self.required_free_vram_bytes > self.observed_total_vram_bytes:
            raise TuningRuntimeError("required VRAM exceeds selected device total VRAM")
        if self.required_free_vram_bytes > self.observed_free_vram_bytes:
            raise TuningRuntimeError("required VRAM exceeds selected device free VRAM")

    def to_dict(self) -> dict[str, int]:
        return {
            "observed_free_vram_bytes": self.observed_free_vram_bytes,
            "observed_total_vram_bytes": self.observed_total_vram_bytes,
            "ordinal": self.ordinal,
            "required_free_vram_bytes": self.required_free_vram_bytes,
        }


@dataclass(frozen=True, slots=True)
class RankSeed:
    rank: int
    seed: int
    data_seed: int

    def __post_init__(self) -> None:
        _bounded_int("rank", self.rank, minimum=0, maximum=_MAX_WORLD_SIZE - 1)
        _bounded_int("seed", self.seed, minimum=0, maximum=_MAX_SEED)
        _bounded_int("data_seed", self.data_seed, minimum=0, maximum=_MAX_SEED)

    def to_dict(self) -> dict[str, int]:
        return {"data_seed": self.data_seed, "rank": self.rank, "seed": self.seed}


@dataclass(frozen=True, slots=True)
class ExecutionStrategyPlan:
    training_plan_digest: str
    topology_report_digest: str
    topology_digest: str
    strategy: StrategyKind
    world_size: int
    device_ordinals: tuple[int, ...]
    device_budgets: tuple[DeviceStrategyBudget, ...]
    host_ram_required_bytes: int
    host_storage_required_bytes: int
    per_device_batch_size: int
    gradient_accumulation_steps: int
    effective_global_batch_size: int
    rank_seed_policy: str
    rank_seeds: tuple[RankSeed, ...]
    schema: str = STRATEGY_PLAN_SCHEMA
    schema_version: int = STRATEGY_PLAN_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_digest("training_plan_digest", self.training_plan_digest)
        _require_digest("topology_report_digest", self.topology_report_digest)
        _require_digest("topology_digest", self.topology_digest)
        object.__setattr__(self, "strategy", StrategyKind(self.strategy))
        _bounded_int("world_size", self.world_size, minimum=1, maximum=_MAX_WORLD_SIZE)
        ordinals = tuple(self.device_ordinals)
        object.__setattr__(self, "device_ordinals", ordinals)
        if ordinals != tuple(sorted(set(ordinals))):
            raise TuningRuntimeError("device_ordinals must be unique and sorted")
        if len(ordinals) != self.world_size:
            raise TuningRuntimeError("world_size must equal selected device count")
        expected_world_size = 1 if self.strategy is StrategyKind.SINGLE_GPU else 2
        if self.world_size != expected_world_size:
            raise TuningRuntimeError(
                f"{self.strategy.value} requires world_size={expected_world_size}"
            )
        budgets = tuple(self.device_budgets)
        object.__setattr__(self, "device_budgets", budgets)
        if tuple(item.ordinal for item in budgets) != ordinals:
            raise TuningRuntimeError("device budgets must exactly match selected device ordinals")
        _bounded_int(
            "host_ram_required_bytes",
            self.host_ram_required_bytes,
            minimum=0,
            maximum=_MAX_BYTES,
        )
        _bounded_int(
            "host_storage_required_bytes",
            self.host_storage_required_bytes,
            minimum=0,
            maximum=_MAX_BYTES,
        )
        _bounded_int(
            "per_device_batch_size",
            self.per_device_batch_size,
            minimum=1,
            maximum=_MAX_BATCH,
        )
        _bounded_int(
            "gradient_accumulation_steps",
            self.gradient_accumulation_steps,
            minimum=1,
            maximum=_MAX_BATCH,
        )
        expected_batch = (
            self.per_device_batch_size
            * self.gradient_accumulation_steps
            * self.world_size
        )
        if self.effective_global_batch_size != expected_batch:
            raise TuningRuntimeError(
                "effective_global_batch_size must equal "
                "per_device_batch_size * gradient_accumulation_steps * world_size"
            )
        _bounded_int(
            "effective_global_batch_size",
            self.effective_global_batch_size,
            minimum=1,
            maximum=_MAX_BATCH * _MAX_BATCH * _MAX_WORLD_SIZE,
        )
        if self.rank_seed_policy != "offset_by_rank_v1":
            raise TuningRuntimeError("rank_seed_policy must be offset_by_rank_v1")
        rank_seeds = tuple(self.rank_seeds)
        object.__setattr__(self, "rank_seeds", rank_seeds)
        if tuple(item.rank for item in rank_seeds) != tuple(range(self.world_size)):
            raise TuningRuntimeError("rank seeds must cover every rank exactly once")

    def descriptor(self) -> dict[str, object]:
        return {
            "device_budgets": [item.to_dict() for item in self.device_budgets],
            "device_ordinals": list(self.device_ordinals),
            "effective_global_batch_size": self.effective_global_batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "host_ram_required_bytes": self.host_ram_required_bytes,
            "host_storage_required_bytes": self.host_storage_required_bytes,
            "per_device_batch_size": self.per_device_batch_size,
            "rank_seed_policy": self.rank_seed_policy,
            "rank_seeds": [item.to_dict() for item in self.rank_seeds],
            "schema": self.schema,
            "schema_version": self.schema_version,
            "strategy": self.strategy.value,
            "topology_digest": self.topology_digest,
            "topology_report_digest": self.topology_report_digest,
            "training_plan_digest": self.training_plan_digest,
            "world_size": self.world_size,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.descriptor())

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "strategy_plan_digest": self.digest}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _rank_seeds(seeds: SeedConfig, world_size: int) -> tuple[RankSeed, ...]:
    records: list[RankSeed] = []
    for rank in range(world_size):
        seed = seeds.seed + rank
        data_seed = seeds.data_seed + rank
        if seed > _MAX_SEED or data_seed > _MAX_SEED:
            raise TuningRuntimeError("rank seed offset exceeds accepted seed range")
        records.append(RankSeed(rank=rank, seed=seed, data_seed=data_seed))
    return tuple(records)


def build_execution_strategy_plan(
    training_plan: TrainingPlan,
    topology_report: AcceleratorTopologyReport,
    *,
    strategy: StrategyKind,
    device_ordinals: tuple[int, ...],
    per_device_batch_size: int | None = None,
) -> ExecutionStrategyPlan:
    strategy = StrategyKind(strategy)
    if topology_report.disposition is not TopologyDisposition.READY:
        raise TuningRuntimeError("strategy planning requires ready topology evidence")
    observed = topology_report.observed
    topology_digest = topology_report.topology_digest
    if observed is None or topology_digest is None:
        raise TuningRuntimeError("strategy planning requires observed topology evidence")
    ordinals = tuple(device_ordinals)
    if ordinals != tuple(sorted(set(ordinals))):
        raise TuningRuntimeError("device_ordinals must be unique and sorted")
    expected_world_size = 1 if strategy is StrategyKind.SINGLE_GPU else 2
    if len(ordinals) != expected_world_size:
        raise TuningRuntimeError(
            f"{strategy.value} requires exactly {expected_world_size} selected devices"
        )
    device_map = {device.index: device for device in observed.devices}
    selected = []
    for ordinal in ordinals:
        if ordinal not in device_map:
            raise TuningRuntimeError("selected device ordinal is missing from topology")
        selected.append(device_map[ordinal])

    required_vram = training_plan.resources.vram_required_free_bytes
    total_limit = training_plan.resources.vram_total_limit_bytes
    budgets: list[DeviceStrategyBudget] = []
    for device in selected:
        if device.vram_free_bytes is None or device.vram_total_bytes is None:
            raise TuningRuntimeError("selected device VRAM evidence is unknown")
        policy_total = (
            device.vram_total_bytes
            if total_limit is None
            else min(device.vram_total_bytes, total_limit)
        )
        if required_vram > policy_total:
            raise TuningRuntimeError("required VRAM exceeds selected device policy total")
        if required_vram > min(device.vram_free_bytes, policy_total):
            raise TuningRuntimeError("required VRAM exceeds selected device available budget")
        budgets.append(
            DeviceStrategyBudget(
                ordinal=device.index,
                required_free_vram_bytes=required_vram,
                observed_free_vram_bytes=min(device.vram_free_bytes, policy_total),
                observed_total_vram_bytes=policy_total,
            )
        )

    batch = (
        training_plan.sft.train_batch_size
        if per_device_batch_size is None
        else per_device_batch_size
    )
    _bounded_int("per_device_batch_size", batch, minimum=1, maximum=_MAX_BATCH)
    baseline_effective_batch = (
        training_plan.sft.train_batch_size
        * training_plan.sft.gradient_accumulation_steps
    )
    denominator = batch * expected_world_size
    if baseline_effective_batch % denominator != 0:
        raise TuningRuntimeError(
            "strategy cannot preserve TrainingPlan effective global batch with integer accumulation"
        )
    accumulation = baseline_effective_batch // denominator
    if accumulation < 1:
        raise TuningRuntimeError("strategy accumulation must remain positive")

    return ExecutionStrategyPlan(
        training_plan_digest=training_plan.digest,
        topology_report_digest=topology_report.digest,
        topology_digest=topology_digest,
        strategy=strategy,
        world_size=expected_world_size,
        device_ordinals=ordinals,
        device_budgets=tuple(budgets),
        host_ram_required_bytes=training_plan.resources.ram_required_bytes,
        host_storage_required_bytes=training_plan.resources.disk_required_bytes,
        per_device_batch_size=batch,
        gradient_accumulation_steps=accumulation,
        effective_global_batch_size=baseline_effective_batch,
        rank_seed_policy="offset_by_rank_v1",
        rank_seeds=_rank_seeds(training_plan.seeds, expected_world_size),
    )


@dataclass(frozen=True, slots=True)
class StrategyBenchmarkPolicy:
    min_throughput_speedup_ratio: float = MIN_REPLICATED_THROUGHPUT_SPEEDUP_RATIO
    max_eval_loss_regression: float = MAX_EVAL_LOSS_REGRESSION

    def __post_init__(self) -> None:
        speedup = _bounded_float(
            "min_throughput_speedup_ratio",
            self.min_throughput_speedup_ratio,
            minimum=1.0,
        )
        regression = _bounded_float(
            "max_eval_loss_regression",
            self.max_eval_loss_regression,
            minimum=0.0,
        )
        object.__setattr__(self, "min_throughput_speedup_ratio", speedup)
        object.__setattr__(self, "max_eval_loss_regression", regression)

    def to_dict(self) -> dict[str, float]:
        return {
            "max_eval_loss_regression": self.max_eval_loss_regression,
            "min_throughput_speedup_ratio": self.min_throughput_speedup_ratio,
        }


@dataclass(frozen=True, slots=True)
class StrategyBenchmarkMeasurement:
    strategy_plan_digest: str
    benchmark_config_digest: str
    processed_samples: int
    wall_seconds: float
    eval_loss: float | None
    train_loss: float | None
    per_device_peak_vram_bytes: tuple[tuple[int, int], ...]
    run_integrity: bool
    checkpoint_integrity: bool

    def __post_init__(self) -> None:
        _require_digest("strategy_plan_digest", self.strategy_plan_digest)
        _require_digest("benchmark_config_digest", self.benchmark_config_digest)
        _bounded_int(
            "processed_samples",
            self.processed_samples,
            minimum=1,
            maximum=10_000_000_000,
        )
        object.__setattr__(
            self,
            "wall_seconds",
            _bounded_float("wall_seconds", self.wall_seconds, minimum=1e-9),
        )
        for name in ("eval_loss", "train_loss"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(
                    self,
                    name,
                    _bounded_float(name, value, minimum=0.0),
                )
        peaks = tuple(self.per_device_peak_vram_bytes)
        object.__setattr__(self, "per_device_peak_vram_bytes", peaks)
        ordinals = tuple(item[0] for item in peaks)
        if ordinals != tuple(sorted(set(ordinals))):
            raise TuningRuntimeError("per-device benchmark VRAM ordinals must be unique and sorted")
        for ordinal, value in peaks:
            _bounded_int("benchmark ordinal", ordinal, minimum=0, maximum=_MAX_WORLD_SIZE - 1)
            _bounded_int(
                "per_device_peak_vram_bytes",
                value,
                minimum=0,
                maximum=_MAX_BYTES,
            )
        if not isinstance(self.run_integrity, bool) or not isinstance(
            self.checkpoint_integrity, bool
        ):
            raise TuningRuntimeError("benchmark integrity fields must be booleans")

    @property
    def throughput_samples_per_second(self) -> float:
        return self.processed_samples / self.wall_seconds

    def to_dict(self) -> dict[str, object]:
        return {
            "benchmark_config_digest": self.benchmark_config_digest,
            "checkpoint_integrity": self.checkpoint_integrity,
            "eval_loss": self.eval_loss,
            "per_device_peak_vram_bytes": [
                {"ordinal": ordinal, "peak_vram_bytes": value}
                for ordinal, value in self.per_device_peak_vram_bytes
            ],
            "processed_samples": self.processed_samples,
            "run_integrity": self.run_integrity,
            "strategy_plan_digest": self.strategy_plan_digest,
            "throughput_samples_per_second": self.throughput_samples_per_second,
            "train_loss": self.train_loss,
            "wall_seconds": self.wall_seconds,
        }


@dataclass(frozen=True, slots=True)
class StrategyBenchmarkReport:
    disposition: StrategyBenchmarkDisposition
    blockers: tuple[str, ...]
    policy: StrategyBenchmarkPolicy
    training_plan_digest: str
    topology_digest: str
    effective_global_batch_size: int
    benchmark_config_digest: str
    baseline: StrategyBenchmarkMeasurement
    candidate: StrategyBenchmarkMeasurement
    throughput_speedup_ratio: float
    eval_loss_delta: float | None
    launch_authorized: bool = False
    schema: str = STRATEGY_BENCHMARK_SCHEMA
    schema_version: int = STRATEGY_BENCHMARK_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "disposition",
            StrategyBenchmarkDisposition(self.disposition),
        )
        blockers = tuple(sorted(set(self.blockers)))
        if any(not blocker for blocker in blockers):
            raise TuningRuntimeError("benchmark blockers must be non-empty strings")
        object.__setattr__(self, "blockers", blockers)
        _require_digest("training_plan_digest", self.training_plan_digest)
        _require_digest("topology_digest", self.topology_digest)
        _require_digest("benchmark_config_digest", self.benchmark_config_digest)
        _bounded_int(
            "effective_global_batch_size",
            self.effective_global_batch_size,
            minimum=1,
            maximum=_MAX_BATCH * _MAX_BATCH * _MAX_WORLD_SIZE,
        )
        object.__setattr__(
            self,
            "throughput_speedup_ratio",
            _bounded_float(
                "throughput_speedup_ratio",
                self.throughput_speedup_ratio,
                minimum=0.0,
            ),
        )
        if self.eval_loss_delta is not None:
            if isinstance(self.eval_loss_delta, bool) or not isinstance(
                self.eval_loss_delta, (int, float)
            ):
                raise TuningRuntimeError("eval_loss_delta must be numeric or null")
            delta = float(self.eval_loss_delta)
            if not math.isfinite(delta):
                raise TuningRuntimeError("eval_loss_delta must be finite or null")
            object.__setattr__(self, "eval_loss_delta", delta)
        if self.launch_authorized is not False:
            raise TuningRuntimeError("V2.4.2 benchmark reports cannot authorize launch")
        if self.disposition is StrategyBenchmarkDisposition.QUALIFIED and blockers:
            raise TuningRuntimeError("qualified benchmark report cannot contain blockers")

    def descriptor(self) -> dict[str, object]:
        return {
            "baseline": self.baseline.to_dict(),
            "benchmark_config_digest": self.benchmark_config_digest,
            "blockers": list(self.blockers),
            "candidate": self.candidate.to_dict(),
            "disposition": self.disposition.value,
            "effective_global_batch_size": self.effective_global_batch_size,
            "eval_loss_delta": self.eval_loss_delta,
            "launch_authorized": self.launch_authorized,
            "policy": self.policy.to_dict(),
            "schema": self.schema,
            "schema_version": self.schema_version,
            "throughput_speedup_ratio": self.throughput_speedup_ratio,
            "topology_digest": self.topology_digest,
            "training_plan_digest": self.training_plan_digest,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.descriptor())

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "report_digest": self.digest}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _measurement_blockers(
    plan: ExecutionStrategyPlan,
    measurement: StrategyBenchmarkMeasurement,
    label: str,
) -> list[str]:
    blockers: list[str] = []
    if measurement.strategy_plan_digest != plan.digest:
        blockers.append(f"{label}_strategy_plan_mismatch")
    if not measurement.run_integrity:
        blockers.append(f"{label}_run_integrity_failed")
    if not measurement.checkpoint_integrity:
        blockers.append(f"{label}_checkpoint_integrity_failed")
    peaks = dict(measurement.per_device_peak_vram_bytes)
    if tuple(peaks) != plan.device_ordinals:
        blockers.append(f"{label}_per_device_vram_mismatch")
    else:
        totals = {item.ordinal: item.observed_total_vram_bytes for item in plan.device_budgets}
        if any(peaks[ordinal] > totals[ordinal] for ordinal in plan.device_ordinals):
            blockers.append(f"{label}_peak_vram_exceeds_device_total")
    return blockers


def evaluate_strategy_benchmark(
    baseline_plan: ExecutionStrategyPlan,
    candidate_plan: ExecutionStrategyPlan,
    baseline: StrategyBenchmarkMeasurement,
    candidate: StrategyBenchmarkMeasurement,
    *,
    policy: StrategyBenchmarkPolicy | None = None,
) -> StrategyBenchmarkReport:
    policy = policy or StrategyBenchmarkPolicy()
    blockers: list[str] = []
    if baseline_plan.strategy is not StrategyKind.SINGLE_GPU:
        blockers.append("baseline_strategy_must_be_single_gpu")
    if candidate_plan.strategy is not StrategyKind.REPLICATED_DATA_PARALLEL:
        blockers.append("candidate_strategy_must_be_replicated_data_parallel")
    if baseline_plan.training_plan_digest != candidate_plan.training_plan_digest:
        blockers.append("training_plan_mismatch")
    if baseline_plan.topology_digest != candidate_plan.topology_digest:
        blockers.append("topology_mismatch")
    if (
        baseline_plan.effective_global_batch_size
        != candidate_plan.effective_global_batch_size
    ):
        blockers.append("effective_global_batch_mismatch")
    if baseline.benchmark_config_digest != candidate.benchmark_config_digest:
        blockers.append("benchmark_config_mismatch")
    if baseline.processed_samples != candidate.processed_samples:
        blockers.append("processed_samples_mismatch")
    blockers.extend(_measurement_blockers(baseline_plan, baseline, "baseline"))
    blockers.extend(_measurement_blockers(candidate_plan, candidate, "candidate"))

    speedup = (
        candidate.throughput_samples_per_second
        / baseline.throughput_samples_per_second
    )
    eval_delta: float | None = None
    inconclusive = False
    if baseline.eval_loss is None or candidate.eval_loss is None:
        blockers.append("eval_loss_missing")
        inconclusive = True
    else:
        eval_delta = candidate.eval_loss - baseline.eval_loss
        if eval_delta > policy.max_eval_loss_regression:
            blockers.append("eval_loss_regression")
    if speedup < policy.min_throughput_speedup_ratio:
        blockers.append("throughput_gain_below_threshold")

    hard_blockers = [
        blocker
        for blocker in blockers
        if blocker not in {"eval_loss_missing"}
    ]
    if not blockers:
        disposition = StrategyBenchmarkDisposition.QUALIFIED
    elif inconclusive and not hard_blockers:
        disposition = StrategyBenchmarkDisposition.INCONCLUSIVE
    else:
        disposition = StrategyBenchmarkDisposition.REJECTED

    return StrategyBenchmarkReport(
        disposition=disposition,
        blockers=tuple(blockers),
        policy=policy,
        training_plan_digest=baseline_plan.training_plan_digest,
        topology_digest=baseline_plan.topology_digest,
        effective_global_batch_size=baseline_plan.effective_global_batch_size,
        benchmark_config_digest=baseline.benchmark_config_digest,
        baseline=baseline,
        candidate=candidate,
        throughput_speedup_ratio=speedup,
        eval_loss_delta=eval_delta,
        launch_authorized=False,
    )
