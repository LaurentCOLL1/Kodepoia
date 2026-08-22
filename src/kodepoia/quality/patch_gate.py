from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

from kodepoia.core.audit import AuditLog
from kodepoia.core.backup import BackupManager
from kodepoia.core.recovery import RecoveryJournal
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.kodecode.workspace import WorkspaceBoundary
from kodepoia.quality.build import redact_sensitive
from kodepoia.quality.health import HealthDimension, HealthMetric, HealthStatus
from kodepoia.quality.tests import TestCaseResult, TestCaseStatus


_SCHEMA_VERSION = 1
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{1,191}$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:/")
_FIXTURE_MARKER = ".kodepoia-r6-rollback-fixture"


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_payload(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _timestamp(value: str, *, field_name: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone")
    return value


def _git_sha(value: str, *, field_name: str) -> str:
    normalized = value.strip().lower()
    if not _SHA_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a 40-character git SHA")
    return normalized


def _sha256(value: str, *, field_name: str) -> str:
    normalized = value.strip().lower()
    if not _SHA256_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return normalized


def _stable_id(value: str, *, field_name: str) -> str:
    normalized = value.strip().lower()
    if not _ID_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a stable lowercase identifier")
    return normalized


def _safe_relative_path(value: str) -> str:
    raw = value.strip().replace("\\", "/")
    path = PurePosixPath(raw)
    if (
        not raw
        or raw in {".", ".."}
        or path.is_absolute()
        or ".." in path.parts
        or _WINDOWS_DRIVE_RE.match(raw)
    ):
        raise ValueError("patch path must be a safe non-empty project-relative path")
    return path.as_posix()


class PatchDomain(StrEnum):
    CORE = "core"
    GOVERNANCE = "governance"
    SECURITY = "security"
    SCHEMA = "schema"
    PUBLIC_API = "public_api"
    BUILD = "build"
    DEPENDENCIES = "dependencies"
    UI = "ui"
    VISUAL = "visual"
    ACCESSIBILITY = "accessibility"
    LOCALIZATION = "localization"
    PRIVACY = "privacy"
    LICENSES = "licenses"
    PERFORMANCE = "performance"
    ASSETS = "assets"
    TESTS = "tests"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class PatchOperation(StrEnum):
    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"


class PatchRisk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PatchClassification(StrEnum):
    MINOR = "minor"
    MAJOR = "major"


class ValidationGate(StrEnum):
    TESTS = "tests"
    REGRESSION = "regression"
    VISUAL = "visual"
    ACCESSIBILITY = "accessibility"
    LOCALIZATION = "localization"
    TECHNICAL_DEBT = "technical_debt"
    CI_BUILD = "ci_build"
    SECURITY = "security"
    PRIVACY = "privacy"
    LICENSE_BOM = "license_bom"
    HEALTH = "health"
    BUDGET = "budget"
    ROLLBACK = "rollback"


class GateEvidenceStatus(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"
    CANCELLED = "cancelled"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"


class RollbackMethod(StrEnum):
    SAFE_CHANGE = "safe_change"
    BACKUP_RESTORE = "backup_restore"
    RECOVERY_JOURNAL = "recovery_journal"
    COMPOSITE = "composite"


class RehearsalStatus(StrEnum):
    NOT_RUN = "not_run"
    PASS = "pass"
    FAIL = "fail"


class PatchGateStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class IntegrationEvidenceStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class PatchChange:
    path: str
    domain: PatchDomain
    operation: PatchOperation
    risk: PatchRisk = PatchRisk.LOW
    platforms: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _safe_relative_path(self.path))
        platforms = tuple(sorted({item.strip().lower() for item in self.platforms if item.strip()}))
        object.__setattr__(self, "platforms", platforms)

    @property
    def destructive(self) -> bool:
        return self.operation in {PatchOperation.DELETE, PatchOperation.RENAME}

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "domain": self.domain.value,
            "operation": self.operation.value,
            "risk": self.risk.value,
            "platforms": list(self.platforms),
            "destructive": self.destructive,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PatchChange":
        change = cls(
            path=str(payload["path"]),
            domain=PatchDomain(str(payload["domain"])),
            operation=PatchOperation(str(payload["operation"])),
            risk=PatchRisk(str(payload.get("risk", "low"))),
            platforms=tuple(str(item) for item in payload.get("platforms", [])),
        )
        if bool(payload.get("destructive", False)) is not change.destructive:
            raise ValueError("serialized destructive flag does not match operation")
        return change


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    classification: PatchClassification
    triggers: tuple[str, ...]

    def __post_init__(self) -> None:
        triggers = tuple(sorted(set(item.strip() for item in self.triggers if item.strip())))
        if self.classification is PatchClassification.MAJOR and not triggers:
            raise ValueError("major classification requires at least one deterministic trigger")
        if self.classification is PatchClassification.MINOR and triggers:
            raise ValueError("minor classification cannot carry major triggers")
        object.__setattr__(self, "triggers", triggers)

    def to_dict(self) -> dict[str, Any]:
        return {"classification": self.classification.value, "triggers": list(self.triggers)}


@dataclass(frozen=True, slots=True)
class GateRequirement:
    gate: ValidationGate
    reason: str

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("gate requirement requires reason")

    def to_dict(self) -> dict[str, str]:
        return {"gate": self.gate.value, "reason": self.reason}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GateRequirement":
        return cls(ValidationGate(str(payload["gate"])), str(payload["reason"]))


@dataclass(frozen=True, slots=True)
class GateEvidence:
    gate: ValidationGate
    status: GateEvidenceStatus
    source: str
    evidence_sha256: str = ""
    source_sha: str = ""
    rationale: str = ""
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("gate evidence requires source")
        measured = self.status in {
            GateEvidenceStatus.PASS,
            GateEvidenceStatus.WARN,
            GateEvidenceStatus.FAIL,
        }
        if measured and not self.evidence_sha256:
            raise ValueError("measured gate evidence requires evidence_sha256")
        if measured and not self.source_sha:
            raise ValueError("measured gate evidence requires source_sha")
        if self.evidence_sha256:
            object.__setattr__(self, "evidence_sha256", _sha256(self.evidence_sha256, field_name="evidence_sha256"))
        if self.source_sha:
            object.__setattr__(self, "source_sha", _git_sha(self.source_sha, field_name="source_sha"))
        if self.status is GateEvidenceStatus.NOT_APPLICABLE and not self.rationale.strip():
            raise ValueError("not-applicable gate evidence requires rationale")
        object.__setattr__(self, "details", dict(redact_sensitive(self.details)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate.value,
            "status": self.status.value,
            "source": self.source,
            "evidence_sha256": self.evidence_sha256,
            "source_sha": self.source_sha,
            "rationale": self.rationale,
            "details": redact_sensitive(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GateEvidence":
        return cls(
            gate=ValidationGate(str(payload["gate"])),
            status=GateEvidenceStatus(str(payload["status"])),
            source=str(payload["source"]),
            evidence_sha256=str(payload.get("evidence_sha256", "")),
            source_sha=str(payload.get("source_sha", "")),
            rationale=str(payload.get("rationale", "")),
            details=dict(payload.get("details") or {}),
        )


@dataclass(frozen=True, slots=True)
class RollbackStrategy:
    id: str
    method: RollbackMethod
    description: str
    restore_scope: tuple[str, ...]
    snapshot_required: bool = True
    audit_required: bool = True
    verification_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _stable_id(self.id, field_name="rollback strategy id"))
        if not self.description.strip():
            raise ValueError("rollback strategy requires description")
        scope = tuple(sorted({_safe_relative_path(item) for item in self.restore_scope}))
        if not scope:
            raise ValueError("rollback strategy requires non-empty restore scope")
        object.__setattr__(self, "restore_scope", scope)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "method": self.method.value,
            "description": self.description,
            "restore_scope": list(self.restore_scope),
            "snapshot_required": self.snapshot_required,
            "audit_required": self.audit_required,
            "verification_required": self.verification_required,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RollbackStrategy":
        return cls(
            id=str(payload["id"]),
            method=RollbackMethod(str(payload["method"])),
            description=str(payload["description"]),
            restore_scope=tuple(str(item) for item in payload.get("restore_scope", [])),
            snapshot_required=bool(payload.get("snapshot_required", True)),
            audit_required=bool(payload.get("audit_required", True)),
            verification_required=bool(payload.get("verification_required", True)),
        )


@dataclass(frozen=True, slots=True)
class RollbackRehearsalEvidence:
    status: RehearsalStatus
    source: str
    evidence_sha256: str
    restored_hashes_match: bool = False
    backup_verified: bool = False
    audit_chain_valid: bool = False
    recovery_checkpoint_cleared: bool = False
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("rollback rehearsal requires source")
        object.__setattr__(self, "evidence_sha256", _sha256(self.evidence_sha256, field_name="evidence_sha256"))
        if self.status is RehearsalStatus.PASS and not all(
            (self.restored_hashes_match, self.backup_verified, self.audit_chain_valid, self.recovery_checkpoint_cleared)
        ):
            raise ValueError("passing rehearsal requires all verification evidence")
        object.__setattr__(self, "details", dict(redact_sensitive(self.details)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "source": self.source,
            "evidence_sha256": self.evidence_sha256,
            "restored_hashes_match": self.restored_hashes_match,
            "backup_verified": self.backup_verified,
            "audit_chain_valid": self.audit_chain_valid,
            "recovery_checkpoint_cleared": self.recovery_checkpoint_cleared,
            "details": redact_sensitive(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RollbackRehearsalEvidence":
        return cls(
            status=RehearsalStatus(str(payload["status"])),
            source=str(payload["source"]),
            evidence_sha256=str(payload["evidence_sha256"]),
            restored_hashes_match=bool(payload.get("restored_hashes_match", False)),
            backup_verified=bool(payload.get("backup_verified", False)),
            audit_chain_valid=bool(payload.get("audit_chain_valid", False)),
            recovery_checkpoint_cleared=bool(payload.get("recovery_checkpoint_cleared", False)),
            details=dict(payload.get("details") or {}),
        )


_PROTECTED_MAJOR_DOMAINS = {
    PatchDomain.CORE,
    PatchDomain.GOVERNANCE,
    PatchDomain.SECURITY,
    PatchDomain.SCHEMA,
    PatchDomain.PUBLIC_API,
    PatchDomain.BUILD,
}

_DOMAIN_GATES: dict[PatchDomain, tuple[ValidationGate, ...]] = {
    PatchDomain.CORE: (ValidationGate.TESTS, ValidationGate.REGRESSION, ValidationGate.TECHNICAL_DEBT, ValidationGate.HEALTH),
    PatchDomain.GOVERNANCE: (ValidationGate.TESTS, ValidationGate.REGRESSION, ValidationGate.SECURITY, ValidationGate.HEALTH),
    PatchDomain.SECURITY: (ValidationGate.TESTS, ValidationGate.REGRESSION, ValidationGate.SECURITY, ValidationGate.HEALTH),
    PatchDomain.SCHEMA: (ValidationGate.TESTS, ValidationGate.REGRESSION, ValidationGate.CI_BUILD, ValidationGate.HEALTH),
    PatchDomain.PUBLIC_API: (ValidationGate.TESTS, ValidationGate.REGRESSION, ValidationGate.CI_BUILD, ValidationGate.HEALTH),
    PatchDomain.BUILD: (ValidationGate.TESTS, ValidationGate.CI_BUILD, ValidationGate.LICENSE_BOM, ValidationGate.HEALTH),
    PatchDomain.DEPENDENCIES: (ValidationGate.TESTS, ValidationGate.CI_BUILD, ValidationGate.SECURITY, ValidationGate.LICENSE_BOM, ValidationGate.HEALTH),
    PatchDomain.UI: (ValidationGate.TESTS, ValidationGate.REGRESSION, ValidationGate.VISUAL, ValidationGate.ACCESSIBILITY, ValidationGate.LOCALIZATION, ValidationGate.HEALTH),
    PatchDomain.VISUAL: (ValidationGate.TESTS, ValidationGate.REGRESSION, ValidationGate.VISUAL, ValidationGate.HEALTH),
    PatchDomain.ACCESSIBILITY: (ValidationGate.TESTS, ValidationGate.ACCESSIBILITY, ValidationGate.HEALTH),
    PatchDomain.LOCALIZATION: (ValidationGate.TESTS, ValidationGate.LOCALIZATION, ValidationGate.HEALTH),
    PatchDomain.PRIVACY: (ValidationGate.TESTS, ValidationGate.PRIVACY, ValidationGate.SECURITY, ValidationGate.HEALTH),
    PatchDomain.LICENSES: (ValidationGate.TESTS, ValidationGate.LICENSE_BOM, ValidationGate.HEALTH),
    PatchDomain.PERFORMANCE: (ValidationGate.TESTS, ValidationGate.REGRESSION, ValidationGate.BUDGET, ValidationGate.HEALTH),
    PatchDomain.ASSETS: (ValidationGate.TESTS, ValidationGate.REGRESSION, ValidationGate.VISUAL, ValidationGate.LICENSE_BOM, ValidationGate.HEALTH),
    PatchDomain.TESTS: (ValidationGate.TESTS, ValidationGate.REGRESSION, ValidationGate.HEALTH),
    PatchDomain.DOCUMENTATION: (ValidationGate.TESTS, ValidationGate.HEALTH),
    PatchDomain.OTHER: (ValidationGate.TESTS, ValidationGate.REGRESSION, ValidationGate.HEALTH),
}


class KodePatchGate:
    @staticmethod
    def classify(changes: Iterable[PatchChange]) -> ClassificationResult:
        values = tuple(changes)
        if not values:
            return ClassificationResult(PatchClassification.MINOR, ())
        triggers: set[str] = set()
        for change in values:
            if change.domain in _PROTECTED_MAJOR_DOMAINS:
                triggers.add(f"protected-domain:{change.domain.value}")
            if change.risk in {PatchRisk.HIGH, PatchRisk.CRITICAL}:
                triggers.add(f"risk:{change.risk.value}")
            if change.destructive and change.domain not in {PatchDomain.DOCUMENTATION, PatchDomain.TESTS}:
                triggers.add(f"destructive:{change.domain.value}")
        if len(values) >= 10:
            triggers.add("change-count>=10")
        if len({platform for change in values for platform in change.platforms}) >= 2:
            triggers.add("multi-platform-change")
        if triggers:
            return ClassificationResult(PatchClassification.MAJOR, tuple(triggers))
        return ClassificationResult(PatchClassification.MINOR, ())

    @staticmethod
    def required_gates(changes: Iterable[PatchChange], classification: ClassificationResult) -> tuple[GateRequirement, ...]:
        values = tuple(changes)
        reasons: dict[ValidationGate, set[str]] = {}
        for change in values:
            for gate in _DOMAIN_GATES[change.domain]:
                reasons.setdefault(gate, set()).add(f"domain:{change.domain.value}")
        if classification.classification is PatchClassification.MAJOR:
            reasons.setdefault(ValidationGate.ROLLBACK, set()).add("major-patch")
            reasons.setdefault(ValidationGate.TECHNICAL_DEBT, set()).add("major-patch")
            reasons.setdefault(ValidationGate.REGRESSION, set()).add("major-patch")
        return tuple(
            GateRequirement(gate, ",".join(sorted(values_)))
            for gate, values_ in sorted(reasons.items(), key=lambda item: item[0].value)
        )

    @staticmethod
    def status_for(
        *,
        classification: ClassificationResult,
        requirements: Iterable[GateRequirement],
        evidence: Iterable[GateEvidence],
        rollback: RollbackStrategy | None,
        rehearsal: RollbackRehearsalEvidence | None,
    ) -> PatchGateStatus:
        required = {item.gate for item in requirements}
        evidence_values = tuple(evidence)
        evidence_map = {item.gate: item for item in evidence_values}
        if len(evidence_map) != len(evidence_values):
            raise ValueError("gate evidence must be unique by gate")
        if not required and classification.classification is PatchClassification.MINOR:
            return PatchGateStatus.UNKNOWN
        blocking_statuses = {
            GateEvidenceStatus.FAIL,
            GateEvidenceStatus.SKIP,
            GateEvidenceStatus.CANCELLED,
            GateEvidenceStatus.MISSING,
            GateEvidenceStatus.NOT_APPLICABLE,
        }
        for gate in required:
            item = evidence_map.get(gate)
            if item is None or item.status in blocking_statuses:
                return PatchGateStatus.FAIL
        if classification.classification is PatchClassification.MAJOR:
            if rollback is None or rehearsal is None or rehearsal.status is not RehearsalStatus.PASS:
                return PatchGateStatus.FAIL
            if not (rollback.snapshot_required and rollback.audit_required and rollback.verification_required):
                return PatchGateStatus.FAIL
        if any(evidence_map[gate].status is GateEvidenceStatus.WARN for gate in required):
            return PatchGateStatus.WARN
        return PatchGateStatus.PASS

    @staticmethod
    def to_health_metric(report: "PatchGateReport") -> HealthMetric:
        report.validate()
        mapping = {
            PatchGateStatus.UNKNOWN: HealthStatus.UNKNOWN,
            PatchGateStatus.PASS: HealthStatus.PASS,
            PatchGateStatus.WARN: HealthStatus.WARN,
            PatchGateStatus.FAIL: HealthStatus.FAIL,
        }
        status = mapping[report.status]
        if status is HealthStatus.UNKNOWN:
            return HealthMetric(
                dimension=HealthDimension.TESTS,
                status=status,
                summary="Patch gate has no applicable validation evidence",
                source="KodePatchGate",
                details={"evidence_sha256": report.evidence_sha256},
            )
        score = {
            PatchGateStatus.PASS: 100.0,
            PatchGateStatus.WARN: 70.0,
            PatchGateStatus.FAIL: 0.0,
        }[report.status]
        return HealthMetric(
            dimension=HealthDimension.TESTS,
            status=status,
            score=score,
            summary=f"{report.classification.classification.value} patch gate: {report.status.value}",
            source="KodePatchGate",
            blocking=report.status is PatchGateStatus.FAIL,
            details={
                "base_sha": report.base_sha,
                "head_sha": report.head_sha,
                "blockers": list(report.blockers),
                "evidence_sha256": report.evidence_sha256,
            },
        )

    @staticmethod
    def to_test_cases(report: "PatchGateReport") -> tuple[TestCaseResult, ...]:
        report.validate()
        status_map = {
            GateEvidenceStatus.PASS: TestCaseStatus.PASS,
            GateEvidenceStatus.FAIL: TestCaseStatus.FAIL,
            GateEvidenceStatus.WARN: TestCaseStatus.SKIP,
            GateEvidenceStatus.SKIP: TestCaseStatus.SKIP,
            GateEvidenceStatus.CANCELLED: TestCaseStatus.FAIL,
            GateEvidenceStatus.MISSING: TestCaseStatus.FAIL,
            GateEvidenceStatus.NOT_APPLICABLE: TestCaseStatus.SKIP,
        }
        required = {item.gate for item in report.requirements}
        cases = []
        for item in report.evidence:
            cases.append(
                TestCaseResult(
                    id=f"patch-gate:{item.gate.value}",
                    status=status_map[item.status],
                    duration_s=0.0,
                    message=f"Patch gate evidence {item.gate.value}: {item.status.value}",
                    source="KodePatchGate",
                    details={"required": item.gate in required, "source_sha": item.source_sha},
                )
            )
        return tuple(cases)


@dataclass(frozen=True, slots=True)
class PatchGateReport:
    generated_at: str
    patch_id: str
    base_sha: str
    head_sha: str
    changes: tuple[PatchChange, ...]
    classification: ClassificationResult
    requirements: tuple[GateRequirement, ...]
    evidence: tuple[GateEvidence, ...]
    rollback: RollbackStrategy | None
    rehearsal: RollbackRehearsalEvidence | None
    status: PatchGateStatus
    evidence_sha256: str
    schema_version: int = _SCHEMA_VERSION

    @property
    def blockers(self) -> tuple[str, ...]:
        required = {item.gate for item in self.requirements}
        evidence_map = {item.gate: item for item in self.evidence}
        blockers: list[str] = []
        for gate in sorted(required, key=lambda item: item.value):
            item = evidence_map.get(gate)
            if item is None:
                blockers.append(f"gate:{gate.value}:missing")
            elif item.status is not GateEvidenceStatus.PASS:
                blockers.append(f"gate:{gate.value}:{item.status.value}")
        if self.classification.classification is PatchClassification.MAJOR:
            if self.rollback is None:
                blockers.append("rollback:strategy:missing")
            elif not (
                self.rollback.snapshot_required
                and self.rollback.audit_required
                and self.rollback.verification_required
            ):
                blockers.append("rollback:strategy:verification-incomplete")
            if self.rehearsal is None:
                blockers.append("rollback:rehearsal:missing")
            elif self.rehearsal.status is not RehearsalStatus.PASS:
                blockers.append(f"rollback:rehearsal:{self.rehearsal.status.value}")
        return tuple(blockers)

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "patch_id": self.patch_id,
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "changes": [item.to_dict() for item in self.changes],
            "classification": self.classification.to_dict(),
            "requirements": [item.to_dict() for item in self.requirements],
            "evidence": [item.to_dict() for item in self.evidence],
            "rollback": self.rollback.to_dict() if self.rollback else None,
            "rehearsal": self.rehearsal.to_dict() if self.rehearsal else None,
            "status": self.status.value,
            "blockers": list(self.blockers),
        }

    def validate(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported patch gate schema version")
        _timestamp(self.generated_at, field_name="generated_at")
        _stable_id(self.patch_id, field_name="patch_id")
        _git_sha(self.base_sha, field_name="base_sha")
        _git_sha(self.head_sha, field_name="head_sha")
        if self.base_sha == self.head_sha:
            raise ValueError("patch base_sha and head_sha must differ")
        paths = [item.path for item in self.changes]
        if len(paths) != len(set(paths)):
            raise ValueError("patch change paths must be unique")
        expected_classification = KodePatchGate.classify(self.changes)
        if self.classification != expected_classification:
            raise ValueError("patch classification does not match deterministic rules")
        expected_requirements = KodePatchGate.required_gates(self.changes, self.classification)
        if self.requirements != expected_requirements:
            raise ValueError("patch gate requirements do not match deterministic selection")
        gates = [item.gate for item in self.evidence]
        if len(gates) != len(set(gates)):
            raise ValueError("patch gate evidence must be unique")
        required = {item.gate for item in self.requirements}
        for item in self.evidence:
            if item.source_sha and item.source_sha != self.head_sha:
                raise ValueError("gate evidence source_sha does not match patch head_sha")
            if item.gate in required and item.status in {
                GateEvidenceStatus.PASS,
                GateEvidenceStatus.WARN,
                GateEvidenceStatus.FAIL,
            }:
                if not item.source_sha:
                    raise ValueError("required measured gate evidence requires source_sha")
                if not item.evidence_sha256:
                    raise ValueError("required measured gate evidence requires evidence_sha256")
        expected_status = KodePatchGate.status_for(
            classification=self.classification,
            requirements=self.requirements,
            evidence=self.evidence,
            rollback=self.rollback,
            rehearsal=self.rehearsal,
        )
        if self.status is not expected_status:
            raise ValueError("patch gate status does not match evidence")
        if self.evidence_sha256 != _sha256_payload(self._payload()):
            raise ValueError("patch gate evidence hash mismatch")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = self._payload()
        payload["evidence_sha256"] = self.evidence_sha256
        return payload

    @classmethod
    def build(
        cls,
        *,
        patch_id: str,
        base_sha: str,
        head_sha: str,
        changes: Iterable[PatchChange],
        evidence: Iterable[GateEvidence],
        rollback: RollbackStrategy | None = None,
        rehearsal: RollbackRehearsalEvidence | None = None,
        generated_at: str | None = None,
    ) -> "PatchGateReport":
        change_tuple = tuple(sorted(changes, key=lambda item: item.path))
        classification = KodePatchGate.classify(change_tuple)
        requirements = KodePatchGate.required_gates(change_tuple, classification)
        evidence_tuple = tuple(sorted(evidence, key=lambda item: item.gate.value))
        status = KodePatchGate.status_for(
            classification=classification,
            requirements=requirements,
            evidence=evidence_tuple,
            rollback=rollback,
            rehearsal=rehearsal,
        )
        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        provisional = cls(
            timestamp,
            _stable_id(patch_id, field_name="patch_id"),
            _git_sha(base_sha, field_name="base_sha"),
            _git_sha(head_sha, field_name="head_sha"),
            change_tuple,
            classification,
            requirements,
            evidence_tuple,
            rollback,
            rehearsal,
            status,
            "",
        )
        digest = _sha256_payload(provisional._payload())
        final = cls(
            provisional.generated_at,
            provisional.patch_id,
            provisional.base_sha,
            provisional.head_sha,
            provisional.changes,
            provisional.classification,
            provisional.requirements,
            provisional.evidence,
            provisional.rollback,
            provisional.rehearsal,
            provisional.status,
            digest,
        )
        final.validate()
        return final

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PatchGateReport":
        classification_payload = payload["classification"]
        report = cls(
            generated_at=str(payload["generated_at"]),
            patch_id=str(payload["patch_id"]),
            base_sha=str(payload["base_sha"]),
            head_sha=str(payload["head_sha"]),
            changes=tuple(PatchChange.from_dict(item) for item in payload.get("changes", [])),
            classification=ClassificationResult(
                PatchClassification(str(classification_payload["classification"])),
                tuple(str(item) for item in classification_payload.get("triggers", [])),
            ),
            requirements=tuple(GateRequirement.from_dict(item) for item in payload.get("requirements", [])),
            evidence=tuple(GateEvidence.from_dict(item) for item in payload.get("evidence", [])),
            rollback=(RollbackStrategy.from_dict(payload["rollback"]) if payload.get("rollback") else None),
            rehearsal=(RollbackRehearsalEvidence.from_dict(payload["rehearsal"]) if payload.get("rehearsal") else None),
            status=PatchGateStatus(str(payload["status"])),
            evidence_sha256=str(payload["evidence_sha256"]),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if tuple(payload.get("blockers") or ()) != report.blockers:
            raise ValueError("serialized patch blockers do not match evidence")
        report.validate()
        return report


@dataclass(frozen=True, slots=True)
class R6SubdivisionEvidence:
    subdivision: str
    status: IntegrationEvidenceStatus
    source: str
    evidence_sha256: str
    accepted_head: str = ""
    manual_satisfied: bool = True

    def __post_init__(self) -> None:
        if self.subdivision not in {f"R6.{index}" for index in range(1, 13)}:
            raise ValueError("invalid R6 subdivision identifier")
        if not self.source.strip():
            raise ValueError("R6 subdivision evidence requires source")
        object.__setattr__(self, "evidence_sha256", _sha256(self.evidence_sha256, field_name="evidence_sha256"))
        if self.status is IntegrationEvidenceStatus.PASS and not self.accepted_head:
            raise ValueError("PASS R6 subdivision evidence requires accepted_head")
        if self.accepted_head:
            object.__setattr__(self, "accepted_head", _git_sha(self.accepted_head, field_name="accepted_head"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "subdivision": self.subdivision,
            "status": self.status.value,
            "source": self.source,
            "evidence_sha256": self.evidence_sha256,
            "accepted_head": self.accepted_head,
            "manual_satisfied": self.manual_satisfied,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "R6SubdivisionEvidence":
        return cls(
            subdivision=str(payload["subdivision"]),
            status=IntegrationEvidenceStatus(str(payload["status"])),
            source=str(payload["source"]),
            evidence_sha256=str(payload["evidence_sha256"]),
            accepted_head=str(payload.get("accepted_head", "")),
            manual_satisfied=bool(payload.get("manual_satisfied", True)),
        )


@dataclass(frozen=True, slots=True)
class R6IntegrationReport:
    generated_at: str
    source_sha: str
    subdivisions: tuple[R6SubdivisionEvidence, ...]
    status: IntegrationEvidenceStatus
    evidence_sha256: str
    schema_version: int = _SCHEMA_VERSION

    @property
    def blockers(self) -> tuple[str, ...]:
        evidence = {item.subdivision: item for item in self.subdivisions}
        blockers: list[str] = []
        for index in range(1, 13):
            key = f"R6.{index}"
            item = evidence.get(key)
            if item is None:
                blockers.append(f"{key}:missing")
            elif item.status is not IntegrationEvidenceStatus.PASS:
                blockers.append(f"{key}:{item.status.value}")
            elif not item.manual_satisfied:
                blockers.append(f"{key}:manual-pending")
            elif key == "R6.12" and item.accepted_head != self.source_sha:
                blockers.append("R6.12:source-sha-mismatch")
        return tuple(blockers)

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "source_sha": self.source_sha,
            "subdivisions": [item.to_dict() for item in self.subdivisions],
            "status": self.status.value,
            "blockers": list(self.blockers),
        }

    def validate(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported R6 integration schema version")
        _timestamp(self.generated_at, field_name="generated_at")
        _git_sha(self.source_sha, field_name="source_sha")
        keys = [item.subdivision for item in self.subdivisions]
        if len(keys) != len(set(keys)):
            raise ValueError("R6 subdivision evidence must be unique")
        r6_12 = next((item for item in self.subdivisions if item.subdivision == "R6.12"), None)
        if (
            r6_12 is not None
            and r6_12.status is IntegrationEvidenceStatus.PASS
            and r6_12.accepted_head != self.source_sha
        ):
            raise ValueError("R6.12 accepted_head must match integration source_sha")
        expected = IntegrationEvidenceStatus.PASS if not self.blockers else IntegrationEvidenceStatus.FAIL
        if self.status is not expected:
            raise ValueError("R6 integration status does not match subdivision evidence")
        if self.evidence_sha256 != _sha256_payload(self._payload()):
            raise ValueError("R6 integration evidence hash mismatch")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = self._payload()
        payload["evidence_sha256"] = self.evidence_sha256
        return payload

    @classmethod
    def build(
        cls,
        source_sha: str,
        subdivisions: Iterable[R6SubdivisionEvidence],
        *,
        generated_at: str | None = None,
    ) -> "R6IntegrationReport":
        values = tuple(sorted(subdivisions, key=lambda item: int(item.subdivision.split(".")[1])))
        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        normalized_sha = _git_sha(source_sha, field_name="source_sha")
        provisional = cls(timestamp, normalized_sha, values, IntegrationEvidenceStatus.FAIL, "")
        expected = IntegrationEvidenceStatus.PASS if not provisional.blockers else IntegrationEvidenceStatus.FAIL
        provisional = cls(timestamp, normalized_sha, values, expected, "")
        final = cls(timestamp, normalized_sha, values, expected, _sha256_payload(provisional._payload()))
        final.validate()
        return final

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "R6IntegrationReport":
        report = cls(
            generated_at=str(payload["generated_at"]),
            source_sha=str(payload["source_sha"]),
            subdivisions=tuple(R6SubdivisionEvidence.from_dict(item) for item in payload.get("subdivisions", [])),
            status=IntegrationEvidenceStatus(str(payload["status"])),
            evidence_sha256=str(payload["evidence_sha256"]),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if tuple(payload.get("blockers") or ()) != report.blockers:
            raise ValueError("serialized R6 integration blockers do not match evidence")
        report.validate()
        return report


def rehearse_fixture_rollback(
    project_root: str | Path,
    support_root: str | Path,
    mutation_path: str,
) -> RollbackRehearsalEvidence:
    """Exercise existing backup/recovery/audit primitives on an explicitly marked test fixture only."""

    project = Path(project_root).resolve(strict=True)
    support = Path(support_root).resolve(strict=False)
    boundary = WorkspaceBoundary(project)
    marker = boundary.resolve(_FIXTURE_MARKER, must_exist=True)
    if not marker.is_file():
        raise PermissionError("rollback rehearsal fixture marker must be a file")
    target = boundary.resolve(_safe_relative_path(mutation_path), must_exist=True)
    if not target.is_file():
        raise ValueError("rollback rehearsal mutation target must be a file")
    if support == project or project in support.parents or support in project.parents:
        raise ValueError("rollback rehearsal support_root must be outside the fixture project tree")
    support.mkdir(parents=True, exist_ok=True)

    before_files = {
        boundary.relative(path): _sha256_file(path)
        for path in sorted(item for item in project.rglob("*") if item.is_file())
    }
    audit = AuditLog(support / "audit.jsonl")
    recovery = RecoveryJournal(support / "recovery.json")
    safe_change = SafeChangeManager(project, support / "safechange")
    backup = BackupManager(support / "backups")

    audit.append("r6.patch", "rollback-rehearsal-start", "KodePatchGate", "started", {"target": boundary.relative(target)})
    snapshot = safe_change.snapshot([target])
    archive = backup.create_archive(project, label="r6-rollback-rehearsal")
    archive_verified_before = backup.verify(archive)
    recovery.save("r6-rollback-rehearsal", "mutating", {"archive": archive.name, "target": boundary.relative(target)})
    target.write_bytes(b"KODEPOIA_R6_ROLLBACK_REHEARSAL_MUTATION\n")
    audit.append("r6.patch", "fixture-mutated", "KodePatchGate", "success", {"snapshot": snapshot.name})

    backup.restore(archive, project, overwrite=True)
    after_boundary = WorkspaceBoundary(project)
    after_files = {
        after_boundary.relative(path): _sha256_file(path)
        for path in sorted(item for item in project.rglob("*") if item.is_file())
    }
    restored = before_files == after_files
    archive_verified_after = backup.verify(archive)
    recovery.clear()
    checkpoint_cleared = recovery.load() is None
    audit.append(
        "r6.patch",
        "rollback-rehearsal-complete",
        "KodePatchGate",
        "success" if restored else "failure",
        {"restored_hashes_match": restored, "archive_verified": archive_verified_after},
    )
    audit_valid = audit.verify()
    status = (
        RehearsalStatus.PASS
        if restored and archive_verified_before and archive_verified_after and checkpoint_cleared and audit_valid
        else RehearsalStatus.FAIL
    )
    payload = {
        "status": status.value,
        "source": "KodePatchGate.rehearse_fixture_rollback",
        "restored_hashes_match": restored,
        "backup_verified": archive_verified_before and archive_verified_after,
        "audit_chain_valid": audit_valid,
        "recovery_checkpoint_cleared": checkpoint_cleared,
        "before_hashes": before_files,
        "after_hashes": after_files,
        "snapshot_manifest_sha256": _sha256_file(snapshot / "MANIFEST.txt"),
        "archive_sha256": _sha256_file(archive),
    }
    return RollbackRehearsalEvidence(
        status=status,
        source="KodePatchGate.rehearse_fixture_rollback",
        evidence_sha256=_sha256_payload(payload),
        restored_hashes_match=restored,
        backup_verified=archive_verified_before and archive_verified_after,
        audit_chain_valid=audit_valid,
        recovery_checkpoint_cleared=checkpoint_cleared,
        details={
            "before_hashes": before_files,
            "after_hashes": after_files,
            "snapshot_manifest_sha256": payload["snapshot_manifest_sha256"],
            "archive_sha256": payload["archive_sha256"],
        },
    )


class PatchGateStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve(strict=False)
        self.boundary = WorkspaceBoundary(self.project_root)
        self.metadata_root = self.boundary.resolve(".kodepoia", must_exist=False)
        self.root = self.boundary.resolve(".kodepoia/patch_gates", must_exist=False)

    def save(self, report: PatchGateReport) -> tuple[Path, Path]:
        report.validate()
        if not self.metadata_root.is_dir():
            raise FileNotFoundError("project .kodepoia metadata directory is not initialized")
        self.root.mkdir(parents=True, exist_ok=True)
        latest = self.boundary.resolve(f".kodepoia/patch_gates/{report.patch_id}-latest.json")
        stamp = report.generated_at.replace(":", "").replace("-", "").replace(".", "")
        snapshot = self.boundary.resolve(f".kodepoia/patch_gates/{report.patch_id}-{stamp}.json")
        payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        for destination in (latest, snapshot):
            temporary = destination.with_name(f".{destination.name}.tmp")
            temporary.write_text(payload, encoding="utf-8")
            temporary.replace(destination)
        return latest, snapshot

    def load_latest(self, patch_id: str) -> PatchGateReport:
        safe = _stable_id(patch_id, field_name="patch_id")
        path = self.boundary.resolve(f".kodepoia/patch_gates/{safe}-latest.json", must_exist=True)
        return PatchGateReport.from_dict(json.loads(path.read_text(encoding="utf-8")))
