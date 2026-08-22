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
from kodepoia.quality.tests import TestCaseResult, TestCaseStatus


_SCHEMA_VERSION = 1
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


class CICheckStatus(StrEnum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    PASS = "pass"
    FAIL = "fail"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"


class CIReportStatus(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CICheck:
    id: str
    status: CICheckStatus
    required: bool = True
    source: str = ""
    message: str = ""
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        check_id = self.id.strip()
        if not check_id:
            raise ValueError("CI check id must be non-empty")
        object.__setattr__(self, "id", check_id)
        object.__setattr__(self, "details", dict(self.details))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status.value,
            "required": self.required,
            "source": self.source,
            "message": self.message,
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CICheck":
        return cls(
            id=str(payload["id"]),
            status=CICheckStatus(str(payload["status"])),
            required=bool(payload.get("required", True)),
            source=str(payload.get("source", "")),
            message=str(payload.get("message", "")),
            details=dict(payload.get("details") or {}),
        )


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash_payload(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _aggregate(checks: tuple[CICheck, ...]) -> CIReportStatus:
    if not checks:
        return CIReportStatus.UNKNOWN
    required = tuple(check for check in checks if check.required)
    optional = tuple(check for check in checks if not check.required)
    hard_failure = {CICheckStatus.FAIL, CICheckStatus.CANCELLED, CICheckStatus.SKIPPED}
    incomplete = {CICheckStatus.QUEUED, CICheckStatus.IN_PROGRESS, CICheckStatus.UNKNOWN}
    if any(check.status in hard_failure for check in required):
        return CIReportStatus.FAIL
    if any(check.status in incomplete for check in required):
        return CIReportStatus.UNKNOWN
    if required and not all(check.status is CICheckStatus.PASS for check in required):
        return CIReportStatus.FAIL
    if any(check.status is not CICheckStatus.PASS for check in optional):
        return CIReportStatus.WARN
    return CIReportStatus.PASS


@dataclass(frozen=True, slots=True)
class CIReport:
    generated_at: str
    workflow_id: str
    source_sha: str
    checks: tuple[CICheck, ...]
    status: CIReportStatus
    evidence_sha256: str
    schema_version: int = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported CI report schema version")
        generated = datetime.fromisoformat(self.generated_at.replace("Z", "+00:00"))
        if generated.tzinfo is None:
            raise ValueError("CI report timestamp must include timezone")
        if not self.workflow_id.strip():
            raise ValueError("workflow_id must be non-empty")
        if not _SHA_RE.fullmatch(self.source_sha):
            raise ValueError("source_sha must be a 40-character Git SHA")
        ids = [check.id for check in self.checks]
        if len(ids) != len(set(ids)):
            raise ValueError("CI check ids must be unique")
        expected = _aggregate(self.checks)
        if self.status is not expected:
            raise ValueError("CI report status does not match check evidence")

    @property
    def counts(self) -> dict[str, int]:
        counts = {status.value: 0 for status in CICheckStatus}
        for check in self.checks:
            counts[check.status.value] += 1
        counts["total"] = len(self.checks)
        counts["required"] = sum(check.required for check in self.checks)
        return counts

    @property
    def blocking_checks(self) -> tuple[str, ...]:
        return tuple(
            check.id
            for check in self.checks
            if check.required and check.status is not CICheckStatus.PASS
        )

    def _evidence_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "workflow_id": self.workflow_id,
            "source_sha": self.source_sha.lower(),
            "status": self.status.value,
            "checks": [check.to_dict() for check in self.checks],
            "counts": self.counts,
            "blocking_checks": list(self.blocking_checks),
        }

    def validate(self) -> None:
        self.__post_init__()
        expected = _hash_payload(self._evidence_payload())
        if self.evidence_sha256 != expected:
            raise ValueError("CI report evidence hash mismatch")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = self._evidence_payload()
        payload["evidence_sha256"] = self.evidence_sha256
        return payload

    @classmethod
    def build(
        cls,
        *,
        workflow_id: str,
        source_sha: str,
        checks: Iterable[CICheck],
        generated_at: str | None = None,
    ) -> "CIReport":
        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        normalized = tuple(checks)
        status = _aggregate(normalized)
        provisional = cls(timestamp, workflow_id, source_sha.lower(), normalized, status, "")
        digest = _hash_payload(provisional._evidence_payload())
        report = cls(timestamp, workflow_id, source_sha.lower(), normalized, status, digest)
        report.validate()
        return report

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CIReport":
        report = cls(
            generated_at=str(payload["generated_at"]),
            workflow_id=str(payload["workflow_id"]),
            source_sha=str(payload["source_sha"]),
            checks=tuple(CICheck.from_dict(item) for item in payload["checks"]),
            status=CIReportStatus(str(payload["status"])),
            evidence_sha256=str(payload["evidence_sha256"]),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if dict(payload.get("counts") or {}) != report.counts:
            raise ValueError("serialized CI counts do not match check evidence")
        if tuple(payload.get("blocking_checks") or ()) != report.blocking_checks:
            raise ValueError("serialized CI blockers do not match check evidence")
        report.validate()
        return report

    @classmethod
    def load(cls, path: Path) -> "CIReport":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("CI report must be a JSON object")
        return cls.from_dict(payload)


class KodeCI:
    @staticmethod
    def evaluate(
        checks: Iterable[CICheck],
        *,
        workflow_id: str,
        source_sha: str,
        generated_at: str | None = None,
    ) -> CIReport:
        return CIReport.build(
            workflow_id=workflow_id,
            source_sha=source_sha,
            checks=checks,
            generated_at=generated_at,
        )

    @staticmethod
    def to_test_cases(report: CIReport) -> tuple[TestCaseResult, ...]:
        cases: list[TestCaseResult] = []
        for check in report.checks:
            if check.status is CICheckStatus.PASS:
                status = TestCaseStatus.PASS
            elif check.required:
                status = (
                    TestCaseStatus.FAIL
                    if check.status in {CICheckStatus.FAIL, CICheckStatus.CANCELLED, CICheckStatus.SKIPPED}
                    else TestCaseStatus.ERROR
                )
            else:
                status = TestCaseStatus.SKIP
            cases.append(
                TestCaseResult(
                    id=f"ci:{report.workflow_id}:{check.id}",
                    status=status,
                    duration_s=0.0,
                    message=check.message or check.status.value,
                    source=check.source or "KodeCI",
                    details={"required": check.required, "ci_status": check.status.value},
                )
            )
        return tuple(cases)


@dataclass(frozen=True, slots=True)
class CIStore:
    project_root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_root", self.project_root.resolve(strict=False))

    @property
    def boundary(self) -> WorkspaceBoundary:
        return WorkspaceBoundary(self.project_root)

    @property
    def metadata_root(self) -> Path:
        return self.boundary.resolve(".kodepoia", must_exist=True)

    @staticmethod
    def _safe(value: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip(".-")
        if not safe:
            raise ValueError("workflow id does not produce a safe path")
        return safe

    @property
    def workflows_root(self) -> Path:
        return self.boundary.resolve(".kodepoia/workflows")

    @staticmethod
    def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def save(self, report: CIReport, *, snapshot: bool = True) -> tuple[Path, Path | None]:
        if not self.metadata_root.is_dir():
            raise FileNotFoundError(f"Kodepoia project metadata not found: {self.metadata_root}")
        root = self.boundary.resolve(f".kodepoia/workflows/{self._safe(report.workflow_id)}")
        root.mkdir(parents=True, exist_ok=True)
        payload = report.to_dict()
        latest = root / "latest.json"
        self._write_json(latest, payload)
        snapshot_path: Path | None = None
        if snapshot:
            parsed = datetime.fromisoformat(report.generated_at.replace("Z", "+00:00")).astimezone(UTC)
            snapshot_path = root / f"ci-{parsed.strftime('%Y%m%dT%H%M%S%fZ')}.json"
            self._write_json(snapshot_path, payload)
        return latest, snapshot_path

    def load_latest(self, workflow_id: str) -> CIReport:
        root = self.boundary.resolve(f".kodepoia/workflows/{self._safe(workflow_id)}")
        return CIReport.load(root / "latest.json")
