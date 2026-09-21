from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.core.sandbox import ProcessSandbox, SandboxResult
from kodepoia.tuning import (
    AcceleratorDevice,
    AcceleratorTopologyReport,
    DatasetBinding,
    DistributedExecutionState,
    DistributedTrainingRunner,
    ModelBinding,
    ObservedAcceleratorTopology,
    QuantizationMode,
    ResourceRequest,
    SFTTrainingConfig,
    SeedConfig,
    StrategyBenchmarkMeasurement,
    StrategyKind,
    TopologyDisposition,
    TrainingAuthorization,
    TrainingBackend,
    TrainingMode,
    TrainingPlan,
    build_distributed_execution_plan,
    build_execution_strategy_plan,
    evaluate_strategy_benchmark,
)
from kodepoia.tuning.runtime import HostResources

GIB = 1024**3
A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _training_plan(root: Path) -> TrainingPlan:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    train = data / "train.jsonl"
    validation = data / "validation.jsonl"
    train.write_text('{"prompt":"a","completion":"b"}\n', encoding="utf-8")
    validation.write_text('{"prompt":"c","completion":"d"}\n', encoding="utf-8")
    return TrainingPlan(
        mode=TrainingMode.QLORA,
        authorization=TrainingAuthorization.TRAIN,
        capability_report_digest=E,
        model=ModelBinding(
            model_ref="fixture/base",
            model_revision="fixture-rev",
            model_digest=A,
            tokenizer_ref="fixture/tokenizer",
            tokenizer_revision="fixture-tokenizer-rev",
            tokenizer_digest=B,
            assistant_mask_capable=True,
        ),
        dataset=DatasetBinding(
            dataset_id="fixture-dataset",
            dataset_digest=C,
            manifest_digest=D,
            train_export_digest=_sha256(train),
            validation_export_digest=_sha256(validation),
            train_rows=8,
            validation_rows=3,
            train_path="data/train.jsonl",
            validation_path="data/validation.jsonl",
        ),
        quantization=QuantizationMode.BNB_NF4,
        sft=SFTTrainingConfig(
            max_steps=4,
            checkpoint_steps=2,
            eval_steps=2,
            train_batch_size=1,
            gradient_accumulation_steps=4,
        ),
        seeds=SeedConfig(seed=100, data_seed=200),
        resources=ResourceRequest(
            disk_required_bytes=20 * GIB,
            ram_required_bytes=8 * GIB,
            vram_estimate_bytes=6 * GIB,
            vram_reserve_bytes=1 * GIB,
            vram_headroom_bytes=1 * GIB,
        ),
    )


def _topology() -> AcceleratorTopologyReport:
    devices = (
        AcceleratorDevice(TrainingBackend.CUDA, 0, "NVIDIA Tesla T4", 12 * GIB, 16 * GIB),
        AcceleratorDevice(TrainingBackend.CUDA, 1, "NVIDIA Tesla T4", 12 * GIB, 16 * GIB),
    )
    return AcceleratorTopologyReport(
        disposition=TopologyDisposition.READY,
        request_digest=A,
        backend=TrainingBackend.CUDA,
        provider_request=None,
        observed=ObservedAcceleratorTopology(TrainingBackend.CUDA, devices),
    )


def _strategy_and_benchmark(root: Path):
    training = _training_plan(root)
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

    def measurement(plan, wall: float) -> StrategyBenchmarkMeasurement:
        return StrategyBenchmarkMeasurement(
            strategy_plan_digest=plan.digest,
            benchmark_config_digest=A,
            processed_samples=1000,
            wall_seconds=wall,
            eval_loss=0.4,
            train_loss=0.3,
            per_device_peak_vram_bytes=tuple((ordinal, 7 * GIB) for ordinal in plan.device_ordinals),
            run_integrity=True,
            checkpoint_integrity=True,
        )

    benchmark = evaluate_strategy_benchmark(
        single,
        replicated,
        measurement(single, 100.0),
        measurement(replicated, 70.0),
    )
    return training, replicated, benchmark


class FixedResources:
    def __init__(self, disk: int | None = 10**12, ram: int | None = 10**12) -> None:
        self.value = HostResources(disk, ram)

    def sample(self, _root: Path) -> HostResources:
        return self.value


class FakeDistributedSandbox:
    def __init__(self, root: Path, result: SandboxResult | None = None) -> None:
        self.root = root
        self.result = result
        self.calls: list[tuple[list[str], dict[str, str]]] = []
        self.omit_rank: int | None = None
        self.bad_ordinal = False

    def run_process_group(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        del cwd, timeout
        self.calls.append((list(argv), dict(env or {})))
        if self.result is not None:
            return self.result
        config_path = self.root / argv[-1]
        config = json.loads(config_path.read_text(encoding="utf-8"))
        execution = dict(config["execution_plan"])
        worker = dict(config["training_worker"])
        run_dir = self.root / str(worker["run_dir"])
        adapter = run_dir / "adapter" / "adapter_model.safetensors"
        adapter.parent.mkdir(parents=True, exist_ok=True)
        adapter.write_bytes(b"distributed-adapter")
        output = {
            "adapter_digest": _sha256(adapter),
            "adapter_path": adapter.relative_to(self.root).as_posix(),
            "checkpoints": [],
            "completed_steps": int(worker["sft"]["max_steps"]),
            "eval_loss": 0.4,
            "framework_versions": {"python": "3.12"},
            "optimized_splits": ["train"],
            "plan_digest": execution["training_plan_digest"],
            "resource_maxima": {
                "peak_ram_bytes": 1,
                "peak_vram_bytes": 7 * GIB,
                "wall_seconds": 1.0,
            },
            "train_loss": 0.3,
            "train_rows": int(worker["dataset"]["train_rows"]),
            "validation_rows": int(worker["dataset"]["validation_rows"]),
        }
        canonical = self.root / str(config["canonical_output_path"])
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_text(json.dumps(output), encoding="utf-8")
        from kodepoia.tuning.contracts import canonical_sha256

        evidence_dir = self.root / str(config["evidence_dir"])
        evidence_dir.mkdir(parents=True, exist_ok=True)
        for rank in range(2):
            if self.omit_rank == rank:
                continue
            rank_seed = execution["rank_seeds"][rank]
            record = {
                "canonical_output_digest": canonical_sha256(output) if rank == 0 else None,
                "completed_steps": int(worker["sft"]["max_steps"]),
                "data_seed": int(rank_seed["data_seed"]),
                "device_ordinal": (
                    9 if self.bad_ordinal and rank == 1 else int(execution["device_ordinals"][rank])
                ),
                "eval_loss": 0.4,
                "execution_plan_digest": execution["execution_plan_digest"],
                "failure_type": None,
                "local_rank": rank,
                "peak_vram_bytes": 7 * GIB,
                "rank": rank,
                "seed": int(rank_seed["seed"]),
                "shared_sampler_seed": int(execution["shared_sampler_seed"]),
                "state": "completed",
                "strategy_plan_digest": execution["strategy_plan_digest"],
                "topology_digest": execution["topology_digest"],
                "train_loss": 0.3,
                "training_plan_digest": execution["training_plan_digest"],
                "world_size": 2,
            }
            (evidence_dir / f"rank-{rank:05d}.json").write_text(
                json.dumps(record), encoding="utf-8"
            )
        return SandboxResult(0, "", "")


def test_execution_plan_binds_qualified_strategy_topology_batch_and_seeds(tmp_path: Path) -> None:
    training, strategy, benchmark = _strategy_and_benchmark(tmp_path)
    execution = build_distributed_execution_plan(training, strategy, benchmark)
    assert execution.training_plan_digest == training.digest
    assert execution.strategy_plan_digest == strategy.digest
    assert execution.benchmark_report_digest == benchmark.digest
    assert execution.topology_digest == strategy.topology_digest
    assert execution.world_size == 2
    assert execution.device_ordinals == (0, 1)
    assert execution.per_device_batch_size == 1
    assert execution.gradient_accumulation_steps == 2
    assert execution.effective_global_batch_size == 4
    assert execution.shared_sampler_seed == 200
    assert [item.to_dict() for item in execution.rank_seeds] == [
        {"data_seed": 200, "rank": 0, "seed": 100},
        {"data_seed": 201, "rank": 1, "seed": 101},
    ]
    assert execution.canonical_rank == 0
    assert execution.resume_authorized is False


def test_execution_plan_rejects_unqualified_or_wrong_candidate_strategy(tmp_path: Path) -> None:
    training, strategy, benchmark = _strategy_and_benchmark(tmp_path)
    rejected = replace(benchmark, disposition="rejected", blockers=("fixture",))
    with pytest.raises(ValueError, match="qualified V2.4.2 benchmark"):
        build_distributed_execution_plan(training, strategy, rejected)
    wrong = replace(
        benchmark,
        candidate=replace(benchmark.candidate, strategy_plan_digest=B),
    )
    with pytest.raises(ValueError, match="candidate strategy lineage"):
        build_distributed_execution_plan(training, strategy, wrong)


def test_runner_uses_fixed_two_rank_torchrun_boundary_and_bounded_env(tmp_path: Path) -> None:
    training, strategy, benchmark = _strategy_and_benchmark(tmp_path)
    sandbox = FakeDistributedSandbox(tmp_path)
    report = DistributedTrainingRunner(
        tmp_path,
        sandbox=sandbox,
        resource_probe=FixedResources(),
    ).run(training, strategy, benchmark)
    assert report.state is DistributedExecutionState.COMPLETED
    assert report.adapter_digest is not None
    argv, env = sandbox.calls[0]
    assert argv[:3] == [sys.executable, "-m", "torch.distributed.run"]
    assert "--standalone" in argv
    assert "--nnodes=1" in argv
    assert "--nproc-per-node=2" in argv
    assert "--max-restarts=0" in argv
    assert "--module" in argv
    assert "kodepoia.tuning.distributed_worker" in argv
    assert env == {"CUDA_VISIBLE_DEVICES": "0,1"}
    joined = " ".join(argv)
    assert training.model.model_ref not in joined
    assert training.dataset.dataset_id not in joined
    for forbidden in ("deepspeed", "fsdp", "tpu", "--rdzv-endpoint", "--rdzv-conf"):
        assert forbidden not in joined.lower()
    assert report.process_group_managed is True
    assert report.resume_authorized is False
    assert [item.rank for item in report.rank_evidence] == [0, 1]


def test_rank_failure_missing_or_mismatched_evidence_never_partially_succeeds(tmp_path: Path) -> None:
    training, strategy, benchmark = _strategy_and_benchmark(tmp_path)
    missing_root = tmp_path / "missing"
    missing_root.mkdir()
    training2, strategy2, benchmark2 = _strategy_and_benchmark(missing_root)
    missing = FakeDistributedSandbox(missing_root)
    missing.omit_rank = 1
    report = DistributedTrainingRunner(
        missing_root, sandbox=missing, resource_probe=FixedResources()
    ).run(training2, strategy2, benchmark2)
    assert report.state is DistributedExecutionState.FAILED
    assert report.adapter_digest is None

    bad_root = tmp_path / "bad"
    bad_root.mkdir()
    training3, strategy3, benchmark3 = _strategy_and_benchmark(bad_root)
    bad = FakeDistributedSandbox(bad_root)
    bad.bad_ordinal = True
    report = DistributedTrainingRunner(
        bad_root, sandbox=bad, resource_probe=FixedResources()
    ).run(training3, strategy3, benchmark3)
    assert report.state is DistributedExecutionState.FAILED
    assert report.adapter_digest is None


def test_timeout_cancel_and_nonzero_are_whole_group_terminal(tmp_path: Path) -> None:
    cases = (
        (SandboxResult(-1, "", "timeout", timed_out=True), DistributedExecutionState.TIMED_OUT),
        (SandboxResult(-1, "", "cancel", cancelled=True), DistributedExecutionState.CANCELLED),
        (SandboxResult(3, "", "rank failed"), DistributedExecutionState.FAILED),
    )
    for index, (result, expected) in enumerate(cases):
        root = tmp_path / str(index)
        root.mkdir()
        training, strategy, benchmark = _strategy_and_benchmark(root)
        report = DistributedTrainingRunner(
            root,
            sandbox=FakeDistributedSandbox(root, result),
            resource_probe=FixedResources(),
        ).run(training, strategy, benchmark)
        assert report.state is expected
        assert report.adapter_digest is None
        assert report.completed_steps == 0


def test_host_budget_unknown_blocks_before_process_group(tmp_path: Path) -> None:
    training, strategy, benchmark = _strategy_and_benchmark(tmp_path)
    sandbox = FakeDistributedSandbox(tmp_path)
    report = DistributedTrainingRunner(
        tmp_path,
        sandbox=sandbox,
        resource_probe=FixedResources(None, None),
    ).run(training, strategy, benchmark)
    assert report.state is DistributedExecutionState.BUDGET_BLOCKED
    assert set(report.blockers) == {"ram_budget_unknown", "storage_budget_unknown"}
    assert sandbox.calls == []


def test_process_sandbox_managed_group_executes_allowlisted_python(tmp_path: Path) -> None:
    sandbox = ProcessSandbox(tmp_path, {Path(sys.executable).name})
    result = sandbox.run_process_group([sys.executable, "-c", "print('GROUP_OK')"])
    assert result.returncode == 0
    assert result.stdout.strip() == "GROUP_OK"


def test_distributed_report_schema_validates_completed_fixture(tmp_path: Path) -> None:
    training, strategy, benchmark = _strategy_and_benchmark(tmp_path)
    report = DistributedTrainingRunner(
        tmp_path,
        sandbox=FakeDistributedSandbox(tmp_path),
        resource_probe=FixedResources(),
    ).run(training, strategy, benchmark)
    schema = json.loads(
        Path("schemas/v2-4-3-distributed-training.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(report.to_dict())


def test_public_tuning_import_remains_lightweight() -> None:
    import kodepoia.tuning  # noqa: F401

    assert "torch" not in sys.modules
    assert "transformers" not in sys.modules
    assert "accelerate" not in sys.modules
