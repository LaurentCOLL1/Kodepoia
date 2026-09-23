from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from kodepoia.bench import (
    BackendCapability,
    BudgetStatus,
    DecisionDisposition,
    DecisionEvidence,
    DiagnosticComponent,
    DiagnosticProbe,
    ExpectedImpact,
    GapDecision,
    GapDecisionEngine,
    ProbeStatus,
)
from kodepoia.experience import (
    ContaminationReport,
    ContentRef,
    DatasetBuild,
    DatasetBuilder,
    DatasetFormat,
    DatasetPolicy,
    DatasetSource,
    DedupItem,
    DedupPolicy,
    ExperienceId,
    ExperienceRecord,
    ExperienceState,
    OutcomeLabel,
    PolicyDecision,
    ProtectedHoldout,
    ProtectedHoldoutRegistry,
    ProvenanceDescriptor,
    SanitizationEvidence,
    SanitizationStatus,
    TransformationRef,
    cluster_items,
    fingerprint_text,
    scan_contamination,
)
from kodepoia.experience import (
    TrainingAuthorization as ExperienceTrainingAuthorization,
)

from .contracts import QuantizationMode, ResourceRequest, SeedConfig, canonical_sha256
from .kaggle_remote import (
    CommandResult,
    SubprocessCommandRunner,
    save_training_plan,
)
from .training import (
    DatasetBinding,
    LoraTrainingConfig,
    ModelBinding,
    SFTTrainingConfig,
    TrainingAuthorization,
    TrainingMode,
    TrainingPlan,
)

BOOTSTRAP_REQUEST_SCHEMA = "kodepoia.v2.4.5.live-bootstrap-request"
BOOTSTRAP_EVIDENCE_SCHEMA = "kodepoia.v2.4.5.live-bootstrap-evidence"
BOOTSTRAP_RESULT_SCHEMA = "kodepoia.v2.4.5.live-bootstrap-result"
BOOTSTRAP_SCHEMA_VERSION = 1
WORKLOAD_SCHEMA = "kodepoia.v2.4.5.live-qualification-workload"
WORKLOAD_RELATIVE_PATH = Path("qualification/v2_4_5/live_workload.json")

QUALIFICATION_MODEL_REF = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
QUALIFICATION_MODEL_REVISION = "fe8a4ea1ffedaf415f4da2f062534de366a451e6"
QUALIFICATION_MODEL_LICENSE = "apache-2.0"
QUALIFICATION_MODEL_FILE_SHA256 = (
    "6e6001da2106d4757498752a021df6c2bdc332c650aae4bae6b0c004dcf14933"
)
QUALIFICATION_CONTROL_REF = "kodepoia/v245-qualification-control"
QUALIFICATION_DATASET_LICENSE = "LicenseRef-Kodepoia-Internal-Qualification"
QUALIFICATION_SHAPE = "NvidiaTeslaT4"

_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_KAGGLE_ID = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_-]{1,49}/[a-z0-9][a-z0-9-]{1,49}$"
)
_WHEEL_DISTRIBUTION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._]*$")
_WHEEL_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._!+]*$")
_WHEEL_BUILD = re.compile(r"^[0-9][A-Za-z0-9._]*$")
_WHEEL_TAG = re.compile(r"^[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*$")
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
_SANITIZER_DIGEST = canonical_sha256(
    {"kind": "repository-owned-v245-qualification-sanitizer", "version": 1}
)
_GOVERNANCE_DIGEST = canonical_sha256(
    {"kind": "repository-owned-v245-qualification-governance", "version": 1}
)


class KaggleLiveBootstrapError(RuntimeError):
    """Raised when the bounded V2.4.5 live-workload bootstrap is invalid."""


class BootstrapCommandRunner(Protocol):
    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 120.0,
    ) -> CommandResult: ...


@dataclass(frozen=True, slots=True)
class LiveQualificationDataset:
    root: Path
    workload_path: Path
    manifest_path: Path
    train_path: Path
    validation_path: Path
    contamination_path: Path
    holdouts_path: Path
    build: DatasetBuild
    workload_digest: str
    contamination_digest: str
    protection_manifest_digest: str
    dedup_policy_digest: str

    @property
    def train_rows(self) -> int:
        return int(self.build.manifest.split_stats["train"]["rows"])

    @property
    def validation_rows(self) -> int:
        return int(self.build.manifest.split_stats["validation"]["rows"])


@dataclass(frozen=True, slots=True)
class KaggleLiveBootstrapRequest:
    source_sha: str
    kaggle_dataset_id: str
    kernel_id: str
    dataset_digest: str
    dataset_manifest_digest: str
    train_export_digest: str
    validation_export_digest: str
    workload_digest: str
    contamination_digest: str
    protection_manifest_digest: str
    dedup_policy_digest: str
    wheel_filename: str
    wheel_sha256: str

    def __post_init__(self) -> None:
        source_sha = self.source_sha.strip().lower()
        if _GIT_SHA.fullmatch(source_sha) is None:
            raise KaggleLiveBootstrapError(
                "source_sha must be 40 lowercase hexadecimal characters"
            )
        object.__setattr__(self, "source_sha", source_sha)
        for label in ("kaggle_dataset_id", "kernel_id"):
            if _KAGGLE_ID.fullmatch(getattr(self, label)) is None:
                raise KaggleLiveBootstrapError(
                    f"{label} must be an exact owner/lowercase-slug identifier"
                )
        for label in (
            "dataset_digest",
            "dataset_manifest_digest",
            "train_export_digest",
            "validation_export_digest",
            "workload_digest",
            "contamination_digest",
            "protection_manifest_digest",
            "dedup_policy_digest",
        ):
            if _SHA256.fullmatch(getattr(self, label)) is None:
                raise KaggleLiveBootstrapError(
                    f"{label} must be 64 lowercase hexadecimal characters"
                )
        _validated_wheel_filename(self.wheel_filename)
        if _SHA256.fullmatch(self.wheel_sha256) is None:
            raise KaggleLiveBootstrapError(
                "wheel_sha256 must be 64 lowercase hexadecimal characters"
            )

    def descriptor(self) -> dict[str, object]:
        return {
            "contamination_digest": self.contamination_digest,
            "dataset_digest": self.dataset_digest,
            "dataset_manifest_digest": self.dataset_manifest_digest,
            "dedup_policy_digest": self.dedup_policy_digest,
            "expected_device_count": 2,
            "expected_model_file_sha256": QUALIFICATION_MODEL_FILE_SHA256,
            "kaggle_dataset_id": self.kaggle_dataset_id,
            "kernel_id": self.kernel_id,
            "model_license": QUALIFICATION_MODEL_LICENSE,
            "model_ref": QUALIFICATION_MODEL_REF,
            "model_revision": QUALIFICATION_MODEL_REVISION,
            "promotion_authorized": False,
            "protection_manifest_digest": self.protection_manifest_digest,
            "requested_shape": QUALIFICATION_SHAPE,
            "schema": BOOTSTRAP_REQUEST_SCHEMA,
            "schema_version": BOOTSTRAP_SCHEMA_VERSION,
            "source_sha": self.source_sha,
            "train_export_digest": self.train_export_digest,
            "validation_export_digest": self.validation_export_digest,
            "wheel_filename": self.wheel_filename,
            "wheel_sha256": self.wheel_sha256,
            "workload_digest": self.workload_digest,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.descriptor())

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "request_digest": self.digest}


@dataclass(frozen=True, slots=True)
class KaggleLiveBootstrapBundle:
    root: Path
    governed_dataset: LiveQualificationDataset
    kaggle_dataset_dir: Path
    kernel_dir: Path
    output_dir: Path
    request: KaggleLiveBootstrapRequest


@dataclass(frozen=True, slots=True)
class KaggleLiveBootstrapResult:
    decision: GapDecision
    training_plan: TrainingPlan | None
    decision_path: Path
    training_plan_path: Path | None
    result_path: Path

    @property
    def train_authorized(self) -> bool:
        return (
            self.decision.disposition is DecisionDisposition.TRAIN
            and self.training_plan is not None
        )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _assert_no_secret_fields(payload: object) -> None:
    def visit(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).lower() in _SECRET_KEYS:
                    raise KaggleLiveBootstrapError(
                        "live bootstrap evidence must not contain secret fields"
                    )
                visit(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                visit(item)

    visit(payload)


def _inside(root: Path, path: Path, *, strict: bool) -> Path:
    resolved_root = root.resolve(strict=True)
    resolved = path.resolve(strict=strict)
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise KaggleLiveBootstrapError("path escapes repository root")
    return resolved


def _safe_text(label: str, value: object, *, maximum: int = 1024) -> str:
    if not isinstance(value, str):
        raise KaggleLiveBootstrapError(f"{label} must be a string")
    text = value.strip()
    if not text or len(text) > maximum or "\x00" in text:
        raise KaggleLiveBootstrapError(f"{label} must be a bounded non-empty string")
    return text


def _safe_id(label: str, value: object) -> str:
    text = _safe_text(label, value, maximum=128)
    if _SAFE_ID.fullmatch(text) is None:
        raise KaggleLiveBootstrapError(f"{label} must be a stable safe identifier")
    return text


def _validated_wheel_filename(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 255
        or "\x00" in value
        or "/" in value
        or "\\" in value
        or not value.endswith(".whl")
    ):
        raise KaggleLiveBootstrapError(
            "wheel_path must preserve a valid wheel filename"
        )
    parts = value[:-4].split("-")
    if len(parts) not in (5, 6):
        raise KaggleLiveBootstrapError(
            "wheel_path must preserve a valid wheel filename"
        )
    distribution, version = parts[:2]
    build = parts[2] if len(parts) == 6 else None
    python_tag, abi_tag, platform_tag = parts[-3:]
    if (
        _WHEEL_DISTRIBUTION.fullmatch(distribution) is None
        or _WHEEL_VERSION.fullmatch(version) is None
        or (build is not None and _WHEEL_BUILD.fullmatch(build) is None)
        or _WHEEL_TAG.fullmatch(python_tag) is None
        or _WHEEL_TAG.fullmatch(abi_tag) is None
        or _WHEEL_TAG.fullmatch(platform_tag) is None
    ):
        raise KaggleLiveBootstrapError(
            "wheel_path must preserve a valid wheel filename"
        )
    return value


def _load_workload(repository_root: Path) -> tuple[Path, dict[str, object], str]:
    root = repository_root.resolve(strict=True)
    path = _inside(root, root / WORKLOAD_RELATIVE_PATH, strict=True)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise KaggleLiveBootstrapError("qualification workload must be a JSON object")
    if payload.get("schema") != WORKLOAD_SCHEMA or payload.get("schema_version") != 1:
        raise KaggleLiveBootstrapError("unsupported qualification workload schema")
    domain = _safe_id("workload domain", payload.get("domain"))
    task = _safe_id("workload task", payload.get("task"))
    license_expression = _safe_text(
        "workload license_expression",
        payload.get("license_expression"),
        maximum=256,
    )
    if license_expression != QUALIFICATION_DATASET_LICENSE:
        raise KaggleLiveBootstrapError("qualification workload license is not authorized")
    training = payload.get("training_examples")
    benchmarks = payload.get("benchmark_tasks")
    if not isinstance(training, list) or not 8 <= len(training) <= 128:
        raise KaggleLiveBootstrapError(
            "qualification workload must contain 8 to 128 training examples"
        )
    if not isinstance(benchmarks, list) or not 2 <= len(benchmarks) <= 16:
        raise KaggleLiveBootstrapError(
            "qualification workload must contain 2 to 16 benchmark tasks"
        )
    seen_ids: set[str] = set()
    training_prompts: set[str] = set()
    for item in training:
        if not isinstance(item, dict):
            raise KaggleLiveBootstrapError("training examples must be objects")
        item_id = _safe_id("training id", item.get("id"))
        if item_id in seen_ids:
            raise KaggleLiveBootstrapError("training example ids must be unique")
        seen_ids.add(item_id)
        prompt = _safe_text("training prompt", item.get("prompt"))
        _safe_text("training completion", item.get("completion"))
        if prompt in training_prompts:
            raise KaggleLiveBootstrapError("training prompts must be unique")
        training_prompts.add(prompt)
    benchmark_ids: set[str] = set()
    for item in benchmarks:
        if not isinstance(item, dict):
            raise KaggleLiveBootstrapError("benchmark tasks must be objects")
        task_id = _safe_id("benchmark task_id", item.get("task_id"))
        if task_id in benchmark_ids:
            raise KaggleLiveBootstrapError("benchmark task ids must be unique")
        benchmark_ids.add(task_id)
        prompt = _safe_text("benchmark prompt", item.get("prompt"))
        _safe_text("benchmark expected", item.get("expected"))
        if prompt in training_prompts:
            raise KaggleLiveBootstrapError(
                "benchmark prompt must not appear in training examples"
            )
        if item.get("critical") is not True:
            raise KaggleLiveBootstrapError(
                "all V2.4.5 qualification benchmark tasks must be critical"
            )
    normalized = {
        "benchmark_tasks": benchmarks,
        "domain": domain,
        "license_expression": license_expression,
        "schema": WORKLOAD_SCHEMA,
        "schema_version": 1,
        "task": task,
        "training_examples": training,
    }
    return path, normalized, canonical_sha256(normalized)


def _qualification_sources(
    workload: dict[str, object],
    workload_digest: str,
) -> list[DatasetSource]:
    workspace_id = "v245-qualification"
    project_id = "v245-qualification"
    domain = str(workload["domain"])
    task = str(workload["task"])
    sources: list[DatasetSource] = []
    for raw in workload["training_examples"]:  # type: ignore[index]
        item = dict(raw)
        item_id = str(item["id"])
        payload = json.dumps(
            {"completion": item["completion"], "prompt": item["prompt"]},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        encoded = payload.encode("utf-8")
        content_digest = _sha256_bytes(encoded)
        source_id = f"v245-{item_id}"
        origin_digest = canonical_sha256(
            {
                "kind": "repository-owned-v245-qualification-example",
                "source_id": source_id,
                "workload_digest": workload_digest,
            }
        )
        experience_id = ExperienceId.derive(
            workspace_id=workspace_id,
            source_id=source_id,
            origin_digest=origin_digest,
        )
        record = ExperienceRecord(
            experience_id=experience_id,
            workspace_id=workspace_id,
            project_id=project_id,
            task_label=task,
            domain_label=domain,
            state=ExperienceState.CURATED,
            outcome=OutcomeLabel.ACCEPTED,
            content=ContentRef(
                workspace_id=workspace_id,
                storage_key=(
                    f"qualification/v2_4_5/{experience_id.value}/"
                    f"{content_digest}.json"
                ),
                sha256=content_digest,
                byte_length=len(encoded),
                media_type="application/json",
            ),
            provenance=ProvenanceDescriptor(
                source_type="repository_qualification",
                source_id=source_id,
                origin_digest=origin_digest,
                project_scope=project_id,
                license_expression=QUALIFICATION_DATASET_LICENSE,
            ),
            authorization=ExperienceTrainingAuthorization(
                source_scope=PolicyDecision.ALLOW,
                consent=PolicyDecision.ALLOW,
                provenance=PolicyDecision.ALLOW,
                license=PolicyDecision.ALLOW,
                privacy=PolicyDecision.ALLOW,
            ),
            sanitization=SanitizationEvidence(
                status=SanitizationStatus.PASSED,
                sanitizer_digest=_SANITIZER_DIGEST,
            ),
            transformations=(
                TransformationRef(
                    transformation_id="r15.3-sanitize-v1",
                    input_digest=origin_digest,
                    output_digest=content_digest,
                    policy_digest=_GOVERNANCE_DIGEST,
                ),
            ),
        )
        sources.append(
            DatasetSource(
                record=record,
                text=payload,
                format=DatasetFormat.PROMPT_COMPLETION,
                language="en",
            )
        )
    return sources


def _dedup_and_holdouts(
    workload: dict[str, object],
    sources: list[DatasetSource],
) -> tuple[
    DedupPolicy,
    object,
    ContaminationReport,
    ProtectedHoldoutRegistry,
]:
    policy = DedupPolicy(near_threshold=1.0, lowercase_comparison=False)
    items = [
        DedupItem(
            item_id=source.item_id,
            content_digest=source.record.content.sha256,
            fingerprint=fingerprint_text(source.text, policy),
        )
        for source in sources
    ]
    dedup = cluster_items(items, policy)
    registry = ProtectedHoldoutRegistry(policy.digest)
    for raw in workload["benchmark_tasks"]:  # type: ignore[index]
        item = dict(raw)
        registry.register(
            ProtectedHoldout.from_text(
                f"v245-{item['task_id']}",
                str(item["prompt"]),
                policy,
            )
        )
    contamination = scan_contamination(items, dedup, registry, policy)
    if contamination.findings or contamination.contaminated_group_ids:
        raise KaggleLiveBootstrapError(
            "repository-owned qualification workload overlaps protected holdouts"
        )
    return policy, dedup, contamination, registry


def build_live_qualification_dataset(
    repository_root: Path,
    output_root: Path,
) -> LiveQualificationDataset:
    repository_root = repository_root.resolve(strict=True)
    output_root = _inside(repository_root, output_root, strict=False)
    if output_root.exists() and any(output_root.iterdir()):
        raise KaggleLiveBootstrapError(
            f"qualification dataset directory is not empty: {output_root}"
        )
    output_root.mkdir(parents=True, exist_ok=True)
    workload_path, workload, workload_digest = _load_workload(repository_root)
    sources = _qualification_sources(workload, workload_digest)
    dedup_policy, dedup, contamination, registry = _dedup_and_holdouts(
        workload,
        sources,
    )

    selected: DatasetBuild | None = None
    for seed in range(256):
        policy = DatasetPolicy(
            seed=seed,
            sanitizer_digest=_SANITIZER_DIGEST,
            governance_policy_digest=_GOVERNANCE_DIGEST,
            dedup_policy_digest=dedup_policy.digest,
            train_weight=4,
            validation_weight=1,
            test_weight=0,
            allowed_domains=(str(workload["domain"]),),
            allowed_tasks=(str(workload["task"]),),
        )
        candidate = DatasetBuilder(policy).build(
            sources,
            dedup=dedup,  # type: ignore[arg-type]
            contamination=contamination,
            intended_use=(
                "Private V2.4.5 live-qualification QLoRA throughput and "
                "lineage validation only."
            ),
            limitations=(
                "Repository-owned synthetic qualification workload only.",
                "Not authorized for product model promotion or public upload.",
                "Protected benchmark holdouts are excluded by R15.4 contamination checks.",
            ),
        )
        train_rows = int(candidate.manifest.split_stats["train"]["rows"])
        validation_rows = int(candidate.manifest.split_stats["validation"]["rows"])
        if train_rows >= 8 and validation_rows >= 2:
            selected = candidate
            break
    if selected is None:
        raise KaggleLiveBootstrapError(
            "unable to derive a bounded train/validation split for qualification"
        )
    for name, value in selected.repository_file_map().items():
        target = output_root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)

    contamination_payload = contamination.safe_descriptor()
    holdouts_payload = registry.safe_manifest()
    _write_json(output_root / "contamination.json", contamination_payload)
    _write_json(output_root / "holdouts.json", holdouts_payload)
    shutil.copy2(workload_path, output_root / "workload.json")
    manifest_path = output_root / "manifest.json"
    train_path = output_root / "train.jsonl"
    validation_path = output_root / "validation.jsonl"
    if not train_path.is_file() or not validation_path.is_file():
        raise KaggleLiveBootstrapError(
            "governed qualification dataset is missing train or validation export"
        )
    return LiveQualificationDataset(
        root=output_root,
        workload_path=output_root / "workload.json",
        manifest_path=manifest_path,
        train_path=train_path,
        validation_path=validation_path,
        contamination_path=output_root / "contamination.json",
        holdouts_path=output_root / "holdouts.json",
        build=selected,
        workload_digest=workload_digest,
        contamination_digest=canonical_sha256(contamination_payload),
        protection_manifest_digest=canonical_sha256(holdouts_payload),
        dedup_policy_digest=dedup_policy.digest,
    )


def _bootstrap_kernel_script() -> str:
    return r'''from __future__ import annotations

import gc
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from importlib.metadata import version
from pathlib import Path


MODEL_REF = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
MODEL_REVISION = "fe8a4ea1ffedaf415f4da2f062534de366a451e6"
MODEL_LICENSE = "apache-2.0"
MODEL_FILE_SHA256 = "6e6001da2106d4757498752a021df6c2bdc332c650aae4bae6b0c004dcf14933"
CONTROL_REF = "kodepoia/v245-qualification-control"
REQUIRED_FILES = (
    "config.json",
    "model.safetensors",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer.model",
    "tokenizer_config.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validated_wheel_filename(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 255
        or "\x00" in value
        or "/" in value
        or "\\" in value
        or not value.endswith(".whl")
    ):
        raise SystemExit("Bootstrap wheel filename is invalid")
    parts = value[:-4].split("-")
    if len(parts) not in (5, 6):
        raise SystemExit("Bootstrap wheel filename is invalid")
    distribution, version = parts[:2]
    build = parts[2] if len(parts) == 6 else None
    python_tag, abi_tag, platform_tag = parts[-3:]
    if (
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._]*", distribution) is None
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._!+]*", version) is None
        or (
            build is not None
            and re.fullmatch(r"[0-9][A-Za-z0-9._]*", build) is None
        )
        or re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*", python_tag)
        is None
        or re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*", abi_tag)
        is None
        or re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*", platform_tag)
        is None
    ):
        raise SystemExit("Bootstrap wheel filename is invalid")
    return value


input_root = Path("/kaggle/input")
manifests = list(input_root.rglob("bootstrap-bundle-manifest.json"))
if len(manifests) != 1:
    raise SystemExit(f"Expected one bootstrap manifest, found {len(manifests)}")
source = manifests[0].parent
manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
if (
    manifest.get("schema") != "kodepoia.v2.4.5.live-bootstrap-bundle"
    or manifest.get("schema_version") != 1
):
    raise SystemExit("Bootstrap manifest schema is invalid")
files = manifest.get("files")
if not isinstance(files, dict):
    raise SystemExit("Bootstrap manifest files are invalid")
wheel_filename = validated_wheel_filename(manifest.get("wheel_filename"))
expected_files = {
    "bootstrap-request.json",
    "contamination.json",
    "holdouts.json",
    "manifest.json",
    "workload.json",
    wheel_filename,
}
if set(files) != expected_files:
    raise SystemExit("Bootstrap manifest file set is invalid")
for name in sorted(expected_files):
    expected = files.get(name)
    path = source / name
    if (
        not isinstance(expected, str)
        or re.fullmatch(r"[0-9a-f]{64}", expected) is None
        or not path.is_file()
        or sha256(path) != expected
    ):
        raise SystemExit(f"Bootstrap bundle integrity failure: {name}")

request = json.loads((source / "bootstrap-request.json").read_text(encoding="utf-8"))
if request.get("request_digest") != manifest.get("request_digest"):
    raise SystemExit("Bootstrap request identity mismatch")
if (
    request.get("wheel_filename") != wheel_filename
    or request.get("wheel_sha256") != manifest.get("wheel_sha256")
    or manifest.get("wheel_sha256") != files[wheel_filename]
):
    raise SystemExit("Bootstrap wheel identity mismatch")

work = Path("/kaggle/working/kodepoia-v245-bootstrap")
if work.exists():
    shutil.rmtree(work)
work.mkdir(parents=True)
for name in sorted(expected_files):
    shutil.copy2(source / name, work / name)

wheel = work / wheel_filename
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

import torch
from huggingface_hub import HfApi, snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer

from kodepoia.bench import (
    BenchmarkSuite,
    BenchmarkTaskSpec,
    KodeBenchRunner,
    ModelIdentity,
    RunConfig,
    ScorerKind,
    ScorerSpec,
)
from kodepoia.brain.base import BrainResponse
from kodepoia.experience import (
    DedupPolicy,
    ProtectedHoldout,
    ProtectedHoldoutRegistry,
)
from kodepoia.tuning.contracts import (
    DTypeName,
    QuantizationMode,
    ResourceRequest,
    RuntimeRequest,
    TrainingBackend,
    canonical_sha256,
)
from kodepoia.tuning.runtime import TrainingRuntime


workload = json.loads((work / "workload.json").read_text(encoding="utf-8"))
if request["model_ref"] != MODEL_REF or request["model_revision"] != MODEL_REVISION:
    raise SystemExit("Bootstrap model identity is not repository-authorized")
if request["model_license"] != MODEL_LICENSE:
    raise SystemExit("Bootstrap model licence expectation mismatch")
if request["expected_model_file_sha256"] != MODEL_FILE_SHA256:
    raise SystemExit("Bootstrap model checksum expectation mismatch")

info = HfApi().model_info(MODEL_REF, revision=MODEL_REVISION)
card_data = getattr(info, "card_data", None)
observed_license = getattr(card_data, "license", None) if card_data is not None else None
if str(observed_license).lower() != MODEL_LICENSE:
    raise SystemExit(f"Unexpected base-model licence: {observed_license!r}")

snapshot = Path(
    snapshot_download(
        repo_id=MODEL_REF,
        revision=MODEL_REVISION,
        allow_patterns=list(REQUIRED_FILES),
    )
)
hashes = {}
for name in REQUIRED_FILES:
    path = snapshot / name
    if not path.is_file():
        raise SystemExit(f"Pinned model snapshot is missing {name}")
    hashes[name] = sha256(path)
if hashes["model.safetensors"] != MODEL_FILE_SHA256:
    raise SystemExit("Pinned model.safetensors SHA-256 mismatch")

model_digest = canonical_sha256(
    {
        "config.json": hashes["config.json"],
        "model.safetensors": hashes["model.safetensors"],
    }
)
tokenizer_digest = canonical_sha256(
    {
        name: hashes[name]
        for name in (
            "special_tokens_map.json",
            "tokenizer.json",
            "tokenizer.model",
            "tokenizer_config.json",
        )
    }
)

dedup_policy = DedupPolicy(near_threshold=1.0, lowercase_comparison=False)
if dedup_policy.digest != request["dedup_policy_digest"]:
    raise SystemExit("Dedup policy digest mismatch")
registry = ProtectedHoldoutRegistry(dedup_policy.digest)
tasks = []
control_answers = {}
for raw in workload["benchmark_tasks"]:
    holdout_id = f"v245-{raw['task_id']}"
    registry.register(
        ProtectedHoldout.from_text(
            holdout_id,
            raw["prompt"],
            dedup_policy,
        )
    )
    control_answers[raw["prompt"]] = raw["expected"]
    tasks.append(
        BenchmarkTaskSpec(
            task_id=raw["task_id"],
            domain=workload["domain"],
            critical=True,
            prompt=raw["prompt"],
            scorer=ScorerSpec.create(
                ScorerKind.EXACT,
                version="v245-1",
                config={"expected": raw["expected"]},
            ),
            protected_holdout_id=holdout_id,
        )
    )
if canonical_sha256(registry.safe_manifest()) != request["protection_manifest_digest"]:
    raise SystemExit("Protected-holdout manifest digest mismatch")

suite = BenchmarkSuite(
    suite_id="v245-live-bootstrap",
    version="1",
    tasks=tuple(tasks),
)


class QualificationClient:
    def __init__(self) -> None:
        self.model = None
        self.tokenizer = None

    def _load(self) -> None:
        if self.model is not None:
            return
        self.tokenizer = AutoTokenizer.from_pretrained(
            snapshot,
            local_files_only=True,
            trust_remote_code=False,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            snapshot,
            local_files_only=True,
            trust_remote_code=False,
            torch_dtype=torch.float16,
            device_map={"": 0},
        )
        self.model.eval()

    def preload(self, model: str, **_kwargs: object) -> dict[str, object]:
        if model != MODEL_REF:
            return {"done_reason": "control"}
        started = time.perf_counter()
        self._load()
        elapsed = time.perf_counter() - started
        return {
            "done_reason": "load",
            "load_duration": int(elapsed * 1_000_000_000),
        }

    def chat(
        self,
        model: str,
        messages: list[object],
        **kwargs: object,
    ) -> BrainResponse:
        prompt = str(getattr(messages[-1], "content"))
        if model == CONTROL_REF:
            answer = control_answers[prompt]
            return BrainResponse(
                content=answer,
                model=model,
                metrics={
                    "eval_count": len(answer.split()),
                    "eval_duration": 1_000_000,
                },
            )
        if model != MODEL_REF:
            raise RuntimeError("unsupported qualification model")
        self._load()
        assert self.model is not None
        assert self.tokenizer is not None
        options = dict(kwargs.get("options") or {})
        torch.manual_seed(int(options.get("seed", 245)))
        rendered = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            add_generation_prompt=True,
            tokenize=False,
        )
        encoded = self.tokenizer(rendered, return_tensors="pt").to("cuda:0")
        max_new_tokens = min(int(options.get("num_predict", 32)), 32)
        started = time.perf_counter()
        with torch.no_grad():
            output = self.model.generate(
                **encoded,
                do_sample=False,
                max_new_tokens=max_new_tokens,
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
        if model != MODEL_REF:
            return
        self.model = None
        self.tokenizer = None
        gc.collect()
        torch.cuda.empty_cache()


control_digest = canonical_sha256({"answers": control_answers, "version": 1})
benchmark = KodeBenchRunner(QualificationClient()).run(
    [MODEL_REF, CONTROL_REF],
    suite,
    config=RunConfig(
        repeats=2,
        seed_base=245,
        temperature=0.0,
        num_predict=32,
    ),
    identities={
        MODEL_REF: ModelIdentity(
            model_ref=MODEL_REF,
            model_digest=model_digest,
            runtime="transformers",
            runtime_version=version("transformers"),
        ),
        CONTROL_REF: ModelIdentity(
            model_ref=CONTROL_REF,
            model_digest=control_digest,
            runtime="kodepoia-control",
            runtime_version="v245-1",
        ),
    },
    holdout_registry=registry,
)
benchmark_payload = {
    **benchmark.safe_descriptor(),
    "report_digest": benchmark.digest,
}

runtime_request = RuntimeRequest(
    backend=TrainingBackend.CUDA,
    dtype=DTypeName.FLOAT16,
    quantization=QuantizationMode.BNB_NF4,
    resources=ResourceRequest(
        disk_required_bytes=4 * 1024**3,
        ram_required_bytes=6 * 1024**3,
        vram_estimate_bytes=3 * 1024**3,
        vram_reserve_bytes=512 * 1024**2,
        vram_headroom_bytes=512 * 1024**2,
    ),
    timeout_seconds=600.0,
    model_ref=MODEL_REF,
    model_revision=MODEL_REVISION,
    tokenizer_ref=MODEL_REF,
    model_load_dry_run=True,
)
capability = TrainingRuntime(work / "runtime").probe(runtime_request)

evidence = {
    "benchmark": benchmark_payload,
    "capability": capability.to_dict(),
    "dataset_digest": request["dataset_digest"],
    "dataset_manifest_digest": request["dataset_manifest_digest"],
    "dedup_policy_digest": request["dedup_policy_digest"],
    "expected_device_count": 2,
    "kaggle_dataset_id": request["kaggle_dataset_id"],
    "kernel_id": request["kernel_id"],
    "model": {
        "license": observed_license,
        "model_digest": model_digest,
        "model_ref": MODEL_REF,
        "model_revision": MODEL_REVISION,
        "snapshot_files": hashes,
        "tokenizer_digest": tokenizer_digest,
        "tokenizer_ref": MODEL_REF,
        "tokenizer_revision": MODEL_REVISION,
    },
    "promotion_authorized": False,
    "protection_manifest_digest": request["protection_manifest_digest"],
    "request_digest": request["request_digest"],
    "requested_shape": request["requested_shape"],
    "schema": "kodepoia.v2.4.5.live-bootstrap-evidence",
    "schema_version": 1,
    "source_sha": request["source_sha"],
    "workload_digest": request["workload_digest"],
}
(work / "bootstrap-evidence.json").write_text(
    json.dumps(evidence, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(
    json.dumps(
        {
            "benchmark_report_digest": benchmark.digest,
            "capability_report_digest": capability.digest,
            "model_digest": model_digest,
            "request_digest": request["request_digest"],
            "state": "completed",
            "tokenizer_digest": tokenizer_digest,
        },
        sort_keys=True,
    )
)
'''


def build_live_bootstrap_bundle(
    *,
    repository_root: Path,
    source_sha: str,
    kaggle_dataset_id: str,
    kernel_id: str,
    wheel_path: Path,
    output_root: Path,
) -> KaggleLiveBootstrapBundle:
    repository_root = repository_root.resolve(strict=True)
    output_root = _inside(repository_root, output_root, strict=False)
    if output_root.exists() and any(output_root.iterdir()):
        raise KaggleLiveBootstrapError(
            f"live bootstrap bundle directory is not empty: {output_root}"
        )
    wheel_path = wheel_path.resolve(strict=True)
    wheel_filename = _validated_wheel_filename(wheel_path.name)
    wheel_sha256 = _sha256_file(wheel_path)
    output_root.mkdir(parents=True, exist_ok=True)
    governed = build_live_qualification_dataset(
        repository_root,
        output_root / "governed-dataset",
    )
    request = KaggleLiveBootstrapRequest(
        source_sha=source_sha,
        kaggle_dataset_id=kaggle_dataset_id,
        kernel_id=kernel_id,
        dataset_digest=governed.build.manifest.dataset_digest,
        dataset_manifest_digest=governed.build.manifest.file_digest,
        train_export_digest=governed.build.manifest.export_digests["train"],
        validation_export_digest=governed.build.manifest.export_digests[
            "validation"
        ],
        workload_digest=governed.workload_digest,
        contamination_digest=governed.contamination_digest,
        protection_manifest_digest=governed.protection_manifest_digest,
        dedup_policy_digest=governed.dedup_policy_digest,
        wheel_filename=wheel_filename,
        wheel_sha256=wheel_sha256,
    )

    dataset_dir = output_root / "kaggle-dataset"
    kernel_dir = output_root / "kernel"
    result_dir = output_root / "output"
    dataset_dir.mkdir()
    kernel_dir.mkdir()
    result_dir.mkdir()

    copies = {
        "contamination.json": governed.contamination_path,
        "holdouts.json": governed.holdouts_path,
        "manifest.json": governed.manifest_path,
        "workload.json": governed.workload_path,
    }
    for name, source in copies.items():
        shutil.copy2(source, dataset_dir / name)
    shutil.copy2(wheel_path, dataset_dir / wheel_filename)
    _write_json(dataset_dir / "bootstrap-request.json", request.to_dict())

    file_names = (
        "bootstrap-request.json",
        "contamination.json",
        "holdouts.json",
        "manifest.json",
        "workload.json",
        wheel_filename,
    )
    manifest = {
        "files": {
            name: _sha256_file(dataset_dir / name)
            for name in file_names
        },
        "request_digest": request.digest,
        "schema": "kodepoia.v2.4.5.live-bootstrap-bundle",
        "schema_version": 1,
        "wheel_filename": wheel_filename,
        "wheel_sha256": wheel_sha256,
    }
    _assert_no_secret_fields(manifest)
    _write_json(dataset_dir / "bootstrap-bundle-manifest.json", manifest)
    dataset_slug = request.kaggle_dataset_id.split("/", 1)[1]
    _write_json(
        dataset_dir / "dataset-metadata.json",
        {
            "description": (
                "Private transient Kodepoia V2.4.5 governed live-qualification "
                "bootstrap evidence."
            ),
            "id": request.kaggle_dataset_id,
            "licenses": [{"name": "other"}],
            "title": dataset_slug,
        },
    )

    script_path = kernel_dir / "run_bootstrap.py"
    script_path.write_text(_bootstrap_kernel_script(), encoding="utf-8")
    kernel_slug = request.kernel_id.split("/", 1)[1]
    kernel_metadata = {
        "code_file": script_path.name,
        "competition_sources": [],
        "dataset_sources": [request.kaggle_dataset_id],
        "enable_gpu": True,
        "enable_internet": True,
        "id": request.kernel_id,
        "is_private": True,
        "kernel_sources": [],
        "kernel_type": "script",
        "language": "python",
        "machine_shape": QUALIFICATION_SHAPE,
        "model_sources": [],
        "title": kernel_slug,
    }
    _assert_no_secret_fields(kernel_metadata)
    _write_json(kernel_dir / "kernel-metadata.json", kernel_metadata)
    _write_json(
        output_root / "bundle.json",
        {
            "governed_dataset_root": "governed-dataset",
            "kaggle_dataset_dir": "kaggle-dataset",
            "kernel_dir": "kernel",
            "output_dir": "output",
            "request": request.to_dict(),
        },
    )
    return KaggleLiveBootstrapBundle(
        root=output_root,
        governed_dataset=governed,
        kaggle_dataset_dir=dataset_dir,
        kernel_dir=kernel_dir,
        output_dir=result_dir,
        request=request,
    )


def _request_from_mapping(value: object) -> KaggleLiveBootstrapRequest:
    if not isinstance(value, dict):
        raise KaggleLiveBootstrapError("bootstrap request must be an object")
    return KaggleLiveBootstrapRequest(
        source_sha=str(value["source_sha"]),
        kaggle_dataset_id=str(value["kaggle_dataset_id"]),
        kernel_id=str(value["kernel_id"]),
        dataset_digest=str(value["dataset_digest"]),
        dataset_manifest_digest=str(value["dataset_manifest_digest"]),
        train_export_digest=str(value["train_export_digest"]),
        validation_export_digest=str(value["validation_export_digest"]),
        workload_digest=str(value["workload_digest"]),
        contamination_digest=str(value["contamination_digest"]),
        protection_manifest_digest=str(value["protection_manifest_digest"]),
        dedup_policy_digest=str(value["dedup_policy_digest"]),
        wheel_filename=str(value["wheel_filename"]),
        wheel_sha256=str(value["wheel_sha256"]),
    )


def load_live_bootstrap_bundle(root: Path) -> KaggleLiveBootstrapBundle:
    root = root.resolve(strict=True)
    bundle_raw = json.loads((root / "bundle.json").read_text(encoding="utf-8"))
    request = _request_from_mapping(bundle_raw["request"])
    if bundle_raw["request"].get("request_digest") != request.digest:
        raise KaggleLiveBootstrapError("saved bootstrap request digest mismatch")
    dataset_dir = _inside(
        root,
        root / str(bundle_raw["kaggle_dataset_dir"]),
        strict=True,
    )
    bundle_manifest = json.loads(
        (dataset_dir / "bootstrap-bundle-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    if (
        bundle_manifest.get("request_digest") != request.digest
        or bundle_manifest.get("wheel_filename") != request.wheel_filename
        or bundle_manifest.get("wheel_sha256") != request.wheel_sha256
    ):
        raise KaggleLiveBootstrapError("saved bootstrap wheel identity mismatch")
    bundle_files = bundle_manifest.get("files")
    if (
        not isinstance(bundle_files, dict)
        or bundle_files.get(request.wheel_filename) != request.wheel_sha256
    ):
        raise KaggleLiveBootstrapError("saved bootstrap wheel manifest mismatch")
    saved_wheel = dataset_dir / request.wheel_filename
    if (
        not saved_wheel.is_file()
        or _sha256_file(saved_wheel) != request.wheel_sha256
    ):
        raise KaggleLiveBootstrapError("saved bootstrap wheel digest mismatch")
    governed_root = root / str(bundle_raw["governed_dataset_root"])
    manifest_raw = json.loads(
        (governed_root / "manifest.json").read_text(encoding="utf-8")
    )
    workload_raw = json.loads(
        (governed_root / "workload.json").read_text(encoding="utf-8")
    )
    contamination_raw = json.loads(
        (governed_root / "contamination.json").read_text(encoding="utf-8")
    )
    holdouts_raw = json.loads(
        (governed_root / "holdouts.json").read_text(encoding="utf-8")
    )
    if canonical_sha256(workload_raw) != request.workload_digest:
        raise KaggleLiveBootstrapError("saved workload digest mismatch")
    if canonical_sha256(contamination_raw) != request.contamination_digest:
        raise KaggleLiveBootstrapError("saved contamination digest mismatch")
    if canonical_sha256(holdouts_raw) != request.protection_manifest_digest:
        raise KaggleLiveBootstrapError("saved holdout digest mismatch")
    if canonical_sha256(manifest_raw) != request.dataset_manifest_digest:
        raise KaggleLiveBootstrapError("saved dataset manifest digest mismatch")

    class _LoadedBuild:
        manifest = None

    del _LoadedBuild
    # Rebuild through the accepted R15.5 path rather than trusting serialized rows.
    repository_root = root
    while repository_root != repository_root.parent:
        if (repository_root / WORKLOAD_RELATIVE_PATH).is_file():
            break
        repository_root = repository_root.parent
    if not (repository_root / WORKLOAD_RELATIVE_PATH).is_file():
        raise KaggleLiveBootstrapError(
            "cannot locate repository root for governed bootstrap reload"
        )
    rebuilt_root = root / ".revalidated-governed-dataset"
    if rebuilt_root.exists():
        shutil.rmtree(rebuilt_root)
    governed = build_live_qualification_dataset(repository_root, rebuilt_root)
    if governed.build.manifest.dataset_digest != request.dataset_digest:
        raise KaggleLiveBootstrapError("rebuilt dataset digest mismatch")
    return KaggleLiveBootstrapBundle(
        root=root,
        governed_dataset=governed,
        kaggle_dataset_dir=dataset_dir,
        kernel_dir=root / str(bundle_raw["kernel_dir"]),
        output_dir=root / str(bundle_raw["output_dir"]),
        request=request,
    )


class KaggleLiveBootstrapClient:
    def __init__(
        self,
        *,
        runner: BootstrapCommandRunner | None = None,
        kaggle_executable: str = "kaggle",
    ) -> None:
        self.runner = runner or SubprocessCommandRunner()
        self.kaggle_executable = kaggle_executable

    def _checked(self, argv: list[str], *, timeout: float) -> CommandResult:
        result = self.runner.run(argv, timeout=timeout)
        if result.returncode != 0:
            raise KaggleLiveBootstrapError(
                f"Kaggle CLI command failed ({result.returncode}): "
                f"{result.stderr.strip()[:4096]}"
            )
        return result

    def upload_private_dataset(
        self,
        bundle: KaggleLiveBootstrapBundle,
    ) -> CommandResult:
        return self._checked(
            [
                self.kaggle_executable,
                "datasets",
                "create",
                "--path",
                str(bundle.kaggle_dataset_dir),
                "--dir-mode",
                "zip",
            ],
            timeout=3600.0,
        )

    def dataset_status(
        self,
        bundle: KaggleLiveBootstrapBundle,
    ) -> CommandResult:
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

    def push(self, bundle: KaggleLiveBootstrapBundle) -> CommandResult:
        return self._checked(
            [
                self.kaggle_executable,
                "kernels",
                "push",
                "--path",
                str(bundle.kernel_dir),
            ],
            timeout=300.0,
        )

    def status(self, bundle: KaggleLiveBootstrapBundle) -> CommandResult:
        return self._checked(
            [
                self.kaggle_executable,
                "kernels",
                "status",
                bundle.request.kernel_id,
            ],
            timeout=120.0,
        )

    def fetch_evidence(
        self,
        bundle: KaggleLiveBootstrapBundle,
    ) -> dict[str, object]:
        bundle.output_dir.mkdir(parents=True, exist_ok=True)
        self._checked(
            [
                self.kaggle_executable,
                "kernels",
                "output",
                bundle.request.kernel_id,
                "--path",
                str(bundle.output_dir),
            ],
            timeout=3600.0,
        )
        matches = list(bundle.output_dir.rglob("bootstrap-evidence.json"))
        if len(matches) != 1:
            raise KaggleLiveBootstrapError(
                "Kaggle output must contain exactly one bootstrap-evidence.json"
            )
        payload = json.loads(matches[0].read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise KaggleLiveBootstrapError("bootstrap evidence must be an object")
        _validate_downloaded_evidence(bundle.request, payload)
        return payload


def _verify_report_digest(label: str, value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise KaggleLiveBootstrapError(f"{label} must be an object")
    payload = dict(value)
    claimed = payload.pop("report_digest", None)
    if not isinstance(claimed, str) or claimed != canonical_sha256(payload):
        raise KaggleLiveBootstrapError(f"{label} report digest mismatch")
    return dict(value)


def _validate_downloaded_evidence(
    request: KaggleLiveBootstrapRequest,
    payload: dict[str, object],
) -> None:
    _assert_no_secret_fields(payload)
    expected = {
        "dataset_digest": request.dataset_digest,
        "dataset_manifest_digest": request.dataset_manifest_digest,
        "dedup_policy_digest": request.dedup_policy_digest,
        "kaggle_dataset_id": request.kaggle_dataset_id,
        "kernel_id": request.kernel_id,
        "protection_manifest_digest": request.protection_manifest_digest,
        "request_digest": request.digest,
        "requested_shape": QUALIFICATION_SHAPE,
        "source_sha": request.source_sha,
        "workload_digest": request.workload_digest,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise KaggleLiveBootstrapError(f"bootstrap evidence {key} mismatch")
    if payload.get("schema") != BOOTSTRAP_EVIDENCE_SCHEMA:
        raise KaggleLiveBootstrapError("unsupported bootstrap evidence schema")
    if payload.get("schema_version") != BOOTSTRAP_SCHEMA_VERSION:
        raise KaggleLiveBootstrapError("unsupported bootstrap evidence version")
    if payload.get("promotion_authorized") is not False:
        raise KaggleLiveBootstrapError("bootstrap evidence cannot authorize promotion")

    model = payload.get("model")
    if not isinstance(model, dict):
        raise KaggleLiveBootstrapError("bootstrap model evidence is missing")
    model_expected = {
        "license": QUALIFICATION_MODEL_LICENSE,
        "model_ref": QUALIFICATION_MODEL_REF,
        "model_revision": QUALIFICATION_MODEL_REVISION,
        "tokenizer_ref": QUALIFICATION_MODEL_REF,
        "tokenizer_revision": QUALIFICATION_MODEL_REVISION,
    }
    for key, value in model_expected.items():
        if model.get(key) != value:
            raise KaggleLiveBootstrapError(f"bootstrap model {key} mismatch")
    snapshot_files = model.get("snapshot_files")
    if (
        not isinstance(snapshot_files, dict)
        or snapshot_files.get("model.safetensors")
        != QUALIFICATION_MODEL_FILE_SHA256
    ):
        raise KaggleLiveBootstrapError("bootstrap model file checksum mismatch")
    for key in ("model_digest", "tokenizer_digest"):
        if not isinstance(model.get(key), str) or _SHA256.fullmatch(str(model[key])) is None:
            raise KaggleLiveBootstrapError(f"bootstrap {key} is invalid")
    _verify_report_digest("benchmark", payload.get("benchmark"))
    _verify_report_digest("capability", payload.get("capability"))


def _benchmark_is_reproducible(
    benchmark: dict[str, object],
) -> bool:
    outcomes = benchmark.get("outcomes")
    if not isinstance(outcomes, list):
        return False
    by_task: dict[str, list[dict[str, object]]] = {}
    for raw in outcomes:
        if not isinstance(raw, dict):
            return False
        if raw.get("model_ref") != QUALIFICATION_MODEL_REF:
            continue
        task_id = raw.get("task_id")
        if not isinstance(task_id, str):
            return False
        by_task.setdefault(task_id, []).append(raw)
    if not by_task:
        return False
    for rows in by_task.values():
        if len(rows) != 2:
            return False
        if {row.get("repeat") for row in rows} != {1, 2}:
            return False
        digests = {row.get("response_digest") for row in rows}
        if len(digests) != 1:
            return False
    return True


def _capability_supported(capability: dict[str, object]) -> bool:
    return bool(
        capability.get("disposition") == "ready"
        and capability.get("backend") == "cuda"
        and capability.get("backend_capability") == "supported"
        and capability.get("dtype_supported") is True
        and capability.get("four_bit_supported") is True
        and capability.get("model_load") == "supported"
        and capability.get("blockers") == []
    )


def _diagnostics(
    benchmark_digest: str,
) -> tuple[DiagnosticProbe, ...]:
    rows = []
    for component in (
        DiagnosticComponent.TOOL,
        DiagnosticComponent.RETRIEVAL,
        DiagnosticComponent.ROUTER,
        DiagnosticComponent.CONTEXT,
    ):
        rows.append(
            DiagnosticProbe(
                component=component,
                status=ProbeStatus.PASS,
                evidence_digest=canonical_sha256(
                    {
                        "benchmark_report_digest": benchmark_digest,
                        "component": component.value,
                        "reason": (
                            "direct-model-only repository-owned qualification "
                            "benchmark; component not in execution path"
                        ),
                    }
                ),
            )
        )
    return tuple(rows)


def finalize_live_bootstrap(
    *,
    repository_root: Path,
    bundle: KaggleLiveBootstrapBundle,
    evidence: dict[str, object],
    output_root: Path,
) -> KaggleLiveBootstrapResult:
    repository_root = repository_root.resolve(strict=True)
    output_root = _inside(repository_root, output_root, strict=False)
    output_root.mkdir(parents=True, exist_ok=True)
    _validate_downloaded_evidence(bundle.request, evidence)

    manifest = json.loads(
        bundle.governed_dataset.manifest_path.read_text(encoding="utf-8")
    )
    if canonical_sha256(manifest) != bundle.request.dataset_manifest_digest:
        raise KaggleLiveBootstrapError("local governed dataset manifest mismatch")
    if manifest.get("dataset_digest") != bundle.request.dataset_digest:
        raise KaggleLiveBootstrapError("local governed dataset identity mismatch")
    if _sha256_file(bundle.governed_dataset.train_path) != (
        bundle.request.train_export_digest
    ):
        raise KaggleLiveBootstrapError("local train export digest mismatch")
    if _sha256_file(bundle.governed_dataset.validation_path) != (
        bundle.request.validation_export_digest
    ):
        raise KaggleLiveBootstrapError("local validation export digest mismatch")

    benchmark = _verify_report_digest("benchmark", evidence["benchmark"])
    capability = _verify_report_digest("capability", evidence["capability"])
    benchmark_digest = str(benchmark["report_digest"])
    capability_digest = str(capability["report_digest"])
    model = dict(evidence["model"])  # type: ignore[arg-type]
    outcomes = benchmark.get("outcomes")
    base_failures = [
        row
        for row in outcomes
        if isinstance(outcomes, list)
        and isinstance(row, dict)
        and row.get("model_ref") == QUALIFICATION_MODEL_REF
        and row.get("passed") is False
    ] if isinstance(outcomes, list) else []
    meaningful = bool(base_failures)

    evidence_digests = tuple(
        sorted(
            (
                ("benchmark", benchmark_digest),
                ("capability", capability_digest),
                ("contamination", bundle.request.contamination_digest),
                (
                    "model-license",
                    canonical_sha256(
                        {
                            "license": QUALIFICATION_MODEL_LICENSE,
                            "model_ref": QUALIFICATION_MODEL_REF,
                            "revision": QUALIFICATION_MODEL_REVISION,
                        }
                    ),
                ),
                ("workload", bundle.request.workload_digest),
            )
        )
    )
    decision_evidence = DecisionEvidence(
        benchmark_reproducible=_benchmark_is_reproducible(benchmark),
        contamination_valid=True,
        dataset_license=PolicyDecision.ALLOW,
        base_model_license=PolicyDecision.ALLOW,
        backend_capability=(
            BackendCapability.SUPPORTED
            if _capability_supported(capability)
            else BackendCapability.UNSUPPORTED
        ),
        budget_status=(
            BudgetStatus.WITHIN_BUDGET
            if _capability_supported(capability)
            else BudgetStatus.EXCEEDED
        ),
        rollback_ready=True,
        expected_impact=(
            ExpectedImpact.MEANINGFUL if meaningful else ExpectedImpact.LOW
        ),
        diagnostics=_diagnostics(benchmark_digest),
        evidence_digests=evidence_digests,
    )
    decision = GapDecisionEngine().evaluate(
        benchmark,
        base_model_ref=QUALIFICATION_MODEL_REF,
        evidence=decision_evidence,
        dataset=manifest,
    )
    decision_path = output_root / "gap-decision.json"
    decision.save(decision_path)

    plan: TrainingPlan | None = None
    plan_path: Path | None = None
    if decision.disposition is DecisionDisposition.TRAIN:
        train_relative = bundle.governed_dataset.train_path.relative_to(
            repository_root
        ).as_posix()
        validation_relative = bundle.governed_dataset.validation_path.relative_to(
            repository_root
        ).as_posix()
        split_stats = manifest["split_stats"]
        exports = manifest["export_digests"]
        plan = TrainingPlan(
            mode=TrainingMode.QLORA,
            authorization=TrainingAuthorization.TRAIN,
            model=ModelBinding(
                model_ref=QUALIFICATION_MODEL_REF,
                model_revision=QUALIFICATION_MODEL_REVISION,
                model_digest=str(model["model_digest"]),
                tokenizer_ref=QUALIFICATION_MODEL_REF,
                tokenizer_revision=QUALIFICATION_MODEL_REVISION,
                tokenizer_digest=str(model["tokenizer_digest"]),
                assistant_mask_capable=False,
            ),
            dataset=DatasetBinding(
                dataset_id=str(manifest["dataset_id"]),
                dataset_digest=str(manifest["dataset_digest"]),
                manifest_digest=bundle.request.dataset_manifest_digest,
                train_export_digest=str(exports["train"]),
                validation_export_digest=str(exports["validation"]),
                train_rows=int(split_stats["train"]["rows"]),
                validation_rows=int(split_stats["validation"]["rows"]),
                format="prompt_completion",
                train_path=train_relative,
                validation_path=validation_relative,
            ),
            lora=LoraTrainingConfig(
                rank=8,
                alpha=16,
                dropout=0.0,
                target_modules=("all-linear",),
            ),
            sft=SFTTrainingConfig(
                max_steps=8,
                train_batch_size=1,
                eval_batch_size=1,
                gradient_accumulation_steps=2,
                context_length=128,
                learning_rate=2e-4,
                checkpoint_steps=4,
                eval_steps=4,
                gradient_checkpointing=True,
                completion_only_loss=True,
                assistant_only_loss=False,
                full_determinism=True,
                optimizer="adamw_torch",
                scheduler="linear",
            ),
            quantization=QuantizationMode.BNB_NF4,
            seeds=SeedConfig(seed=245, data_seed=245),
            resources=ResourceRequest(
                disk_required_bytes=4 * 1024**3,
                ram_required_bytes=6 * 1024**3,
                vram_estimate_bytes=3 * 1024**3,
                vram_reserve_bytes=512 * 1024**2,
                vram_headroom_bytes=512 * 1024**2,
            ),
            timeout_seconds=3600.0,
            capability_report_digest=capability_digest,
        )
        plan_path = output_root / "training-plan.json"
        save_training_plan(plan, plan_path)

    result_payload: dict[str, object] = {
        "capability_report_digest": capability_digest,
        "decision_digest": decision.digest,
        "disposition": decision.disposition.value,
        "model_digest": model["model_digest"],
        "promotion_authorized": False,
        "qualification_only": True,
        "request_digest": bundle.request.digest,
        "schema": BOOTSTRAP_RESULT_SCHEMA,
        "schema_version": BOOTSTRAP_SCHEMA_VERSION,
        "source_sha": bundle.request.source_sha,
        "tokenizer_digest": model["tokenizer_digest"],
        "training_plan_digest": None if plan is None else plan.digest,
    }
    result_payload["result_digest"] = canonical_sha256(result_payload)
    result_path = output_root / "bootstrap-result.json"
    _write_json(result_path, result_payload)
    return KaggleLiveBootstrapResult(
        decision=decision,
        training_plan=plan,
        decision_path=decision_path,
        training_plan_path=plan_path,
        result_path=result_path,
    )


__all__ = [
    "BOOTSTRAP_EVIDENCE_SCHEMA",
    "BOOTSTRAP_REQUEST_SCHEMA",
    "BOOTSTRAP_RESULT_SCHEMA",
    "KaggleLiveBootstrapBundle",
    "KaggleLiveBootstrapClient",
    "KaggleLiveBootstrapError",
    "KaggleLiveBootstrapRequest",
    "KaggleLiveBootstrapResult",
    "LiveQualificationDataset",
    "QUALIFICATION_MODEL_LICENSE",
    "QUALIFICATION_MODEL_REF",
    "QUALIFICATION_MODEL_REVISION",
    "build_live_bootstrap_bundle",
    "build_live_qualification_dataset",
    "finalize_live_bootstrap",
    "load_live_bootstrap_bundle",
]
