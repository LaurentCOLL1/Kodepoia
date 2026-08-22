from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from kodepoia.kodecode.workspace import WorkspaceBoundary
from kodepoia.quality.tests import TestCaseStatus, TestRunReport


class RegressionChange(StrEnum):
    UNCHANGED = "unchanged"
    REGRESSED = "regressed"
    FIXED = "fixed"
    ADDED = "added"
    REMOVED = "removed"


class RegressionStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class RegressionEntry:
    id: str
    change: RegressionChange
    baseline_status: TestCaseStatus | None
    current_status: TestCaseStatus | None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Regression entry ID is required")

    @property
    def is_regression(self) -> bool:
        if self.change in {RegressionChange.REGRESSED, RegressionChange.REMOVED}:
            return True
        return self.change is RegressionChange.ADDED and self.current_status in {
            TestCaseStatus.FAIL,
            TestCaseStatus.ERROR,
        }


def _classify_status_change(before: TestCaseStatus, after: TestCaseStatus) -> RegressionChange:
    if before is after:
        return RegressionChange.UNCHANGED
    if after is TestCaseStatus.PASS:
        return RegressionChange.FIXED
    if after is TestCaseStatus.SKIP:
        return RegressionChange.REGRESSED
    if before in {TestCaseStatus.PASS, TestCaseStatus.SKIP}:
        return RegressionChange.REGRESSED
    if before is TestCaseStatus.ERROR and after is TestCaseStatus.FAIL:
        return RegressionChange.FIXED
    if before is TestCaseStatus.FAIL and after is TestCaseStatus.ERROR:
        return RegressionChange.REGRESSED
    return RegressionChange.UNCHANGED


@dataclass(frozen=True, slots=True)
class RegressionReport:
    schema_version: int
    generated_at: str
    suite: str
    baseline_generated_at: str
    current_generated_at: str
    status: RegressionStatus
    entries: tuple[RegressionEntry, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("Unsupported regression report schema version")
        for value in (self.generated_at, self.baseline_generated_at, self.current_generated_at):
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError("Regression timestamps must include a timezone")
        if not self.suite.strip():
            raise ValueError("Regression suite is required")
        ids = [item.id for item in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("Regression entry IDs must be unique")
        if self.status is not self._derive_status():
            raise ValueError("Regression status does not match entry evidence")

    def _derive_status(self) -> RegressionStatus:
        if not self.entries:
            return RegressionStatus.UNKNOWN
        if any(item.is_regression for item in self.entries):
            return RegressionStatus.FAIL
        if all(item.change is RegressionChange.ADDED for item in self.entries):
            return RegressionStatus.WARN
        return RegressionStatus.PASS

    @property
    def regressions(self) -> tuple[str, ...]:
        return tuple(item.id for item in self.entries if item.is_regression)

    @property
    def fixed(self) -> tuple[str, ...]:
        return tuple(item.id for item in self.entries if item.change is RegressionChange.FIXED)

    @property
    def added(self) -> tuple[str, ...]:
        return tuple(item.id for item in self.entries if item.change is RegressionChange.ADDED)

    @property
    def removed(self) -> tuple[str, ...]:
        return tuple(item.id for item in self.entries if item.change is RegressionChange.REMOVED)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "suite": self.suite,
            "baseline_generated_at": self.baseline_generated_at,
            "current_generated_at": self.current_generated_at,
            "status": self.status.value,
            "regressions": list(self.regressions),
            "fixed": list(self.fixed),
            "added": list(self.added),
            "removed": list(self.removed),
            "entries": [
                {
                    "id": item.id,
                    "change": item.change.value,
                    "baseline_status": (
                        None if item.baseline_status is None else item.baseline_status.value
                    ),
                    "current_status": (
                        None if item.current_status is None else item.current_status.value
                    ),
                }
                for item in self.entries
            ],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RegressionReport":
        if int(payload.get("schema_version", 0)) != 1:
            raise ValueError("Unsupported regression report schema version")
        raw_entries = payload.get("entries")
        if not isinstance(raw_entries, list):
            raise ValueError("Regression entries must be a list")
        entries = tuple(
            RegressionEntry(
                id=str(item["id"]),
                change=RegressionChange(item["change"]),
                baseline_status=(
                    None
                    if item.get("baseline_status") is None
                    else TestCaseStatus(item["baseline_status"])
                ),
                current_status=(
                    None
                    if item.get("current_status") is None
                    else TestCaseStatus(item["current_status"])
                ),
            )
            for item in raw_entries
        )
        report = cls(
            schema_version=1,
            generated_at=str(payload["generated_at"]),
            suite=str(payload["suite"]),
            baseline_generated_at=str(payload["baseline_generated_at"]),
            current_generated_at=str(payload["current_generated_at"]),
            status=RegressionStatus(payload["status"]),
            entries=entries,
        )
        for key, expected in (
            ("regressions", report.regressions),
            ("fixed", report.fixed),
            ("added", report.added),
            ("removed", report.removed),
        ):
            if tuple(payload.get(key, [])) != expected:
                raise ValueError(f"Serialized regression {key} do not match entry evidence")
        return report

    @classmethod
    def load(cls, path: Path) -> "RegressionReport":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Regression report must be a JSON object")
        return cls.from_dict(payload)


class KodeRegression:
    @staticmethod
    def compare(
        baseline: TestRunReport,
        current: TestRunReport,
        *,
        generated_at: str | None = None,
    ) -> RegressionReport:
        if baseline.suite != current.suite:
            raise ValueError("Regression comparison requires matching test suites")
        baseline_by_id = {item.id: item for item in baseline.results}
        current_by_id = {item.id: item for item in current.results}
        entries: list[RegressionEntry] = []
        for case_id in sorted(set(baseline_by_id) | set(current_by_id)):
            before = baseline_by_id.get(case_id)
            after = current_by_id.get(case_id)
            if before is None:
                change = RegressionChange.ADDED
            elif after is None:
                change = RegressionChange.REMOVED
            else:
                change = _classify_status_change(before.status, after.status)
            entries.append(
                RegressionEntry(
                    case_id,
                    change,
                    None if before is None else before.status,
                    None if after is None else after.status,
                )
            )
        if not entries:
            status = RegressionStatus.UNKNOWN
        elif any(item.is_regression for item in entries):
            status = RegressionStatus.FAIL
        elif all(item.change is RegressionChange.ADDED for item in entries):
            status = RegressionStatus.WARN
        else:
            status = RegressionStatus.PASS
        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        return RegressionReport(
            1,
            timestamp,
            current.suite,
            baseline.generated_at,
            current.generated_at,
            status,
            tuple(entries),
        )


@dataclass(frozen=True, slots=True)
class RegressionStore:
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
    def regression_root(self) -> Path:
        return self.boundary.resolve(".kodepoia/tests/regression")

    def _require_initialized_project(self) -> None:
        if not self.metadata_root.is_dir():
            raise FileNotFoundError(f"Kodepoia project metadata not found: {self.metadata_root}")

    @staticmethod
    def _safe_suite_name(suite: str) -> str:
        value = "".join(char if char.isalnum() or char in "-_" else "-" for char in suite)
        return value.strip("-") or "suite"

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def save(self, report: RegressionReport, *, snapshot: bool = True) -> tuple[Path, Path | None]:
        self._require_initialized_project()
        root = self.regression_root
        root.mkdir(parents=True, exist_ok=True)
        payload = report.to_dict()
        latest = root / "latest.json"
        self._write_json(latest, payload)
        snapshot_path: Path | None = None
        if snapshot:
            parsed = datetime.fromisoformat(report.generated_at.replace("Z", "+00:00")).astimezone(UTC)
            snapshot_path = root / (
                f"regression-{self._safe_suite_name(report.suite)}-"
                f"{parsed.strftime('%Y%m%dT%H%M%S%fZ')}.json"
            )
            self._write_json(snapshot_path, payload)
        return latest, snapshot_path

    def load_latest(self) -> RegressionReport:
        self._require_initialized_project()
        return RegressionReport.load(self.regression_root / "latest.json")
