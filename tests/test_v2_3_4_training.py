from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from kodepoia.bench.decision import (
    BackendCapability,
    BudgetStatus,
    DecisionEvidence,
    DiagnosticComponent,
    DiagnosticProbe,
    ExpectedImpact,
    GapDecisionEngine,
    ProbeStatus,
)
from kodepoia.bench.kodebench import (
    BenchmarkSuite,
    BenchmarkTaskSpec,
    KodeBenchRunner,
    ModelIdentity,
    RunConfig,
    ScorerKind,
    ScorerSpec,
)
from kodepoia.brain.base import BrainResponse
from kodepoia.experience.contracts import PolicyDecision
from kodepoia.kodestudio.model_lab_training import ModelLabTrainingService, TrainingUXError
from kodepoia.tuning.contracts import (
    CapabilityReport,
    CapabilityState,
    ResourcePreflight,
    RuntimeDisposition,
    TrainingBackend,
)
from kodepoia.tuning.kaggle_remote import save_training_plan
from kodepoia.tuning.r15_ux import R15UXPolicyError, R15UXService, R15WorkflowRequest
from kodepoia.tuning.training import (
    CheckpointRecord,
    DatasetBinding,
    ModelBinding,
    SFTTrainingConfig,
    TrainingAuthorization,
    TrainingMode,
    TrainingPlan,
    TrainingReport,
    TrainingRunState,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class FakeBrain:
    def preload(self, model: str, **kwargs: object) -> dict[str, object]:
        return {"done_reason": "load"}

    def unload(self, model: str) -> None:
        return None

    def running_models(self) -> list[dict[str, object]]:
        return []

    def show_model(self, model: str) -> dict[str, object]:
        return {"capabilities": ["completion"]}

    def chat(self, model: str, messages: list[object], **kwargs: object) -> BrainResponse:
        del kwargs
        prompt = str(messages[0].content)
        return BrainResponse(
            "WRONG" if "gap" in prompt else "OK",
            model,
            metrics={"eval_count": 1, "eval_duration": 1_000_000_000},
        )


def _suite() -> BenchmarkSuite:
    return BenchmarkSuite(
        "v234-fixture",
        "v1",
        (
            BenchmarkTaskSpec(
                task_id="python-gap",
                domain="python",
                critical=True,
                prompt="gap prompt",
                scorer=ScorerSpec.create(
                    ScorerKind.EXACT,
                    version="fixture-v1",
                    config={"expected": "OK"},
                ),
            ),
        ),
    )


def _decision_evidence() -> DecisionEvidence:
    diagnostics = tuple(
        DiagnosticProbe(
            component=component,
            status=ProbeStatus.PASS,
            evidence_digest=_digest(component.value),
        )
        for component in (
            DiagnosticComponent.TOOL,
            DiagnosticComponent.RETRIEVAL,
            DiagnosticComponent.ROUTER,
            DiagnosticComponent.CONTEXT,
            DiagnosticComponent.PROMPT,
            DiagnosticComponent.PRODUCT,
        )
    )
    return DecisionEvidence(
        benchmark_reproducible=True,
        contamination_valid=True,
        dataset_license=PolicyDecision.ALLOW,
        base_model_license=PolicyDecision.ALLOW,
        backend_capability=BackendCapability.SUPPORTED,
        budget_status=BudgetStatus.WITHIN_BUDGET,
        rollback_ready=True,
        expected_impact=ExpectedImpact.MEANINGFUL,
        diagnostics=diagnostics,
        evidence_digests=(("system", _digest("system")),),
    )


def _project(tmp_path: Path) -> tuple[Path, TrainingPlan, TrainingReport]:
    root = tmp_path / "project"
    evidence = root / ".kodepoia" / "tuning"
    bench = root / ".kodepoia" / "benchmarks"
    data = root / "data"
    evidence.mkdir(parents=True)
    bench.mkdir(parents=True)
    data.mkdir(parents=True)

    report = KodeBenchRunner(FakeBrain()).run(
        ["base", "peer"],
        _suite(),
        config=RunConfig(repeats=1),
        identities={
            "base": ModelIdentity(
                "base",
                _digest("base-model"),
                runtime="fixture",
                runtime_version="1",
            ),
            "peer": ModelIdentity(
                "peer",
                _digest("peer-model"),
                runtime="fixture",
                runtime_version="1",
            ),
        },
    )
    report.save(bench / "baseline.json")
    decision = GapDecisionEngine().evaluate(
        report.to_dict(),
        base_model_ref="base",
        evidence=_decision_evidence(),
        dataset={
            "dataset_id": "fixture-dataset",
            "dataset_digest": _digest("dataset"),
            "entries": [
                {"domain": "python", "example_id": f"item-{index}", "split": "train"}
                for index in range(4)
            ],
        },
    )
    decision.save(bench / "decision.json")
    assert decision.disposition.value == "train"

    capability = CapabilityReport(
        disposition=RuntimeDisposition.READY,
        request_digest=_digest("runtime-request"),
        backend=TrainingBackend.CPU,
        backend_capability=CapabilityState.SUPPORTED,
        dtype_supported=True,
        four_bit_supported=False,
        packages=(("torch", "fixture"),),
        python_version="3.12.0",
        torch_backend_version="fixture",
        device=None,
        resources=ResourcePreflight(
            disk_free_bytes=10**9,
            ram_free_bytes=10**9,
            vram_free_bytes=None,
            vram_total_bytes=None,
        ),
        seed_applied=True,
        model_load=CapabilityState.SUPPORTED,
        blockers=(),
    )
    capability.save(evidence / "capability.json")

    train = data / "train.jsonl"
    validation = data / "validation.jsonl"
    train.write_text('{"prompt":"a","completion":"b"}\n', encoding="utf-8")
    validation.write_text('{"prompt":"c","completion":"d"}\n', encoding="utf-8")
    plan = TrainingPlan(
        mode=TrainingMode.SFT,
        authorization=TrainingAuthorization.TRAIN,
        capability_report_digest=capability.digest,
        model=ModelBinding(
            model_ref="base",
            model_revision="fixture-rev",
            model_digest=_digest("base-model"),
            tokenizer_ref="fixture-tokenizer",
            tokenizer_revision="fixture-tokenizer-rev",
            tokenizer_digest=_digest("tokenizer"),
            assistant_mask_capable=True,
        ),
        dataset=DatasetBinding(
            dataset_id="fixture-dataset",
            dataset_digest=_digest("dataset"),
            manifest_digest=_digest("manifest"),
            train_export_digest=hashlib.sha256(train.read_bytes()).hexdigest(),
            validation_export_digest=hashlib.sha256(validation.read_bytes()).hexdigest(),
            train_rows=1,
            validation_rows=1,
            train_path="data/train.jsonl",
            validation_path="data/validation.jsonl",
        ),
        sft=SFTTrainingConfig(max_steps=2, checkpoint_steps=1, eval_steps=1),
    )
    save_training_plan(plan, evidence / "training-plan.json")

    checkpoint = CheckpointRecord(
        checkpoint_id="checkpoint-00000001",
        plan_digest=plan.digest,
        step=1,
        artifact_path="tuning-runs/checkpoint-00000001/adapter.safetensors",
        artifact_digest=_digest("checkpoint"),
        train_loss=0.6,
        eval_loss=0.7,
    )
    run = TrainingReport(
        plan_digest=plan.digest,
        run_id=plan.run_id,
        state=TrainingRunState.COMPLETED,
        adapter_path="tuning-runs/adapter/adapter_model.safetensors",
        adapter_digest=_digest("adapter"),
        checkpoints=(checkpoint,),
        completed_steps=2,
        train_loss=0.4,
        eval_loss=0.5,
        train_rows=1,
        validation_rows=1,
        optimized_splits=("train",),
        framework_versions=(("python", "3.12"),),
        resource_maxima=(
            ("peak_ram_bytes", 1),
            ("peak_vram_bytes", None),
            ("wall_seconds", 1.0),
        ),
        resumed_from=None,
    )
    run.save(evidence / "training-run.json")
    return root, plan, run


def test_snapshot_binds_train_decision_capability_plan_run_and_checkpoint(tmp_path: Path) -> None:
    root, plan, run = _project(tmp_path)
    snapshot = ModelLabTrainingService(root).snapshot()

    assert snapshot["summary"] == {
        "plan_count": 1,
        "authorized_plans": 1,
        "capability_count": 1,
        "run_count": 1,
        "active_runs": 0,
    }
    item = snapshot["plans"][0]
    assert item["plan_digest"] == plan.digest
    assert item["authorized"] is True
    assert item["decision_digest"]
    assert item["capability_bound"] is True
    assert item["dataset_paths_bound"] is True
    assert item["model"]["model_digest"] == _digest("base-model")
    assert item["model"]["tokenizer_digest"] == _digest("tokenizer")

    run_item = snapshot["runs"][0]
    assert run_item["report_digest"] == run.digest
    assert run_item["plan_bound"] is True
    assert run_item["state"] == "completed"
    assert run_item["checkpoints"][0]["lineage_bound"] is True


def test_launch_blocks_without_persisted_evidence_bound_train_decision(tmp_path: Path) -> None:
    root, plan, _run = _project(tmp_path)
    (root / ".kodepoia" / "benchmarks" / "decision.json").unlink()
    service = ModelLabTrainingService(root)

    snapshot = service.snapshot()
    assert snapshot["plans"][0]["authorized"] is False
    assert "accepted_train_decision_missing" in snapshot["plans"][0]["blockers"]
    with pytest.raises(TrainingUXError, match="not launch-authorized"):
        service.preview_run(plan.digest, "local")


def test_typed_training_actions_preserve_backend_dry_run_confirmation_cancel_and_resume(
    tmp_path: Path,
) -> None:
    root, plan, run = _project(tmp_path)
    calls: list[R15WorkflowRequest] = []

    def handler(request: R15WorkflowRequest) -> dict[str, object]:
        calls.append(request)
        return {
            "status": "ok",
            "identifier": request.identifier,
            "backend": request.backend,
            "secret": "hidden",
        }

    service = ModelLabTrainingService(
        root,
        r15_service=R15UXService(
            root,
            handlers={
                "training.doctor": handler,
                "training.plan": handler,
                "training.run": handler,
                "training.status": handler,
                "training.cancel": handler,
                "training.resume": handler,
            },
        ),
    )

    doctor = service.inspect_doctor("kaggle")
    assert doctor["backend"] == "kaggle"
    assert calls[-1].key == "training.doctor"

    preview = service.preview_run(plan.digest, "local")
    assert preview["status"] == "dry_run"
    assert preview["backend"] == "local"
    assert [call.key for call in calls] == ["training.doctor"]

    with pytest.raises(R15UXPolicyError, match="confirmation"):
        service.run_training(plan.digest, "local", confirmed=False)

    applied = service.run_training(plan.digest, "local", confirmed=True)
    assert applied["workflow"] == "training.run"
    assert calls[-1].backend == "local"

    inspected = service.inspect_run(run.run_id, "local")
    assert inspected["workflow"] == "training.status"

    cancelled = service.cancel_run(run.run_id, "local", confirmed=True)
    assert cancelled["workflow"] == "training.cancel"
    assert calls[-1].mode.value == "cancel"

    resumed = service.resume_checkpoint("checkpoint-00000001", "kaggle", confirmed=True)
    assert resumed["workflow"] == "training.resume"
    assert calls[-1].identifier == "checkpoint-00000001"
    assert calls[-1].parent_identifier == plan.digest
    assert calls[-1].backend == "kaggle"
    assert resumed["secret"] == "<redacted>"


def test_backend_selection_is_bounded_and_later_mutations_remain_absent(tmp_path: Path) -> None:
    root, _plan, _run = _project(tmp_path)
    service = ModelLabTrainingService(root)

    with pytest.raises(TrainingUXError, match="local or kaggle"):
        service.inspect_doctor("shell:cuda")

    snapshot = service.snapshot()
    assert snapshot["later_mutations"] == {
        "conversion": False,
        "candidate_evaluation": False,
        "promotion": False,
        "rollback": False,
        "public_publish": False,
    }
    assert snapshot["reference_context"]["instruction_authority"] is False
    assert snapshot["reference_context"]["auto_training_ingest"] is False
    kaggle = next(item for item in snapshot["backends"] if item["id"] == "kaggle")
    assert kaggle["accelerator"] == "NvidiaTeslaT4"
    assert kaggle["gpu_count_claim"] is None
    assert kaggle["aggregate_vram_claim"] is None


def test_cross_project_r15_binding_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="project root"):
        ModelLabTrainingService(
            tmp_path / "a",
            r15_service=R15UXService(tmp_path / "b"),
        )
