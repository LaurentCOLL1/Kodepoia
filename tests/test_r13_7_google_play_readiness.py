from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from kodepoia.core.secrets import KodeSecrets, MemorySecretBackend
from kodepoia.mobile.android_signing import AndroidSigningState
from kodepoia.mobile.contracts import StoreReadinessState
from kodepoia.mobile.google_play import (
    GooglePlayApiCapability,
    PlayAabCandidate,
    PlayAccountContext,
    PlayAccountKind,
    PlayApiMode,
    PlayContentRatingDeclaration,
    PlayDataSafetyDeclaration,
    PlayDeclarationState,
    PlayLocalizedListing,
    PlayPermissionDeclaration,
    PlayReleaseIntent,
    PlayReleaseKind,
    PlayReleaseTrack,
    PlaySdkDeclaration,
    PlayStoreMetadata,
    current_google_play_policy_snapshot,
    evaluate_google_play_readiness,
)

ROOT = Path(__file__).resolve().parents[1]
A = "11" * 32
B = "22" * 32
Q = "33" * 32
SOURCE = "a" * 40
APP_ID = "com.kodepoia.r13acceptance"


def _candidate(
    *,
    target_sdk: int = 36,
    signing_state: AndroidSigningState = AndroidSigningState.PLAY_APP_SIGNING_READY,
) -> PlayAabCandidate:
    return PlayAabCandidate(
        application_id=APP_ID,
        artifact_sha256=A,
        target_sdk=target_sdk,
        build_evidence_sha256=B,
        signing_state=signing_state,
        signing_artifact_sha256=A,
    )


def _metadata(*, application_id: str = APP_ID, app_name: str = "Kodepoia") -> PlayStoreMetadata:
    return PlayStoreMetadata(
        application_id=application_id,
        localizations=(
            PlayLocalizedListing(
                locale="en-US",
                app_name=app_name,
                short_description="Governed mobile readiness",
                full_description="Deterministic Google Play readiness evidence for Kodepoia.",
            ),
        ),
    )


def _data_complete() -> PlayDataSafetyDeclaration:
    return PlayDataSafetyDeclaration(
        PlayDeclarationState.COMPLETE,
        privacy_policy_url="https://example.invalid/privacy",
        third_party_sdks_reviewed=True,
    )


def _rating_complete() -> PlayContentRatingDeclaration:
    return PlayContentRatingDeclaration(PlayDeclarationState.COMPLETE, Q)


def _release(
    track: PlayReleaseTrack = PlayReleaseTrack.CLOSED,
    *,
    release_kind: PlayReleaseKind = PlayReleaseKind.FIRST_RELEASE,
    rollout_percent: int | None = None,
    application_id: str = APP_ID,
    planned_tester_count: int | None = None,
) -> PlayReleaseIntent:
    return PlayReleaseIntent(
        release_id="r13.7-fixture",
        application_id=application_id,
        track=track,
        release_kind=release_kind,
        rollout_percent=rollout_percent,
        planned_tester_count=planned_tester_count,
    )


def _evaluate(**overrides):
    args = {
        "source_sha": SOURCE,
        "evaluated_on": "2026-08-26",
        "policy": current_google_play_policy_snapshot(),
        "release": _release(),
        "candidate": _candidate(),
        "metadata": _metadata(),
        "data_safety": _data_complete(),
        "content_rating": _rating_complete(),
    }
    args.update(overrides)
    return evaluate_google_play_readiness(**args)


def _blockers(report) -> set[str]:
    return set(report.store_status.blockers)


def test_r13_7_internal_dry_run_uses_data_safety_exemption_without_publish() -> None:
    report = _evaluate(
        release=_release(PlayReleaseTrack.INTERNAL, planned_tester_count=100),
        data_safety=PlayDataSafetyDeclaration(PlayDeclarationState.MISSING),
        content_rating=PlayContentRatingDeclaration(PlayDeclarationState.MISSING),
    )
    assert report.store_status.readiness is StoreReadinessState.TEST_READY
    assert report.dry_run is True
    assert report.publish_attempted is False
    assert _blockers(report) == set()
    assert any(item.code == "data_safety_internal_exemption" for item in report.findings)


def test_r13_7_closed_track_requires_data_safety_and_content_rating() -> None:
    report = _evaluate(
        data_safety=PlayDataSafetyDeclaration(PlayDeclarationState.MISSING),
        content_rating=PlayContentRatingDeclaration(PlayDeclarationState.MISSING),
    )
    assert report.store_status.readiness is StoreReadinessState.BLOCKED
    assert {"data_safety_missing", "content_rating_missing"} <= _blockers(report)


def test_r13_7_api36_deadline_is_effective_date_driven() -> None:
    before = _evaluate(evaluated_on="2026-08-30", candidate=_candidate(target_sdk=35))
    assert "target_api_below_effective_requirement" not in _blockers(before)
    deadline = _evaluate(evaluated_on="2026-08-31", candidate=_candidate(target_sdk=35))
    assert "target_api_below_effective_requirement" in _blockers(deadline)


def test_r13_7_stale_policy_snapshot_cannot_claim_current_or_ready() -> None:
    report = _evaluate(evaluated_on="2026-10-01")
    assert report.policy_freshness.value == "STALE"
    assert "policy_snapshot_stale" in _blockers(report)
    assert report.store_status.readiness is StoreReadinessState.BLOCKED


def test_r13_7_listing_limits_come_from_policy_snapshot() -> None:
    report = _evaluate(metadata=_metadata(app_name="x" * 31))
    assert "listing_app_name_too_long" in _blockers(report)


def test_r13_7_package_and_signing_substitution_fail_closed() -> None:
    mismatch = _evaluate(metadata=_metadata(application_id="com.kodepoia.substitute"))
    assert "package_identity_mismatch" in _blockers(mismatch)
    with pytest.raises(ValueError, match="substitution"):
        PlayAabCandidate(APP_ID, A, 36, B, AndroidSigningState.UPLOAD_SIGNED, Q)


def test_r13_7_first_release_rejects_staged_rollout_and_internal_limit_is_bounded() -> None:
    rollout = _evaluate(release=_release(rollout_percent=10))
    assert "staged_rollout_unavailable_first_release" in _blockers(rollout)
    internal = _evaluate(release=_release(PlayReleaseTrack.INTERNAL, planned_tester_count=101))
    assert "internal_tester_limit_exceeded" in _blockers(internal)


def test_r13_7_unsafe_permission_and_unreviewed_sdk_block_readiness() -> None:
    report = _evaluate(
        permissions=(
            PlayPermissionDeclaration(
                "android.permission.READ_SMS",
                play_declaration_required=True,
                play_declaration_complete=False,
            ),
        ),
        sdks=(PlaySdkDeclaration("vendor.analytics", False, False),),
    )
    assert {
        "unsafe_permission_declaration",
        "sdk_policy_review_missing",
        "sdk_data_safety_missing",
    } <= _blockers(report)


def test_r13_7_personal_account_testing_rule_is_scoped_not_universal() -> None:
    personal = PlayAccountContext(
        kind=PlayAccountKind.PERSONAL,
        created_on="2024-01-01",
        closed_testers_continuous=11,
        closed_test_days_continuous=13,
        production_access_granted=False,
    )
    blocked = _evaluate(release=_release(PlayReleaseTrack.PRODUCTION), account=personal)
    assert {
        "personal_account_closed_testers_insufficient",
        "personal_account_closed_test_days_insufficient",
        "personal_account_production_access_not_granted",
    } <= _blockers(blocked)
    organization = PlayAccountContext(kind=PlayAccountKind.ORGANIZATION)
    ready = _evaluate(release=_release(PlayReleaseTrack.PRODUCTION), account=organization)
    assert ready.store_status.readiness is StoreReadinessState.STORE_READY


def test_r13_7_open_track_requires_production_access_for_scoped_new_personal_account() -> None:
    personal = PlayAccountContext(
        kind=PlayAccountKind.PERSONAL,
        created_on="2024-01-01",
        closed_testers_continuous=12,
        closed_test_days_continuous=14,
        production_access_granted=False,
    )
    report = _evaluate(release=_release(PlayReleaseTrack.OPEN), account=personal)
    assert "personal_account_open_track_requires_production_access" in _blockers(report)


def test_r13_7_test_signed_aab_does_not_manufacture_play_signing_readiness() -> None:
    report = _evaluate(candidate=_candidate(signing_state=AndroidSigningState.TEST_SIGNED))
    assert "play_signing_not_ready" in _blockers(report)


def test_r13_7_metadata_ordering_and_report_digest_are_deterministic() -> None:
    en = PlayLocalizedListing("en-US", "Kodepoia", "Governed readiness", "English description")
    fr = PlayLocalizedListing("fr-FR", "Kodepoia", "Préparation gouvernée", "Description française")
    first = PlayStoreMetadata(APP_ID, (fr, en))
    second = PlayStoreMetadata(APP_ID, (en, fr))
    a = _evaluate(metadata=first)
    b = _evaluate(metadata=second)
    assert a.metadata_sha256 == b.metadata_sha256
    assert a.digest() == b.digest()


def test_r13_7_optional_api_capability_uses_kodesecrets_ref_and_never_allows_publish() -> None:
    backend = MemorySecretBackend()
    secrets = KodeSecrets(backend)
    secrets.store("kodepoia.play", "service-account", "super-secret-json")
    capability = GooglePlayApiCapability(
        mode=PlayApiMode.DRAFT_ONLY,
        credential_ref=secrets.ref("kodepoia.play", "service-account"),
    )
    assert capability.authorized(secrets) is True
    serialized = json.dumps(capability.to_dict(), sort_keys=True)
    assert "super-secret-json" not in serialized
    assert capability.to_dict()["publish_allowed"] is False


def test_r13_7_report_schema_is_strict_and_matches_model() -> None:
    schema = json.loads(
        (ROOT / "schemas/r13/google-play-readiness.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    payload = _evaluate().to_dict()
    Draft202012Validator(schema).validate(payload)
    payload["live_publish_token"] = "forbidden"
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(payload)
