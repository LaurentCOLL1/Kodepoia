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
_PLATFORM_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_PERSONAL_VALUE_KEY_RE = re.compile(
    r"(?:^|_)(?:raw|sample|example|actual|personal|user|customer|person|email|phone|address|"
    r"location|ip|device[_-]?id|advertising[_-]?id|account[_-]?id|identifier|payload|content|value)(?:$|_)",
    re.IGNORECASE,
)
_APPLE_PLATFORMS = {"ios", "ipados", "macos", "tvos", "visionos", "watchos"}
_GOOGLE_PLAY_PLATFORMS = {"android"}


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


def _stable_platform(value: str) -> str:
    normalized = value.strip().lower()
    if not _PLATFORM_RE.fullmatch(normalized):
        raise ValueError("platform must be a stable lowercase identifier")
    return normalized


def _sanitize_privacy_value(value: Any, *, key: str = "") -> Any:
    """Persist privacy evidence as metadata, never raw personal-data samples."""

    value = redact_sensitive(value, key=key)
    if key and _PERSONAL_VALUE_KEY_RE.search(key):
        if value not in (None, "", [], {}, ()):
            return "<redacted-personal-data>"
        return value
    if isinstance(value, Mapping):
        return {
            str(item_key): _sanitize_privacy_value(item_value, key=str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_sanitize_privacy_value(item, key=key) for item in value]
    if isinstance(value, str):
        redacted = _EMAIL_RE.sub("<redacted-email>", value)
        redacted = _IPV4_RE.sub("<redacted-ip>", redacted)
        return redacted
    return value


def redact_privacy_evidence(value: Any) -> Any:
    return _sanitize_privacy_value(value)


class PrivacyDisposition(StrEnum):
    COLLECTED = "collected"
    NONE = "none"
    NOT_APPLICABLE = "not_applicable"


class PrivacyBasisState(StrEnum):
    UNSPECIFIED = "unspecified"
    DECLARED = "declared"
    NOT_APPLICABLE = "not_applicable"


class PrivacySensitivity(StrEnum):
    UNKNOWN = "unknown"
    NON_PERSONAL = "non_personal"
    PERSONAL = "personal"
    SENSITIVE = "sensitive"


class PrivacyApplicability(StrEnum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"


class PrivacyCheckStatus(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class PrivacyReportStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class PrivacySeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StoreKind(StrEnum):
    APPLE_APP_STORE = "apple_app_store"
    GOOGLE_PLAY = "google_play"
    OTHER = "other"


class DeclarationValue(StrEnum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class PrivacyDataItem:
    id: str
    category: str
    disposition: PrivacyDisposition
    platform_scope: tuple[str, ...]
    evidence_source: str
    data_source: str = ""
    purpose: str = ""
    storage: tuple[str, ...] = ()
    recipients: tuple[str, ...] = ()
    retention: str = ""
    deletion: str = ""
    sensitivity: PrivacySensitivity = PrivacySensitivity.UNKNOWN
    basis_state: PrivacyBasisState = PrivacyBasisState.UNSPECIFIED
    legal_basis: str = ""
    consent_basis: str = ""
    basis_source: str = ""
    rationale: str = ""
    basis_rationale: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _stable_id(self.id, field_name="privacy data id"))
        category = self.category.strip().lower()
        if not category:
            raise ValueError("privacy data category cannot be empty")
        object.__setattr__(self, "category", category)
        platforms = tuple(sorted({_stable_platform(item) for item in self.platform_scope}))
        if not platforms:
            raise ValueError("privacy data item requires platform_scope")
        object.__setattr__(self, "platform_scope", platforms)
        if not self.evidence_source.strip():
            raise ValueError("privacy data item requires evidence_source")

        storage = tuple(item.strip() for item in self.storage if item.strip())
        recipients = tuple(item.strip() for item in self.recipients if item.strip())
        object.__setattr__(self, "storage", storage)
        object.__setattr__(self, "recipients", recipients)

        if self.disposition is PrivacyDisposition.COLLECTED:
            if not self.data_source.strip():
                raise ValueError("collected privacy data requires data_source")
            if not self.purpose.strip():
                raise ValueError("collected privacy data requires purpose")
            if not storage:
                raise ValueError("collected privacy data requires storage")
            if not self.retention.strip():
                raise ValueError("collected privacy data requires retention")
            if not self.deletion.strip():
                raise ValueError("collected privacy data requires deletion")
        else:
            if not self.rationale.strip():
                raise ValueError("none/not_applicable privacy data requires rationale")
            if any(
                (
                    self.data_source.strip(),
                    self.purpose.strip(),
                    storage,
                    recipients,
                    self.retention.strip(),
                    self.deletion.strip(),
                )
            ):
                raise ValueError("none/not_applicable privacy data cannot carry collection lifecycle fields")

        if self.basis_state is PrivacyBasisState.DECLARED:
            if not (self.legal_basis.strip() or self.consent_basis.strip()):
                raise ValueError("declared privacy basis requires legal_basis or consent_basis")
            if not self.basis_source.strip():
                raise ValueError("declared privacy basis requires basis_source")
        elif self.basis_state is PrivacyBasisState.NOT_APPLICABLE:
            if self.legal_basis.strip() or self.consent_basis.strip() or self.basis_source.strip():
                raise ValueError("not-applicable privacy basis cannot carry declared basis fields")
            if not self.basis_rationale.strip():
                raise ValueError("not-applicable privacy basis requires rationale")
        else:
            if self.legal_basis.strip() or self.consent_basis.strip() or self.basis_source.strip():
                raise ValueError("unspecified privacy basis cannot carry declared basis fields")

        object.__setattr__(self, "details", dict(redact_privacy_evidence(self.details)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "disposition": self.disposition.value,
            "platform_scope": list(self.platform_scope),
            "evidence_source": self.evidence_source,
            "data_source": self.data_source,
            "purpose": self.purpose,
            "storage": list(self.storage),
            "recipients": list(self.recipients),
            "retention": self.retention,
            "deletion": self.deletion,
            "sensitivity": self.sensitivity.value,
            "basis_state": self.basis_state.value,
            "legal_basis": self.legal_basis,
            "consent_basis": self.consent_basis,
            "basis_source": self.basis_source,
            "rationale": self.rationale,
            "basis_rationale": self.basis_rationale,
            "details": redact_privacy_evidence(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PrivacyDataItem":
        return cls(
            id=str(payload["id"]),
            category=str(payload["category"]),
            disposition=PrivacyDisposition(str(payload["disposition"])),
            platform_scope=tuple(str(item) for item in payload.get("platform_scope", [])),
            evidence_source=str(payload["evidence_source"]),
            data_source=str(payload.get("data_source", "")),
            purpose=str(payload.get("purpose", "")),
            storage=tuple(str(item) for item in payload.get("storage", [])),
            recipients=tuple(str(item) for item in payload.get("recipients", [])),
            retention=str(payload.get("retention", "")),
            deletion=str(payload.get("deletion", "")),
            sensitivity=PrivacySensitivity(str(payload.get("sensitivity", "unknown"))),
            basis_state=PrivacyBasisState(str(payload.get("basis_state", "unspecified"))),
            legal_basis=str(payload.get("legal_basis", "")),
            consent_basis=str(payload.get("consent_basis", "")),
            basis_source=str(payload.get("basis_source", "")),
            rationale=str(payload.get("rationale", "")),
            basis_rationale=str(payload.get("basis_rationale", "")),
            details=dict(payload.get("details") or {}),
        )


@dataclass(frozen=True, slots=True)
class PrivacyIssue:
    id: str
    title: str
    applicability: PrivacyApplicability
    status: PrivacyCheckStatus
    severity: PrivacySeverity = PrivacySeverity.MEDIUM
    rationale: str = ""
    evidence_source: str = ""
    blocking: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _stable_id(self.id, field_name="privacy issue id"))
        if not self.title.strip():
            raise ValueError("privacy issue title cannot be empty")
        if self.applicability is PrivacyApplicability.NOT_APPLICABLE:
            if self.status is not PrivacyCheckStatus.NOT_APPLICABLE:
                raise ValueError("not-applicable privacy issue must use NOT_APPLICABLE status")
            if not self.rationale.strip():
                raise ValueError("not-applicable privacy issue requires rationale")
            if self.blocking:
                raise ValueError("not-applicable privacy issue cannot block")
        else:
            if self.status is PrivacyCheckStatus.NOT_APPLICABLE:
                raise ValueError("applicable privacy issue cannot use NOT_APPLICABLE status")
            if self.status in {
                PrivacyCheckStatus.PASS,
                PrivacyCheckStatus.WARN,
                PrivacyCheckStatus.FAIL,
            } and not self.evidence_source.strip():
                raise ValueError("measured privacy issue requires evidence_source")
            if self.blocking and self.status is not PrivacyCheckStatus.FAIL:
                raise ValueError("only failed privacy issues can block")
        object.__setattr__(self, "details", dict(redact_privacy_evidence(self.details)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "applicability": self.applicability.value,
            "status": self.status.value,
            "severity": self.severity.value,
            "rationale": self.rationale,
            "evidence_source": self.evidence_source,
            "blocking": self.blocking,
            "details": redact_privacy_evidence(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PrivacyIssue":
        return cls(
            id=str(payload["id"]),
            title=str(payload["title"]),
            applicability=PrivacyApplicability(str(payload["applicability"])),
            status=PrivacyCheckStatus(str(payload["status"])),
            severity=PrivacySeverity(str(payload.get("severity", "medium"))),
            rationale=str(payload.get("rationale", "")),
            evidence_source=str(payload.get("evidence_source", "")),
            blocking=bool(payload.get("blocking", False)),
            details=dict(payload.get("details") or {}),
        )


@dataclass(frozen=True, slots=True)
class StorePrivacyDeclaration:
    platform: str
    store: StoreKind
    data_category_id: str
    collected: DeclarationValue
    shared: DeclarationValue = DeclarationValue.UNKNOWN
    linked_to_user: DeclarationValue = DeclarationValue.UNKNOWN
    tracking: DeclarationValue = DeclarationValue.UNKNOWN
    optional_collection: DeclarationValue = DeclarationValue.UNKNOWN
    purposes: tuple[str, ...] = ()
    source: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "platform", _stable_platform(self.platform))
        object.__setattr__(
            self,
            "data_category_id",
            _stable_id(self.data_category_id, field_name="store declaration data category id"),
        )
        purposes = tuple(sorted({item.strip() for item in self.purposes if item.strip()}))
        object.__setattr__(self, "purposes", purposes)
        if not self.source.strip():
            raise ValueError("store privacy declaration requires provenance source")
        if self.store is StoreKind.APPLE_APP_STORE and self.platform not in _APPLE_PLATFORMS:
            raise ValueError("Apple privacy declaration uses an unsupported platform")
        if self.store is StoreKind.GOOGLE_PLAY and self.platform not in _GOOGLE_PLAY_PLATFORMS:
            raise ValueError("Google Play privacy declaration must target android")
        if self.collected is DeclarationValue.YES and not purposes:
            raise ValueError("collected store declaration requires purposes")
        if self.collected in {DeclarationValue.NO, DeclarationValue.NOT_APPLICABLE}:
            if purposes:
                raise ValueError("non-collected store declaration cannot carry purposes")
            for value in (self.shared, self.linked_to_user, self.tracking):
                if value is DeclarationValue.YES:
                    raise ValueError("non-collected store declaration cannot claim shared/linked/tracking yes")
        object.__setattr__(self, "details", dict(redact_privacy_evidence(self.details)))

    @property
    def id(self) -> str:
        return f"{self.store.value}:{self.platform}:{self.data_category_id}"

    @property
    def ready(self) -> bool:
        if self.collected in {DeclarationValue.UNKNOWN, DeclarationValue.NOT_APPLICABLE}:
            return self.collected is DeclarationValue.NOT_APPLICABLE
        if self.collected is DeclarationValue.NO:
            return True
        if self.store is StoreKind.APPLE_APP_STORE:
            return (
                self.linked_to_user in {DeclarationValue.YES, DeclarationValue.NO}
                and self.tracking in {DeclarationValue.YES, DeclarationValue.NO}
                and bool(self.purposes)
            )
        if self.store is StoreKind.GOOGLE_PLAY:
            return (
                self.shared in {DeclarationValue.YES, DeclarationValue.NO}
                and self.optional_collection in {DeclarationValue.YES, DeclarationValue.NO}
                and bool(self.purposes)
            )
        return bool(self.purposes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "store": self.store.value,
            "data_category_id": self.data_category_id,
            "collected": self.collected.value,
            "shared": self.shared.value,
            "linked_to_user": self.linked_to_user.value,
            "tracking": self.tracking.value,
            "optional_collection": self.optional_collection.value,
            "purposes": list(self.purposes),
            "source": self.source,
            "ready": self.ready,
            "details": redact_privacy_evidence(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "StorePrivacyDeclaration":
        declaration = cls(
            platform=str(payload["platform"]),
            store=StoreKind(str(payload["store"])),
            data_category_id=str(payload["data_category_id"]),
            collected=DeclarationValue(str(payload["collected"])),
            shared=DeclarationValue(str(payload.get("shared", "unknown"))),
            linked_to_user=DeclarationValue(str(payload.get("linked_to_user", "unknown"))),
            tracking=DeclarationValue(str(payload.get("tracking", "unknown"))),
            optional_collection=DeclarationValue(str(payload.get("optional_collection", "unknown"))),
            purposes=tuple(str(item) for item in payload.get("purposes", [])),
            source=str(payload.get("source", "")),
            details=dict(payload.get("details") or {}),
        )
        if "ready" in payload and bool(payload["ready"]) is not declaration.ready:
            raise ValueError("serialized store declaration readiness does not match evidence")
        return declaration


@dataclass(frozen=True, slots=True)
class PrivacyReport:
    generated_at: str
    project_name: str
    target_platforms: tuple[str, ...]
    inventory: tuple[PrivacyDataItem, ...]
    issues: tuple[PrivacyIssue, ...]
    declarations: tuple[StorePrivacyDeclaration, ...]
    status: PrivacyReportStatus
    evidence_sha256: str
    schema_version: int = _SCHEMA_VERSION

    @property
    def counts(self) -> dict[str, int]:
        return {
            "inventory_total": len(self.inventory),
            "collected": sum(item.disposition is PrivacyDisposition.COLLECTED for item in self.inventory),
            "none": sum(item.disposition is PrivacyDisposition.NONE for item in self.inventory),
            "not_applicable": sum(
                item.disposition is PrivacyDisposition.NOT_APPLICABLE for item in self.inventory
            ),
            "basis_unspecified": sum(
                item.disposition is PrivacyDisposition.COLLECTED
                and item.basis_state is PrivacyBasisState.UNSPECIFIED
                for item in self.inventory
            ),
            "sensitivity_unknown": sum(
                item.disposition is PrivacyDisposition.COLLECTED
                and item.sensitivity is PrivacySensitivity.UNKNOWN
                for item in self.inventory
            ),
            "issues_total": len(self.issues),
            "issues_pass": sum(item.status is PrivacyCheckStatus.PASS for item in self.issues),
            "issues_warn": sum(item.status is PrivacyCheckStatus.WARN for item in self.issues),
            "issues_fail": sum(item.status is PrivacyCheckStatus.FAIL for item in self.issues),
            "issues_unknown": sum(item.status is PrivacyCheckStatus.UNKNOWN for item in self.issues),
            "declarations_total": len(self.declarations),
            "declarations_ready": sum(item.ready for item in self.declarations),
            "declarations_pending": sum(not item.ready for item in self.declarations),
        }

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple(f"issue:{item.id}" for item in self.issues if item.blocking)

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "project_name": self.project_name,
            "target_platforms": list(self.target_platforms),
            "status": self.status.value,
            "counts": self.counts,
            "blockers": list(self.blockers),
            "inventory": [item.to_dict() for item in self.inventory],
            "issues": [item.to_dict() for item in self.issues],
            "declarations": [item.to_dict() for item in self.declarations],
        }

    def validate(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported privacy report schema version")
        _parse_timestamp(self.generated_at, field_name="generated_at")
        platforms = tuple(sorted({_stable_platform(item) for item in self.target_platforms}))
        if not platforms or platforms != self.target_platforms:
            raise ValueError("target_platforms must be unique, sorted and non-empty")
        inventory_ids = [item.id for item in self.inventory]
        issue_ids = [item.id for item in self.issues]
        declaration_ids = [item.id for item in self.declarations]
        if len(inventory_ids) != len(set(inventory_ids)):
            raise ValueError("privacy inventory ids must be unique")
        if len(issue_ids) != len(set(issue_ids)):
            raise ValueError("privacy issue ids must be unique")
        if len(declaration_ids) != len(set(declaration_ids)):
            raise ValueError("privacy declaration identities must be unique")
        platform_set = set(platforms)
        inventory_map = {item.id: item for item in self.inventory}
        for item in self.inventory:
            if not set(item.platform_scope) <= platform_set:
                raise ValueError(f"privacy data item targets platform outside report: {item.id}")
        for declaration in self.declarations:
            if declaration.platform not in platform_set:
                raise ValueError("store declaration targets platform outside report")
            item = inventory_map.get(declaration.data_category_id)
            if item is None:
                raise ValueError("store declaration references unknown data category")
            if declaration.platform not in item.platform_scope:
                raise ValueError("store declaration platform is outside data-category scope")
            expected_collection = {
                PrivacyDisposition.COLLECTED: DeclarationValue.YES,
                PrivacyDisposition.NONE: DeclarationValue.NO,
                PrivacyDisposition.NOT_APPLICABLE: DeclarationValue.NOT_APPLICABLE,
            }[item.disposition]
            if declaration.collected is not expected_collection:
                raise ValueError("store declaration collection state contradicts inventory")
        expected_status = KodePrivacy.status_for(self.inventory, self.issues, self.declarations)
        if self.status is not expected_status:
            raise ValueError("privacy report status does not match evidence")
        if self.evidence_sha256 != _sha256(self._payload()):
            raise ValueError("privacy report evidence hash mismatch")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = self._payload()
        payload["evidence_sha256"] = self.evidence_sha256
        return payload

    @classmethod
    def build(
        cls,
        project_name: str,
        target_platforms: Iterable[str],
        inventory: Iterable[PrivacyDataItem],
        issues: Iterable[PrivacyIssue] = (),
        declarations: Iterable[StorePrivacyDeclaration] = (),
        *,
        generated_at: str | None = None,
    ) -> "PrivacyReport":
        platforms = tuple(sorted({_stable_platform(item) for item in target_platforms}))
        inventory_tuple = tuple(inventory)
        issue_tuple = tuple(issues)
        declaration_tuple = tuple(declarations)
        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        status = KodePrivacy.status_for(inventory_tuple, issue_tuple, declaration_tuple)
        provisional = cls(
            timestamp,
            project_name,
            platforms,
            inventory_tuple,
            issue_tuple,
            declaration_tuple,
            status,
            "",
        )
        digest = _sha256(provisional._payload())
        report = cls(
            timestamp,
            project_name,
            platforms,
            inventory_tuple,
            issue_tuple,
            declaration_tuple,
            status,
            digest,
        )
        report.validate()
        return report

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PrivacyReport":
        if int(payload.get("schema_version", 0)) != _SCHEMA_VERSION:
            raise ValueError("unsupported privacy report schema version")
        report = cls(
            generated_at=str(payload["generated_at"]),
            project_name=str(payload.get("project_name", "")),
            target_platforms=tuple(str(item) for item in payload.get("target_platforms", [])),
            inventory=tuple(PrivacyDataItem.from_dict(item) for item in payload.get("inventory", [])),
            issues=tuple(PrivacyIssue.from_dict(item) for item in payload.get("issues", [])),
            declarations=tuple(
                StorePrivacyDeclaration.from_dict(item)
                for item in payload.get("declarations", [])
            ),
            status=PrivacyReportStatus(str(payload["status"])),
            evidence_sha256=str(payload["evidence_sha256"]),
        )
        if dict(payload.get("counts") or {}) != report.counts:
            raise ValueError("serialized privacy counts do not match evidence")
        if tuple(payload.get("blockers") or ()) != report.blockers:
            raise ValueError("serialized privacy blockers do not match evidence")
        report.validate()
        return report


class KodePrivacy:
    @staticmethod
    def status_for(
        inventory: Iterable[PrivacyDataItem],
        issues: Iterable[PrivacyIssue],
        declarations: Iterable[StorePrivacyDeclaration],
    ) -> PrivacyReportStatus:
        inventory_values = tuple(inventory)
        issue_values = tuple(issues)
        declaration_values = tuple(declarations)
        if any(item.blocking or item.status is PrivacyCheckStatus.FAIL for item in issue_values):
            return PrivacyReportStatus.FAIL
        if not inventory_values:
            return PrivacyReportStatus.UNKNOWN
        collected = [item for item in inventory_values if item.disposition is PrivacyDisposition.COLLECTED]
        if (
            any(item.status in {PrivacyCheckStatus.WARN, PrivacyCheckStatus.UNKNOWN} for item in issue_values)
            or any(item.basis_state is PrivacyBasisState.UNSPECIFIED for item in collected)
            or any(item.sensitivity is PrivacySensitivity.UNKNOWN for item in collected)
            or any(not item.ready for item in declaration_values)
        ):
            return PrivacyReportStatus.WARN
        return PrivacyReportStatus.PASS

    @staticmethod
    def score_for(report: PrivacyReport) -> float | None:
        report.validate()
        if not report.inventory and not report.issues and not report.declarations:
            return None
        values: list[float] = []
        for item in report.inventory:
            if item.disposition is not PrivacyDisposition.COLLECTED:
                values.append(100.0)
                continue
            score = 100.0
            if item.basis_state is PrivacyBasisState.UNSPECIFIED:
                score -= 25.0
            if item.sensitivity is PrivacySensitivity.UNKNOWN:
                score -= 15.0
            values.append(max(0.0, score))
        issue_scores = {
            PrivacyCheckStatus.PASS: 100.0,
            PrivacyCheckStatus.WARN: 70.0,
            PrivacyCheckStatus.UNKNOWN: 40.0,
            PrivacyCheckStatus.FAIL: 0.0,
            PrivacyCheckStatus.NOT_APPLICABLE: 100.0,
        }
        values.extend(issue_scores[item.status] for item in report.issues)
        values.extend(100.0 if item.ready else 60.0 for item in report.declarations)
        if not values:
            return None
        return round(sum(values) / len(values), 2)

    @staticmethod
    def to_health_metric(report: PrivacyReport) -> HealthMetric:
        report.validate()
        if report.status is PrivacyReportStatus.UNKNOWN:
            return HealthMetric(
                dimension=HealthDimension.PRIVACY,
                status=HealthStatus.UNKNOWN,
                summary="Privacy inventory evidence is not yet sufficient for a measured result",
                source="KodePrivacy",
                details={
                    "counts": report.counts,
                    "blockers": list(report.blockers),
                    "evidence_sha256": report.evidence_sha256,
                },
            )
        status_map = {
            PrivacyReportStatus.PASS: HealthStatus.PASS,
            PrivacyReportStatus.WARN: HealthStatus.WARN,
            PrivacyReportStatus.FAIL: HealthStatus.FAIL,
        }
        score = KodePrivacy.score_for(report)
        if score is None:
            raise ValueError("measured privacy report requires a score")
        return HealthMetric(
            dimension=HealthDimension.PRIVACY,
            status=status_map[report.status],
            score=score,
            summary=(
                f"{report.counts['inventory_total']} data categor(y/ies), "
                f"{report.counts['issues_total']} issue(s), "
                f"{report.counts['declarations_total']} store declaration(s)"
            ),
            source="KodePrivacy",
            blocking=bool(report.blockers),
            details={
                "counts": report.counts,
                "blockers": list(report.blockers),
                "target_platforms": list(report.target_platforms),
                "evidence_sha256": report.evidence_sha256,
            },
        )

    @staticmethod
    def to_test_cases(report: PrivacyReport) -> tuple[TestCaseResult, ...]:
        report.validate()
        cases: list[TestCaseResult] = []
        for item in report.inventory:
            if item.disposition is PrivacyDisposition.COLLECTED:
                complete = (
                    item.basis_state is not PrivacyBasisState.UNSPECIFIED
                    and item.sensitivity is not PrivacySensitivity.UNKNOWN
                )
                status = TestCaseStatus.PASS if complete else TestCaseStatus.SKIP
            else:
                status = TestCaseStatus.SKIP
            cases.append(
                TestCaseResult(
                    id=f"privacy:data:{item.id}",
                    status=status,
                    duration_s=0.0,
                    message=f"Privacy inventory: {item.category}",
                    source="KodePrivacy",
                    details={
                        "disposition": item.disposition.value,
                        "basis_state": item.basis_state.value,
                        "sensitivity": item.sensitivity.value,
                        "platform_scope": list(item.platform_scope),
                    },
                )
            )
        issue_status = {
            PrivacyCheckStatus.PASS: TestCaseStatus.PASS,
            PrivacyCheckStatus.FAIL: TestCaseStatus.FAIL,
            PrivacyCheckStatus.WARN: TestCaseStatus.SKIP,
            PrivacyCheckStatus.UNKNOWN: TestCaseStatus.SKIP,
            PrivacyCheckStatus.NOT_APPLICABLE: TestCaseStatus.SKIP,
        }
        for item in report.issues:
            cases.append(
                TestCaseResult(
                    id=f"privacy:issue:{item.id}",
                    status=issue_status[item.status],
                    duration_s=0.0,
                    message=item.title,
                    source="KodePrivacy",
                    details={
                        "applicability": item.applicability.value,
                        "severity": item.severity.value,
                        "blocking": item.blocking,
                    },
                )
            )
        for item in report.declarations:
            cases.append(
                TestCaseResult(
                    id=f"privacy:store:{item.id}",
                    status=TestCaseStatus.PASS if item.ready else TestCaseStatus.SKIP,
                    duration_s=0.0,
                    message=f"Store privacy declaration: {item.id}",
                    source="KodePrivacy",
                    details={"ready": item.ready, "collected": item.collected.value},
                )
            )
        return tuple(cases)


class PrivacyStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve(strict=False)
        self.boundary = WorkspaceBoundary(self.project_root)
        self.metadata_root = self.boundary.resolve(".kodepoia", must_exist=False)
        self.privacy_root = self.boundary.resolve(".kodepoia/diagnostics/privacy", must_exist=False)

    @staticmethod
    def _safe_project(name: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip(".-")
        return safe or "project"

    def save(self, report: PrivacyReport) -> tuple[Path, Path]:
        report.validate()
        if not self.metadata_root.is_dir():
            raise FileNotFoundError("project .kodepoia metadata directory is not initialized")
        self.privacy_root.mkdir(parents=True, exist_ok=True)
        name = self._safe_project(report.project_name)
        latest = self.boundary.resolve(f".kodepoia/diagnostics/privacy/{name}-latest.json")
        stamp = report.generated_at.replace(":", "").replace("-", "").replace(".", "")
        snapshot = self.boundary.resolve(
            f".kodepoia/diagnostics/privacy/privacy-{name}-{stamp}.json"
        )
        payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        for destination in (latest, snapshot):
            temporary = destination.with_name(f".{destination.name}.tmp")
            temporary.write_text(payload, encoding="utf-8")
            temporary.replace(destination)
        return latest, snapshot

    def load_latest(self, project_name: str) -> PrivacyReport:
        path = self.boundary.resolve(
            f".kodepoia/diagnostics/privacy/{self._safe_project(project_name)}-latest.json",
            must_exist=True,
        )
        return PrivacyReport.from_dict(json.loads(path.read_text(encoding="utf-8")))
