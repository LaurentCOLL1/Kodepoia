from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.project.dna import Dimension, PerformanceBudget, Platform, ProjectDNA, ProjectType
from kodepoia.quality.budget import (
    BudgetConstraint,
    BudgetDirection,
    BudgetMetric,
    BudgetObservation,
    BudgetReport,
    BudgetStatus,
    BudgetStore,
    KodeBudget,
    PlatformBudgetSpec,
)


def _dna() -> ProjectDNA:
    return ProjectDNA(
        schema_version=1,
        name="fixture",
        project_type=ProjectType.GAME,
        platforms=[Platform.WINDOWS],
        engine="Godot",
        engine_version="4.7",
        dimension=Dimension.D3,
        performance={
            "windows": PerformanceBudget(
                target_fps=60,
                min_fps=30,
                max_vram_mb=4096,
                max_ram_mb=8192,
                max_build_mb=500,
            )
        },
    )


def test_budget_specs_are_derived_only_for_target_platforms() -> None:
    specs = KodeBudget.from_project_dna(_dna())

    assert set(specs) == {Platform.WINDOWS}
    constraints = {item.metric: item for item in specs[Platform.WINDOWS].constraints}
    assert constraints[BudgetMetric.FPS].target == 60.0
    assert constraints[BudgetMetric.FPS].limit == 30.0
    assert constraints[BudgetMetric.FRAME_TIME_MS].target == pytest.approx(1000 / 60)
    assert constraints[BudgetMetric.FRAME_TIME_MS].limit == pytest.approx(1000 / 30)
    assert constraints[BudgetMetric.VRAM_MB].limit == 4096.0
    assert constraints[BudgetMetric.RAM_MB].limit == 8192.0
    assert constraints[BudgetMetric.BUILD_SIZE_MB].limit == 500.0
    assert BudgetMetric.BATTERY_PERCENT_PER_HOUR in specs[Platform.WINDOWS].unconfigured_metrics


def test_complete_budget_observations_pass() -> None:
    spec = KodeBudget.from_project_dna(_dna())[Platform.WINDOWS]
    report = KodeBudget.evaluate(
        spec,
        [
            BudgetObservation(BudgetMetric.FPS, 60),
            BudgetObservation(BudgetMetric.FRAME_TIME_MS, 16.0),
            BudgetObservation(BudgetMetric.VRAM_MB, 3500),
            BudgetObservation(BudgetMetric.RAM_MB, 7000),
            BudgetObservation(BudgetMetric.BUILD_SIZE_MB, 450),
        ],
        project_name="fixture",
        generated_at="2026-08-22T08:00:00Z",
    )

    assert report.status is BudgetStatus.PASS
    assert report.coverage == 1.0
    assert report.blockers == ()
    assert report.unknown_metrics == ()


def test_target_miss_warns_without_crossing_hard_limit() -> None:
    spec = PlatformBudgetSpec(
        Platform.WINDOWS,
        (
            BudgetConstraint(
                BudgetMetric.FPS,
                BudgetDirection.AT_LEAST,
                limit=30,
                target=60,
                unit="fps",
            ),
        ),
    )

    report = KodeBudget.evaluate(spec, [BudgetObservation(BudgetMetric.FPS, 45)])

    assert report.status is BudgetStatus.WARN
    assert report.results[0].status is BudgetStatus.WARN


def test_hard_limit_failure_is_blocking_when_constraint_is_blocking() -> None:
    spec = PlatformBudgetSpec(
        Platform.WINDOWS,
        (
            BudgetConstraint(
                BudgetMetric.FPS,
                BudgetDirection.AT_LEAST,
                limit=30,
                target=60,
                unit="fps",
                blocking=True,
            ),
        ),
    )

    report = KodeBudget.evaluate(spec, [BudgetObservation(BudgetMetric.FPS, 20)])

    assert report.status is BudgetStatus.FAIL
    assert report.blockers == (BudgetMetric.FPS,)


def test_missing_configured_observations_are_explicitly_unknown() -> None:
    spec = KodeBudget.from_project_dna(_dna())[Platform.WINDOWS]
    report = KodeBudget.evaluate(spec, [BudgetObservation(BudgetMetric.FPS, 60)])

    assert report.status is BudgetStatus.WARN
    assert report.coverage == 0.2
    assert BudgetMetric.FRAME_TIME_MS in report.unknown_metrics


def test_unconfigured_and_duplicate_observations_are_rejected() -> None:
    spec = PlatformBudgetSpec(
        Platform.WINDOWS,
        (BudgetConstraint(BudgetMetric.FPS, BudgetDirection.AT_LEAST, 30, target=60),),
    )
    fps = BudgetObservation(BudgetMetric.FPS, 60)

    with pytest.raises(ValueError, match="Duplicate budget observation"):
        KodeBudget.evaluate(spec, [fps, fps])
    with pytest.raises(ValueError, match="unconfigured budget metric"):
        KodeBudget.evaluate(spec, [BudgetObservation(BudgetMetric.RAM_MB, 100)])


def test_budget_report_round_trip_and_derived_field_tamper_detection(tmp_path: Path) -> None:
    spec = PlatformBudgetSpec(
        Platform.WINDOWS,
        (
            BudgetConstraint(
                BudgetMetric.FPS,
                BudgetDirection.AT_LEAST,
                30,
                target=60,
                blocking=True,
            ),
        ),
    )
    report = KodeBudget.evaluate(
        spec,
        [BudgetObservation(BudgetMetric.FPS, 20)],
        generated_at="2026-08-22T08:00:00Z",
    )
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report.to_dict()), encoding="utf-8")

    assert BudgetReport.load(path) == report

    payload = report.to_dict()
    payload["blockers"] = []
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="blockers do not match"):
        BudgetReport.load(path)


def test_budget_store_is_project_confined_and_round_trips(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / ".kodepoia").mkdir(parents=True)
    spec = PlatformBudgetSpec(
        Platform.WINDOWS,
        (BudgetConstraint(BudgetMetric.FPS, BudgetDirection.AT_LEAST, 30, target=60),),
    )
    report = KodeBudget.evaluate(
        spec,
        [BudgetObservation(BudgetMetric.FPS, 60)],
        project_name="fixture",
        generated_at="2026-08-22T08:00:00Z",
    )

    latest, snapshot = BudgetStore(project).save(report)

    assert latest == project / ".kodepoia" / "budgets" / "windows-latest.json"
    assert snapshot == project / ".kodepoia" / "budgets" / "budget-windows-20260822T080000000000Z.json"
    assert BudgetStore(project).load_latest(Platform.WINDOWS) == report


def test_budget_store_requires_initialized_project(tmp_path: Path) -> None:
    spec = PlatformBudgetSpec(Platform.WINDOWS)
    report = KodeBudget.evaluate(spec, [])

    with pytest.raises((FileNotFoundError, PermissionError)):
        BudgetStore(tmp_path / "missing").save(report)
