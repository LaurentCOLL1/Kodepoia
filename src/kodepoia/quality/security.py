from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Mapping

from kodepoia.kodecode.workspace import WorkspaceBoundary
from kodepoia.quality.build import redact_sensitive
from kodepoia.quality.health import HealthDimension, HealthMetric, HealthStatus
from kodepoia.quality.tests import TestCaseResult, TestCaseStatus


_SCHEMA_VERSION = 1
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{1,127}$")
_ASVS_REF_RE = re.compile(r"^v5\.0\.0-\d+\.\d+\.\d+$")


def _parse_timestamp(value: str, *, field_name: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return parsed


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _stable_id(value: str, *, field_name: str) -> str:
    normalized = value.strip().lower()
    if not _ID_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a stable lowercase identifier")
    return normalized


class SecurityApplicability(StrEnum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"


class SecurityCheckStatus(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class SecurityReportStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class SecuritySeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityCategory(StrEnum):
    PATH = "path"
    INPUT = "input"
    NETWORK = "network"
    AUTH = "auth"
    SESSION = "session"
    SECRET_STORAGE = "secret_storage"
    DEPENDENCY = "dependency"
    EXECUTION = "execution"
    GOVERNANCE = "governance"
    OTHER = "other"


class ResidualRisk(StrEnum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DependencySecurityStatus(StrEnum):
    CLEAR = "clear"
    AFFECTED = "affected"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ThreatAsset:
    id: str
    name: str
    description: str = ""
    sensitivity: str = "internal"

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _stable_id(self.id, field_name="asset id"))
        if not self.name.strip():
            raise ValueError("asset name cannot be empty")
        if not self.sensitivity.strip():
            raise ValueError("asset sensitivity cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sensitivity": self.sensitivity,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ThreatAsset:
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            description=str(payload.get("description", "")),
            sensitivity=str(payload.get("sensitivity", "internal")),
        )


@dataclass(frozen=True, slots=True)
class TrustBoundary:
    id: str
    name: str
    source_zone: str
    target_zone: str
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _stable_id(self.id, field_name="trust boundary id"))
        if not self.name.strip() or not self.source_zone.strip() or not self.target_zone.strip():
            raise ValueError("trust boundary name/source_zone/target_zone cannot be empty")
        if self.source_zone.strip() == self.target_zone.strip():
            raise ValueError("trust boundary must separate different zones")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_zone": self.source_zone,
            "target_zone": self.target_zone,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> TrustBoundary:
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            source_zone=str(payload["source_zone"]),
            target_zone=str(payload["target_zone"]),
            description=str(payload.get("description", "")),
        )


@dataclass(frozen=True, slots=True)
class SecurityEntryPoint:
    id: str
    name: str
    kind: str
    boundary_id: str | None = None
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _stable_id(self.id, field_name="entry point id"))
        if not self.name.strip() or not self.kind.strip():
            raise ValueError("entry point name/kind cannot be empty")
        if self.boundary_id is not None:
            object.__setattr__(
                self,
                "boundary_id",
                _stable_id(self.boundary_id, field_name="entry point boundary id"),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "boundary_id": self.boundary_id,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SecurityEntryPoint:
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            kind=str(payload["kind"]),
            boundary_id=(str(payload["boundary_id"]) if payload.get("boundary_id") else None),
            description=str(payload.get("description", "")),
        )


@dataclass(frozen=True, slots=True)
class Threat:
    id: str
    title: str
    scenario: str
    asset_ids: tuple[str, ...]
    entry_point_ids: tuple[str, ...] = ()
    boundary_ids: tuple[str, ...] = ()
    mitigations: tuple[str, ...] = ()
    residual_risk: ResidualRisk = ResidualRisk.UNKNOWN
    blocking: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _stable_id(self.id, field_name="threat id"))
        object.__setattr__(
            self,
            "asset_ids",
            tuple(_stable_id(item, field_name="threat asset id") for item in self.asset_ids),
        )
        object.__setattr__(
            self,
            "entry_point_ids",
            tuple(_stable_id(item, field_name="threat entry point id") for item in self.entry_point_ids),
        )
        object.__setattr__(
            self,
            "boundary_ids",
            tuple(_stable_id(item, field_name="threat boundary id") for item in self.boundary_ids),
        )
        if not self.title.strip() or not self.scenario.strip():
            raise ValueError("threat title/scenario cannot be empty")
        if not self.asset_ids:
            raise ValueError("threat must reference at least one asset")
        if not self.entry_point_ids and not self.boundary_ids:
            raise ValueError("threat must reference an entry point or trust boundary")
        if not self.mitigations:
            raise ValueError("threat must record at least one mitigation")
        if self.blocking and self.residual_risk not in {ResidualRisk.HIGH, ResidualRisk.CRITICAL}:
            raise ValueError("blocking threat must have high or critical residual risk")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "scenario": self.scenario,
            "asset_ids": list(self.asset_ids),
            "entry_point_ids": list(self.entry_point_ids),
            "boundary_ids": list(self.boundary_ids),
            "mitigations": list(self.mitigations),
            "residual_risk": self.residual_risk.value,
            "blocking": self.blocking,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> Threat:
        return cls(
            id=str(payload["id"]),
            title=str(payload["title"]),
            scenario=str(payload["scenario"]),
            asset_ids=tuple(str(item) for item in payload.get("asset_ids", [])),
            entry_point_ids=tuple(str(item) for item in payload.get("entry_point_ids", [])),
            boundary_ids=tuple(str(item) for item in payload.get("boundary_ids", [])),
            mitigations=tuple(str(item) for item in payload.get("mitigations", [])),
            residual_risk=ResidualRisk(str(payload.get("residual_risk", "unknown"))),
            blocking=bool(payload.get("blocking", False)),
        )


@dataclass(frozen=True, slots=True)
class ThreatModel:
    assets: tuple[ThreatAsset, ...]
    trust_boundaries: tuple[TrustBoundary, ...]
    entry_points: tuple[SecurityEntryPoint, ...]
    threats: tuple[Threat, ...]

    def validate(self) -> None:
        asset_ids = [item.id for item in self.assets]
        boundary_ids = [item.id for item in self.trust_boundaries]
        entry_ids = [item.id for item in self.entry_points]
        threat_ids = [item.id for item in self.threats]
        for name, values in (
            ("asset", asset_ids),
            ("trust boundary", boundary_ids),
            ("entry point", entry_ids),
            ("threat", threat_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} ids must be unique")
        if not self.assets or not self.trust_boundaries or not self.entry_points or not self.threats:
            raise ValueError("threat model must include assets, trust boundaries, entry points and threats")
        asset_set = set(asset_ids)
        boundary_set = set(boundary_ids)
        entry_set = set(entry_ids)
        for entry in self.entry_points:
            if entry.boundary_id is not None and entry.boundary_id not in boundary_set:
                raise ValueError(f"entry point references unknown trust boundary: {entry.id}")
        for threat in self.threats:
            if not set(threat.asset_ids) <= asset_set:
                raise ValueError(f"threat references unknown asset: {threat.id}")
            if not set(threat.boundary_ids) <= boundary_set:
                raise ValueError(f"threat references unknown trust boundary: {threat.id}")
            if not set(threat.entry_point_ids) <= entry_set:
                raise ValueError(f"threat references unknown entry point: {threat.id}")

    @property
    def blockers(self) -> tuple[str, ...]:
        self.validate()
        return tuple(item.id for item in self.threats if item.blocking)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "assets": [item.to_dict() for item in self.assets],
            "trust_boundaries": [item.to_dict() for item in self.trust_boundaries],
            "entry_points": [item.to_dict() for item in self.entry_points],
            "threats": [item.to_dict() for item in self.threats],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ThreatModel:
        model = cls(
            assets=tuple(ThreatAsset.from_dict(item) for item in payload.get("assets", [])),
            trust_boundaries=tuple(
                TrustBoundary.from_dict(item) for item in payload.get("trust_boundaries", [])
            ),
            entry_points=tuple(
                SecurityEntryPoint.from_dict(item) for item in payload.get("entry_points", [])
            ),
            threats=tuple(Threat.from_dict(item) for item in payload.get("threats", [])),
        )
        model.validate()
        return model


@dataclass(frozen=True, slots=True)
class SecurityRequirement:
    id: str
    category: SecurityCategory
    title: str
    applicability: SecurityApplicability
    status: SecurityCheckStatus
    severity: SecuritySeverity = SecuritySeverity.MEDIUM
    reference: str = ""
    rationale: str = ""
    evidence_source: str = ""
    blocking: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _stable_id(self.id, field_name="security requirement id"))
        if not self.title.strip():
            raise ValueError("security requirement title cannot be empty")
        if self.reference and not _ASVS_REF_RE.fullmatch(self.reference):
            raise ValueError("ASVS reference must use versioned v5.0.0-x.y.z form")
        if self.applicability is SecurityApplicability.NOT_APPLICABLE:
            if self.status is not SecurityCheckStatus.NOT_APPLICABLE:
                raise ValueError("not-applicable requirement must use NOT_APPLICABLE status")
            if not self.rationale.strip():
                raise ValueError("not-applicable requirement requires rationale")
            if self.blocking:
                raise ValueError("not-applicable requirement cannot block")
        else:
            if self.status is SecurityCheckStatus.NOT_APPLICABLE:
                raise ValueError("applicable requirement cannot use NOT_APPLICABLE status")
            if self.status in {
                SecurityCheckStatus.PASS,
                SecurityCheckStatus.WARN,
                SecurityCheckStatus.FAIL,
            } and not self.evidence_source.strip():
                raise ValueError("measured security requirement requires evidence_source")
            if self.blocking and self.status is not SecurityCheckStatus.FAIL:
                raise ValueError("only failed security requirements can block")
        object.__setattr__(self, "details", dict(redact_sensitive(self.details)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category.value,
            "title": self.title,
            "applicability": self.applicability.value,
            "status": self.status.value,
            "severity": self.severity.value,
            "reference": self.reference,
            "rationale": self.rationale,
            "evidence_source": self.evidence_source,
            "blocking": self.blocking,
            "details": redact_sensitive(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SecurityRequirement:
        return cls(
            id=str(payload["id"]),
            category=SecurityCategory(str(payload["category"])),
            title=str(payload["title"]),
            applicability=SecurityApplicability(str(payload["applicability"])),
            status=SecurityCheckStatus(str(payload["status"])),
            severity=SecuritySeverity(str(payload.get("severity", "medium"))),
            reference=str(payload.get("reference", "")),
            rationale=str(payload.get("rationale", "")),
            evidence_source=str(payload.get("evidence_source", "")),
            blocking=bool(payload.get("blocking", False)),
            details=dict(payload.get("details") or {}),
        )


@dataclass(frozen=True, slots=True)
class DependencyVulnerabilityEvidence:
    component: str
    version: str
    status: DependencySecurityStatus
    checked_at: str
    source: str
    advisory_ids: tuple[str, ...] = ()
    severity: SecuritySeverity = SecuritySeverity.INFO
    blocking: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        component = self.component.strip().lower()
        if not component or not self.version.strip():
            raise ValueError("dependency component/version cannot be empty")
        if not self.source.strip():
            raise ValueError("dependency vulnerability evidence requires provenance source")
        _parse_timestamp(self.checked_at, field_name="dependency checked_at")
        if self.status is DependencySecurityStatus.AFFECTED and not self.advisory_ids:
            raise ValueError("affected dependency evidence requires advisory_ids")
        if self.status is not DependencySecurityStatus.AFFECTED and self.blocking:
            raise ValueError("only affected dependency evidence can block")
        if self.status is DependencySecurityStatus.CLEAR and self.advisory_ids:
            raise ValueError("clear dependency evidence cannot carry advisory_ids")
        object.__setattr__(self, "component", component)
        object.__setattr__(self, "advisory_ids", tuple(sorted(set(self.advisory_ids))))
        object.__setattr__(self, "details", dict(redact_sensitive(self.details)))

    @property
    def id(self) -> str:
        return f"{self.component}@{self.version}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "version": self.version,
            "status": self.status.value,
            "checked_at": self.checked_at,
            "source": self.source,
            "advisory_ids": list(self.advisory_ids),
            "severity": self.severity.value,
            "blocking": self.blocking,
            "details": redact_sensitive(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> DependencyVulnerabilityEvidence:
        return cls(
            component=str(payload["component"]),
            version=str(payload["version"]),
            status=DependencySecurityStatus(str(payload["status"])),
            checked_at=str(payload["checked_at"]),
            source=str(payload["source"]),
            advisory_ids=tuple(str(item) for item in payload.get("advisory_ids", [])),
            severity=SecuritySeverity(str(payload.get("severity", "info"))),
            blocking=bool(payload.get("blocking", False)),
            details=dict(payload.get("details") or {}),
        )


@dataclass(frozen=True, slots=True)
class SecurityReport:
    generated_at: str
    project_name: str
    threat_model: ThreatModel
    requirements: tuple[SecurityRequirement, ...]
    dependencies: tuple[DependencyVulnerabilityEvidence, ...]
    status: SecurityReportStatus
    evidence_sha256: str
    schema_version: int = _SCHEMA_VERSION

    @property
    def counts(self) -> dict[str, int]:
        return {
            "requirements_total": len(self.requirements),
            "applicable": sum(
                item.applicability is SecurityApplicability.APPLICABLE for item in self.requirements
            ),
            "not_applicable": sum(
                item.applicability is SecurityApplicability.NOT_APPLICABLE
                for item in self.requirements
            ),
            "pass": sum(item.status is SecurityCheckStatus.PASS for item in self.requirements),
            "warn": sum(item.status is SecurityCheckStatus.WARN for item in self.requirements),
            "fail": sum(item.status is SecurityCheckStatus.FAIL for item in self.requirements),
            "unknown": sum(item.status is SecurityCheckStatus.UNKNOWN for item in self.requirements),
            "dependencies_total": len(self.dependencies),
            "dependencies_clear": sum(
                item.status is DependencySecurityStatus.CLEAR for item in self.dependencies
            ),
            "dependencies_affected": sum(
                item.status is DependencySecurityStatus.AFFECTED for item in self.dependencies
            ),
            "dependencies_unknown": sum(
                item.status is DependencySecurityStatus.UNKNOWN for item in self.dependencies
            ),
            "threats_total": len(self.threat_model.threats),
            "blocking_threats": len(self.threat_model.blockers),
        }

    @property
    def blockers(self) -> tuple[str, ...]:
        requirement_blockers = [
            f"requirement:{item.id}" for item in self.requirements if item.blocking
        ]
        dependency_blockers = [
            f"dependency:{item.id}" for item in self.dependencies if item.blocking
        ]
        threat_blockers = [f"threat:{item}" for item in self.threat_model.blockers]
        return tuple(requirement_blockers + dependency_blockers + threat_blockers)

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "project_name": self.project_name,
            "status": self.status.value,
            "counts": self.counts,
            "blockers": list(self.blockers),
            "threat_model": self.threat_model.to_dict(),
            "requirements": [item.to_dict() for item in self.requirements],
            "dependencies": [item.to_dict() for item in self.dependencies],
        }

    def validate(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported security report schema version")
        _parse_timestamp(self.generated_at, field_name="generated_at")
        self.threat_model.validate()
        requirement_ids = [item.id for item in self.requirements]
        dependency_ids = [item.id for item in self.dependencies]
        if len(requirement_ids) != len(set(requirement_ids)):
            raise ValueError("security requirement ids must be unique")
        if len(dependency_ids) != len(set(dependency_ids)):
            raise ValueError("dependency evidence identities must be unique")
        expected_status = KodeAppSecurity.status_for(
            self.threat_model,
            self.requirements,
            self.dependencies,
        )
        if self.status is not expected_status:
            raise ValueError("security report status does not match evidence")
        if self.evidence_sha256 != _sha256(self._payload()):
            raise ValueError("security report evidence hash mismatch")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = self._payload()
        payload["evidence_sha256"] = self.evidence_sha256
        return payload

    @classmethod
    def build(
        cls,
        project_name: str,
        threat_model: ThreatModel,
        requirements: Iterable[SecurityRequirement],
        dependencies: Iterable[DependencyVulnerabilityEvidence],
        *,
        generated_at: str | None = None,
    ) -> SecurityReport:
        threat_model.validate()
        requirement_tuple = tuple(requirements)
        dependency_tuple = tuple(dependencies)
        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        status = KodeAppSecurity.status_for(threat_model, requirement_tuple, dependency_tuple)
        provisional = cls(
            timestamp,
            project_name,
            threat_model,
            requirement_tuple,
            dependency_tuple,
            status,
            "",
        )
        digest = _sha256(provisional._payload())
        report = cls(
            timestamp,
            project_name,
            threat_model,
            requirement_tuple,
            dependency_tuple,
            status,
            digest,
        )
        report.validate()
        return report

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SecurityReport:
        if int(payload.get("schema_version", 0)) != _SCHEMA_VERSION:
            raise ValueError("unsupported security report schema version")
        report = cls(
            generated_at=str(payload["generated_at"]),
            project_name=str(payload.get("project_name", "")),
            threat_model=ThreatModel.from_dict(dict(payload["threat_model"])),
            requirements=tuple(
                SecurityRequirement.from_dict(item) for item in payload.get("requirements", [])
            ),
            dependencies=tuple(
                DependencyVulnerabilityEvidence.from_dict(item)
                for item in payload.get("dependencies", [])
            ),
            status=SecurityReportStatus(str(payload["status"])),
            evidence_sha256=str(payload["evidence_sha256"]),
        )
        if dict(payload.get("counts") or {}) != report.counts:
            raise ValueError("serialized security counts do not match evidence")
        if tuple(payload.get("blockers") or ()) != report.blockers:
            raise ValueError("serialized security blockers do not match evidence")
        report.validate()
        return report


class KodeAppSecurity:
    @staticmethod
    def status_for(
        threat_model: ThreatModel,
        requirements: Iterable[SecurityRequirement],
        dependencies: Iterable[DependencyVulnerabilityEvidence],
    ) -> SecurityReportStatus:
        threat_model.validate()
        requirement_values = tuple(requirements)
        dependency_values = tuple(dependencies)
        if (
            any(
                item.blocking or item.status is SecurityCheckStatus.FAIL
                for item in requirement_values
            )
            or any(
                item.blocking or item.status is DependencySecurityStatus.AFFECTED
                for item in dependency_values
            )
            or threat_model.blockers
        ):
            return SecurityReportStatus.FAIL
        applicable = [
            item
            for item in requirement_values
            if item.applicability is SecurityApplicability.APPLICABLE
        ]
        if (
            not applicable
            and not dependency_values
            and all(item.residual_risk is ResidualRisk.UNKNOWN for item in threat_model.threats)
        ):
            return SecurityReportStatus.UNKNOWN
        if (
            any(
                item.status in {SecurityCheckStatus.WARN, SecurityCheckStatus.UNKNOWN}
                for item in applicable
            )
            or any(item.status is DependencySecurityStatus.UNKNOWN for item in dependency_values)
            or any(
                item.residual_risk
                in {
                    ResidualRisk.UNKNOWN,
                    ResidualRisk.MEDIUM,
                    ResidualRisk.HIGH,
                    ResidualRisk.CRITICAL,
                }
                for item in threat_model.threats
            )
        ):
            return SecurityReportStatus.WARN
        return SecurityReportStatus.PASS

    @staticmethod
    def score_for(report: SecurityReport) -> float | None:
        report.validate()
        values: list[float] = []
        requirement_scores = {
            SecurityCheckStatus.PASS: 100.0,
            SecurityCheckStatus.WARN: 70.0,
            SecurityCheckStatus.UNKNOWN: 40.0,
            SecurityCheckStatus.FAIL: 0.0,
        }
        for item in report.requirements:
            if item.applicability is SecurityApplicability.APPLICABLE:
                values.append(requirement_scores[item.status])
        dependency_scores = {
            DependencySecurityStatus.CLEAR: 100.0,
            DependencySecurityStatus.UNKNOWN: 40.0,
            DependencySecurityStatus.AFFECTED: 0.0,
        }
        values.extend(dependency_scores[item.status] for item in report.dependencies)
        threat_scores = {
            ResidualRisk.LOW: 90.0,
            ResidualRisk.MEDIUM: 70.0,
            ResidualRisk.HIGH: 35.0,
            ResidualRisk.CRITICAL: 0.0,
        }
        values.extend(
            threat_scores[item.residual_risk]
            for item in report.threat_model.threats
            if item.residual_risk is not ResidualRisk.UNKNOWN
        )
        if not values:
            return None
        return round(sum(values) / len(values), 2)

    @staticmethod
    def to_health_metric(report: SecurityReport) -> HealthMetric:
        report.validate()
        if report.status is SecurityReportStatus.UNKNOWN:
            return HealthMetric(
                dimension=HealthDimension.SECURITY,
                status=HealthStatus.UNKNOWN,
                summary="Security evidence is not yet sufficient for a measured result",
                source="KodeAppSecurity",
                details={
                    "counts": report.counts,
                    "blockers": list(report.blockers),
                    "evidence_sha256": report.evidence_sha256,
                },
            )
        status_map = {
            SecurityReportStatus.PASS: HealthStatus.PASS,
            SecurityReportStatus.WARN: HealthStatus.WARN,
            SecurityReportStatus.FAIL: HealthStatus.FAIL,
        }
        score = KodeAppSecurity.score_for(report)
        if score is None:
            raise ValueError("measured security report requires a score")
        return HealthMetric(
            dimension=HealthDimension.SECURITY,
            status=status_map[report.status],
            score=score,
            summary=(
                f"{report.counts['applicable']} applicable requirement(s), "
                f"{report.counts['dependencies_total']} dependency observation(s), "
                f"{report.counts['threats_total']} threat(s)"
            ),
            source="KodeAppSecurity",
            blocking=bool(report.blockers),
            details={
                "counts": report.counts,
                "blockers": list(report.blockers),
                "evidence_sha256": report.evidence_sha256,
            },
        )

    @staticmethod
    def to_test_cases(report: SecurityReport) -> tuple[TestCaseResult, ...]:
        report.validate()
        cases: list[TestCaseResult] = []
        requirement_status = {
            SecurityCheckStatus.PASS: TestCaseStatus.PASS,
            SecurityCheckStatus.FAIL: TestCaseStatus.FAIL,
            SecurityCheckStatus.WARN: TestCaseStatus.SKIP,
            SecurityCheckStatus.UNKNOWN: TestCaseStatus.SKIP,
            SecurityCheckStatus.NOT_APPLICABLE: TestCaseStatus.SKIP,
        }
        for item in report.requirements:
            cases.append(
                TestCaseResult(
                    id=f"security:{item.id}",
                    status=requirement_status[item.status],
                    duration_s=0.0,
                    message=item.title,
                    source="KodeAppSecurity",
                    details={
                        "category": item.category.value,
                        "applicability": item.applicability.value,
                        "severity": item.severity.value,
                        "reference": item.reference,
                        "blocking": item.blocking,
                    },
                )
            )
        dependency_status = {
            DependencySecurityStatus.CLEAR: TestCaseStatus.PASS,
            DependencySecurityStatus.AFFECTED: TestCaseStatus.FAIL,
            DependencySecurityStatus.UNKNOWN: TestCaseStatus.SKIP,
        }
        for item in report.dependencies:
            cases.append(
                TestCaseResult(
                    id=f"security:dependency:{item.component}:{item.version}",
                    status=dependency_status[item.status],
                    duration_s=0.0,
                    message=f"Dependency vulnerability evidence for {item.id}",
                    source="KodeAppSecurity",
                    details={
                        "severity": item.severity.value,
                        "blocking": item.blocking,
                        "advisory_ids": list(item.advisory_ids),
                        "checked_at": item.checked_at,
                        "source": item.source,
                    },
                )
            )
        for item in report.threat_model.threats:
            if item.blocking:
                status = TestCaseStatus.FAIL
            elif item.residual_risk is ResidualRisk.LOW:
                status = TestCaseStatus.PASS
            else:
                status = TestCaseStatus.SKIP
            cases.append(
                TestCaseResult(
                    id=f"security:threat:{item.id}",
                    status=status,
                    duration_s=0.0,
                    message=item.title,
                    source="KodeAppSecurity",
                    details={
                        "residual_risk": item.residual_risk.value,
                        "blocking": item.blocking,
                    },
                )
            )
        return tuple(cases)


class SecurityStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve(strict=False)
        self.boundary = WorkspaceBoundary(self.project_root)
        self.metadata_root = self.boundary.resolve(".kodepoia", must_exist=False)
        self.security_root = self.boundary.resolve(
            ".kodepoia/diagnostics/security",
            must_exist=False,
        )

    @staticmethod
    def _safe_project(name: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip(".-")
        return safe or "project"

    def save(self, report: SecurityReport) -> tuple[Path, Path]:
        report.validate()
        if not self.metadata_root.is_dir():
            raise FileNotFoundError("project .kodepoia metadata directory is not initialized")
        self.security_root.mkdir(parents=True, exist_ok=True)
        name = self._safe_project(report.project_name)
        latest = self.boundary.resolve(
            f".kodepoia/diagnostics/security/{name}-latest.json"
        )
        stamp = report.generated_at.replace(":", "").replace("-", "").replace(".", "")
        snapshot = self.boundary.resolve(
            f".kodepoia/diagnostics/security/security-{name}-{stamp}.json"
        )
        payload = json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"
        for destination in (latest, snapshot):
            temporary = destination.with_name(f".{destination.name}.tmp")
            temporary.write_text(payload, encoding="utf-8")
            temporary.replace(destination)
        return latest, snapshot

    def load_latest(self, project_name: str) -> SecurityReport:
        path = self.boundary.resolve(
            f".kodepoia/diagnostics/security/{self._safe_project(project_name)}-latest.json",
            must_exist=True,
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("security report must be a JSON object")
        return SecurityReport.from_dict(payload)


def applicable_requirement(
    *,
    id: str,
    category: SecurityCategory,
    title: str,
    status: SecurityCheckStatus,
    evidence_source: str = "",
    severity: SecuritySeverity = SecuritySeverity.MEDIUM,
    reference: str = "",
    rationale: str = "",
    blocking: bool = False,
    details: Mapping[str, Any] | None = None,
) -> SecurityRequirement:
    return SecurityRequirement(
        id=id,
        category=category,
        title=title,
        applicability=SecurityApplicability.APPLICABLE,
        status=status,
        severity=severity,
        reference=reference,
        rationale=rationale,
        evidence_source=evidence_source,
        blocking=blocking,
        details=dict(details or {}),
    )


def not_applicable_requirement(
    *,
    id: str,
    category: SecurityCategory,
    title: str,
    rationale: str,
    severity: SecuritySeverity = SecuritySeverity.INFO,
    reference: str = "",
) -> SecurityRequirement:
    return SecurityRequirement(
        id=id,
        category=category,
        title=title,
        applicability=SecurityApplicability.NOT_APPLICABLE,
        status=SecurityCheckStatus.NOT_APPLICABLE,
        severity=severity,
        reference=reference,
        rationale=rationale,
    )


def secure_storage_requirement(
    *,
    backend: str,
    persists_plaintext: bool,
    evidence_source: str,
) -> SecurityRequirement:
    backend_name = backend.strip().lower()
    if not backend_name:
        raise ValueError("secure-storage backend cannot be empty")
    is_os_backed = backend_name in {"os-keyring", "keyring", "windows-credential-manager"}
    passed = is_os_backed and not persists_plaintext
    return applicable_requirement(
        id="secret-storage.os-backed",
        category=SecurityCategory.SECRET_STORAGE,
        title="Secrets use OS-backed storage and are not persisted as plaintext",
        status=SecurityCheckStatus.PASS if passed else SecurityCheckStatus.FAIL,
        evidence_source=evidence_source,
        severity=SecuritySeverity.HIGH,
        blocking=not passed,
        details={
            "backend": backend_name,
            "persists_plaintext": persists_plaintext,
        },
    )


def kodepoia_threat_model() -> ThreatModel:
    """Architecture-level model; residual risk stays UNKNOWN until measured evidence exists."""
    return ThreatModel(
        assets=(
            ThreatAsset(
                "project.workspace",
                "Project workspace",
                "User project files and Kodepoia metadata constrained by WorkspaceBoundary.",
                "high",
            ),
            ThreatAsset(
                "secrets.os-store",
                "Delegated secrets",
                "Credentials stored through the OS-backed KodeSecrets backend.",
                "critical",
            ),
            ThreatAsset(
                "audit.chain",
                "Audit evidence",
                "Hash-chained governance and mutation evidence.",
                "high",
            ),
            ThreatAsset(
                "model.context",
                "Model context",
                "Prompt/context material that must exclude raw secrets.",
                "high",
            ),
            ThreatAsset(
                "build.artifacts",
                "Build artifacts",
                "Source-SHA-bound packages and quality evidence.",
                "high",
            ),
        ),
        trust_boundaries=(
            TrustBoundary(
                "boundary.project-input",
                "Project input boundary",
                "user-controlled project",
                "kodepoia process",
                "Files and metadata enter Kodepoia from the project workspace.",
            ),
            TrustBoundary(
                "boundary.child-process",
                "Child process boundary",
                "kodepoia process",
                "sandboxed child process",
                "Structured tool execution crosses into allowlisted child processes.",
            ),
            TrustBoundary(
                "boundary.loopback",
                "Loopback service boundary",
                "kodepoia process",
                "loopback development service",
                "Godot LSP/DAP/debug services are expected to stay loopback-only.",
            ),
            TrustBoundary(
                "boundary.external-network",
                "External network boundary",
                "kodepoia process",
                "external service",
                "Any public-network research/download activity is permission-scoped.",
            ),
        ),
        entry_points=(
            SecurityEntryPoint(
                "entry.project-files",
                "Project files",
                "filesystem",
                "boundary.project-input",
                "Paths and file content supplied by a user project.",
            ),
            SecurityEntryPoint(
                "entry.tool-request",
                "Structured tool request",
                "tool-api",
                "boundary.child-process",
                "Model-originated actions are converted to structured governed requests.",
            ),
            SecurityEntryPoint(
                "entry.child-process",
                "Allowlisted process execution",
                "process",
                "boundary.child-process",
                "ProcessSandbox launches fixed/allowlisted executables without shell=True.",
            ),
            SecurityEntryPoint(
                "entry.loopback-service",
                "Local development sockets",
                "network",
                "boundary.loopback",
                "Godot automation uses local LSP/DAP/debug sockets.",
            ),
            SecurityEntryPoint(
                "entry.external-network",
                "Permission-scoped external network",
                "network",
                "boundary.external-network",
                "Research and downloads may cross the external network boundary.",
            ),
        ),
        threats=(
            Threat(
                "threat.path-traversal",
                "Workspace path traversal",
                "Untrusted path input attempts to escape the configured project root.",
                ("project.workspace", "audit.chain"),
                entry_point_ids=("entry.project-files",),
                boundary_ids=("boundary.project-input",),
                mitigations=(
                    "Resolve all governed project paths through WorkspaceBoundary.",
                    "Reject symlink/path escapes instead of normalizing them into acceptance.",
                ),
            ),
            Threat(
                "threat.command-injection",
                "Arbitrary process execution",
                "Model or project-controlled data attempts to become a shell command or executable path.",
                ("project.workspace", "secrets.os-store", "audit.chain"),
                entry_point_ids=("entry.tool-request", "entry.child-process"),
                boundary_ids=("boundary.child-process",),
                mitigations=(
                    "Guardian and PermissionSet authorize structured execution requests.",
                    "ProcessSandbox uses shell=False, constrained cwd and executable allowlists.",
                    "Global KillSwitch tracks and terminates governed child processes.",
                ),
            ),
            Threat(
                "threat.secret-disclosure",
                "Raw secret disclosure",
                "A tool, report or model-context path exposes credentials outside delegated operations.",
                ("secrets.os-store", "model.context", "build.artifacts"),
                entry_point_ids=("entry.tool-request", "entry.external-network"),
                boundary_ids=("boundary.external-network",),
                mitigations=(
                    "Guardian denies raw SECRET_READ requests.",
                    "KodeSecrets delegates retrieval and quality evidence redacts secret-shaped fields/tokens.",
                    "Build and diagnostic evidence must never persist raw credentials.",
                ),
            ),
            Threat(
                "threat.loopback-exposure",
                "Development service exposure",
                "A local development protocol unintentionally binds beyond loopback or accepts an untrusted host.",
                ("project.workspace", "audit.chain"),
                entry_point_ids=("entry.loopback-service",),
                boundary_ids=("boundary.loopback",),
                mitigations=(
                    "Accepted Godot services remain loopback-only with fixed protocol entry points.",
                    "Do not expose arbitrary host/program/cwd fields from model input.",
                ),
            ),
            Threat(
                "threat.untrusted-download-execution",
                "Downloaded code bypasses governance",
                "Downloaded content is executed directly without sandbox/Guardian approval.",
                ("project.workspace", "secrets.os-store", "audit.chain"),
                entry_point_ids=("entry.external-network", "entry.child-process"),
                boundary_ids=("boundary.external-network", "boundary.child-process"),
                mitigations=(
                    "Guardian denies downloaded code execution outside KodeSandbox.",
                    "Installation remains an explicit approval boundary with SafeChange where required.",
                ),
            ),
        ),
    )
