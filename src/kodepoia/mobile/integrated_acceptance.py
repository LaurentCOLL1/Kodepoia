from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Callable, Iterable

R12_INTEGRATED_PATH = "docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json"
R12_ACCEPTED_DIGEST = "daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50"
R13_CI_PATH = "docs/roadmap/R13_17_CI_ACCEPTANCE.json"
R13_CONTINUITY_PATH = "docs/continuity/KODEPOIA_CONTINUITY.md"
R13_SUBDIVISIONS = tuple(f"R13.{index}" for index in range(1, 18))
R13_ACCEPTANCE_PATHS = tuple(f"docs/roadmap/R13_{index}_ACCEPTANCE.md" for index in range(1, 18))
R13_INTEGRATED_REPORT_PATH = "docs/roadmap/R13_INTEGRATED_ACCEPTANCE.json"

REQUIRED_RUNS = (
    "R0 Repository Guard",
    "Python Core",
    "KodeStudio UI Smoke",
    "R13 Android Build Acceptance",
    "R13 Android Signing Acceptance",
    "R13 Android Device Acceptance",
    "R13 Google Play Readiness Acceptance",
    "R13 Apple Xcode Acceptance",
    "R13 Apple SwiftUI Scaffold Acceptance",
    "R13 Apple Signing Archive Acceptance",
    "R13 Apple XCTest Acceptance",
    "R13 Integrated Release Readiness",
)
REQUIRED_ARTIFACT_KINDS = ("android_build", "android_device", "apple_xctest")
_ARTIFACT_RUN = {
    "android_build": "R13 Android Build Acceptance",
    "android_device": "R13 Android Device Acceptance",
    "apple_xctest": "R13 Apple XCTest Acceptance",
}
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
        if self.subdivision not in R13_SUBDIVISIONS:
            raise ValueError("unexpected R13 subdivision")
        expected = f"docs/roadmap/R13_{self.subdivision.split('.')[1]}_ACCEPTANCE.md"
        if _safe_source(self.source) != expected:
            raise ValueError("subdivision acceptance source mismatch")
        _require_sha256(self.sha256, field="subdivision sha256")
        if not isinstance(self.bytes, int) or isinstance(self.bytes, bool) or self.bytes <= 0:
            raise ValueError("subdivision bytes must be positive")

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
        if self.phase != "R12" or self.source != R12_INTEGRATED_PATH:
            raise ValueError("R13 must bind exactly the accepted R12 integrated report")
        _require_sha256(self.sha256, field="prior report file sha256")
        _require_sha256(self.evidence_sha256, field="prior report semantic sha256")
        if self.evidence_sha256 != R12_ACCEPTED_DIGEST:
            raise ValueError("accepted R12 integrated semantic digest drift")
        if not isinstance(self.bytes, int) or isinstance(self.bytes, bool) or self.bytes <= 0:
            raise ValueError("prior report bytes must be positive")

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
        required = {"phase", "source", "sha256", "bytes", "evidence_sha256"}
        if not isinstance(raw, dict) or set(raw) != required:
            raise ValueError("prior integrated binding has invalid keys")
        return cls(
            str(raw["phase"]),
            str(raw["source"]),
            str(raw["sha256"]),
            int(raw["bytes"]),
            str(raw["evidence_sha256"]),
        )


@dataclass(frozen=True, slots=True)
class WorkflowRunBinding:
    name: str
    run_id: int
    run_number: int
    conclusion: str

    def __post_init__(self) -> None:
        if self.name not in REQUIRED_RUNS:
            raise ValueError(f"unexpected R13.17 workflow run: {self.name}")
        if not isinstance(self.run_id, int) or isinstance(self.run_id, bool) or self.run_id <= 0:
            raise ValueError("run_id must be positive")
        if not isinstance(self.run_number, int) or isinstance(self.run_number, bool) or self.run_number <= 0:
            raise ValueError("run_number must be positive")
        if self.conclusion != "success":
            raise ValueError(f"required workflow must conclude success: {self.name}")

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "run_id": self.run_id,
            "run_number": self.run_number,
            "conclusion": self.conclusion,
        }

    @classmethod
    def from_dict(cls, raw: object) -> "WorkflowRunBinding":
        if not isinstance(raw, dict) or set(raw) != {"name", "run_id", "run_number", "conclusion"}:
            raise ValueError("workflow run binding has invalid keys")
        return cls(
            str(raw["name"]),
            int(raw["run_id"]),
            int(raw["run_number"]),
            str(raw["conclusion"]),
        )


@dataclass(frozen=True, slots=True)
class WorkflowArtifactBinding:
    kind: str
    run_name: str
    artifact_id: int
    name: str
    sha256: str

    def __post_init__(self) -> None:
        if self.kind not in REQUIRED_ARTIFACT_KINDS:
            raise ValueError(f"unexpected integrated artifact kind: {self.kind}")
        if self.run_name != _ARTIFACT_RUN[self.kind]:
            raise ValueError("integrated artifact is bound to the wrong workflow")
        if not isinstance(self.artifact_id, int) or isinstance(self.artifact_id, bool) or self.artifact_id <= 0:
            raise ValueError("artifact_id must be positive")
        if not isinstance(self.name, str) or not self.name.strip() or "\x00" in self.name:
            raise ValueError("artifact name is required")
        _require_sha256(self.sha256, field="artifact sha256")

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "run_name": self.run_name,
            "artifact_id": self.artifact_id,
            "name": self.name,
            "sha256": self.sha256,
        }

    @classmethod
    def from_dict(cls, raw: object) -> "WorkflowArtifactBinding":
        required = {"kind", "run_name", "artifact_id", "name", "sha256"}
        if not isinstance(raw, dict) or set(raw) != required:
            raise ValueError("workflow artifact binding has invalid keys")
        return cls(
            str(raw["kind"]),
            str(raw["run_name"]),
            int(raw["artifact_id"]),
            str(raw["name"]),
            str(raw["sha256"]),
        )


@dataclass(frozen=True, slots=True)
class IntegratedClaims:
    android_hosted_build: bool = True
    android_target_api: int = 36
    android_package_kinds: tuple[str, ...] = ("aab", "apk")
    android_device_scope: str = "VIRTUAL"
    android_physical_device_claim: bool = False
    ios_hosted_build_test: bool = True
    ios_scope: str = "SIMULATOR"
    apple_physical_device_claim: bool = False
    live_store_query_attempted: bool = False
    production_signing_credential_used: bool = False

    def __post_init__(self) -> None:
        if self.android_hosted_build is not True:
            raise ValueError("canonical Android hosted build must be proven")
        if self.android_target_api != 36:
            raise ValueError("canonical R13 Android evidence must target API 36")
        if tuple(self.android_package_kinds) != ("aab", "apk"):
            raise ValueError("canonical Android evidence must bind AAB and APK")
        if self.android_device_scope != "VIRTUAL" or self.android_physical_device_claim is not False:
            raise ValueError("virtual Android evidence cannot manufacture physical-device proof")
        if self.ios_hosted_build_test is not True:
            raise ValueError("canonical iOS hosted build/test must be proven")
        if self.ios_scope != "SIMULATOR" or self.apple_physical_device_claim is not False:
            raise ValueError("simulator evidence cannot manufacture Apple physical-device proof")
        if self.live_store_query_attempted is not False:
            raise ValueError("core integrated PASS cannot require or claim a live store query")
        if self.production_signing_credential_used is not False:
            raise ValueError("core integrated PASS cannot claim production signing credentials")

    def to_dict(self) -> dict[str, object]:
        return {
            "android_hosted_build": self.android_hosted_build,
            "android_target_api": self.android_target_api,
            "android_package_kinds": list(self.android_package_kinds),
            "android_device_scope": self.android_device_scope,
            "android_physical_device_claim": self.android_physical_device_claim,
            "ios_hosted_build_test": self.ios_hosted_build_test,
            "ios_scope": self.ios_scope,
            "apple_physical_device_claim": self.apple_physical_device_claim,
            "live_store_query_attempted": self.live_store_query_attempted,
            "production_signing_credential_used": self.production_signing_credential_used,
        }

    @classmethod
    def from_dict(cls, raw: object) -> "IntegratedClaims":
        required = {
            "android_hosted_build",
            "android_target_api",
            "android_package_kinds",
            "android_device_scope",
            "android_physical_device_claim",
            "ios_hosted_build_test",
            "ios_scope",
            "apple_physical_device_claim",
            "live_store_query_attempted",
            "production_signing_credential_used",
        }
        if not isinstance(raw, dict) or set(raw) != required:
            raise ValueError("integrated claims have invalid keys")
        packages = raw["android_package_kinds"]
        if not isinstance(packages, list) or any(not isinstance(item, str) for item in packages):
            raise ValueError("android_package_kinds must be an array of strings")
        for field in (
            "android_hosted_build",
            "android_physical_device_claim",
            "ios_hosted_build_test",
            "apple_physical_device_claim",
            "live_store_query_attempted",
            "production_signing_credential_used",
        ):
            if not isinstance(raw[field], bool):
                raise ValueError(f"{field} must be boolean")
        target_api = raw["android_target_api"]
        if not isinstance(target_api, int) or isinstance(target_api, bool):
            raise ValueError("android_target_api must be an integer")
        return cls(
            android_hosted_build=raw["android_hosted_build"],
            android_target_api=target_api,
            android_package_kinds=tuple(packages),
            android_device_scope=str(raw["android_device_scope"]),
            android_physical_device_claim=raw["android_physical_device_claim"],
            ios_hosted_build_test=raw["ios_hosted_build_test"],
            ios_scope=str(raw["ios_scope"]),
            apple_physical_device_claim=raw["apple_physical_device_claim"],
            live_store_query_attempted=raw["live_store_query_attempted"],
            production_signing_credential_used=raw["production_signing_credential_used"],
        )


@dataclass(frozen=True, slots=True)
class R13IntegratedCIEvidence:
    schema_version: int
    generated_at: str
    source_sha: str
    runs: tuple[WorkflowRunBinding, ...]
    artifacts: tuple[WorkflowArtifactBinding, ...]
    claims: IntegratedClaims
    manual_state: str
    status: str
    blockers: tuple[str, ...]
    evidence_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported R13 integrated CI evidence schema")
        if not isinstance(self.generated_at, str) or not self.generated_at.strip():
            raise ValueError("generated_at is required")
        _require_commit(self.source_sha, field="source_sha")
        if tuple(item.name for item in self.runs) != REQUIRED_RUNS:
            raise ValueError("R13 integrated CI evidence requires the exact ordered workflow set")
        if len({item.run_id for item in self.runs}) != len(self.runs):
            raise ValueError("workflow run ids must be unique")
        if tuple(item.kind for item in self.artifacts) != REQUIRED_ARTIFACT_KINDS:
            raise ValueError("R13 integrated CI evidence requires exact platform artifact kinds")
        if len({item.artifact_id for item in self.artifacts}) != len(self.artifacts):
            raise ValueError("workflow artifact ids must be unique")
        run_names = {item.name for item in self.runs}
        if any(item.run_name not in run_names for item in self.artifacts):
            raise ValueError("artifact workflow is not present in required run set")
        if self.manual_state not in {"conditional_not_triggered", "conditional_satisfied"}:
            raise ValueError("R13.17 conditional manual state is not satisfied")
        if self.status != "pass" or self.blockers:
            raise ValueError("R13 integrated CI evidence must be PASS with no blockers")
        _require_sha256(self.evidence_sha256, field="evidence_sha256")
        if self.evidence_sha256 != canonical_sha256(self.semantic_payload()):
            raise ValueError("R13 integrated CI semantic digest mismatch")

    def semantic_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "runs": [item.to_dict() for item in self.runs],
            "artifacts": [item.to_dict() for item in self.artifacts],
            "claims": self.claims.to_dict(),
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
    def from_dict(cls, raw: object) -> "R13IntegratedCIEvidence":
        required = {
            "schema_version",
            "generated_at",
            "source_sha",
            "runs",
            "artifacts",
            "claims",
            "manual_state",
            "status",
            "blockers",
            "evidence_sha256",
        }
        if not isinstance(raw, dict) or set(raw) != required:
            raise ValueError("R13 integrated CI evidence has unknown or missing keys")
        runs = raw["runs"]
        artifacts = raw["artifacts"]
        blockers = raw["blockers"]
        if not isinstance(runs, list) or not isinstance(artifacts, list) or not isinstance(blockers, list):
            raise ValueError("R13 integrated CI runs/artifacts/blockers must be arrays")
        if any(not isinstance(item, str) for item in blockers):
            raise ValueError("R13 integrated CI blockers must be strings")
        return cls(
            schema_version=int(raw["schema_version"]),
            generated_at=str(raw["generated_at"]),
            source_sha=str(raw["source_sha"]),
            runs=tuple(WorkflowRunBinding.from_dict(item) for item in runs),
            artifacts=tuple(WorkflowArtifactBinding.from_dict(item) for item in artifacts),
            claims=IntegratedClaims.from_dict(raw["claims"]),
            manual_state=str(raw["manual_state"]),
            status=str(raw["status"]),
            blockers=tuple(blockers),
            evidence_sha256=str(raw["evidence_sha256"]),
        )


@dataclass(frozen=True, slots=True)
class CIEvidenceBinding:
    source: str
    sha256: str
    bytes: int
    source_sha: str
    evidence_sha256: str

    def __post_init__(self) -> None:
        if self.source != R13_CI_PATH:
            raise ValueError("unexpected R13 integrated CI evidence source")
        _require_sha256(self.sha256, field="CI file sha256")
        _require_commit(self.source_sha, field="CI source_sha")
        _require_sha256(self.evidence_sha256, field="CI semantic sha256")
        if not isinstance(self.bytes, int) or isinstance(self.bytes, bool) or self.bytes <= 0:
            raise ValueError("CI evidence bytes must be positive")

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "source_sha": self.source_sha,
            "evidence_sha256": self.evidence_sha256,
        }

    @classmethod
    def from_dict(cls, raw: object) -> "CIEvidenceBinding":
        required = {"source", "sha256", "bytes", "source_sha", "evidence_sha256"}
        if not isinstance(raw, dict) or set(raw) != required:
            raise ValueError("CI evidence binding has invalid keys")
        return cls(
            str(raw["source"]),
            str(raw["sha256"]),
            int(raw["bytes"]),
            str(raw["source_sha"]),
            str(raw["evidence_sha256"]),
        )


@dataclass(frozen=True, slots=True)
class R13IntegratedReport:
    schema_version: int
    generated_at: str
    source_sha: str
    continuity: EvidenceBinding
    subdivisions: tuple[SubdivisionBinding, ...]
    ci: CIEvidenceBinding
    prior_phase: PriorIntegratedBinding
    manual_state: str
    status: str
    blockers: tuple[str, ...]
    evidence_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported R13 integrated report schema")
        if not isinstance(self.generated_at, str) or not self.generated_at.strip():
            raise ValueError("generated_at is required")
        _require_commit(self.source_sha, field="source_sha")
        if self.continuity.source != R13_CONTINUITY_PATH:
            raise ValueError("continuity source mismatch")
        if tuple(item.subdivision for item in self.subdivisions) != R13_SUBDIVISIONS:
            raise ValueError("R13 integrated report requires exactly R13.1 through R13.17 in order")
        if self.ci.source_sha != self.source_sha:
            raise ValueError("CI source SHA must match immutable R13.17 implementation source SHA")
        if self.manual_state not in {"conditional_not_triggered", "conditional_satisfied"}:
            raise ValueError("R13.17 conditional manual state is not satisfied")
        if self.status != "pass" or self.blockers:
            raise ValueError("R13 integrated report must be PASS with no blockers")
        _require_sha256(self.evidence_sha256, field="evidence_sha256")
        if self.evidence_sha256 != canonical_sha256(self.semantic_payload()):
            raise ValueError("R13 integrated semantic digest mismatch")

    def semantic_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "continuity": self.continuity.to_dict(),
            "subdivisions": [item.to_dict() for item in self.subdivisions],
            "ci": self.ci.to_dict(),
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
    def from_dict(cls, raw: object) -> "R13IntegratedReport":
        required = {
            "schema_version",
            "generated_at",
            "source_sha",
            "continuity",
            "subdivisions",
            "ci",
            "prior_phase",
            "manual_state",
            "status",
            "blockers",
            "evidence_sha256",
        }
        if not isinstance(raw, dict) or set(raw) != required:
            raise ValueError("R13 integrated report has unknown or missing keys")
        subdivisions = raw["subdivisions"]
        blockers = raw["blockers"]
        if not isinstance(subdivisions, list) or not isinstance(blockers, list):
            raise ValueError("R13 subdivisions/blockers must be arrays")
        if any(not isinstance(item, str) for item in blockers):
            raise ValueError("R13 blockers must be strings")
        return cls(
            schema_version=int(raw["schema_version"]),
            generated_at=str(raw["generated_at"]),
            source_sha=str(raw["source_sha"]),
            continuity=EvidenceBinding.from_dict(raw["continuity"]),
            subdivisions=tuple(SubdivisionBinding.from_dict(item) for item in subdivisions),
            ci=CIEvidenceBinding.from_dict(raw["ci"]),
            prior_phase=PriorIntegratedBinding.from_dict(raw["prior_phase"]),
            manual_state=str(raw["manual_state"]),
            status=str(raw["status"]),
            blockers=tuple(blockers),
            evidence_sha256=str(raw["evidence_sha256"]),
        )


def bind_repository_file(source: str, read_bytes: Callable[[str], bytes]) -> EvidenceBinding:
    source = _safe_source(source)
    payload = read_bytes(source)
    if not isinstance(payload, bytes) or not payload:
        raise ValueError(f"repository evidence is missing or empty: {source}")
    return EvidenceBinding(source, hashlib.sha256(payload).hexdigest(), len(payload))


def _load_json(path: str, read_bytes: Callable[[str], bytes], *, label: str) -> tuple[dict[str, object], EvidenceBinding]:
    binding = bind_repository_file(path, read_bytes)
    try:
        raw = json.loads(read_bytes(path))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"{label} must be a JSON object")
    return raw, binding


def load_ci_evidence(read_bytes: Callable[[str], bytes]) -> tuple[R13IntegratedCIEvidence, EvidenceBinding]:
    raw, binding = _load_json(R13_CI_PATH, read_bytes, label="R13 integrated CI evidence")
    return R13IntegratedCIEvidence.from_dict(raw), binding


def load_prior_evidence(read_bytes: Callable[[str], bytes]) -> tuple[dict[str, object], EvidenceBinding]:
    raw, binding = _load_json(R12_INTEGRATED_PATH, read_bytes, label="R12 integrated evidence")
    if raw.get("status") != "pass" or raw.get("blockers") != []:
        raise ValueError("R12 integrated evidence is not PASS")
    if raw.get("evidence_sha256") != R12_ACCEPTED_DIGEST:
        raise ValueError("accepted R12 integrated semantic digest drift")
    return raw, binding


def build_ci_evidence(
    *,
    source_sha: str,
    generated_at: str,
    runs: Iterable[WorkflowRunBinding],
    artifacts: Iterable[WorkflowArtifactBinding],
    manual_state: str = "conditional_not_triggered",
) -> R13IntegratedCIEvidence:
    ordered_runs = tuple(runs)
    ordered_artifacts = tuple(artifacts)
    semantic = {
        "schema_version": 1,
        "source_sha": source_sha,
        "runs": [item.to_dict() for item in ordered_runs],
        "artifacts": [item.to_dict() for item in ordered_artifacts],
        "claims": IntegratedClaims().to_dict(),
        "manual_state": manual_state,
        "status": "pass",
        "blockers": [],
    }
    return R13IntegratedCIEvidence(
        schema_version=1,
        generated_at=generated_at,
        source_sha=source_sha,
        runs=ordered_runs,
        artifacts=ordered_artifacts,
        claims=IntegratedClaims(),
        manual_state=manual_state,
        status="pass",
        blockers=(),
        evidence_sha256=canonical_sha256(semantic),
    )


def build_repository_report(
    *,
    source_sha: str,
    generated_at: str,
    read_bytes: Callable[[str], bytes],
) -> R13IntegratedReport:
    _require_commit(source_sha, field="source_sha")
    continuity = bind_repository_file(R13_CONTINUITY_PATH, read_bytes)
    subdivisions: list[SubdivisionBinding] = []
    for subdivision, path in zip(R13_SUBDIVISIONS, R13_ACCEPTANCE_PATHS, strict=True):
        bound = bind_repository_file(path, read_bytes)
        subdivisions.append(SubdivisionBinding(subdivision, path, bound.sha256, bound.bytes))
    ci, ci_file = load_ci_evidence(read_bytes)
    if ci.source_sha != source_sha:
        raise ValueError("R13 CI evidence was not produced from the immutable implementation head")
    prior, prior_file = load_prior_evidence(read_bytes)
    ci_binding = CIEvidenceBinding(
        R13_CI_PATH,
        ci_file.sha256,
        ci_file.bytes,
        ci.source_sha,
        ci.evidence_sha256,
    )
    prior_binding = PriorIntegratedBinding(
        "R12",
        R12_INTEGRATED_PATH,
        prior_file.sha256,
        prior_file.bytes,
        str(prior["evidence_sha256"]),
    )
    semantic = {
        "schema_version": 1,
        "source_sha": source_sha,
        "continuity": continuity.to_dict(),
        "subdivisions": [item.to_dict() for item in subdivisions],
        "ci": ci_binding.to_dict(),
        "prior_phase": prior_binding.to_dict(),
        "manual_state": ci.manual_state,
        "status": "pass",
        "blockers": [],
    }
    return R13IntegratedReport(
        schema_version=1,
        generated_at=generated_at,
        source_sha=source_sha,
        continuity=continuity,
        subdivisions=tuple(subdivisions),
        ci=ci_binding,
        prior_phase=prior_binding,
        manual_state=ci.manual_state,
        status="pass",
        blockers=(),
        evidence_sha256=canonical_sha256(semantic),
    )


def validate_repository_evidence(
    report: R13IntegratedReport,
    read_bytes: Callable[[str], bytes],
) -> None:
    if report.status != "pass" or report.blockers:
        raise ValueError("R13 integrated report is not PASS")
    current_continuity = bind_repository_file(report.continuity.source, read_bytes)
    if current_continuity != report.continuity:
        raise ValueError("continuity evidence identity mismatch")
    for expected, recorded in zip(R13_SUBDIVISIONS, report.subdivisions, strict=True):
        if recorded.subdivision != expected:
            raise ValueError("R13 subdivision ordering mismatch")
        rebound = bind_repository_file(recorded.source, read_bytes)
        if rebound.sha256 != recorded.sha256 or rebound.bytes != recorded.bytes:
            raise ValueError(f"subdivision acceptance identity mismatch: {recorded.subdivision}")
    ci, ci_file = load_ci_evidence(read_bytes)
    if ci.source_sha != report.source_sha:
        raise ValueError("R13 CI evidence source SHA mismatch")
    if ci.manual_state != report.manual_state:
        raise ValueError("R13 CI/manual-state mismatch")
    if (
        ci_file.sha256 != report.ci.sha256
        or ci_file.bytes != report.ci.bytes
        or ci.evidence_sha256 != report.ci.evidence_sha256
    ):
        raise ValueError("R13 integrated CI evidence identity mismatch")
    prior, prior_file = load_prior_evidence(read_bytes)
    if (
        prior_file.sha256 != report.prior_phase.sha256
        or prior_file.bytes != report.prior_phase.bytes
        or prior["evidence_sha256"] != report.prior_phase.evidence_sha256
    ):
        raise ValueError("R12 integrated evidence identity mismatch")
