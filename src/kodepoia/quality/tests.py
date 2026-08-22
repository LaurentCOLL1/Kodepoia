from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from kodepoia.kodecode.workspace import WorkspaceBoundary


class TestCaseStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIP = "skip"


class TestRunStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class TestCaseResult:
    id: str
    status: TestCaseStatus
    duration_s: float = 0.0
    message: str = ""
    source: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Test case ID is required")
        if self.duration_s < 0:
            raise ValueError("Test duration cannot be negative")


@dataclass(frozen=True, slots=True)
class TestRunReport:
    schema_version: int
    generated_at: str
    suite: str
    platform: str
    status: TestRunStatus
    results: tuple[TestCaseResult, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("Unsupported test run schema version")
        parsed = datetime.fromisoformat(self.generated_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Test run timestamp must include a timezone")
        if not self.suite.strip():
            raise ValueError("Test suite is required")
        ids = [item.id for item in self.results]
        if len(ids) != len(set(ids)):
            raise ValueError("Test case IDs must be unique")
        if self.status is not self._derive_status():
            raise ValueError("Test run status does not match result evidence")

    def _derive_status(self) -> TestRunStatus:
        if not self.results:
            return TestRunStatus.UNKNOWN
        if any(item.status in {TestCaseStatus.FAIL, TestCaseStatus.ERROR} for item in self.results):
            return TestRunStatus.FAIL
        if any(item.status is TestCaseStatus.SKIP for item in self.results):
            return TestRunStatus.WARN
        return TestRunStatus.PASS

    @property
    def counts(self) -> dict[str, int]:
        return {
            "total": len(self.results),
            "passed": sum(item.status is TestCaseStatus.PASS for item in self.results),
            "failed": sum(item.status is TestCaseStatus.FAIL for item in self.results),
            "errors": sum(item.status is TestCaseStatus.ERROR for item in self.results),
            "skipped": sum(item.status is TestCaseStatus.SKIP for item in self.results),
        }

    @property
    def duration_s(self) -> float:
        return round(sum(item.duration_s for item in self.results), 6)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "suite": self.suite,
            "platform": self.platform,
            "status": self.status.value,
            "counts": self.counts,
            "duration_s": self.duration_s,
            "results": [
                {
                    "id": item.id,
                    "status": item.status.value,
                    "duration_s": item.duration_s,
                    "message": item.message,
                    "source": item.source,
                    "details": item.details,
                }
                for item in self.results
            ],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TestRunReport":
        if int(payload.get("schema_version", 0)) != 1:
            raise ValueError("Unsupported test run schema version")
        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raise ValueError("Test run results must be a list")
        results = tuple(
            TestCaseResult(
                id=str(item["id"]),
                status=TestCaseStatus(item["status"]),
                duration_s=float(item.get("duration_s", 0.0)),
                message=str(item.get("message", "")),
                source=str(item.get("source", "")),
                details=dict(item.get("details", {})),
            )
            for item in raw_results
        )
        report = cls(
            schema_version=1,
            generated_at=str(payload["generated_at"]),
            suite=str(payload["suite"]),
            platform=str(payload.get("platform", "")),
            status=TestRunStatus(payload["status"]),
            results=results,
        )
        if payload.get("counts") != report.counts:
            raise ValueError("Serialized test counts do not match result evidence")
        if abs(float(payload.get("duration_s", 0.0)) - report.duration_s) > 0.000001:
            raise ValueError("Serialized test duration does not match result evidence")
        return report

    @classmethod
    def load(cls, path: Path) -> "TestRunReport":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Test run report must be a JSON object")
        return cls.from_dict(payload)


class KodeTests:
    @staticmethod
    def evaluate(
        results: Iterable[TestCaseResult],
        *,
        suite: str,
        platform: str = "",
        generated_at: str | None = None,
    ) -> TestRunReport:
        normalized = tuple(results)
        if not normalized:
            status = TestRunStatus.UNKNOWN
        elif any(item.status in {TestCaseStatus.FAIL, TestCaseStatus.ERROR} for item in normalized):
            status = TestRunStatus.FAIL
        elif any(item.status is TestCaseStatus.SKIP for item in normalized):
            status = TestRunStatus.WARN
        else:
            status = TestRunStatus.PASS
        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        return TestRunReport(1, timestamp, suite, platform, status, normalized)


@dataclass(frozen=True, slots=True)
class TestRunStore:
    project_root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_root", self.project_root.resolve(strict=False))

    @property
    def boundary(self) -> WorkspaceBoundary:
        return WorkspaceBoundary(self.project_root)

    @property
    def metadata_root(self) -> Path:
        return self.boundary.resolve(".kodepoia", must_exist=True)

    @property
    def runs_root(self) -> Path:
        return self.boundary.resolve(".kodepoia/tests/runs")

    def _require_initialized_project(self) -> None:
        if not self.metadata_root.is_dir():
            raise FileNotFoundError(f"Kodepoia project metadata not found: {self.metadata_root}")

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    @staticmethod
    def _safe_suite_name(suite: str) -> str:
        value = "".join(char if char.isalnum() or char in "-_" else "-" for char in suite)
        return value.strip("-") or "suite"

    def save(self, report: TestRunReport, *, snapshot: bool = True) -> tuple[Path, Path | None]:
        self._require_initialized_project()
        root = self.runs_root
        root.mkdir(parents=True, exist_ok=True)
        payload = report.to_dict()
        latest = root / "latest.json"
        self._write_json(latest, payload)
        snapshot_path: Path | None = None
        if snapshot:
            parsed = datetime.fromisoformat(report.generated_at.replace("Z", "+00:00")).astimezone(UTC)
            snapshot_path = root / (
                f"tests-{self._safe_suite_name(report.suite)}-"
                f"{parsed.strftime('%Y%m%dT%H%M%S%fZ')}.json"
            )
            self._write_json(snapshot_path, payload)
        return latest, snapshot_path

    def load_latest(self) -> TestRunReport:
        self._require_initialized_project()
        return TestRunReport.load(self.runs_root / "latest.json")
