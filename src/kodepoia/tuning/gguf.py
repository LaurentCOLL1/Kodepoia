from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

GGUF_SCHEMA = "kodepoia.r15.12.gguf-conversion"
GGUF_SCHEMA_VERSION = 1
GGUF_MAGIC = b"GGUF"
SUPPORTED_GGUF_VERSIONS = frozenset({2, 3})
HIGH_PRECISION_TYPES = frozenset({"F32", "F16", "BF16"})
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_QUANT_TYPE = re.compile(r"^[A-Z0-9][A-Z0-9_]{0,31}$")


class GgufConversionError(ValueError):
    """Raised when R15.12 conversion evidence cannot be proven safe or complete."""


class SourceKind(StrEnum):
    HF_DIRECTORY = "hf_directory"
    GGUF = "gguf"


class QualityDisposition(StrEnum):
    ACCEPT = "accept"
    REJECT_QUALITY = "reject_quality"
    REJECT_CRITICAL = "reject_critical"


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def digest_path(path: Path) -> str:
    """Hash one file or a directory tree without serializing absolute paths."""
    resolved = path.resolve()
    if resolved.is_file():
        return _sha256_file(resolved)
    if not resolved.is_dir():
        raise GgufConversionError("source path does not exist")
    rows: list[dict[str, object]] = []
    for item in sorted(
        (entry for entry in resolved.rglob("*") if entry.is_file()),
        key=lambda entry: entry.relative_to(resolved).as_posix(),
    ):
        rows.append(
            {
                "path": item.relative_to(resolved).as_posix(),
                "sha256": _sha256_file(item),
                "size_bytes": item.stat().st_size,
            }
        )
    if not rows:
        raise GgufConversionError("source directory is empty")
    return hashlib.sha256(_canonical_json(rows).encode("utf-8")).hexdigest()


def _require_digest(label: str, value: str) -> str:
    if _DIGEST.fullmatch(value) is None:
        raise GgufConversionError(f"{label} must be 64 lowercase hex characters")
    return value


def _require_safe_id(label: str, value: str) -> str:
    if _SAFE_ID.fullmatch(value) is None:
        raise GgufConversionError(f"{label} must be a stable safe identifier")
    return value


def _require_quant_type(value: str) -> str:
    normalized = value.upper()
    if _QUANT_TYPE.fullmatch(normalized) is None:
        raise GgufConversionError("quantization type is not a safe structured value")
    return normalized


def _require_bounded_text(label: str, value: str, *, limit: int = 512) -> str:
    resolved = value.strip()
    if not resolved or len(resolved) > limit or any(ord(char) < 32 for char in resolved):
        raise GgufConversionError(f"{label} must be bounded non-empty text")
    return resolved


@dataclass(frozen=True, slots=True)
class GgufHeader:
    version: int
    tensor_count: int
    metadata_kv_count: int
    size_bytes: int
    sha256: str

    def descriptor(self) -> dict[str, object]:
        return {
            "metadata_kv_count": self.metadata_kv_count,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "tensor_count": self.tensor_count,
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class ToolRunResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


ToolRunner = Callable[[Sequence[str]], ToolRunResult]


@dataclass(frozen=True, slots=True)
class GgufToolchain:
    converter: Path
    quantizer: Path
    revision: str
    python_executable: str = sys.executable

    def __post_init__(self) -> None:
        object.__setattr__(self, "revision", _require_bounded_text("tool revision", self.revision, limit=128))
        object.__setattr__(
            self,
            "python_executable",
            _require_bounded_text("python executable", self.python_executable, limit=512),
        )

    def capability(self) -> dict[str, object]:
        return {
            "converter_available": self.converter.is_file(),
            "quantizer_available": self.quantizer.is_file(),
            "revision": self.revision,
        }


@dataclass(frozen=True, slots=True)
class ConversionBinding:
    candidate_id: str
    architecture: str
    source_digest: str
    export_manifest_digest: str
    evaluation_digest: str
    source_kind: SourceKind
    source_precision: str
    source_quantization: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_id", _require_safe_id("candidate_id", self.candidate_id))
        object.__setattr__(self, "architecture", _require_safe_id("architecture", self.architecture))
        for field in ("source_digest", "export_manifest_digest", "evaluation_digest"):
            _require_digest(field, getattr(self, field))
        object.__setattr__(self, "source_precision", _require_quant_type(self.source_precision))
        if self.source_quantization is not None:
            object.__setattr__(self, "source_quantization", _require_quant_type(self.source_quantization))

    def descriptor(self) -> dict[str, object]:
        return {
            "architecture": self.architecture,
            "candidate_id": self.candidate_id,
            "evaluation_digest": self.evaluation_digest,
            "export_manifest_digest": self.export_manifest_digest,
            "source_digest": self.source_digest,
            "source_kind": self.source_kind.value,
            "source_precision": self.source_precision,
            "source_quantization": self.source_quantization,
        }


@dataclass(frozen=True, slots=True)
class QuantizationTarget:
    quant_type: str
    max_aggregate_loss: float
    max_critical_loss: float = 0.0
    importance_matrix_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "quant_type", _require_quant_type(self.quant_type))
        if not 0.0 <= self.max_aggregate_loss <= 1.0:
            raise GgufConversionError("max_aggregate_loss must be within [0, 1]")
        if not 0.0 <= self.max_critical_loss <= 1.0:
            raise GgufConversionError("max_critical_loss must be within [0, 1]")
        if self.importance_matrix_digest is not None:
            _require_digest("importance_matrix_digest", self.importance_matrix_digest)


@dataclass(frozen=True, slots=True)
class ConversionPlan:
    binding: ConversionBinding
    targets: tuple[QuantizationTarget, ...]
    max_artifact_bytes: int
    allow_requantize: bool = False

    def __post_init__(self) -> None:
        if not self.targets:
            raise GgufConversionError("at least one quantization target is required")
        quant_types = [target.quant_type for target in self.targets]
        if len(set(quant_types)) != len(quant_types):
            raise GgufConversionError("duplicate quantization targets are not allowed")
        if self.max_artifact_bytes <= 0:
            raise GgufConversionError("max_artifact_bytes must be positive")
        if self.allow_requantize:
            raise GgufConversionError("R15.12 authoritative plans cannot silently allow requantization")


@dataclass(frozen=True, slots=True)
class DomainScore:
    domain: str
    baseline: float
    candidate: float
    critical: bool = False

    def __post_init__(self) -> None:
        _require_safe_id("domain", self.domain)
        if not 0.0 <= self.baseline <= 1.0 or not 0.0 <= self.candidate <= 1.0:
            raise GgufConversionError("domain scores must be within [0, 1]")

    @property
    def loss(self) -> float:
        return max(0.0, self.baseline - self.candidate)


@dataclass(frozen=True, slots=True)
class QualityAssessment:
    disposition: QualityDisposition
    aggregate_loss: float
    critical_regressions: tuple[str, ...]

    def descriptor(self) -> dict[str, object]:
        return {
            "aggregate_loss": self.aggregate_loss,
            "critical_regressions": list(self.critical_regressions),
            "disposition": self.disposition.value,
        }


@dataclass(frozen=True, slots=True)
class ArtifactEvidence:
    operation: str
    quant_type: str
    input_sha256: str
    output: GgufHeader
    tool_revision: str
    argv_shape: tuple[str, ...]

    def descriptor(self) -> dict[str, object]:
        return {
            "argv_shape": list(self.argv_shape),
            "input_sha256": self.input_sha256,
            "operation": self.operation,
            "output": self.output.descriptor(),
            "quant_type": self.quant_type,
            "tool_revision": self.tool_revision,
        }


def inspect_gguf(path: Path, *, max_size_bytes: int | None = None) -> GgufHeader:
    """Validate the bounded GGUF header and return immutable file evidence."""
    resolved = path.resolve()
    if not resolved.is_file():
        raise GgufConversionError("GGUF artifact does not exist")
    size_bytes = resolved.stat().st_size
    if max_size_bytes is not None and size_bytes > max_size_bytes:
        raise GgufConversionError("GGUF artifact exceeds configured disk budget")
    if size_bytes < 24:
        raise GgufConversionError("GGUF artifact is truncated")
    with resolved.open("rb") as handle:
        raw = handle.read(24)
    magic, version, tensor_count, metadata_kv_count = struct.unpack("<4sIQQ", raw)
    if magic != GGUF_MAGIC:
        raise GgufConversionError("GGUF magic is invalid")
    if version not in SUPPORTED_GGUF_VERSIONS:
        raise GgufConversionError("GGUF version is unsupported")
    if tensor_count <= 0 or tensor_count > 100_000_000:
        raise GgufConversionError("GGUF tensor count is invalid")
    if metadata_kv_count <= 0 or metadata_kv_count > 1_000_000:
        raise GgufConversionError("GGUF metadata count is invalid")
    return GgufHeader(
        version=version,
        tensor_count=tensor_count,
        metadata_kv_count=metadata_kv_count,
        size_bytes=size_bytes,
        sha256=_sha256_file(resolved),
    )


def require_authoritative_source(binding: ConversionBinding) -> None:
    """Reject already-quantized GGUF as an authoritative conversion source."""
    if binding.source_kind is not SourceKind.GGUF:
        return
    source_type = binding.source_quantization or binding.source_precision
    if source_type not in HIGH_PRECISION_TYPES:
        raise GgufConversionError("authoritative R15.12 path refuses requantization of quantized GGUF")


def verify_source(binding: ConversionBinding, source: Path) -> str:
    require_authoritative_source(binding)
    actual = digest_path(source)
    if actual != binding.source_digest:
        raise GgufConversionError("conversion source digest does not match immutable export lineage")
    return actual


def build_conversion_argv(
    toolchain: GgufToolchain,
    source: Path,
    output: Path,
    *,
    outtype: str = "f16",
) -> tuple[str, ...]:
    normalized = _require_quant_type(outtype)
    return (
        toolchain.python_executable,
        str(toolchain.converter),
        "--outfile",
        str(output),
        "--outtype",
        normalized.lower(),
        str(source),
    )


def build_quantize_argv(
    toolchain: GgufToolchain,
    source: Path,
    output: Path,
    target: QuantizationTarget,
    *,
    importance_matrix: Path | None = None,
) -> tuple[str, ...]:
    argv: list[str] = [str(toolchain.quantizer)]
    if importance_matrix is not None:
        if target.importance_matrix_digest is None:
            raise GgufConversionError("importance matrix path requires an immutable matrix digest")
        if _sha256_file(importance_matrix) != target.importance_matrix_digest:
            raise GgufConversionError("importance matrix digest mismatch")
        argv.extend(("--imatrix", str(importance_matrix)))
    argv.extend((str(source), str(output), target.quant_type))
    return tuple(argv)


def _argv_shape(argv: Sequence[str]) -> tuple[str, ...]:
    shape: list[str] = []
    for index, value in enumerate(argv):
        if index == 0:
            shape.append("tool")
        elif value.startswith("--"):
            shape.append(value)
        elif index > 0 and argv[index - 1] in {"--outtype"}:
            shape.append(value)
        else:
            shape.append("arg")
    return tuple(shape)


def run_high_precision_conversion(
    *,
    toolchain: GgufToolchain,
    plan: ConversionPlan,
    source: Path,
    output: Path,
    runner: ToolRunner,
    outtype: str = "F16",
) -> ArtifactEvidence:
    if not toolchain.converter.is_file():
        raise GgufConversionError("llama.cpp converter capability is unavailable")
    input_digest = verify_source(plan.binding, source)
    if output.exists():
        raise GgufConversionError("immutable conversion destination already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    argv = build_conversion_argv(toolchain, source, output, outtype=outtype)
    result = runner(argv)
    if result.returncode != 0:
        raise GgufConversionError("GGUF conversion tool failed")
    header = inspect_gguf(output, max_size_bytes=plan.max_artifact_bytes)
    return ArtifactEvidence(
        operation="convert",
        quant_type=_require_quant_type(outtype),
        input_sha256=input_digest,
        output=header,
        tool_revision=toolchain.revision,
        argv_shape=_argv_shape(argv),
    )


def run_quantization(
    *,
    toolchain: GgufToolchain,
    plan: ConversionPlan,
    source: Path,
    output: Path,
    target: QuantizationTarget,
    runner: ToolRunner,
    importance_matrix: Path | None = None,
) -> ArtifactEvidence:
    if target not in plan.targets:
        raise GgufConversionError("quantization target is not authorized by the plan")
    if not toolchain.quantizer.is_file():
        raise GgufConversionError("llama.cpp quantizer capability is unavailable")
    source_header = inspect_gguf(source, max_size_bytes=plan.max_artifact_bytes)
    if output.exists():
        raise GgufConversionError("immutable quantization destination already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    argv = build_quantize_argv(
        toolchain,
        source,
        output,
        target,
        importance_matrix=importance_matrix,
    )
    result = runner(argv)
    if result.returncode != 0:
        raise GgufConversionError("GGUF quantization tool failed")
    header = inspect_gguf(output, max_size_bytes=plan.max_artifact_bytes)
    return ArtifactEvidence(
        operation="quantize",
        quant_type=target.quant_type,
        input_sha256=source_header.sha256,
        output=header,
        tool_revision=toolchain.revision,
        argv_shape=_argv_shape(argv),
    )


def assess_quantization_quality(
    scores: Iterable[DomainScore],
    target: QuantizationTarget,
) -> QualityAssessment:
    rows = tuple(scores)
    if not rows:
        raise GgufConversionError("quality comparison requires domain evidence")
    critical = tuple(
        row.domain
        for row in rows
        if row.critical and row.loss > target.max_critical_loss
    )
    aggregate_loss = sum(row.loss for row in rows) / len(rows)
    if critical:
        disposition = QualityDisposition.REJECT_CRITICAL
    elif aggregate_loss > target.max_aggregate_loss:
        disposition = QualityDisposition.REJECT_QUALITY
    else:
        disposition = QualityDisposition.ACCEPT
    return QualityAssessment(
        disposition=disposition,
        aggregate_loss=round(aggregate_loss, 12),
        critical_regressions=critical,
    )


def build_quality_matrix_report(
    *,
    plan: ConversionPlan,
    high_precision: ArtifactEvidence,
    quantized: Mapping[str, tuple[ArtifactEvidence, QualityAssessment]],
) -> dict[str, object]:
    target_types = {target.quant_type for target in plan.targets}
    if set(quantized) != target_types:
        raise GgufConversionError("quality matrix must account for every authorized target exactly once")
    variants: list[dict[str, object]] = []
    for quant_type in sorted(quantized):
        artifact, quality = quantized[quant_type]
        if artifact.quant_type != quant_type:
            raise GgufConversionError("quality matrix quantization identity mismatch")
        variants.append(
            {
                "artifact": artifact.descriptor(),
                "quality": quality.descriptor(),
            }
        )
    report: dict[str, object] = {
        "schema": GGUF_SCHEMA,
        "schema_version": GGUF_SCHEMA_VERSION,
        "binding": plan.binding.descriptor(),
        "high_precision": high_precision.descriptor(),
        "variants": variants,
    }
    report["report_digest"] = hashlib.sha256(_canonical_json(report).encode("utf-8")).hexdigest()
    return report
