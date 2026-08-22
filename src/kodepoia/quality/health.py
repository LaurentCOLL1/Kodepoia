from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class HealthDimension(StrEnum):
    BUILD = "build"
    TESTS = "tests"
    WARNINGS = "warnings"
    SECURITY = "security"
    DEPENDENCIES = "dependencies"
    PERFORMANCE = "performance"
    MEMORY = "memory"
    ASSETS = "assets"
    AUDIO = "audio"
    ACCESSIBILITY = "accessibility"
    LOCALIZATION = "localization"
    TECHNICAL_DEBT = "technical_debt"
    LICENSES = "licenses"
    PRIVACY = "privacy"


class HealthStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class HealthMetric:
    dimension: HealthDimension
    status: HealthStatus
    score: float | None = None
    summary: str = ""
    source: str = ""
    blocking: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.score is not None and not 0.0 <= self.score <= 100.0:
            raise ValueError("Health metric score must be between 0 and 100")
        if self.status is HealthStatus.UNKNOWN and self.score is not None:
            raise ValueError("Unknown health metrics cannot carry a score")
        if self.status is not HealthStatus.UNKNOWN and self.score is None:
            raise ValueError("Measured health metrics require a score")
        if self.blocking and self.status is not HealthStatus.FAIL:
            raise ValueError("Only failing health metrics can be blocking")


@dataclass(frozen=True, slots=True)
class HealthPolicy:
    pass_score: float = 85.0
    fail_score: float = 60.0
    require_complete_for_pass: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= self.fail_score < self.pass_score <= 100.0:
            raise ValueError("Health thresholds must satisfy 0 <= fail < pass <= 100")


@dataclass(frozen=True, slots=True)
class HealthReport:
    schema_version: int
    generated_at: str
    project_name: str
    overall_score: float | None
    coverage: float
    status: HealthStatus
    metrics: tuple[HealthMetric, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("Unsupported health report schema version")
        generated = datetime.fromisoformat(self.generated_at.replace("Z", "+00:00"))
        if generated.tzinfo is None:
            raise ValueError("Health report timestamp must include a timezone")
        if self.overall_score is not None and not 0.0 <= self.overall_score <= 100.0:
            raise ValueError("Health report overall score must be between 0 and 100")
        if not 0.0 <= self.coverage <= 1.0:
            raise ValueError("Health report coverage must be between 0 and 1")

        dimensions = [metric.dimension for metric in self.metrics]
        if len(dimensions) != len(set(dimensions)):
            raise ValueError("Health report dimensions must be unique")
        if set(dimensions) != set(HealthDimension):
            raise ValueError("Health report must contain every architecture health dimension")

        measured = [metric for metric in self.metrics if metric.status is not HealthStatus.UNKNOWN]
        expected_coverage = round(len(measured) / len(HealthDimension), 6)
        if abs(self.coverage - expected_coverage) > 0.000001:
            raise ValueError("Health report coverage does not match measured dimensions")
        if measured and self.overall_score is None:
            raise ValueError("Measured health reports require an overall score")
        if not measured and self.overall_score is not None:
            raise ValueError("Unmeasured health reports cannot carry an overall score")

    @property
    def blockers(self) -> tuple[HealthDimension, ...]:
        return tuple(
            metric.dimension
            for metric in self.metrics
            if metric.status is HealthStatus.FAIL and metric.blocking
        )

    @property
    def unknown_dimensions(self) -> tuple[HealthDimension, ...]:
        return tuple(
            metric.dimension for metric in self.metrics if metric.status is HealthStatus.UNKNOWN
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "project_name": self.project_name,
            "overall_score": self.overall_score,
            "coverage": self.coverage,
            "status": self.status.value,
            "blockers": [dimension.value for dimension in self.blockers],
            "unknown_dimensions": [dimension.value for dimension in self.unknown_dimensions],
            "metrics": [
                {
                    "dimension": metric.dimension.value,
                    "status": metric.status.value,
                    "score": metric.score,
                    "summary": metric.summary,
                    "source": metric.source,
                    "blocking": metric.blocking,
                    "details": metric.details,
                }
                for metric in self.metrics
            ],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> HealthReport:
        if int(payload.get("schema_version", 0)) != 1:
            raise ValueError("Unsupported health report schema version")
        raw_metrics = payload.get("metrics")
        if not isinstance(raw_metrics, list):
            raise ValueError("Health report metrics must be a list")
        metrics = tuple(
            HealthMetric(
                dimension=HealthDimension(item["dimension"]),
                status=HealthStatus(item["status"]),
                score=None if item.get("score") is None else float(item["score"]),
                summary=str(item.get("summary", "")),
                source=str(item.get("source", "")),
                blocking=bool(item.get("blocking", False)),
                details=dict(item.get("details", {})),
            )
            for item in raw_metrics
        )
        coverage = float(payload["coverage"])
        overall = payload.get("overall_score")
        return cls(
            schema_version=1,
            generated_at=str(payload["generated_at"]),
            project_name=str(payload.get("project_name", "")),
            overall_score=None if overall is None else float(overall),
            coverage=coverage,
            status=HealthStatus(payload["status"]),
            metrics=metrics,
        )

    @classmethod
    def load(cls, path: Path) -> HealthReport:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Health report must be a JSON object")
        return cls.from_dict(payload)


class KodeHealth:
    DIMENSIONS = tuple(HealthDimension)

    def __init__(self, policy: HealthPolicy | None = None) -> None:
        self.policy = policy or HealthPolicy()

    def evaluate(
        self,
        metrics: Iterable[HealthMetric],
        *,
        project_name: str = "",
        generated_at: str | None = None,
    ) -> HealthReport:
        supplied: dict[HealthDimension, HealthMetric] = {}
        for metric in metrics:
            if metric.dimension in supplied:
                raise ValueError(f"Duplicate health dimension: {metric.dimension.value}")
            supplied[metric.dimension] = metric

        normalized = tuple(
            supplied.get(
                dimension,
                HealthMetric(
                    dimension=dimension,
                    status=HealthStatus.UNKNOWN,
                    summary="No observation supplied",
                ),
            )
            for dimension in self.DIMENSIONS
        )
        measured = [metric for metric in normalized if metric.status is not HealthStatus.UNKNOWN]
        coverage = len(measured) / len(self.DIMENSIONS)
        overall_score = (
            round(sum(float(metric.score) for metric in measured) / len(measured), 2)
            if measured
            else None
        )

        if not measured:
            status = HealthStatus.UNKNOWN
        elif any(metric.status is HealthStatus.FAIL for metric in measured):
            status = HealthStatus.FAIL
        elif overall_score is not None and overall_score < self.policy.fail_score:
            status = HealthStatus.FAIL
        elif any(metric.status is HealthStatus.WARN for metric in measured):
            status = HealthStatus.WARN
        elif overall_score is not None and overall_score < self.policy.pass_score:
            status = HealthStatus.WARN
        elif self.policy.require_complete_for_pass and coverage < 1.0:
            status = HealthStatus.WARN
        else:
            status = HealthStatus.PASS

        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        return HealthReport(
            schema_version=1,
            generated_at=timestamp,
            project_name=project_name,
            overall_score=overall_score,
            coverage=round(coverage, 6),
            status=status,
            metrics=normalized,
        )


@dataclass(frozen=True, slots=True)
class HealthStore:
    project_root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_root", self.project_root.resolve(strict=False))

    @property
    def metadata_root(self) -> Path:
        return self.project_root / ".kodepoia"

    @property
    def health_root(self) -> Path:
        return self.metadata_root / "health"

    def _require_initialized_project(self) -> None:
        if not self.metadata_root.is_dir():
            raise FileNotFoundError(f"Kodepoia project metadata not found: {self.metadata_root}")

    @staticmethod
    def _snapshot_name(generated_at: str) -> str:
        parsed = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        utc_value = parsed.astimezone(UTC)
        return f"health-{utc_value.strftime('%Y%m%dT%H%M%S%fZ')}.json"

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def save(self, report: HealthReport, *, snapshot: bool = True) -> tuple[Path, Path | None]:
        self._require_initialized_project()
        self.health_root.mkdir(exist_ok=True)
        payload = report.to_dict()
        latest = self.health_root / "latest.json"
        self._write_json(latest, payload)
        snapshot_path: Path | None = None
        if snapshot:
            snapshot_path = self.health_root / self._snapshot_name(report.generated_at)
            self._write_json(snapshot_path, payload)
        return latest, snapshot_path

    def load_latest(self) -> HealthReport:
        self._require_initialized_project()
        return HealthReport.load(self.health_root / "latest.json")
