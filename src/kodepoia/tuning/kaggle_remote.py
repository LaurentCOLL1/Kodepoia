from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from .contracts import QuantizationMode, ResourceRequest, SeedConfig, TrainingBackend
from .topology import ProviderAcceleratorRequest
from .training import (
    DatasetBinding,
    LoraTrainingConfig,
    ModelBinding,
    SFTTrainingConfig,
    TrainingAuthorization,
    TrainingError,
    TrainingMode,
    TrainingPlan,
    TrainingReport,
    TrainingRunner,
)

_BUNDLE_SCHEMA = "kodepoia.r15.kaggle-training-bundle"
_BUNDLE_SCHEMA_VERSION = 1
_SAFE_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,49}$")
_SAFE_USERNAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,49}$")
_SECRET_KEYS = {
    "access_token",
    "api_key",
    "credential",
    "credentials",
    "kaggle_api_token",
    "kaggle_key",
    "password",
    "refresh_token",
    "secret",
    "token",
}


class KaggleRemoteError(RuntimeError):
    """Raised when a governed Kaggle remote-training operation is invalid."""


class KaggleAccelerator(StrEnum):
    NVIDIA_T4 = "NvidiaTeslaT4"
    NVIDIA_L4 = "NvidiaL4"


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


class CommandRunner(Protocol):
    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 120.0,
    ) -> CommandResult: ...


class SubprocessCommandRunner:
    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 120.0,
    ) -> CommandResult:
        child_env = os.environ.copy()
        child_env["PYTHONUTF8"] = "1"
        child_env["PYTHONIOENCODING"] = "utf-8"
        completed = subprocess.run(
            argv,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            timeout=timeout,
            shell=False,
            env=child_env,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


@dataclass(frozen=True, slots=True)
class KaggleDoctorReport:
    cli_available: bool
    authenticated: bool
    version: str | None
    message: str

    @property
    def ready(self) -> bool:
        return self.cli_available and self.authenticated

    def to_dict(self) -> dict[str, object]:
        return {
            "authenticated": self.authenticated,
            "cli_available": self.cli_available,
            "message": self.message,
            "ready": self.ready,
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class KaggleRemoteConfig:
    username: str
    dataset_slug: str
    kernel_slug: str
    accelerator: KaggleAccelerator = KaggleAccelerator.NVIDIA_T4
    enable_internet: bool = True

    def __post_init__(self) -> None:
        username = self.username.strip()
        dataset_slug = self.dataset_slug.strip().lower()
        kernel_slug = self.kernel_slug.strip().lower()
        if _SAFE_USERNAME.fullmatch(username) is None:
            raise KaggleRemoteError("Kaggle username contains unsupported characters")
        for label, value in (("dataset_slug", dataset_slug), ("kernel_slug", kernel_slug)):
            if _SAFE_SLUG.fullmatch(value) is None:
                raise KaggleRemoteError(f"{label} must be a lowercase Kaggle slug")
        object.__setattr__(self, "username", username)
        object.__setattr__(self, "dataset_slug", dataset_slug)
        object.__setattr__(self, "kernel_slug", kernel_slug)
        object.__setattr__(self, "accelerator", KaggleAccelerator(self.accelerator))

    @property
    def dataset_id(self) -> str:
        return f"{self.username}/{self.dataset_slug}"

    @property
    def kernel_id(self) -> str:
        return f"{self.username}/{self.kernel_slug}"

    @property
    def kernel_title(self) -> str:
        return self.kernel_slug.replace("-", " ")

    def topology_request(self) -> ProviderAcceleratorRequest:
        if self.accelerator is KaggleAccelerator.NVIDIA_T4:
            return ProviderAcceleratorRequest(
                provider="kaggle",
                shape=self.accelerator.value,
                expected_backend=TrainingBackend.CUDA,
                expected_device_count=2,
                expected_name_contains="T4",
            )
        return ProviderAcceleratorRequest(
            provider="kaggle",
            shape=self.accelerator.value,
            expected_backend=TrainingBackend.CUDA,
            expected_device_count=None,
            expected_name_contains="L4",
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "accelerator": self.accelerator.value,
            "dataset_id": self.dataset_id,
            "dataset_slug": self.dataset_slug,
            "enable_internet": self.enable_internet,
            "kernel_id": self.kernel_id,
            "kernel_slug": self.kernel_slug,
            "username": self.username,
        }


@dataclass(frozen=True, slots=True)
class KaggleTrainingBundle:
    root: Path
    dataset_dir: Path
    kernel_dir: Path
    output_dir: Path
    manifest_path: Path
    config: KaggleRemoteConfig
    plan_digest: str
    run_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "config": self.config.to_dict(),
            "dataset_dir": str(self.dataset_dir),
            "kernel_dir": str(self.kernel_dir),
            "manifest_path": str(self.manifest_path),
            "output_dir": str(self.output_dir),
            "plan_digest": self.plan_digest,
            "root": str(self.root),
            "run_id": self.run_id,
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _assert_no_secret_fields(payload: object) -> None:
    def visit(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).lower() in _SECRET_KEYS:
                    raise KaggleRemoteError("Kaggle bundle must not contain credential or secret fields")
                visit(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                visit(item)

    visit(payload)


def training_plan_payload(plan: TrainingPlan) -> dict[str, object]:
    payload = plan.descriptor()
    payload["dataset_paths"] = plan.dataset.to_dict(include_paths=True)
    payload["plan_digest"] = plan.digest
    payload["run_id"] = plan.run_id
    return payload


def save_training_plan(plan: TrainingPlan, path: Path) -> Path:
    payload = training_plan_payload(plan)
    _assert_no_secret_fields(payload)
    _write_json(path, payload)
    return path


def load_training_plan(path: Path) -> TrainingPlan:
    raw = json.loads(path.read_text(encoding="utf-8"))
    model_raw = dict(raw["model"])
    dataset_raw = dict(raw["dataset_paths"])
    lora_raw = dict(raw["lora"])
    sft_raw = dict(raw["sft"])
    seeds_raw = dict(raw["seeds"])
    resources_raw = dict(raw["resources"])
    resources_raw.pop("vram_required_free_bytes", None)
    plan = TrainingPlan(
        mode=TrainingMode(str(raw["mode"])),
        authorization=TrainingAuthorization(str(raw["authorization"])),
        model=ModelBinding(**model_raw),
        dataset=DatasetBinding(**dataset_raw),
        lora=LoraTrainingConfig(
            rank=int(lora_raw["rank"]),
            alpha=int(lora_raw["alpha"]),
            dropout=float(lora_raw["dropout"]),
            target_modules=tuple(str(item) for item in lora_raw["target_modules"]),
        ),
        sft=SFTTrainingConfig(**sft_raw),
        quantization=QuantizationMode(str(raw["quantization"])),
        seeds=SeedConfig(**seeds_raw),
        resources=ResourceRequest(**resources_raw),
        timeout_seconds=float(raw["timeout_seconds"]),
        capability_report_digest=(
            None
            if raw.get("capability_report_digest") is None
            else str(raw["capability_report_digest"])
        ),
        fixture_authorization=(
            None if raw.get("fixture_authorization") is None else str(raw["fixture_authorization"])
        ),
    )
    if raw.get("plan_digest") not in {None, plan.digest}:
        raise KaggleRemoteError("saved TrainingPlan digest does not match reconstructed plan")
    return plan


class KaggleResultValidator(TrainingRunner):
    """Reuse the exact R15.9 worker-output validation for remote Kaggle results."""

    def validate_external_output(self, plan: TrainingPlan, output: object) -> TrainingReport:
        try:
            return self._validate_worker_report(plan, output, None, "")
        except (TrainingError, KeyError, TypeError, ValueError, OSError) as exc:
            raise KaggleRemoteError(f"Kaggle training output rejected: {exc}") from exc


class KaggleRemoteTrainer:
    def __init__(
        self,
        *,
        runner: CommandRunner | None = None,
        kaggle_executable: str | None = None,
    ) -> None:
        self.runner = runner or SubprocessCommandRunner()
        self.kaggle_executable = kaggle_executable or shutil.which("kaggle") or "kaggle"

    def doctor(self) -> KaggleDoctorReport:
        executable = (
            shutil.which(self.kaggle_executable)
            if self.kaggle_executable == "kaggle"
            else self.kaggle_executable
        )
        if not executable or (os.path.sep in executable and not Path(executable).exists()):
            return KaggleDoctorReport(False, False, None, "Kaggle CLI is not installed or not on PATH")
        version_result = self.runner.run([executable, "--version"], timeout=30.0)
        version = version_result.stdout.strip() or version_result.stderr.strip() or None
        if version_result.returncode != 0:
            return KaggleDoctorReport(True, False, version, "Kaggle CLI version check failed")
        auth_result = self.runner.run(
            [executable, "datasets", "list", "--mine", "--page-size", "1"],
            timeout=60.0,
        )
        if auth_result.returncode != 0:
            return KaggleDoctorReport(
                True,
                False,
                version,
                "Kaggle CLI is installed but authentication is unavailable; run 'kaggle auth login'",
            )
        return KaggleDoctorReport(True, True, version, "Kaggle CLI is ready")

    def prepare_bundle(
        self,
        *,
        project_root: Path,
        plan: TrainingPlan,
        wheel_path: Path,
        config: KaggleRemoteConfig,
        output_root: Path,
    ) -> KaggleTrainingBundle:
        if plan.authorization is not TrainingAuthorization.TRAIN:
            raise KaggleRemoteError("Kaggle remote training requires governed TRAIN authorization")
        if plan.mode not in {TrainingMode.SFT, TrainingMode.QLORA}:
            raise KaggleRemoteError("Kaggle remote training accepts only real SFT or QLoRA plans")
        if plan.dataset.train_path is None or plan.dataset.validation_path is None:
            raise KaggleRemoteError("TrainingPlan must bind explicit train and validation paths")

        project_root = project_root.resolve(strict=True)
        train_path = (project_root / plan.dataset.train_path).resolve(strict=True)
        validation_path = (project_root / plan.dataset.validation_path).resolve(strict=True)
        for label, path in (("train", train_path), ("validation", validation_path)):
            if project_root not in path.parents:
                raise KaggleRemoteError(f"{label} dataset path escapes project root")
        if _sha256(train_path) != plan.dataset.train_export_digest:
            raise KaggleRemoteError("train export digest does not match TrainingPlan")
        if _sha256(validation_path) != plan.dataset.validation_export_digest:
            raise KaggleRemoteError("validation export digest does not match TrainingPlan")

        wheel_path = wheel_path.resolve(strict=True)
        if wheel_path.suffix.lower() != ".whl":
            raise KaggleRemoteError("wheel_path must reference a built Kodepoia wheel")

        root = (output_root / plan.run_id).resolve(strict=False)
        if root.exists() and any(root.iterdir()):
            raise KaggleRemoteError(f"Kaggle bundle directory is not empty: {root}")
        dataset_dir = root / "dataset"
        kernel_dir = root / "kernel"
        output_dir = root / "output"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        kernel_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        train_copy = dataset_dir / "train.jsonl"
        validation_copy = dataset_dir / "validation.jsonl"
        wheel_copy = dataset_dir / "kodepoia.whl"
        shutil.copy2(train_path, train_copy)
        shutil.copy2(validation_path, validation_copy)
        shutil.copy2(wheel_path, wheel_copy)

        remote_dataset = replace(
            plan.dataset,
            train_path="train.jsonl",
            validation_path="validation.jsonl",
        )
        remote_plan = replace(plan, dataset=remote_dataset)
        worker_config = remote_plan.worker_payload(
            dataset_dir,
            dataset_dir / "tuning-runs" / plan.run_id,
            None,
        )
        config_path = dataset_dir / "worker-config.json"
        _write_json(config_path, worker_config)

        manifest = {
            "files": {
                "kodepoia.whl": _sha256(wheel_copy),
                "train.jsonl": _sha256(train_copy),
                "validation.jsonl": _sha256(validation_copy),
                "worker-config.json": _sha256(config_path),
            },
            "plan_digest": plan.digest,
            "run_id": plan.run_id,
            "schema": _BUNDLE_SCHEMA,
            "schema_version": _BUNDLE_SCHEMA_VERSION,
        }
        _assert_no_secret_fields(manifest)
        manifest_path = dataset_dir / "bundle-manifest.json"
        _write_json(manifest_path, manifest)

        dataset_metadata = {
            "description": "Private transient Kodepoia governed training bundle.",
            "id": config.dataset_id,
            "licenses": [{"name": "other"}],
            "title": f"Kodepoia training {plan.run_id}",
        }
        _assert_no_secret_fields(dataset_metadata)
        _write_json(dataset_dir / "dataset-metadata.json", dataset_metadata)

        script_path = kernel_dir / "run_training.py"
        script_path.write_text(_kernel_script(), encoding="utf-8")
        kernel_metadata = {
            "code_file": script_path.name,
            "competition_sources": [],
            "dataset_sources": [config.dataset_id],
            "enable_gpu": True,
            "enable_internet": config.enable_internet,
            "id": config.kernel_id,
            "is_private": True,
            "kernel_sources": [],
            "kernel_type": "script",
            "language": "python",
            "machine_shape": config.accelerator.value,
            "model_sources": [],
            "title": config.kernel_title,
        }
        _assert_no_secret_fields(kernel_metadata)
        _write_json(kernel_dir / "kernel-metadata.json", kernel_metadata)

        bundle_metadata = {
            "config": config.to_dict(),
            "plan_digest": plan.digest,
            "run_id": plan.run_id,
            "schema": _BUNDLE_SCHEMA,
            "schema_version": _BUNDLE_SCHEMA_VERSION,
        }
        _assert_no_secret_fields(bundle_metadata)
        _write_json(root / "bundle.json", bundle_metadata)
        save_training_plan(plan, root / "training-plan.json")
        return KaggleTrainingBundle(
            root=root,
            dataset_dir=dataset_dir,
            kernel_dir=kernel_dir,
            output_dir=output_dir,
            manifest_path=manifest_path,
            config=config,
            plan_digest=plan.digest,
            run_id=plan.run_id,
        )

    def upload_private_dataset(self, bundle: KaggleTrainingBundle) -> CommandResult:
        return self._checked(
            [
                self.kaggle_executable,
                "datasets",
                "create",
                "--path",
                str(bundle.dataset_dir),
                "--dir-mode",
                "zip",
            ],
            timeout=3600.0,
        )

    def dataset_status(self, bundle: KaggleTrainingBundle) -> CommandResult:
        return self._checked(
            [
                self.kaggle_executable,
                "datasets",
                "status",
                bundle.config.dataset_id,
                "--format",
                "json",
            ],
            timeout=120.0,
        )

    def push_kernel(self, bundle: KaggleTrainingBundle) -> CommandResult:
        return self._checked(
            [self.kaggle_executable, "kernels", "push", "--path", str(bundle.kernel_dir)],
            timeout=300.0,
        )

    def kernel_status(self, bundle: KaggleTrainingBundle) -> CommandResult:
        return self._checked(
            [self.kaggle_executable, "kernels", "status", bundle.config.kernel_id],
            timeout=120.0,
        )

    def fetch_output(self, bundle: KaggleTrainingBundle, plan: TrainingPlan) -> TrainingReport:
        bundle.output_dir.mkdir(parents=True, exist_ok=True)
        self._checked(
            [
                self.kaggle_executable,
                "kernels",
                "output",
                bundle.config.kernel_id,
                "--path",
                str(bundle.output_dir),
            ],
            timeout=3600.0,
        )
        output_path = bundle.output_dir / "worker-output.json"
        if not output_path.is_file():
            matches = list(bundle.output_dir.rglob("worker-output.json"))
            if len(matches) != 1:
                raise KaggleRemoteError(
                    "Kaggle output does not contain exactly one worker-output.json"
                )
            output_path = matches[0]
        output_root = output_path.parent
        output = json.loads(output_path.read_text(encoding="utf-8"))
        return KaggleResultValidator(output_root).validate_external_output(plan, output)

    def _checked(self, argv: list[str], *, timeout: float) -> CommandResult:
        result = self.runner.run(argv, timeout=timeout)
        if result.returncode != 0:
            stderr = result.stderr.strip()[:4096]
            raise KaggleRemoteError(
                f"Kaggle CLI command failed ({result.returncode}): {stderr}"
            )
        return result


def _kernel_script() -> str:
    return '''from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


input_root = Path("/kaggle/input")
manifests = list(input_root.rglob("bundle-manifest.json"))
if len(manifests) != 1:
    raise SystemExit(f"Expected one Kodepoia bundle manifest, found {len(manifests)}")
source = manifests[0].parent
manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
if manifest.get("schema") != "kodepoia.r15.kaggle-training-bundle":
    raise SystemExit("Unsupported Kodepoia Kaggle bundle schema")
for name, expected in manifest["files"].items():
    path = source / name
    if not path.is_file() or sha256(path) != expected:
        raise SystemExit(f"Bundle integrity failure: {name}")

work = Path("/kaggle/working/kodepoia-training")
if work.exists():
    shutil.rmtree(work)
work.mkdir(parents=True)
for name in ("train.jsonl", "validation.jsonl", "worker-config.json", "kodepoia.whl"):
    shutil.copy2(source / name, work / name)

try:
    from kaggle_secrets import UserSecretsClient

    hf_token = UserSecretsClient().get_secret("HF_TOKEN")
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token
except Exception:
    pass

wheel = work / "kodepoia.whl"
install = subprocess.run(
    [sys.executable, "-m", "pip", "install", f"{wheel}[tuning,tuning-bnb]"],
    cwd=work,
    capture_output=True,
    text=True,
    check=False,
)
(work / "pip-install.log").write_text(
    install.stdout + "\n" + install.stderr,
    encoding="utf-8",
)
if install.returncode != 0:
    raise SystemExit("Kodepoia tuning dependencies failed to install")

training = subprocess.run(
    [sys.executable, "-m", "kodepoia.tuning.train_worker", "worker-config.json"],
    cwd=work,
    capture_output=True,
    text=True,
    check=False,
)
(work / "worker-stderr.txt").write_text(training.stderr, encoding="utf-8")
if training.returncode != 0:
    raise SystemExit("Kodepoia training worker failed; inspect worker-stderr.txt")
payload = json.loads(training.stdout)
(work / "worker-output.json").write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(
    json.dumps(
        {
            "plan_digest": manifest["plan_digest"],
            "run_id": manifest["run_id"],
            "state": "completed",
        }
    )
)
'''


def _bundle_from_root(root: Path) -> KaggleTrainingBundle:
    payload = json.loads((root / "bundle.json").read_text(encoding="utf-8"))
    config_raw = dict(payload["config"])
    config = KaggleRemoteConfig(
        username=str(config_raw["username"]),
        dataset_slug=str(config_raw["dataset_slug"]),
        kernel_slug=str(config_raw["kernel_slug"]),
        accelerator=KaggleAccelerator(str(config_raw["accelerator"])),
        enable_internet=bool(config_raw["enable_internet"]),
    )
    return KaggleTrainingBundle(
        root=root,
        dataset_dir=root / "dataset",
        kernel_dir=root / "kernel",
        output_dir=root / "output",
        manifest_path=root / "dataset" / "bundle-manifest.json",
        config=config,
        plan_digest=str(payload["plan_digest"]),
        run_id=str(payload["run_id"]),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Governed Kodepoia remote training on Kaggle"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Check Kaggle CLI and authentication")

    prepare = sub.add_parser("prepare", help="Prepare a private Kaggle training bundle")
    prepare.add_argument("--project-root", type=Path, required=True)
    prepare.add_argument("--plan", type=Path, required=True)
    prepare.add_argument("--wheel", type=Path, required=True)
    prepare.add_argument("--username", required=True)
    prepare.add_argument("--dataset-slug", required=True)
    prepare.add_argument("--kernel-slug", required=True)
    prepare.add_argument(
        "--accelerator",
        choices=[item.value for item in KaggleAccelerator],
        default=KaggleAccelerator.NVIDIA_T4.value,
    )
    prepare.add_argument("--output", type=Path, required=True)

    for name in ("upload", "dataset-status", "run", "status", "fetch"):
        item = sub.add_parser(name)
        item.add_argument("--bundle", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    trainer = KaggleRemoteTrainer()
    if args.command == "doctor":
        report = trainer.doctor()
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0 if report.ready else 2
    if args.command == "prepare":
        plan = load_training_plan(args.plan)
        bundle = trainer.prepare_bundle(
            project_root=args.project_root,
            plan=plan,
            wheel_path=args.wheel,
            config=KaggleRemoteConfig(
                username=args.username,
                dataset_slug=args.dataset_slug,
                kernel_slug=args.kernel_slug,
                accelerator=KaggleAccelerator(args.accelerator),
            ),
            output_root=args.output,
        )
        print(json.dumps(bundle.to_dict(), indent=2, sort_keys=True))
        return 0

    bundle = _bundle_from_root(args.bundle.resolve(strict=True))
    if args.command == "upload":
        print(trainer.upload_private_dataset(bundle).stdout)
    elif args.command == "dataset-status":
        print(trainer.dataset_status(bundle).stdout)
    elif args.command == "run":
        print(trainer.push_kernel(bundle).stdout)
    elif args.command == "status":
        print(trainer.kernel_status(bundle).stdout)
    elif args.command == "fetch":
        plan = load_training_plan(bundle.root / "training-plan.json")
        report = trainer.fetch_output(bundle, plan)
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
