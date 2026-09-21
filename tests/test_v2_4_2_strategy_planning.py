from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.tuning import (
    AcceleratorDevice,
    AcceleratorTopologyReport,
    DatasetBinding,
    ExecutionStrategyPlan,
    ModelBinding,
    ObservedAcceleratorTopology,
    ResourceRequest,
    SFTTrainingConfig,
    SeedConfig,
    StrategyBenchmarkDisposition,
    StrategyBenchmarkMeasurement,
    StrategyKind,
    TopologyDisposition,
    TrainingAuthorization,
    TrainingBackend,
    TrainingMode,
    TrainingPlan,
    build_execution_strategy_plan,
    evaluate_strategy_benchmark,
)

GIB = 1024**3
A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64


def _training_plan(**changes: object) -> TrainingPlan:
    values: dict[str, object] = {
        "mode": TrainingMode.FIXTURE_SFT,
        "authorization": TrainingAuthorization.FIXTURE,
        "fixture_authorization": "repository-owned-r15.9-fixture",
        "model": ModelBinding(
            model_ref="fixture/base",
            model_revision="fixture-rev-1",
            model_digest=A,
            tokenizer_ref="fixture/tokenizer",
            tokenizer_revision="fixture-tokenizer-rev-1",
            tokenizer_digest=B,
            assistant_mask_capable=True,
        ),
        "dataset": DatasetBinding(
            dataset_id="fixture-dataset-v1",
            dataset_digest=C,
            manifest_digest=D,
            train_export_digest=A,
            validation_export_digest=B,
            train_rows=8,
            validation_rows=3,
        ),
        "sft": SFTTrainingConfig(
            max_steps=4,
            checkpoint_steps=2,
            eval_steps=2,
            train_batch_size=1,
            gradient_accumulation_steps=4,
        ),
        "seeds": SeedConfig(seed=100, data_seed=200),
        "resources": ResourceRequest(
            disk_required_bytes=20 * GIB,
            ram_required_bytes=8 * GIB,
            vram_estimate_bytes=6 * GIB,
            vram_reserve_bytes=1 * GIB,
            vram_headroom_bytes=1 * GIB,
        ),
    }
    values.update(changes)
    return TrainingPlan(**values)  # type: ignore[arg-type]


def _topology(*, free: int | None = 12 * GIB, total: int | None = 16 * GIB) -> AcceleratorTopologyReport:
    devices = (
        AcceleratorDevice(TrainingBackend.CUDA, 0, "NVIDIA Tesla T4", free, total),
        AcceleratorDevice(TrainingBackend.CUDA, 1, "NVIDIA Tesla T4", free, total),
    )
    observed = ObservedAcceleratorTopology(TrainingBackend.CUDA, devices)
    return AcceleratorTopologyReport(
        disposition=TopologyDisposition.READY,
        request_digest=A,
        backend=TrainingBackend.CUDA,
        provider_request=None,
        observed=observed,
    )


def _plans() -> tuple[ExecutionStrategyPlan, ExecutionStrategyPlan]:
    training = _training_plan()
    topology = _topology()
    single = build_execution_strategy_plan(
        training,
        topology,
        strategy=StrategyKind.SINGLE_GPU,
        device_ordinals=(0,),
    )
    replicated = build_execution_strategy_plan(
        training,
        topology,
        strategy=StrategyKind.REPLICATED_DATA_PARALLEL,
        device_ordinals=(0, 1),
    )
    return single, replicated


def _measurement(
    plan: ExecutionStrategyPlan,
    *,
    wall_seconds: float,
    eval_loss: float | None = 0.4,
    run_integrity: bool = True,
    checkpoint_integrity: bool = True,
    config_digest: str = E,
) -> StrategyBenchmarkMeasurement:
    peaks = tuple((ordinal, 7 * GIB) for ordinal in plan.device_ordinals)
    return StrategyBenchmarkMeasurement(
        strategy_plan_digest=plan.digest,
        benchmark_config_digest=config_digest,
        processed_samples=1_000,
        wall_seconds=wall_seconds,
        eval_loss=eval_loss,
        train_loss=0.3,
        per_device_peak_vram_bytes=peaks,
        run_integrity=run_integrity,
        checkpoint_integrity=checkpoint_integrity,
    )


def test_strategy_plans_bind_training_topology_world_size_batch_and_rank_seeds() -> None:
    single, replicated = _plans()
    assert single.training_plan_digest == replicated.training_plan_digest
    assert single.topology_digest == replicated.topology_digest
    assert single.strategy is StrategyKind.SINGLE_GPU
    assert single.world_size == 1
    assert single.device_ordinals == (0,)
    assert single.gradient_accumulation_steps == 4
    assert replicated.strategy is StrategyKind.REPLICATED_DATA_PARALLEL
    assert replicated.world_size == 2
    assert replicated.device_ordinals == (0, 1)
    assert replicated.gradient_accumulation_steps == 2
    assert single.effective_global_batch_size == replicated.effective_global_batch_size == 4
    assert [item.to_dict() for item in replicated.rank_seeds] == [
        {"data_seed": 200, "rank": 0, "seed": 100},
        {"data_seed": 201, "rank": 1, "seed": 101},
    ]
    assert single.digest != replicated.digest


def test_host_resources_are_not_multiplied_and_vram_is_device_specific() -> None:
    _single, replicated = _plans()
    assert replicated.host_ram_required_bytes == 8 * GIB
    assert replicated.host_storage_required_bytes == 20 * GIB
    assert [item.required_free_vram_bytes for item in replicated.device_budgets] == [
        8 * GIB,
        8 * GIB,
    ]
    assert "aggregate_vram" not in json.dumps(replicated.to_dict())


def test_replicated_strategy_rejects_pooled_vram_and_unknown_device_budget() -> None:
    too_large = _training_plan(
        resources=ResourceRequest(vram_estimate_bytes=20 * GIB)
    )
    with pytest.raises(ValueError, match="policy total"):
        build_execution_strategy_plan(
            too_large,
            _topology(),
            strategy=StrategyKind.REPLICATED_DATA_PARALLEL,
            device_ordinals=(0, 1),
        )
    with pytest.raises(ValueError, match="VRAM evidence is unknown"):
        build_execution_strategy_plan(
            _training_plan(),
            _topology(free=None, total=None),
            strategy=StrategyKind.REPLICATED_DATA_PARALLEL,
            device_ordinals=(0, 1),
        )


def test_strategy_requires_explicit_exact_ordinals_and_preserved_effective_batch() -> None:
    training = _training_plan()
    topology = _topology()
    with pytest.raises(ValueError, match="exactly 2 selected devices"):
        build_execution_strategy_plan(
            training,
            topology,
            strategy=StrategyKind.REPLICATED_DATA_PARALLEL,
            device_ordinals=(0,),
        )
    with pytest.raises(ValueError, match="unique and sorted"):
        build_execution_strategy_plan(
            training,
            topology,
            strategy=StrategyKind.REPLICATED_DATA_PARALLEL,
            device_ordinals=(1, 0),
        )
    with pytest.raises(ValueError, match="cannot preserve"):
        build_execution_strategy_plan(
            replace(
                training,
                sft=replace(training.sft, gradient_accumulation_steps=3),
            ),
            topology,
            strategy=StrategyKind.REPLICATED_DATA_PARALLEL,
            device_ordinals=(0, 1),
        )


def test_strategy_rejects_non_ready_topology_and_missing_device() -> None:
    training = _training_plan()
    topology = _topology()
    with pytest.raises(ValueError, match="ready topology"):
        build_execution_strategy_plan(
            replace(topology, disposition=TopologyDisposition.MISMATCH, blockers=("fixture",)),
            training,  # type: ignore[arg-type]
            strategy=StrategyKind.SINGLE_GPU,
            device_ordinals=(0,),
        )


def test_strategy_plan_json_schema_is_valid_and_accepts_serialization() -> None:
    single, _replicated = _plans()
    schema = json.loads(
        Path("schemas/v2-4-2-execution-strategy.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(single.to_dict())


def test_paired_benchmark_qualifies_only_material_gain_without_quality_regression() -> None:
    single, replicated = _plans()
    baseline = _measurement(single, wall_seconds=100.0)
    candidate = _measurement(replicated, wall_seconds=70.0)
    report = evaluate_strategy_benchmark(single, replicated, baseline, candidate)
    assert report.disposition is StrategyBenchmarkDisposition.QUALIFIED
    assert report.throughput_speedup_ratio > 1.25
    assert report.eval_loss_delta == 0.0
    assert report.launch_authorized is False
    assert report.blockers == ()


def test_paired_benchmark_rejects_subthreshold_gain_and_eval_loss_regression() -> None:
    single, replicated = _plans()
    slow = evaluate_strategy_benchmark(
        single,
        replicated,
        _measurement(single, wall_seconds=100.0),
        _measurement(replicated, wall_seconds=90.0),
    )
    assert slow.disposition is StrategyBenchmarkDisposition.REJECTED
    assert "throughput_gain_below_threshold" in slow.blockers

    regressed = evaluate_strategy_benchmark(
        single,
        replicated,
        _measurement(single, wall_seconds=100.0, eval_loss=0.4),
        _measurement(replicated, wall_seconds=70.0, eval_loss=0.41),
    )
    assert regressed.disposition is StrategyBenchmarkDisposition.REJECTED
    assert "eval_loss_regression" in regressed.blockers


def test_benchmark_is_inconclusive_without_eval_loss_and_rejects_integrity_failure() -> None:
    single, replicated = _plans()
    inconclusive = evaluate_strategy_benchmark(
        single,
        replicated,
        _measurement(single, wall_seconds=100.0, eval_loss=None),
        _measurement(replicated, wall_seconds=70.0, eval_loss=None),
    )
    assert inconclusive.disposition is StrategyBenchmarkDisposition.INCONCLUSIVE
    assert inconclusive.blockers == ("eval_loss_missing",)

    failed = evaluate_strategy_benchmark(
        single,
        replicated,
        _measurement(single, wall_seconds=100.0),
        _measurement(
            replicated,
            wall_seconds=70.0,
            run_integrity=False,
        ),
    )
    assert failed.disposition is StrategyBenchmarkDisposition.REJECTED
    assert "candidate_run_integrity_failed" in failed.blockers


def test_benchmark_requires_same_config_work_and_effective_global_batch() -> None:
    single, replicated = _plans()
    mismatch = evaluate_strategy_benchmark(
        single,
        replicated,
        _measurement(single, wall_seconds=100.0, config_digest=A),
        _measurement(replicated, wall_seconds=70.0, config_digest=B),
    )
    assert mismatch.disposition is StrategyBenchmarkDisposition.REJECTED
    assert "benchmark_config_mismatch" in mismatch.blockers


def test_benchmark_schema_validates_and_never_authorizes_launch() -> None:
    single, replicated = _plans()
    report = evaluate_strategy_benchmark(
        single,
        replicated,
        _measurement(single, wall_seconds=100.0),
        _measurement(replicated, wall_seconds=70.0),
    )
    schema = json.loads(
        Path("schemas/v2-4-2-strategy-benchmark.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(report.to_dict())
    assert report.to_dict()["launch_authorized"] is False
