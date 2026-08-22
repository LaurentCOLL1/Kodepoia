from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.quality.health import HealthDimension, HealthStatus
from kodepoia.quality.security import (
    DependencySecurityStatus,
    DependencyVulnerabilityEvidence,
    KodeAppSecurity,
    ResidualRisk,
    SecurityApplicability,
    SecurityCategory,
    SecurityCheckStatus,
    SecurityReport,
    SecurityReportStatus,
    SecurityRequirement,
    SecuritySeverity,
    SecurityStore,
    ThreatModel,
    applicable_requirement,
    kodepoia_threat_model,
    not_applicable_requirement,
    secure_storage_requirement,
)
from kodepoia.quality.tests import TestCaseStatus


NOW = "2026-08-22T12:30:00Z"


def _low_risk_model() -> ThreatModel:
    model = kodepoia_threat_model()
    return replace(
        model,
        threats=tuple(replace(item, residual_risk=ResidualRisk.LOW) for item in model.threats),
    )


def _pass_requirement() -> SecurityRequirement:
    return applicable_requirement(
        id="execution.shell-disabled",
        category=SecurityCategory.EXECUTION,
        title="Process execution does not use a command shell",
        status=SecurityCheckStatus.PASS,
        evidence_source="tests:test_process_sandbox_shell_false",
        severity=SecuritySeverity.HIGH,
        reference="v5.0.0-1.2.5",
    )


def _clear_dependency() -> DependencyVulnerabilityEvidence:
    return DependencyVulnerabilityEvidence(
        component="example-package",
        version="1.2.3",
        status=DependencySecurityStatus.CLEAR,
        checked_at=NOW,
        source="fixture:trusted-advisory-snapshot",
    )


def _pass_report() -> SecurityReport:
    return SecurityReport.build(
        "kodepoia",
        _low_risk_model(),
        (_pass_requirement(),),
        (_clear_dependency(),),
        generated_at=NOW,
    )


def test_kodepoia_threat_model_is_complete_and_cross_referenced() -> None:
    model = kodepoia_threat_model()
    model.validate()
    assert len(model.assets) >= 5
    assert len(model.trust_boundaries) >= 4
    assert len(model.entry_points) >= 5
    assert {item.id for item in model.threats} >= {
        "threat.path-traversal",
        "threat.command-injection",
        "threat.secret-disclosure",
        "threat.loopback-exposure",
        "threat.untrusted-download-execution",
    }
    assert all(item.residual_risk is ResidualRisk.UNKNOWN for item in model.threats)
    assert not model.blockers


def test_threat_model_rejects_unknown_cross_reference() -> None:
    model = kodepoia_threat_model()
    broken = replace(
        model,
        threats=(replace(model.threats[0], asset_ids=("asset.does-not-exist",)),)
        + model.threats[1:],
    )
    with pytest.raises(ValueError, match="unknown asset"):
        broken.validate()


def test_threat_model_rejects_duplicate_ids() -> None:
    model = kodepoia_threat_model()
    broken = replace(model, assets=model.assets + (model.assets[0],))
    with pytest.raises(ValueError, match="asset ids must be unique"):
        broken.validate()


def test_not_applicable_is_distinct_from_pass_and_requires_rationale() -> None:
    item = not_applicable_requirement(
        id="auth.browser-session",
        category=SecurityCategory.AUTH,
        title="Browser authentication session controls",
        rationale="Kodepoia currently exposes no browser authentication/session surface.",
    )
    assert item.applicability is SecurityApplicability.NOT_APPLICABLE
    assert item.status is SecurityCheckStatus.NOT_APPLICABLE
    assert not item.blocking

    with pytest.raises(ValueError, match="requires rationale"):
        SecurityRequirement(
            id="auth.bad-na",
            category=SecurityCategory.AUTH,
            title="Bad N/A",
            applicability=SecurityApplicability.NOT_APPLICABLE,
            status=SecurityCheckStatus.NOT_APPLICABLE,
        )


def test_applicable_requirement_cannot_hide_as_not_applicable() -> None:
    with pytest.raises(ValueError, match="applicable requirement cannot"):
        SecurityRequirement(
            id="input.bad-na",
            category=SecurityCategory.INPUT,
            title="Applicable check",
            applicability=SecurityApplicability.APPLICABLE,
            status=SecurityCheckStatus.NOT_APPLICABLE,
        )


def test_measured_requirement_requires_evidence_source() -> None:
    with pytest.raises(ValueError, match="requires evidence_source"):
        applicable_requirement(
            id="path.no-evidence",
            category=SecurityCategory.PATH,
            title="Path confinement",
            status=SecurityCheckStatus.PASS,
        )

    unknown = applicable_requirement(
        id="path.pending",
        category=SecurityCategory.PATH,
        title="Pending path evidence",
        status=SecurityCheckStatus.UNKNOWN,
    )
    assert unknown.status is SecurityCheckStatus.UNKNOWN


def test_asvs_reference_must_be_explicitly_versioned() -> None:
    item = applicable_requirement(
        id="execution.versioned",
        category=SecurityCategory.EXECUTION,
        title="Versioned ASVS reference",
        status=SecurityCheckStatus.PASS,
        evidence_source="fixture",
        reference="v5.0.0-1.2.5",
    )
    assert item.reference == "v5.0.0-1.2.5"

    with pytest.raises(ValueError, match="versioned"):
        applicable_requirement(
            id="execution.unversioned",
            category=SecurityCategory.EXECUTION,
            title="Unversioned ASVS reference",
            status=SecurityCheckStatus.PASS,
            evidence_source="fixture",
            reference="1.2.5",
        )


def test_secure_storage_helper_distinguishes_os_backed_and_plaintext() -> None:
    secure = secure_storage_requirement(
        backend="keyring",
        persists_plaintext=False,
        evidence_source="src/kodepoia/core/secrets.py:KeyringSecretBackend",
    )
    assert secure.status is SecurityCheckStatus.PASS
    assert not secure.blocking

    plaintext = secure_storage_requirement(
        backend="memory",
        persists_plaintext=True,
        evidence_source="fixture:plaintext-secret-store",
    )
    assert plaintext.status is SecurityCheckStatus.FAIL
    assert plaintext.blocking


def test_dependency_evidence_requires_timestamp_and_provenance() -> None:
    with pytest.raises(ValueError, match="timezone"):
        DependencyVulnerabilityEvidence(
            component="pkg",
            version="1",
            status=DependencySecurityStatus.UNKNOWN,
            checked_at="2026-08-22T12:00:00",
            source="fixture",
        )

    with pytest.raises(ValueError, match="provenance"):
        DependencyVulnerabilityEvidence(
            component="pkg",
            version="1",
            status=DependencySecurityStatus.UNKNOWN,
            checked_at=NOW,
            source="",
        )


def test_dependency_affected_requires_advisory_and_only_affected_can_block() -> None:
    with pytest.raises(ValueError, match="requires advisory_ids"):
        DependencyVulnerabilityEvidence(
            component="pkg",
            version="1",
            status=DependencySecurityStatus.AFFECTED,
            checked_at=NOW,
            source="fixture",
        )

    affected = DependencyVulnerabilityEvidence(
        component="pkg",
        version="1",
        status=DependencySecurityStatus.AFFECTED,
        checked_at=NOW,
        source="fixture",
        advisory_ids=("GHSA-example",),
        severity=SecuritySeverity.HIGH,
        blocking=True,
    )
    assert affected.blocking

    with pytest.raises(ValueError, match="only affected"):
        DependencyVulnerabilityEvidence(
            component="pkg",
            version="1",
            status=DependencySecurityStatus.UNKNOWN,
            checked_at=NOW,
            source="fixture",
            blocking=True,
        )

    with pytest.raises(ValueError, match="cannot carry advisory"):
        DependencyVulnerabilityEvidence(
            component="pkg",
            version="1",
            status=DependencySecurityStatus.CLEAR,
            checked_at=NOW,
            source="fixture",
            advisory_ids=("GHSA-stale",),
        )


def test_report_status_unknown_warn_pass_and_fail() -> None:
    model = kodepoia_threat_model()
    only_na = not_applicable_requirement(
        id="auth.none",
        category=SecurityCategory.AUTH,
        title="Authentication surface",
        rationale="No authentication surface exists in this fixture.",
    )
    unknown = SecurityReport.build("x", model, (only_na,), (), generated_at=NOW)
    assert unknown.status is SecurityReportStatus.UNKNOWN

    pending = applicable_requirement(
        id="network.pending",
        category=SecurityCategory.NETWORK,
        title="Network policy evidence",
        status=SecurityCheckStatus.UNKNOWN,
    )
    warn = SecurityReport.build("x", model, (pending,), (), generated_at=NOW)
    assert warn.status is SecurityReportStatus.WARN

    passed = _pass_report()
    assert passed.status is SecurityReportStatus.PASS

    failed_requirement = applicable_requirement(
        id="path.escape",
        category=SecurityCategory.PATH,
        title="Path escape detected",
        status=SecurityCheckStatus.FAIL,
        evidence_source="fixture:path-escape",
        severity=SecuritySeverity.HIGH,
        blocking=True,
    )
    failed = SecurityReport.build(
        "x",
        _low_risk_model(),
        (failed_requirement,),
        (),
        generated_at=NOW,
    )
    assert failed.status is SecurityReportStatus.FAIL
    assert failed.blockers == ("requirement:path.escape",)


def test_affected_dependency_causes_fail_even_without_explicit_blocker() -> None:
    affected = DependencyVulnerabilityEvidence(
        component="pkg",
        version="1",
        status=DependencySecurityStatus.AFFECTED,
        checked_at=NOW,
        source="fixture",
        advisory_ids=("CVE-2099-0001",),
    )
    report = SecurityReport.build("x", _low_risk_model(), (), (affected,), generated_at=NOW)
    assert report.status is SecurityReportStatus.FAIL


def test_report_round_trip_counts_blockers_and_hash() -> None:
    report = _pass_report()
    payload = report.to_dict()
    restored = SecurityReport.from_dict(payload)
    assert restored.to_dict() == payload
    assert restored.counts["pass"] == 1
    assert restored.counts["dependencies_clear"] == 1
    assert restored.counts["threats_total"] == len(kodepoia_threat_model().threats)
    assert not restored.blockers
    assert len(restored.evidence_sha256) == 64


def test_report_rejects_derived_field_and_hash_tampering() -> None:
    payload = _pass_report().to_dict()

    wrong_counts = json.loads(json.dumps(payload))
    wrong_counts["counts"]["pass"] = 99
    with pytest.raises(ValueError, match="counts"):
        SecurityReport.from_dict(wrong_counts)

    wrong_blockers = json.loads(json.dumps(payload))
    wrong_blockers["blockers"] = ["requirement:invented"]
    with pytest.raises(ValueError, match="blockers"):
        SecurityReport.from_dict(wrong_blockers)

    wrong_hash = json.loads(json.dumps(payload))
    wrong_hash["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        SecurityReport.from_dict(wrong_hash)


def test_security_details_are_recursively_redacted() -> None:
    requirement = applicable_requirement(
        id="secret.redaction",
        category=SecurityCategory.SECRET_STORAGE,
        title="Redacted evidence",
        status=SecurityCheckStatus.PASS,
        evidence_source="fixture",
        details={
            "token": "super-secret-token",
            "nested": {"message": "Authorization: Bearer abc.def.ghi"},
        },
    )
    payload = requirement.to_dict()
    assert payload["details"]["token"] == "<redacted>"
    assert "abc.def.ghi" not in json.dumps(payload)

    dependency = DependencyVulnerabilityEvidence(
        component="pkg",
        version="1",
        status=DependencySecurityStatus.UNKNOWN,
        checked_at=NOW,
        source="fixture",
        details={"password": "raw-password"},
    )
    assert dependency.to_dict()["details"]["password"] == "<redacted>"


def test_health_adapter_preserves_unknown_and_blocking_failure() -> None:
    unknown = SecurityReport.build("x", kodepoia_threat_model(), (), (), generated_at=NOW)
    unknown_metric = KodeAppSecurity.to_health_metric(unknown)
    assert unknown_metric.dimension is HealthDimension.SECURITY
    assert unknown_metric.status is HealthStatus.UNKNOWN
    assert unknown_metric.score is None

    failed_requirement = applicable_requirement(
        id="execution.blocked",
        category=SecurityCategory.EXECUTION,
        title="Unsafe execution",
        status=SecurityCheckStatus.FAIL,
        evidence_source="fixture",
        blocking=True,
    )
    failed = SecurityReport.build(
        "x", _low_risk_model(), (failed_requirement,), (), generated_at=NOW
    )
    failed_metric = KodeAppSecurity.to_health_metric(failed)
    assert failed_metric.status is HealthStatus.FAIL
    assert failed_metric.blocking
    # Score remains aggregate evidence; the blocker independently forces FAIL.
    assert failed_metric.score == 75.0


def test_test_adapter_uses_stable_ids_and_never_turns_na_into_pass() -> None:
    na = not_applicable_requirement(
        id="session.none",
        category=SecurityCategory.SESSION,
        title="Session controls",
        rationale="No session surface in fixture.",
    )
    passed = _pass_requirement()
    unknown_dep = DependencyVulnerabilityEvidence(
        component="pkg",
        version="1",
        status=DependencySecurityStatus.UNKNOWN,
        checked_at=NOW,
        source="fixture",
    )
    report = SecurityReport.build(
        "x", _low_risk_model(), (na, passed), (unknown_dep,), generated_at=NOW
    )
    cases = {item.id: item for item in KodeAppSecurity.to_test_cases(report)}
    assert cases["security:session.none"].status is TestCaseStatus.SKIP
    assert cases["security:execution.shell-disabled"].status is TestCaseStatus.PASS
    assert cases["security:dependency:pkg:1"].status is TestCaseStatus.SKIP
    assert all(
        cases[f"security:threat:{item.id}"].status is TestCaseStatus.PASS
        for item in report.threat_model.threats
    )


def test_security_store_roundtrip_requires_initialized_project(tmp_path: Path) -> None:
    report = _pass_report()
    store = SecurityStore(tmp_path)
    with pytest.raises(FileNotFoundError, match="not initialized"):
        store.save(report)

    (tmp_path / ".kodepoia").mkdir()
    latest, snapshot = store.save(report)
    assert latest.parent == tmp_path / ".kodepoia" / "diagnostics" / "security"
    assert snapshot.parent == latest.parent
    assert latest.exists() and snapshot.exists()
    assert store.load_latest("kodepoia").to_dict() == report.to_dict()


def test_security_schema_accepts_canonical_report() -> None:
    schema = json.loads(Path("schemas/security-report-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(_pass_report().to_dict())


def test_malformed_payload_variants_fail_closed() -> None:
    payload = _pass_report().to_dict()
    mutations = []

    duplicate_requirement = json.loads(json.dumps(payload))
    duplicate_requirement["requirements"].append(duplicate_requirement["requirements"][0])
    duplicate_requirement["counts"]["requirements_total"] = 2
    duplicate_requirement["counts"]["applicable"] = 2
    duplicate_requirement["counts"]["pass"] = 2
    mutations.append(duplicate_requirement)

    bad_reference = json.loads(json.dumps(payload))
    bad_reference["requirements"][0]["reference"] = "latest-1.2.5"
    mutations.append(bad_reference)

    broken_threat_ref = json.loads(json.dumps(payload))
    broken_threat_ref["threat_model"]["threats"][0]["asset_ids"] = ["asset.missing"]
    mutations.append(broken_threat_ref)

    naive_dependency_time = json.loads(json.dumps(payload))
    naive_dependency_time["dependencies"][0]["checked_at"] = "2026-08-22T12:30:00"
    mutations.append(naive_dependency_time)

    for mutated in mutations:
        with pytest.raises(ValueError):
            SecurityReport.from_dict(mutated)
