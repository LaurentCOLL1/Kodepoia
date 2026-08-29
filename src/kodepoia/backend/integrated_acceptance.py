from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Callable, Iterable

R13_INTEGRATED_PATH = "docs/roadmap/R13_INTEGRATED_ACCEPTANCE.json"
R13_ACCEPTED_DIGEST = "831b155fce200eae6b9fbe91c8eb44e992ea036c0922e508171644b497a4c3c7"
R14_CI_PATH = "docs/roadmap/R14_17_CI_ACCEPTANCE.json"
R14_SCENARIO_PATH = "docs/roadmap/R14_17_SCENARIO_EVIDENCE.json"
R14_DESIGN_PATH = "docs/roadmap/R14_17_DESIGN.md"
R14_INTEGRATED_REPORT_PATH = "docs/roadmap/R14_INTEGRATED_ACCEPTANCE.json"
R14_SUBDIVISION_PATHS = tuple(f"docs/roadmap/R14_{index}_ACCEPTANCE.md" for index in range(1, 17))

REQUIRED_RUNS = (
    "R0 Repository Guard",
    "Python Core",
    "KodeStudio UI Smoke",
    "R14 Integrated Acceptance",
)
REQUIRED_ARTIFACT_KINDS = ("integrated_scenario",)

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
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _require_commit(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _COMMIT.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase 40-character commit SHA")
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
            raise ValueError("evidence bytes must be positive")

    def to_dict(self) -> dict[str, object]:
        return {"source": self.source, "sha256": self.sha256, "bytes": self.bytes}

    @classmethod
    def from_dict(cls, raw: object) -> "EvidenceBinding":
        if not isinstance(raw, dict) or set(raw) != {"source", "sha256", "bytes"}:
            raise ValueError("evidence binding has invalid keys")
        return cls(str(raw["source"]), str(raw["sha256"]), int(raw["bytes"]))


@dataclass(frozen=True, slots=True)
class WorkflowRunBinding:
    name: str
    run_id: int
    run_number: int
    conclusion: str = "success"

    def __post_init__(self) -> None:
        if self.name not in REQUIRED_RUNS:
            raise ValueError(f"unexpected R14.17 workflow run: {self.name}")
        if not isinstance(self.run_id, int) or isinstance(self.run_id, bool) or self.run_id <= 0:
            raise ValueError("run_id must be positive")
        if not isinstance(self.run_number, int) or isinstance(self.run_number, bool) or self.run_number <= 0:
            raise ValueError("run_number must be positive")
        if self.conclusion != "success":
            raise ValueError(f"required workflow did not succeed: {self.name}")

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
            raise ValueError("unexpected R14.17 artifact kind")
        if self.run_name != "R14 Integrated Acceptance":
            raise ValueError("integrated scenario artifact must come from the integrated workflow")
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
class IntegratedCIEvidence:
    schema_version: int
    generated_at: str
    source_sha: str
    runs: tuple[WorkflowRunBinding, ...]
    artifacts: tuple[WorkflowArtifactBinding, ...]
    manual_state: str
    provider_live_claim: bool
    secrets_exposed: bool
    status: str
    blockers: tuple[str, ...]
    evidence_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported R14.17 CI evidence schema")
        if not isinstance(self.generated_at, str) or not self.generated_at.strip():
            raise ValueError("generated_at is required")
        _require_commit(self.source_sha, field="source_sha")
        if tuple(item.name for item in self.runs) != REQUIRED_RUNS:
            raise ValueError("R14.17 CI evidence requires the exact ordered workflow set")
        if len({item.run_id for item in self.runs}) != len(self.runs):
            raise ValueError("workflow run ids must be unique")
        if tuple(item.kind for item in self.artifacts) != REQUIRED_ARTIFACT_KINDS:
            raise ValueError("R14.17 CI evidence requires the integrated scenario artifact")
        if self.manual_state != "conditional_not_triggered":
            raise ValueError("core R14.17 closes only while conditional manual work is not triggered")
        if self.provider_live_claim is not False or self.secrets_exposed is not False:
            raise ValueError("sandbox/local evidence cannot manufacture provider-live or secret claims")
        if self.status != "pass" or self.blockers:
            raise ValueError("accepted R14.17 CI evidence must be blocker-free pass")
        _require_sha256(self.evidence_sha256, field="CI evidence_sha256")
        if self.evidence_sha256 != canonical_sha256(self.payload_without_digest()):
            raise ValueError("R14.17 CI evidence digest mismatch")

    def payload_without_digest(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "source_sha": self.source_sha,
            "runs": [item.to_dict() for item in self.runs],
            "artifacts": [item.to_dict() for item in self.artifacts],
            "manual_state": self.manual_state,
            "provider_live_claim": self.provider_live_claim,
            "secrets_exposed": self.secrets_exposed,
            "status": self.status,
            "blockers": list(self.blockers),
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.payload_without_digest(), "evidence_sha256": self.evidence_sha256}

    @classmethod
    def from_dict(cls, raw: object) -> "IntegratedCIEvidence":
        required = {
            "schema_version", "generated_at", "source_sha", "runs", "artifacts",
            "manual_state", "provider_live_claim", "secrets_exposed", "status", "blockers",
            "evidence_sha256",
        }
        if not isinstance(raw, dict) or set(raw) != required:
            raise ValueError("R14.17 CI evidence has invalid keys")
        runs_raw = raw["runs"]
        artifacts_raw = raw["artifacts"]
        blockers_raw = raw["blockers"]
        if not isinstance(runs_raw, list) or not isinstance(artifacts_raw, list) or not isinstance(blockers_raw, list):
            raise ValueError("R14.17 CI evidence arrays are invalid")
        return cls(
            schema_version=int(raw["schema_version"]),
            generated_at=str(raw["generated_at"]),
            source_sha=str(raw["source_sha"]),
            runs=tuple(WorkflowRunBinding.from_dict(item) for item in runs_raw),
            artifacts=tuple(WorkflowArtifactBinding.from_dict(item) for item in artifacts_raw),
            manual_state=str(raw["manual_state"]),
            provider_live_claim=raw["provider_live_claim"] if isinstance(raw["provider_live_claim"], bool) else True,
            secrets_exposed=raw["secrets_exposed"] if isinstance(raw["secrets_exposed"], bool) else True,
            status=str(raw["status"]),
            blockers=tuple(str(item) for item in blockers_raw),
            evidence_sha256=str(raw["evidence_sha256"]),
        )


@dataclass(frozen=True, slots=True)
class IntegratedReport:
    schema_version: int
    generated_at: str
    source_sha: str
    prior_phase: EvidenceBinding
    subdivision_acceptance: tuple[EvidenceBinding, ...]
    design: EvidenceBinding
    scenario: EvidenceBinding
    ci: EvidenceBinding
    manual_state: str
    provider_live_claim: bool
    secrets_exposed: bool
    pii_exposed: bool
    production_publish_claim: bool
    status: str
    blockers: tuple[str, ...]
    evidence_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported R14 integrated report schema")
        if not isinstance(self.generated_at, str) or not self.generated_at.strip():
            raise ValueError("generated_at is required")
        _require_commit(self.source_sha, field="source_sha")
        if self.prior_phase.source != R13_INTEGRATED_PATH:
            raise ValueError("R14 must bind the accepted R13 integrated report")
        if len(self.subdivision_acceptance) != 16:
            raise ValueError("R14 report must bind R14.1-R14.16 acceptance docs exactly once")
        if tuple(item.source for item in self.subdivision_acceptance) != R14_SUBDIVISION_PATHS:
            raise ValueError("R14 subdivision acceptance binding order/path mismatch")
        if self.design.source != R14_DESIGN_PATH or self.scenario.source != R14_SCENARIO_PATH or self.ci.source != R14_CI_PATH:
            raise ValueError("R14 integrated report evidence source mismatch")
        if self.manual_state != "conditional_not_triggered":
            raise ValueError("R14 core acceptance cannot silently satisfy a live-provider manual gate")
        if any((self.provider_live_claim, self.secrets_exposed, self.pii_exposed, self.production_publish_claim)):
            raise ValueError("R14 integrated report contains an unsupported live/sensitive claim")
        if self.status != "pass" or self.blockers:
            raise ValueError("accepted R14 integrated report must be blocker-free pass")
        _require_sha256(self.evidence_sha256, field="integrated evidence_sha256")
        if self.evidence_sha256 != canonical_sha256(self.payload_without_digest()):
            raise ValueError("R14 integrated report digest mismatch")

    def payload_without_digest(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "source_sha": self.source_sha,
            "prior_phase": self.prior_phase.to_dict(),
            "subdivision_acceptance": [item.to_dict() for item in self.subdivision_acceptance],
            "design": self.design.to_dict(),
            "scenario": self.scenario.to_dict(),
            "ci": self.ci.to_dict(),
            "manual_state": self.manual_state,
            "provider_live_claim": self.provider_live_claim,
            "secrets_exposed": self.secrets_exposed,
            "pii_exposed": self.pii_exposed,
            "production_publish_claim": self.production_publish_claim,
            "status": self.status,
            "blockers": list(self.blockers),
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.payload_without_digest(), "evidence_sha256": self.evidence_sha256}

    @classmethod
    def from_dict(cls, raw: object) -> "IntegratedReport":
        required = {
            "schema_version", "generated_at", "source_sha", "prior_phase", "subdivision_acceptance",
            "design", "scenario", "ci", "manual_state", "provider_live_claim", "secrets_exposed",
            "pii_exposed", "production_publish_claim", "status", "blockers", "evidence_sha256",
        }
        if not isinstance(raw, dict) or set(raw) != required:
            raise ValueError("R14 integrated report has invalid keys")
        subdivisions = raw["subdivision_acceptance"]
        blockers = raw["blockers"]
        if not isinstance(subdivisions, list) or not isinstance(blockers, list):
            raise ValueError("R14 integrated report arrays are invalid")
        bool_fields = ("provider_live_claim", "secrets_exposed", "pii_exposed", "production_publish_claim")
        if any(not isinstance(raw[name], bool) for name in bool_fields):
            raise ValueError("R14 integrated report claim fields must be booleans")
        return cls(
            schema_version=int(raw["schema_version"]),
            generated_at=str(raw["generated_at"]),
            source_sha=str(raw["source_sha"]),
            prior_phase=EvidenceBinding.from_dict(raw["prior_phase"]),
            subdivision_acceptance=tuple(EvidenceBinding.from_dict(item) for item in subdivisions),
            design=EvidenceBinding.from_dict(raw["design"]),
            scenario=EvidenceBinding.from_dict(raw["scenario"]),
            ci=EvidenceBinding.from_dict(raw["ci"]),
            manual_state=str(raw["manual_state"]),
            provider_live_claim=raw["provider_live_claim"],
            secrets_exposed=raw["secrets_exposed"],
            pii_exposed=raw["pii_exposed"],
            production_publish_claim=raw["production_publish_claim"],
            status=str(raw["status"]),
            blockers=tuple(str(item) for item in blockers),
            evidence_sha256=str(raw["evidence_sha256"]),
        )


def _binding(source: str, read_bytes: Callable[[str], bytes]) -> EvidenceBinding:
    raw = read_bytes(source)
    if not raw:
        raise ValueError(f"required evidence is empty: {source}")
    return EvidenceBinding(source, hashlib.sha256(raw).hexdigest(), len(raw))


def build_ci_evidence(
    *,
    source_sha: str,
    generated_at: str,
    runs: Iterable[WorkflowRunBinding],
    artifacts: Iterable[WorkflowArtifactBinding],
) -> IntegratedCIEvidence:
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "source_sha": _require_commit(source_sha, field="source_sha"),
        "runs": [item.to_dict() for item in runs],
        "artifacts": [item.to_dict() for item in artifacts],
        "manual_state": "conditional_not_triggered",
        "provider_live_claim": False,
        "secrets_exposed": False,
        "status": "pass",
        "blockers": [],
    }
    return IntegratedCIEvidence.from_dict({**payload, "evidence_sha256": canonical_sha256(payload)})


def build_repository_report(
    *,
    source_sha: str,
    generated_at: str,
    read_bytes: Callable[[str], bytes],
) -> IntegratedReport:
    _require_commit(source_sha, field="source_sha")
    prior_raw = json.loads(read_bytes(R13_INTEGRATED_PATH))
    if prior_raw.get("evidence_sha256") != R13_ACCEPTED_DIGEST:
        raise ValueError("accepted R13 integrated semantic digest drift")

    scenario_raw = json.loads(read_bytes(R14_SCENARIO_PATH))
    ci_raw = json.loads(read_bytes(R14_CI_PATH))
    ci = IntegratedCIEvidence.from_dict(ci_raw)
    if scenario_raw.get("source_sha") != source_sha or ci.source_sha != source_sha:
        raise ValueError("R14 integrated evidence mixes source SHAs")
    if scenario_raw.get("status") != "pass" or scenario_raw.get("blockers") != []:
        raise ValueError("R14 integrated scenario is not a blocker-free pass")
    if scenario_raw.get("manual_state") != "conditional_not_triggered":
        raise ValueError("R14 integrated scenario manual state is not accepted")
    for name in ("provider_live_claim", "secrets_exposed", "pii_exposed", "production_publish_claim"):
        if scenario_raw.get(name) is not False:
            raise ValueError(f"R14 integrated scenario overclaim: {name}")

    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "source_sha": source_sha,
        "prior_phase": _binding(R13_INTEGRATED_PATH, read_bytes).to_dict(),
        "subdivision_acceptance": [_binding(path, read_bytes).to_dict() for path in R14_SUBDIVISION_PATHS],
        "design": _binding(R14_DESIGN_PATH, read_bytes).to_dict(),
        "scenario": _binding(R14_SCENARIO_PATH, read_bytes).to_dict(),
        "ci": _binding(R14_CI_PATH, read_bytes).to_dict(),
        "manual_state": "conditional_not_triggered",
        "provider_live_claim": False,
        "secrets_exposed": False,
        "pii_exposed": False,
        "production_publish_claim": False,
        "status": "pass",
        "blockers": [],
    }
    return IntegratedReport.from_dict({**payload, "evidence_sha256": canonical_sha256(payload)})


def validate_repository_evidence(report: IntegratedReport, read_bytes: Callable[[str], bytes]) -> None:
    for binding in (
        report.prior_phase,
        *report.subdivision_acceptance,
        report.design,
        report.scenario,
        report.ci,
    ):
        raw = read_bytes(binding.source)
        if len(raw) != binding.bytes or hashlib.sha256(raw).hexdigest() != binding.sha256:
            raise ValueError(f"bound evidence drift: {binding.source}")
    ci = IntegratedCIEvidence.from_dict(json.loads(read_bytes(R14_CI_PATH)))
    scenario = json.loads(read_bytes(R14_SCENARIO_PATH))
    if ci.source_sha != report.source_sha or scenario.get("source_sha") != report.source_sha:
        raise ValueError("repository evidence source mismatch")
    if report.evidence_sha256 != canonical_sha256(report.payload_without_digest()):
        raise ValueError("integrated report semantic digest mismatch")


__all__ = [
    "R13_ACCEPTED_DIGEST",
    "R13_INTEGRATED_PATH",
    "R14_CI_PATH",
    "R14_DESIGN_PATH",
    "R14_INTEGRATED_REPORT_PATH",
    "R14_SCENARIO_PATH",
    "REQUIRED_ARTIFACT_KINDS",
    "REQUIRED_RUNS",
    "EvidenceBinding",
    "IntegratedCIEvidence",
    "IntegratedReport",
    "WorkflowArtifactBinding",
    "WorkflowRunBinding",
    "build_ci_evidence",
    "build_repository_report",
    "canonical_json_bytes",
    "canonical_sha256",
    "validate_repository_evidence",
]
