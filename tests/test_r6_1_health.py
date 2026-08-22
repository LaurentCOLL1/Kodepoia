from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.kodecode.workspace import WorkspaceViolation
from kodepoia.quality.health import (
    HealthDimension,
    HealthMetric,
    HealthReport,
    HealthStatus,
    HealthStore,
    KodeHealth,
)


def _all_pass_metrics() -> list[HealthMetric]:
    return [
        HealthMetric(dimension=dimension, status=HealthStatus.PASS, score=100.0)
        for dimension in HealthDimension
    ]


def test_incomplete_health_report_is_warning_and_exposes_unknown_dimensions() -> None:
    report = KodeHealth().evaluate(
        [
            HealthMetric(HealthDimension.BUILD, HealthStatus.PASS, 100.0),
            HealthMetric(HealthDimension.TESTS, HealthStatus.PASS, 90.0),
        ],
        project_name="fixture",
        generated_at="2026-08-22T08:00:00Z",
    )

    assert report.status is HealthStatus.WARN
    assert report.overall_score == 95.0
    assert report.coverage == round(2 / len(HealthDimension), 6)
    assert HealthDimension.SECURITY in report.unknown_dimensions


def test_complete_clean_health_report_passes() -> None:
    report = KodeHealth().evaluate(_all_pass_metrics())

    assert report.status is HealthStatus.PASS
    assert report.overall_score == 100.0
    assert report.coverage == 1.0
    assert report.unknown_dimensions == ()
    assert report.blockers == ()


def test_failing_blocker_forces_fail_even_with_high_average() -> None:
    metrics = [
        HealthMetric(
            dimension,
            HealthStatus.FAIL if dimension is HealthDimension.SECURITY else HealthStatus.PASS,
            0.0 if dimension is HealthDimension.SECURITY else 100.0,
            summary="Critical security regression" if dimension is HealthDimension.SECURITY else "",
            blocking=dimension is HealthDimension.SECURITY,
        )
        for dimension in HealthDimension
    ]

    report = KodeHealth().evaluate(metrics)

    assert report.status is HealthStatus.FAIL
    assert report.blockers == (HealthDimension.SECURITY,)


def test_duplicate_health_dimension_is_rejected() -> None:
    metric = HealthMetric(HealthDimension.BUILD, HealthStatus.PASS, 100.0)

    with pytest.raises(ValueError, match="Duplicate health dimension"):
        KodeHealth().evaluate([metric, metric])


def test_metric_validation_rejects_inconsistent_unknown_and_blocking_values() -> None:
    with pytest.raises(ValueError, match="Unknown health metrics cannot carry a score"):
        HealthMetric(HealthDimension.BUILD, HealthStatus.UNKNOWN, 50.0)
    with pytest.raises(ValueError, match="Only failing health metrics can be blocking"):
        HealthMetric(HealthDimension.BUILD, HealthStatus.PASS, 100.0, blocking=True)


def test_serialized_derived_fields_must_match_metric_evidence() -> None:
    report = KodeHealth().evaluate(_all_pass_metrics())
    payload = report.to_dict()
    payload["blockers"] = [HealthDimension.SECURITY.value]

    with pytest.raises(ValueError, match="blockers do not match"):
        HealthReport.from_dict(payload)

    payload = report.to_dict()
    payload["unknown_dimensions"] = [HealthDimension.PRIVACY.value]
    with pytest.raises(ValueError, match="unknown dimensions do not match"):
        HealthReport.from_dict(payload)


def test_health_store_writes_latest_and_snapshot_and_round_trips(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / ".kodepoia").mkdir(parents=True)
    store = HealthStore(project)
    report = KodeHealth().evaluate(
        _all_pass_metrics(),
        project_name="fixture",
        generated_at="2026-08-22T08:00:00Z",
    )

    latest, snapshot = store.save(report)

    assert latest == project / ".kodepoia" / "health" / "latest.json"
    assert snapshot == project / ".kodepoia" / "health" / "health-20260822T080000000000Z.json"
    assert latest.is_file()
    assert snapshot is not None and snapshot.is_file()
    assert store.load_latest() == report
    assert HealthReport.load(snapshot) == report


def test_health_store_requires_initialized_project(tmp_path: Path) -> None:
    report = KodeHealth().evaluate(_all_pass_metrics())

    with pytest.raises(FileNotFoundError, match="Kodepoia project metadata not found"):
        HealthStore(tmp_path / "missing").save(report)


def test_health_store_rejects_metadata_symlink_escape(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    try:
        (project / ".kodepoia").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlink creation is not available on this platform/runner")

    with pytest.raises(WorkspaceViolation, match="escapes workspace"):
        HealthStore(project).save(KodeHealth().evaluate(_all_pass_metrics()))
