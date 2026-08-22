from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.core.backup import BackupManager
from kodepoia.quality.patch_gate import (
    GateEvidence,
    GateEvidenceStatus,
    IntegrationEvidenceStatus,
    KodePatchGate,
    PatchChange,
    PatchClassification,
    PatchDomain,
    PatchGateReport,
    PatchGateStatus,
    PatchGateStore,
    PatchOperation,
    PatchRisk,
    R6IntegrationReport,
    R6SubdivisionEvidence,
    RehearsalStatus,
    RollbackMethod,
    RollbackRehearsalEvidence,
    RollbackStrategy,
    ValidationGate,
    rehearse_fixture_rollback,
)
from kodepoia.quality.tests import TestCaseStatus


NOW = "2026-08-22T15:00:00Z"
BASE = "1" * 40
HEAD = "2" * 40
OTHER = "3" * 40


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def change(
    domain: PatchDomain = PatchDomain.CORE,
    *,
    path: str = "src/demo.py",
    operation: PatchOperation = PatchOperation.MODIFY,
    risk: PatchRisk = PatchRisk.LOW,
    platforms: tuple[str, ...] = (),
) -> PatchChange:
    return PatchChange(path, domain, operation, risk, platforms)


def evidence(
    gate: ValidationGate,
    *,
    status: GateEvidenceStatus = GateEvidenceStatus.PASS,
    head: str = HEAD,
) -> GateEvidence:
    return GateEvidence(
        gate=gate,
        status=status,
        source=f"fixture:{gate.value}",
        evidence_sha256=digest(f"evidence:{gate.value}:{status.value}"),
        source_sha=head,
        rationale=("fixture not applicable" if status is GateEvidenceStatus.NOT_APPLICABLE else ""),
    )


def rollback_strategy() -> RollbackStrategy:
    return RollbackStrategy(
        id="fixture-rollback",
        method=RollbackMethod.COMPOSITE,
        description="Restore the controlled fixture from verified snapshot/backup evidence.",
        restore_scope=("src/demo.py",),
    )


def rehearsal() -> RollbackRehearsalEvidence:
    return RollbackRehearsalEvidence(
        status=RehearsalStatus.PASS,
        source="fixture:rollback-rehearsal",
        evidence_sha256=digest("rollback-rehearsal"),
        restored_hashes_match=True,
        backup_verified=True,
        audit_chain_valid=True,
        recovery_checkpoint_cleared=True,
    )


def full_evidence(changes: tuple[PatchChange, ...]) -> tuple[GateEvidence, ...]:
    classification = KodePatchGate.classify(changes)
    return tuple(
        evidence(requirement.gate)
        for requirement in KodePatchGate.required_gates(changes, classification)
    )


def pass_major_report() -> PatchGateReport:
    changes = (change(PatchDomain.CORE),)
    return PatchGateReport.build(
        patch_id="r6-12-fixture",
        base_sha=BASE,
        head_sha=HEAD,
        changes=changes,
        evidence=full_evidence(changes),
        rollback=rollback_strategy(),
        rehearsal=rehearsal(),
        generated_at=NOW,
    )


def subdivisions(*, source_sha: str = HEAD) -> tuple[R6SubdivisionEvidence, ...]:
    values = []
    for index in range(1, 13):
        accepted = source_sha if index == 12 else f"{index:x}"[-1] * 40
        values.append(
            R6SubdivisionEvidence(
                subdivision=f"R6.{index}",
                status=IntegrationEvidenceStatus.PASS,
                source=f"fixture:R6.{index}",
                evidence_sha256=digest(f"R6.{index}"),
                accepted_head=accepted,
                manual_satisfied=True,
            )
        )
    return tuple(values)


def test_deterministic_major_minor_classification_and_triggers() -> None:
    minor = KodePatchGate.classify((change(PatchDomain.DOCUMENTATION, path="docs/readme.md"),))
    assert minor.classification is PatchClassification.MINOR
    assert not minor.triggers

    protected = KodePatchGate.classify((change(PatchDomain.CORE),))
    assert protected.classification is PatchClassification.MAJOR
    assert "protected-domain:core" in protected.triggers

    risky = KodePatchGate.classify(
        (change(PatchDomain.DOCUMENTATION, path="docs/risk.md", risk=PatchRisk.HIGH),)
    )
    assert risky.classification is PatchClassification.MAJOR
    assert "risk:high" in risky.triggers

    multi = KodePatchGate.classify(
        (
            change(PatchDomain.DOCUMENTATION, path="docs/a.md", platforms=("windows",)),
            change(PatchDomain.TESTS, path="tests/a.py", platforms=("ubuntu",)),
        )
    )
    assert multi.classification is PatchClassification.MAJOR
    assert "multi-platform-change" in multi.triggers


def test_required_gate_matrix_is_domain_driven_and_major_adds_rollback() -> None:
    changes = (change(PatchDomain.UI, risk=PatchRisk.HIGH),)
    classification = KodePatchGate.classify(changes)
    assert classification.classification is PatchClassification.MAJOR
    gates = {item.gate for item in KodePatchGate.required_gates(changes, classification)}
    assert {
        ValidationGate.TESTS,
        ValidationGate.REGRESSION,
        ValidationGate.VISUAL,
        ValidationGate.ACCESSIBILITY,
        ValidationGate.LOCALIZATION,
        ValidationGate.HEALTH,
    }.issubset(gates)
    assert ValidationGate.ROLLBACK in gates
    assert ValidationGate.TECHNICAL_DEBT in gates


def test_major_patch_requires_rollback_strategy_and_passing_rehearsal() -> None:
    changes = (change(PatchDomain.CORE),)
    ev = full_evidence(changes)
    missing = PatchGateReport.build(
        patch_id="missing-rollback",
        base_sha=BASE,
        head_sha=HEAD,
        changes=changes,
        evidence=ev,
        generated_at=NOW,
    )
    assert missing.status is PatchGateStatus.FAIL
    assert "rollback:strategy:missing" in missing.blockers
    assert "rollback:rehearsal:missing" in missing.blockers

    incomplete_strategy = RollbackStrategy(
        id="incomplete-rollback",
        method=RollbackMethod.COMPOSITE,
        description="Incomplete rollback evidence must not pass.",
        restore_scope=("src/demo.py",),
        verification_required=False,
    )
    incomplete = PatchGateReport.build(
        patch_id="incomplete-rollback",
        base_sha=BASE,
        head_sha=HEAD,
        changes=changes,
        evidence=ev,
        rollback=incomplete_strategy,
        rehearsal=rehearsal(),
        generated_at=NOW,
    )
    assert incomplete.status is PatchGateStatus.FAIL
    assert "rollback:strategy:verification-incomplete" in incomplete.blockers

    passed = pass_major_report()
    assert passed.status is PatchGateStatus.PASS
    assert not passed.blockers


def test_required_missing_skip_cancelled_and_not_applicable_fail_closed() -> None:
    changes = (change(PatchDomain.CORE),)
    baseline = list(full_evidence(changes))
    target = next(item.gate for item in baseline if item.gate is not ValidationGate.ROLLBACK)
    for bad in (
        GateEvidenceStatus.FAIL,
        GateEvidenceStatus.SKIP,
        GateEvidenceStatus.CANCELLED,
        GateEvidenceStatus.MISSING,
        GateEvidenceStatus.NOT_APPLICABLE,
    ):
        replaced = [
            evidence(item.gate, status=bad) if item.gate is target else item
            for item in baseline
        ]
        report = PatchGateReport.build(
            patch_id=f"bad-{bad.value}",
            base_sha=BASE,
            head_sha=HEAD,
            changes=changes,
            evidence=replaced,
            rollback=rollback_strategy(),
            rehearsal=rehearsal(),
            generated_at=NOW,
        )
        assert report.status is PatchGateStatus.FAIL

    omitted = [item for item in baseline if item.gate is not target]
    missing_report = PatchGateReport.build(
        patch_id="omitted-required",
        base_sha=BASE,
        head_sha=HEAD,
        changes=changes,
        evidence=omitted,
        rollback=rollback_strategy(),
        rehearsal=rehearsal(),
        generated_at=NOW,
    )
    assert missing_report.status is PatchGateStatus.FAIL


def test_warn_is_preserved_as_warn_not_fake_pass() -> None:
    changes = (change(PatchDomain.CORE),)
    baseline = list(full_evidence(changes))
    target = next(item.gate for item in baseline if item.gate is not ValidationGate.ROLLBACK)
    replaced = [
        evidence(item.gate, status=GateEvidenceStatus.WARN) if item.gate is target else item
        for item in baseline
    ]
    report = PatchGateReport.build(
        patch_id="warn-gate",
        base_sha=BASE,
        head_sha=HEAD,
        changes=changes,
        evidence=replaced,
        rollback=rollback_strategy(),
        rehearsal=rehearsal(),
        generated_at=NOW,
    )
    assert report.status is PatchGateStatus.WARN
    assert KodePatchGate.to_health_metric(report).status.value == "warn"


def test_measured_evidence_must_bind_source_sha_and_digest_and_report_checks_head() -> None:
    changes = (change(PatchDomain.CORE),)
    required = KodePatchGate.required_gates(changes, KodePatchGate.classify(changes))
    target = required[0].gate

    wrong_sha = [
        evidence(item.gate, head=OTHER if item.gate is target else HEAD)
        for item in required
    ]
    with pytest.raises(ValueError, match="head_sha"):
        PatchGateReport.build(
            patch_id="wrong-source",
            base_sha=BASE,
            head_sha=HEAD,
            changes=changes,
            evidence=wrong_sha,
            rollback=rollback_strategy(),
            rehearsal=rehearsal(),
            generated_at=NOW,
        )

    with pytest.raises(ValueError, match="source_sha"):
        GateEvidence(
            gate=target,
            status=GateEvidenceStatus.PASS,
            source="fixture:unbound-source",
            evidence_sha256=digest("unbound-source"),
            source_sha="",
        )

    with pytest.raises(ValueError, match="evidence_sha256"):
        GateEvidence(
            gate=target,
            status=GateEvidenceStatus.PASS,
            source="fixture:unbound-digest",
            evidence_sha256="",
            source_sha=HEAD,
        )


def test_patch_paths_reject_parent_absolute_and_windows_drive_escape() -> None:
    with pytest.raises(ValueError, match="safe"):
        change(path="../outside.txt")
    with pytest.raises(ValueError, match="safe"):
        change(path="/tmp/outside.txt")
    with pytest.raises(ValueError, match="safe"):
        change(path="C:/Windows/System32/demo.dll")
    with pytest.raises(ValueError, match="safe"):
        change(path=r"D:\outside\demo.dll")


def test_roundtrip_and_tamper_rejection() -> None:
    report = pass_major_report()
    payload = report.to_dict()
    assert PatchGateReport.from_dict(payload).to_dict() == payload

    wrong_hash = json.loads(json.dumps(payload))
    wrong_hash["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        PatchGateReport.from_dict(wrong_hash)

    wrong_status = json.loads(json.dumps(payload))
    wrong_status["status"] = "warn"
    with pytest.raises(ValueError, match="status"):
        PatchGateReport.from_dict(wrong_status)

    wrong_classification = json.loads(json.dumps(payload))
    wrong_classification["classification"] = {"classification": "minor", "triggers": []}
    with pytest.raises(ValueError, match="classification"):
        PatchGateReport.from_dict(wrong_classification)


def test_r6_3_adapter_preserves_required_gate_failures() -> None:
    report = pass_major_report()
    cases = {item.id: item for item in KodePatchGate.to_test_cases(report)}
    assert all(item.status is TestCaseStatus.PASS for item in cases.values())

    changes = (change(PatchDomain.CORE),)
    required = KodePatchGate.required_gates(changes, KodePatchGate.classify(changes))
    target = required[0].gate
    ev = [
        evidence(item.gate, status=GateEvidenceStatus.CANCELLED if item.gate is target else GateEvidenceStatus.PASS)
        for item in required
    ]
    failed = PatchGateReport.build(
        patch_id="cancelled-case",
        base_sha=BASE,
        head_sha=HEAD,
        changes=changes,
        evidence=ev,
        rollback=rollback_strategy(),
        rehearsal=rehearsal(),
        generated_at=NOW,
    )
    failed_cases = {item.id: item for item in KodePatchGate.to_test_cases(failed)}
    assert failed_cases[f"patch-gate:{target.value}"].status is TestCaseStatus.FAIL


def test_fixture_rollback_rehearsal_restores_exact_file_set_and_hashes(tmp_path: Path) -> None:
    project = tmp_path / "fixture-project"
    support = tmp_path / "support"
    (project / "src").mkdir(parents=True)
    (project / ".kodepoia-r6-rollback-fixture").write_text("fixture\n", encoding="utf-8")
    target = project / "src" / "demo.txt"
    target.write_text("original\n", encoding="utf-8")
    (project / "keep.txt").write_text("keep\n", encoding="utf-8")
    before = {
        path.relative_to(project).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(project.rglob("*"))
        if path.is_file()
    }

    result = rehearse_fixture_rollback(project, support, "src/demo.txt")
    after = {
        path.relative_to(project).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(project.rglob("*"))
        if path.is_file()
    }
    assert result.status is RehearsalStatus.PASS
    assert result.restored_hashes_match
    assert result.backup_verified
    assert result.audit_chain_valid
    assert result.recovery_checkpoint_cleared
    assert before == after
    assert target.read_text(encoding="utf-8") == "original\n"
    assert (support / "audit.jsonl").is_file()
    assert not (support / "recovery.json").exists()


def test_fixture_rollback_rehearsal_refuses_realish_or_escaped_targets(tmp_path: Path) -> None:
    project = tmp_path / "project"
    support = tmp_path / "support"
    project.mkdir()
    (project / "demo.txt").write_text("x", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        rehearse_fixture_rollback(project, support, "demo.txt")

    (project / ".kodepoia-r6-rollback-fixture").write_text("fixture", encoding="utf-8")
    with pytest.raises(ValueError, match="safe"):
        rehearse_fixture_rollback(project, support, "../outside.txt")
    with pytest.raises(ValueError, match="outside"):
        rehearse_fixture_rollback(project, project / "support", "demo.txt")


def test_corrupted_backup_fails_closed(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "demo.txt").write_text("original", encoding="utf-8")
    manager = BackupManager(tmp_path / "backups")
    archive = manager.create_archive(project, "fixture")
    assert manager.verify(archive)
    archive.write_bytes(b"corrupt-not-a-zip")
    assert not manager.verify(archive)
    with pytest.raises(ValueError, match="invalid or corrupted"):
        manager.restore(archive, tmp_path / "restore")


def test_patch_gate_store_requires_initialized_metadata_and_roundtrips(tmp_path: Path) -> None:
    report = pass_major_report()
    store = PatchGateStore(tmp_path)
    with pytest.raises(FileNotFoundError):
        store.save(report)
    (tmp_path / ".kodepoia").mkdir()
    latest, snapshot = store.save(report)
    assert latest.is_file() and snapshot.is_file()
    assert latest.is_relative_to(tmp_path)
    assert store.load_latest(report.patch_id).to_dict() == report.to_dict()


def test_r6_integration_requires_all_subdivisions_manual_satisfaction_and_exact_r6_12_head() -> None:
    report = R6IntegrationReport.build(HEAD, subdivisions(source_sha=HEAD), generated_at=NOW)
    assert report.status is IntegrationEvidenceStatus.PASS
    assert not report.blockers

    missing = R6IntegrationReport.build(HEAD, subdivisions(source_sha=HEAD)[:-1], generated_at=NOW)
    assert missing.status is IntegrationEvidenceStatus.FAIL
    assert "R6.12:missing" in missing.blockers

    pending_values = list(subdivisions(source_sha=HEAD))
    pending_values[4] = R6SubdivisionEvidence(
        subdivision="R6.5",
        status=IntegrationEvidenceStatus.PASS,
        source="fixture:R6.5",
        evidence_sha256=digest("R6.5"),
        accepted_head="5" * 40,
        manual_satisfied=False,
    )
    pending = R6IntegrationReport.build(HEAD, pending_values, generated_at=NOW)
    assert pending.status is IntegrationEvidenceStatus.FAIL
    assert "R6.5:manual-pending" in pending.blockers

    with pytest.raises(ValueError, match="accepted_head"):
        R6SubdivisionEvidence(
            subdivision="R6.6",
            status=IntegrationEvidenceStatus.PASS,
            source="fixture:R6.6",
            evidence_sha256=digest("R6.6"),
            accepted_head="",
        )

    stale_values = list(subdivisions(source_sha=HEAD))
    stale_values[-1] = R6SubdivisionEvidence(
        subdivision="R6.12",
        status=IntegrationEvidenceStatus.PASS,
        source="fixture:R6.12",
        evidence_sha256=digest("R6.12"),
        accepted_head=OTHER,
    )
    with pytest.raises(ValueError, match="source_sha"):
        R6IntegrationReport.build(HEAD, stale_values, generated_at=NOW)


def test_r6_integration_roundtrip_and_tamper_rejection() -> None:
    report = R6IntegrationReport.build(HEAD, subdivisions(source_sha=HEAD), generated_at=NOW)
    payload = report.to_dict()
    assert R6IntegrationReport.from_dict(payload).to_dict() == payload

    wrong_hash = json.loads(json.dumps(payload))
    wrong_hash["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        R6IntegrationReport.from_dict(wrong_hash)

    wrong_manual = json.loads(json.dumps(payload))
    wrong_manual["subdivisions"][0]["manual_satisfied"] = False
    with pytest.raises(ValueError):
        R6IntegrationReport.from_dict(wrong_manual)


def test_json_schemas_accept_canonical_reports() -> None:
    root = Path(__file__).resolve().parents[1]
    patch_schema = json.loads(
        (root / "schemas" / "patch-gate-report-v1.schema.json").read_text(encoding="utf-8")
    )
    integration_schema = json.loads(
        (root / "schemas" / "r6-integration-report-v1.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(patch_schema).validate(pass_major_report().to_dict())
    Draft202012Validator(integration_schema).validate(
        R6IntegrationReport.build(HEAD, subdivisions(source_sha=HEAD), generated_at=NOW).to_dict()
    )
