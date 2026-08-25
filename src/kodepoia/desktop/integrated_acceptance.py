from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Callable

R11_INTEGRATED_PATH = "docs/roadmap/R11_INTEGRATED_ACCEPTANCE.json"
R11_ACCEPTED_DIGEST = "ed956be1aa19592b654382a209e5ca99d44d3cbcd67dd3981bdae3d865563170"
R12_WINDOWS_CI_PATH = "docs/roadmap/R12_16_WINDOWS_CI_ACCEPTANCE.json"
R12_CONTINUITY_PATH = "docs/continuity/KODEPOIA_CONTINUITY.md"
R12_SUBDIVISIONS = tuple(f"R12.{index}" for index in range(1, 17))
R12_ACCEPTANCE_PATHS = tuple(
    f"docs/roadmap/R12_{index}_ACCEPTANCE.md" for index in range(1, 17)
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_sha256(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _require_commit(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not _COMMIT.fullmatch(value):
        raise ValueError(f"{field} must be a 40-character lowercase commit SHA")
    return value


def _safe_source(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("evidence source must be a non-empty POSIX repository path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("evidence source escapes repository boundary")
    return path.as_posix()


@dataclass(frozen=True, slots=True)
class EvidenceBinding:
    source: str
    sha256: str
    bytes: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", _safe_source(self.source))
        _require_sha256(self.sha256, field="evidence sha256")
        if not isinstance(self.bytes, int) or isinstance(self.bytes, bool) or self.bytes <= 0:
            raise ValueError("evidence bytes must be a positive integer")

    def to_dict(self) -> dict[str, object]:
        return {"source": self.source, "sha256": self.sha256, "bytes": self.bytes}

    @classmethod
    def from_dict(cls, raw: object) -> "EvidenceBinding":
        if not isinstance(raw, dict) or set(raw) != {"source", "sha256", "bytes"}:
            raise ValueError("evidence binding has invalid keys")
        return cls(str(raw["source"]), str(raw["sha256"]), int(raw["bytes"]))


@dataclass(frozen=True, slots=True)
class SubdivisionBinding:
    subdivision: str
    source: str
    sha256: str
    bytes: int

    def __post_init__(self) -> None:
        if self.subdivision not in R12_SUBDIVISIONS:
            raise ValueError("unexpected R12 subdivision")
        expected = f"docs/roadmap/R12_{self.subdivision.split('.')[1]}_ACCEPTANCE.md"
        if _safe_source(self.source) != expected:
            raise ValueError("subdivision acceptance source mismatch")
        _require_sha256(self.sha256, field="subdivision sha256")
        if not isinstance(self.bytes, int) or isinstance(self.bytes, bool) or self.bytes <= 0:
            raise ValueError("subdivision bytes must be a positive integer")

    def to_dict(self) -> dict[str, object]:
        return {
            "subdivision": self.subdivision,
            "source": self.source,
            "sha256": self.sha256,
            "bytes": self.bytes,
        }

    @classmethod
    def from_dict(cls, raw: object) -> "SubdivisionBinding":
        if not isinstance(raw, dict) or set(raw) != {"subdivision", "source", "sha256", "bytes"}:
            raise ValueError("subdivision binding has invalid keys")
        return cls(
            str(raw["subdivision"]),
            str(raw["source"]),
            str(raw["sha256"]),
            int(raw["bytes"]),
        )


@dataclass(frozen=True, slots=True)
class PriorIntegratedBinding:
    phase: str
    source: str
    sha256: str
    bytes: int
    evidence_sha256: str

    def __post_init__(self) -> None:
        if self.phase != "R11" or self.source != R11_INTEGRATED_PATH:
            raise ValueError("R12 must bind exactly the accepted R11 integrated report")
        _require_sha256(self.sha256, field="prior report file sha256")
        _require_sha256(self.evidence_sha256, field="prior report semantic sha256")
        if self.evidence_sha256 != R11_ACCEPTED_DIGEST:
            raise ValueError("accepted R11 integrated semantic digest drift")
        if not isinstance(self.bytes, int) or isinstance(self.bytes, bool) or self.bytes <= 0:
            raise ValueError("prior report bytes must be a positive integer")

    def to_dict(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "source": self.source,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "evidence_sha256": self.evidence_sha256,
        }

    @classmethod
    def from_dict(cls, raw: object) -> "PriorIntegratedBinding":
        if not isinstance(raw, dict) or set(raw) != {
            "phase", "source", "sha256", "bytes", "evidence_sha256"
        }:
            raise ValueError("prior integrated binding has invalid keys")
        return cls(
            str(raw["phase"]),
            str(raw["source"]),
            str(raw["sha256"]),
            int(raw["bytes"]),
            str(raw["evidence_sha256"]),
        )


@dataclass(frozen=True, slots=True)
class WizardWindowsEvidence:
    schema_version: int
    generated_at: str
    source_sha: str
    project_type: str
    platform: str
    framework: str
    architecture: str
    package_kind: str
    project_dna_sha256: str
    product_sha256: str
    workspace_manifest_sha256: str
    model_sha256: str
    package_manifest_sha256: str
    artifact_count: int
    build_returncode: int
    test_returncode: int
    test_sentinel: str
    status: str
    blockers: tuple[str, ...]
    evidence_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported R12 Windows CI evidence schema")
        if not isinstance(self.generated_at, str) or not self.generated_at.strip():
            raise ValueError("generated_at is required")
        _require_commit(self.source_sha, field="source_sha")
        expected = {
            "project_type": (self.project_type, "desktop_app"),
            "platform": (self.platform, "windows"),
            "framework": (self.framework, "wpf"),
            "architecture": (self.architecture, "x64"),
            "package_kind": (self.package_kind, "archive"),
            "status": (self.status, "pass"),
        }
        for field, (actual, wanted) in expected.items():
            if actual != wanted:
                raise ValueError(f"{field} must be {wanted!r} for canonical R12 Windows evidence")
        for field in (
            "project_dna_sha256",
            "product_sha256",
            "workspace_manifest_sha256",
            "model_sha256",
            "package_manifest_sha256",
        ):
            _require_sha256(getattr(self, field), field=field)
        if not isinstance(self.artifact_count, int) or isinstance(self.artifact_count, bool) or self.artifact_count < 1:
            raise ValueError("artifact_count must be positive")
        if self.build_returncode != 0 or self.test_returncode != 0:
            raise ValueError("canonical Windows build and test must both return zero")
        expected_sentinel = f"KODEPOIA_WPF_TEST_PASS:{self.model_sha256}"
        if self.test_sentinel != expected_sentinel:
            raise ValueError("WPF test sentinel does not bind the accepted model digest")
        if self.blockers:
            raise ValueError("PASS Windows CI evidence cannot contain blockers")
        _require_sha256(self.evidence_sha256, field="evidence_sha256")
        if self.evidence_sha256 != canonical_sha256(self.semantic_payload()):
            raise ValueError("Windows CI evidence semantic digest mismatch")

    def semantic_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "project_type": self.project_type,
            "platform": self.platform,
            "framework": self.framework,
            "architecture": self.architecture,
            "package_kind": self.package_kind,
            "project_dna_sha256": self.project_dna_sha256,
            "product_sha256": self.product_sha256,
            "workspace_manifest_sha256": self.workspace_manifest_sha256,
            "model_sha256": self.model_sha256,
            "package_manifest_sha256": self.package_manifest_sha256,
            "artifact_count": self.artifact_count,
            "build_returncode": self.build_returncode,
            "test_returncode": self.test_returncode,
            "test_sentinel": self.test_sentinel,
            "status": self.status,
            "blockers": list(self.blockers),
        }

    def to_dict(self) -> dict[str, object]:
        return {
            **self.semantic_payload(),
            "generated_at": self.generated_at,
            "evidence_sha256": self.evidence_sha256,
        }

    @classmethod
    def from_dict(cls, raw: object) -> "WizardWindowsEvidence":
        if not isinstance(raw, dict):
            raise ValueError("Windows CI evidence must be a JSON object")
        required = {
            "schema_version", "generated_at", "source_sha", "project_type", "platform",
            "framework", "architecture", "package_kind", "project_dna_sha256", "product_sha256",
            "workspace_manifest_sha256", "model_sha256", "package_manifest_sha256", "artifact_count",
            "build_returncode", "test_returncode", "test_sentinel", "status", "blockers", "evidence_sha256",
        }
        if set(raw) != required:
            raise ValueError("Windows CI evidence has unknown or missing keys")
        blockers = raw["blockers"]
        if not isinstance(blockers, list) or any(not isinstance(item, str) for item in blockers):
            raise ValueError("Windows CI blockers must be an array of strings")
        return cls(
            schema_version=int(raw["schema_version"]),
            generated_at=str(raw["generated_at"]),
            source_sha=str(raw["source_sha"]),
            project_type=str(raw["project_type"]),
            platform=str(raw["platform"]),
            framework=str(raw["framework"]),
            architecture=str(raw["architecture"]),
            package_kind=str(raw["package_kind"]),
            project_dna_sha256=str(raw["project_dna_sha256"]),
            product_sha256=str(raw["product_sha256"]),
            workspace_manifest_sha256=str(raw["workspace_manifest_sha256"]),
            model_sha256=str(raw["model_sha256"]),
            package_manifest_sha256=str(raw["package_manifest_sha256"]),
            artifact_count=int(raw["artifact_count"]),
            build_returncode=int(raw["build_returncode"]),
            test_returncode=int(raw["test_returncode"]),
            test_sentinel=str(raw["test_sentinel"]),
            status=str(raw["status"]),
            blockers=tuple(blockers),
            evidence_sha256=str(raw["evidence_sha256"]),
        )


@dataclass(frozen=True, slots=True)
class WizardWindowsBinding:
    source: str
    sha256: str
    bytes: int
    source_sha: str
    evidence_sha256: str

    def __post_init__(self) -> None:
        if self.source != R12_WINDOWS_CI_PATH:
            raise ValueError("unexpected R12 Windows CI evidence source")
        _require_sha256(self.sha256, field="Windows CI file sha256")
        _require_commit(self.source_sha, field="Windows CI source_sha")
        _require_sha256(self.evidence_sha256, field="Windows CI semantic sha256")
        if not isinstance(self.bytes, int) or isinstance(self.bytes, bool) or self.bytes <= 0:
            raise ValueError("Windows CI evidence bytes must be positive")

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "source_sha": self.source_sha,
            "evidence_sha256": self.evidence_sha256,
        }

    @classmethod
    def from_dict(cls, raw: object) -> "WizardWindowsBinding":
        if not isinstance(raw, dict) or set(raw) != {
            "source", "sha256", "bytes", "source_sha", "evidence_sha256"
        }:
            raise ValueError("Windows CI binding has invalid keys")
        return cls(
            str(raw["source"]), str(raw["sha256"]), int(raw["bytes"]),
            str(raw["source_sha"]), str(raw["evidence_sha256"]),
        )


@dataclass(frozen=True, slots=True)
class R12IntegratedReport:
    schema_version: int
    generated_at: str
    source_sha: str
    continuity: EvidenceBinding
    subdivisions: tuple[SubdivisionBinding, ...]
    windows_ci: WizardWindowsBinding
    prior_phase: PriorIntegratedBinding
    manual_state: str
    status: str
    blockers: tuple[str, ...]
    evidence_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported R12 integrated report schema")
        if not self.generated_at.strip():
            raise ValueError("generated_at is required")
        _require_commit(self.source_sha, field="source_sha")
        if self.continuity.source != R12_CONTINUITY_PATH:
            raise ValueError("continuity source mismatch")
        if tuple(item.subdivision for item in self.subdivisions) != R12_SUBDIVISIONS:
            raise ValueError("R12 integrated report requires exactly R12.1 through R12.16 in order")
        if self.windows_ci.source_sha != self.source_sha:
            raise ValueError("Windows CI source SHA must match integrated implementation source SHA")
        if self.manual_state not in {"conditional_not_triggered", "conditional_satisfied"}:
            raise ValueError("R12.16 manual state is not satisfied")
        if self.status != "pass" or self.blockers:
            raise ValueError("R12 integrated report must be PASS with no blockers")
        _require_sha256(self.evidence_sha256, field="evidence_sha256")
        if self.evidence_sha256 != canonical_sha256(self.semantic_payload()):
            raise ValueError("R12 integrated semantic digest mismatch")

    def semantic_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "continuity": self.continuity.to_dict(),
            "subdivisions": [item.to_dict() for item in self.subdivisions],
            "windows_ci": self.windows_ci.to_dict(),
            "prior_phase": self.prior_phase.to_dict(),
            "manual_state": self.manual_state,
            "status": self.status,
            "blockers": list(self.blockers),
        }

    def to_dict(self) -> dict[str, object]:
        return {
            **self.semantic_payload(),
            "generated_at": self.generated_at,
            "evidence_sha256": self.evidence_sha256,
        }

    @classmethod
    def from_dict(cls, raw: object) -> "R12IntegratedReport":
        if not isinstance(raw, dict):
            raise ValueError("R12 integrated report must be a JSON object")
        required = {
            "schema_version", "generated_at", "source_sha", "continuity", "subdivisions",
            "windows_ci", "prior_phase", "manual_state", "status", "blockers", "evidence_sha256",
        }
        if set(raw) != required:
            raise ValueError("R12 integrated report has unknown or missing keys")
        subdivisions = raw["subdivisions"]
        blockers = raw["blockers"]
        if not isinstance(subdivisions, list) or not isinstance(blockers, list):
            raise ValueError("R12 subdivisions/blockers must be arrays")
        report = cls(
            schema_version=int(raw["schema_version"]),
            generated_at=str(raw["generated_at"]),
            source_sha=str(raw["source_sha"]),
            continuity=EvidenceBinding.from_dict(raw["continuity"]),
            subdivisions=tuple(SubdivisionBinding.from_dict(item) for item in subdivisions),
            windows_ci=WizardWindowsBinding.from_dict(raw["windows_ci"]),
            prior_phase=PriorIntegratedBinding.from_dict(raw["prior_phase"]),
            manual_state=str(raw["manual_state"]),
            status=str(raw["status"]),
            blockers=tuple(str(item) for item in blockers),
            evidence_sha256=str(raw["evidence_sha256"]),
        )
        return report


def bind_repository_file(source: str, read_bytes: Callable[[str], bytes]) -> EvidenceBinding:
    source = _safe_source(source)
    payload = read_bytes(source)
    if not isinstance(payload, bytes) or not payload:
        raise ValueError(f"repository evidence is missing or empty: {source}")
    return EvidenceBinding(source, hashlib.sha256(payload).hexdigest(), len(payload))


def _load_windows_ci(read_bytes: Callable[[str], bytes]) -> tuple[WizardWindowsEvidence, EvidenceBinding]:
    binding = bind_repository_file(R12_WINDOWS_CI_PATH, read_bytes)
    try:
        raw = json.loads(read_bytes(R12_WINDOWS_CI_PATH))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("R12 Windows CI evidence is not valid UTF-8 JSON") from exc
    return WizardWindowsEvidence.from_dict(raw), binding


def _load_prior(read_bytes: Callable[[str], bytes]) -> tuple[dict[str, object], EvidenceBinding]:
    binding = bind_repository_file(R11_INTEGRATED_PATH, read_bytes)
    try:
        raw = json.loads(read_bytes(R11_INTEGRATED_PATH))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("R11 integrated evidence is not valid UTF-8 JSON") from exc
    if not isinstance(raw, dict):
        raise ValueError("R11 integrated evidence must be a JSON object")
    if raw.get("status") != "pass" or raw.get("blockers") != []:
        raise ValueError("R11 integrated evidence is not PASS")
    if raw.get("evidence_sha256") != R11_ACCEPTED_DIGEST:
        raise ValueError("accepted R11 integrated semantic digest drift")
    return raw, binding


def build_repository_report(
    *,
    source_sha: str,
    generated_at: str,
    read_bytes: Callable[[str], bytes],
    manual_state: str = "conditional_not_triggered",
) -> R12IntegratedReport:
    _require_commit(source_sha, field="source_sha")
    continuity = bind_repository_file(R12_CONTINUITY_PATH, read_bytes)
    subdivisions: list[SubdivisionBinding] = []
    for subdivision, path in zip(R12_SUBDIVISIONS, R12_ACCEPTANCE_PATHS, strict=True):
        bound = bind_repository_file(path, read_bytes)
        subdivisions.append(SubdivisionBinding(subdivision, path, bound.sha256, bound.bytes))
    windows, windows_file = _load_windows_ci(read_bytes)
    if windows.source_sha != source_sha:
        raise ValueError("Windows CI evidence was not produced from the immutable implementation head")
    prior, prior_file = _load_prior(read_bytes)
    report_without_digest = {
        "schema_version": 1,
        "source_sha": source_sha,
        "continuity": continuity.to_dict(),
        "subdivisions": [item.to_dict() for item in subdivisions],
        "windows_ci": WizardWindowsBinding(
            R12_WINDOWS_CI_PATH,
            windows_file.sha256,
            windows_file.bytes,
            windows.source_sha,
            windows.evidence_sha256,
        ).to_dict(),
        "prior_phase": PriorIntegratedBinding(
            "R11",
            R11_INTEGRATED_PATH,
            prior_file.sha256,
            prior_file.bytes,
            str(prior["evidence_sha256"]),
        ).to_dict(),
        "manual_state": manual_state,
        "status": "pass",
        "blockers": [],
    }
    return R12IntegratedReport(
        schema_version=1,
        generated_at=generated_at,
        source_sha=source_sha,
        continuity=continuity,
        subdivisions=tuple(subdivisions),
        windows_ci=WizardWindowsBinding.from_dict(report_without_digest["windows_ci"]),
        prior_phase=PriorIntegratedBinding.from_dict(report_without_digest["prior_phase"]),
        manual_state=manual_state,
        status="pass",
        blockers=(),
        evidence_sha256=canonical_sha256(report_without_digest),
    )


def validate_repository_evidence(
    report: R12IntegratedReport,
    read_bytes: Callable[[str], bytes],
) -> None:
    if report.status != "pass" or report.blockers:
        raise ValueError("R12 integrated report is not PASS")
    current_continuity = bind_repository_file(report.continuity.source, read_bytes)
    if current_continuity != report.continuity:
        raise ValueError("continuity evidence identity mismatch")
    for expected, recorded in zip(R12_SUBDIVISIONS, report.subdivisions, strict=True):
        if recorded.subdivision != expected:
            raise ValueError("R12 subdivision ordering mismatch")
        rebound = bind_repository_file(recorded.source, read_bytes)
        if rebound.sha256 != recorded.sha256 or rebound.bytes != recorded.bytes:
            raise ValueError(f"subdivision acceptance identity mismatch: {recorded.subdivision}")
    windows, windows_file = _load_windows_ci(read_bytes)
    if windows.source_sha != report.source_sha:
        raise ValueError("Windows CI evidence source SHA mismatch")
    if (
        windows_file.sha256 != report.windows_ci.sha256
        or windows_file.bytes != report.windows_ci.bytes
        or windows.evidence_sha256 != report.windows_ci.evidence_sha256
    ):
        raise ValueError("Windows CI evidence identity mismatch")
    prior, prior_file = _load_prior(read_bytes)
    if (
        prior_file.sha256 != report.prior_phase.sha256
        or prior_file.bytes != report.prior_phase.bytes
        or prior.get("evidence_sha256") != report.prior_phase.evidence_sha256
    ):
        raise ValueError("prior integrated evidence identity mismatch")
    if report.evidence_sha256 != canonical_sha256(report.semantic_payload()):
        raise ValueError("R12 integrated semantic digest mismatch")
