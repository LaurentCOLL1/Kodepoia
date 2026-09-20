from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from kodepoia.tuning.contracts import QuantizationMode, TrainingBackend
from kodepoia.tuning.kaggle_remote import (
    CommandResult,
    KaggleAccelerator,
    KaggleRemoteConfig,
    KaggleRemoteError,
    KaggleRemoteTrainer,
    load_training_plan,
    save_training_plan,
)
from kodepoia.tuning.training import (
    DatasetBinding,
    ModelBinding,
    SFTTrainingConfig,
    TrainingAuthorization,
    TrainingMode,
    TrainingPlan,
)

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _plan(root: Path) -> TrainingPlan:
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
            train_rows=1,
            validation_rows=1,
            train_path="data/train.jsonl",
            validation_path="data/validation.jsonl",
        ),
        quantization=QuantizationMode.BNB_NF4,
        sft=SFTTrainingConfig(max_steps=2, checkpoint_steps=1, eval_steps=1),
    )


class FakeRunner:
    def __init__(self, results: list[CommandResult] | None = None) -> None:
        self.results = list(results or [])
        self.calls: list[list[str]] = []

    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 120.0,
    ) -> CommandResult:
        del cwd, timeout
        self.calls.append(argv)
        return self.results.pop(0) if self.results else CommandResult(0, "ok", "")


def _bundle(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    plan = _plan(project)
    wheel = tmp_path / "kodepoia.whl"
    wheel.write_bytes(b"wheel-fixture")
    trainer = KaggleRemoteTrainer(runner=FakeRunner(), kaggle_executable="kaggle")
    bundle = trainer.prepare_bundle(
        project_root=project,
        plan=plan,
        wheel_path=wheel,
        config=KaggleRemoteConfig(
            username="kodepoiaTester",
            dataset_slug="kodepoia-train-data",
            kernel_slug="kodepoia-train-run",
        ),
        output_root=tmp_path / "bundles",
    )
    return trainer, plan, bundle


def test_bundle_is_private_gpu_t4_and_contains_no_credentials(tmp_path: Path) -> None:
    _trainer, plan, bundle = _bundle(tmp_path)
    kernel = json.loads((bundle.kernel_dir / "kernel-metadata.json").read_text(encoding="utf-8"))
    dataset = json.loads((bundle.dataset_dir / "dataset-metadata.json").read_text(encoding="utf-8"))
    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    saved_plan = json.loads((bundle.root / "training-plan.json").read_text(encoding="utf-8"))

    assert kernel["is_private"] is True
    assert kernel["enable_gpu"] is True
    assert kernel["machine_shape"] == KaggleAccelerator.NVIDIA_T4.value
    assert kernel["dataset_sources"] == [bundle.config.dataset_id]
    assert dataset["id"] == bundle.config.dataset_id
    assert manifest["plan_digest"] == plan.digest
    assert load_training_plan(bundle.root / "training-plan.json").digest == plan.digest

    serialized = json.dumps([kernel, dataset, manifest, saved_plan]).lower()
    for forbidden in ("kaggle_api_token", "kaggle_key", "password", "access_token", "refresh_token"):
        assert forbidden not in serialized


def test_t4_provider_topology_request_is_explicit_and_not_observed_truth() -> None:
    config = KaggleRemoteConfig(
        username="kodepoiaTester",
        dataset_slug="private-data",
        kernel_slug="private-run",
    )
    request = config.topology_request()
    assert request.provider == "kaggle"
    assert request.shape == KaggleAccelerator.NVIDIA_T4.value
    assert request.expected_backend is TrainingBackend.CUDA
    assert request.expected_device_count == 2
    assert request.expected_name_contains == "T4"
    assert "observed" not in request.to_dict()


def test_l4_is_supported_but_retired_p100_is_not() -> None:
    config = KaggleRemoteConfig(
        username="kodepoiaTester",
        dataset_slug="private-data",
        kernel_slug="private-run",
        accelerator=KaggleAccelerator.NVIDIA_L4,
    )
    assert config.accelerator is KaggleAccelerator.NVIDIA_L4
    with pytest.raises(ValueError):
        KaggleAccelerator("NvidiaTeslaP100")


def test_dataset_upload_never_requests_public_visibility(tmp_path: Path) -> None:
    trainer, _plan_value, bundle = _bundle(tmp_path)
    trainer.upload_private_dataset(bundle)
    argv = trainer.runner.calls[-1]  # type: ignore[attr-defined]
    assert argv[:3] == ["kaggle", "datasets", "create"]
    assert "--public" not in argv
    assert "-u" not in argv
    assert "--dir-mode" in argv
    assert "zip" in argv


def test_kernel_push_status_and_output_use_owned_private_kernel(tmp_path: Path) -> None:
    trainer, plan, bundle = _bundle(tmp_path)
    trainer.push_kernel(bundle)
    trainer.kernel_status(bundle)
    calls = trainer.runner.calls  # type: ignore[attr-defined]
    assert calls[-2][:3] == ["kaggle", "kernels", "push"]
    assert calls[-1] == ["kaggle", "kernels", "status", bundle.config.kernel_id]

    output_root = bundle.output_dir
    adapter = output_root / "tuning-runs" / plan.run_id / "adapter" / "adapter_model.safetensors"
    adapter.parent.mkdir(parents=True, exist_ok=True)
    adapter.write_bytes(b"adapter")
    worker_output = {
        "adapter_digest": _sha256(adapter),
        "adapter_path": adapter.relative_to(output_root).as_posix(),
        "checkpoints": [],
        "completed_steps": plan.sft.max_steps,
        "eval_loss": 0.4,
        "framework_versions": {"python": "3.12"},
        "optimized_splits": ["train"],
        "plan_digest": plan.digest,
        "resource_maxima": {
            "peak_ram_bytes": 1,
            "peak_vram_bytes": 1,
            "wall_seconds": 1.0,
        },
        "train_loss": 0.3,
        "train_rows": plan.dataset.train_rows,
        "validation_rows": plan.dataset.validation_rows,
    }
    (output_root / "worker-output.json").write_text(
        json.dumps(worker_output),
        encoding="utf-8",
    )
    report = trainer.fetch_output(bundle, plan)
    assert report.plan_digest == plan.digest
    assert report.adapter_digest == _sha256(adapter)
    assert trainer.runner.calls[-1][:3] == ["kaggle", "kernels", "output"]  # type: ignore[attr-defined]


def test_tampered_adapter_is_rejected_after_download(tmp_path: Path) -> None:
    trainer, plan, bundle = _bundle(tmp_path)
    adapter = bundle.output_dir / "tuning-runs" / plan.run_id / "adapter" / "adapter_model.safetensors"
    adapter.parent.mkdir(parents=True, exist_ok=True)
    adapter.write_bytes(b"tampered")
    output = {
        "adapter_digest": "0" * 64,
        "adapter_path": adapter.relative_to(bundle.output_dir).as_posix(),
        "checkpoints": [],
        "completed_steps": plan.sft.max_steps,
        "eval_loss": 0.4,
        "framework_versions": {"python": "3.12"},
        "optimized_splits": ["train"],
        "plan_digest": plan.digest,
        "resource_maxima": {
            "peak_ram_bytes": 1,
            "peak_vram_bytes": 1,
            "wall_seconds": 1.0,
        },
        "train_loss": 0.3,
        "train_rows": plan.dataset.train_rows,
        "validation_rows": plan.dataset.validation_rows,
    }
    (bundle.output_dir / "worker-output.json").write_text(json.dumps(output), encoding="utf-8")
    with pytest.raises(KaggleRemoteError, match="digest mismatch"):
        trainer.fetch_output(bundle, plan)


def test_training_plan_round_trip_preserves_digest(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    plan = _plan(project)
    path = tmp_path / "plan.json"
    save_training_plan(plan, path)
    restored = load_training_plan(path)
    assert restored.digest == plan.digest
