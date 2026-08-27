from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from functools import total_ordering
from typing import Iterable
from urllib.parse import urlparse

from .contracts import MobilePackageKind, MobilePlatform, canonical_json_bytes

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_STABLE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,127}$")
_APPLE_BUILD_RE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){0,3}$")
_SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\."
    r"(0|[1-9][0-9]*)\."
    r"(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
_MAX_ANDROID_VERSION_CODE = 2_147_483_647
_MAX_RELEASE_REVISION = 1_000_000_000
_MAX_EVIDENCE = 128
_MAX_ARTIFACTS = 32
_MAX_ROLLBACK_POINTS = 128


def _stable_id(value: str, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable identifier")
    return value


def _sha256(value: str, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _digest(payload: dict[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _https_url(value: str, field: str) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError(f"{field} must be a bounded HTTPS URL")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError(f"{field} must be a public HTTPS URL without credentials")
    return value


def _numeric_build_tuple(value: str) -> tuple[int, ...]:
    if _APPLE_BUILD_RE.fullmatch(value) is None:
        raise ValueError("apple build number must be a bounded dotted numeric value")
    parts = tuple(int(part) for part in value.split("."))
    if any(part > _MAX_ANDROID_VERSION_CODE for part in parts):
        raise ValueError("apple build number segment exceeds bounded range")
    return parts


@total_ordering
@dataclass(frozen=True, slots=True)
class SemanticVersion:
    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()
    build: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if min(self.major, self.minor, self.patch) < 0:
            raise ValueError("semantic version components must be non-negative")
        text = str(self)
        match = _SEMVER_RE.fullmatch(text)
        if match is None:
            raise ValueError("invalid SemVer 2.0.0 value")

    @classmethod
    def parse(cls, value: str) -> "SemanticVersion":
        if not isinstance(value, str) or len(value) > 256:
            raise ValueError("semantic version must be bounded text")
        match = _SEMVER_RE.fullmatch(value)
        if match is None:
            raise ValueError("invalid SemVer 2.0.0 value")
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=tuple(match.group(4).split(".")) if match.group(4) else (),
            build=tuple(match.group(5).split(".")) if match.group(5) else (),
        )

    def __str__(self) -> str:
        value = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            value += "-" + ".".join(self.prerelease)
        if self.build:
            value += "+" + ".".join(self.build)
        return value

    def _compare_prerelease(self, other: "SemanticVersion") -> int:
        if not self.prerelease and not other.prerelease:
            return 0
        if not self.prerelease:
            return 1
        if not other.prerelease:
            return -1
        for left, right in zip(self.prerelease, other.prerelease):
            if left == right:
                continue
            left_numeric = left.isdigit()
            right_numeric = right.isdigit()
            if left_numeric and right_numeric:
                return -1 if int(left) < int(right) else 1
            if left_numeric != right_numeric:
                return -1 if left_numeric else 1
            return -1 if left < right else 1
        if len(self.prerelease) == len(other.prerelease):
            return 0
        return -1 if len(self.prerelease) < len(other.prerelease) else 1

    def compare_precedence(self, other: "SemanticVersion") -> int:
        left = (self.major, self.minor, self.patch)
        right = (other.major, other.minor, other.patch)
        if left != right:
            return -1 if left < right else 1
        return self._compare_prerelease(other)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return self.compare_precedence(other) < 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return False
        return self.compare_precedence(other) == 0


class ReleaseChannel(StrEnum):
    INTERNAL = "INTERNAL"
    BETA = "BETA"
    PRODUCTION = "PRODUCTION"


class ReleaseProvider(StrEnum):
    LOCAL = "LOCAL"
    GOOGLE_PLAY = "GOOGLE_PLAY"
    APP_STORE = "APP_STORE"


class RolloutMode(StrEnum):
    IMMEDIATE = "IMMEDIATE"
    STAGED_PERCENT = "STAGED_PERCENT"
    PROVIDER_PHASED = "PROVIDER_PHASED"


class RolloutAction(StrEnum):
    START = "START"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    HALT = "HALT"
    COMPLETE = "COMPLETE"


class PromotionDecision(StrEnum):
    PROMOTED = "PROMOTED"
    REVISION_CONFLICT = "REVISION_CONFLICT"
    TRAIN_MISMATCH = "TRAIN_MISMATCH"
    CHANNEL_MISMATCH = "CHANNEL_MISMATCH"
    AUTHORITATIVE_MISMATCH = "AUTHORITATIVE_MISMATCH"
    CANDIDATE_SUBSTITUTION = "CANDIDATE_SUBSTITUTION"
    ARTIFACT_SUBSTITUTION = "ARTIFACT_SUBSTITUTION"
    EVIDENCE_SUBSTITUTION = "EVIDENCE_SUBSTITUTION"
    VERSION_REGRESSION = "VERSION_REGRESSION"
    ANDROID_BUILD_REGRESSION = "ANDROID_BUILD_REGRESSION"
    APPLE_BUILD_REGRESSION = "APPLE_BUILD_REGRESSION"
    RELEASED_VERSION_IMMUTABLE = "RELEASED_VERSION_IMMUTABLE"
    ALREADY_AUTHORITATIVE = "ALREADY_AUTHORITATIVE"


@dataclass(frozen=True, slots=True)
class ReleaseVersion:
    product_version: SemanticVersion
    android_version_code: int | None = None
    apple_build_number: str | None = None

    def __post_init__(self) -> None:
        if self.android_version_code is not None:
            if not 1 <= self.android_version_code <= _MAX_ANDROID_VERSION_CODE:
                raise ValueError("android_version_code is outside bounded positive range")
        if self.apple_build_number is not None:
            _numeric_build_tuple(self.apple_build_number)
        if self.android_version_code is None and self.apple_build_number is None:
            raise ValueError("release version must map at least one platform build identity")

    def to_dict(self) -> dict[str, object]:
        return {
            "product_version": str(self.product_version),
            "android_version_code": self.android_version_code,
            "apple_build_number": self.apple_build_number,
        }


@dataclass(frozen=True, slots=True)
class ReleaseArtifactBinding:
    artifact_id: str
    platform: MobilePlatform
    package_kind: MobilePackageKind
    artifact_sha256: str
    provenance_sha256: str

    def __post_init__(self) -> None:
        _stable_id(self.artifact_id, "artifact_id")
        _sha256(self.artifact_sha256, "artifact_sha256")
        _sha256(self.provenance_sha256, "provenance_sha256")
        if self.platform is MobilePlatform.ANDROID and self.package_kind not in {
            MobilePackageKind.APK,
            MobilePackageKind.AAB,
        }:
            raise ValueError("Android release artifact must be APK or AAB")
        if self.platform in {MobilePlatform.IOS, MobilePlatform.IPADOS} and self.package_kind not in {
            MobilePackageKind.APP,
            MobilePackageKind.XCARCHIVE,
            MobilePackageKind.IPA,
        }:
            raise ValueError("Apple release artifact has an incompatible package kind")

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "platform": self.platform.value,
            "package_kind": self.package_kind.value,
            "artifact_sha256": self.artifact_sha256,
            "provenance_sha256": self.provenance_sha256,
        }


@dataclass(frozen=True, slots=True)
class RolloutPolicyEvidence:
    provider: ReleaseProvider
    source_url: str
    retrieved_on: date
    evidence_sha256: str
    allowed_modes: tuple[RolloutMode, ...]
    allowed_actions: tuple[RolloutAction, ...]
    automatic_schedule_percent: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if self.provider is ReleaseProvider.LOCAL:
            raise ValueError("provider policy evidence must identify a real store provider")
        _https_url(self.source_url, "source_url")
        _sha256(self.evidence_sha256, "evidence_sha256")
        modes = tuple(sorted(set(self.allowed_modes), key=lambda item: item.value))
        actions = tuple(sorted(set(self.allowed_actions), key=lambda item: item.value))
        if not modes or not actions:
            raise ValueError("rollout policy evidence requires bounded modes and actions")
        object.__setattr__(self, "allowed_modes", modes)
        object.__setattr__(self, "allowed_actions", actions)
        schedule = tuple(self.automatic_schedule_percent)
        if any(value < 1 or value > 100 for value in schedule):
            raise ValueError("automatic rollout schedule percentages must be 1..100")
        if schedule and (tuple(sorted(schedule)) != schedule or schedule[-1] != 100):
            raise ValueError("automatic rollout schedule must increase monotonically to 100")
        if self.provider is ReleaseProvider.GOOGLE_PLAY and RolloutMode.PROVIDER_PHASED in modes:
            raise ValueError("Google Play evidence cannot claim provider-defined phased scheduling")
        if self.provider is ReleaseProvider.APP_STORE:
            if RolloutMode.STAGED_PERCENT in modes:
                raise ValueError("App Store evidence cannot claim arbitrary staged percentage control")
            if RolloutMode.PROVIDER_PHASED in modes and not schedule:
                raise ValueError("App Store phased evidence requires an explicit versioned schedule")
        object.__setattr__(self, "automatic_schedule_percent", schedule)

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider.value,
            "source_url": self.source_url,
            "retrieved_on": self.retrieved_on.isoformat(),
            "evidence_sha256": self.evidence_sha256,
            "allowed_modes": [item.value for item in self.allowed_modes],
            "allowed_actions": [item.value for item in self.allowed_actions],
            "automatic_schedule_percent": list(self.automatic_schedule_percent),
        }


@dataclass(frozen=True, slots=True)
class RolloutIntent:
    provider: ReleaseProvider
    mode: RolloutMode
    action: RolloutAction
    percentage_basis_points: int | None = None
    policy_evidence_sha256: str | None = None

    def __post_init__(self) -> None:
        if self.provider is ReleaseProvider.LOCAL:
            if self.mode is not RolloutMode.IMMEDIATE or self.percentage_basis_points is not None:
                raise ValueError("local rollout intent supports only immediate local authority")
            if self.policy_evidence_sha256 is not None:
                raise ValueError("local rollout intent cannot bind store policy evidence")
            return
        if self.policy_evidence_sha256 is None:
            raise ValueError("store rollout intent requires versioned policy evidence")
        _sha256(self.policy_evidence_sha256, "policy_evidence_sha256")
        if self.provider is ReleaseProvider.GOOGLE_PLAY:
            if self.mode is RolloutMode.PROVIDER_PHASED:
                raise ValueError("Google Play rollout intent cannot use provider phased mode")
            if self.mode is RolloutMode.STAGED_PERCENT:
                if self.percentage_basis_points is None or not 1 <= self.percentage_basis_points <= 10_000:
                    raise ValueError("Google staged rollout requires 1..10000 basis points")
            elif self.percentage_basis_points is not None:
                raise ValueError("immediate rollout cannot carry percentage basis points")
        elif self.provider is ReleaseProvider.APP_STORE:
            if self.mode is RolloutMode.STAGED_PERCENT:
                raise ValueError("App Store rollout percentage is provider-defined")
            if self.percentage_basis_points is not None:
                raise ValueError("App Store rollout intent cannot choose an arbitrary percentage")

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider.value,
            "mode": self.mode.value,
            "action": self.action.value,
            "percentage_basis_points": self.percentage_basis_points,
            "policy_evidence_sha256": self.policy_evidence_sha256,
        }


@dataclass(frozen=True, slots=True)
class ReleaseCandidate:
    candidate_id: str
    train_id: str
    channel: ReleaseChannel
    version: ReleaseVersion
    artifacts: tuple[ReleaseArtifactBinding, ...]
    evidence_sha256: tuple[str, ...]
    changelog_sha256: str
    sbom_sha256: str
    compliance_sha256: str
    rollout_intent: RolloutIntent | None = None

    def __post_init__(self) -> None:
        _stable_id(self.candidate_id, "candidate_id")
        _stable_id(self.train_id, "train_id")
        artifacts = tuple(sorted(self.artifacts, key=lambda item: (item.platform.value, item.package_kind.value, item.artifact_id)))
        if not artifacts or len(artifacts) > _MAX_ARTIFACTS:
            raise ValueError("release candidate requires 1..32 immutable artifacts")
        keys = {(item.platform, item.package_kind, item.artifact_id) for item in artifacts}
        if len(keys) != len(artifacts):
            raise ValueError("release candidate cannot contain duplicate artifact identities")
        object.__setattr__(self, "artifacts", artifacts)
        evidence = tuple(sorted(set(self.evidence_sha256)))
        if not evidence or len(evidence) > _MAX_EVIDENCE:
            raise ValueError("release candidate requires 1..128 evidence digests")
        for digest in evidence:
            _sha256(digest, "evidence_sha256")
        object.__setattr__(self, "evidence_sha256", evidence)
        _sha256(self.changelog_sha256, "changelog_sha256")
        _sha256(self.sbom_sha256, "sbom_sha256")
        _sha256(self.compliance_sha256, "compliance_sha256")
        platforms = {item.platform for item in artifacts}
        if MobilePlatform.ANDROID in platforms and self.version.android_version_code is None:
            raise ValueError("Android candidate requires android_version_code")
        if platforms & {MobilePlatform.IOS, MobilePlatform.IPADOS} and self.version.apple_build_number is None:
            raise ValueError("Apple candidate requires apple_build_number")

    def artifact_set_sha256(self) -> str:
        return _digest({"artifacts": [item.to_dict() for item in self.artifacts]})

    def evidence_set_sha256(self) -> str:
        return _digest({
            "evidence_sha256": list(self.evidence_sha256),
            "changelog_sha256": self.changelog_sha256,
            "sbom_sha256": self.sbom_sha256,
            "compliance_sha256": self.compliance_sha256,
        })

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "train_id": self.train_id,
            "channel": self.channel.value,
            "version": self.version.to_dict(),
            "artifacts": [item.to_dict() for item in self.artifacts],
            "evidence_sha256": list(self.evidence_sha256),
            "changelog_sha256": self.changelog_sha256,
            "sbom_sha256": self.sbom_sha256,
            "compliance_sha256": self.compliance_sha256,
            "rollout_intent": self.rollout_intent.to_dict() if self.rollout_intent else None,
        }

    def digest(self) -> str:
        return _digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class ReleasedVersionSeal:
    product_version: str
    candidate_sha256: str
    artifact_set_sha256: str

    def __post_init__(self) -> None:
        SemanticVersion.parse(self.product_version)
        _sha256(self.candidate_sha256, "candidate_sha256")
        _sha256(self.artifact_set_sha256, "artifact_set_sha256")

    def to_dict(self) -> dict[str, object]:
        return {
            "product_version": self.product_version,
            "candidate_sha256": self.candidate_sha256,
            "artifact_set_sha256": self.artifact_set_sha256,
        }


@dataclass(frozen=True, slots=True)
class RollbackPoint:
    rollback_point_id: str
    train_id: str
    channel: ReleaseChannel
    revision: int
    candidate_sha256: str
    artifact_set_sha256: str
    product_version: str
    android_version_code: int | None
    apple_build_number: str | None

    def __post_init__(self) -> None:
        _stable_id(self.rollback_point_id, "rollback_point_id")
        _stable_id(self.train_id, "train_id")
        if not 0 <= self.revision <= _MAX_RELEASE_REVISION:
            raise ValueError("rollback revision outside bounded range")
        _sha256(self.candidate_sha256, "candidate_sha256")
        _sha256(self.artifact_set_sha256, "artifact_set_sha256")
        SemanticVersion.parse(self.product_version)
        if self.android_version_code is not None and not 1 <= self.android_version_code <= _MAX_ANDROID_VERSION_CODE:
            raise ValueError("rollback Android versionCode invalid")
        if self.apple_build_number is not None:
            _numeric_build_tuple(self.apple_build_number)

    def to_dict(self) -> dict[str, object]:
        return {
            "rollback_point_id": self.rollback_point_id,
            "train_id": self.train_id,
            "channel": self.channel.value,
            "revision": self.revision,
            "candidate_sha256": self.candidate_sha256,
            "artifact_set_sha256": self.artifact_set_sha256,
            "product_version": self.product_version,
            "android_version_code": self.android_version_code,
            "apple_build_number": self.apple_build_number,
        }


@dataclass(frozen=True, slots=True)
class ReleaseAuthorityState:
    train_id: str
    channel: ReleaseChannel
    revision: int = 0
    authoritative_candidate_sha256: str | None = None
    authoritative_artifact_set_sha256: str | None = None
    authoritative_product_version: str | None = None
    authoritative_android_version_code: int | None = None
    authoritative_apple_build_number: str | None = None
    released_version_seals: tuple[ReleasedVersionSeal, ...] = ()
    rollback_points: tuple[RollbackPoint, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.train_id, "train_id")
        if not 0 <= self.revision <= _MAX_RELEASE_REVISION:
            raise ValueError("release revision outside bounded range")
        authoritative_fields = (
            self.authoritative_candidate_sha256,
            self.authoritative_artifact_set_sha256,
            self.authoritative_product_version,
        )
        if any(value is None for value in authoritative_fields) and any(value is not None for value in authoritative_fields):
            raise ValueError("authoritative release identity must be complete or absent")
        if self.authoritative_candidate_sha256 is not None:
            _sha256(self.authoritative_candidate_sha256, "authoritative_candidate_sha256")
            _sha256(self.authoritative_artifact_set_sha256 or "", "authoritative_artifact_set_sha256")
            SemanticVersion.parse(self.authoritative_product_version or "")
        if self.authoritative_android_version_code is not None and not 1 <= self.authoritative_android_version_code <= _MAX_ANDROID_VERSION_CODE:
            raise ValueError("authoritative Android versionCode invalid")
        if self.authoritative_apple_build_number is not None:
            _numeric_build_tuple(self.authoritative_apple_build_number)
        seals = tuple(sorted(self.released_version_seals, key=lambda item: SemanticVersion.parse(item.product_version)))
        if len({item.product_version for item in seals}) != len(seals):
            raise ValueError("released version seals must be unique by product version")
        object.__setattr__(self, "released_version_seals", seals)
        points = tuple(sorted(self.rollback_points, key=lambda item: (item.revision, item.rollback_point_id)))
        if len(points) > _MAX_ROLLBACK_POINTS:
            raise ValueError("rollback point history exceeds bounded retention")
        if len({item.rollback_point_id for item in points}) != len(points):
            raise ValueError("rollback point identities must be unique")
        object.__setattr__(self, "rollback_points", points)

    def to_dict(self) -> dict[str, object]:
        return {
            "train_id": self.train_id,
            "channel": self.channel.value,
            "revision": self.revision,
            "authoritative_candidate_sha256": self.authoritative_candidate_sha256,
            "authoritative_artifact_set_sha256": self.authoritative_artifact_set_sha256,
            "authoritative_product_version": self.authoritative_product_version,
            "authoritative_android_version_code": self.authoritative_android_version_code,
            "authoritative_apple_build_number": self.authoritative_apple_build_number,
            "released_version_seals": [item.to_dict() for item in self.released_version_seals],
            "rollback_points": [item.to_dict() for item in self.rollback_points],
        }

    def digest(self) -> str:
        return _digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class PromotionRequest:
    promotion_id: str
    candidate: ReleaseCandidate
    expected_revision: int
    expected_candidate_sha256: str
    expected_artifact_set_sha256: str
    expected_evidence_set_sha256: str
    expected_authoritative_candidate_sha256: str | None = None

    def __post_init__(self) -> None:
        _stable_id(self.promotion_id, "promotion_id")
        if not 0 <= self.expected_revision <= _MAX_RELEASE_REVISION:
            raise ValueError("expected release revision outside bounded range")
        _sha256(self.expected_candidate_sha256, "expected_candidate_sha256")
        _sha256(self.expected_artifact_set_sha256, "expected_artifact_set_sha256")
        _sha256(self.expected_evidence_set_sha256, "expected_evidence_set_sha256")
        if self.expected_authoritative_candidate_sha256 is not None:
            _sha256(self.expected_authoritative_candidate_sha256, "expected_authoritative_candidate_sha256")


@dataclass(frozen=True, slots=True)
class PromotionOutcome:
    decision: PromotionDecision
    state: ReleaseAuthorityState
    rollback_point: RollbackPoint | None = None

    @property
    def promoted(self) -> bool:
        return self.decision is PromotionDecision.PROMOTED


def _failed(state: ReleaseAuthorityState, decision: PromotionDecision) -> PromotionOutcome:
    return PromotionOutcome(decision=decision, state=state)


def promote_release(state: ReleaseAuthorityState, request: PromotionRequest) -> PromotionOutcome:
    candidate = request.candidate
    if request.expected_revision != state.revision:
        return _failed(state, PromotionDecision.REVISION_CONFLICT)
    if candidate.train_id != state.train_id:
        return _failed(state, PromotionDecision.TRAIN_MISMATCH)
    if candidate.channel is not state.channel:
        return _failed(state, PromotionDecision.CHANNEL_MISMATCH)
    if request.expected_authoritative_candidate_sha256 != state.authoritative_candidate_sha256:
        return _failed(state, PromotionDecision.AUTHORITATIVE_MISMATCH)
    candidate_sha256 = candidate.digest()
    artifact_set_sha256 = candidate.artifact_set_sha256()
    evidence_set_sha256 = candidate.evidence_set_sha256()
    if candidate_sha256 != request.expected_candidate_sha256:
        return _failed(state, PromotionDecision.CANDIDATE_SUBSTITUTION)
    if artifact_set_sha256 != request.expected_artifact_set_sha256:
        return _failed(state, PromotionDecision.ARTIFACT_SUBSTITUTION)
    if evidence_set_sha256 != request.expected_evidence_set_sha256:
        return _failed(state, PromotionDecision.EVIDENCE_SUBSTITUTION)
    if state.authoritative_candidate_sha256 == candidate_sha256:
        return _failed(state, PromotionDecision.ALREADY_AUTHORITATIVE)

    version_text = str(candidate.version.product_version)
    for seal in state.released_version_seals:
        if seal.product_version == version_text and (
            seal.candidate_sha256 != candidate_sha256 or seal.artifact_set_sha256 != artifact_set_sha256
        ):
            return _failed(state, PromotionDecision.RELEASED_VERSION_IMMUTABLE)

    if state.authoritative_product_version is not None:
        current_version = SemanticVersion.parse(state.authoritative_product_version)
        if candidate.version.product_version.compare_precedence(current_version) <= 0:
            return _failed(state, PromotionDecision.VERSION_REGRESSION)
    if state.authoritative_android_version_code is not None and candidate.version.android_version_code is not None:
        if candidate.version.android_version_code <= state.authoritative_android_version_code:
            return _failed(state, PromotionDecision.ANDROID_BUILD_REGRESSION)
    if state.authoritative_apple_build_number is not None and candidate.version.apple_build_number is not None:
        if _numeric_build_tuple(candidate.version.apple_build_number) <= _numeric_build_tuple(state.authoritative_apple_build_number):
            return _failed(state, PromotionDecision.APPLE_BUILD_REGRESSION)

    rollback_point: RollbackPoint | None = None
    rollback_points = state.rollback_points
    if state.authoritative_candidate_sha256 is not None:
        rollback_point = RollbackPoint(
            rollback_point_id=f"rollback-{state.revision}-{state.authoritative_candidate_sha256[:12]}",
            train_id=state.train_id,
            channel=state.channel,
            revision=state.revision,
            candidate_sha256=state.authoritative_candidate_sha256,
            artifact_set_sha256=state.authoritative_artifact_set_sha256 or "",
            product_version=state.authoritative_product_version or "",
            android_version_code=state.authoritative_android_version_code,
            apple_build_number=state.authoritative_apple_build_number,
        )
        rollback_points = tuple((rollback_points + (rollback_point,))[-_MAX_ROLLBACK_POINTS:])

    seals = list(state.released_version_seals)
    if not any(item.product_version == version_text for item in seals):
        seals.append(
            ReleasedVersionSeal(
                product_version=version_text,
                candidate_sha256=candidate_sha256,
                artifact_set_sha256=artifact_set_sha256,
            )
        )

    new_state = ReleaseAuthorityState(
        train_id=state.train_id,
        channel=state.channel,
        revision=state.revision + 1,
        authoritative_candidate_sha256=candidate_sha256,
        authoritative_artifact_set_sha256=artifact_set_sha256,
        authoritative_product_version=version_text,
        authoritative_android_version_code=candidate.version.android_version_code,
        authoritative_apple_build_number=candidate.version.apple_build_number,
        released_version_seals=tuple(seals),
        rollback_points=rollback_points,
    )
    return PromotionOutcome(decision=PromotionDecision.PROMOTED, state=new_state, rollback_point=rollback_point)


def rollback_release(
    state: ReleaseAuthorityState,
    rollback_point_id: str,
    *,
    expected_revision: int,
) -> ReleaseAuthorityState:
    _stable_id(rollback_point_id, "rollback_point_id")
    if expected_revision != state.revision:
        raise ValueError("release revision conflict")
    matches = [point for point in state.rollback_points if point.rollback_point_id == rollback_point_id]
    if len(matches) != 1:
        raise ValueError("rollback point is missing or ambiguous")
    point = matches[0]
    if point.train_id != state.train_id or point.channel is not state.channel:
        raise ValueError("rollback point belongs to a different release authority")
    if state.authoritative_candidate_sha256 == point.candidate_sha256:
        raise ValueError("rollback point is already authoritative")
    return ReleaseAuthorityState(
        train_id=state.train_id,
        channel=state.channel,
        revision=state.revision + 1,
        authoritative_candidate_sha256=point.candidate_sha256,
        authoritative_artifact_set_sha256=point.artifact_set_sha256,
        authoritative_product_version=point.product_version,
        authoritative_android_version_code=point.android_version_code,
        authoritative_apple_build_number=point.apple_build_number,
        released_version_seals=state.released_version_seals,
        rollback_points=state.rollback_points,
    )


def bind_rollout_policy(intent: RolloutIntent, evidence: RolloutPolicyEvidence) -> None:
    if intent.provider is ReleaseProvider.LOCAL:
        if evidence.provider is not ReleaseProvider.LOCAL:
            raise ValueError("local rollout intent does not accept store evidence")
        return
    if intent.provider is not evidence.provider:
        raise ValueError("rollout policy provider mismatch")
    evidence_digest = _digest(evidence.to_dict())
    if intent.policy_evidence_sha256 != evidence_digest:
        raise ValueError("rollout policy evidence substitution detected")
    if intent.mode not in evidence.allowed_modes or intent.action not in evidence.allowed_actions:
        raise ValueError("rollout intent is not allowed by bound provider evidence")


def digest_policy_evidence(evidence: RolloutPolicyEvidence) -> str:
    return _digest(evidence.to_dict())


def digest_artifact_bindings(items: Iterable[ReleaseArtifactBinding]) -> str:
    ordered = tuple(sorted(items, key=lambda item: (item.platform.value, item.package_kind.value, item.artifact_id)))
    return _digest({"artifacts": [item.to_dict() for item in ordered]})
