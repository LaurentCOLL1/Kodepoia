from __future__ import annotations

import json
import struct
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from kodepoia.core.sandbox import SandboxResult
from kodepoia.tuning.contracts import QuantizationMode, ResourceRequest
from kodepoia.tuning.runtime import HostResources
from kodepoia.tuning.training import (
    DatasetBinding,
    LoraTrainingConfig,
    ModelBinding,
    SFTTrainingConfig,
    TrainingAuthorization,
    TrainingError,
    TrainingMode,
    TrainingPlan,
    TrainingRunner,
    TrainingRunState,
)

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64


def _model() -> ModelBinding:
    return ModelBinding(
        model_ref="fixture/base",
        model_revision="fixture-rev-1",
        model_digest=A,
        tokenizer_ref="fixture/tokenizer",
        tokenizer_revision="fixture-tokenizer-rev-1",
        tokenizer_digest=B,
        assistant_mask_capable=True,
    )


def _dataset() -> DatasetBinding:
    return DatasetBinding(
        dataset_id="fixture-dataset-v1",
        dataset_digest=C,
        manifest_digest=D,
        train_export_digest=A,
        validation_export_digest=B,
        train_rows=8,
        validation_rows=3,
    )


def _plan(**changes: object) -> TrainingPlan:
    values: dict[str, object] = {
        "mode": TrainingMode.FIXTURE_SFT,
        "authorization": TrainingAuthorization.FIXTURE,
        "fixture_authorization": "repository-owned-r15.9-fixture",
        "model": _model(),
        "dataset": _dataset(),
        "sft": SFTTrainingConfig(max_steps=4, checkpoint_steps=2, eval_steps=2),
    }
    values.update(changes)
    return TrainingPlan(**values)  # type: ignore[arg-type]


class FixedResources:
    def __init__(self, disk: int | None = 10**12, ram: int | None = 10**12) -> None:
        self.value = HostResources(disk, ram)

    def sample(self, _root: Path) -> HostResources:
        return self.value


class FakeSandbox:
    def __init__(self, result: SandboxResult) -> None:
        self.result = result
        self.calls: list[list[str]] = []

    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        self.calls.append(argv)
        return self.result


def _checkpoint_metadata(root: Path, plan: TrainingPlan, step: int = 2) -> str:
    return str(
        Path("tuning-runs") / plan.run_id / "checkpoints" / f"checkpoint-{step:08d}" / "checkpoint.json"
    )


def test_training_plan_digest_is_deterministic_and_lineage_bound() -> None:
    first = _plan()
    second = _plan()
    assert first.digest == second.digest
    assert first.run_id == second.run_id
    changed_base = replace(first, model=replace(first.model, model_digest=E))
    changed_tokenizer = replace(first, model=replace(first.model, tokenizer_digest=E))
    changed_dataset = replace(first, dataset=replace(first.dataset, dataset_digest=E))
    assert len({first.digest, changed_base.digest, changed_tokenizer.digest, changed_dataset.digest}) == 4


def test_real_training_requires_train_authorization_capability_and_explicit_dataset_paths() -> None:
    with pytest.raises(TrainingError, match="TRAIN authorization"):
        _plan(mode=TrainingMode.SFT)
    with pytest.raises(TrainingError, match="capability report"):
        TrainingPlan(
            mode=TrainingMode.SFT,
            authorization=TrainingAuthorization.TRAIN,
            model=_model(),
            dataset=replace(
                _dataset(), train_path="data/train.jsonl", validation_path="data/validation.jsonl"
            ),
        )


def test_qlora_requires_nf4_and_all_linear_is_explicit_policy() -> None:
    dataset = replace(_dataset(), train_path="data/train.jsonl", validation_path="data/validation.jsonl")
    with pytest.raises(TrainingError, match="requires capability-probed NF4"):
        TrainingPlan(
            mode=TrainingMode.QLORA,
            authorization=TrainingAuthorization.TRAIN,
            capability_report_digest=E,
            model=_model(),
            dataset=dataset,
            quantization=QuantizationMode.NONE,
        )
    plan = TrainingPlan(
        mode=TrainingMode.QLORA,
        authorization=TrainingAuthorization.TRAIN,
        capability_report_digest=E,
        model=_model(),
        dataset=dataset,
        quantization=QuantizationMode.BNB_NF4,
        lora=LoraTrainingConfig(target_modules=("all-linear",)),
    )
    assert plan.lora.target_modules == ("all-linear",)


def test_train_and_validation_must_be_distinct() -> None:
    with pytest.raises(TrainingError, match="exports must be distinct"):
        replace(_dataset(), validation_export_digest=A)
    with pytest.raises(TrainingError, match="paths must be distinct"):
        replace(_dataset(), train_path="data/same.jsonl", validation_path="data/same.jsonl")


def test_loss_modes_fail_closed_without_compatible_dataset_or_template_capability() -> None:
    base = _plan()
    with pytest.raises(TrainingError, match="conversational dataset"):
        replace(base, sft=replace(base.sft, assistant_only_loss=True))
    conversational = replace(base.dataset, format="conversational")
    incapable = replace(base.model, assistant_mask_capable=False)
    with pytest.raises(TrainingError, match="generation-mask capability"):
        replace(
            base,
            model=incapable,
            dataset=conversational,
            sft=replace(base.sft, assistant_only_loss=True, completion_only_loss=False),
        )
    with pytest.raises(TrainingError, match="prompt_completion"):
        replace(base, dataset=replace(base.dataset, format="text"))


def test_fixture_training_produces_valid_deterministic_safetensors_and_train_only_optimization(
    tmp_path: Path,
) -> None:
    plan = _plan()
    runner = TrainingRunner(tmp_path, resource_probe=FixedResources())
    first = runner.run(plan)
    second = runner.run(plan)
    assert first.state is TrainingRunState.COMPLETED
    assert first.adapter_digest == second.adapter_digest
    assert first.optimized_splits == ("train",)
    assert first.train_rows == 8
    assert first.validation_rows == 3
    assert first.completed_steps == 4
    assert [item.step for item in first.checkpoints] == [2, 4]
    assert first.adapter_path is not None
    adapter = tmp_path / first.adapter_path
    raw = adapter.read_bytes()
    header_len = struct.unpack("<Q", raw[:8])[0]
    header = json.loads(raw[8 : 8 + header_len].decode("utf-8").rstrip(" "))
    assert header["__metadata__"]["format"] == "kodepoia-r15.9-fixture"
    assert set(header) == {"__metadata__", "fixture.lora_A.weight", "fixture.lora_B.weight"}


def test_resume_from_same_plan_checkpoint_is_reproducible(tmp_path: Path) -> None:
    plan = _plan()
    runner = TrainingRunner(tmp_path, resource_probe=FixedResources())
    first = runner.run(plan)
    resumed = runner.run(plan, resume_checkpoint=_checkpoint_metadata(tmp_path, plan, 2))
    assert first.state is TrainingRunState.COMPLETED
    assert resumed.state is TrainingRunState.COMPLETED
    assert resumed.resumed_from == "checkpoint-00000002"
    assert resumed.adapter_digest == first.adapter_digest


def test_resume_rejects_changed_base_tokenizer_or_dataset(tmp_path: Path) -> None:
    plan = _plan()
    runner = TrainingRunner(tmp_path, resource_probe=FixedResources())
    assert runner.run(plan).state is TrainingRunState.COMPLETED
    checkpoint = _checkpoint_metadata(tmp_path, plan, 2)
    for changed in (
        replace(plan, model=replace(plan.model, model_digest=E)),
        replace(plan, model=replace(plan.model, tokenizer_digest=E)),
        replace(plan, dataset=replace(plan.dataset, dataset_digest=E)),
    ):
        with pytest.raises(TrainingError, match="lineage"):
            runner.run(changed, resume_checkpoint=checkpoint)


def test_budget_unknown_blocks_before_subprocess() -> None:
    sandbox = FakeSandbox(SandboxResult(0, "{}", ""))
    plan = _plan(resources=ResourceRequest(disk_required_bytes=1, ram_required_bytes=1))
    runner = TrainingRunner(Path.cwd(), sandbox=sandbox, resource_probe=FixedResources(None, None))
    report = runner.run(plan)
    assert report.state is TrainingRunState.BUDGET_BLOCKED
    assert set(report.blockers) == {"ram_budget_unknown", "storage_budget_unknown"}
    assert sandbox.calls == []


def test_timeout_and_cancel_are_terminal_without_adapter(tmp_path: Path) -> None:
    timeout = FakeSandbox(SandboxResult(-1, "", "late", timed_out=True))
    report = TrainingRunner(tmp_path, sandbox=timeout, resource_probe=FixedResources()).run(_plan())
    assert report.state is TrainingRunState.TIMED_OUT
    assert report.adapter_digest is None

    cancelled = FakeSandbox(SandboxResult(-1, "", "cancelled", cancelled=True))
    report = TrainingRunner(tmp_path, sandbox=cancelled, resource_probe=FixedResources()).run(_plan())
    assert report.state is TrainingRunState.CANCELLED
    assert report.adapter_digest is None


def test_worker_argv_never_contains_model_tokenizer_or_dataset_identifiers(tmp_path: Path) -> None:
    sandbox = FakeSandbox(SandboxResult(-1, "", "cancelled", cancelled=True))
    plan = _plan()
    runner = TrainingRunner(tmp_path, sandbox=sandbox, resource_probe=FixedResources())
    runner.run(plan)
    argv = " ".join(sandbox.calls[0])
    assert plan.model.model_ref not in argv
    assert plan.model.tokenizer_ref not in argv
    assert plan.dataset.dataset_id not in argv
    assert argv.startswith(sys.executable)


def test_sft_loss_mode_and_seed_configuration_are_digest_bound() -> None:
    base = _plan()
    conversational = replace(base.dataset, format="conversational")
    assistant = replace(
        base,
        dataset=conversational,
        sft=replace(base.sft, assistant_only_loss=True, completion_only_loss=False),
    )
    full_sequence = replace(base, sft=replace(base.sft, completion_only_loss=False))
    different_data_seed = replace(base, seeds=replace(base.seeds, data_seed=99))
    assert len({base.digest, assistant.digest, full_sequence.digest, different_data_seed.digest}) == 4


def test_importing_public_tuning_surface_does_not_import_heavy_ml_packages() -> None:
    import kodepoia.tuning  # noqa: F401

    assert "torch" not in sys.modules
    assert "transformers" not in sys.modules
    assert "peft" not in sys.modules
    assert "trl" not in sys.modules
    assert "bitsandbytes" not in sys.modules
