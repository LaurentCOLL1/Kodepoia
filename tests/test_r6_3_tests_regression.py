from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.quality.regression import (
    KodeRegression,
    RegressionChange,
    RegressionReport,
    RegressionStatus,
    RegressionStore,
)
from kodepoia.quality.tests import (
    KodeTests,
    TestCaseResult,
    TestCaseStatus,
    TestRunReport,
    TestRunStatus,
    TestRunStore,
)


def _run(
    results: list[TestCaseResult],
    *,
    generated_at: str = "2026-08-22T08:00:00Z",
    suite: str = "core",
) -> TestRunReport:
    return KodeTests.evaluate(results, suite=suite, platform="windows", generated_at=generated_at)


def test_clean_test_run_passes_with_deterministic_counts_and_duration() -> None:
    report = _run(
        [
            TestCaseResult("a", TestCaseStatus.PASS, duration_s=0.1),
            TestCaseResult("b", TestCaseStatus.PASS, duration_s=0.2),
        ]
    )

    assert report.status is TestRunStatus.PASS
    assert report.counts == {"total": 2, "passed": 2, "failed": 0, "errors": 0, "skipped": 0}
    assert report.duration_s == pytest.approx(0.3)


def test_skip_warns_and_failure_or_error_fails() -> None:
    assert _run([TestCaseResult("a", TestCaseStatus.SKIP)]).status is TestRunStatus.WARN
    assert _run([TestCaseResult("a", TestCaseStatus.FAIL)]).status is TestRunStatus.FAIL
    assert _run([TestCaseResult("a", TestCaseStatus.ERROR)]).status is TestRunStatus.FAIL
    assert _run([]).status is TestRunStatus.UNKNOWN


def test_duplicate_test_ids_and_negative_duration_are_rejected() -> None:
    with pytest.raises(ValueError, match="duration cannot be negative"):
        TestCaseResult("a", TestCaseStatus.PASS, duration_s=-1)
    duplicate = TestCaseResult("a", TestCaseStatus.PASS)
    with pytest.raises(ValueError, match="Test case IDs must be unique"):
        _run([duplicate, duplicate])


def test_test_report_round_trip_rejects_tampered_derived_fields(tmp_path: Path) -> None:
    report = _run([TestCaseResult("a", TestCaseStatus.PASS, duration_s=0.25)])
    path = tmp_path / "test-run.json"
    path.write_text(json.dumps(report.to_dict()), encoding="utf-8")

    assert TestRunReport.load(path) == report

    payload = report.to_dict()
    payload["counts"]["passed"] = 99
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="counts do not match"):
        TestRunReport.load(path)


def test_test_run_store_is_project_confined_and_round_trips(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / ".kodepoia").mkdir(parents=True)
    report = _run([TestCaseResult("a", TestCaseStatus.PASS)])

    latest, snapshot = TestRunStore(project).save(report)

    assert latest == project / ".kodepoia" / "tests" / "runs" / "latest.json"
    assert snapshot is not None and snapshot.is_file()
    assert TestRunStore(project).load_latest() == report


def test_regression_compare_tracks_fixed_and_added_without_false_failure() -> None:
    baseline = _run(
        [
            TestCaseResult("stable", TestCaseStatus.PASS),
            TestCaseResult("broken", TestCaseStatus.FAIL),
        ]
    )
    current = _run(
        [
            TestCaseResult("stable", TestCaseStatus.PASS),
            TestCaseResult("broken", TestCaseStatus.PASS),
            TestCaseResult("new", TestCaseStatus.PASS),
        ],
        generated_at="2026-08-22T08:01:00Z",
    )

    report = KodeRegression.compare(baseline, current, generated_at="2026-08-22T08:02:00Z")

    assert report.status is RegressionStatus.PASS
    assert report.fixed == ("broken",)
    assert report.added == ("new",)
    assert report.regressions == ()


def test_pass_to_fail_pass_to_skip_and_removed_cases_are_regressions() -> None:
    baseline = _run(
        [
            TestCaseResult("fail-now", TestCaseStatus.PASS),
            TestCaseResult("skip-now", TestCaseStatus.PASS),
            TestCaseResult("removed", TestCaseStatus.PASS),
        ]
    )
    current = _run(
        [
            TestCaseResult("fail-now", TestCaseStatus.FAIL),
            TestCaseResult("skip-now", TestCaseStatus.SKIP),
        ],
        generated_at="2026-08-22T08:01:00Z",
    )

    report = KodeRegression.compare(baseline, current)

    assert report.status is RegressionStatus.FAIL
    assert report.regressions == ("fail-now", "removed", "skip-now")
    assert report.removed == ("removed",)


def test_fail_to_skip_is_not_counted_as_a_fix() -> None:
    baseline = _run([TestCaseResult("hidden", TestCaseStatus.FAIL)])
    current = _run(
        [TestCaseResult("hidden", TestCaseStatus.SKIP)],
        generated_at="2026-08-22T08:01:00Z",
    )

    report = KodeRegression.compare(baseline, current)

    assert report.status is RegressionStatus.FAIL
    assert report.regressions == ("hidden",)
    assert report.fixed == ()


def test_no_baseline_warns_for_only_new_passing_tests_and_fails_for_new_failure() -> None:
    empty = _run([])
    passing = _run(
        [TestCaseResult("new", TestCaseStatus.PASS)],
        generated_at="2026-08-22T08:01:00Z",
    )
    failing = _run(
        [TestCaseResult("new", TestCaseStatus.FAIL)],
        generated_at="2026-08-22T08:01:00Z",
    )

    assert KodeRegression.compare(empty, passing).status is RegressionStatus.WARN
    failed_report = KodeRegression.compare(empty, failing)
    assert failed_report.status is RegressionStatus.FAIL
    assert failed_report.regressions == ("new",)


def test_suite_mismatch_is_rejected() -> None:
    baseline = _run([TestCaseResult("a", TestCaseStatus.PASS)], suite="core")
    current = _run(
        [TestCaseResult("a", TestCaseStatus.PASS)],
        generated_at="2026-08-22T08:01:00Z",
        suite="other",
    )

    with pytest.raises(ValueError, match="matching test suites"):
        KodeRegression.compare(baseline, current)


def test_regression_report_round_trip_and_tamper_detection(tmp_path: Path) -> None:
    baseline = _run([TestCaseResult("a", TestCaseStatus.PASS)])
    current = _run(
        [TestCaseResult("a", TestCaseStatus.FAIL)],
        generated_at="2026-08-22T08:01:00Z",
    )
    report = KodeRegression.compare(
        baseline,
        current,
        generated_at="2026-08-22T08:02:00Z",
    )
    path = tmp_path / "regression.json"
    path.write_text(json.dumps(report.to_dict()), encoding="utf-8")

    assert RegressionReport.load(path) == report

    payload = report.to_dict()
    payload["regressions"] = []
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="regressions do not match"):
        RegressionReport.load(path)


def test_regression_store_persists_latest_and_snapshot(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / ".kodepoia").mkdir(parents=True)
    baseline = _run([TestCaseResult("a", TestCaseStatus.PASS)])
    current = _run(
        [TestCaseResult("a", TestCaseStatus.PASS)],
        generated_at="2026-08-22T08:01:00Z",
    )
    report = KodeRegression.compare(
        baseline,
        current,
        generated_at="2026-08-22T08:02:00Z",
    )

    latest, snapshot = RegressionStore(project).save(report)

    assert latest == project / ".kodepoia" / "tests" / "regression" / "latest.json"
    assert snapshot is not None and snapshot.is_file()
    assert RegressionStore(project).load_latest() == report


def test_regression_entry_change_values_are_stable() -> None:
    assert [item.value for item in RegressionChange] == [
        "unchanged",
        "regressed",
        "fixed",
        "added",
        "removed",
    ]
