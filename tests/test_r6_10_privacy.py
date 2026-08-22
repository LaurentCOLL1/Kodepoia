from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.quality.health import HealthDimension, HealthStatus
from kodepoia.quality.privacy import (
    DeclarationValue,
    KodePrivacy,
    PrivacyApplicability,
    PrivacyBasisState,
    PrivacyCheckStatus,
    PrivacyDataItem,
    PrivacyDisposition,
    PrivacyIssue,
    PrivacyReport,
    PrivacyReportStatus,
    PrivacySensitivity,
    PrivacySeverity,
    PrivacyStore,
    StoreKind,
    StorePrivacyDeclaration,
    redact_privacy_evidence,
)
from kodepoia.quality.tests import TestCaseStatus


NOW = "2026-08-22T13:00:00Z"


def collected_item(
    *,
    item_id: str = "data.diagnostics",
    platforms: tuple[str, ...] = ("android", "ios"),
    basis_state: PrivacyBasisState = PrivacyBasisState.DECLARED,
    sensitivity: PrivacySensitivity = PrivacySensitivity.PERSONAL,
) -> PrivacyDataItem:
    kwargs: dict[str, str] = {}
    if basis_state is PrivacyBasisState.DECLARED:
        kwargs = {
            "legal_basis": "declared-by-project-owner",
            "basis_source": "fixture:privacy-policy-draft",
        }
    elif basis_state is PrivacyBasisState.NOT_APPLICABLE:
        kwargs = {"basis_rationale": "Fixture explicitly marks this basis as not applicable."}
    return PrivacyDataItem(
        id=item_id,
        category="diagnostics",
        disposition=PrivacyDisposition.COLLECTED,
        platform_scope=platforms,
        evidence_source="fixture:data-flow-review",
        data_source="application diagnostics",
        purpose="diagnose application failures",
        storage=("local project metadata",),
        recipients=("project owner",),
        retention="until project diagnostic history is removed",
        deletion="delete diagnostic history from project metadata",
        sensitivity=sensitivity,
        basis_state=basis_state,
        **kwargs,
    )


def none_item(*, item_id: str = "data.ads", platforms: tuple[str, ...] = ("android", "ios")) -> PrivacyDataItem:
    return PrivacyDataItem(
        id=item_id,
        category="advertising",
        disposition=PrivacyDisposition.NONE,
        platform_scope=platforms,
        evidence_source="fixture:no-advertising-data-flow",
        rationale="Fixture has no advertising data collection.",
    )


def apple_declaration(item_id: str = "data.diagnostics", *, ready: bool = True) -> StorePrivacyDeclaration:
    return StorePrivacyDeclaration(
        platform="ios",
        store=StoreKind.APPLE_APP_STORE,
        data_category_id=item_id,
        collected=DeclarationValue.YES,
        linked_to_user=DeclarationValue.NO if ready else DeclarationValue.UNKNOWN,
        tracking=DeclarationValue.NO if ready else DeclarationValue.UNKNOWN,
        purposes=("app_functionality",),
        source="fixture:apple-privacy-preparation",
    )


def google_declaration(item_id: str = "data.diagnostics", *, ready: bool = True) -> StorePrivacyDeclaration:
    return StorePrivacyDeclaration(
        platform="android",
        store=StoreKind.GOOGLE_PLAY,
        data_category_id=item_id,
        collected=DeclarationValue.YES,
        shared=DeclarationValue.NO if ready else DeclarationValue.UNKNOWN,
        optional_collection=DeclarationValue.NO if ready else DeclarationValue.UNKNOWN,
        purposes=("app_functionality",),
        source="fixture:google-data-safety-preparation",
    )


def pass_issue() -> PrivacyIssue:
    return PrivacyIssue(
        id="issue.lifecycle-documented",
        title="Lifecycle metadata is documented",
        applicability=PrivacyApplicability.APPLICABLE,
        status=PrivacyCheckStatus.PASS,
        evidence_source="fixture:lifecycle-check",
    )


def pass_report() -> PrivacyReport:
    return PrivacyReport.build(
        "kodepoia",
        ("android", "ios"),
        (collected_item(), none_item()),
        (pass_issue(),),
        (apple_declaration(), google_declaration()),
        generated_at=NOW,
    )


def test_collected_item_requires_explicit_lifecycle_fields() -> None:
    with pytest.raises(ValueError, match="purpose"):
        PrivacyDataItem(
            id="data.bad",
            category="diagnostics",
            disposition=PrivacyDisposition.COLLECTED,
            platform_scope=("android",),
            evidence_source="fixture",
            data_source="app",
            purpose="",
            storage=("local",),
            retention="one day",
            deletion="automatic",
        )

    with pytest.raises(ValueError, match="storage"):
        replace(collected_item(), storage=())
    with pytest.raises(ValueError, match="retention"):
        replace(collected_item(), retention="")
    with pytest.raises(ValueError, match="deletion"):
        replace(collected_item(), deletion="")


def test_none_and_not_applicable_are_explicit_and_cannot_carry_collection_fields() -> None:
    item = none_item()
    assert item.disposition is PrivacyDisposition.NONE

    with pytest.raises(ValueError, match="requires rationale"):
        replace(item, rationale="")
    with pytest.raises(ValueError, match="cannot carry collection lifecycle"):
        replace(item, purpose="advertising")

    na = PrivacyDataItem(
        id="data.health",
        category="health",
        disposition=PrivacyDisposition.NOT_APPLICABLE,
        platform_scope=("android",),
        evidence_source="fixture:not-applicable",
        rationale="Product has no health-data feature.",
    )
    assert na.disposition is PrivacyDisposition.NOT_APPLICABLE


def test_basis_is_declared_unspecified_or_not_applicable_never_inferred() -> None:
    unspecified = collected_item(basis_state=PrivacyBasisState.UNSPECIFIED)
    assert unspecified.legal_basis == ""
    assert unspecified.consent_basis == ""

    with pytest.raises(ValueError, match="requires legal_basis or consent_basis"):
        replace(collected_item(), legal_basis="", consent_basis="")
    with pytest.raises(ValueError, match="requires basis_source"):
        replace(collected_item(), basis_source="")

    not_applicable = collected_item(basis_state=PrivacyBasisState.NOT_APPLICABLE)
    assert not_applicable.basis_state is PrivacyBasisState.NOT_APPLICABLE

    with pytest.raises(ValueError, match="requires rationale"):
        replace(not_applicable, basis_rationale="")


def test_privacy_evidence_redacts_secrets_and_personal_samples() -> None:
    payload = redact_privacy_evidence(
        {
            "token": "secret-token",
            "raw_value": "alice@example.com",
            "nested": {
                "message": "Contact alice@example.com from 192.168.1.42",
                "user_content": "private text",
            },
        }
    )
    encoded = json.dumps(payload)
    assert "secret-token" not in encoded
    assert "alice@example.com" not in encoded
    assert "192.168.1.42" not in encoded
    assert "private text" not in encoded
    assert payload["raw_value"] == "<redacted-personal-data>"


def test_issue_applicability_and_measurement_fail_closed() -> None:
    na = PrivacyIssue(
        id="issue.ads",
        title="Advertising privacy issue",
        applicability=PrivacyApplicability.NOT_APPLICABLE,
        status=PrivacyCheckStatus.NOT_APPLICABLE,
        rationale="No advertising surface.",
    )
    assert not na.blocking

    with pytest.raises(ValueError, match="requires rationale"):
        replace(na, rationale="")
    with pytest.raises(ValueError, match="requires evidence_source"):
        PrivacyIssue(
            id="issue.unproven",
            title="Unproven result",
            applicability=PrivacyApplicability.APPLICABLE,
            status=PrivacyCheckStatus.PASS,
        )
    with pytest.raises(ValueError, match="only failed"):
        replace(pass_issue(), blocking=True)


def test_store_declaration_readiness_is_platform_specific() -> None:
    assert apple_declaration().ready
    assert google_declaration().ready
    assert not apple_declaration(ready=False).ready
    assert not google_declaration(ready=False).ready

    with pytest.raises(ValueError, match="Apple privacy declaration"):
        StorePrivacyDeclaration(
            platform="android",
            store=StoreKind.APPLE_APP_STORE,
            data_category_id="data.diagnostics",
            collected=DeclarationValue.YES,
            linked_to_user=DeclarationValue.NO,
            tracking=DeclarationValue.NO,
            purposes=("app_functionality",),
            source="fixture",
        )
    with pytest.raises(ValueError, match="Google Play"):
        replace(google_declaration(), platform="ios")


def test_store_declaration_collection_state_cannot_contradict_inventory() -> None:
    bad = replace(apple_declaration(), collected=DeclarationValue.NO, purposes=())
    with pytest.raises(ValueError, match="contradicts inventory"):
        PrivacyReport.build(
            "x", ("android", "ios"), (collected_item(),), declarations=(bad,), generated_at=NOW
        )


def test_declaration_must_reference_known_category_and_matching_platform() -> None:
    unknown = replace(apple_declaration(), data_category_id="data.unknown")
    with pytest.raises(ValueError, match="unknown data category"):
        PrivacyReport.build(
            "x", ("android", "ios"), (collected_item(),), declarations=(unknown,), generated_at=NOW
        )

    android_only = collected_item(platforms=("android",))
    with pytest.raises(ValueError, match="outside data-category scope"):
        PrivacyReport.build(
            "x", ("android", "ios"), (android_only,), declarations=(apple_declaration(),), generated_at=NOW
        )


def test_report_status_unknown_warn_pass_and_fail() -> None:
    unknown = PrivacyReport.build("x", ("android",), (), generated_at=NOW)
    assert unknown.status is PrivacyReportStatus.UNKNOWN

    warn = PrivacyReport.build(
        "x",
        ("android", "ios"),
        (collected_item(basis_state=PrivacyBasisState.UNSPECIFIED),),
        declarations=(apple_declaration(), google_declaration()),
        generated_at=NOW,
    )
    assert warn.status is PrivacyReportStatus.WARN

    passed = pass_report()
    assert passed.status is PrivacyReportStatus.PASS

    failed_issue = PrivacyIssue(
        id="issue.raw-personal-data",
        title="Raw personal data in diagnostic evidence",
        applicability=PrivacyApplicability.APPLICABLE,
        status=PrivacyCheckStatus.FAIL,
        severity=PrivacySeverity.HIGH,
        evidence_source="fixture:privacy-audit",
        blocking=True,
    )
    failed = PrivacyReport.build(
        "x", ("android", "ios"), (collected_item(),), (failed_issue,), generated_at=NOW
    )
    assert failed.status is PrivacyReportStatus.FAIL
    assert failed.blockers == ("issue:issue.raw-personal-data",)


def test_unknown_sensitivity_and_pending_store_declaration_warn() -> None:
    unknown_sensitivity = PrivacyReport.build(
        "x",
        ("android", "ios"),
        (collected_item(sensitivity=PrivacySensitivity.UNKNOWN),),
        declarations=(apple_declaration(), google_declaration()),
        generated_at=NOW,
    )
    assert unknown_sensitivity.status is PrivacyReportStatus.WARN

    pending = PrivacyReport.build(
        "x",
        ("android", "ios"),
        (collected_item(),),
        declarations=(apple_declaration(ready=False), google_declaration()),
        generated_at=NOW,
    )
    assert pending.status is PrivacyReportStatus.WARN


def test_none_only_inventory_is_evidence_backed_pass_not_fake_collection() -> None:
    item = none_item(platforms=("android",))
    declaration = StorePrivacyDeclaration(
        platform="android",
        store=StoreKind.GOOGLE_PLAY,
        data_category_id=item.id,
        collected=DeclarationValue.NO,
        shared=DeclarationValue.NO,
        optional_collection=DeclarationValue.NO,
        source="fixture:no-collection-declaration",
    )
    report = PrivacyReport.build(
        "x", ("android",), (item,), declarations=(declaration,), generated_at=NOW
    )
    assert report.status is PrivacyReportStatus.PASS
    cases = {case.id: case for case in KodePrivacy.to_test_cases(report)}
    assert cases[f"privacy:data:{item.id}"].status is TestCaseStatus.SKIP
    assert cases[f"privacy:store:{declaration.id}"].status is TestCaseStatus.PASS


def test_report_roundtrip_counts_hash_and_blockers() -> None:
    report = pass_report()
    payload = report.to_dict()
    restored = PrivacyReport.from_dict(payload)
    assert restored.to_dict() == payload
    assert restored.counts["inventory_total"] == 2
    assert restored.counts["collected"] == 1
    assert restored.counts["none"] == 1
    assert restored.counts["declarations_ready"] == 2
    assert not restored.blockers
    assert len(restored.evidence_sha256) == 64


def test_report_rejects_counts_blockers_readiness_and_hash_tampering() -> None:
    payload = pass_report().to_dict()

    wrong_counts = json.loads(json.dumps(payload))
    wrong_counts["counts"]["collected"] = 99
    with pytest.raises(ValueError, match="counts"):
        PrivacyReport.from_dict(wrong_counts)

    wrong_blockers = json.loads(json.dumps(payload))
    wrong_blockers["blockers"] = ["issue:invented"]
    with pytest.raises(ValueError, match="blockers"):
        PrivacyReport.from_dict(wrong_blockers)

    wrong_ready = json.loads(json.dumps(payload))
    wrong_ready["declarations"][0]["ready"] = False
    with pytest.raises(ValueError, match="readiness"):
        PrivacyReport.from_dict(wrong_ready)

    wrong_hash = json.loads(json.dumps(payload))
    wrong_hash["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        PrivacyReport.from_dict(wrong_hash)


def test_duplicate_ids_and_declarations_are_rejected() -> None:
    item = collected_item()
    with pytest.raises(ValueError, match="inventory ids"):
        PrivacyReport.build("x", ("android", "ios"), (item, item), generated_at=NOW)

    declaration = apple_declaration()
    with pytest.raises(ValueError, match="declaration identities"):
        PrivacyReport.build(
            "x",
            ("android", "ios"),
            (item,),
            declarations=(declaration, declaration),
            generated_at=NOW,
        )


def test_health_adapter_preserves_unknown_warn_pass_and_blocking_fail() -> None:
    unknown = PrivacyReport.build("x", ("android",), (), generated_at=NOW)
    unknown_metric = KodePrivacy.to_health_metric(unknown)
    assert unknown_metric.dimension is HealthDimension.PRIVACY
    assert unknown_metric.status is HealthStatus.UNKNOWN
    assert unknown_metric.score is None

    warn = PrivacyReport.build(
        "x",
        ("android", "ios"),
        (collected_item(basis_state=PrivacyBasisState.UNSPECIFIED),),
        generated_at=NOW,
    )
    assert KodePrivacy.to_health_metric(warn).status is HealthStatus.WARN

    passed_metric = KodePrivacy.to_health_metric(pass_report())
    assert passed_metric.status is HealthStatus.PASS
    assert passed_metric.score == 100.0

    failed_issue = PrivacyIssue(
        id="issue.blocker",
        title="Blocking privacy defect",
        applicability=PrivacyApplicability.APPLICABLE,
        status=PrivacyCheckStatus.FAIL,
        evidence_source="fixture",
        blocking=True,
    )
    failed = PrivacyReport.build(
        "x", ("android", "ios"), (collected_item(),), (failed_issue,), generated_at=NOW
    )
    failed_metric = KodePrivacy.to_health_metric(failed)
    assert failed_metric.status is HealthStatus.FAIL
    assert failed_metric.blocking


def test_r6_3_adapter_uses_stable_ids_and_unknown_or_na_never_pass() -> None:
    item = collected_item(basis_state=PrivacyBasisState.UNSPECIFIED)
    na_issue = PrivacyIssue(
        id="issue.ads",
        title="Ads",
        applicability=PrivacyApplicability.NOT_APPLICABLE,
        status=PrivacyCheckStatus.NOT_APPLICABLE,
        rationale="No ads.",
    )
    pending = apple_declaration(ready=False)
    report = PrivacyReport.build(
        "x",
        ("android", "ios"),
        (item,),
        (na_issue,),
        (pending,),
        generated_at=NOW,
    )
    cases = {case.id: case for case in KodePrivacy.to_test_cases(report)}
    assert cases[f"privacy:data:{item.id}"].status is TestCaseStatus.SKIP
    assert cases["privacy:issue:issue.ads"].status is TestCaseStatus.SKIP
    assert cases[f"privacy:store:{pending.id}"].status is TestCaseStatus.SKIP


def test_privacy_store_roundtrip_requires_initialized_project(tmp_path: Path) -> None:
    report = pass_report()
    store = PrivacyStore(tmp_path)
    with pytest.raises(FileNotFoundError, match="not initialized"):
        store.save(report)

    (tmp_path / ".kodepoia").mkdir()
    latest, snapshot = store.save(report)
    expected = tmp_path / ".kodepoia" / "diagnostics" / "privacy"
    assert latest.parent == expected
    assert snapshot.parent == expected
    assert latest.exists() and snapshot.exists()
    assert store.load_latest("kodepoia").to_dict() == report.to_dict()


def test_privacy_schema_accepts_canonical_report() -> None:
    schema = json.loads(Path("schemas/privacy-report-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(pass_report().to_dict())


def test_malformed_target_platforms_and_out_of_scope_inventory_fail_closed() -> None:
    item = collected_item(platforms=("ios",))
    with pytest.raises(ValueError, match="outside report"):
        PrivacyReport.build("x", ("android",), (item,), generated_at=NOW)

    report = pass_report()
    payload = report.to_dict()
    payload["target_platforms"] = ["ios", "android"]
    with pytest.raises(ValueError, match="unique, sorted"):
        PrivacyReport.from_dict(payload)
