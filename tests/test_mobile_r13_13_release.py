from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from kodepoia.mobile.contracts import MobilePackageKind, MobilePlatform
from kodepoia.mobile.release import (
    PromotionDecision,
    PromotionRequest,
    ReleaseArtifactBinding,
    ReleaseAuthorityState,
    ReleaseCandidate,
    ReleaseChannel,
    ReleaseProvider,
    ReleaseVersion,
    RolloutAction,
    RolloutIntent,
    RolloutMode,
    RolloutPolicyEvidence,
    SemanticVersion,
    bind_rollout_policy,
    digest_policy_evidence,
    promote_release,
    rollback_release,
)


def _sha(char: str) -> str:
    return char * 64


def _artifact(
    artifact_id: str = "android-aab",
    *,
    platform: MobilePlatform = MobilePlatform.ANDROID,
    package_kind: MobilePackageKind = MobilePackageKind.AAB,
    digest_char: str = "a",
) -> ReleaseArtifactBinding:
    return ReleaseArtifactBinding(
        artifact_id=artifact_id,
        platform=platform,
        package_kind=package_kind,
        artifact_sha256=_sha(digest_char),
        provenance_sha256=_sha("f"),
    )


def _candidate(
    version: str = "1.0.0",
    *,
    code: int = 1,
    apple_build: str | None = None,
    artifacts: tuple[ReleaseArtifactBinding, ...] | None = None,
    candidate_id: str = "candidate-1",
    train_id: str = "mobile-stable",
    channel: ReleaseChannel = ReleaseChannel.PRODUCTION,
    evidence: tuple[str, ...] = (_sha("1"), _sha("2")),
    rollout: RolloutIntent | None = None,
) -> ReleaseCandidate:
    actual_artifacts = artifacts or (_artifact(),)
    if any(item.platform in {MobilePlatform.IOS, MobilePlatform.IPADOS} for item in actual_artifacts):
        apple_build = apple_build or "1"
    return ReleaseCandidate(
        candidate_id=candidate_id,
        train_id=train_id,
        channel=channel,
        version=ReleaseVersion(
            product_version=SemanticVersion.parse(version),
            android_version_code=code if any(item.platform is MobilePlatform.ANDROID for item in actual_artifacts) else None,
            apple_build_number=apple_build,
        ),
        artifacts=actual_artifacts,
        evidence_sha256=evidence,
        changelog_sha256=_sha("3"),
        sbom_sha256=_sha("4"),
        compliance_sha256=_sha("5"),
        rollout_intent=rollout,
    )


def _request(candidate: ReleaseCandidate, state: ReleaseAuthorityState, *, promotion_id: str = "promote-1") -> PromotionRequest:
    return PromotionRequest(
        promotion_id=promotion_id,
        candidate=candidate,
        expected_revision=state.revision,
        expected_candidate_sha256=candidate.digest(),
        expected_artifact_set_sha256=candidate.artifact_set_sha256(),
        expected_evidence_set_sha256=candidate.evidence_set_sha256(),
        expected_authoritative_candidate_sha256=state.authoritative_candidate_sha256,
    )


def _first_state() -> ReleaseAuthorityState:
    return ReleaseAuthorityState(train_id="mobile-stable", channel=ReleaseChannel.PRODUCTION)


def test_semver_strict_parser_and_precedence() -> None:
    with pytest.raises(ValueError):
        SemanticVersion.parse("01.0.0")
    with pytest.raises(ValueError):
        SemanticVersion.parse("1.0")
    with pytest.raises(ValueError):
        SemanticVersion.parse("1.0.0-alpha..1")

    assert SemanticVersion.parse("1.0.0-alpha.2") < SemanticVersion.parse("1.0.0-alpha.10")
    assert SemanticVersion.parse("1.0.0-alpha") < SemanticVersion.parse("1.0.0")
    assert SemanticVersion.parse("1.0.0+build.1") == SemanticVersion.parse("1.0.0+build.9")


def test_candidate_digest_is_deterministic_under_input_ordering() -> None:
    android = _artifact()
    ios = _artifact(
        "ios-archive",
        platform=MobilePlatform.IOS,
        package_kind=MobilePackageKind.XCARCHIVE,
        digest_char="b",
    )
    first = _candidate(artifacts=(ios, android), apple_build="2", evidence=(_sha("2"), _sha("1")))
    second = _candidate(artifacts=(android, ios), apple_build="2", evidence=(_sha("1"), _sha("2")))
    assert first.digest() == second.digest()
    assert first.artifact_set_sha256() == second.artifact_set_sha256()
    assert first.evidence_set_sha256() == second.evidence_set_sha256()


def test_platform_package_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError):
        _artifact(package_kind=MobilePackageKind.IPA)
    with pytest.raises(ValueError):
        _artifact(platform=MobilePlatform.IOS, package_kind=MobilePackageKind.AAB)


def test_candidate_requires_platform_build_mapping() -> None:
    android = _artifact()
    with pytest.raises(ValueError):
        ReleaseCandidate(
            candidate_id="bad-android",
            train_id="mobile-stable",
            channel=ReleaseChannel.PRODUCTION,
            version=ReleaseVersion(product_version=SemanticVersion.parse("1.0.0"), apple_build_number="1"),
            artifacts=(android,),
            evidence_sha256=(_sha("1"),),
            changelog_sha256=_sha("3"),
            sbom_sha256=_sha("4"),
            compliance_sha256=_sha("5"),
        )

    ios = _artifact("ios", platform=MobilePlatform.IOS, package_kind=MobilePackageKind.IPA)
    with pytest.raises(ValueError):
        ReleaseCandidate(
            candidate_id="bad-ios",
            train_id="mobile-stable",
            channel=ReleaseChannel.PRODUCTION,
            version=ReleaseVersion(product_version=SemanticVersion.parse("1.0.0"), android_version_code=1),
            artifacts=(ios,),
            evidence_sha256=(_sha("1"),),
            changelog_sha256=_sha("3"),
            sbom_sha256=_sha("4"),
            compliance_sha256=_sha("5"),
        )


def test_candidate_requires_evidence_and_supporting_digests() -> None:
    with pytest.raises(ValueError):
        _candidate(evidence=())
    with pytest.raises(ValueError):
        ReleaseCandidate(
            candidate_id="bad-digest",
            train_id="mobile-stable",
            channel=ReleaseChannel.PRODUCTION,
            version=ReleaseVersion(product_version=SemanticVersion.parse("1.0.0"), android_version_code=1),
            artifacts=(_artifact(),),
            evidence_sha256=(_sha("1"),),
            changelog_sha256="not-a-digest",
            sbom_sha256=_sha("4"),
            compliance_sha256=_sha("5"),
        )


def test_first_promotion_advances_revision_once() -> None:
    state = _first_state()
    candidate = _candidate()
    outcome = promote_release(state, _request(candidate, state))
    assert outcome.promoted
    assert outcome.decision is PromotionDecision.PROMOTED
    assert outcome.state.revision == 1
    assert outcome.state.authoritative_candidate_sha256 == candidate.digest()
    assert outcome.rollback_point is None
    assert state.revision == 0


def test_stale_concurrent_promotion_is_deterministic_and_non_mutating() -> None:
    initial = _first_state()
    first = _candidate()
    state = promote_release(initial, _request(first, initial)).state
    second = _candidate("1.1.0", code=2, candidate_id="candidate-2")
    request = _request(second, state)
    request = PromotionRequest(
        promotion_id=request.promotion_id,
        candidate=request.candidate,
        expected_revision=0,
        expected_candidate_sha256=request.expected_candidate_sha256,
        expected_artifact_set_sha256=request.expected_artifact_set_sha256,
        expected_evidence_set_sha256=request.expected_evidence_set_sha256,
        expected_authoritative_candidate_sha256=request.expected_authoritative_candidate_sha256,
    )
    outcome = promote_release(state, request)
    assert outcome.decision is PromotionDecision.REVISION_CONFLICT
    assert outcome.state is state


def test_train_channel_and_prior_authority_mismatch_leave_state_unchanged() -> None:
    state = _first_state()
    wrong_train = _candidate(train_id="other-train")
    outcome = promote_release(state, _request(wrong_train, state))
    assert outcome.decision is PromotionDecision.TRAIN_MISMATCH
    assert outcome.state is state

    wrong_channel = _candidate(channel=ReleaseChannel.BETA)
    outcome = promote_release(state, _request(wrong_channel, state))
    assert outcome.decision is PromotionDecision.CHANNEL_MISMATCH
    assert outcome.state is state

    candidate = _candidate()
    request = _request(candidate, state)
    request = PromotionRequest(
        promotion_id=request.promotion_id,
        candidate=candidate,
        expected_revision=0,
        expected_candidate_sha256=candidate.digest(),
        expected_artifact_set_sha256=candidate.artifact_set_sha256(),
        expected_evidence_set_sha256=candidate.evidence_set_sha256(),
        expected_authoritative_candidate_sha256=_sha("9"),
    )
    outcome = promote_release(state, request)
    assert outcome.decision is PromotionDecision.AUTHORITATIVE_MISMATCH
    assert outcome.state is state


@pytest.mark.parametrize(
    ("field", "decision"),
    [
        ("candidate", PromotionDecision.CANDIDATE_SUBSTITUTION),
        ("artifact", PromotionDecision.ARTIFACT_SUBSTITUTION),
        ("evidence", PromotionDecision.EVIDENCE_SUBSTITUTION),
    ],
)
def test_independent_substitution_guards(field: str, decision: PromotionDecision) -> None:
    state = _first_state()
    candidate = _candidate()
    request = _request(candidate, state)
    kwargs = {
        "promotion_id": request.promotion_id,
        "candidate": candidate,
        "expected_revision": request.expected_revision,
        "expected_candidate_sha256": request.expected_candidate_sha256,
        "expected_artifact_set_sha256": request.expected_artifact_set_sha256,
        "expected_evidence_set_sha256": request.expected_evidence_set_sha256,
        "expected_authoritative_candidate_sha256": request.expected_authoritative_candidate_sha256,
    }
    if field == "candidate":
        kwargs["expected_candidate_sha256"] = _sha("8")
    elif field == "artifact":
        kwargs["expected_artifact_set_sha256"] = _sha("8")
    else:
        kwargs["expected_evidence_set_sha256"] = _sha("8")
    outcome = promote_release(state, PromotionRequest(**kwargs))
    assert outcome.decision is decision
    assert outcome.state is state


def test_product_version_regression_and_equal_precedence_are_rejected() -> None:
    initial = _first_state()
    current = _candidate("2.0.0", code=20)
    state = promote_release(initial, _request(current, initial)).state

    lower = _candidate("1.9.9", code=21, candidate_id="lower")
    outcome = promote_release(state, _request(lower, state))
    assert outcome.decision is PromotionDecision.VERSION_REGRESSION

    equal_precedence = _candidate("2.0.0+different-build", code=21, candidate_id="equal")
    outcome = promote_release(state, _request(equal_precedence, state))
    assert outcome.decision is PromotionDecision.VERSION_REGRESSION


def test_platform_build_regressions_are_rejected_after_semver_increase() -> None:
    android_initial = _first_state()
    android_current = _candidate("1.0.0", code=10)
    android_state = promote_release(android_initial, _request(android_current, android_initial)).state
    android_next = _candidate("1.1.0", code=9, candidate_id="android-next")
    outcome = promote_release(android_state, _request(android_next, android_state))
    assert outcome.decision is PromotionDecision.ANDROID_BUILD_REGRESSION

    ios_artifact = _artifact("ios", platform=MobilePlatform.IOS, package_kind=MobilePackageKind.IPA)
    ios_initial = ReleaseAuthorityState(train_id="mobile-stable", channel=ReleaseChannel.PRODUCTION)
    ios_current = _candidate("1.0.0", artifacts=(ios_artifact,), apple_build="10", candidate_id="ios-current")
    ios_state = promote_release(ios_initial, _request(ios_current, ios_initial)).state
    ios_next = _candidate("1.1.0", artifacts=(ios_artifact,), apple_build="9", candidate_id="ios-next")
    outcome = promote_release(ios_state, _request(ios_next, ios_state))
    assert outcome.decision is PromotionDecision.APPLE_BUILD_REGRESSION


def test_released_version_is_immutable_even_after_later_release() -> None:
    initial = _first_state()
    first = _candidate("1.0.0", code=1)
    state1 = promote_release(initial, _request(first, initial)).state
    second = _candidate("2.0.0", code=2, candidate_id="candidate-2")
    state2 = promote_release(state1, _request(second, state1)).state

    changed_v1 = _candidate(
        "1.0.0",
        code=3,
        candidate_id="candidate-v1-mutated",
        artifacts=(_artifact(digest_char="b"),),
    )
    outcome = promote_release(state2, _request(changed_v1, state2))
    assert outcome.decision is PromotionDecision.RELEASED_VERSION_IMMUTABLE
    assert outcome.state is state2


def test_successful_second_promotion_creates_rollback_and_rollback_restores_local_authority() -> None:
    initial = _first_state()
    first = _candidate("1.0.0", code=1)
    state1 = promote_release(initial, _request(first, initial)).state
    second = _candidate("1.1.0", code=2, candidate_id="candidate-2")
    outcome = promote_release(state1, _request(second, state1, promotion_id="promote-2"))
    assert outcome.promoted
    assert outcome.rollback_point is not None
    assert outcome.rollback_point.candidate_sha256 == first.digest()
    assert len(outcome.state.released_version_seals) == 2

    restored = rollback_release(
        outcome.state,
        outcome.rollback_point.rollback_point_id,
        expected_revision=outcome.state.revision,
    )
    assert restored.revision == outcome.state.revision + 1
    assert restored.authoritative_candidate_sha256 == first.digest()
    assert restored.authoritative_product_version == "1.0.0"
    assert len(restored.released_version_seals) == 2


def test_rollback_requires_exact_revision_and_known_same_authority_point() -> None:
    initial = _first_state()
    first = _candidate()
    state1 = promote_release(initial, _request(first, initial)).state
    second = _candidate("1.1.0", code=2, candidate_id="candidate-2")
    outcome = promote_release(state1, _request(second, state1))
    point = outcome.rollback_point
    assert point is not None

    with pytest.raises(ValueError, match="revision conflict"):
        rollback_release(outcome.state, point.rollback_point_id, expected_revision=0)
    with pytest.raises(ValueError, match="missing or ambiguous"):
        rollback_release(outcome.state, "rollback-missing", expected_revision=outcome.state.revision)


def test_google_rollout_intent_is_policy_bound_and_percentage_bounded() -> None:
    evidence = RolloutPolicyEvidence(
        provider=ReleaseProvider.GOOGLE_PLAY,
        source_url="https://support.google.com/googleplay/android-developer/answer/6346149",
        retrieved_on=date(2026, 8, 27),
        evidence_sha256=_sha("6"),
        allowed_modes=(RolloutMode.IMMEDIATE, RolloutMode.STAGED_PERCENT),
        allowed_actions=(RolloutAction.START, RolloutAction.PAUSE, RolloutAction.RESUME, RolloutAction.HALT),
    )
    intent = RolloutIntent(
        provider=ReleaseProvider.GOOGLE_PLAY,
        mode=RolloutMode.STAGED_PERCENT,
        action=RolloutAction.START,
        percentage_basis_points=2500,
        policy_evidence_sha256=digest_policy_evidence(evidence),
    )
    bind_rollout_policy(intent, evidence)

    with pytest.raises(ValueError):
        RolloutIntent(
            provider=ReleaseProvider.GOOGLE_PLAY,
            mode=RolloutMode.STAGED_PERCENT,
            action=RolloutAction.START,
            percentage_basis_points=0,
            policy_evidence_sha256=digest_policy_evidence(evidence),
        )


def test_apple_phased_rollout_is_provider_defined_and_policy_bound() -> None:
    evidence = RolloutPolicyEvidence(
        provider=ReleaseProvider.APP_STORE,
        source_url="https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases",
        retrieved_on=date(2026, 8, 27),
        evidence_sha256=_sha("7"),
        allowed_modes=(RolloutMode.IMMEDIATE, RolloutMode.PROVIDER_PHASED),
        allowed_actions=(RolloutAction.START, RolloutAction.PAUSE, RolloutAction.RESUME, RolloutAction.COMPLETE),
        automatic_schedule_percent=(1, 2, 5, 10, 20, 50, 100),
    )
    intent = RolloutIntent(
        provider=ReleaseProvider.APP_STORE,
        mode=RolloutMode.PROVIDER_PHASED,
        action=RolloutAction.START,
        policy_evidence_sha256=digest_policy_evidence(evidence),
    )
    bind_rollout_policy(intent, evidence)

    with pytest.raises(ValueError):
        RolloutIntent(
            provider=ReleaseProvider.APP_STORE,
            mode=RolloutMode.PROVIDER_PHASED,
            action=RolloutAction.START,
            percentage_basis_points=100,
            policy_evidence_sha256=digest_policy_evidence(evidence),
        )


def test_rollout_policy_substitution_and_provider_mismatch_fail_closed() -> None:
    evidence = RolloutPolicyEvidence(
        provider=ReleaseProvider.GOOGLE_PLAY,
        source_url="https://support.google.com/googleplay/android-developer/answer/6346149",
        retrieved_on=date(2026, 8, 27),
        evidence_sha256=_sha("6"),
        allowed_modes=(RolloutMode.STAGED_PERCENT,),
        allowed_actions=(RolloutAction.START,),
    )
    substituted = RolloutIntent(
        provider=ReleaseProvider.GOOGLE_PLAY,
        mode=RolloutMode.STAGED_PERCENT,
        action=RolloutAction.START,
        percentage_basis_points=1000,
        policy_evidence_sha256=_sha("9"),
    )
    with pytest.raises(ValueError, match="substitution"):
        bind_rollout_policy(substituted, evidence)

    apple = RolloutPolicyEvidence(
        provider=ReleaseProvider.APP_STORE,
        source_url="https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases",
        retrieved_on=date(2026, 8, 27),
        evidence_sha256=_sha("7"),
        allowed_modes=(RolloutMode.PROVIDER_PHASED,),
        allowed_actions=(RolloutAction.START,),
        automatic_schedule_percent=(1, 2, 5, 10, 20, 50, 100),
    )
    valid_google_intent = RolloutIntent(
        provider=ReleaseProvider.GOOGLE_PLAY,
        mode=RolloutMode.STAGED_PERCENT,
        action=RolloutAction.START,
        percentage_basis_points=1000,
        policy_evidence_sha256=digest_policy_evidence(evidence),
    )
    with pytest.raises(ValueError, match="provider mismatch"):
        bind_rollout_policy(valid_google_intent, apple)


def test_release_candidate_schema_matches_canonical_payload() -> None:
    schema_path = Path("schemas/mobile-release-v1.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    candidate = _candidate()
    payload = candidate.to_dict()

    assert schema["title"] == "Kodepoia Mobile Release Candidate"
    assert schema["additionalProperties"] is False
    required = set(schema["required"])
    assert required == set(payload)
    assert schema["$defs"]["sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert payload["candidate_id"] == "candidate-1"
    assert payload["artifacts"][0]["package_kind"] == "aab"


def test_core_release_model_has_no_live_store_secret_or_raw_command_fields() -> None:
    candidate_keys = set(_candidate().to_dict())
    state_keys = set(_first_state().to_dict())
    forbidden = {
        "token",
        "password",
        "secret",
        "private_key",
        "service_account",
        "endpoint",
        "argv",
        "command",
        "publish",
        "upload",
    }
    assert not candidate_keys & forbidden
    assert not state_keys & forbidden
