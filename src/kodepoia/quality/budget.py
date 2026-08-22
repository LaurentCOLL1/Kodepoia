from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from kodepoia.kodecode.workspace import WorkspaceBoundary
from kodepoia.project.dna import Platform, ProjectDNA


class BudgetMetric(StrEnum):
    FPS = "fps"
    FRAME_TIME_MS = "frame_time_ms"
    CPU_MS = "cpu_ms"
    GPU_MS = "gpu_ms"
    RAM_MB = "ram_mb"
    VRAM_MB = "vram_mb"
    STORAGE_MB = "storage_mb"
    DRAW_CALLS = "draw_calls"
    POLYGONS = "polygons"
    TEXTURE_MB = "texture_mb"
    AUDIO_MEMORY_MB = "audio_memory_mb"
    AUDIO_VOICES = "audio_voices"
    BUILD_SIZE_MB = "build_size_mb"
    BATTERY_PERCENT_PER_HOUR = "battery_percent_per_hour"
    THERMAL_LEVEL = "thermal_level"
    NETWORK_KBPS = "network_kbps"


class BudgetDirection(StrEnum):
    AT_LEAST = "at_least"
    AT_MOST = "at_most"


class BudgetStatus(StrEnum):
    UNKNOWN = "unknown"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class BudgetConstraint:
    metric: BudgetMetric
    direction: BudgetDirection
    limit: float
    target: float | None = None
    unit: str = ""
    blocking: bool = False

    def __post_init__(self) -> None:
        if self.limit < 0:
            raise ValueError("Budget limits cannot be negative")
        if self.target is not None and self.target < 0:
            raise ValueError("Budget targets cannot be negative")
        if self.target is not None:
            if self.direction is BudgetDirection.AT_LEAST and self.target < self.limit:
                raise ValueError("AT_LEAST target cannot be below its hard limit")
            if self.direction is BudgetDirection.AT_MOST and self.target > self.limit:
                raise ValueError("AT_MOST target cannot exceed its hard limit")


@dataclass(frozen=True, slots=True)
class PlatformBudgetSpec:
    platform: Platform
    constraints: tuple[BudgetConstraint, ...] = ()

    def __post_init__(self) -> None:
        metrics = [item.metric for item in self.constraints]
        if len(metrics) != len(set(metrics)):
            raise ValueError(f"Duplicate budget metric for platform {self.platform.value}")

    @property
    def unconfigured_metrics(self) -> tuple[BudgetMetric, ...]:
        configured = {item.metric for item in self.constraints}
        return tuple(metric for metric in BudgetMetric if metric not in configured)


@dataclass(frozen=True, slots=True)
class BudgetObservation:
    metric: BudgetMetric
    value: float
    source: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Budget observations cannot be negative")


@dataclass(frozen=True, slots=True)
class BudgetMetricResult:
    metric: BudgetMetric
    status: BudgetStatus
    value: float | None
    limit: float
    target: float | None
    direction: BudgetDirection
    unit: str
    blocking: bool = False
    source: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status is BudgetStatus.UNKNOWN and self.value is not None:
            raise ValueError("Unknown budget results cannot carry a value")
        if self.status is not BudgetStatus.UNKNOWN and self.value is None:
            raise ValueError("Measured budget results require a value")
        if self.blocking and self.status is not BudgetStatus.FAIL:
            raise ValueError("Only failing budget results can be blocking")


@dataclass(frozen=True, slots=True)
class BudgetReport:
    schema_version: int
    generated_at: str
    project_name: str
    platform: Platform
    status: BudgetStatus
    coverage: float
    results: tuple[BudgetMetricResult, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("Unsupported budget report schema version")
        parsed = datetime.fromisoformat(self.generated_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Budget report timestamp must include a timezone")
        if not 0.0 <= self.coverage <= 1.0:
            raise ValueError("Budget report coverage must be between 0 and 1")
        metrics = [item.metric for item in self.results]
        if len(metrics) != len(set(metrics)):
            raise ValueError("Budget report metrics must be unique")
        measured = [item for item in self.results if item.status is not BudgetStatus.UNKNOWN]
        expected = 0.0 if not self.results else round(len(measured) / len(self.results), 6)
        if abs(self.coverage - expected) > 0.000001:
            raise ValueError("Budget report coverage does not match configured constraints")
        if self.status is not self._derive_status():
            raise ValueError("Budget report status does not match result evidence")

    def _derive_status(self) -> BudgetStatus:
        if not self.results:
            return BudgetStatus.UNKNOWN
        measured = [item for item in self.results if item.status is not BudgetStatus.UNKNOWN]
        if not measured:
            return BudgetStatus.UNKNOWN
        if any(item.status is BudgetStatus.FAIL for item in measured):
            return BudgetStatus.FAIL
        if len(measured) != len(self.results) or any(item.status is BudgetStatus.WARN for item in measured):
            return BudgetStatus.WARN
        return BudgetStatus.PASS

    @property
    def blockers(self) -> tuple[BudgetMetric, ...]:
        return tuple(item.metric for item in self.results if item.status is BudgetStatus.FAIL and item.blocking)

    @property
    def unknown_metrics(self) -> tuple[BudgetMetric, ...]:
        return tuple(item.metric for item in self.results if item.status is BudgetStatus.UNKNOWN)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "project_name": self.project_name,
            "platform": self.platform.value,
            "status": self.status.value,
            "coverage": self.coverage,
            "blockers": [metric.value for metric in self.blockers],
            "unknown_metrics": [metric.value for metric in self.unknown_metrics],
            "results": [
                {
                    "metric": item.metric.value,
                    "status": item.status.value,
                    "value": item.value,
                    "limit": item.limit,
                    "target": item.target,
                    "direction": item.direction.value,
                    "unit": item.unit,
                    "blocking": item.blocking,
                    "source": item.source,
                    "details": item.details,
                }
                for item in self.results
            ],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BudgetReport":
        if int(payload.get("schema_version", 0)) != 1:
            raise ValueError("Unsupported budget report schema version")
        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raise ValueError("Budget report results must be a list")
        results = tuple(
            BudgetMetricResult(
                metric=BudgetMetric(item["metric"]),
                status=BudgetStatus(item["status"]),
                value=None if item.get("value") is None else float(item["value"]),
                limit=float(item["limit"]),
                target=None if item.get("target") is None else float(item["target"]),
                direction=BudgetDirection(item["direction"]),
                unit=str(item.get("unit", "")),
                blocking=bool(item.get("blocking", False)),
                source=str(item.get("source", "")),
                details=dict(item.get("details", {})),
            )
            for item in raw_results
        )
        report = cls(
            schema_version=1,
            generated_at=str(payload["generated_at"]),
            project_name=str(payload.get("project_name", "")),
            platform=Platform(payload["platform"]),
            status=BudgetStatus(payload["status"]),
            coverage=float(payload["coverage"]),
            results=results,
        )
        blockers = tuple(BudgetMetric(item) for item in payload.get("blockers", []))
        unknown = tuple(BudgetMetric(item) for item in payload.get("unknown_metrics", []))
        if blockers != report.blockers:
            raise ValueError("Serialized budget blockers do not match result evidence")
        if unknown != report.unknown_metrics:
            raise ValueError("Serialized unknown budget metrics do not match result evidence")
        return report

    @classmethod
    def load(cls, path: Path) -> "BudgetReport":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Budget report must be a JSON object")
        return cls.from_dict(payload)


class KodeBudget:
    @staticmethod
    def from_project_dna(dna: ProjectDNA) -> dict[Platform, PlatformBudgetSpec]:
        dna.validate()
        specs: dict[Platform, PlatformBudgetSpec] = {}
        for platform in dna.platforms:
            performance = dna.performance.get(platform.value)
            constraints: list[BudgetConstraint] = []
            if performance is not None:
                constraints.extend(
                    [
                        BudgetConstraint(
                            BudgetMetric.FPS,
                            BudgetDirection.AT_LEAST,
                            float(performance.min_fps),
                            target=float(performance.target_fps),
                            unit="fps",
                            blocking=True,
                        ),
                        BudgetConstraint(
                            BudgetMetric.FRAME_TIME_MS,
                            BudgetDirection.AT_MOST,
                            round(1000.0 / performance.min_fps, 6),
                            target=round(1000.0 / performance.target_fps, 6),
                            unit="ms",
                            blocking=True,
                        ),
                    ]
                )
                optional = (
                    (BudgetMetric.VRAM_MB, performance.max_vram_mb, "MB"),
                    (BudgetMetric.RAM_MB, performance.max_ram_mb, "MB"),
                    (BudgetMetric.BUILD_SIZE_MB, performance.max_build_mb, "MB"),
                )
                for metric, limit, unit in optional:
                    if limit is not None:
                        constraints.append(
                            BudgetConstraint(
                                metric,
                                BudgetDirection.AT_MOST,
                                float(limit),
                                unit=unit,
                                blocking=True,
                            )
                        )
            specs[platform] = PlatformBudgetSpec(platform, tuple(constraints))
        return specs

    @staticmethod
    def evaluate(
        spec: PlatformBudgetSpec,
        observations: Iterable[BudgetObservation],
        *,
        project_name: str = "",
        generated_at: str | None = None,
    ) -> BudgetReport:
        supplied: dict[BudgetMetric, BudgetObservation] = {}
        for observation in observations:
            if observation.metric in supplied:
                raise ValueError(f"Duplicate budget observation: {observation.metric.value}")
            supplied[observation.metric] = observation
        configured = {item.metric for item in spec.constraints}
        unexpected = set(supplied) - configured
        if unexpected:
            names = ", ".join(sorted(item.value for item in unexpected))
            raise ValueError(f"Observation supplied for unconfigured budget metric(s): {names}")

        results = tuple(
            KodeBudget._evaluate_constraint(constraint, supplied.get(constraint.metric))
            for constraint in spec.constraints
        )
        measured = [item for item in results if item.status is not BudgetStatus.UNKNOWN]
        coverage = 0.0 if not results else len(measured) / len(results)
        if not measured:
            status = BudgetStatus.UNKNOWN
        elif any(item.status is BudgetStatus.FAIL for item in measured):
            status = BudgetStatus.FAIL
        elif len(measured) != len(results) or any(item.status is BudgetStatus.WARN for item in measured):
            status = BudgetStatus.WARN
        else:
            status = BudgetStatus.PASS
        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        return BudgetReport(
            schema_version=1,
            generated_at=timestamp,
            project_name=project_name,
            platform=spec.platform,
            status=status,
            coverage=round(coverage, 6),
            results=results,
        )

    @staticmethod
    def _evaluate_constraint(
        constraint: BudgetConstraint, observation: BudgetObservation | None
    ) -> BudgetMetricResult:
        if observation is None:
            return BudgetMetricResult(
                metric=constraint.metric,
                status=BudgetStatus.UNKNOWN,
                value=None,
                limit=constraint.limit,
                target=constraint.target,
                direction=constraint.direction,
                unit=constraint.unit,
            )
        value = observation.value
        if constraint.direction is BudgetDirection.AT_LEAST:
            if value < constraint.limit:
                status = BudgetStatus.FAIL
            elif constraint.target is not None and value < constraint.target:
                status = BudgetStatus.WARN
            else:
                status = BudgetStatus.PASS
        else:
            if value > constraint.limit:
                status = BudgetStatus.FAIL
            elif constraint.target is not None and value > constraint.target:
                status = BudgetStatus.WARN
            else:
                status = BudgetStatus.PASS
        return BudgetMetricResult(
            metric=constraint.metric,
            status=status,
            value=value,
            limit=constraint.limit,
            target=constraint.target,
            direction=constraint.direction,
            unit=constraint.unit,
            blocking=constraint.blocking and status is BudgetStatus.FAIL,
            source=observation.source,
            details=dict(observation.details),
        )


@dataclass(frozen=True, slots=True)
class BudgetStore:
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
    def budgets_root(self) -> Path:
        return self.boundary.resolve(".kodepoia/budgets")

    def _require_initialized_project(self) -> None:
        if not self.metadata_root.is_dir():
            raise FileNotFoundError(f"Kodepoia project metadata not found: {self.metadata_root}")

    @staticmethod
    def _snapshot_name(report: BudgetReport) -> str:
        parsed = datetime.fromisoformat(report.generated_at.replace("Z", "+00:00")).astimezone(UTC)
        return f"budget-{report.platform.value}-{parsed.strftime('%Y%m%dT%H%M%S%fZ')}.json"

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def save(self, report: BudgetReport, *, snapshot: bool = True) -> tuple[Path, Path | None]:
        self._require_initialized_project()
        root = self.budgets_root
        root.mkdir(exist_ok=True)
        payload = report.to_dict()
        latest = root / f"{report.platform.value}-latest.json"
        self._write_json(latest, payload)
        snapshot_path: Path | None = None
        if snapshot:
            snapshot_path = root / self._snapshot_name(report)
            self._write_json(snapshot_path, payload)
        return latest, snapshot_path

    def load_latest(self, platform: Platform) -> BudgetReport:
        self._require_initialized_project()
        return BudgetReport.load(self.budgets_root / f"{platform.value}-latest.json")
