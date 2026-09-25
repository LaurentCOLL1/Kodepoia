from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from kodepoia.tuning import kaggle_live_pair as live_pair
from kodepoia.tuning.kaggle_live_pair import (
    KaggleLivePairBundle,
    KaggleLivePairClient,
    KaggleLivePairError,
    KaggleLivePairRequest,
)
from kodepoia.tuning.kaggle_remote import CommandResult

SOURCE_SHA = "a" * 40
A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64
F = "f" * 64


def _request() -> KaggleLivePairRequest:
    files = (
        ("config.json", A),
        ("model.safetensors", live_pair._MODEL_FILE_SHA256),
        ("special_tokens_map.json", B),
        ("tokenizer.json", C),
        ("tokenizer.model", D),
        ("tokenizer_config.json", E),
    )
    return KaggleLivePairRequest(
        source_sha=SOURCE_SHA,
        kaggle_dataset_id="fixture/kodepoia-v245-live-pair-data",
        kernel_id="fixture/kodepoia-v245-live-pair",
        training_plan_digest=A,
        capability_report_digest=B,
        gap_decision_digest=C,
        bootstrap_result_digest=D,
        bootstrap_evidence_sha256=E,
        topology_report_digest=F,
        topology_digest=A,
        single_strategy_plan_digest=B,
        replicated_strategy_plan_digest=C,
        qualification_permit_digest=D,
        qualification_execution_plan_digest=E,
        benchmark_config_digest=F,
        processed_samples=16,
        effective_global_batch_size=2,
        wheel_filename="kodepoia-1.1.0rc8-py3-none-any.whl",
        wheel_sha256=A,
        model_ref=live_pair._MODEL_REF,
        model_revision=live_pair._MODEL_REVISION,
        model_digest=B,
        tokenizer_digest=C,
        dataset_digest=D,
        dataset_manifest_digest=E,
        train_export_digest=F,
        validation_export_digest=A,
        protection_manifest_digest=B,
        model_snapshot_files=files,
    )


class _Runner:
    def __init__(self, output_payload: dict[str, object] | None = None) -> None:
        self.calls: list[list[str]] = []
        self.output_payload = output_payload

    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 120.0,
    ) -> CommandResult:
        del cwd, timeout
        self.calls.append(list(argv))
        if self.output_payload is not None and "output" in argv:
            output = Path(argv[argv.index("--path") + 1])
            output.mkdir(parents=True, exist_ok=True)
            (output / "live-pair-result.json").write_text(
                json.dumps(self.output_payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return CommandResult(0, "ok", "")


def _bundle(tmp_path: Path, request: KaggleLivePairRequest) -> KaggleLivePairBundle:
    root = tmp_path / "pair"
    dataset = root / "dataset"
    kernel = root / "kernel"
    output = root / "output"
    dataset.mkdir(parents=True)
    kernel.mkdir()
    output.mkdir()

    script = kernel / "run_live_pair.py"
    script.write_text("print('pair')\n", encoding="utf-8")
    script_sha = hashlib.sha256(script.read_bytes()).hexdigest()
    (kernel / "kernel-metadata.json").write_text(
        json.dumps(
            {
                "code_file": script.name,
                "id": request.kernel_id,
                "is_private": True,
            }
        ),
        encoding="utf-8",
    )
    (kernel / "kernel-manifest.json").write_text(
        json.dumps(
            {
                "pair_request_digest": request.digest,
                "schema": "kodepoia.v2.4.5.live-pair-kernel-bundle",
                "schema_version": 1,
                "script_sha256": script_sha,
                "source_sha": request.source_sha,
            }
        ),
        encoding="utf-8",
    )
    return KaggleLivePairBundle(
        root=root,
        dataset_dir=dataset,
        kernel_dir=kernel,
        output_dir=output,
        request=request,
    )


def test_live_pair_request_is_exact_source_and_digest_bound() -> None:
    request = _request()
    restored = KaggleLivePairRequest.from_dict(request.to_dict())

    assert request.source_sha == SOURCE_SHA
    assert restored == request
    assert restored.digest == request.digest
    assert restored.processed_samples == 16
    assert restored.effective_global_batch_size == 2
    assert dict(restored.model_snapshot_files)["model.safetensors"] == (
        live_pair._MODEL_FILE_SHA256
    )


def test_live_pair_request_rejects_unpinned_source_or_model() -> None:
    request = _request()

    with pytest.raises(KaggleLivePairError, match="source_sha"):
        live_pair.KaggleLivePairRequest(
            **{
                **request.descriptor(),
                "source_sha": "b" * 64,
                "model_snapshot_files": request.model_snapshot_files,
            }
        )

    bad_files = tuple(
        (name, "0" * 64 if name == "model.safetensors" else digest)
        for name, digest in request.model_snapshot_files
    )
    with pytest.raises(KaggleLivePairError, match="pinned V2.4.5"):
        live_pair.KaggleLivePairRequest(
            **{
                **request.descriptor(),
                "model_snapshot_files": bad_files,
            }
        )


def test_repository_owned_live_pair_kernel_uses_existing_runners_and_real_gates() -> None:
    request = _request()
    script = live_pair._kernel_script(
        request.wheel_filename,
        request.wheel_sha256,
        request.source_sha,
        request.digest,
    )
    compile(script, "run_live_pair.py", "exec")
    module_source = Path(live_pair.__file__).read_text(encoding="utf-8")

    assert "run_live_pair_kernel" in script
    assert '[sys.executable, "-m", "pip", "install"' in script
    assert "HF_TOKEN" not in script
    assert "kaggle_secrets" not in script
    assert "--public" not in script

    for required in (
        "TrainingRunner(",
        ".run_qualification_only(",
        "evaluate_strategy_benchmark(",
        "StrategyBenchmarkDisposition.QUALIFIED",
        "build_distributed_execution_plan(",
        "build_distributed_checkpoint_manifest(",
        "build_distributed_recovery_plan(",
        "BaseAdapterEvaluator().evaluate(",
        'snapshot_download(',
        'token=False',
        'local_files_only=True',
    ):
        assert required in module_source

    assert '"CUDA_VISIBLE_DEVICES"] = self.visible_devices' in module_source
    assert '"0,1"' in module_source
    assert "FSDP" not in module_source
    assert "DeepSpeed" not in module_source
    assert "ZeRO" not in module_source
    assert "tensor parallel" not in module_source.lower()
    assert "pipeline parallel" not in module_source.lower()


def test_live_pair_client_uses_private_one_shot_kaggle_argv(tmp_path: Path) -> None:
    request = _request()
    bundle = _bundle(tmp_path, request)
    runner = _Runner()
    client = KaggleLivePairClient(runner=runner, kaggle_executable="kaggle")

    client.upload_private_dataset(bundle)
    client.dataset_status(bundle)
    client.push(bundle)
    client.status(bundle)

    assert runner.calls[0][:3] == ["kaggle", "datasets", "create"]
    assert "--public" not in runner.calls[0]
    assert runner.calls[1] == [
        "kaggle",
        "datasets",
        "status",
        request.kaggle_dataset_id,
        "--format",
        "json",
    ]
    assert runner.calls[2][:3] == ["kaggle", "kernels", "push"]
    assert runner.calls[3] == ["kaggle", "kernels", "status", request.kernel_id]


def test_live_pair_download_preserves_honest_benchmark_rejection(tmp_path: Path) -> None:
    request = _request()
    bundle = _bundle(tmp_path, request)
    payload = {
        "benchmark_report": {
            "blockers": ["throughput_gain_below_threshold"],
            "disposition": "rejected",
        },
        "kernel_id": request.kernel_id,
        "pair_request_digest": request.digest,
        "schema": live_pair.LIVE_PAIR_RESULT_SCHEMA,
        "schema_version": 1,
        "source_sha": request.source_sha,
        "status": "benchmark_rejected",
    }
    runner = _Runner(payload)
    client = KaggleLivePairClient(runner=runner, kaggle_executable="kaggle")

    result = client.fetch_and_validate(bundle)

    assert result["production_qualified"] is False
    assert result["result"]["status"] == "benchmark_rejected"
    assert runner.calls[-1][:3] == ["kaggle", "kernels", "output"]
    assert "--quiet" in runner.calls[-1]
