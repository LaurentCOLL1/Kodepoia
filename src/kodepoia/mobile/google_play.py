from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Sequence
from urllib.parse import urlparse

from kodepoia.core.secrets import KodeSecrets, SecretRef
from kodepoia.mobile.android_build import (
    AndroidArtifactKind,
    AndroidBuildEvidence,
    AndroidBuildStatus,
)
from kodepoia.mobile.android_signing import (
    AndroidSigningInspection,
    AndroidSigningState,
)
from kodepoia.mobile.contracts import (
    MobilePlatform,
    StoreReadinessState,
    StoreReleaseStatus,
    canonical_sha256,
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_APP_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
_LOCALE_RE = re.compile(r"^[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*$")
_PERMISSION_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.]{1,255}$")
_STABLE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class PlayReleaseTrack(StrEnum):
    INTERNAL = "internal"
    CLOSED = "closed"
    OPEN = "open"
    PRODUCTION = "production"


class PlayReleaseKind(StrEnum):
    FIRST_RELEASE = "first_release"
    UPDATE = "update"


class PlayPolicyFreshness(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"


class PlayAccountKind(StrEnum):
    UNKNOWN = "unknown"
    PERSONAL = "personal"
    ORGANIZATION = "organization"


class PlayDeclarationState(StrEnum):
    COMPLETE = "complete"
    MISSING = "missing"


class PlayFindingSeverity(StrEnum):
    WARNING = "warning"
    BLOCKER = "blocker"


class PlayAssetKind(StrEnum):
    ICON = "icon"
    FEATURE_GRAPHIC = "feature_graphic"
    PHONE_SCREENSHOT = "phone_screenshot"
    TABLET_SCREENSHOT = "tablet_screenshot"


class PlayApiMode(StrEnum):
    DISABLED = "disabled"
    DRAFT_ONLY = "draft_only"


@dataclass(frozen=True, slots=True)
class GooglePlayApiCapability:
    mode: PlayApiMode = PlayApiMode.DISABLED
    credential_ref: SecretRef | None = None

    def __post_init__(self) -> None:
        if self.mode is PlayApiMode.DRAFT_ONLY and self.credential_ref is None:
            raise ValueError("draft-only Play API capability requires a KodeSecrets reference")

    def authorized(self, secrets: KodeSecrets) -> bool:
        if self.mode is PlayApiMode.DISABLED or self.credential_ref is None:
            return False
        return secrets.resolve(self.credential_ref) is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode.value,
            "credential_ref": (
                self.credential_ref.to_dict() if self.credential_ref is not None else None
            ),
            "draft_upload_capability": self.mode is PlayApiMode.DRAFT_ONLY,
            "publish_allowed": False,
        }


def _iso_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


def _sha(value: str, field: str) -> str:
    if _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be lowercase SHA-256")
    return value


def _stable(value: str, field: str) -> str:
    if _STABLE_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable identifier")
    return value


def _https_url(value: str, field: str, *, official_only: bool = False) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(f"{field} must be an HTTPS URL")
    if official_only and parsed.hostname not in {
        "developer.android.com",
        "support.google.com",
    }:
        raise ValueError(f"{field} must use an official Android/Google Play host")
    return value


@dataclass(frozen=True, slots=True)
class GooglePlayPolicySnapshot:
    policy_id: str
    observed_on: str
    freshness_days: int
    target_api_effective_from: str
    target_api_before: int
    target_api_on_or_after: int
    app_name_max_chars: int
    short_description_max_chars: int
    full_description_max_chars: int
    internal_tester_limit: int
    personal_account_rule_created_after: str
    personal_account_min_closed_testers: int
    personal_account_min_closed_days: int
    official_sources: tuple[str, ...]

    def __post_init__(self) -> None:
        _stable(self.policy_id, "policy_id")
        observed = _iso_date(self.observed_on, "observed_on")
        effective = _iso_date(self.target_api_effective_from, "target_api_effective_from")
        threshold = _iso_date(
            self.personal_account_rule_created_after,
            "personal_account_rule_created_after",
        )
        if observed > effective and self.target_api_before > self.target_api_on_or_after:
            raise ValueError("target API policy progression is inconsistent")
        if threshold > observed:
            raise ValueError("personal-account policy threshold cannot postdate observation")
        if not 1 <= self.freshness_days <= 366:
            raise ValueError("freshness_days outside bounded range")
        for field_name in (
            "target_api_before",
            "target_api_on_or_after",
            "app_name_max_chars",
            "short_description_max_chars",
            "full_description_max_chars",
            "internal_tester_limit",
            "personal_account_min_closed_testers",
            "personal_account_min_closed_days",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 1:
                raise ValueError(f"{field_name} must be positive")
        if not self.official_sources or len(self.official_sources) > 16:
            raise ValueError("policy snapshot requires 1..16 official sources")
        sources = tuple(sorted(set(self.official_sources)))
        for source in sources:
            _https_url(source, "official source", official_only=True)
        object.__setattr__(self, "official_sources", sources)

    def required_target_api(self, on_date: str) -> int:
        target_date = _iso_date(on_date, "evaluation date")
        effective = _iso_date(self.target_api_effective_from, "target_api_effective_from")
        return self.target_api_on_or_after if target_date >= effective else self.target_api_before

    def freshness(self, on_date: str) -> PlayPolicyFreshness:
        target_date = _iso_date(on_date, "evaluation date")
        observed = _iso_date(self.observed_on, "observed_on")
        age = (target_date - observed).days
        return (
            PlayPolicyFreshness.CURRENT
            if 0 <= age <= self.freshness_days
            else PlayPolicyFreshness.STALE
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "observed_on": self.observed_on,
            "freshness_days": self.freshness_days,
            "target_api_effective_from": self.target_api_effective_from,
            "target_api_before": self.target_api_before,
            "target_api_on_or_after": self.target_api_on_or_after,
            "app_name_max_chars": self.app_name_max_chars,
            "short_description_max_chars": self.short_description_max_chars,
            "full_description_max_chars": self.full_description_max_chars,
            "internal_tester_limit": self.internal_tester_limit,
            "personal_account_rule_created_after": self.personal_account_rule_created_after,
            "personal_account_min_closed_testers": self.personal_account_min_closed_testers,
            "personal_account_min_closed_days": self.personal_account_min_closed_days,
            "official_sources": list(self.official_sources),
        }

    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


@dataclass(frozen=True, slots=True)
class PlayLocalizedListing:
    locale: str
    app_name: str
    short_description: str
    full_description: str

    def __post_init__(self) -> None:
        if _LOCALE_RE.fullmatch(self.locale) is None:
            raise ValueError("invalid Play listing locale")
        for field_name in ("app_name", "short_description", "full_description"):
            value = getattr(self, field_name)
            if not value.strip() or "\x00" in value:
                raise ValueError(f"{field_name} must be non-empty text")

    def to_dict(self) -> dict[str, object]:
        return {
            "locale": self.locale,
            "app_name": self.app_name,
            "short_description": self.short_description,
            "full_description": self.full_description,
        }


@dataclass(frozen=True, slots=True)
class PlayStoreAsset:
    kind: PlayAssetKind
    sha256: str
    locale: str | None = None

    def __post_init__(self) -> None:
        _sha(self.sha256, "store asset digest")
        if self.locale is not None and _LOCALE_RE.fullmatch(self.locale) is None:
            raise ValueError("invalid store asset locale")

    def to_dict(self) -> dict[str, object]:
        return {"kind": self.kind.value, "sha256": self.sha256, "locale": self.locale}


@dataclass(frozen=True, slots=True)
class PlayStoreMetadata:
    application_id: str
    localizations: tuple[PlayLocalizedListing, ...]
    assets: tuple[PlayStoreAsset, ...] = ()

    def __post_init__(self) -> None:
        if _APP_ID_RE.fullmatch(self.application_id) is None:
            raise ValueError("invalid Play metadata application_id")
        localizations = tuple(sorted(self.localizations, key=lambda item: item.locale.lower()))
        if not localizations or len(localizations) > 128:
            raise ValueError("Play metadata requires 1..128 localizations")
        locales = [item.locale.lower() for item in localizations]
        if len(set(locales)) != len(locales):
            raise ValueError("duplicate Play listing locale")
        assets = tuple(
            sorted(
                self.assets,
                key=lambda item: (item.kind.value, item.locale or "", item.sha256),
            )
        )
        if len(assets) > 512:
            raise ValueError("too many Play store assets")
        object.__setattr__(self, "localizations", localizations)
        object.__setattr__(self, "assets", assets)

    def to_dict(self) -> dict[str, object]:
        return {
            "application_id": self.application_id,
            "localizations": [item.to_dict() for item in self.localizations],
            "assets": [item.to_dict() for item in self.assets],
        }


@dataclass(frozen=True, slots=True)
class PlayDataSafetyDeclaration:
    state: PlayDeclarationState
    privacy_policy_url: str | None = None
    third_party_sdks_reviewed: bool = False

    def __post_init__(self) -> None:
        if self.privacy_policy_url is not None:
            _https_url(self.privacy_policy_url, "privacy_policy_url")
        if self.state is PlayDeclarationState.COMPLETE:
            if self.privacy_policy_url is None or not self.third_party_sdks_reviewed:
                raise ValueError("complete Data safety declaration requires privacy policy and SDK review")

    def to_dict(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "privacy_policy_present": self.privacy_policy_url is not None,
            "third_party_sdks_reviewed": self.third_party_sdks_reviewed,
        }


@dataclass(frozen=True, slots=True)
class PlayContentRatingDeclaration:
    state: PlayDeclarationState
    questionnaire_sha256: str | None = None

    def __post_init__(self) -> None:
        if self.questionnaire_sha256 is not None:
            _sha(self.questionnaire_sha256, "content-rating questionnaire digest")
        if self.state is PlayDeclarationState.COMPLETE and self.questionnaire_sha256 is None:
            raise ValueError("complete content rating requires questionnaire digest")

    def to_dict(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "questionnaire_sha256": self.questionnaire_sha256,
        }


@dataclass(frozen=True, slots=True)
class PlayPermissionDeclaration:
    permission: str
    play_declaration_required: bool = False
    play_declaration_complete: bool = False

    def __post_init__(self) -> None:
        if _PERMISSION_RE.fullmatch(self.permission) is None:
            raise ValueError("invalid Android permission identifier")
        if self.play_declaration_complete and not self.play_declaration_required:
            raise ValueError("permission cannot complete a Play declaration that is not required")

    def to_dict(self) -> dict[str, object]:
        return {
            "permission": self.permission,
            "play_declaration_required": self.play_declaration_required,
            "play_declaration_complete": self.play_declaration_complete,
        }


@dataclass(frozen=True, slots=True)
class PlaySdkDeclaration:
    sdk_id: str
    policy_reviewed: bool
    data_safety_accounted: bool

    def __post_init__(self) -> None:
        _stable(self.sdk_id, "sdk_id")

    def to_dict(self) -> dict[str, object]:
        return {
            "sdk_id": self.sdk_id,
            "policy_reviewed": self.policy_reviewed,
            "data_safety_accounted": self.data_safety_accounted,
        }


@dataclass(frozen=True, slots=True)
class PlayAccountContext:
    kind: PlayAccountKind
    created_on: str | None = None
    closed_testers_continuous: int = 0
    closed_test_days_continuous: int = 0
    production_access_granted: bool = False

    def __post_init__(self) -> None:
        if self.created_on is not None:
            _iso_date(self.created_on, "account created_on")
        if self.kind is PlayAccountKind.PERSONAL and self.created_on is None:
            raise ValueError("personal Play account context requires created_on")
        if self.closed_testers_continuous < 0 or self.closed_test_days_continuous < 0:
            raise ValueError("closed-test counters cannot be negative")

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "created_on": self.created_on,
            "closed_testers_continuous": self.closed_testers_continuous,
            "closed_test_days_continuous": self.closed_test_days_continuous,
            "production_access_granted": self.production_access_granted,
        }


@dataclass(frozen=True, slots=True)
class PlayReleaseIntent:
    release_id: str
    application_id: str
    track: PlayReleaseTrack
    release_kind: PlayReleaseKind
    rollout_percent: int | None = None
    planned_tester_count: int | None = None

    def __post_init__(self) -> None:
        _stable(self.release_id, "release_id")
        if _APP_ID_RE.fullmatch(self.application_id) is None:
            raise ValueError("invalid release application_id")
        if self.rollout_percent is not None and not 1 <= self.rollout_percent <= 100:
            raise ValueError("rollout_percent must be 1..100")
        if self.planned_tester_count is not None and not 1 <= self.planned_tester_count <= 1_000_000:
            raise ValueError("planned_tester_count outside bounded range")

    def to_dict(self) -> dict[str, object]:
        return {
            "release_id": self.release_id,
            "application_id": self.application_id,
            "track": self.track.value,
            "release_kind": self.release_kind.value,
            "rollout_percent": self.rollout_percent,
            "planned_tester_count": self.planned_tester_count,
        }


@dataclass(frozen=True, slots=True)
class PlayAabCandidate:
    application_id: str
    artifact_sha256: str
    target_sdk: int
    build_evidence_sha256: str
    signing_state: AndroidSigningState
    signing_artifact_sha256: str

    def __post_init__(self) -> None:
        if _APP_ID_RE.fullmatch(self.application_id) is None:
            raise ValueError("invalid AAB application_id")
        _sha(self.artifact_sha256, "AAB artifact digest")
        _sha(self.build_evidence_sha256, "Android build evidence digest")
        _sha(self.signing_artifact_sha256, "signing artifact digest")
        if self.target_sdk < 1:
            raise ValueError("target_sdk must be positive")
        if self.signing_artifact_sha256 != self.artifact_sha256:
            raise ValueError("AAB/signing artifact substitution detected")

    @classmethod
    def from_evidence(
        cls,
        build: AndroidBuildEvidence,
        signing: AndroidSigningInspection,
    ) -> "PlayAabCandidate":
        if build.status is not AndroidBuildStatus.PASS:
            raise ValueError("Play candidate requires PASS Android build evidence")
        aabs = tuple(item for item in build.artifacts if item.kind is AndroidArtifactKind.AAB)
        if len(aabs) != 1:
            raise ValueError("Play candidate requires exactly one validated AAB")
        aab = aabs[0]
        if signing.kind is not AndroidArtifactKind.AAB:
            raise ValueError("Play candidate signing evidence must describe an AAB")
        return cls(
            application_id=build.request.application_id,
            artifact_sha256=aab.sha256,
            target_sdk=build.request.target_sdk,
            build_evidence_sha256=build.digest(),
            signing_state=signing.state,
            signing_artifact_sha256=signing.artifact_sha256,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "application_id": self.application_id,
            "artifact_sha256": self.artifact_sha256,
            "target_sdk": self.target_sdk,
            "build_evidence_sha256": self.build_evidence_sha256,
            "signing_state": self.signing_state.value,
            "signing_artifact_sha256": self.signing_artifact_sha256,
        }


@dataclass(frozen=True, slots=True)
class PlayPolicyFinding:
    code: str
    severity: PlayFindingSeverity
    message: str

    def __post_init__(self) -> None:
        _stable(self.code, "finding code")
        if not self.message.strip() or len(self.message) > 512 or "\x00" in self.message:
            raise ValueError("finding message must be bounded text")

    def to_dict(self) -> dict[str, object]:
        return {"code": self.code, "severity": self.severity.value, "message": self.message}


@dataclass(frozen=True, slots=True)
class GooglePlayReadinessReport:
    schema_version: int
    source_sha: str
    evaluated_on: str
    policy_freshness: PlayPolicyFreshness
    policy_snapshot_sha256: str
    release: PlayReleaseIntent
    candidate: PlayAabCandidate
    metadata_sha256: str
    data_safety_sha256: str
    content_rating_sha256: str
    permissions_sha256: str
    sdks_sha256: str
    account_context_sha256: str | None
    findings: tuple[PlayPolicyFinding, ...]
    store_status: StoreReleaseStatus
    dry_run: bool = True
    publish_attempted: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("R13.7 readiness schema version must be 1")
        if _GIT_SHA_RE.fullmatch(self.source_sha) is None:
            raise ValueError("source_sha must be exact lowercase Git SHA")
        _iso_date(self.evaluated_on, "evaluated_on")
        _sha(self.policy_snapshot_sha256, "policy snapshot digest")
        _sha(self.metadata_sha256, "metadata digest")
        _sha(self.data_safety_sha256, "Data safety declaration digest")
        _sha(self.content_rating_sha256, "content rating declaration digest")
        _sha(self.permissions_sha256, "permissions declaration digest")
        _sha(self.sdks_sha256, "SDK declaration digest")
        if self.account_context_sha256 is not None:
            _sha(self.account_context_sha256, "account context digest")
        if not self.dry_run or self.publish_attempted:
            raise ValueError("R13.7 core readiness report must remain dry-run and non-publishing")
        findings = tuple(sorted(self.findings, key=lambda item: (item.severity.value, item.code)))
        blockers = tuple(item.code for item in findings if item.severity is PlayFindingSeverity.BLOCKER)
        if self.store_status.platform is not MobilePlatform.ANDROID:
            raise ValueError("R13.7 store status must target Android")
        if blockers != self.store_status.blockers:
            raise ValueError("store status blockers must equal readiness blocker findings")
        object.__setattr__(self, "findings", findings)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "evaluated_on": self.evaluated_on,
            "dry_run": self.dry_run,
            "publish_attempted": self.publish_attempted,
            "policy_freshness": self.policy_freshness.value,
            "policy_snapshot_sha256": self.policy_snapshot_sha256,
            "release": self.release.to_dict(),
            "candidate": self.candidate.to_dict(),
            "metadata_sha256": self.metadata_sha256,
            "data_safety_sha256": self.data_safety_sha256,
            "content_rating_sha256": self.content_rating_sha256,
            "permissions_sha256": self.permissions_sha256,
            "sdks_sha256": self.sdks_sha256,
            "account_context_sha256": self.account_context_sha256,
            "findings": [item.to_dict() for item in self.findings],
            "store_status": self.store_status.canonical(),
        }

    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


def current_google_play_policy_snapshot() -> GooglePlayPolicySnapshot:
    return GooglePlayPolicySnapshot(
        policy_id="google-play-2026-08-26",
        observed_on="2026-08-26",
        freshness_days=30,
        target_api_effective_from="2026-08-31",
        target_api_before=35,
        target_api_on_or_after=36,
        app_name_max_chars=30,
        short_description_max_chars=80,
        full_description_max_chars=4000,
        internal_tester_limit=100,
        personal_account_rule_created_after="2023-11-13",
        personal_account_min_closed_testers=12,
        personal_account_min_closed_days=14,
        official_sources=(
            "https://developer.android.com/google/play/requirements/target-sdk",
            "https://support.google.com/googleplay/android-developer/answer/11926878",
            "https://support.google.com/googleplay/android-developer/answer/9845334",
            "https://support.google.com/googleplay/android-developer/answer/9859152",
            "https://support.google.com/googleplay/android-developer/answer/10787469",
            "https://support.google.com/googleplay/android-developer/answer/9898843",
            "https://support.google.com/googleplay/android-developer/answer/9859348",
            "https://support.google.com/googleplay/android-developer/answer/14151465",
            "https://support.google.com/googleplay/android-developer/answer/9859455",
        ),
    )


def evaluate_google_play_readiness(
    *,
    source_sha: str,
    evaluated_on: str,
    policy: GooglePlayPolicySnapshot,
    release: PlayReleaseIntent,
    candidate: PlayAabCandidate,
    metadata: PlayStoreMetadata,
    data_safety: PlayDataSafetyDeclaration,
    content_rating: PlayContentRatingDeclaration,
    permissions: Sequence[PlayPermissionDeclaration] = (),
    sdks: Sequence[PlaySdkDeclaration] = (),
    account: PlayAccountContext | None = None,
) -> GooglePlayReadinessReport:
    if _GIT_SHA_RE.fullmatch(source_sha) is None:
        raise ValueError("source_sha must be exact lowercase Git SHA")
    _iso_date(evaluated_on, "evaluated_on")
    findings: list[PlayPolicyFinding] = []

    def block(code: str, message: str) -> None:
        findings.append(PlayPolicyFinding(code, PlayFindingSeverity.BLOCKER, message))

    def warn(code: str, message: str) -> None:
        findings.append(PlayPolicyFinding(code, PlayFindingSeverity.WARNING, message))

    freshness = policy.freshness(evaluated_on)
    if freshness is PlayPolicyFreshness.STALE:
        block("policy_snapshot_stale", "official Google Play policy snapshot must be refreshed")

    if (
        release.application_id != candidate.application_id
        or metadata.application_id != candidate.application_id
    ):
        block("package_identity_mismatch", "release, metadata and AAB application identifiers must match")

    required_api = policy.required_target_api(evaluated_on)
    if candidate.target_sdk < required_api:
        block(
            "target_api_below_effective_requirement",
            f"target SDK {candidate.target_sdk} is below required API {required_api}",
        )

    for listing in metadata.localizations:
        if len(listing.app_name) > policy.app_name_max_chars:
            block("listing_app_name_too_long", f"{listing.locale} app name exceeds policy snapshot limit")
        if len(listing.short_description) > policy.short_description_max_chars:
            block(
                "listing_short_description_too_long",
                f"{listing.locale} short description exceeds policy snapshot limit",
            )
        if len(listing.full_description) > policy.full_description_max_chars:
            block(
                "listing_full_description_too_long",
                f"{listing.locale} full description exceeds policy snapshot limit",
            )

    if release.release_kind is PlayReleaseKind.FIRST_RELEASE and release.rollout_percent is not None:
        block(
            "staged_rollout_unavailable_first_release",
            "Google Play rollout percentage is unavailable for a first release",
        )
    if (
        release.track is PlayReleaseTrack.INTERNAL
        and release.planned_tester_count is not None
        and release.planned_tester_count > policy.internal_tester_limit
    ):
        block(
            "internal_tester_limit_exceeded",
            "planned internal tester count exceeds the policy snapshot limit",
        )

    data_safety_required = release.track is not PlayReleaseTrack.INTERNAL
    if data_safety_required and data_safety.state is not PlayDeclarationState.COMPLETE:
        block("data_safety_missing", "Data safety declaration is required outside internal-only testing")
    elif not data_safety_required and data_safety.state is PlayDeclarationState.MISSING:
        warn("data_safety_internal_exemption", "internal-only testing is exempt from the Data safety section")

    if (
        release.track is not PlayReleaseTrack.INTERNAL
        and content_rating.state is not PlayDeclarationState.COMPLETE
    ):
        block(
            "content_rating_missing",
            "non-internal Play readiness requires completed IARC content-rating evidence",
        )

    for permission in sorted(permissions, key=lambda item: item.permission):
        if permission.play_declaration_required and not permission.play_declaration_complete:
            block(
                "unsafe_permission_declaration",
                f"required Play declaration is incomplete for {permission.permission}",
            )

    for sdk in sorted(sdks, key=lambda item: item.sdk_id):
        if not sdk.policy_reviewed:
            block("sdk_policy_review_missing", f"SDK policy review is incomplete for {sdk.sdk_id}")
        if data_safety_required and not sdk.data_safety_accounted:
            block("sdk_data_safety_missing", f"SDK Data safety accounting is incomplete for {sdk.sdk_id}")

    if release.track in {PlayReleaseTrack.OPEN, PlayReleaseTrack.PRODUCTION}:
        if account is None or account.kind is PlayAccountKind.UNKNOWN:
            block(
                "play_account_context_missing",
                "open/production track capability requires explicit account context",
            )
        elif account.kind is PlayAccountKind.PERSONAL:
            created = _iso_date(account.created_on or "", "account created_on")
            threshold = _iso_date(policy.personal_account_rule_created_after, "personal account threshold")
            if created > threshold and not account.production_access_granted:
                if account.closed_testers_continuous < policy.personal_account_min_closed_testers:
                    block(
                        "personal_account_closed_testers_insufficient",
                        "personal account has not met the scoped continuous closed-tester threshold",
                    )
                if account.closed_test_days_continuous < policy.personal_account_min_closed_days:
                    block(
                        "personal_account_closed_test_days_insufficient",
                        "personal account has not met the scoped continuous closed-test duration",
                    )
                if release.track is PlayReleaseTrack.OPEN:
                    block(
                        "personal_account_open_track_requires_production_access",
                        "open testing requires production access for this scoped personal-account policy",
                    )
                if release.track is PlayReleaseTrack.PRODUCTION:
                    block(
                        "personal_account_production_access_not_granted",
                        "production access has not yet been granted for this scoped personal-account policy",
                    )

    store_signing_states = {
        AndroidSigningState.UPLOAD_SIGNED,
        AndroidSigningState.PLAY_APP_SIGNING_READY,
    }
    if candidate.signing_state not in store_signing_states:
        block("play_signing_not_ready", "AAB lacks upload/Play App Signing readiness evidence")

    unique: dict[tuple[str, PlayFindingSeverity], PlayPolicyFinding] = {}
    for finding in findings:
        unique[(finding.code, finding.severity)] = finding
    ordered = tuple(sorted(unique.values(), key=lambda item: (item.severity.value, item.code)))
    blocker_codes = tuple(item.code for item in ordered if item.severity is PlayFindingSeverity.BLOCKER)

    if blocker_codes:
        readiness = StoreReadinessState.BLOCKED
    elif release.track is PlayReleaseTrack.INTERNAL:
        readiness = StoreReadinessState.TEST_READY
    else:
        readiness = StoreReadinessState.STORE_READY

    status = StoreReleaseStatus(
        release_id=release.release_id,
        platform=MobilePlatform.ANDROID,
        readiness=readiness,
        artifact_digest=candidate.artifact_sha256,
        compliance_snapshot_digest=policy.digest(),
        blockers=blocker_codes,
    )
    return GooglePlayReadinessReport(
        schema_version=1,
        source_sha=source_sha,
        evaluated_on=evaluated_on,
        policy_freshness=freshness,
        policy_snapshot_sha256=policy.digest(),
        release=release,
        candidate=candidate,
        metadata_sha256=canonical_sha256(metadata.to_dict()),
        data_safety_sha256=canonical_sha256(data_safety.to_dict()),
        content_rating_sha256=canonical_sha256(content_rating.to_dict()),
        permissions_sha256=canonical_sha256(
            {
                "permissions": [
                    item.to_dict()
                    for item in sorted(permissions, key=lambda item: item.permission)
                ]
            }
        ),
        sdks_sha256=canonical_sha256(
            {
                "sdks": [
                    item.to_dict() for item in sorted(sdks, key=lambda item: item.sdk_id)
                ]
            }
        ),
        account_context_sha256=(canonical_sha256(account.to_dict()) if account is not None else None),
        findings=ordered,
        store_status=status,
    )
