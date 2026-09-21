from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.core.sandbox import SandboxResult
from kodepoia.tuning import (
    AcceleratorDevice,
    AcceleratorTopologyReport,
    DatasetBinding,
    DistributedExecutionState,
    DistributedRecoveryRunner,
    DistributedTrainingRunner,
    ModelBinding,
    ObservedAcceleratorTopology,
    QuantizationMode,
    ResourceRequest,
    SeedConfig,
    SFTTrainingConfig,
    StrategyBenchmarkMeasurement,
    StrategyKind,
    TopologyDisposition,
    TrainingAuthorization,
    TrainingBackend,
    TrainingMode,
    TrainingPlan,
    build_distributed_checkpoint_manifest,
    build_execution_strategy_plan,
    evaluate_strategy_benchmark,
)
from kodepoia.tuning.contracts import canonical_sha256
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


class SourceCheckpointSandbox:
    def __init__(self, root: Path) -> None:
        self.root = root

    def run_process_group(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        del cwd, timeout, env
        config = json.loads((self.root / argv[-1]).read_text(encoding="utf-8"))
        execution = dict(config["execution_plan"])
        worker = dict(config["training_worker"])
        run_dir = self.root / str(worker["run_dir"])
        checkpoint_dir = run_dir / "trainer" / "checkpoint-2"
        checkpoint_adapter = checkpoint_dir / "adapter_model.safetensors"
        checkpoint_adapter.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_adapter.write_bytes(b"checkpoint-adapter")
        checkpoint = {
            "artifact_digest": _sha256(checkpoint_adapter),
            "artifact_path": checkpoint_adapter.relative_to(self.root).as_posix(),
            "checkpoint_id": "checkpoint-2",
            "eval_loss": 0.5,
            "plan_digest": execution["training_plan_digest"],
            "step": 2,
            "train_loss": 0.4,
        }
        (checkpoint_dir / "checkpoint.json").write_text(
            json.dumps(checkpoint, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        adapter = run_dir / "adapter" / "adapter_model.safetensors"
        adapter.parent.mkdir(parents=True, exist_ok=True)
        adapter.write_bytes(b"distributed-adapter")
        output = {
            "adapter_digest": _sha256(adapter),
            "adapter_path": adapter.relative_to(self.root).as_posix(),
            "checkpoints": [checkpoint],
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
        evidence_dir = self.root / str(config["evidence_dir"])
        evidence_dir.mkdir(parents=True, exist_ok=True)
        for rank in range(2):
            seed = execution["rank_seeds"][rank]
            record = {
                "canonical_output_digest": canonical_sha256(output) if rank == 0 else None,
                "completed_steps": int(worker["sft"]["max_steps"]),
                "data_seed": int(seed["data_seed"]),
                "device_ordinal": int(execution["device_ordinals"][rank]),
                "eval_loss": 0.4,
                "execution_plan_digest": execution["execution_plan_digest"],
                "failure_type": None,
                "local_rank": rank,
                "peak_vram_bytes": 7 * GIB,
                "rank": rank,
                "seed": int(seed["seed"]),
                "shared_sampler_seed": int(execution["shared_sampler_seed"]),
                "state": "completed",
                "strategy_plan_digest": execution["strategy_plan_digest"],
                "topology_digest": execution["topology_digest"],
                "train_loss": 0.3,
                "training_plan_digest": execution["training_plan_digest"],
                "world_size": 2,
            }
            (evidence_dir / f"rank-{rank:05d}.json").write_text(json.dumps(record), encoding="utf-8")
        return SandboxResult(0, "", "")


class RecoverySandbox:
    def __init__(self, root: Path, result: SandboxResult | None = None) -> None:
        self.root = root
        self.result = result
        self.calls: list[tuple[list[str], dict[str, str], dict[str, object]]] = []
        self.omit_rank: int | None = None
        self.bad_manifest_digest = False

    def run_process_group(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        del cwd, timeout
        config = json.loads((self.root / argv[-1]).read_text(encoding="utf-8"))
        self.calls.append((list(argv), dict(env or {}), config))
        if self.result is not None:
            return self.result
        execution = dict(config["execution_plan"])
        recovery = dict(config["recovery_plan"])
        manifest = dict(config["checkpoint_manifest"])
        worker = dict(config["training_worker"])
        run_dir = self.root / str(worker["run_dir"])
        adapter = run_dir / "adapter" / "adapter_model.safetensors"
        adapter.parent.mkdir(parents=True, exist_ok=True)
        adapter.write_bytes(b"recovered-adapter")
        output = {
            "adapter_digest": _sha256(adapter),
            "adapter_path": adapter.relative_to(self.root).as_posix(),
            "checkpoints": [],
            "completed_steps": int(worker["sft"]["max_steps"]),
            "eval_loss": 0.35,
            "framework_versions": {"python": "3.12"},
            "optimized_splits": ["train"],
            "plan_digest": execution["training_plan_digest"],
            "resource_maxima": {
                "peak_ram_bytes": 1,
                "peak_vram_bytes": 7 * GIB,
                "wall_seconds": 1.0,
            },
            "train_loss": 0.25,
            "train_rows": int(worker["dataset"]["train_rows"]),
            "validation_rows": int(worker["dataset"]["validation_rows"]),
        }
        canonical = self.root / str(config["canonical_output_path"])
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_text(json.dumps(output), encoding="utf-8")
        evidence_dir = self.root / str(config["evidence_dir"])
        evidence_dir.mkdir(parents=True, exist_ok=True)
        for rank in range(2):
            if self.omit_rank == rank:
                continue
            seed = execution["rank_seeds"][rank]
            record = {
                "canonical_output_digest": canonical_sha256(output) if rank == 0 else None,
                "checkpoint_manifest_digest": (
                    B if self.bad_manifest_digest and rank == 1 else recovery["checkpoint_manifest_digest"]
                ),
                "completed_steps": int(worker["sft"]["max_steps"]),
                "data_seed": int(seed["data_seed"]),
                "device_ordinal": int(execution["device_ordinals"][rank]),
                "eval_loss": 0.35,
                "execution_plan_digest": execution["execution_plan_digest"],
                "failure_type": None,
                "local_rank": rank,
                "peak_vram_bytes": 7 * GIB,
                "rank": rank,
                "recovery_plan_digest": recovery["recovery_plan_digest"],
                "resumed_from_checkpoint_id": manifest["checkpoint_id"],
                "resumed_from_step": int(manifest["step"]),
                "seed": int(seed["seed"]),
                "shared_sampler_seed": int(execution["shared_sampler_seed"]),
                "state": "completed",
                "strategy_plan_digest": execution["strategy_plan_digest"],
                "topology_digest": execution["topology_digest"],
                "train_loss": 0.25,
                "training_plan_digest": execution["training_plan_digest"],
                "world_size": 2,
            }
            (evidence_dir / f"rank-{rank:05d}.json").write_text(json.dumps(record), encoding="utf-8")
        return SandboxResult(0, "", "")


def _source_and_manifest(root: Path):
    training, strategy, benchmark = _strategy_and_benchmark(root)
    source = DistributedTrainingRunner(
        root,
        sandbox=SourceCheckpointSandbox(root),
        resource_probe=FixedResources(),
    ).run(training, strategy, benchmark)
    manifest = build_distributed_checkpoint_manifest(
        root,
        training,
        strategy,
        benchmark,
        source,
        checkpoint_id="checkpoint-2",
    )
    return training, strategy, benchmark, source, manifest


def test_manifest_is_rank_zero_canonical_and_exact_lineage_bound(tmp_path: Path) -> None:
    training, strategy, benchmark, source, manifest = _source_and_manifest(tmp_path)
    assert manifest.source_report_digest == source.digest
    assert manifest.training_plan_digest == training.digest
    assert manifest.strategy_plan_digest == strategy.digest
    assert manifest.benchmark_report_digest == benchmark.digest
    assert manifest.world_size == 2
    assert manifest.device_ordinals == (0, 1)
    assert manifest.checkpoint_id == "checkpoint-2"
    assert manifest.step == 2
    assert manifest.canonical_rank == 0
    assert len(manifest.rank_evidence_digests) == 2
    schema = json.loads(
        Path("schemas/v2-4-4-distributed-checkpoint.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(manifest.to_dict())


def test_manifest_rejects_tampered_checkpoint_or_source_lineage(tmp_path: Path) -> None:
    training, strategy, benchmark, source, manifest = _source_and_manifest(tmp_path)
    artifact = tmp_path / manifest.checkpoint_artifact_path
    artifact.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="artifact digest mismatch"):
        DistributedRecoveryRunner(
            tmp_path,
            sandbox=RecoverySandbox(tmp_path),
            resource_probe=FixedResources(),
        ).resume(training, strategy, benchmark, manifest)

    fresh = tmp_path / "fresh"
    fresh.mkdir()
    training2, strategy2, benchmark2, source2, _manifest2 = _source_and_manifest(fresh)
    bad_source = replace(source2, training_plan_digest=A)
    with pytest.raises(ValueError, match="source TrainingPlan lineage mismatch"):
        build_distributed_checkpoint_manifest(
            fresh,
            training2,
            strategy2,
            benchmark2,
            bad_source,
            checkpoint_id="checkpoint-2",
        )


def test_recovery_uses_same_fixed_two_rank_launcher_and_exact_resume_path(tmp_path: Path) -> None:
    training, strategy, benchmark, source, manifest = _source_and_manifest(tmp_path)
    sandbox = RecoverySandbox(tmp_path)
    report = DistributedRecoveryRunner(
        tmp_path,
        sandbox=sandbox,
        resource_probe=FixedResources(),
    ).resume(training, strategy, benchmark, manifest)
    assert report.state is DistributedExecutionState.COMPLETED
    assert report.resume_authorized is True
    assert report.resumed_from_checkpoint_id == "checkpoint-2"
    assert report.resumed_from_step == 2
    assert report.source_report_digest == source.digest
    assert report.adapter_digest is not None
    argv, env, config = sandbox.calls[0]
    assert argv[:3] == [sys.executable, "-m", "torch.distributed.run"]
    assert "--standalone" in argv
    assert "--nnodes=1" in argv
    assert "--nproc-per-node=2" in argv
    assert "--max-restarts=0" in argv
    assert "kodepoia.tuning.distributed_worker" in argv
    assert env == {"CUDA_VISIBLE_DEVICES": "0,1"}
    worker = dict(config["training_worker"])
    assert worker["resume_checkpoint"] == manifest.checkpoint_metadata_path
    assert dict(config["checkpoint_manifest"])["manifest_digest"] == manifest.digest
    assert dict(config["recovery_plan"])["resume_authorized"] is True


def test_cancel_timeout_and_rank_failure_are_whole_group_terminal(tmp_path: Path) -> None:
    cases = (
        (SandboxResult(-1, "", "timeout", timed_out=True), DistributedExecutionState.TIMED_OUT),
        (SandboxResult(-1, "", "cancel", cancelled=True), DistributedExecutionState.CANCELLED),
        (SandboxResult(7, "", "rank failure"), DistributedExecutionState.FAILED),
    )
    for index, (result, expected) in enumerate(cases):
        root = tmp_path / str(index)
        root.mkdir()
        training, strategy, benchmark, _source, manifest = _source_and_manifest(root)
        report = DistributedRecoveryRunner(
            root,
            sandbox=RecoverySandbox(root, result),
            resource_probe=FixedResources(),
        ).resume(training, strategy, benchmark, manifest)
        assert report.state is expected
        assert report.adapter_digest is None
        assert report.canonical_training_report_digest is None
        assert report.resumed_from_checkpoint_id == manifest.checkpoint_id
        assert report.resume_authorized is True


def test_missing_or_tampered_rank_recovery_evidence_never_succeeds(tmp_path: Path) -> None:
    for mode in ("missing", "tampered"):
        root = tmp_path / mode
        root.mkdir()
        training, strategy, benchmark, _source, manifest = _source_and_manifest(root)
        sandbox = RecoverySandbox(root)
        if mode == "missing":
            sandbox.omit_rank = 1
        else:
            sandbox.bad_manifest_digest = True
        report = DistributedRecoveryRunner(
            root,
            sandbox=sandbox,
            resource_probe=FixedResources(),
        ).resume(training, strategy, benchmark, manifest)
        assert report.state is DistributedExecutionState.FAILED
        assert report.adapter_digest is None


def test_recovery_rejects_changed_topology_strategy_or_world_identity(tmp_path: Path) -> None:
    training, strategy, benchmark, _source, manifest = _source_and_manifest(tmp_path)
    changed = replace(manifest, topology_digest=B)
    with pytest.raises(ValueError, match="topology_digest mismatch"):
        DistributedRecoveryRunner(
            tmp_path,
            sandbox=RecoverySandbox(tmp_path),
            resource_probe=FixedResources(),
        ).resume(training, strategy, benchmark, changed)
    changed_world = replace(manifest, device_ordinals=(0, 2))
    with pytest.raises(ValueError, match="topology/world-size identity mismatch"):
        DistributedRecoveryRunner(
            tmp_path,
            sandbox=RecoverySandbox(tmp_path),
            resource_probe=FixedResources(),
        ).resume(training, strategy, benchmark, changed_world)


def test_recovery_report_schema_validates_completed_fixture(tmp_path: Path) -> None:
    training, strategy, benchmark, _source, manifest = _source_and_manifest(tmp_path)
    report = DistributedRecoveryRunner(
        tmp_path,
        sandbox=RecoverySandbox(tmp_path),
        resource_probe=FixedResources(),
    ).resume(training, strategy, benchmark, manifest)
    schema = json.loads(
        Path("schemas/v2-4-4-distributed-recovery.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(report.to_dict())


def test_public_tuning_import_still_does_not_import_ml_packages() -> None:
    import kodepoia.tuning  # noqa: F401

    assert "torch" not in sys.modules
    assert "transformers" not in sys.modules
    assert "accelerate" not in sys.modules
