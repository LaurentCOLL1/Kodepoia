from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.quality.accessibility import (
    AccessibilityReport,
    AccessibilityReportStatus,
    AccessibilityResult,
    AccessibilitySeverity,
    AccessibilityStatus,
    AccessibilityStore,
    KodeAccessibility,
)
from kodepoia.quality.tests import TestCaseStatus


def _result(
    rule: str,
    target: str,
    status: AccessibilityStatus,
    *,
    blocking: bool = False,
    reason: str = "",
) -> AccessibilityResult:
    return AccessibilityResult(
        rule_id=rule,
        target_id=target,
        status=status,
        severity=AccessibilitySeverity.MAJOR,
        summary=f"{rule}:{target}",
        evidence={"source": "fixture"},
        applicability_reason=reason,
        blocking=blocking,
    )


def test_report_status_and_counts_ignore_not_applicable_for_pass() -> None:
    report = KodeAccessibility.evaluate(
        [
            _result("name.required", "save", AccessibilityStatus.PASS),
            _result(
                "focus.visible",
                "hidden-panel",
                AccessibilityStatus.NOT_APPLICABLE,
                reason="Panel is intentionally hidden in this state",
            ),
        ],
        surface="fixture",
        generated_at="2026-08-22T10:00:00Z",
    )
    assert report.status is AccessibilityReportStatus.PASS
    assert report.counts == {
        "total": 2,
        "applicable": 1,
        "passed": 1,
        "warnings": 0,
        "failed": 0,
        "unknown": 0,
        "not_applicable": 1,
        "blocking_failures": 0,
    }


def test_warn_unknown_fail_and_empty_statuses_are_deterministic() -> None:
    warned = KodeAccessibility.evaluate(
        [_result("focus.visible", "button", AccessibilityStatus.WARN)],
        surface="warn",
    )
    unknown = KodeAccessibility.evaluate(
        [_result("role.exposed", "button", AccessibilityStatus.UNKNOWN)],
        surface="unknown",
    )
    failed = KodeAccessibility.evaluate(
        [_result("name.required", "button", AccessibilityStatus.FAIL, blocking=True)],
        surface="fail",
    )
    empty = KodeAccessibility.evaluate([], surface="empty")
    na_only = KodeAccessibility.evaluate(
        [
            _result(
                "focus.visible",
                "hidden",
                AccessibilityStatus.NOT_APPLICABLE,
                reason="Hidden by design",
            )
        ],
        surface="na-only",
    )
    assert warned.status is AccessibilityReportStatus.WARN
    assert unknown.status is AccessibilityReportStatus.WARN
    assert failed.status is AccessibilityReportStatus.FAIL
    assert failed.counts["blocking_failures"] == 1
    assert empty.status is AccessibilityReportStatus.UNKNOWN
    assert na_only.status is AccessibilityReportStatus.UNKNOWN


def test_not_applicable_and_blocking_invariants() -> None:
    with pytest.raises(ValueError, match="require a reason"):
        _result("focus.visible", "hidden", AccessibilityStatus.NOT_APPLICABLE)
    with pytest.raises(ValueError, match="cannot be blocking"):
        _result(
            "focus.visible",
            "hidden",
            AccessibilityStatus.NOT_APPLICABLE,
            blocking=True,
            reason="Hidden",
        )
    with pytest.raises(ValueError, match="Only failing"):
        _result("name.required", "button", AccessibilityStatus.PASS, blocking=True)
    with pytest.raises(ValueError, match="Applicability reason"):
        _result(
            "name.required",
            "button",
            AccessibilityStatus.PASS,
            reason="should not exist",
        )


def test_duplicate_rule_target_pair_and_unstable_ids_are_rejected() -> None:
    item = _result("name.required", "button", AccessibilityStatus.PASS)
    with pytest.raises(ValueError, match="must be unique"):
        KodeAccessibility.evaluate([item, item], surface="duplicate")
    with pytest.raises(ValueError, match="stable non-empty"):
        AccessibilityResult(
            rule_id="bad rule",
            target_id="button",
            status=AccessibilityStatus.PASS,
        )


def test_round_trip_and_derived_evidence_tampering_are_rejected() -> None:
    report = KodeAccessibility.evaluate(
        [
            _result("name.required", "button", AccessibilityStatus.PASS),
            _result("focus.keyboard", "field", AccessibilityStatus.FAIL, blocking=True),
        ],
        surface="roundtrip",
        generated_at="2026-08-22T10:01:00Z",
    )
    payload = report.to_dict()
    loaded = AccessibilityReport.from_dict(json.loads(json.dumps(payload)))
    assert loaded == report
    assert len(report.evidence_sha256) == 64

    tampered_counts = json.loads(json.dumps(payload))
    tampered_counts["counts"]["failed"] = 0
    with pytest.raises(ValueError, match="counts"):
        AccessibilityReport.from_dict(tampered_counts)

    tampered_blockers = json.loads(json.dumps(payload))
    tampered_blockers["blockers"] = []
    with pytest.raises(ValueError, match="blockers"):
        AccessibilityReport.from_dict(tampered_blockers)

    tampered_evidence = json.loads(json.dumps(payload))
    tampered_evidence["results"][0]["summary"] = "forged"
    with pytest.raises(ValueError, match="SHA-256"):
        AccessibilityReport.from_dict(tampered_evidence)


def test_r6_3_adapter_uses_stable_ids_and_does_not_emit_na_cases() -> None:
    report = KodeAccessibility.evaluate(
        [
            _result("name.required", "pass", AccessibilityStatus.PASS),
            _result("focus.visible", "warn", AccessibilityStatus.WARN),
            _result("role.exposed", "fail", AccessibilityStatus.FAIL, blocking=True),
            _result("state.known", "unknown", AccessibilityStatus.UNKNOWN),
            _result(
                "target.minimum",
                "na",
                AccessibilityStatus.NOT_APPLICABLE,
                reason="No explicit geometry source",
            ),
        ],
        surface="adapter",
    )
    cases = report.to_test_case_results()
    assert [case.id for case in cases] == [
        "accessibility:name.required:pass",
        "accessibility:focus.visible:warn",
        "accessibility:role.exposed:fail",
        "accessibility:state.known:unknown",
    ]
    assert [case.status for case in cases] == [
        TestCaseStatus.PASS,
        TestCaseStatus.SKIP,
        TestCaseStatus.FAIL,
        TestCaseStatus.ERROR,
    ]
    assert all(case.details["accessibility_evidence_sha256"] == report.evidence_sha256 for case in cases)


def test_contrast_ratio_and_explicit_contrast_check() -> None:
    assert KodeAccessibility.contrast_ratio((0, 0, 0), (255, 255, 255)) == 21.0
    passing = KodeAccessibility.check_contrast(
        target_id="body-text",
        foreground=(0, 0, 0),
        background=(255, 255, 255),
        minimum_ratio=4.5,
    )
    failing = KodeAccessibility.check_contrast(
        target_id="low-contrast",
        foreground=(120, 120, 120),
        background=(130, 130, 130),
        minimum_ratio=4.5,
    )
    assert passing.status is AccessibilityStatus.PASS
    assert failing.status is AccessibilityStatus.FAIL
    assert failing.blocking
    with pytest.raises(ValueError, match="RGB"):
        KodeAccessibility.contrast_ratio((0, 0, 300), (255, 255, 255))


def test_target_size_check_is_explicit_and_warns_when_nonblocking() -> None:
    passing = KodeAccessibility.check_target_size(
        target_id="button",
        width=24,
        height=24,
    )
    warning = KodeAccessibility.check_target_size(
        target_id="small",
        width=20,
        height=24,
    )
    blocking = KodeAccessibility.check_target_size(
        target_id="small-blocking",
        width=20,
        height=20,
        blocking=True,
    )
    assert passing.status is AccessibilityStatus.PASS
    assert warning.status is AccessibilityStatus.WARN
    assert blocking.status is AccessibilityStatus.FAIL and blocking.blocking
    assert warning.evidence["measurement"] == "direct_rectangle_only"


def test_store_round_trip_and_initialized_metadata_requirement(tmp_path: Path) -> None:
    store = AccessibilityStore(tmp_path)
    report = KodeAccessibility.evaluate(
        [_result("name.required", "button", AccessibilityStatus.PASS)],
        surface="KodeStudio Main",
        generated_at="2026-08-22T10:02:03Z",
    )
    with pytest.raises(FileNotFoundError, match="metadata"):
        store.save(report)

    (tmp_path / ".kodepoia" / "diagnostics").mkdir(parents=True)
    latest, snapshot = store.save(report)
    assert latest == tmp_path / ".kodepoia" / "diagnostics" / "accessibility" / "KodeStudio-Main-latest.json"
    assert snapshot is not None and snapshot.exists()
    assert store.load_latest("KodeStudio Main") == report


def test_store_rejects_accessibility_root_symlink_escape(tmp_path: Path) -> None:
    metadata = tmp_path / ".kodepoia"
    diagnostics = metadata / "diagnostics"
    diagnostics.mkdir(parents=True)
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir(exist_ok=True)
    link = diagnostics / "accessibility"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable on this platform: {exc}")

    store = AccessibilityStore(tmp_path)
    report = KodeAccessibility.evaluate(
        [_result("name.required", "button", AccessibilityStatus.PASS)],
        surface="escape",
    )
    with pytest.raises(ValueError, match="workspace"):
        store.save(report)


def test_json_schema_accepts_a_valid_report() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "accessibility-report-v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    report = KodeAccessibility.evaluate(
        [_result("name.required", "button", AccessibilityStatus.PASS)],
        surface="schema",
        generated_at="2026-08-22T10:03:00Z",
    )
    jsonschema.validate(instance=report.to_dict(), schema=schema)


def test_enum_values_are_stable() -> None:
    assert [item.value for item in AccessibilitySeverity] == ["info", "minor", "major", "critical"]
    assert [item.value for item in AccessibilityStatus] == [
        "unknown",
        "pass",
        "warn",
        "fail",
        "not_applicable",
    ]
    assert [item.value for item in AccessibilityReportStatus] == ["unknown", "pass", "warn", "fail"]
