from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.mobile.compliance import (
    ComplianceContext,
    ComplianceFact,
    ComplianceFindingStatus,
    ComplianceInput,
    ComplianceProvider,
    ComplianceRule,
    ComplianceRuleCurrentness,
    ComplianceRuleOperator,
    ComplianceRuleSet,
    ComplianceScope,
    ComplianceSeverity,
    StoreComplianceState,
    ThirdPartySdkEvidence,
    build_store_surface_facts,
    evaluate_store_compliance,
    facts_from_mapping,
)
from kodepoia.mobile.contracts import MobilePlatform


def _sha(char: str = "a") -> str:
    return char * 64


def _source(provider: ComplianceProvider) -> str:
    if provider is ComplianceProvider.GOOGLE_PLAY:
        return "https://support.google.com/googleplay/android-developer/answer/11926878"
    return "https://developer.apple.com/news/upcoming-requirements/"


def _scope(platform: MobilePlatform) -> ComplianceScope:
    return ComplianceScope(platforms=(platform,), regions=("GLOBAL",), app_categories=("all",))


def _rule(
    *,
    rule_id: str,
    provider: ComplianceProvider = ComplianceProvider.GOOGLE_PLAY,
    platform: MobilePlatform = MobilePlatform.ANDROID,
    requirement: str = "android.target-api",
    operator: ComplianceRuleOperator = ComplianceRuleOperator.MIN_INTEGER,
    expected: object = 35,
    retrieved_on: str = "2026-08-27",
    effective_from: str = "2025-08-31",
    expires_on: str | None = None,
    source_url: str | None = None,
    freshness_days: int = 30,
    severity: ComplianceSeverity = ComplianceSeverity.BLOCKER,
    account_only: bool = False,
) -> ComplianceRule:
    return ComplianceRule(
        rule_id=rule_id,
        provider=provider,
        requirement=requirement,
        operator=operator,
        expected=expected,
        source_url=source_url or _source(provider),
        source_sha256=_sha("b"),
        retrieved_on=retrieved_on,
        effective_from=effective_from,
        expires_on=expires_on,
        freshness_days=freshness_days,
        scope=_scope(platform),
        severity=severity,
        remediation=f"Remediate {requirement}.",
        account_only=account_only,
    )


def _context(
    provider: ComplianceProvider = ComplianceProvider.GOOGLE_PLAY,
    platform: MobilePlatform = MobilePlatform.ANDROID,
    *,
    account_connected: bool = False,
) -> ComplianceContext:
    return ComplianceContext(
        provider=provider,
        platform=platform,
        region="FR",
        app_category="all",
        account_connected=account_connected,
    )


def _evaluate(
    rules: tuple[ComplianceRule, ...],
    facts: dict[str, object],
    *,
    evaluated_on: str = "2026-08-27",
    context: ComplianceContext | None = None,
    sdks: tuple[ThirdPartySdkEvidence, ...] = (),
):
    return evaluate_store_compliance(
        source_sha="c" * 40,
        evaluated_on=evaluated_on,
        context=context or _context(),
        ruleset=ComplianceRuleSet("rules-1", rules),
        evidence=ComplianceInput(facts=facts_from_mapping(facts), third_party_sdks=sdks),
    )


def test_current_official_minimum_rule_passes_and_claim_is_advisory() -> None:
    report = _evaluate((_rule(rule_id="play-api-35"),), {"android.target-api": 35})
    assert report.state is StoreComplianceState.READY
    assert report.current_policy_claim is True
    assert report.blockers == ()
    assert report.legal_certification is False
    assert report.live_account_query_attempted is False
    assert report.findings[0].status is ComplianceFindingStatus.PASS


def test_google_api_36_effective_boundary_is_data_driven_not_hardcoded() -> None:
    old = _rule(
        rule_id="play-api-35",
        expected=35,
        effective_from="2025-08-31",
        expires_on="2026-08-30",
    )
    new = _rule(
        rule_id="play-api-36",
        expected=36,
        effective_from="2026-08-31",
    )

    before = _evaluate((old, new), {"android.target-api": 35}, evaluated_on="2026-08-30")
    assert before.state is StoreComplianceState.READY
    assert "play-api-35" in before.current_rule_ids
    assert "play-api-36" in before.noncurrent_rule_ids
    assert any(
        item.rule_id == "play-api-36"
        and item.currentness is ComplianceRuleCurrentness.FUTURE
        for item in before.findings
    )

    on_boundary = _evaluate((old, new), {"android.target-api": 35}, evaluated_on="2026-08-31")
    assert on_boundary.state is StoreComplianceState.BLOCKED
    assert "play-api-36" in on_boundary.current_rule_ids
    assert any(item.rule_id == "play-api-36" and item.status is ComplianceFindingStatus.FAIL for item in on_boundary.findings)

    compliant = _evaluate((old, new), {"android.target-api": 36}, evaluated_on="2026-08-31")
    assert compliant.state is StoreComplianceState.READY
    assert compliant.current_policy_claim is True


def test_stale_only_evidence_cannot_claim_current_and_blocks_readiness() -> None:
    stale = _rule(
        rule_id="stale-rule",
        retrieved_on="2026-01-01",
        effective_from="2026-01-01",
        freshness_days=30,
    )
    report = _evaluate((stale,), {"android.target-api": 99}, evaluated_on="2026-08-27")
    assert report.state is StoreComplianceState.BLOCKED
    assert report.current_policy_claim is False
    assert "stale-rule" in report.noncurrent_rule_ids
    assert any(item.currentness is ComplianceRuleCurrentness.STALE for item in report.findings)
    assert any(item.finding_id == "no-current-android-target-api" for item in report.findings)


def test_unofficial_only_evidence_is_preserved_but_never_current() -> None:
    unofficial = _rule(
        rule_id="community-copy",
        source_url="https://example.com/google-play-policy",
    )
    report = _evaluate((unofficial,), {"android.target-api": 99})
    assert report.state is StoreComplianceState.BLOCKED
    assert report.current_policy_claim is False
    assert any(item.currentness is ComplianceRuleCurrentness.UNOFFICIAL for item in report.findings)


def test_conflicting_current_official_rules_surface_blocker_instead_of_choosing() -> None:
    left = _rule(rule_id="api-a", expected=35)
    right = _rule(rule_id="api-b", expected=36)
    report = _evaluate((left, right), {"android.target-api": 36})
    assert report.state is StoreComplianceState.BLOCKED
    conflicts = [item for item in report.findings if item.status is ComplianceFindingStatus.CONFLICT]
    assert len(conflicts) == 1
    assert conflicts[0].requirement == "android.target-api"


def test_future_rule_does_not_override_current_predecessor_before_effective_date() -> None:
    predecessor = _rule(rule_id="permission-old", requirement="permission.location-reviewed", operator=ComplianceRuleOperator.TRUE, expected=True)
    future = _rule(
        rule_id="permission-future",
        requirement="permission.location-reviewed",
        operator=ComplianceRuleOperator.EQUALS,
        expected="future-form",
        effective_from="2026-10-28",
    )
    report = _evaluate(
        (predecessor, future),
        {"permission.location-reviewed": True},
        evaluated_on="2026-08-27",
    )
    assert report.state is StoreComplianceState.READY
    assert report.current_policy_claim is True
    assert "permission-future" in report.noncurrent_rule_ids


def test_account_only_current_rule_becomes_confirmation_not_local_blocker() -> None:
    account_rule = _rule(
        rule_id="play-account-form",
        requirement="account.play-form-confirmed",
        operator=ComplianceRuleOperator.TRUE,
        expected=True,
        account_only=True,
    )
    report = _evaluate((account_rule,), {})
    assert report.state is StoreComplianceState.READY_WITH_WARNINGS
    assert report.blockers == ()
    assert report.account_confirmations == ("play-account-form",)
    assert report.current_policy_claim is True
    assert any(item.status is ComplianceFindingStatus.NEEDS_ACCOUNT_CONFIRMATION for item in report.findings)


def test_account_only_rule_is_evaluated_when_local_account_evidence_is_explicitly_supplied() -> None:
    account_rule = _rule(
        rule_id="play-account-form",
        requirement="account.play-form-confirmed",
        operator=ComplianceRuleOperator.TRUE,
        expected=True,
        account_only=True,
    )
    report = _evaluate(
        (account_rule,),
        {"account.play-form-confirmed": True},
        context=_context(account_connected=True),
    )
    assert report.state is StoreComplianceState.READY
    assert report.account_confirmations == ()


def test_google_sdk_inventory_requires_review_and_data_safety_accounting() -> None:
    gate = _rule(
        rule_id="sdk-gate",
        requirement="store.metadata-reviewed",
        operator=ComplianceRuleOperator.TRUE,
        expected=True,
    )
    sdk = ThirdPartySdkEvidence(
        sdk_id="analytics",
        version="1.2.3",
        platforms=(MobilePlatform.ANDROID,),
        data_practices_reviewed=False,
        google_data_safety_accounted=False,
        permissions=("android.permission.ACCESS_FINE_LOCATION",),
        data_types=("precise-location",),
    )
    report = _evaluate((gate,), {"store.metadata-reviewed": True}, sdks=(sdk,))
    assert report.state is StoreComplianceState.BLOCKED
    assert {"sdk-review-analytics", "sdk-play-data-safety-analytics"}.issubset(report.blockers)


def test_apple_sdk_inventory_requires_app_privacy_accounting() -> None:
    apple_gate = _rule(
        rule_id="apple-privacy",
        provider=ComplianceProvider.APPLE_APP_STORE,
        platform=MobilePlatform.IOS,
        requirement="apple.app-privacy-complete",
        operator=ComplianceRuleOperator.TRUE,
        expected=True,
    )
    sdk = ThirdPartySdkEvidence(
        sdk_id="telemetry",
        version="4.0",
        platforms=(MobilePlatform.IOS,),
        data_practices_reviewed=True,
        apple_app_privacy_accounted=False,
        apple_privacy_manifest_present=True,
    )
    report = _evaluate(
        (apple_gate,),
        {"apple.app-privacy-complete": True},
        context=_context(ComplianceProvider.APPLE_APP_STORE, MobilePlatform.IOS),
        sdks=(sdk,),
    )
    assert report.state is StoreComplianceState.BLOCKED
    assert "sdk-apple-app-privacy-telemetry" in report.blockers


def test_apple_required_reason_codes_are_checked_as_rule_data() -> None:
    rule = _rule(
        rule_id="apple-required-reasons",
        provider=ComplianceProvider.APPLE_APP_STORE,
        platform=MobilePlatform.IOS,
        requirement="apple.required-reason-codes",
        operator=ComplianceRuleOperator.CONTAINS_ALL,
        expected=("C617.1", "CA92.1"),
    )
    ok = _evaluate(
        (rule,),
        {"apple.required-reason-codes": ("CA92.1", "C617.1", "extra")},
        context=_context(ComplianceProvider.APPLE_APP_STORE, MobilePlatform.IOS),
    )
    assert ok.state is StoreComplianceState.READY
    bad = _evaluate(
        (rule,),
        {"apple.required-reason-codes": ("C617.1",)},
        context=_context(ComplianceProvider.APPLE_APP_STORE, MobilePlatform.IOS),
    )
    assert bad.state is StoreComplianceState.BLOCKED


def test_store_surface_helper_emits_localization_asset_accessibility_and_privacy_facts() -> None:
    facts = build_store_surface_facts(
        localizations=("fr-FR", "en-US"),
        asset_kinds=("icon", "phone-screenshot"),
        accessibility_reviewed=True,
        privacy_policy_url="https://example.org/privacy",
    )
    values = {item.key: item.value for item in facts}
    assert values["store.localizations"] == ("en-US", "fr-FR")
    assert values["store.assets"] == ("icon", "phone-screenshot")
    assert values["store.accessibility-reviewed"] is True
    assert values["store.privacy-policy-url"] == "https://example.org/privacy"


def test_rule_scope_is_provider_platform_region_and_category_aware() -> None:
    fr_games = ComplianceScope(
        platforms=(MobilePlatform.ANDROID,),
        regions=("FR",),
        app_categories=("games",),
    )
    rule = ComplianceRule(
        rule_id="fr-games",
        provider=ComplianceProvider.GOOGLE_PLAY,
        requirement="store.rating-present",
        operator=ComplianceRuleOperator.TRUE,
        expected=True,
        source_url=_source(ComplianceProvider.GOOGLE_PLAY),
        source_sha256=_sha("d"),
        retrieved_on="2026-08-27",
        effective_from="2026-01-01",
        scope=fr_games,
        severity=ComplianceSeverity.BLOCKER,
        remediation="Complete content rating.",
    )
    context = ComplianceContext(
        provider=ComplianceProvider.GOOGLE_PLAY,
        platform=MobilePlatform.ANDROID,
        region="US",
        app_category="games",
    )
    report = _evaluate((rule,), {"store.rating-present": True}, context=context)
    assert report.state is StoreComplianceState.BLOCKED
    assert report.blockers == ("no-applicable-rules",)


def test_rule_set_and_input_digests_are_deterministic_under_input_order() -> None:
    a = _rule(rule_id="a", requirement="store.a", operator=ComplianceRuleOperator.TRUE, expected=True)
    b = _rule(rule_id="b", requirement="store.b", operator=ComplianceRuleOperator.TRUE, expected=True)
    left = ComplianceRuleSet("set", (b, a))
    right = ComplianceRuleSet("set", (a, b))
    assert left.digest() == right.digest()

    evidence_left = ComplianceInput((ComplianceFact("store.b", True), ComplianceFact("store.a", True)))
    evidence_right = ComplianceInput((ComplianceFact("store.a", True), ComplianceFact("store.b", True)))
    assert evidence_left.digest() == evidence_right.digest()


def test_duplicate_rule_ids_and_fact_keys_fail_closed() -> None:
    one = _rule(rule_id="dup")
    with pytest.raises(ValueError, match="duplicate compliance rule_id"):
        ComplianceRuleSet("set", (one, one))
    with pytest.raises(ValueError, match="duplicate compliance fact key"):
        ComplianceInput((ComplianceFact("store.a", True), ComplianceFact("store.a", False)))


def test_malformed_dates_hashes_urls_and_provider_platform_pairs_fail_closed() -> None:
    with pytest.raises(ValueError, match="source_sha256"):
        ComplianceRule(
            rule_id="bad",
            provider=ComplianceProvider.GOOGLE_PLAY,
            requirement="store.a",
            operator=ComplianceRuleOperator.TRUE,
            expected=True,
            source_url="https://support.google.com/x",
            source_sha256="bad",
            retrieved_on="2026-08-27",
            effective_from="2026-08-27",
            scope=_scope(MobilePlatform.ANDROID),
            severity=ComplianceSeverity.BLOCKER,
            remediation="Fix.",
        )
    with pytest.raises(ValueError, match="HTTPS"):
        _rule(rule_id="bad-url", source_url="http://example.com")
    with pytest.raises(ValueError, match="ISO date"):
        _rule(rule_id="bad-date", retrieved_on="27-08-2026")
    with pytest.raises(ValueError, match="Google Play context"):
        _context(ComplianceProvider.GOOGLE_PLAY, MobilePlatform.IOS)


def test_rule_retrieved_after_evaluation_fails_closed() -> None:
    rule = _rule(rule_id="future-retrieval", retrieved_on="2026-08-28")
    with pytest.raises(ValueError, match="retrieved after evaluation"):
        _evaluate((rule,), {"android.target-api": 35}, evaluated_on="2026-08-27")


def test_schema_declares_advisory_non_live_contract() -> None:
    schema = json.loads(
        (Path(__file__).parents[1] / "schemas" / "store-compliance-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert schema["$id"].endswith("/store-compliance-v1.schema.json")
    assert schema["properties"]["legal_certification"]["const"] is False
    assert schema["properties"]["live_account_query_attempted"]["const"] is False
    assert "current_policy_claim" in schema["required"]
