from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from kodepoia.kodecode.workspace import WorkspaceViolation
from kodepoia.quality.health import HealthDimension, HealthStatus
from kodepoia.quality.regression import KodeRegression, RegressionStatus
from kodepoia.quality.technical_debt import (
    DebtCategory,
    DebtReference,
    DebtReferenceKind,
    DebtSeverity,
    DebtState,
    KodeTechnicalDebt,
    TechnicalDebtItem,
    TechnicalDebtReport,
    TechnicalDebtStatus,
    TechnicalDebtStore,
)
from kodepoia.quality.tests import KodeTests, TestCaseStatus


T0 = "2026-08-22T10:00:00Z"
T1 = "2026-08-22T11:00:00Z"
T2 = "2026-08-22T12:00:00Z"


def _item(
    debt_id: str = "DEBT-001",
    *,
    state: DebtState = DebtState.OPEN,
    blocking: bool = False,
    severity: DebtSeverity = DebtSeverity.MEDIUM,
    summary: str = "Replace deprecated API",
    scope: str = "src/example.py",
    accepted_rationale: str = "",
    resolved_at: str | None = None,
    first_seen: str = T0,
    last_seen: str = T1,
    references: tuple[DebtReference, ...] | None = None,
) -> TechnicalDebtItem:
    return TechnicalDebtItem(
        id=debt_id,
        category=DebtCategory.CODE_QUALITY,
        severity=severity,
        summary=summary,
        scope=scope,
        source="pytest-warning",
        provenance="GitHub Actions Python Core log",
        impact=4,
        probability=3,
        effort=2,
        first_seen=first_seen,
        last_seen=last_seen,
        state=state,
        owner="quality",
        references=references or (DebtReference(DebtReferenceKind.FILE, scope),),
        blocking=blocking,
        accepted_rationale=accepted_rationale,
        resolved_at=resolved_at,
    )


def test_priority_is_deterministic_and_bounded() -> None:
    item = _item(severity=DebtSeverity.CRITICAL)
    assert item.priority_score == 24.0
    maximum = TechnicalDebtItem(
        id="MAX",
        category=DebtCategory.SECURITY,
        severity=DebtSeverity.CRITICAL,
        summary="Critical",
        scope="core",
        source="fixture",
        provenance="test",
        impact=5,
        probability=5,
        effort=1,
        first_seen=T0,
        last_seen=T0,
    )
    assert maximum.priority_score == 100.0


def test_fingerprint_is_stable_across_lifecycle_and_timestamps() -> None:
    open_item = _item(first_seen=T0, last_seen=T1)
    accepted = _item(
        state=DebtState.ACCEPTED,
        first_seen=T0,
        last_seen=T2,
        accepted_rationale="Temporary compatibility debt with review plan",
    )
    resolved = _item(
        state=DebtState.RESOLVED,
        first_seen=T0,
        last_seen=T2,
        resolved_at=T2,
    )
    assert open_item.fingerprint == accepted.fingerprint == resolved.fingerprint


def test_lifecycle_invariants() -> None:
    with pytest.raises(ValueError, match="accepted_rationale"):
        _item(state=DebtState.ACCEPTED)
    with pytest.raises(ValueError, match="cannot remain blocking"):
        _item(
            state=DebtState.ACCEPTED,
            blocking=True,
            accepted_rationale="Accepted temporarily",
        )
    with pytest.raises(ValueError, match="requires resolved_at"):
        _item(state=DebtState.RESOLVED)
    with pytest.raises(ValueError, match="open debt cannot have resolved_at"):
        _item(resolved_at=T2)
    with pytest.raises(ValueError, match="last_seen"):
        _item(first_seen=T2, last_seen=T0)


def test_duplicate_references_and_fingerprints_rejected() -> None:
    ref = DebtReference(DebtReferenceKind.FILE, "src/x.py")
    with pytest.raises(ValueError, match="references"):
        _item(references=(ref, ref))

    one = _item("DEBT-001")
    two = _item("DEBT-002")
    with pytest.raises(ValueError, match="fingerprints"):
        TechnicalDebtReport.build("Kodepoia", (one, two))


def test_report_status_and_ranking() -> None:
    assert TechnicalDebtReport.build("Kodepoia", ()).status is TechnicalDebtStatus.PASS

    low = _item("LOW", severity=DebtSeverity.LOW, summary="Low debt", scope="a.py")
    high = _item("HIGH", severity=DebtSeverity.CRITICAL, summary="High debt", scope="b.py")
    accepted = _item(
        "ACCEPTED",
        state=DebtState.ACCEPTED,
        summary="Accepted debt",
        scope="c.py",
        accepted_rationale="Known temporary debt",
    )
    report = TechnicalDebtReport.build("Kodepoia", (low, accepted, high))
    assert report.status is TechnicalDebtStatus.WARN
    assert report.ranked_active_ids[0] == "HIGH"
    assert report.counts == {"total": 3, "open": 2, "accepted": 1, "resolved": 0, "blocking": 0}
    assert report.debt_penalty > 0

    blocker = _item("BLOCK", blocking=True, summary="Blocking", scope="d.py")
    failing = TechnicalDebtReport.build("Kodepoia", (blocker,))
    assert failing.status is TechnicalDebtStatus.FAIL
    assert failing.blockers == ("BLOCK",)


def test_resolved_only_report_passes_but_retains_history() -> None:
    resolved = _item(state=DebtState.RESOLVED, resolved_at=T2, last_seen=T2)
    report = TechnicalDebtReport.build("Kodepoia", (resolved,))
    assert report.status is TechnicalDebtStatus.PASS
    assert report.counts["resolved"] == 1
    assert report.items[0].summary == "Replace deprecated API"


def test_report_roundtrip_and_derived_tamper_rejection() -> None:
    report = TechnicalDebtReport.build("Kodepoia", (_item(),))
    restored = TechnicalDebtReport.from_dict(report.to_dict())
    assert restored.to_dict() == report.to_dict()

    payload = report.to_dict()
    payload["counts"]["open"] = 99
    with pytest.raises(ValueError, match="counts"):
        TechnicalDebtReport.from_dict(payload)

    payload = report.to_dict()
    payload["ranked_active_ids"] = []
    with pytest.raises(ValueError, match="ranking"):
        TechnicalDebtReport.from_dict(payload)

    payload = report.to_dict()
    payload["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash"):
        TechnicalDebtReport.from_dict(payload)

    payload = report.to_dict()
    payload["items"][0]["fingerprint"] = "0" * 64
    with pytest.raises(ValueError, match="fingerprint"):
        TechnicalDebtReport.from_dict(payload)


def test_health_adapter_preserves_blocking_and_penalty() -> None:
    report = TechnicalDebtReport.build("Kodepoia", (_item(blocking=True),))
    metric = KodeTechnicalDebt.to_health_metric(report)
    assert metric.dimension is HealthDimension.TECHNICAL_DEBT
    assert metric.status is HealthStatus.FAIL
    assert metric.blocking is True
    assert metric.score is not None and metric.score < 100
    assert metric.details["blockers"] == ["DEBT-001"]

    clean = KodeTechnicalDebt.to_health_metric(TechnicalDebtReport.build("Kodepoia", ()))
    assert clean.status is HealthStatus.PASS
    assert clean.score == 100.0


def test_r6_3_adapter_and_new_blocking_debt_is_regression() -> None:
    baseline_report = TechnicalDebtReport.build("Kodepoia", ())
    current_report = TechnicalDebtReport.build("Kodepoia", (_item(blocking=True),))

    baseline = KodeTests.evaluate(
        KodeTechnicalDebt.to_test_cases(baseline_report),
        suite="technical-debt",
        generated_at=T0,
    )
    current = KodeTests.evaluate(
        KodeTechnicalDebt.to_test_cases(current_report),
        suite="technical-debt",
        generated_at=T1,
    )
    assert current.results[0].status is TestCaseStatus.FAIL
    regression = KodeRegression.compare(baseline, current, generated_at=T2)
    assert regression.status is RegressionStatus.FAIL
    assert regression.regressions == ("technical-debt:DEBT-001",)


def test_accepted_is_not_resolved_in_test_adapter() -> None:
    accepted = _item(
        state=DebtState.ACCEPTED,
        accepted_rationale="Temporary compatibility debt",
    )
    resolved = _item(
        "RESOLVED",
        state=DebtState.RESOLVED,
        summary="Resolved debt",
        scope="resolved.py",
        resolved_at=T2,
        last_seen=T2,
    )
    report = TechnicalDebtReport.build("Kodepoia", (accepted, resolved))
    cases = {case.id: case for case in KodeTechnicalDebt.to_test_cases(report)}
    assert cases["technical-debt:DEBT-001"].status is TestCaseStatus.SKIP
    assert cases["technical-debt:RESOLVED"].status is TestCaseStatus.PASS


def test_store_is_confined_and_roundtrips(tmp_path: Path) -> None:
    (tmp_path / ".kodepoia").mkdir()
    report = TechnicalDebtReport.build("Kodepoia", (_item(),))
    store = TechnicalDebtStore(tmp_path)
    latest, snapshot = store.save(report)
    assert latest.is_file() and snapshot.is_file()
    assert latest.parent == tmp_path / ".kodepoia" / "diagnostics" / "technical_debt"
    assert store.load_latest("Kodepoia").to_dict() == report.to_dict()


def test_store_rejects_symlink_escape(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("symlink creation may require elevated Windows policy")
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / ".kodepoia").mkdir()
    (tmp_path / ".kodepoia" / "diagnostics").symlink_to(outside, target_is_directory=True)
    with pytest.raises(WorkspaceViolation):
        TechnicalDebtStore(tmp_path)


def test_json_serialization_is_stable() -> None:
    report = TechnicalDebtReport.build("Kodepoia", (_item(),))
    encoded = json.dumps(report.to_dict(), sort_keys=True)
    assert "DEBT-001" in encoded
    assert report.evidence_sha256 in encoded
