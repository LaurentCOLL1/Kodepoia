from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import PurePosixPath

from kodepoia.tuning.integrated_acceptance import (
    canonical_sha256,
    validate_integrated_evidence,
)

R14_INTEGRATED_PATH = "docs/roadmap/R14_INTEGRATED_ACCEPTANCE.json"
R14_ACCEPTED_DIGEST = "06dbdc830b20fd4b2966b11cbacfd4b010f93101b071d827766c8b9cbfd45189"
R15_PLAN_PATH = "docs/roadmap/R15_PLAN.md"
R15_CI_PATH = "docs/roadmap/R15_17_CI_ACCEPTANCE.json"
R15_SCENARIO_PATH = "docs/roadmap/R15_17_SCENARIO_EVIDENCE.json"
R15_DESIGN_PATH = "docs/roadmap/R15_17_DESIGN.md"
R15_INTEGRATED_REPORT_PATH = "docs/roadmap/R15_INTEGRATED_ACCEPTANCE.json"
R15_SUBDIVISION_PATHS = (
    "docs/roadmap/R15_1_ACCEPTANCE.md",
    "docs/roadmap/R15_2_ACCEPTANCE.md",
    "docs/roadmap/R15_3_ACCEPTANCE.md",
    "docs/roadmap/R15_4_ACCEPTANCE.md",
    "docs/roadmap/R15_5_ACCEPTANCE.md",
    "docs/roadmap/R15_6_ACCEPTANCE.md",
    "docs/roadmap/R15_7_ACCEPTANCE.md",
    "docs/roadmap/R15_8_ACCEPTANCE.md",
    "docs/roadmap/R15_13_ACCEPTANCE.md",
    "docs/roadmap/R15_14_ACCEPTANCE.md",
    "docs/roadmap/R15_15_ACCEPTANCE.md",
    "docs/roadmap/R15_16_ACCEPTANCE.md",
)

REQUIRED_RUNS = (
    "R0 Repository Guard",
    "Python Core",
    "KodeStudio UI Smoke",
    "R15 Integrated Acceptance",
)
REQUIRED_ARTIFACT_KINDS = ("integrated_scenario",)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")


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


def _validate_phase_plan(raw: bytes) -> None:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("R15 phase plan must be UTF-8") from exc
    for index in range(1, 17):
        if f"# R15.{index} —" not in text:
            raise ValueError(f"R15 phase plan is missing subdivision heading R15.{index}")
    for index in range(9, 13):
        start_marker = f"# R15.{index} —"
        next_marker = f"# R15.{index + 1} —"
        start = text.index(start_marker)
        end = text.find(next_marker, start + len(start_marker))
        section = text[start:] if end < 0 else text[start:end]
        if "## Completion record" not in section or "COMPLETE" not in section:
            raise ValueError(
                f"R15 phase plan lacks accepted completion authority for R15.{index}"
            )


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
    def from_dict(cls, raw: object) -> EvidenceBinding:
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
            raise ValueError(f"unexpected R15.17 workflow run: {self.name}")
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
    def from_dict(cls, raw: object) -> WorkflowRunBinding:
        required = {"name", "run_id", "run_number", "conclusion"}
        if not isinstance(raw, dict) or set(raw) != required:
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
            raise ValueError("unexpected R15.17 artifact kind")
        if self.run_name != "R15 Integrated Acceptance":
            raise ValueError("integrated scenario artifact must come from R15 Integrated Acceptance")
        if (
            not isinstance(self.artifact_id, int)
            or isinstance(self.artifact_id, bool)
            or self.artifact_id <= 0
        ):
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
    def from_dict(cls, raw: object) -> WorkflowArtifactBinding:
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
    optional_capability_state: str
    secrets_exposed: bool
    status: str
    blockers: tuple[str, ...]
    evidence_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported R15.17 CI evidence schema")
        if not isinstance(self.generated_at, str) or not self.generated_at.strip():
            raise ValueError("generated_at is required")
        _require_commit(self.source_sha, field="source_sha")
        if tuple(item.name for item in self.runs) != REQUIRED_RUNS:
            raise ValueError("R15.17 CI evidence requires the exact ordered workflow set")
        if len({item.run_id for item in self.runs}) != len(self.runs):
            raise ValueError("workflow run ids must be unique")
        if tuple(item.kind for item in self.artifacts) != REQUIRED_ARTIFACT_KINDS:
            raise ValueError("R15.17 CI evidence requires the integrated scenario artifact")
        artifact = self.artifacts[0]
        expected_name = f"R15_17_INTEGRATED_SCENARIO-{self.source_sha}"
        if artifact.name != expected_name:
            raise ValueError("integrated scenario artifact name/source SHA mismatch")
        if self.manual_state != "conditional_not_triggered":
            raise ValueError("core R15.17 closes only while conditional manual work is not triggered")
        if self.optional_capability_state != "unavailable":
            raise ValueError("R15.17 fixture capability state must remain truthful unavailable")
        if self.secrets_exposed is not False:
            raise ValueError("R15.17 CI evidence cannot expose secrets")
        if self.status != "pass" or self.blockers:
            raise ValueError("accepted R15.17 CI evidence must be blocker-free pass")
        _require_sha256(self.evidence_sha256, field="CI evidence_sha256")
        if self.evidence_sha256 != canonical_sha256(self.payload_without_digest()):
            raise ValueError("R15.17 CI evidence digest mismatch")

    def payload_without_digest(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "source_sha": self.source_sha,
            "runs": [item.to_dict() for item in self.runs],
            "artifacts": [item.to_dict() for item in self.artifacts],
            "manual_state": self.manual_state,
            "optional_capability_state": self.optional_capability_state,
            "secrets_exposed": self.secrets_exposed,
            "status": self.status,
            "blockers": list(self.blockers),
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.payload_without_digest(), "evidence_sha256": self.evidence_sha256}

    @classmethod
    def from_dict(cls, raw: object) -> IntegratedCIEvidence:
        required = {
            "schema_version",
            "generated_at",
            "source_sha",
            "runs",
            "artifacts",
            "manual_state",
            "optional_capability_state",
            "secrets_exposed",
            "status",
            "blockers",
            "evidence_sha256",
        }
        if not isinstance(raw, dict) or set(raw) != required:
            raise ValueError("R15.17 CI evidence has invalid keys")
        runs_raw = raw["runs"]
        artifacts_raw = raw["artifacts"]
        blockers_raw = raw["blockers"]
        if (
            not isinstance(runs_raw, list)
            or not isinstance(artifacts_raw, list)
            or not isinstance(blockers_raw, list)
        ):
            raise ValueError("R15.17 CI evidence arrays are invalid")
        if not isinstance(raw["secrets_exposed"], bool):
            raise ValueError("R15.17 CI secrets_exposed must be boolean")
        return cls(
            schema_version=int(raw["schema_version"]),
            generated_at=str(raw["generated_at"]),
            source_sha=str(raw["source_sha"]),
            runs=tuple(WorkflowRunBinding.from_dict(item) for item in runs_raw),
            artifacts=tuple(WorkflowArtifactBinding.from_dict(item) for item in artifacts_raw),
            manual_state=str(raw["manual_state"]),
            optional_capability_state=str(raw["optional_capability_state"]),
            secrets_exposed=raw["secrets_exposed"],
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
    phase_plan: EvidenceBinding
    subdivision_acceptance: tuple[EvidenceBinding, ...]
    design: EvidenceBinding
    scenario: EvidenceBinding
    ci: EvidenceBinding
    manual_state: str
    optional_capability_state: str
    secrets_exposed: bool
    status: str
    blockers: tuple[str, ...]
    evidence_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported R15 integrated report schema")
        if not isinstance(self.generated_at, str) or not self.generated_at.strip():
            raise ValueError("generated_at is required")
        _require_commit(self.source_sha, field="source_sha")
        if self.prior_phase.source != R14_INTEGRATED_PATH:
            raise ValueError("R15 must bind the accepted R14 integrated report")
        if self.phase_plan.source != R15_PLAN_PATH:
            raise ValueError("R15 integrated report must bind the phase plan")
        if len(self.subdivision_acceptance) != len(R15_SUBDIVISION_PATHS):
            raise ValueError("R15 report must bind every standalone subdivision acceptance")
        if tuple(item.source for item in self.subdivision_acceptance) != R15_SUBDIVISION_PATHS:
            raise ValueError("R15 subdivision acceptance binding order/path mismatch")
        expected = (R15_DESIGN_PATH, R15_SCENARIO_PATH, R15_CI_PATH)
        actual = (self.design.source, self.scenario.source, self.ci.source)
        if actual != expected:
            raise ValueError("R15 integrated report evidence source mismatch")
        if self.manual_state != "conditional_not_triggered":
            raise ValueError("R15 core acceptance cannot silently satisfy a manual gate")
        if self.optional_capability_state != "unavailable":
            raise ValueError("R15 integrated report must preserve truthful unavailable fixture state")
        if self.secrets_exposed is not False:
            raise ValueError("R15 integrated report cannot expose secrets")
        if self.status != "pass" or self.blockers:
            raise ValueError("accepted R15 integrated report must be blocker-free pass")
        _require_sha256(self.evidence_sha256, field="integrated evidence_sha256")
        if self.evidence_sha256 != canonical_sha256(self.payload_without_digest()):
            raise ValueError("R15 integrated report digest mismatch")

    def payload_without_digest(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "source_sha": self.source_sha,
            "prior_phase": self.prior_phase.to_dict(),
            "phase_plan": self.phase_plan.to_dict(),
            "subdivision_acceptance": [item.to_dict() for item in self.subdivision_acceptance],
            "design": self.design.to_dict(),
            "scenario": self.scenario.to_dict(),
            "ci": self.ci.to_dict(),
            "manual_state": self.manual_state,
            "optional_capability_state": self.optional_capability_state,
            "secrets_exposed": self.secrets_exposed,
            "status": self.status,
            "blockers": list(self.blockers),
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.payload_without_digest(), "evidence_sha256": self.evidence_sha256}

    @classmethod
    def from_dict(cls, raw: object) -> IntegratedReport:
        required = {
            "schema_version",
            "generated_at",
            "source_sha",
            "prior_phase",
            "phase_plan",
            "subdivision_acceptance",
            "design",
            "scenario",
            "ci",
            "manual_state",
            "optional_capability_state",
            "secrets_exposed",
            "status",
            "blockers",
            "evidence_sha256",
        }
        if not isinstance(raw, dict) or set(raw) != required:
            raise ValueError("R15 integrated report has invalid keys")
        subdivisions = raw["subdivision_acceptance"]
        blockers = raw["blockers"]
        if not isinstance(subdivisions, list) or not isinstance(blockers, list):
            raise ValueError("R15 integrated report arrays are invalid")
        if not isinstance(raw["secrets_exposed"], bool):
            raise ValueError("R15 integrated report secrets_exposed must be boolean")
        return cls(
            schema_version=int(raw["schema_version"]),
            generated_at=str(raw["generated_at"]),
            source_sha=str(raw["source_sha"]),
            prior_phase=EvidenceBinding.from_dict(raw["prior_phase"]),
            phase_plan=EvidenceBinding.from_dict(raw["phase_plan"]),
            subdivision_acceptance=tuple(EvidenceBinding.from_dict(item) for item in subdivisions),
            design=EvidenceBinding.from_dict(raw["design"]),
            scenario=EvidenceBinding.from_dict(raw["scenario"]),
            ci=EvidenceBinding.from_dict(raw["ci"]),
            manual_state=str(raw["manual_state"]),
            optional_capability_state=str(raw["optional_capability_state"]),
            secrets_exposed=raw["secrets_exposed"],
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
        "optional_capability_state": "unavailable",
        "secrets_exposed": False,
        "status": "pass",
        "blockers": [],
    }
    return IntegratedCIEvidence.from_dict(
        {**payload, "evidence_sha256": canonical_sha256(payload)}
    )


def build_repository_report(
    *,
    source_sha: str,
    generated_at: str,
    read_bytes: Callable[[str], bytes],
) -> IntegratedReport:
    _require_commit(source_sha, field="source_sha")
    prior_raw = json.loads(read_bytes(R14_INTEGRATED_PATH))
    if prior_raw.get("evidence_sha256") != R14_ACCEPTED_DIGEST:
        raise ValueError("accepted R14 integrated semantic digest drift")

    plan_raw = read_bytes(R15_PLAN_PATH)
    _validate_phase_plan(plan_raw)
    scenario_raw = json.loads(read_bytes(R15_SCENARIO_PATH))
    validate_integrated_evidence(scenario_raw)
    ci = IntegratedCIEvidence.from_dict(json.loads(read_bytes(R15_CI_PATH)))
    if scenario_raw.get("source_sha") != source_sha or ci.source_sha != source_sha:
        raise ValueError("R15 integrated evidence mixes source SHAs")

    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "source_sha": source_sha,
        "prior_phase": _binding(R14_INTEGRATED_PATH, read_bytes).to_dict(),
        "phase_plan": _binding(R15_PLAN_PATH, read_bytes).to_dict(),
        "subdivision_acceptance": [
            _binding(path, read_bytes).to_dict() for path in R15_SUBDIVISION_PATHS
        ],
        "design": _binding(R15_DESIGN_PATH, read_bytes).to_dict(),
        "scenario": _binding(R15_SCENARIO_PATH, read_bytes).to_dict(),
        "ci": _binding(R15_CI_PATH, read_bytes).to_dict(),
        "manual_state": "conditional_not_triggered",
        "optional_capability_state": "unavailable",
        "secrets_exposed": False,
        "status": "pass",
        "blockers": [],
    }
    return IntegratedReport.from_dict(
        {**payload, "evidence_sha256": canonical_sha256(payload)}
    )


def validate_repository_evidence(
    report: IntegratedReport,
    read_bytes: Callable[[str], bytes],
) -> None:
    for binding in (
        report.prior_phase,
        report.phase_plan,
        *report.subdivision_acceptance,
        report.design,
        report.scenario,
        report.ci,
    ):
        raw = read_bytes(binding.source)
        if len(raw) != binding.bytes or hashlib.sha256(raw).hexdigest() != binding.sha256:
            raise ValueError(f"bound evidence drift: {binding.source}")
    prior = json.loads(read_bytes(R14_INTEGRATED_PATH))
    if prior.get("evidence_sha256") != R14_ACCEPTED_DIGEST:
        raise ValueError("accepted R14 integrated semantic digest drift")
    _validate_phase_plan(read_bytes(R15_PLAN_PATH))
    ci = IntegratedCIEvidence.from_dict(json.loads(read_bytes(R15_CI_PATH)))
    scenario = json.loads(read_bytes(R15_SCENARIO_PATH))
    validate_integrated_evidence(scenario)
    if ci.source_sha != report.source_sha or scenario.get("source_sha") != report.source_sha:
        raise ValueError("repository evidence source mismatch")
    if report.evidence_sha256 != canonical_sha256(report.payload_without_digest()):
        raise ValueError("integrated report semantic digest mismatch")


__all__ = [
    "R14_ACCEPTED_DIGEST",
    "R14_INTEGRATED_PATH",
    "R15_CI_PATH",
    "R15_DESIGN_PATH",
    "R15_INTEGRATED_REPORT_PATH",
    "R15_PLAN_PATH",
    "R15_SCENARIO_PATH",
    "R15_SUBDIVISION_PATHS",
    "REQUIRED_ARTIFACT_KINDS",
    "REQUIRED_RUNS",
    "EvidenceBinding",
    "IntegratedCIEvidence",
    "IntegratedReport",
    "WorkflowArtifactBinding",
    "WorkflowRunBinding",
    "build_ci_evidence",
    "build_repository_report",
    "validate_repository_evidence",
]
