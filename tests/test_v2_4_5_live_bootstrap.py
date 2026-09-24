from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from kodepoia.bench import DecisionDisposition
from kodepoia.tuning.contracts import canonical_sha256
from kodepoia.tuning.kaggle_live_bootstrap import (
    BOOTSTRAP_EVIDENCE_SCHEMA,
    QUALIFICATION_MODEL_FILE_SHA256,
    QUALIFICATION_MODEL_LICENSE,
    QUALIFICATION_MODEL_REF,
    QUALIFICATION_MODEL_REQUIRED_FILES,
    QUALIFICATION_MODEL_REVISION,
    QUALIFICATION_RUNTIME_MODEL_RELATIVE,
    QUALIFICATION_TRAINING_DATA_RELATIVE,
    KaggleLiveBootstrapClient,
    KaggleLiveBootstrapError,
    build_live_bootstrap_bundle,
    build_live_qualification_dataset,
    finalize_live_bootstrap,
    stage_runtime_model_snapshot,
    stage_training_exports,
)
from kodepoia.tuning.kaggle_remote import CommandResult, SubprocessCommandRunner

SOURCE_SHA = "a" * 40
DATASET_ID = "fixture/kodepoia-v245-bootstrap-data"
KERNEL_ID = "fixture/kodepoia-v245-bootstrap-kernel"


def _repository(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    workload = root / "qualification" / "v2_4_5" / "live_workload.json"
    workload.parent.mkdir(parents=True)
    source = Path(__file__).resolve().parents[1] / "qualification" / "v2_4_5" / "live_workload.json"
    shutil.copy2(source, workload)
    return root


def _model_snapshot(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    hashes: dict[str, str] = {}
    for name in QUALIFICATION_MODEL_REQUIRED_FILES:
        payload = f"fixture:{name}".encode()
        path = snapshot / name
        path.write_bytes(payload)
        hashes[name] = hashlib.sha256(payload).hexdigest()
    return snapshot, hashes


def _bundle(tmp_path: Path):
    root = _repository(tmp_path)
    wheel = root / "dist" / "kodepoia-1.1.0rc8-py3-none-any.whl"
    wheel.parent.mkdir(parents=True)
    wheel.write_bytes(b"deterministic-test-wheel")
    bundle = build_live_bootstrap_bundle(
        repository_root=root,
        source_sha=SOURCE_SHA,
        kaggle_dataset_id=DATASET_ID,
        kernel_id=KERNEL_ID,
        wheel_path=wheel,
        output_root=root / ".kodepoia" / "live" / "bootstrap",
    )
    return root, bundle


def _report(payload: dict[str, object]) -> dict[str, object]:
    return {**payload, "report_digest": canonical_sha256(payload)}


def _evidence(bundle) -> dict[str, object]:
    request = bundle.request
    return {
        "benchmark": _report({"outcomes": [], "schema": "fixture-benchmark"}),
        "capability": _report({"schema": "fixture-capability"}),
        "dataset_digest": request.dataset_digest,
        "dataset_manifest_digest": request.dataset_manifest_digest,
        "dedup_policy_digest": request.dedup_policy_digest,
        "expected_device_count": 2,
        "kaggle_dataset_id": request.kaggle_dataset_id,
        "kernel_id": request.kernel_id,
        "model": {
            "license": QUALIFICATION_MODEL_LICENSE,
            "model_digest": "1" * 64,
            "model_ref": QUALIFICATION_MODEL_REF,
            "model_revision": QUALIFICATION_MODEL_REVISION,
            "snapshot_files": {
                "model.safetensors": QUALIFICATION_MODEL_FILE_SHA256,
            },
            "tokenizer_digest": "2" * 64,
            "tokenizer_ref": QUALIFICATION_MODEL_REF,
            "tokenizer_revision": QUALIFICATION_MODEL_REVISION,
        },
        "promotion_authorized": False,
        "protection_manifest_digest": request.protection_manifest_digest,
        "request_digest": request.digest,
        "requested_shape": "NvidiaTeslaT4",
        "schema": BOOTSTRAP_EVIDENCE_SCHEMA,
        "schema_version": 1,
        "source_sha": request.source_sha,
        "workload_digest": request.workload_digest,
    }


def _train_evidence(bundle) -> dict[str, object]:
    payload = _evidence(bundle)
    payload["benchmark"] = _report(
        {
            "config_digest": "3" * 64,
            "model_identities": [
                {
                    "model_digest": "1" * 64,
                    "model_ref": QUALIFICATION_MODEL_REF,
                    "resolved": True,
                    "runtime": "fixture",
                    "runtime_version": "1",
                }
            ],
            "outcomes": [
                {
                    "category": "wrong_answer",
                    "critical": True,
                    "domain": "v245-qualification",
                    "error": None,
                    "model_ref": QUALIFICATION_MODEL_REF,
                    "passed": False,
                    "repeat": repeat,
                    "resources": {},
                    "response_digest": "a" * 64,
                    "scorer_digest": "b" * 64,
                    "seed": 245 + repeat,
                    "task_id": "holdout-fixture",
                }
                for repeat in (1, 2)
            ],
            "protection_manifest_digest": bundle.request.protection_manifest_digest,
            "suite_digest": "6" * 64,
        }
    )
    payload["capability"] = _report(
        {
            "backend": "cuda",
            "backend_capability": "supported",
            "blockers": [],
            "device": {"backend_type": "cuda", "index": 0, "name": "Tesla T4"},
            "disposition": "ready",
            "dtype_supported": True,
            "four_bit_supported": True,
            "model_load": "supported",
            "packages": {},
            "python_version": "3.12.13",
            "request_digest": "9" * 64,
            "resources": {
                "blockers": [],
                "disk": {"free_bytes": 10 * 1024**3, "metric": "storage_mb"},
                "ram": {"free_bytes": 10 * 1024**3, "metric": "ram_mb"},
                "vram": {
                    "free_bytes": 12 * 1024**3,
                    "metric": "vram_mb",
                    "total_bytes": 15 * 1024**3,
                },
            },
            "schema": "kodepoia.r15.8.capability-report",
            "schema_version": 1,
            "seed_applied": True,
            "stderr": "",
            "torch_backend_version": "12.8",
        }
    )
    return payload


class _RecordingRunner:
    def __init__(self, payload: dict[str, object] | None = None) -> None:
        self.calls: list[list[str]] = []
        self.payload = payload

    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 120.0,
    ) -> CommandResult:
        del cwd, timeout
        self.calls.append(list(argv))
        if self.payload is not None and "output" in argv:
            output = Path(argv[argv.index("--path") + 1])
            output.mkdir(parents=True, exist_ok=True)
            (output / "bootstrap-evidence.json").write_text(
                json.dumps(self.payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return CommandResult(0, "ok", "")


def test_live_bootstrap_accepts_exact_git_sha_and_rejects_sha256_source(tmp_path: Path) -> None:
    _, bundle = _bundle(tmp_path)
    assert bundle.request.source_sha == SOURCE_SHA
    assert len(bundle.request.source_sha) == 40

    with pytest.raises(KaggleLiveBootstrapError, match="40 lowercase hexadecimal"):
        type(bundle.request)(
            source_sha="b" * 64,
            kaggle_dataset_id=DATASET_ID,
            kernel_id=KERNEL_ID,
            dataset_digest=bundle.request.dataset_digest,
            dataset_manifest_digest=bundle.request.dataset_manifest_digest,
            train_export_digest=bundle.request.train_export_digest,
            validation_export_digest=bundle.request.validation_export_digest,
            workload_digest=bundle.request.workload_digest,
            contamination_digest=bundle.request.contamination_digest,
            protection_manifest_digest=bundle.request.protection_manifest_digest,
            dedup_policy_digest=bundle.request.dedup_policy_digest,
            wheel_filename=bundle.request.wheel_filename,
            wheel_sha256=bundle.request.wheel_sha256,
        )


def test_governed_live_dataset_is_reproducible_and_has_separate_splits(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    first = build_live_qualification_dataset(root, root / "build-a")
    second = build_live_qualification_dataset(root, root / "build-b")

    assert first.workload_digest == second.workload_digest
    assert first.build.manifest.dataset_digest == second.build.manifest.dataset_digest
    assert first.build.manifest.export_digests == second.build.manifest.export_digests
    assert first.train_rows >= 8
    assert first.validation_rows >= 2
    assert first.train_path.read_bytes() != first.validation_path.read_bytes()
    assert json.loads(first.contamination_path.read_text(encoding="utf-8"))["findings"] == []


def test_live_bootstrap_bundle_is_private_non_promotable_and_fixed_shape(tmp_path: Path) -> None:
    _, bundle = _bundle(tmp_path)
    metadata = json.loads(
        (bundle.kernel_dir / "kernel-metadata.json").read_text(encoding="utf-8")
    )
    dataset_metadata = json.loads(
        (bundle.kaggle_dataset_dir / "dataset-metadata.json").read_text(encoding="utf-8")
    )
    request = bundle.request.to_dict()

    assert request["source_sha"] == SOURCE_SHA
    assert request["promotion_authorized"] is False
    assert metadata["id"] == KERNEL_ID
    assert metadata["is_private"] is True
    assert metadata["enable_gpu"] is True
    assert metadata["enable_internet"] is True
    assert metadata["machine_shape"] == "NvidiaTeslaT4"
    assert metadata["dataset_sources"] == [DATASET_ID]
    assert dataset_metadata["id"] == DATASET_ID
    assert "public" not in dataset_metadata


def test_live_bootstrap_preserves_exact_wheel_filename_and_hashes_it(
    tmp_path: Path,
) -> None:
    _, bundle = _bundle(tmp_path)
    wheel_filename = "kodepoia-1.1.0rc8-py3-none-any.whl"
    expected_digest = hashlib.sha256(b"deterministic-test-wheel").hexdigest()
    manifest = json.loads(
        (bundle.kaggle_dataset_dir / "bootstrap-bundle-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    script = (bundle.kernel_dir / "run_bootstrap.py").read_text(encoding="utf-8")

    compile(script, "run_bootstrap.py", "exec")
    assert bundle.request.wheel_filename == wheel_filename
    assert bundle.request.wheel_sha256 == expected_digest
    assert (bundle.kaggle_dataset_dir / wheel_filename).read_bytes() == (
        b"deterministic-test-wheel"
    )
    assert not (bundle.kaggle_dataset_dir / "kodepoia.whl").exists()
    assert manifest["wheel_filename"] == wheel_filename
    assert manifest["wheel_sha256"] == expected_digest
    assert manifest["files"][wheel_filename] == expected_digest
    assert "wheel = work / wheel_filename" in script
    assert (
        '[sys.executable, "-m", "pip", "install", '
        'f"{wheel}[tuning,tuning-bnb]"]'
    ) in script
    assert 'download_root = work / "pinned-model"' in script
    assert 'local_dir=download_root' in script
    assert 'QUALIFICATION_RUNTIME_MODEL_RELATIVE' in script
    assert 'stage_runtime_model_snapshot(' in script
    assert 'model_ref=QUALIFICATION_RUNTIME_MODEL_RELATIVE' in script
    assert 'model_revision=None' in script
    assert 'tokenizer_ref=QUALIFICATION_RUNTIME_MODEL_RELATIVE' in script
    assert 'local_files_only=True' in script
    assert 'trust_remote_code=False' in script
    for forbidden in (
        "HF_HOME",
        "HF_HUB_CACHE",
        "HF_TOKEN",
        "HUGGINGFACE_HUB_CACHE",
    ):
        assert forbidden not in script


def test_stage_runtime_model_snapshot_copies_exact_verified_files(
    tmp_path: Path,
) -> None:
    snapshot, hashes = _model_snapshot(tmp_path)
    runtime_root = tmp_path / "runtime"

    staged = stage_runtime_model_snapshot(snapshot, runtime_root, hashes)

    assert staged == runtime_root.resolve() / QUALIFICATION_RUNTIME_MODEL_RELATIVE
    assert not Path(QUALIFICATION_RUNTIME_MODEL_RELATIVE).is_absolute()
    assert ".." not in Path(QUALIFICATION_RUNTIME_MODEL_RELATIVE).parts
    assert Path(QUALIFICATION_RUNTIME_MODEL_RELATIVE).parts == (
        QUALIFICATION_RUNTIME_MODEL_RELATIVE,
    )
    assert tuple(sorted(path.name for path in staged.iterdir())) == tuple(
        sorted(QUALIFICATION_MODEL_REQUIRED_FILES)
    )
    for name in QUALIFICATION_MODEL_REQUIRED_FILES:
        assert hashlib.sha256((staged / name).read_bytes()).hexdigest() == hashes[name]


def test_stage_runtime_model_snapshot_rejects_incomplete_tampered_or_preexisting(
    tmp_path: Path,
) -> None:
    snapshot, hashes = _model_snapshot(tmp_path)

    incomplete = dict(hashes)
    incomplete.pop(QUALIFICATION_MODEL_REQUIRED_FILES[-1])
    with pytest.raises(
        KaggleLiveBootstrapError,
        match="must cover exactly",
    ):
        stage_runtime_model_snapshot(snapshot, tmp_path / "runtime-incomplete", incomplete)

    tampered = dict(hashes)
    tampered[QUALIFICATION_MODEL_REQUIRED_FILES[0]] = "0" * 64
    with pytest.raises(
        KaggleLiveBootstrapError,
        match="source hash mismatch",
    ):
        stage_runtime_model_snapshot(snapshot, tmp_path / "runtime-tampered", tampered)

    runtime_existing = tmp_path / "runtime-existing"
    target = runtime_existing / QUALIFICATION_RUNTIME_MODEL_RELATIVE
    target.mkdir(parents=True)
    (target / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(
        KaggleLiveBootstrapError,
        match="target already exists",
    ):
        stage_runtime_model_snapshot(snapshot, runtime_existing, hashes)


def test_stage_training_exports_copies_exact_verified_files(tmp_path: Path) -> None:
    root, bundle = _bundle(tmp_path)

    train_relative, validation_relative = stage_training_exports(
        bundle.governed_dataset,
        root,
        bundle.request.train_export_digest,
        bundle.request.validation_export_digest,
    )

    assert train_relative == f"{QUALIFICATION_TRAINING_DATA_RELATIVE}/train.jsonl"
    assert validation_relative == f"{QUALIFICATION_TRAINING_DATA_RELATIVE}/validation.jsonl"
    assert train_relative != validation_relative
    assert not Path(train_relative).is_absolute()
    assert ".." not in Path(train_relative).parts
    assert not Path(validation_relative).is_absolute()
    assert ".." not in Path(validation_relative).parts
    train_path = root / train_relative
    validation_path = root / validation_relative
    assert hashlib.sha256(train_path.read_bytes()).hexdigest() == (
        bundle.request.train_export_digest
    )
    assert hashlib.sha256(validation_path.read_bytes()).hexdigest() == (
        bundle.request.validation_export_digest
    )


def test_stage_training_exports_rejects_unsafe_identifiers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import kodepoia.tuning.kaggle_live_bootstrap as bootstrap

    root, bundle = _bundle(tmp_path)
    absolute = Path(Path.cwd().anchor) / "kodepoia-v245-escape"
    monkeypatch.setattr(
        bootstrap,
        "QUALIFICATION_TRAINING_DATA_RELATIVE",
        absolute.as_posix(),
    )
    with pytest.raises(KaggleLiveBootstrapError, match="relative identifier is unsafe"):
        bootstrap.stage_training_exports(
            bundle.governed_dataset,
            root,
            bundle.request.train_export_digest,
            bundle.request.validation_export_digest,
        )

    monkeypatch.setattr(
        bootstrap,
        "QUALIFICATION_TRAINING_DATA_RELATIVE",
        "qualification-runtime-data/../escape",
    )
    with pytest.raises(KaggleLiveBootstrapError, match="relative identifier is unsafe"):
        bootstrap.stage_training_exports(
            bundle.governed_dataset,
            root,
            bundle.request.train_export_digest,
            bundle.request.validation_export_digest,
        )


def test_stage_training_exports_rejects_tamper_preexisting_and_digest_divergence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import kodepoia.tuning.kaggle_live_bootstrap as bootstrap

    tampered_root, tampered_bundle = _bundle(tmp_path / "tampered")
    tampered_bundle.governed_dataset.train_path.write_bytes(b"tampered")
    with pytest.raises(KaggleLiveBootstrapError, match="source digest mismatch"):
        stage_training_exports(
            tampered_bundle.governed_dataset,
            tampered_root,
            tampered_bundle.request.train_export_digest,
            tampered_bundle.request.validation_export_digest,
        )

    existing_root, existing_bundle = _bundle(tmp_path / "existing")
    existing_target = existing_root / QUALIFICATION_TRAINING_DATA_RELATIVE
    existing_target.mkdir(parents=True)
    (existing_target / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(KaggleLiveBootstrapError, match="target already exists"):
        stage_training_exports(
            existing_bundle.governed_dataset,
            existing_root,
            existing_bundle.request.train_export_digest,
            existing_bundle.request.validation_export_digest,
        )

    divergent_root, divergent_bundle = _bundle(tmp_path / "divergent")
    real_copy2 = bootstrap.shutil.copy2

    def corrupt_copy2(
        source: Path,
        target: Path,
        *,
        follow_symlinks: bool = True,
    ) -> str:
        result = real_copy2(source, target, follow_symlinks=follow_symlinks)
        if Path(target).name == "train.jsonl":
            Path(target).write_bytes(Path(target).read_bytes() + b"tampered")
        return str(result)

    monkeypatch.setattr(bootstrap.shutil, "copy2", corrupt_copy2)
    with pytest.raises(KaggleLiveBootstrapError, match="staged export digest mismatch"):
        bootstrap.stage_training_exports(
            divergent_bundle.governed_dataset,
            divergent_root,
            divergent_bundle.request.train_export_digest,
            divergent_bundle.request.validation_export_digest,
        )
    assert not (divergent_root / QUALIFICATION_TRAINING_DATA_RELATIVE).exists()


def test_stage_training_exports_rejects_symlink_escape(tmp_path: Path) -> None:
    root, bundle = _bundle(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    symlink_parent = root / Path(QUALIFICATION_TRAINING_DATA_RELATIVE).parts[0]
    try:
        symlink_parent.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("platform does not permit test symlink creation")

    with pytest.raises(KaggleLiveBootstrapError, match="path escapes repository root"):
        stage_training_exports(
            bundle.governed_dataset,
            root,
            bundle.request.train_export_digest,
            bundle.request.validation_export_digest,
        )


def test_finalize_live_bootstrap_real_train_materializes_safe_training_plan(
    tmp_path: Path,
) -> None:
    root, bundle = _bundle(tmp_path)
    evidence = _train_evidence(bundle)

    result = finalize_live_bootstrap(
        repository_root=root,
        bundle=bundle,
        evidence=evidence,
        output_root=root / ".kodepoia" / "finalized-train",
    )

    assert result.decision.disposition is DecisionDisposition.TRAIN
    assert result.train_authorized is True
    assert result.training_plan is not None
    assert result.training_plan_path is not None
    assert result.training_plan_path.is_file()
    assert result.result_path.is_file()
    plan = result.training_plan
    assert plan.dataset.train_path == f"{QUALIFICATION_TRAINING_DATA_RELATIVE}/train.jsonl"
    assert plan.dataset.validation_path == (
        f"{QUALIFICATION_TRAINING_DATA_RELATIVE}/validation.jsonl"
    )
    assert plan.dataset.train_path != plan.dataset.validation_path
    assert not plan.dataset.train_path.startswith(".")
    assert not plan.dataset.validation_path.startswith(".")
    assert hashlib.sha256((root / plan.dataset.train_path).read_bytes()).hexdigest() == (
        bundle.request.train_export_digest
    )
    assert hashlib.sha256(
        (root / plan.dataset.validation_path).read_bytes()
    ).hexdigest() == bundle.request.validation_export_digest
    saved_plan = json.loads(result.training_plan_path.read_text(encoding="utf-8"))
    assert saved_plan["dataset_paths"]["train_path"] == plan.dataset.train_path
    assert saved_plan["dataset_paths"]["validation_path"] == plan.dataset.validation_path
    saved_result = json.loads(result.result_path.read_text(encoding="utf-8"))
    assert saved_result["disposition"] == "train"
    assert saved_result["qualification_only"] is True
    assert saved_result["promotion_authorized"] is False
    assert saved_result["training_plan_digest"] == plan.digest


def test_live_bootstrap_rejects_invalid_wheel_filename(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    wheel = root / "dist" / "kodepoia.whl"
    wheel.parent.mkdir(parents=True)
    wheel.write_bytes(b"invalid-wheel-name")

    with pytest.raises(
        KaggleLiveBootstrapError,
        match="preserve a valid wheel filename",
    ):
        build_live_bootstrap_bundle(
            repository_root=root,
            source_sha=SOURCE_SHA,
            kaggle_dataset_id=DATASET_ID,
            kernel_id=KERNEL_ID,
            wheel_path=wheel,
            output_root=root / ".kodepoia" / "live" / "invalid-wheel",
        )


def test_subprocess_runner_forces_utf8_for_kaggle_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_run(argv: list[str], **kwargs: object) -> SimpleNamespace:
        captured["argv"] = list(argv)
        captured.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(
        "kodepoia.tuning.kaggle_remote.subprocess.run",
        fake_run,
    )

    result = SubprocessCommandRunner().run(
        ["kaggle", "kernels", "output", "owner/kernel"],
        timeout=42.0,
    )

    env = captured["env"]
    assert isinstance(env, dict)
    assert env["PYTHONUTF8"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "strict"
    assert captured["shell"] is False
    assert captured["text"] is True
    assert captured["timeout"] == 42.0
    assert result == CommandResult(0, "ok", "")


def test_live_bootstrap_client_uses_fixed_kaggle_argv_and_revalidates_output(
    tmp_path: Path,
) -> None:
    _, bundle = _bundle(tmp_path)
    payload = _evidence(bundle)
    runner = _RecordingRunner(payload)
    client = KaggleLiveBootstrapClient(runner=runner)

    client.upload_private_dataset(bundle)
    client.dataset_status(bundle)
    client.push(bundle)
    client.status(bundle)
    observed = client.fetch_evidence(bundle)

    assert observed == payload
    assert runner.calls[0][:3] == ["kaggle", "datasets", "create"]
    assert "--public" not in runner.calls[0]
    assert runner.calls[1] == [
        "kaggle",
        "datasets",
        "status",
        DATASET_ID,
        "--format",
        "json",
    ]
    assert runner.calls[2] == ["kaggle", "kernels", "push", "--path", str(bundle.kernel_dir)]
    assert runner.calls[3] == ["kaggle", "kernels", "status", KERNEL_ID]
    assert runner.calls[4] == [
        "kaggle",
        "kernels",
        "output",
        KERNEL_ID,
        "--path",
        str(bundle.output_dir),
        "--quiet",
    ]

    bad = dict(payload)
    bad["source_sha"] = "f" * 40
    bad_runner = _RecordingRunner(bad)
    with pytest.raises(KaggleLiveBootstrapError, match="source_sha mismatch"):
        KaggleLiveBootstrapClient(runner=bad_runner).fetch_evidence(bundle)


def test_finalize_live_bootstrap_does_not_force_train(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import kodepoia.tuning.kaggle_live_bootstrap as bootstrap

    root, bundle = _bundle(tmp_path)
    evidence = _evidence(bundle)

    class _NoTrainDecision:
        disposition = DecisionDisposition.NO_TRAIN
        digest = "d" * 64

        def save(self, path: Path) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{"disposition":"no_train"}\n', encoding="utf-8")

    class _Engine:
        def evaluate(self, *_args: object, **_kwargs: object) -> _NoTrainDecision:
            return _NoTrainDecision()

    monkeypatch.setattr(bootstrap, "GapDecisionEngine", _Engine)

    result = finalize_live_bootstrap(
        repository_root=root,
        bundle=bundle,
        evidence=evidence,
        output_root=root / ".kodepoia" / "finalized",
    )
    saved = json.loads(result.result_path.read_text(encoding="utf-8"))

    assert result.train_authorized is False
    assert result.training_plan is None
    assert result.training_plan_path is None
    assert saved["disposition"] == "no_train"
    assert saved["promotion_authorized"] is False
    assert saved["qualification_only"] is True
    assert saved["training_plan_digest"] is None
