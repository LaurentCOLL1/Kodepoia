from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from kodepoia.bench import (
    BenchmarkSuite,
    BenchmarkTaskSpec,
    KodeBenchRunner,
    ModelIdentity,
    RunConfig,
    ScorerKind,
    ScorerSpec,
)
from kodepoia.bench.evaluation import (
    BaseAdapterEvaluator,
    CandidateBinding,
    CandidateEvaluationPolicy,
    TrainingLossContext,
)
from kodepoia.brain.base import BrainResponse
from kodepoia.core.sandbox import ProcessSandbox, SandboxResult
from kodepoia.experience import DedupPolicy, ProtectedHoldout, ProtectedHoldoutRegistry

from .contracts import TrainingBackend, canonical_sha256
from .distributed import (
    DistributedExecutionState,
    DistributedTrainingRunner,
    QualificationOnlyDistributedTrainingReport,
    build_distributed_execution_plan,
    build_qualification_only_distributed_execution_plan,
    build_qualification_only_launch_permit,
)
from .distributed_recovery import (
    build_distributed_checkpoint_manifest,
    build_distributed_recovery_plan,
)
from .kaggle_live_qualification import (
    KaggleLiveQualificationRequest,
    validate_live_evidence,
)
from .kaggle_remote import (
    CommandResult,
    KaggleResultValidator,
    SubprocessCommandRunner,
    load_training_plan,
)
from .strategy import (
    StrategyBenchmarkDisposition,
    StrategyBenchmarkMeasurement,
    StrategyKind,
    build_execution_strategy_plan,
    evaluate_strategy_benchmark,
)
from .topology import (
    AcceleratorDevice,
    AcceleratorTopologyReport,
    ObservedAcceleratorTopology,
    ProviderAcceleratorRequest,
    TopologyDisposition,
)
from .training import TrainingPlan, TrainingRunState, TrainingRunner

LIVE_PAIR_REQUEST_SCHEMA = "kodepoia.v2.4.5.live-pair-request"
LIVE_PAIR_BUNDLE_SCHEMA = "kodepoia.v2.4.5.live-pair-bundle"
LIVE_PAIR_RESULT_SCHEMA = "kodepoia.v2.4.5.live-pair-result"
LIVE_PAIR_EVIDENCE_SCHEMA = "kodepoia.v2.4.5.live-pair-evidence"
LIVE_PAIR_SCHEMA_VERSION = 1

_MODEL_REF = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
_MODEL_REVISION = "fe8a4ea1ffedaf415f4da2f062534de366a451e6"
_MODEL_FILE_SHA256 = "6e6001da2106d4757498752a021df6c2bdc332c650aae4bae6b0c004dcf14933"
_REQUIRED_MODEL_FILES = (
    "config.json",
    "model.safetensors",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer.model",
    "tokenizer_config.json",
)
_CUDA_ENV_ALLOWLIST = (
    "LD_LIBRARY_PATH",
    "CUDA_VISIBLE_DEVICES",
    "CUDA_DEVICE_ORDER",
    "NVIDIA_VISIBLE_DEVICES",
    "NVIDIA_DRIVER_CAPABILITIES",
)
_HF_ENV_FORBIDDEN = (
    "HF_HOME",
    "HF_HUB_CACHE",
    "HF_TOKEN",
    "HUGGINGFACE_HUB_CACHE",
)
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_SHA = re.compile(r"^[0-9a-f]{40}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{1,127}$")
_SECRET_KEYS = {
    "access_token",
    "api_key",
    "credential",
    "credentials",
    "hf_token",
    "kaggle_api_token",
    "kaggle_key",
    "password",
    "refresh_token",
    "secret",
    "token",
}


class KaggleLivePairError(RuntimeError):
    """Raised when the bounded V2.4.5 live-pair contract is invalid."""


class CommandRunner(Protocol):
    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 120.0,
    ) -> CommandResult: ...


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inside(root: Path, path: Path, *, strict: bool = False) -> Path:
    resolved_root = root.resolve(strict=True)
    resolved = path.resolve(strict=strict)
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise KaggleLivePairError("live-pair path escapes repository/work root")
    return resolved


def _digest(label: str, value: str) -> str:
    if _DIGEST.fullmatch(value) is None:
        raise KaggleLivePairError(f"{label} must be 64 lowercase hex characters")
    return value


def _safe_id(label: str, value: str) -> str:
    value = value.strip()
    if _SAFE_ID.fullmatch(value) is None or ".." in value:
        raise KaggleLivePairError(f"{label} must be a bounded safe identifier")
    return value


def _assert_no_secrets(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in _SECRET_KEYS:
                raise KaggleLivePairError("live-pair evidence contains a secret-like field")
            _assert_no_secrets(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_secrets(item)


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise KaggleLivePairError(f"expected JSON object: {path}")
    return payload


def load_topology_report(path: Path) -> AcceleratorTopologyReport:
    payload = _read_json(path)
    provider_raw = payload.get("provider_request")
    observed_raw = payload.get("observed")
    if not isinstance(provider_raw, Mapping) or not isinstance(observed_raw, Mapping):
        raise KaggleLivePairError("topology report is missing provider/observed evidence")
    devices_raw = observed_raw.get("devices")
    if not isinstance(devices_raw, list):
        raise KaggleLivePairError("topology report devices must be a list")
    provider = ProviderAcceleratorRequest(
        provider=str(provider_raw["provider"]),
        shape=str(provider_raw["shape"]),
        expected_backend=TrainingBackend(str(provider_raw["expected_backend"])),
        expected_device_count=int(provider_raw["expected_device_count"]),
        expected_name_contains=str(provider_raw["expected_name_contains"]),
    )
    observed = ObservedAcceleratorTopology(
        backend_type=TrainingBackend(str(observed_raw["backend_type"])),
        devices=tuple(
            AcceleratorDevice(
                backend_type=TrainingBackend(str(item["backend_type"])),
                index=int(item["index"]),
                name=str(item["name"]),
                vram_free_bytes=int(item["vram_free_bytes"]),
                vram_total_bytes=int(item["vram_total_bytes"]),
            )
            for item in devices_raw
            if isinstance(item, Mapping)
        ),
    )
    report = AcceleratorTopologyReport(
        disposition=TopologyDisposition(str(payload["disposition"])),
        request_digest=str(payload["request_digest"]),
        backend=TrainingBackend(str(payload["backend"])),
        provider_request=provider,
        observed=observed,
        blockers=tuple(str(item) for item in payload.get("blockers", [])),
        stderr=str(payload.get("stderr", "")),
        schema=str(payload["schema"]),
        schema_version=int(payload["schema_version"]),
    )
    if report.digest != payload.get("report_digest"):
        raise KaggleLivePairError("topology report digest mismatch")
    if report.topology_digest != payload.get("topology_digest"):
        raise KaggleLivePairError("topology digest mismatch")
    return report


@dataclass(frozen=True, slots=True)
class KaggleLivePairRequest:
    source_sha: str
    kaggle_dataset_id: str
    kernel_id: str
    training_plan_digest: str
    capability_report_digest: str
    gap_decision_digest: str
    bootstrap_result_digest: str
    bootstrap_evidence_sha256: str
    topology_report_digest: str
    topology_digest: str
    single_strategy_plan_digest: str
    replicated_strategy_plan_digest: str
    qualification_permit_digest: str
    qualification_execution_plan_digest: str
    benchmark_config_digest: str
    processed_samples: int
    effective_global_batch_size: int
    wheel_filename: str
    wheel_sha256: str
    model_ref: str
    model_revision: str
    model_digest: str
    tokenizer_digest: str
    dataset_digest: str
    dataset_manifest_digest: str
    train_export_digest: str
    validation_export_digest: str
    protection_manifest_digest: str
    model_snapshot_files: tuple[tuple[str, str], ...]
    requested_shape: str = "NvidiaTeslaT4"
    schema: str = LIVE_PAIR_REQUEST_SCHEMA
    schema_version: int = LIVE_PAIR_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if _SOURCE_SHA.fullmatch(self.source_sha) is None:
            raise KaggleLivePairError("source_sha must be 40 lowercase hex characters")
        object.__setattr__(self, "kaggle_dataset_id", _safe_id("kaggle_dataset_id", self.kaggle_dataset_id))
        object.__setattr__(self, "kernel_id", _safe_id("kernel_id", self.kernel_id))
        for label in (
            "training_plan_digest",
            "capability_report_digest",
            "gap_decision_digest",
            "bootstrap_result_digest",
            "bootstrap_evidence_sha256",
            "topology_report_digest",
            "topology_digest",
            "single_strategy_plan_digest",
            "replicated_strategy_plan_digest",
            "qualification_permit_digest",
            "qualification_execution_plan_digest",
            "benchmark_config_digest",
            "wheel_sha256",
            "model_digest",
            "tokenizer_digest",
            "dataset_digest",
            "dataset_manifest_digest",
            "train_export_digest",
            "validation_export_digest",
            "protection_manifest_digest",
        ):
            _digest(label, getattr(self, label))
        if self.processed_samples < 1 or self.effective_global_batch_size < 1:
            raise KaggleLivePairError("live-pair sample/global-batch values must be positive")
        if self.wheel_filename != Path(self.wheel_filename).name or not self.wheel_filename.endswith(".whl"):
            raise KaggleLivePairError("wheel filename must be a plain .whl filename")
        if self.model_ref != _MODEL_REF or self.model_revision != _MODEL_REVISION:
            raise KaggleLivePairError("live pair must use the fixed V2.4.5 model identity")
        files = tuple(self.model_snapshot_files)
        object.__setattr__(self, "model_snapshot_files", files)
        if tuple(name for name, _ in files) != tuple(sorted(_REQUIRED_MODEL_FILES)):
            raise KaggleLivePairError("model snapshot file set is not the fixed required set")
        for name, digest in files:
            if Path(name).name != name:
                raise KaggleLivePairError("model snapshot filenames must be plain filenames")
            _digest(f"model snapshot {name}", digest)
        if dict(files)["model.safetensors"] != _MODEL_FILE_SHA256:
            raise KaggleLivePairError("model.safetensors digest is not the pinned V2.4.5 digest")
        if self.requested_shape != "NvidiaTeslaT4":
            raise KaggleLivePairError("V2.4.5 live pair requires NvidiaTeslaT4")
        if self.schema != LIVE_PAIR_REQUEST_SCHEMA or self.schema_version != LIVE_PAIR_SCHEMA_VERSION:
            raise KaggleLivePairError("unsupported live-pair request schema")

    def descriptor(self) -> dict[str, object]:
        return {
            "benchmark_config_digest": self.benchmark_config_digest,
            "bootstrap_evidence_sha256": self.bootstrap_evidence_sha256,
            "bootstrap_result_digest": self.bootstrap_result_digest,
            "capability_report_digest": self.capability_report_digest,
            "dataset_digest": self.dataset_digest,
            "dataset_manifest_digest": self.dataset_manifest_digest,
            "effective_global_batch_size": self.effective_global_batch_size,
            "gap_decision_digest": self.gap_decision_digest,
            "kaggle_dataset_id": self.kaggle_dataset_id,
            "kernel_id": self.kernel_id,
            "model_digest": self.model_digest,
            "model_ref": self.model_ref,
            "model_revision": self.model_revision,
            "model_snapshot_files": dict(self.model_snapshot_files),
            "processed_samples": self.processed_samples,
            "protection_manifest_digest": self.protection_manifest_digest,
            "qualification_execution_plan_digest": self.qualification_execution_plan_digest,
            "qualification_permit_digest": self.qualification_permit_digest,
            "replicated_strategy_plan_digest": self.replicated_strategy_plan_digest,
            "requested_shape": self.requested_shape,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "single_strategy_plan_digest": self.single_strategy_plan_digest,
            "source_sha": self.source_sha,
            "tokenizer_digest": self.tokenizer_digest,
            "topology_digest": self.topology_digest,
            "topology_report_digest": self.topology_report_digest,
            "train_export_digest": self.train_export_digest,
            "training_plan_digest": self.training_plan_digest,
            "validation_export_digest": self.validation_export_digest,
            "wheel_filename": self.wheel_filename,
            "wheel_sha256": self.wheel_sha256,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.descriptor())

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "pair_request_digest": self.digest}

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> "KaggleLivePairRequest":
        files = raw.get("model_snapshot_files")
        if not isinstance(files, Mapping):
            raise KaggleLivePairError("model_snapshot_files must be an object")
        return cls(
            source_sha=str(raw["source_sha"]),
            kaggle_dataset_id=str(raw["kaggle_dataset_id"]),
            kernel_id=str(raw["kernel_id"]),
            training_plan_digest=str(raw["training_plan_digest"]),
            capability_report_digest=str(raw["capability_report_digest"]),
            gap_decision_digest=str(raw["gap_decision_digest"]),
            bootstrap_result_digest=str(raw["bootstrap_result_digest"]),
            bootstrap_evidence_sha256=str(raw["bootstrap_evidence_sha256"]),
            topology_report_digest=str(raw["topology_report_digest"]),
            topology_digest=str(raw["topology_digest"]),
            single_strategy_plan_digest=str(raw["single_strategy_plan_digest"]),
            replicated_strategy_plan_digest=str(raw["replicated_strategy_plan_digest"]),
            qualification_permit_digest=str(raw["qualification_permit_digest"]),
            qualification_execution_plan_digest=str(raw["qualification_execution_plan_digest"]),
            benchmark_config_digest=str(raw["benchmark_config_digest"]),
            processed_samples=int(raw["processed_samples"]),
            effective_global_batch_size=int(raw["effective_global_batch_size"]),
            wheel_filename=str(raw["wheel_filename"]),
            wheel_sha256=str(raw["wheel_sha256"]),
            model_ref=str(raw["model_ref"]),
            model_revision=str(raw["model_revision"]),
            model_digest=str(raw["model_digest"]),
            tokenizer_digest=str(raw["tokenizer_digest"]),
            dataset_digest=str(raw["dataset_digest"]),
            dataset_manifest_digest=str(raw["dataset_manifest_digest"]),
            train_export_digest=str(raw["train_export_digest"]),
            validation_export_digest=str(raw["validation_export_digest"]),
            protection_manifest_digest=str(raw["protection_manifest_digest"]),
            model_snapshot_files=tuple(
                sorted((str(name), str(value)) for name, value in files.items())
            ),
            requested_shape=str(raw.get("requested_shape", "NvidiaTeslaT4")),
            schema=str(raw.get("schema", LIVE_PAIR_REQUEST_SCHEMA)),
            schema_version=int(raw.get("schema_version", LIVE_PAIR_SCHEMA_VERSION)),
        )


@dataclass(frozen=True, slots=True)
class KaggleLivePairBundle:
    root: Path
    dataset_dir: Path
    kernel_dir: Path
    output_dir: Path
    request: KaggleLivePairRequest


def _context(
    *,
    source_sha: str,
    training_plan: TrainingPlan,
    topology: AcceleratorTopologyReport,
    bootstrap_evidence: Mapping[str, object],
    decision: Mapping[str, object],
    bootstrap_result: Mapping[str, object],
    kaggle_dataset_id: str,
    kernel_id: str,
    wheel_filename: str,
    wheel_sha256: str,
    bootstrap_evidence_sha256: str,
) -> tuple[
    KaggleLivePairRequest,
    object,
    object,
    object,
    object,
]:
    capability = bootstrap_evidence.get("capability")
    model = bootstrap_evidence.get("model")
    if not isinstance(capability, Mapping) or not isinstance(model, Mapping):
        raise KaggleLivePairError("bootstrap evidence lacks capability/model evidence")
    if (
        capability.get("disposition") != "ready"
        or capability.get("backend") != "cuda"
        or capability.get("backend_capability") != "supported"
        or capability.get("dtype_supported") is not True
        or capability.get("four_bit_supported") is not True
        or capability.get("model_load") != "supported"
        or capability.get("blockers") != []
    ):
        raise KaggleLivePairError("R15.8 is not accepted for live-pair launch")
    if decision.get("disposition") != "train" or decision.get("blockers") != []:
        raise KaggleLivePairError("live-pair launch requires a real blocker-free R15.7 TRAIN")
    if bootstrap_result.get("qualification_only") is not True:
        raise KaggleLivePairError("bootstrap result must remain qualification-only")
    if bootstrap_result.get("promotion_authorized") is not False:
        raise KaggleLivePairError("bootstrap result cannot authorize promotion")
    if bootstrap_result.get("source_sha") != source_sha:
        raise KaggleLivePairError("bootstrap result source SHA mismatch")
    if bootstrap_result.get("training_plan_digest") != training_plan.digest:
        raise KaggleLivePairError("bootstrap TrainingPlan lineage mismatch")
    if training_plan.capability_report_digest != capability.get("report_digest"):
        raise KaggleLivePairError("TrainingPlan capability lineage mismatch")
    if topology.disposition is not TopologyDisposition.READY or topology.blockers:
        raise KaggleLivePairError("live-pair launch requires ready topology")
    if topology.topology_digest is None:
        raise KaggleLivePairError("live-pair topology digest is missing")

    single = build_execution_strategy_plan(
        training_plan,
        topology,
        strategy=StrategyKind.SINGLE_GPU,
        device_ordinals=(0,),
    )
    replicated = build_execution_strategy_plan(
        training_plan,
        topology,
        strategy=StrategyKind.REPLICATED_DATA_PARALLEL,
        device_ordinals=(0, 1),
    )
    if single.effective_global_batch_size != replicated.effective_global_batch_size:
        raise KaggleLivePairError("live-pair effective global batch is not preserved")

    permit = build_qualification_only_launch_permit(
        source_sha=source_sha,
        training_plan=training_plan,
        topology_report=topology,
        strategy_plan=replicated,
        gap_decision_digest=str(decision["decision_digest"]),
        bootstrap_result_digest=str(bootstrap_result["result_digest"]),
    )
    qualification_execution = build_qualification_only_distributed_execution_plan(
        training_plan,
        replicated,
        permit,
    )
    processed_samples = training_plan.sft.max_steps * single.effective_global_batch_size
    benchmark_config = {
        "checkpoint_steps": training_plan.sft.checkpoint_steps,
        "dataset_digest": training_plan.dataset.dataset_digest,
        "dataset_manifest_digest": training_plan.dataset.manifest_digest,
        "effective_global_batch_size": single.effective_global_batch_size,
        "eval_steps": training_plan.sft.eval_steps,
        "max_steps": training_plan.sft.max_steps,
        "model_digest": training_plan.model.model_digest,
        "model_ref": training_plan.model.model_ref,
        "model_revision": training_plan.model.model_revision,
        "processed_samples": processed_samples,
        "quantization": training_plan.quantization.value,
        "replicated_strategy_plan_digest": replicated.digest,
        "schema": "kodepoia.v2.4.5.live-pair-benchmark-config",
        "schema_version": 1,
        "single_strategy_plan_digest": single.digest,
        "source_sha": source_sha,
        "tokenizer_digest": training_plan.model.tokenizer_digest,
        "tokenizer_ref": training_plan.model.tokenizer_ref,
        "tokenizer_revision": training_plan.model.tokenizer_revision,
        "topology_digest": topology.topology_digest,
        "topology_report_digest": topology.digest,
        "train_export_digest": training_plan.dataset.train_export_digest,
        "training_plan_digest": training_plan.digest,
        "validation_export_digest": training_plan.dataset.validation_export_digest,
    }
    snapshot_files = model.get("snapshot_files")
    if not isinstance(snapshot_files, Mapping):
        raise KaggleLivePairError("bootstrap evidence lacks pinned snapshot hashes")
    request = KaggleLivePairRequest(
        source_sha=source_sha,
        kaggle_dataset_id=kaggle_dataset_id,
        kernel_id=kernel_id,
        training_plan_digest=training_plan.digest,
        capability_report_digest=str(capability["report_digest"]),
        gap_decision_digest=str(decision["decision_digest"]),
        bootstrap_result_digest=str(bootstrap_result["result_digest"]),
        bootstrap_evidence_sha256=bootstrap_evidence_sha256,
        topology_report_digest=topology.digest,
        topology_digest=topology.topology_digest,
        single_strategy_plan_digest=single.digest,
        replicated_strategy_plan_digest=replicated.digest,
        qualification_permit_digest=permit.digest,
        qualification_execution_plan_digest=qualification_execution.digest,
        benchmark_config_digest=canonical_sha256(benchmark_config),
        processed_samples=processed_samples,
        effective_global_batch_size=single.effective_global_batch_size,
        wheel_filename=wheel_filename,
        wheel_sha256=wheel_sha256,
        model_ref=str(model["model_ref"]),
        model_revision=str(model["model_revision"]),
        model_digest=str(model["model_digest"]),
        tokenizer_digest=str(model["tokenizer_digest"]),
        dataset_digest=training_plan.dataset.dataset_digest,
        dataset_manifest_digest=training_plan.dataset.manifest_digest,
        train_export_digest=training_plan.dataset.train_export_digest,
        validation_export_digest=training_plan.dataset.validation_export_digest,
        protection_manifest_digest=str(bootstrap_evidence["protection_manifest_digest"]),
        model_snapshot_files=tuple(
            sorted((str(name), str(value)) for name, value in snapshot_files.items())
        ),
    )
    return request, single, replicated, permit, qualification_execution


def _kernel_script(
    wheel_filename: str,
    wheel_sha256: str,
    source_sha: str,
    pair_request_digest: str,
) -> str:
    embedded_name = json.dumps(wheel_filename)
    embedded_sha = json.dumps(wheel_sha256)
    embedded_source = json.dumps(source_sha)
    embedded_request = json.dumps(pair_request_digest)
    return f'''from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

WHEEL_FILENAME = {embedded_name}
WHEEL_SHA256 = {embedded_sha}
SOURCE_SHA = {embedded_source}
PAIR_REQUEST_DIGEST = {embedded_request}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


input_root = Path("/kaggle/input")
manifests = list(input_root.rglob("live-pair-bundle-manifest.json"))
if len(manifests) != 1:
    raise SystemExit(f"Expected one live-pair bundle manifest, found {{len(manifests)}}")
source = manifests[0].parent
manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
if (
    manifest.get("schema") != "{LIVE_PAIR_BUNDLE_SCHEMA}"
    or manifest.get("schema_version") != {LIVE_PAIR_SCHEMA_VERSION}
):
    raise SystemExit("Live-pair bundle manifest schema mismatch")
if (
    manifest.get("source_sha") != SOURCE_SHA
    or manifest.get("pair_request_digest") != PAIR_REQUEST_DIGEST
):
    raise SystemExit("Live-pair exact-source request identity mismatch")
files = manifest.get("files")
if not isinstance(files, dict):
    raise SystemExit("Live-pair bundle file map is invalid")
for name, expected in files.items():
    path = source / name
    if (
        not isinstance(expected, str)
        or not path.is_file()
        or path.is_symlink()
        or sha256(path) != expected
    ):
        raise SystemExit(f"Live-pair bundle integrity failure: {{name}}")
wheel = source / WHEEL_FILENAME
if not wheel.is_file() or wheel.is_symlink() or sha256(wheel) != WHEEL_SHA256:
    raise SystemExit("Exact-head wheel integrity failure")
install = subprocess.run(
    [sys.executable, "-m", "pip", "install", f"{{wheel}}[tuning,tuning-bnb]"],
    capture_output=True,
    text=True,
    check=False,
)
Path("/kaggle/working/live-pair-pip-install.log").write_text(
    install.stdout + "\n" + install.stderr,
    encoding="utf-8",
)
if install.returncode != 0:
    raise SystemExit("Kodepoia live-pair dependencies failed to install")

from kodepoia.tuning.kaggle_live_pair import run_live_pair_kernel

run_live_pair_kernel(source, Path("/kaggle/working/kodepoia-v245-live-pair"))
'''


def build_live_pair_bundle(
    *,
    repository_root: Path,
    source_sha: str,
    kaggle_dataset_id: str,
    kernel_id: str,
    wheel_path: Path,
    topology_report_path: Path,
    bootstrap_evidence_path: Path,
    decision_path: Path,
    training_plan_path: Path,
    bootstrap_result_path: Path,
    workload_path: Path,
    holdouts_path: Path,
    output_root: Path,
) -> KaggleLivePairBundle:
    repository_root = repository_root.resolve(strict=True)
    output_root = _inside(repository_root, output_root, strict=False)
    if output_root.exists() and any(output_root.iterdir()):
        raise KaggleLivePairError("live-pair bundle directory must be empty")
    wheel_path = wheel_path.resolve(strict=True)
    if wheel_path.name != "kodepoia-1.1.0rc8-py3-none-any.whl":
        raise KaggleLivePairError("live-pair wheel filename must remain exact")
    wheel_sha256 = _sha256(wheel_path)
    training_plan = load_training_plan(training_plan_path.resolve(strict=True))
    topology = load_topology_report(topology_report_path.resolve(strict=True))
    evidence = _read_json(bootstrap_evidence_path.resolve(strict=True))
    decision = _read_json(decision_path.resolve(strict=True))
    bootstrap_result = _read_json(bootstrap_result_path.resolve(strict=True))
    request, _single, _replicated, _permit, _execution = _context(
        source_sha=source_sha,
        training_plan=training_plan,
        topology=topology,
        bootstrap_evidence=evidence,
        decision=decision,
        bootstrap_result=bootstrap_result,
        kaggle_dataset_id=kaggle_dataset_id,
        kernel_id=kernel_id,
        wheel_filename=wheel_path.name,
        wheel_sha256=wheel_sha256,
        bootstrap_evidence_sha256=_sha256(bootstrap_evidence_path),
    )
    train_path = _inside(repository_root, repository_root / str(training_plan.dataset.train_path), strict=True)
    validation_path = _inside(
        repository_root,
        repository_root / str(training_plan.dataset.validation_path),
        strict=True,
    )
    if _sha256(train_path) != training_plan.dataset.train_export_digest:
        raise KaggleLivePairError("live-pair train export digest mismatch")
    if _sha256(validation_path) != training_plan.dataset.validation_export_digest:
        raise KaggleLivePairError("live-pair validation export digest mismatch")

    output_root.mkdir(parents=True, exist_ok=True)
    dataset_dir = output_root / "kaggle-dataset"
    kernel_dir = output_root / "kernel"
    output_dir = output_root / "output"
    dataset_dir.mkdir()
    kernel_dir.mkdir()
    output_dir.mkdir()

    copies = {
        request.wheel_filename: wheel_path,
        "bootstrap-evidence.json": bootstrap_evidence_path,
        "bootstrap-result.json": bootstrap_result_path,
        "gap-decision.json": decision_path,
        "holdouts.json": holdouts_path,
        "topology-report.json": topology_report_path,
        "training-plan.json": training_plan_path,
        "train.jsonl": train_path,
        "validation.jsonl": validation_path,
        "workload.json": workload_path,
    }
    for name, source in copies.items():
        shutil.copy2(source.resolve(strict=True), dataset_dir / name)
    request_path = dataset_dir / "live-pair-request.json"
    request_path.write_text(
        json.dumps(request.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    files = {
        path.name: _sha256(path)
        for path in sorted(dataset_dir.iterdir())
        if path.is_file()
    }
    manifest = {
        "files": files,
        "pair_request_digest": request.digest,
        "schema": LIVE_PAIR_BUNDLE_SCHEMA,
        "schema_version": LIVE_PAIR_SCHEMA_VERSION,
        "source_sha": source_sha,
        "wheel_filename": request.wheel_filename,
        "wheel_sha256": request.wheel_sha256,
    }
    _assert_no_secrets(manifest)
    (dataset_dir / "live-pair-bundle-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    dataset_metadata = {
        "description": "Private transient Kodepoia V2.4.5 exact-source live-pair bundle.",
        "id": request.kaggle_dataset_id,
        "licenses": [{"name": "other"}],
        "title": f"Kodepoia V2.4.5 live pair {source_sha[:8]}",
    }
    _assert_no_secrets(dataset_metadata)
    (dataset_dir / "dataset-metadata.json").write_text(
        json.dumps(dataset_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    script = kernel_dir / "run_live_pair.py"
    script.write_text(
        _kernel_script(
            request.wheel_filename,
            request.wheel_sha256,
            source_sha,
            request.digest,
        ),
        encoding="utf-8",
    )
    kernel_manifest = {
        "pair_request_digest": request.digest,
        "schema": "kodepoia.v2.4.5.live-pair-kernel-bundle",
        "schema_version": LIVE_PAIR_SCHEMA_VERSION,
        "script_sha256": _sha256(script),
        "source_sha": source_sha,
    }
    _assert_no_secrets(kernel_manifest)
    (kernel_dir / "kernel-manifest.json").write_text(
        json.dumps(kernel_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    kernel_metadata = {
        "code_file": script.name,
        "competition_sources": [],
        "dataset_sources": [request.kaggle_dataset_id],
        "enable_gpu": True,
        "enable_internet": True,
        "id": request.kernel_id,
        "is_private": True,
        "kernel_sources": [],
        "kernel_type": "script",
        "language": "python",
        "machine_shape": request.requested_shape,
        "model_sources": [],
        "title": request.kernel_id.split("/", 1)[1],
    }
    _assert_no_secrets(kernel_metadata)
    (kernel_dir / "kernel-metadata.json").write_text(
        json.dumps(kernel_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return KaggleLivePairBundle(
        root=output_root,
        dataset_dir=dataset_dir,
        kernel_dir=kernel_dir,
        output_dir=output_dir,
        request=request,
    )


class _FixedCudaSandbox:
    def __init__(self, root: Path, visible_devices: str) -> None:
        self.visible_devices = visible_devices
        self.base = ProcessSandbox(
            root,
            allowed_executables={Path(sys.executable).name},
        )

    def _environment(self) -> dict[str, str]:
        environment = {
            key: os.environ[key]
            for key in _CUDA_ENV_ALLOWLIST
            if key in os.environ
        }
        environment["CUDA_VISIBLE_DEVICES"] = self.visible_devices
        return environment

    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: Mapping[str, str] | None = None,
    ) -> SandboxResult:
        if env not in (None, {}):
            raise KaggleLivePairError("single-GPU runner does not accept caller environment")
        return self.base.run(argv, cwd=cwd, timeout=timeout, env=self._environment())

    def run_process_group(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: Mapping[str, str] | None = None,
    ) -> SandboxResult:
        if env != {"CUDA_VISIBLE_DEVICES": self.visible_devices}:
            raise KaggleLivePairError("distributed runner requested unexpected environment")
        return self.base.run_process_group(
            argv,
            cwd=cwd,
            timeout=timeout,
            env=self._environment(),
        )


def _resource(report: object, name: str) -> float | int | None:
    resources = dict(getattr(report, "resource_maxima"))
    return resources.get(name)


def _checkpoint_integrity(report: object, plan: TrainingPlan) -> bool:
    checkpoints = tuple(getattr(report, "checkpoints"))
    return bool(checkpoints) and any(
        item.step == plan.sft.checkpoint_steps and item.step < plan.sft.max_steps
        for item in checkpoints
    )


def _measurement(
    *,
    strategy_digest: str,
    benchmark_config_digest: str,
    processed_samples: int,
    report: object,
    per_device_peak_vram_bytes: tuple[tuple[int, int], ...],
    plan: TrainingPlan,
) -> StrategyBenchmarkMeasurement:
    wall = _resource(report, "wall_seconds")
    if isinstance(wall, bool) or not isinstance(wall, (int, float)):
        raise KaggleLivePairError("training report is missing wall_seconds")
    state = getattr(report, "state")
    completed = state in {TrainingRunState.COMPLETED, DistributedExecutionState.COMPLETED}
    return StrategyBenchmarkMeasurement(
        strategy_plan_digest=strategy_digest,
        benchmark_config_digest=benchmark_config_digest,
        processed_samples=processed_samples,
        wall_seconds=float(wall),
        eval_loss=getattr(report, "eval_loss"),
        train_loss=getattr(report, "train_loss"),
        per_device_peak_vram_bytes=per_device_peak_vram_bytes,
        run_integrity=bool(completed and not getattr(report, "blockers")),
        checkpoint_integrity=_checkpoint_integrity(report, plan),
    )


def _qualification_request_from_dict(raw: Mapping[str, object]) -> KaggleLiveQualificationRequest:
    return KaggleLiveQualificationRequest(
        source_sha=str(raw["source_sha"]),
        training_plan_digest=str(raw["training_plan_digest"]),
        topology_report_digest=str(raw["topology_report_digest"]),
        topology_digest=str(raw["topology_digest"]),
        single_strategy_plan_digest=str(raw["single_strategy_plan_digest"]),
        replicated_strategy_plan_digest=str(raw["replicated_strategy_plan_digest"]),
        benchmark_report_digest=str(raw["benchmark_report_digest"]),
        execution_plan_digest=str(raw["execution_plan_digest"]),
        recovery_plan_digest=str(raw["recovery_plan_digest"]),
        kernel_id=str(raw["kernel_id"]),
        requested_shape=str(raw.get("requested_shape", "NvidiaTeslaT4")),
        expected_device_count=int(raw.get("expected_device_count", 2)),
    )


def _candidate_evaluation(
    *,
    root: Path,
    plan: TrainingPlan,
    request: KaggleLivePairRequest,
    base_benchmark: Mapping[str, object],
    workload: Mapping[str, object],
    adapter_path: Path,
    adapter_digest: str,
    train_loss: float,
    eval_loss: float,
) -> tuple[dict[str, object], dict[str, object], bool]:
    import gc
    import time

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    local_model = root / request.model_ref
    dedup_policy = DedupPolicy(near_threshold=1.0, lowercase_comparison=False)
    registry = ProtectedHoldoutRegistry(dedup_policy.digest)
    tasks: list[BenchmarkTaskSpec] = []
    for raw in workload["benchmark_tasks"]:  # type: ignore[index]
        if not isinstance(raw, Mapping):
            raise KaggleLivePairError("benchmark task is invalid")
        holdout_id = f"v245-{raw['task_id']}"
        registry.register(ProtectedHoldout.from_text(holdout_id, str(raw["prompt"]), dedup_policy))
        tasks.append(
            BenchmarkTaskSpec(
                task_id=str(raw["task_id"]),
                domain=str(workload["domain"]),
                critical=True,
                prompt=str(raw["prompt"]),
                scorer=ScorerSpec.create(
                    ScorerKind.EXACT,
                    version="v245-1",
                    config={"expected": raw["expected"]},
                ),
                protected_holdout_id=holdout_id,
            )
        )
    suite = BenchmarkSuite(suite_id="v245-live-bootstrap", version="1", tasks=tuple(tasks))
    if canonical_sha256(registry.safe_manifest()) != request.protection_manifest_digest:
        raise KaggleLivePairError("candidate benchmark protection manifest mismatch")

    candidate_ref = f"kodepoia/v245-live-adapter-{request.source_sha[:8]}"
    candidate_digest = canonical_sha256(
        {"adapter_digest": adapter_digest, "base_model_digest": request.model_digest}
    )

    class CandidateClient:
        def __init__(self) -> None:
            self.model = None
            self.tokenizer = None

        def _load(self) -> None:
            if self.model is not None:
                return
            self.tokenizer = AutoTokenizer.from_pretrained(
                local_model,
                local_files_only=True,
                trust_remote_code=False,
            )
            base = AutoModelForCausalLM.from_pretrained(
                local_model,
                local_files_only=True,
                trust_remote_code=False,
                torch_dtype=torch.float16,
                device_map={"": 0},
            )
            self.model = PeftModel.from_pretrained(base, adapter_path.parent, is_trainable=False)
            self.model.eval()

        def preload(self, model: str, **_kwargs: object) -> dict[str, object]:
            if model != candidate_ref:
                raise RuntimeError("unsupported candidate model")
            started = time.perf_counter()
            self._load()
            return {
                "done_reason": "load",
                "load_duration": int((time.perf_counter() - started) * 1_000_000_000),
            }

        def chat(
            self,
            model: str,
            messages: list[object],
            **kwargs: object,
        ) -> BrainResponse:
            if model != candidate_ref:
                raise RuntimeError("unsupported candidate model")
            self._load()
            assert self.model is not None and self.tokenizer is not None
            prompt = str(getattr(messages[-1], "content"))
            options = dict(kwargs.get("options") or {})
            torch.manual_seed(int(options.get("seed", 245)))
            rendered = self.tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}],
                add_generation_prompt=True,
                tokenize=False,
            )
            encoded = self.tokenizer(rendered, return_tensors="pt").to("cuda:0")
            started = time.perf_counter()
            with torch.no_grad():
                output = self.model.generate(
                    **encoded,
                    do_sample=False,
                    max_new_tokens=min(int(options.get("num_predict", 32)), 32),
                    pad_token_id=self.tokenizer.eos_token_id,
                )
            elapsed = time.perf_counter() - started
            generated = output[0][encoded["input_ids"].shape[-1] :]
            answer = self.tokenizer.decode(generated, skip_special_tokens=True).strip()
            return BrainResponse(
                content=answer,
                model=model,
                metrics={
                    "eval_count": int(generated.shape[-1]),
                    "eval_duration": max(1, int(elapsed * 1_000_000_000)),
                },
            )

        def unload(self, model: str) -> None:
            if model != candidate_ref:
                return
            self.model = None
            self.tokenizer = None
            gc.collect()
            torch.cuda.empty_cache()

    report = KodeBenchRunner(CandidateClient()).run(
        [candidate_ref],
        suite,
        config=RunConfig(repeats=2, seed_base=245, temperature=0.0, num_predict=32),
        identities={
            candidate_ref: ModelIdentity(
                model_ref=candidate_ref,
                model_digest=candidate_digest,
                runtime="transformers-peft",
                runtime_version="v245-1",
            )
        },
        holdout_registry=registry,
    )
    candidate_report = {**report.safe_descriptor(), "report_digest": report.digest}
    binding = CandidateBinding(
        candidate_id=f"v245-live-adapter-{request.source_sha[:8]}",
        base_model_ref=request.model_ref,
        base_model_digest=request.model_digest,
        candidate_model_ref=candidate_ref,
        candidate_model_digest=candidate_digest,
        adapter_digest=adapter_digest,
        training_plan_digest=plan.digest,
        dataset_digest=plan.dataset.dataset_digest,
    )
    evaluation = BaseAdapterEvaluator().evaluate(
        base_benchmark,
        candidate_report,
        binding=binding,
        policy=CandidateEvaluationPolicy(target_domains=(str(workload["domain"]),)),
        training_loss=TrainingLossContext(train_loss, eval_loss),
    )
    return candidate_report, evaluation.to_dict(), not evaluation.critical_regressions


def run_live_pair_kernel(dataset_source: Path, work_root: Path) -> None:
    dataset_source = dataset_source.resolve(strict=True)
    work_root = work_root.resolve(strict=False)
    if work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True)
    manifest = _read_json(dataset_source / "live-pair-bundle-manifest.json")
    if manifest.get("schema") != LIVE_PAIR_BUNDLE_SCHEMA:
        raise KaggleLivePairError("live-pair bundle schema mismatch")
    files = manifest.get("files")
    if not isinstance(files, Mapping):
        raise KaggleLivePairError("live-pair bundle file map is invalid")
    for name, expected in files.items():
        source = dataset_source / str(name)
        if (
            not source.is_file()
            or source.is_symlink()
            or _sha256(source) != str(expected)
        ):
            raise KaggleLivePairError(f"live-pair input integrity failure: {name}")
        shutil.copy2(source, work_root / source.name)

    request = KaggleLivePairRequest.from_dict(_read_json(work_root / "live-pair-request.json"))
    if request.digest != manifest.get("pair_request_digest"):
        raise KaggleLivePairError("live-pair request/manifest digest mismatch")
    if _sha256(work_root / "bootstrap-evidence.json") != request.bootstrap_evidence_sha256:
        raise KaggleLivePairError("bootstrap evidence SHA-256 mismatch")
    plan = load_training_plan(work_root / "training-plan.json")
    topology = load_topology_report(work_root / "topology-report.json")
    bootstrap_evidence = _read_json(work_root / "bootstrap-evidence.json")
    decision = _read_json(work_root / "gap-decision.json")
    bootstrap_result = _read_json(work_root / "bootstrap-result.json")
    rebuilt, single, replicated, permit, qualification_execution = _context(
        source_sha=request.source_sha,
        training_plan=plan,
        topology=topology,
        bootstrap_evidence=bootstrap_evidence,
        decision=decision,
        bootstrap_result=bootstrap_result,
        kaggle_dataset_id=request.kaggle_dataset_id,
        kernel_id=request.kernel_id,
        wheel_filename=request.wheel_filename,
        wheel_sha256=request.wheel_sha256,
        bootstrap_evidence_sha256=request.bootstrap_evidence_sha256,
    )
    if rebuilt.digest != request.digest:
        raise KaggleLivePairError("live-pair request reconstruction mismatch")
    if permit.digest != request.qualification_permit_digest:
        raise KaggleLivePairError("qualification permit digest mismatch")
    if qualification_execution.digest != request.qualification_execution_plan_digest:
        raise KaggleLivePairError("qualification execution digest mismatch")

    for key in _HF_ENV_FORBIDDEN:
        os.environ.pop(key, None)

    from huggingface_hub import snapshot_download

    local_model = work_root / request.model_ref
    local_model.parent.mkdir(parents=True, exist_ok=True)
    snapshot = Path(
        snapshot_download(
            repo_id=request.model_ref,
            revision=request.model_revision,
            local_dir=local_model,
            allow_patterns=list(_REQUIRED_MODEL_FILES),
            token=False,
        )
    ).resolve(strict=True)
    if snapshot != local_model.resolve(strict=True):
        raise KaggleLivePairError("pinned model local directory mismatch")
    for name, expected in request.model_snapshot_files:
        path = local_model / name
        if not path.is_file() or path.is_symlink() or _sha256(path) != expected:
            raise KaggleLivePairError(f"pinned model file mismatch: {name}")

    train_target = _inside(work_root, work_root / str(plan.dataset.train_path), strict=False)
    validation_target = _inside(
        work_root,
        work_root / str(plan.dataset.validation_path),
        strict=False,
    )
    train_target.parent.mkdir(parents=True, exist_ok=True)
    validation_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(work_root / "train.jsonl", train_target)
    shutil.copy2(work_root / "validation.jsonl", validation_target)
    if _sha256(train_target) != request.train_export_digest:
        raise KaggleLivePairError("staged train export digest mismatch")
    if _sha256(validation_target) != request.validation_export_digest:
        raise KaggleLivePairError("staged validation export digest mismatch")

    single_report = TrainingRunner(
        work_root,
        sandbox=_FixedCudaSandbox(work_root, "0"),
    ).run(plan)
    if single_report.state is not TrainingRunState.COMPLETED:
        raise KaggleLivePairError(f"single_gpu failed: {single_report.blockers}")

    qualification_report = DistributedTrainingRunner(
        work_root,
        sandbox=_FixedCudaSandbox(work_root, "0,1"),
    ).run_qualification_only(plan, replicated, permit)
    if qualification_report.state is not DistributedExecutionState.COMPLETED:
        raise KaggleLivePairError(
            f"qualification replicated run failed: {qualification_report.blockers}"
        )
    if not isinstance(qualification_report, QualificationOnlyDistributedTrainingReport):
        raise KaggleLivePairError("qualification run returned wrong report type")

    qualification_output = (
        work_root
        / "distributed-runs"
        / qualification_report.run_id
        / "canonical-worker-output.json"
    )
    qualification_canonical = KaggleResultValidator(work_root).validate_external_output(
        plan,
        _read_json(qualification_output),
    )
    single_peak = _resource(single_report, "peak_vram_bytes")
    if (
        isinstance(single_peak, bool)
        or not isinstance(single_peak, (int, float))
        or single_peak <= 0
    ):
        raise KaggleLivePairError("single_gpu peak VRAM is missing or non-positive")
    if any(
        item.peak_vram_bytes is None or item.peak_vram_bytes <= 0
        for item in qualification_report.rank_evidence
    ):
        raise KaggleLivePairError("qualification replicated run lacks concrete per-rank VRAM")
    candidate_peaks = tuple(
        (item.device_ordinal, int(item.peak_vram_bytes))
        for item in qualification_report.rank_evidence
        if item.peak_vram_bytes is not None
    )
    baseline_measurement = _measurement(
        strategy_digest=single.digest,
        benchmark_config_digest=request.benchmark_config_digest,
        processed_samples=request.processed_samples,
        report=single_report,
        per_device_peak_vram_bytes=((0, int(single_peak)),),
        plan=plan,
    )
    candidate_measurement = _measurement(
        strategy_digest=replicated.digest,
        benchmark_config_digest=request.benchmark_config_digest,
        processed_samples=request.processed_samples,
        report=qualification_canonical,
        per_device_peak_vram_bytes=candidate_peaks,
        plan=plan,
    )
    benchmark_report = evaluate_strategy_benchmark(
        single,
        replicated,
        baseline_measurement,
        candidate_measurement,
    )
    benchmark_report.save(work_root / "strategy-benchmark.json")

    if benchmark_report.disposition is not StrategyBenchmarkDisposition.QUALIFIED:
        result = {
            "benchmark_report": benchmark_report.to_dict(),
            "kernel_id": request.kernel_id,
            "pair_request_digest": request.digest,
            "qualification_report": qualification_report.to_dict(),
            "schema": LIVE_PAIR_RESULT_SCHEMA,
            "schema_version": LIVE_PAIR_SCHEMA_VERSION,
            "source_sha": request.source_sha,
            "status": "benchmark_rejected",
        }
        _assert_no_secrets(result)
        (work_root / "live-pair-result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return

    normal_report = DistributedTrainingRunner(
        work_root,
        sandbox=_FixedCudaSandbox(work_root, "0,1"),
    ).run(plan, replicated, benchmark_report)
    if normal_report.state is not DistributedExecutionState.COMPLETED:
        raise KaggleLivePairError(f"qualified replicated run failed: {normal_report.blockers}")
    normal_execution = build_distributed_execution_plan(plan, replicated, benchmark_report)
    if normal_report.execution_plan_digest != normal_execution.digest:
        raise KaggleLivePairError("normal distributed execution lineage mismatch")
    normal_output = (
        work_root
        / "distributed-runs"
        / normal_report.run_id
        / "canonical-worker-output.json"
    )
    normal_canonical = KaggleResultValidator(work_root).validate_external_output(
        plan,
        _read_json(normal_output),
    )
    if any(
        item.peak_vram_bytes is None or item.peak_vram_bytes <= 0
        for item in normal_report.rank_evidence
    ):
        raise KaggleLivePairError("qualified replicated run lacks concrete per-rank VRAM")
    normal_peaks = tuple(
        (item.device_ordinal, int(item.peak_vram_bytes))
        for item in normal_report.rank_evidence
        if item.peak_vram_bytes is not None
    )
    normal_measurement = _measurement(
        strategy_digest=replicated.digest,
        benchmark_config_digest=request.benchmark_config_digest,
        processed_samples=request.processed_samples,
        report=normal_canonical,
        per_device_peak_vram_bytes=normal_peaks,
        plan=plan,
    )

    checkpoint_matches = tuple(
        item
        for item in normal_canonical.checkpoints
        if item.step == plan.sft.checkpoint_steps and item.step < plan.sft.max_steps
    )
    if len(checkpoint_matches) != 1:
        raise KaggleLivePairError(
            "qualified replicated run must contain exactly one validated recovery checkpoint"
        )
    checkpoint_id = checkpoint_matches[0].checkpoint_id
    checkpoint_manifest = build_distributed_checkpoint_manifest(
        work_root,
        plan,
        replicated,
        benchmark_report,
        normal_report,
        checkpoint_id=checkpoint_id,
    )
    recovery_plan = build_distributed_recovery_plan(
        plan,
        replicated,
        benchmark_report,
        checkpoint_manifest,
    )
    checkpoint_manifest.save(work_root / "distributed-checkpoint-manifest.json")
    recovery_plan.save(work_root / "distributed-recovery-plan.json")

    workload = _read_json(work_root / "workload.json")
    base_benchmark = bootstrap_evidence.get("benchmark")
    if not isinstance(base_benchmark, Mapping):
        raise KaggleLivePairError("bootstrap base benchmark is missing")
    if normal_report.adapter_path is None or normal_report.adapter_digest is None:
        raise KaggleLivePairError("normal distributed run lacks adapter evidence")
    adapter_path = _inside(work_root, work_root / normal_report.adapter_path, strict=True)
    candidate_report, candidate_evaluation, critical_pass = _candidate_evaluation(
        root=work_root,
        plan=plan,
        request=request,
        base_benchmark=base_benchmark,
        workload=workload,
        adapter_path=adapter_path,
        adapter_digest=normal_report.adapter_digest,
        train_loss=float(normal_report.train_loss or 0.0),
        eval_loss=float(normal_report.eval_loss or 0.0),
    )

    qualification_request = KaggleLiveQualificationRequest(
        source_sha=request.source_sha,
        training_plan_digest=plan.digest,
        topology_report_digest=topology.digest,
        topology_digest=str(topology.topology_digest),
        single_strategy_plan_digest=single.digest,
        replicated_strategy_plan_digest=replicated.digest,
        benchmark_report_digest=benchmark_report.digest,
        execution_plan_digest=normal_execution.digest,
        recovery_plan_digest=recovery_plan.digest,
        kernel_id=request.kernel_id,
    )
    evidence = {
        "benchmark": benchmark_report.to_dict(),
        "candidate_benchmark": candidate_report,
        "candidate_evaluation": candidate_evaluation,
        "critical_regression_pass": critical_pass,
        "download_revalidated": False,
        "provider": {
            "authenticated": False,
            "kernel_id": request.kernel_id,
            "private_kernel": True,
            "requested_shape": request.requested_shape,
        },
        "qualification_candidate": {
            "measurement": candidate_measurement.to_dict(),
            "report": qualification_report.to_dict(),
        },
        "qualification_request": qualification_request.to_dict(),
        "recovery_plan_digest": recovery_plan.digest,
        "request_digest": qualification_request.digest,
        "runs": {
            "single_gpu": {
                **baseline_measurement.to_dict(),
                "effective_global_batch_size": single.effective_global_batch_size,
                "state": "completed",
                "strategy": "single_gpu",
                "topology_digest": topology.topology_digest,
                "training_plan_digest": plan.digest,
            },
            "replicated_data_parallel": {
                **normal_measurement.to_dict(),
                "effective_global_batch_size": replicated.effective_global_batch_size,
                "execution_plan_digest": normal_execution.digest,
                "rank_evidence": [item.to_dict() for item in normal_report.rank_evidence],
                "state": "completed",
                "strategy": "replicated_data_parallel",
                "topology_digest": topology.topology_digest,
                "training_plan_digest": plan.digest,
            },
        },
        "schema": LIVE_PAIR_EVIDENCE_SCHEMA,
        "schema_version": LIVE_PAIR_SCHEMA_VERSION,
        "secret_scan_pass": False,
        "source_sha": request.source_sha,
        "topology": topology.observed.to_dict() if topology.observed is not None else {},
    }
    _assert_no_secrets(evidence)
    evidence_path = work_root / "live-pair-evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = {
        "benchmark_report_digest": benchmark_report.digest,
        "evidence_sha256": _sha256(evidence_path),
        "execution_plan_digest": normal_execution.digest,
        "kernel_id": request.kernel_id,
        "pair_request_digest": request.digest,
        "qualification_request_digest": qualification_request.digest,
        "recovery_plan_digest": recovery_plan.digest,
        "schema": LIVE_PAIR_RESULT_SCHEMA,
        "schema_version": LIVE_PAIR_SCHEMA_VERSION,
        "source_sha": request.source_sha,
        "status": "completed",
    }
    (work_root / "live-pair-result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class KaggleLivePairClient:
    def __init__(
        self,
        *,
        runner: CommandRunner | None = None,
        kaggle_executable: str | None = None,
    ) -> None:
        self.runner = runner or SubprocessCommandRunner()
        self.kaggle_executable = kaggle_executable or shutil.which("kaggle") or "kaggle"

    def upload_private_dataset(self, bundle: KaggleLivePairBundle) -> CommandResult:
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

    def dataset_status(self, bundle: KaggleLivePairBundle) -> CommandResult:
        return self._checked(
            [
                self.kaggle_executable,
                "datasets",
                "status",
                bundle.request.kaggle_dataset_id,
                "--format",
                "json",
            ],
            timeout=120.0,
        )

    def push(self, bundle: KaggleLivePairBundle) -> CommandResult:
        metadata = _read_json(bundle.kernel_dir / "kernel-metadata.json")
        manifest = _read_json(bundle.kernel_dir / "kernel-manifest.json")
        script = bundle.kernel_dir / str(metadata.get("code_file", ""))
        if metadata.get("is_private") is not True:
            raise KaggleLivePairError("live-pair kernel must be private")
        if (
            manifest.get("source_sha") != bundle.request.source_sha
            or manifest.get("pair_request_digest") != bundle.request.digest
            or not script.is_file()
            or script.is_symlink()
            or manifest.get("script_sha256") != _sha256(script)
        ):
            raise KaggleLivePairError("live-pair kernel manifest integrity mismatch")
        return self._checked(
            [self.kaggle_executable, "kernels", "push", "--path", str(bundle.kernel_dir)],
            timeout=300.0,
        )

    def status(self, bundle: KaggleLivePairBundle) -> CommandResult:
        return self._checked(
            [self.kaggle_executable, "kernels", "status", bundle.request.kernel_id],
            timeout=120.0,
        )

    def fetch_and_validate(self, bundle: KaggleLivePairBundle) -> dict[str, object]:
        output = bundle.output_dir
        if output.exists() and any(output.iterdir()):
            raise KaggleLivePairError("live-pair output directory must be empty before fetch")
        output.mkdir(parents=True, exist_ok=True)
        self._checked(
            [
                self.kaggle_executable,
                "kernels",
                "output",
                bundle.request.kernel_id,
                "--path",
                str(output),
                "--quiet",
            ],
            timeout=3600.0,
        )
        results = list(output.rglob("live-pair-result.json"))
        if len(results) != 1:
            raise KaggleLivePairError("downloaded output must contain exactly one live-pair-result.json")
        result = _read_json(results[0])
        if result.get("source_sha") != bundle.request.source_sha:
            raise KaggleLivePairError("downloaded live-pair source SHA mismatch")
        if result.get("pair_request_digest") != bundle.request.digest:
            raise KaggleLivePairError("downloaded live-pair request digest mismatch")
        if result.get("kernel_id") != bundle.request.kernel_id:
            raise KaggleLivePairError("downloaded live-pair kernel identity mismatch")
        if result.get("status") != "completed":
            return {"result": result, "production_qualified": False}

        evidence_paths = list(output.rglob("live-pair-evidence.json"))
        if len(evidence_paths) != 1:
            raise KaggleLivePairError("completed live pair must contain exactly one evidence file")
        evidence_path = evidence_paths[0]
        if _sha256(evidence_path) != result.get("evidence_sha256"):
            raise KaggleLivePairError("downloaded live-pair evidence SHA mismatch")
        evidence = _read_json(evidence_path)
        _assert_no_secrets(evidence)
        request_raw = evidence.get("qualification_request")
        if not isinstance(request_raw, Mapping):
            raise KaggleLivePairError("downloaded qualification request is missing")
        qualification_request = _qualification_request_from_dict(request_raw)
        if qualification_request.digest != evidence.get("request_digest"):
            raise KaggleLivePairError("downloaded qualification request digest mismatch")
        if qualification_request.source_sha != bundle.request.source_sha:
            raise KaggleLivePairError("downloaded qualification request source mismatch")
        if qualification_request.kernel_id != bundle.request.kernel_id:
            raise KaggleLivePairError("downloaded qualification request kernel mismatch")

        provider = evidence.get("provider")
        if not isinstance(provider, dict):
            raise KaggleLivePairError("downloaded provider evidence is invalid")
        provider["authenticated"] = True
        evidence["download_revalidated"] = True
        evidence["secret_scan_pass"] = True
        _assert_no_secrets(evidence)
        report = validate_live_evidence(qualification_request, evidence)
        final_payload = {
            "downloaded_evidence_sha256": _sha256(evidence_path),
            "evidence": evidence,
            "live_report": report,
            "pair_result": result,
        }
        (output / "downloaded-live-pair-validation.json").write_text(
            json.dumps(final_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return final_payload

    def _checked(self, argv: list[str], *, timeout: float) -> CommandResult:
        result = self.runner.run(argv, timeout=timeout)
        if result.returncode != 0:
            raise KaggleLivePairError(
                f"Kaggle CLI live-pair command failed ({result.returncode}): "
                f"{result.stderr.strip()[:4096]}"
            )
        return result


__all__ = [
    "KaggleLivePairBundle",
    "KaggleLivePairClient",
    "KaggleLivePairError",
    "KaggleLivePairRequest",
    "LIVE_PAIR_BUNDLE_SCHEMA",
    "LIVE_PAIR_EVIDENCE_SCHEMA",
    "LIVE_PAIR_REQUEST_SCHEMA",
    "build_live_pair_bundle",
    "load_topology_report",
    "run_live_pair_kernel",
]
