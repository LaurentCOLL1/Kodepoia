from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

EXPORT_SCHEMA = "kodepoia.r15.11.model-export"
EXPORT_SCHEMA_VERSION = 1
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SECRET_MARKERS = (
    "-----begin private key-----",
    "ghp_",
    "github_pat_",
    "sk-",
    "password=",
    "authorization: bearer ",
)


class ModelExportError(ValueError):
    """Raised when an R15.11 export cannot be proven safe and lineage-complete."""


class MergeDisposition(StrEnum):
    NOT_REQUESTED = "not_requested"
    MERGED = "merged"
    UNSUPPORTED = "unsupported"


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_digest(label: str, value: str) -> str:
    if _DIGEST.fullmatch(value) is None:
        raise ModelExportError(f"{label} must be 64 lowercase hex characters")
    return value


def _require_safe_id(label: str, value: str) -> str:
    if _SAFE_ID.fullmatch(value) is None:
        raise ModelExportError(f"{label} must be a stable safe identifier")
    return value


def _require_text(label: str, value: str, *, limit: int = 512) -> str:
    resolved = value.strip()
    invalid_control = any(ord(char) < 32 and char not in "\n\t" for char in resolved)
    if not resolved or len(resolved) > limit or invalid_control:
        raise ModelExportError(f"{label} must be bounded non-empty text")
    lowered = resolved.lower()
    if any(marker in lowered for marker in _SECRET_MARKERS):
        raise ModelExportError(f"{label} contains secret-like content")
    return resolved


def _tree_files(path: Path) -> list[Path]:
    return sorted(
        (item for item in path.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(path).as_posix(),
    )


def _tree_manifest(path: Path) -> list[dict[str, object]]:
    return [
        {
            "path": item.relative_to(path).as_posix(),
            "sha256": _sha256_file(item),
            "size_bytes": item.stat().st_size,
        }
        for item in _tree_files(path)
    ]


def _tree_digest(entries: list[dict[str, object]]) -> str:
    return _sha256_bytes(_canonical_json(entries).encode("utf-8"))


@dataclass(frozen=True, slots=True)
class ExportBinding:
    candidate_id: str
    base_model_ref: str
    base_model_revision: str
    base_model_digest: str
    adapter_digest: str
    dataset_digest: str
    training_plan_digest: str
    evaluation_digest: str
    base_license: str
    adapter_license: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_id", _require_safe_id("candidate_id", self.candidate_id))
        for field in ("base_model_ref", "base_model_revision", "base_license", "adapter_license"):
            object.__setattr__(self, field, _require_text(field, getattr(self, field), limit=256))
        for field in (
            "base_model_digest",
            "adapter_digest",
            "dataset_digest",
            "training_plan_digest",
            "evaluation_digest",
        ):
            _require_digest(field, getattr(self, field))

    def descriptor(self) -> dict[str, str]:
        return {
            "adapter_digest": self.adapter_digest,
            "adapter_license": self.adapter_license,
            "base_license": self.base_license,
            "base_model_digest": self.base_model_digest,
            "base_model_ref": self.base_model_ref,
            "base_model_revision": self.base_model_revision,
            "candidate_id": self.candidate_id,
            "dataset_digest": self.dataset_digest,
            "evaluation_digest": self.evaluation_digest,
            "training_plan_digest": self.training_plan_digest,
        }


@dataclass(frozen=True, slots=True)
class ExportRequest:
    binding: ExportBinding
    intended_use: str
    limitations: str
    eval_summary: str
    merge_requested: bool = False

    def __post_init__(self) -> None:
        for field in ("intended_use", "limitations", "eval_summary"):
            object.__setattr__(self, field, _require_text(field, getattr(self, field), limit=2000))


@dataclass(frozen=True, slots=True)
class ExportReport:
    manifest: Mapping[str, object]
    manifest_digest: str
    output_dir: Path

    def descriptor(self) -> dict[str, object]:
        return dict(self.manifest)


def require_promoted_candidate(evaluation: Mapping[str, object], binding: ExportBinding) -> None:
    if evaluation.get("disposition") != "promote_to_export" or evaluation.get("can_export") is not True:
        raise ModelExportError("R15.11 accepts only R15.10 PROMOTE_TO_EXPORT evidence")
    evaluation_binding = evaluation.get("binding")
    if not isinstance(evaluation_binding, Mapping):
        raise ModelExportError("candidate evaluation binding is required")
    required = {
        "candidate_id": binding.candidate_id,
        "base_model_ref": binding.base_model_ref,
        "base_model_digest": binding.base_model_digest,
        "adapter_digest": binding.adapter_digest,
        "dataset_digest": binding.dataset_digest,
        "training_plan_digest": binding.training_plan_digest,
    }
    for key, expected in required.items():
        if evaluation_binding.get(key) != expected:
            raise ModelExportError(f"candidate evaluation {key} does not match export binding")


def _validate_adapter(adapter_dir: Path, binding: ExportBinding) -> dict[str, object]:
    if not adapter_dir.is_dir():
        raise ModelExportError("adapter directory does not exist")
    config_path = adapter_dir / "adapter_config.json"
    if not config_path.is_file():
        raise ModelExportError("adapter_config.json is required")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelExportError("adapter_config.json is not valid JSON") from exc
    if not isinstance(config, dict):
        raise ModelExportError("adapter_config.json must be an object")
    if config.get("base_model_name_or_path") != binding.base_model_ref:
        raise ModelExportError("adapter base_model_name_or_path does not match immutable base identity")
    revision = config.get("revision")
    if revision not in (None, binding.base_model_revision):
        raise ModelExportError("adapter revision does not match immutable base revision")
    files = _tree_manifest(adapter_dir)
    if not any(str(item["path"]).endswith(".safetensors") for item in files):
        raise ModelExportError("adapter export requires Safetensors weights")
    actual_digest = _tree_digest(files)
    if actual_digest != binding.adapter_digest:
        raise ModelExportError("adapter digest does not match immutable training lineage")
    return {"config": config, "files": files, "tree_digest": actual_digest}


def _copy_adapter(adapter_dir: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=False)
    for source in _tree_files(adapter_dir):
        relative = source.relative_to(adapter_dir)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def _model_card(request: ExportRequest, merge: MergeDisposition) -> str:
    binding = request.binding
    lines = [
        "---",
        f"base_model: {binding.base_model_ref}",
        f"license: {binding.adapter_license}",
        "library_name: peft",
        "tags:",
        "- kodepoia",
        "- r15.11",
        "---",
        "",
        f"# {binding.candidate_id}",
        "",
        "## Lineage",
        "",
        f"- Base model: `{binding.base_model_ref}`",
        f"- Base revision: `{binding.base_model_revision}`",
        f"- Base digest: `{binding.base_model_digest}`",
        f"- Adapter digest: `{binding.adapter_digest}`",
        f"- Dataset digest: `{binding.dataset_digest}`",
        f"- Training-plan digest: `{binding.training_plan_digest}`",
        f"- Accepted evaluation digest: `{binding.evaluation_digest}`",
        f"- Merge disposition: `{merge.value}`",
        "",
        "## Intended use",
        "",
        request.intended_use,
        "",
        "## Limitations",
        "",
        request.limitations,
        "",
        "## Accepted evaluation summary",
        "",
        request.eval_summary,
        "",
        "## Licenses",
        "",
        f"- Base model license/provenance expression: `{binding.base_license}`",
        f"- Adapter license/provenance expression: `{binding.adapter_license}`",
        "",
        (
            "No raw training examples, private source text, credentials, or source filesystem paths "
            "are embedded in this card."
        ),
        "",
    ]
    card = "\n".join(lines)
    _require_text("model card", card, limit=16_000)
    return card


def export_candidate(
    *,
    adapter_dir: Path,
    output_root: Path,
    request: ExportRequest,
    evaluation: Mapping[str, object],
    merger: Callable[[Path, Path, ExportBinding], bool] | None = None,
    load_smoke: Callable[[Path, ExportBinding, MergeDisposition], bool] | None = None,
) -> ExportReport:
    """Export one accepted candidate without mutating source weights.

    ``merger`` is capability-injected so core acceptance never imports heavy ML packages.
    Returning ``False`` means merge is unsupported and preserves an adapter-only export.
    """
    require_promoted_candidate(evaluation, request.binding)
    source = adapter_dir.resolve()
    root = output_root.resolve()
    if source == root or source in root.parents or root in source.parents:
        raise ModelExportError("source adapter and export root must be disjoint")
    validated = _validate_adapter(source, request.binding)

    destination = root / request.binding.candidate_id
    if destination.exists():
        raise ModelExportError("immutable export destination already exists")
    destination.mkdir(parents=True, exist_ok=False)
    adapter_target = destination / "adapter"
    _copy_adapter(source, adapter_target)

    merge = MergeDisposition.NOT_REQUESTED
    merged_manifest: list[dict[str, object]] | None = None
    if request.merge_requested:
        merge = MergeDisposition.UNSUPPORTED
        if merger is not None:
            merged_target = destination / "merged"
            merged_target.mkdir(parents=True, exist_ok=False)
            supported = bool(merger(adapter_target, merged_target, request.binding))
            if supported:
                if not _tree_files(merged_target):
                    raise ModelExportError("merger reported support but produced no files")
                merge = MergeDisposition.MERGED
                merged_manifest = _tree_manifest(merged_target)
            else:
                shutil.rmtree(merged_target)

    if load_smoke is not None and not load_smoke(destination, request.binding, merge):
        raise ModelExportError("export load/inference smoke failed")

    card = _model_card(request, merge)
    (destination / "README.md").write_text(card, encoding="utf-8", newline="\n")
    manifest: dict[str, object] = {
        "schema": EXPORT_SCHEMA,
        "schema_version": EXPORT_SCHEMA_VERSION,
        "binding": request.binding.descriptor(),
        "adapter": {
            "files": _tree_manifest(adapter_target),
            "tree_digest": validated["tree_digest"],
        },
        "merge": {
            "disposition": merge.value,
            "files": merged_manifest,
        },
        "model_card": {
            "path": "README.md",
            "sha256": _sha256_bytes(card.encode("utf-8")),
        },
        "source_overwritten": False,
    }
    manifest_digest = _sha256_bytes(_canonical_json(manifest).encode("utf-8"))
    manifest["manifest_digest"] = manifest_digest
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return ExportReport(manifest=manifest, manifest_digest=manifest_digest, output_dir=destination)
