from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import pytest

from kodepoia.core.kill_switch import KillSwitch
from kodepoia.core.sandbox import SandboxResult
from kodepoia.tuning.runtime import HostResources
from kodepoia.tuning.training import TrainingOrchestrator
from kodepoia.tuning.training_contracts import (
    DatasetFormat,
    LoraPlan,
    SFTPlan,
    TrainingBudget,
    TrainingEngine,
    TrainingPlan,
    TrainingPlanError,
    TrainingRunState,
)


class FixedResources:
    def __init__(self, disk: int | None = 10 << 30, ram: int | None = 16 << 30) -> None:
        self.value = HostResources(disk, ram)

    def sample(self, _root: Path) -> HostResources:
        return self.value


class TerminalSandbox:
    def __init__(self, *, timed_out: bool = False, cancelled: bool = False) -> None:
        self.timed_out = timed_out
        self.cancelled = cancelled
        self.calls = 0
        self.argv: list[str] = []

    def run(self, argv: list[str], **_kwargs: object) -> SandboxResult:
        self.calls += 1
        self.argv = list(argv)
        return SandboxResult(0, "{}", "", timed_out=self.timed_out, cancelled=self.cancelled)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_split(path: Path, rows: list[dict[str, object]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return _sha(path)


def make_plan(
    root: Path,
    *,
    train_rows: list[dict[str, object]] | None = None,
    validation_rows: list[dict[str, object]] | None = None,
    dataset_format: DatasetFormat = DatasetFormat.PROMPT_COMPLETION,
    sft: SFTPlan | None = None,
) -> TrainingPlan:
    train_rows = train_rows or [{"prompt": "2+2?", "completion": "4"}, {"prompt": "3+3?", "completion": "6"}]
    train_path = root / "dataset/train.jsonl"
    train_digest = _write_split(train_path, train_rows)
    validation_path = None
    validation_digest = None
    if validation_rows is not None:
        validation_path = root / "dataset/validation.jsonl"
        validation_digest = _write_split(validation_path, validation_rows)
    return TrainingPlan(
        source_sha="1" * 64,
        base_model_ref="fixture/base",
        base_revision="immutable-rev",
        base_model_digest="2" * 64,
        tokenizer_ref="fixture/tokenizer",
        tokenizer_digest="3" * 64,
        dataset_manifest_digest="4" * 64,
        train_split_digest=train_digest,
        train_path="dataset/train.jsonl",
        validation_split_digest=validation_digest,
        validation_path=None if validation_path is None else "dataset/validation.jsonl",
        dataset_format=dataset_format,
        engine=TrainingEngine.FIXTURE,
        lora=LoraPlan(rank=4, alpha=8, dropout=0.0, target_modules="all-linear"),
        sft=sft or SFTPlan(max_steps=4, checkpoint_every_steps=2, context_length=64),
        budget=TrainingBudget(disk_limit_bytes=1, ram_limit_bytes=1, timeout_seconds=30),
    )


def _assert_safetensors(path: Path) -> None:
    raw = path.read_bytes()
    header_len = struct.unpack("<Q", raw[:8])[0]
    header = json.loads(raw[8 : 8 + header_len].decode("utf-8").rstrip())
    assert header["__metadata__"]["fixture"] == "r15.9"
    assert set(header) >= {"lora_A.weight", "lora_B.weight"}
    assert len(raw) == 8 + header_len + 16


def test_fixture_training_produces_deterministic_adapter_and_checkpoints(tmp_path: Path) -> None:
    plan = make_plan(tmp_path, validation_rows=[{"prompt": "5+5?", "completion": "10"}])
    orchestrator = TrainingOrchestrator(tmp_path, kill_switch=KillSwitch(), resource_probe=FixedResources())
    first = orchestrator.run(plan)
    second = orchestrator.run(plan)
    assert first.state is TrainingRunState.SUCCEEDED
    assert second.state is TrainingRunState.SUCCEEDED
    assert first.adapter_digest == second.adapter_digest
    assert first.train_loss == second.train_loss
    assert first.eval_loss == second.eval_loss
    assert first.steps_completed == 4
    assert first.checkpoint is not None and first.checkpoint.step == 4
    _assert_safetensors(tmp_path / str(first.adapter_path))
    assert (tmp_path / f"runs/{first.run_id}/checkpoint-2/kodepoia_checkpoint.json").is_file()


def test_resume_from_compatible_checkpoint_preserves_lineage(tmp_path: Path) -> None:
    plan = make_plan(tmp_path)
    orchestrator = TrainingOrchestrator(tmp_path, kill_switch=KillSwitch(), resource_probe=FixedResources())
    first = orchestrator.run(plan)
    checkpoint = f"runs/{first.run_id}/checkpoint-2"
    resumed = orchestrator.run(plan, resume_checkpoint=checkpoint)
    assert resumed.state is TrainingRunState.SUCCEEDED
    assert resumed.adapter_digest == first.adapter_digest
    assert resumed.checkpoint is not None and resumed.checkpoint.step == 4


def test_resume_rejects_mismatched_plan_before_worker(tmp_path: Path) -> None:
    plan = make_plan(tmp_path)
    orchestrator = TrainingOrchestrator(tmp_path, kill_switch=KillSwitch(), resource_probe=FixedResources())
    first = orchestrator.run(plan)
    checkpoint_dir = tmp_path / f"runs/{first.run_id}/checkpoint-2"
    metadata_path = checkpoint_dir / "kodepoia_checkpoint.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["base_model_digest"] = "9" * 64
    metadata_path.write_text(json.dumps(metadata, sort_keys=True), encoding="utf-8")
    blocked = orchestrator.run(plan, resume_checkpoint=checkpoint_dir.relative_to(tmp_path).as_posix())
    assert blocked.state is TrainingRunState.FAILED
    assert "resume_lineage_mismatch" in blocked.blockers


def test_validation_split_is_evaluation_only_for_fixture_adapter(tmp_path: Path) -> None:
    plan_a = make_plan(tmp_path, validation_rows=[{"prompt": "A", "completion": "one"}])
    first = TrainingOrchestrator(tmp_path, kill_switch=KillSwitch(), resource_probe=FixedResources()).run(plan_a)
    plan_b = make_plan(tmp_path, validation_rows=[{"prompt": "B", "completion": "two"}])
    second = TrainingOrchestrator(tmp_path, kill_switch=KillSwitch(), resource_probe=FixedResources()).run(plan_b)
    assert first.state is TrainingRunState.SUCCEEDED
    assert second.state is TrainingRunState.SUCCEEDED
    assert first.adapter_digest == second.adapter_digest
    assert first.train_loss == second.train_loss
    assert first.eval_loss != second.eval_loss


def test_dataset_digest_mismatch_fails_before_worker(tmp_path: Path) -> None:
    plan = make_plan(tmp_path)
    sandbox = TerminalSandbox()
    (tmp_path / plan.train_path).write_text('{"prompt":"changed","completion":"x"}\n', encoding="utf-8")
    report = TrainingOrchestrator(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=sandbox,
        resource_probe=FixedResources(),
    ).run(plan)
    assert report.state is TrainingRunState.FAILED
    assert report.blockers == ("train_split_digest_mismatch",)
    assert sandbox.calls == 0


def test_budget_unknown_and_exceeded_fail_without_worker(tmp_path: Path) -> None:
    plan = make_plan(tmp_path)
    sandbox = TerminalSandbox()
    unknown = TrainingOrchestrator(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=sandbox,
        resource_probe=FixedResources(None, None),
    ).run(plan)
    assert unknown.state is TrainingRunState.BUDGET_BLOCKED
    assert set(unknown.blockers) == {"ram_budget_unknown", "storage_budget_unknown"}
    assert sandbox.calls == 0

    exceeded = TrainingOrchestrator(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=sandbox,
        resource_probe=FixedResources(0, 0),
    ).run(plan)
    assert exceeded.state is TrainingRunState.BUDGET_BLOCKED
    assert set(exceeded.blockers) == {"ram_budget_exceeded", "storage_budget_exceeded"}
    assert sandbox.calls == 0


def test_timeout_and_cancel_are_terminal_and_argv_is_structured(tmp_path: Path) -> None:
    plan = make_plan(tmp_path)
    timeout = TerminalSandbox(timed_out=True)
    report = TrainingOrchestrator(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=timeout,
        resource_probe=FixedResources(),
    ).run(plan)
    assert report.state is TrainingRunState.TIMED_OUT
    joined = " ".join(timeout.argv)
    assert "fixture/base" not in joined
    assert "fixture/tokenizer" not in joined
    assert "dataset/train.jsonl" not in joined

    cancelled = TerminalSandbox(cancelled=True)
    report = TrainingOrchestrator(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=cancelled,
        resource_probe=FixedResources(),
    ).run(plan)
    assert report.state is TrainingRunState.CANCELLED


def test_training_plan_rejects_validation_as_training_and_bad_loss_modes(tmp_path: Path) -> None:
    train = tmp_path / "same.jsonl"
    digest = _write_split(train, [{"prompt": "a", "completion": "b"}])
    with pytest.raises(TrainingPlanError):
        TrainingPlan(
            source_sha="1" * 64,
            base_model_ref="fixture/base",
            base_revision="rev",
            base_model_digest="2" * 64,
            tokenizer_ref="fixture/tokenizer",
            tokenizer_digest="3" * 64,
            dataset_manifest_digest="4" * 64,
            train_split_digest=digest,
            train_path="same.jsonl",
            validation_split_digest=digest,
            validation_path="same.jsonl",
        )
    with pytest.raises(TrainingPlanError):
        make_plan(tmp_path, dataset_format=DatasetFormat.TEXT, sft=SFTPlan(assistant_only_loss=True))
    with pytest.raises(TrainingPlanError):
        make_plan(tmp_path, dataset_format=DatasetFormat.CONVERSATIONAL, sft=SFTPlan(completion_only_loss=True))


def test_real_training_engine_requires_r15_8_capability(tmp_path: Path) -> None:
    train_digest = _write_split(tmp_path / "dataset/train.jsonl", [{"prompt": "a", "completion": "b"}])
    plan = TrainingPlan(
        source_sha="1" * 64,
        base_model_ref="fixture/base",
        base_revision="rev",
        base_model_digest="2" * 64,
        tokenizer_ref="fixture/tokenizer",
        tokenizer_digest="3" * 64,
        dataset_manifest_digest="4" * 64,
        train_split_digest=train_digest,
        train_path="dataset/train.jsonl",
        engine=TrainingEngine.TRL_PEFT,
        budget=TrainingBudget(disk_limit_bytes=1, ram_limit_bytes=1),
    )
    sandbox = TerminalSandbox()
    report = TrainingOrchestrator(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=sandbox,
        resource_probe=FixedResources(),
    ).run(plan)
    assert report.state is TrainingRunState.UNSUPPORTED
    assert report.blockers == ("r15_8_capability_required",)
    assert sandbox.calls == 0
