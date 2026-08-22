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
from kodepoia.quality.health import HealthDimension, HealthMetric, HealthStatus
from kodepoia.quality.tests import TestCaseResult, TestCaseStatus


_SCHEMA_VERSION = 1


class DebtCategory(StrEnum):
    ARCHITECTURE = "architecture"
    CODE_QUALITY = "code_quality"
    TESTS = "tests"
    BUILD = "build"
    DEPENDENCIES = "dependencies"
    PERFORMANCE = "performance"
    ACCESSIBILITY = "accessibility"
    LOCALIZATION = "localization"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class DebtSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def weight(self) -> int:
        return {
            DebtSeverity.LOW: 1,
            DebtSeverity.MEDIUM: 2,
            DebtSeverity.HIGH: 3,
            DebtSeverity.CRITICAL: 4,
        }[self]


class DebtState(StrEnum):
    OPEN = "open"
    ACCEPTED = "accepted"
    RESOLVED = "resolved"


class DebtReferenceKind(StrEnum):
    FILE = "file"
    SYMBOL = "symbol"
    TEST = "test"
    REQUIREMENT = "requirement"
    ISSUE = "issue"
    OTHER = "other"


class TechnicalDebtStatus(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class DebtReference:
    kind: DebtReferenceKind
    value: str

    def __post_init__(self) -> None:
        value = self.value.strip()
        if not value:
            raise ValueError("debt reference value must be non-empty")
        object.__setattr__(self, "value", value)

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind.value, "value": self.value}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DebtReference":
        return cls(DebtReferenceKind(str(payload["kind"])), str(payload["value"]))


def _parse_timestamp(value: str, *, field_name: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return parsed


def _normalized_identity(text: str) -> str:
    return " ".join(text.casefold().split())


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class TechnicalDebtItem:
    id: str
    category: DebtCategory
    severity: DebtSeverity
    summary: str
    scope: str
    source: str
    provenance: str
    impact: int
    probability: int
    effort: int
    first_seen: str
    last_seen: str
    state: DebtState = DebtState.OPEN
    owner: str = ""
    references: tuple[DebtReference, ...] = ()
    blocking: bool = False
    accepted_rationale: str = ""
    review_at: str | None = None
    expires_at: str | None = None
    resolved_at: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        item_id = self.id.strip()
        summary = self.summary.strip()
        scope = self.scope.strip()
        source = self.source.strip()
        provenance = self.provenance.strip()
        if not item_id or not summary or not scope or not source or not provenance:
            raise ValueError("debt id, summary, scope, source and provenance must be non-empty")
        for name, value in (("impact", self.impact), ("probability", self.probability), ("effort", self.effort)):
            if not 1 <= int(value) <= 5:
                raise ValueError(f"{name} must be between 1 and 5")
        first = _parse_timestamp(self.first_seen, field_name="first_seen")
        last = _parse_timestamp(self.last_seen, field_name="last_seen")
        if last < first:
            raise ValueError("last_seen cannot precede first_seen")
        refs = [(reference.kind, reference.value) for reference in self.references]
        if len(refs) != len(set(refs)):
            raise ValueError("debt references must be unique")
        for timestamp_name, timestamp_value in (
            ("review_at", self.review_at),
            ("expires_at", self.expires_at),
            ("resolved_at", self.resolved_at),
        ):
            if timestamp_value:
                _parse_timestamp(timestamp_value, field_name=timestamp_name)
        if self.state is DebtState.ACCEPTED:
            if not self.accepted_rationale.strip():
                raise ValueError("accepted debt requires accepted_rationale")
            if self.blocking:
                raise ValueError("accepted debt cannot remain blocking")
            if self.resolved_at is not None:
                raise ValueError("accepted debt cannot have resolved_at")
        elif self.state is DebtState.RESOLVED:
            if self.resolved_at is None:
                raise ValueError("resolved debt requires resolved_at")
            if _parse_timestamp(self.resolved_at, field_name="resolved_at") < first:
                raise ValueError("resolved_at cannot precede first_seen")
            if self.blocking:
                raise ValueError("resolved debt cannot remain blocking")
            if self.accepted_rationale.strip():
                raise ValueError("resolved debt must not use accepted_rationale")
        else:
            if self.resolved_at is not None:
                raise ValueError("open debt cannot have resolved_at")
            if self.accepted_rationale.strip():
                raise ValueError("open debt must not use accepted_rationale")
        object.__setattr__(self, "id", item_id)
        object.__setattr__(self, "summary", summary)
        object.__setattr__(self, "scope", scope)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "provenance", provenance)
        object.__setattr__(self, "owner", self.owner.strip())
        object.__setattr__(self, "accepted_rationale", self.accepted_rationale.strip())
        object.__setattr__(self, "details", dict(self.details))

    @property
    def priority_score(self) -> float:
        # Max = 4 * 5 * 5 / 1 = 100. Lower effort raises actionable priority.
        return round(self.severity.weight * self.impact * self.probability / self.effort, 4)

    @property
    def fingerprint(self) -> str:
        identity = {
            "category": self.category.value,
            "summary": _normalized_identity(self.summary),
            "scope": _normalized_identity(self.scope),
            "references": sorted(
                (reference.kind.value, _normalized_identity(reference.value))
                for reference in self.references
            ),
        }
        return hashlib.sha256(_canonical_json(identity).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category.value,
            "severity": self.severity.value,
            "summary": self.summary,
            "scope": self.scope,
            "source": self.source,
            "provenance": self.provenance,
            "owner": self.owner,
            "impact": self.impact,
            "probability": self.probability,
            "effort": self.effort,
            "priority_score": self.priority_score,
            "fingerprint": self.fingerprint,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "state": self.state.value,
            "blocking": self.blocking,
            "accepted_rationale": self.accepted_rationale,
            "review_at": self.review_at,
            "expires_at": self.expires_at,
            "resolved_at": self.resolved_at,
            "references": [reference.to_dict() for reference in self.references],
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TechnicalDebtItem":
        item = cls(
            id=str(payload["id"]),
            category=DebtCategory(str(payload["category"])),
            severity=DebtSeverity(str(payload["severity"])),
            summary=str(payload["summary"]),
            scope=str(payload["scope"]),
            source=str(payload["source"]),
            provenance=str(payload["provenance"]),
            owner=str(payload.get("owner", "")),
            impact=int(payload["impact"]),
            probability=int(payload["probability"]),
            effort=int(payload["effort"]),
            first_seen=str(payload["first_seen"]),
            last_seen=str(payload["last_seen"]),
            state=DebtState(str(payload["state"])),
            blocking=bool(payload.get("blocking", False)),
            accepted_rationale=str(payload.get("accepted_rationale", "")),
            review_at=(str(payload["review_at"]) if payload.get("review_at") else None),
            expires_at=(str(payload["expires_at"]) if payload.get("expires_at") else None),
            resolved_at=(str(payload["resolved_at"]) if payload.get("resolved_at") else None),
            references=tuple(DebtReference.from_dict(item) for item in payload.get("references", [])),
            details=dict(payload.get("details") or {}),
        )
        if float(payload.get("priority_score", -1)) != item.priority_score:
            raise ValueError("serialized priority_score does not match debt evidence")
        if str(payload.get("fingerprint", "")) != item.fingerprint:
            raise ValueError("serialized fingerprint does not match debt identity")
        return item


@dataclass(frozen=True, slots=True)
class TechnicalDebtReport:
    generated_at: str
    project_name: str
    items: tuple[TechnicalDebtItem, ...]
    status: TechnicalDebtStatus
    evidence_sha256: str
    schema_version: int = _SCHEMA_VERSION

    @property
    def counts(self) -> dict[str, int]:
        return {
            "total": len(self.items),
            "open": sum(item.state is DebtState.OPEN for item in self.items),
            "accepted": sum(item.state is DebtState.ACCEPTED for item in self.items),
            "resolved": sum(item.state is DebtState.RESOLVED for item in self.items),
            "blocking": sum(item.blocking for item in self.items),
        }

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple(item.id for item in self.items if item.blocking)

    @property
    def ranked_active_ids(self) -> tuple[str, ...]:
        active = [item for item in self.items if item.state is not DebtState.RESOLVED]
        return tuple(
            item.id
            for item in sorted(active, key=lambda item: (-item.priority_score, item.id))
        )

    @property
    def debt_penalty(self) -> float:
        open_penalty = sum(item.priority_score for item in self.items if item.state is DebtState.OPEN)
        accepted_penalty = sum(
            item.priority_score * 0.25 for item in self.items if item.state is DebtState.ACCEPTED
        )
        return round(min(100.0, open_penalty + accepted_penalty), 4)

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "project_name": self.project_name,
            "status": self.status.value,
            "counts": self.counts,
            "blockers": list(self.blockers),
            "ranked_active_ids": list(self.ranked_active_ids),
            "debt_penalty": self.debt_penalty,
            "items": [item.to_dict() for item in self.items],
        }

    def validate(self) -> None:
        _parse_timestamp(self.generated_at, field_name="generated_at")
        ids = [item.id for item in self.items]
        fingerprints = [item.fingerprint for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("technical debt ids must be unique")
        if len(fingerprints) != len(set(fingerprints)):
            raise ValueError("technical debt fingerprints must be unique")
        expected_status = KodeTechnicalDebt.status_for(self.items)
        if self.status is not expected_status:
            raise ValueError("technical debt report status does not match evidence")
        if self.evidence_sha256 != _sha256(self._payload()):
            raise ValueError("technical debt report evidence hash mismatch")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = self._payload()
        payload["evidence_sha256"] = self.evidence_sha256
        return payload

    @classmethod
    def build(
        cls,
        project_name: str,
        items: Iterable[TechnicalDebtItem],
        *,
        generated_at: str | None = None,
    ) -> "TechnicalDebtReport":
        item_tuple = tuple(items)
        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        status = KodeTechnicalDebt.status_for(item_tuple)
        provisional = cls(timestamp, project_name, item_tuple, status, "")
        digest = _sha256(provisional._payload())
        report = cls(timestamp, project_name, item_tuple, status, digest)
        report.validate()
        return report

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TechnicalDebtReport":
        if int(payload.get("schema_version", 0)) != _SCHEMA_VERSION:
            raise ValueError("unsupported technical debt report schema version")
        report = cls(
            generated_at=str(payload["generated_at"]),
            project_name=str(payload.get("project_name", "")),
            items=tuple(TechnicalDebtItem.from_dict(item) for item in payload.get("items", [])),
            status=TechnicalDebtStatus(str(payload["status"])),
            evidence_sha256=str(payload["evidence_sha256"]),
        )
        if dict(payload.get("counts") or {}) != report.counts:
            raise ValueError("serialized technical debt counts do not match items")
        if tuple(payload.get("blockers") or ()) != report.blockers:
            raise ValueError("serialized technical debt blockers do not match items")
        if tuple(payload.get("ranked_active_ids") or ()) != report.ranked_active_ids:
            raise ValueError("serialized debt ranking does not match items")
        if float(payload.get("debt_penalty", -1)) != report.debt_penalty:
            raise ValueError("serialized debt penalty does not match items")
        report.validate()
        return report


class KodeTechnicalDebt:
    @staticmethod
    def status_for(items: Iterable[TechnicalDebtItem]) -> TechnicalDebtStatus:
        values = tuple(items)
        if any(item.blocking for item in values):
            return TechnicalDebtStatus.FAIL
        if any(item.state is not DebtState.RESOLVED for item in values):
            return TechnicalDebtStatus.WARN
        return TechnicalDebtStatus.PASS

    @staticmethod
    def to_health_metric(report: TechnicalDebtReport) -> HealthMetric:
        report.validate()
        status_map = {
            TechnicalDebtStatus.PASS: HealthStatus.PASS,
            TechnicalDebtStatus.WARN: HealthStatus.WARN,
            TechnicalDebtStatus.FAIL: HealthStatus.FAIL,
        }
        return HealthMetric(
            dimension=HealthDimension.TECHNICAL_DEBT,
            status=status_map[report.status],
            score=round(100.0 - report.debt_penalty, 4),
            summary=(
                f"{report.counts['open']} open, {report.counts['accepted']} accepted, "
                f"{report.counts['resolved']} resolved technical-debt item(s)"
            ),
            source="KodeTechnicalDebt",
            blocking=bool(report.blockers),
            details={
                "counts": report.counts,
                "blockers": list(report.blockers),
                "ranked_active_ids": list(report.ranked_active_ids),
                "evidence_sha256": report.evidence_sha256,
            },
        )

    @staticmethod
    def to_test_cases(report: TechnicalDebtReport) -> tuple[TestCaseResult, ...]:
        report.validate()
        cases: list[TestCaseResult] = []
        for item in report.items:
            if item.state is DebtState.RESOLVED:
                status = TestCaseStatus.PASS
            elif item.blocking:
                status = TestCaseStatus.FAIL
            else:
                status = TestCaseStatus.SKIP
            cases.append(
                TestCaseResult(
                    id=f"technical-debt:{item.id}",
                    status=status,
                    duration_s=0.0,
                    message=item.summary,
                    source="KodeTechnicalDebt",
                    details={
                        "state": item.state.value,
                        "severity": item.severity.value,
                        "priority_score": item.priority_score,
                        "fingerprint": item.fingerprint,
                        "blocking": item.blocking,
                    },
                )
            )
        return tuple(cases)


class TechnicalDebtStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve(strict=False)
        self.boundary = WorkspaceBoundary(self.project_root)
        self.metadata_root = self.boundary.resolve(".kodepoia", must_exist=False)
        self.debt_root = self.boundary.resolve(".kodepoia/diagnostics/technical_debt", must_exist=False)

    @staticmethod
    def _safe_project(name: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip(".-")
        return safe or "project"

    def save(self, report: TechnicalDebtReport) -> tuple[Path, Path]:
        report.validate()
        if not self.metadata_root.is_dir():
            raise FileNotFoundError("project .kodepoia metadata directory is not initialized")
        self.debt_root.mkdir(parents=True, exist_ok=True)
        name = self._safe_project(report.project_name)
        latest = self.boundary.resolve(f".kodepoia/diagnostics/technical_debt/{name}-latest.json")
        stamp = report.generated_at.replace(":", "").replace("-", "").replace(".", "")
        snapshot = self.boundary.resolve(
            f".kodepoia/diagnostics/technical_debt/technical-debt-{name}-{stamp}.json"
        )
        payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        for destination in (latest, snapshot):
            temporary = destination.with_name(f".{destination.name}.tmp")
            temporary.write_text(payload, encoding="utf-8")
            temporary.replace(destination)
        return latest, snapshot

    def load_latest(self, project_name: str) -> TechnicalDebtReport:
        path = self.boundary.resolve(
            f".kodepoia/diagnostics/technical_debt/{self._safe_project(project_name)}-latest.json",
            must_exist=True,
        )
        return TechnicalDebtReport.from_dict(json.loads(path.read_text(encoding="utf-8")))
