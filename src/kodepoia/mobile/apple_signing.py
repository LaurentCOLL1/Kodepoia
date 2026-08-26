from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TypeAlias

from kodepoia.core.secrets import SecretRef, assert_secret_refs_only
from kodepoia.mobile.boundary import MobileBoundaryError, MobileToolchainBoundary
from kodepoia.mobile.contracts import MobileToolKind

_TEAM_ID_RE = re.compile(r"^[A-Z0-9]{10}$")
_PROFILE_UUID_RE = re.compile(
    r"^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$"
)
_BUNDLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*(?:\.[A-Za-z0-9][A-Za-z0-9-]*)+$")
_SCHEME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ENTITLEMENT_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,191}$")

EntitlementScalar: TypeAlias = bool | int | str
EntitlementValue: TypeAlias = EntitlementScalar | tuple[str, ...]


class AppleSigningMode(str, Enum):
    UNSIGNED_SIMULATOR = "UNSIGNED_SIMULATOR"
    DEVELOPMENT = "DEVELOPMENT"
    AD_HOC = "AD_HOC"
    APP_STORE = "APP_STORE"


class AppleExportMethod(str, Enum):
    NONE = "NONE"
    DEVELOPMENT = "DEVELOPMENT"
    AD_HOC = "AD_HOC"
    APP_STORE_CONNECT = "APP_STORE_CONNECT"


class AppleSigningReadiness(str, Enum):
    SIMULATOR_UNSIGNED_READY = "SIMULATOR_UNSIGNED_READY"
    ARCHIVE_METADATA_READY = "ARCHIVE_METADATA_READY"
    DISTRIBUTION_CREDENTIALS_REQUIRED = "DISTRIBUTION_CREDENTIALS_REQUIRED"
    DISTRIBUTION_READY = "DISTRIBUTION_READY"
    BLOCKED = "BLOCKED"


class AppleCapability(str, Enum):
    PUSH_NOTIFICATIONS = "PUSH_NOTIFICATIONS"
    ASSOCIATED_DOMAINS = "ASSOCIATED_DOMAINS"
    APP_GROUPS = "APP_GROUPS"


_CAPABILITY_ENTITLEMENTS: dict[AppleCapability, tuple[str, ...]] = {
    AppleCapability.PUSH_NOTIFICATIONS: ("aps-environment",),
    AppleCapability.ASSOCIATED_DOMAINS: ("com.apple.developer.associated-domains",),
    AppleCapability.APP_GROUPS: ("com.apple.security.application-groups",),
}

_SYSTEM_ENTITLEMENTS = frozenset(
    {
        "application-identifier",
        "com.apple.developer.team-identifier",
        "get-task-allow",
        "keychain-access-groups",
    }
)
_ALLOWED_ENTITLEMENTS = frozenset(
    _SYSTEM_ENTITLEMENTS
    | {key for values in _CAPABILITY_ENTITLEMENTS.values() for key in values}
)

_EXPORT_METHOD_BY_SIGNING_MODE: dict[AppleSigningMode, AppleExportMethod] = {
    AppleSigningMode.UNSIGNED_SIMULATOR: AppleExportMethod.NONE,
    AppleSigningMode.DEVELOPMENT: AppleExportMethod.DEVELOPMENT,
    AppleSigningMode.AD_HOC: AppleExportMethod.AD_HOC,
    AppleSigningMode.APP_STORE: AppleExportMethod.APP_STORE_CONNECT,
}

_XCODE_EXPORT_METHOD: dict[AppleExportMethod, str] = {
    AppleExportMethod.DEVELOPMENT: "development",
    AppleExportMethod.AD_HOC: "ad-hoc",
    AppleExportMethod.APP_STORE_CONNECT: "app-store-connect",
}


def _canonical_bytes(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(payload: object) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _validate_team_id(value: str) -> str:
    if _TEAM_ID_RE.fullmatch(value) is None:
        raise ValueError("Apple Team ID must be exactly 10 uppercase alphanumeric characters")
    return value


def _validate_bundle_id(value: str, *, allow_terminal_wildcard: bool = False) -> str:
    if allow_terminal_wildcard and value.endswith(".*"):
        prefix = value[:-2]
        if _BUNDLE_ID_RE.fullmatch(prefix) is None:
            raise ValueError("Apple wildcard bundle pattern is invalid")
        return value
    if _BUNDLE_ID_RE.fullmatch(value) is None or "*" in value:
        raise ValueError("Apple bundle identifier is invalid")
    return value


def _normalize_entitlement_value(value: object) -> EntitlementValue:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        if not value or any(ch in value for ch in "\r\n\x00"):
            raise ValueError("entitlement string is empty or contains a control delimiter")
        return value
    if isinstance(value, (list, tuple)):
        items = tuple(str(item) for item in value)
        if not items or len(set(items)) != len(items):
            raise ValueError("entitlement arrays must be non-empty and unique")
        if any((not item) or any(ch in item for ch in "\r\n\x00") for item in items):
            raise ValueError("entitlement array contains an invalid string")
        return items
    raise ValueError("unsupported entitlement value type")


def normalize_entitlements(values: Mapping[str, object] | None) -> tuple[tuple[str, EntitlementValue], ...]:
    if not values:
        return ()
    normalized: list[tuple[str, EntitlementValue]] = []
    for key, value in values.items():
        name = str(key)
        if _ENTITLEMENT_KEY_RE.fullmatch(name) is None or name not in _ALLOWED_ENTITLEMENTS:
            raise ValueError(f"Apple entitlement is not allowlisted: {name}")
        normalized.append((name, _normalize_entitlement_value(value)))
    return tuple(sorted(normalized, key=lambda item: item[0]))


def entitlement_keys_for_capabilities(capabilities: Iterable[AppleCapability]) -> tuple[str, ...]:
    keys: set[str] = set()
    for capability in capabilities:
        if not isinstance(capability, AppleCapability):
            raise ValueError("Apple capabilities must use the frozen AppleCapability enum")
        keys.update(_CAPABILITY_ENTITLEMENTS[capability])
    return tuple(sorted(keys))


@dataclass(frozen=True, slots=True)
class AppleCertificateIdentity:
    sha256: str
    common_name: str | None = None

    def __post_init__(self) -> None:
        if _SHA256_RE.fullmatch(self.sha256) is None:
            raise ValueError("certificate SHA-256 fingerprint must be lowercase 64-hex")
        if self.common_name is not None:
            value = self.common_name.strip()
            if not value or len(value) > 256 or any(ch in value for ch in "\r\n\x00"):
                raise ValueError("certificate public common name is invalid")
            object.__setattr__(self, "common_name", value)

    def to_dict(self) -> dict[str, object]:
        return {"sha256": self.sha256, "common_name": self.common_name}


@dataclass(frozen=True, slots=True)
class AppleProvisioningProfileIdentity:
    uuid: str
    team_id: str
    app_id_prefix: str
    bundle_id_pattern: str
    certificate_sha256s: tuple[str, ...]
    entitlements: tuple[tuple[str, EntitlementValue], ...]

    def __post_init__(self) -> None:
        if _PROFILE_UUID_RE.fullmatch(self.uuid) is None:
            raise ValueError("provisioning profile UUID must be canonical uppercase UUID")
        _validate_team_id(self.team_id)
        _validate_team_id(self.app_id_prefix)
        _validate_bundle_id(self.bundle_id_pattern, allow_terminal_wildcard=True)
        if not self.certificate_sha256s:
            raise ValueError("provisioning profile must expose at least one public certificate fingerprint")
        for fingerprint in self.certificate_sha256s:
            if _SHA256_RE.fullmatch(fingerprint) is None:
                raise ValueError("provisioning profile certificate fingerprint must be lowercase 64-hex")
        if len(set(self.certificate_sha256s)) != len(self.certificate_sha256s):
            raise ValueError("provisioning profile certificate fingerprints must be unique")
        keys = [key for key, _ in self.entitlements]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("provisioning profile entitlements must be sorted and unique")
        for key, value in self.entitlements:
            if key not in _ALLOWED_ENTITLEMENTS:
                raise ValueError(f"provisioning profile entitlement is not allowlisted: {key}")
            _normalize_entitlement_value(value)

    @classmethod
    def from_public_metadata(
        cls,
        *,
        uuid: str,
        team_id: str,
        app_id_prefix: str,
        bundle_id_pattern: str,
        certificate_sha256s: Sequence[str],
        entitlements: Mapping[str, object],
    ) -> "AppleProvisioningProfileIdentity":
        return cls(
            uuid=uuid,
            team_id=team_id,
            app_id_prefix=app_id_prefix,
            bundle_id_pattern=bundle_id_pattern,
            certificate_sha256s=tuple(sorted(certificate_sha256s)),
            entitlements=normalize_entitlements(entitlements),
        )

    @property
    def application_identifier_pattern(self) -> str:
        return f"{self.app_id_prefix}.{self.bundle_id_pattern}"

    def matches_bundle_id(self, bundle_id: str) -> bool:
        _validate_bundle_id(bundle_id)
        if self.bundle_id_pattern.endswith(".*"):
            prefix = self.bundle_id_pattern[:-1]
            return bundle_id.startswith(prefix) and len(bundle_id) > len(prefix)
        return bundle_id == self.bundle_id_pattern

    def entitlement_map(self) -> dict[str, EntitlementValue]:
        return dict(self.entitlements)

    def to_dict(self) -> dict[str, object]:
        return {
            "uuid": self.uuid,
            "team_id": self.team_id,
            "app_id_prefix": self.app_id_prefix,
            "bundle_id_pattern": self.bundle_id_pattern,
            "application_identifier_pattern": self.application_identifier_pattern,
            "certificate_sha256s": list(self.certificate_sha256s),
            "entitlements": {key: list(value) if isinstance(value, tuple) else value for key, value in self.entitlements},
        }


@dataclass(frozen=True, slots=True)
class AppleSigningSecretRefs:
    signing_certificate: SecretRef | None = None
    signing_certificate_password: SecretRef | None = None
    provisioning_profile: SecretRef | None = None

    def refs(self) -> tuple[SecretRef, ...]:
        return tuple(
            item
            for item in (
                self.signing_certificate,
                self.signing_certificate_password,
                self.provisioning_profile,
            )
            if item is not None
        )

    def complete_for_distribution(self) -> bool:
        return all(
            item is not None
            for item in (
                self.signing_certificate,
                self.signing_certificate_password,
                self.provisioning_profile,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "signing_certificate": self.signing_certificate.to_dict() if self.signing_certificate else None,
            "signing_certificate_password": (
                self.signing_certificate_password.to_dict() if self.signing_certificate_password else None
            ),
            "provisioning_profile": self.provisioning_profile.to_dict() if self.provisioning_profile else None,
        }


@dataclass(frozen=True, slots=True)
class AppleArchiveDefinition:
    bundle_id: str
    scheme: str
    signing_mode: AppleSigningMode
    export_method: AppleExportMethod
    team_id: str | None = None
    profile_uuid: str | None = None
    certificate_sha256: str | None = None
    capabilities: tuple[AppleCapability, ...] = ()
    entitlements: tuple[tuple[str, EntitlementValue], ...] = ()
    privacy_manifest_required: bool = True
    secrets: AppleSigningSecretRefs = AppleSigningSecretRefs()

    def __post_init__(self) -> None:
        _validate_bundle_id(self.bundle_id)
        if _SCHEME_RE.fullmatch(self.scheme) is None:
            raise ValueError("Xcode scheme is not a bounded stable identifier")
        if self.export_method is not _EXPORT_METHOD_BY_SIGNING_MODE[self.signing_mode]:
            raise ValueError("export method does not match Apple signing mode")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise ValueError("Apple capabilities must be unique")
        required_entitlement_keys = set(entitlement_keys_for_capabilities(self.capabilities))
        claim_keys = {key for key, _ in self.entitlements}
        if not required_entitlement_keys <= claim_keys:
            raise ValueError("capability-to-entitlement mapping is incomplete")
        if self.signing_mode is AppleSigningMode.UNSIGNED_SIMULATOR:
            if any(value is not None for value in (self.team_id, self.profile_uuid, self.certificate_sha256)):
                raise ValueError("unsigned simulator definition cannot carry distribution identities")
            if self.secrets.refs():
                raise ValueError("unsigned simulator definition cannot carry signing secret references")
        else:
            if self.team_id is not None:
                _validate_team_id(self.team_id)
            if self.profile_uuid is not None and _PROFILE_UUID_RE.fullmatch(self.profile_uuid) is None:
                raise ValueError("archive provisioning profile UUID is invalid")
            if self.certificate_sha256 is not None and _SHA256_RE.fullmatch(self.certificate_sha256) is None:
                raise ValueError("archive certificate fingerprint is invalid")

    @classmethod
    def create(
        cls,
        *,
        bundle_id: str,
        scheme: str,
        signing_mode: AppleSigningMode,
        team_id: str | None = None,
        profile_uuid: str | None = None,
        certificate_sha256: str | None = None,
        capabilities: Sequence[AppleCapability] = (),
        entitlements: Mapping[str, object] | None = None,
        privacy_manifest_required: bool = True,
        secrets: AppleSigningSecretRefs | None = None,
    ) -> "AppleArchiveDefinition":
        return cls(
            bundle_id=bundle_id,
            scheme=scheme,
            signing_mode=signing_mode,
            export_method=_EXPORT_METHOD_BY_SIGNING_MODE[signing_mode],
            team_id=team_id,
            profile_uuid=profile_uuid,
            certificate_sha256=certificate_sha256,
            capabilities=tuple(capabilities),
            entitlements=normalize_entitlements(entitlements),
            privacy_manifest_required=privacy_manifest_required,
            secrets=secrets or AppleSigningSecretRefs(),
        )

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": 1,
            "bundle_id": self.bundle_id,
            "scheme": self.scheme,
            "signing_mode": self.signing_mode.value,
            "export_method": self.export_method.value,
            "team_id": self.team_id,
            "profile_uuid": self.profile_uuid,
            "certificate_sha256": self.certificate_sha256,
            "capabilities": [item.value for item in self.capabilities],
            "entitlements": {
                key: list(value) if isinstance(value, tuple) else value for key, value in self.entitlements
            },
            "privacy_manifest_required": self.privacy_manifest_required,
            "secrets": self.secrets.to_dict(),
        }
        return payload

    def digest(self) -> str:
        return _digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class AppleSigningAssessment:
    readiness: AppleSigningReadiness
    archive_metadata_ready: bool
    distribution_signing_capable: bool
    credentials_required: bool
    privacy_manifest_present: bool
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "readiness": self.readiness.value,
            "archive_metadata_ready": self.archive_metadata_ready,
            "distribution_signing_capable": self.distribution_signing_capable,
            "credentials_required": self.credentials_required,
            "privacy_manifest_present": self.privacy_manifest_present,
            "blockers": list(self.blockers),
        }


def _string_matches_profile_rule(claimed: str, allowed: str) -> bool:
    if "*" in claimed:
        return False
    if allowed.endswith("*"):
        return claimed.startswith(allowed[:-1])
    return claimed == allowed


def _value_authorized(claimed: EntitlementValue, allowed: EntitlementValue) -> bool:
    if isinstance(claimed, tuple):
        if not isinstance(allowed, tuple):
            return False
        return all(
            any(_string_matches_profile_rule(item, candidate) for candidate in allowed)
            for item in claimed
        )
    if isinstance(claimed, str):
        return isinstance(allowed, str) and _string_matches_profile_rule(claimed, allowed)
    return claimed == allowed


def entitlement_blockers(
    definition: AppleArchiveDefinition,
    profile: AppleProvisioningProfileIdentity,
) -> tuple[str, ...]:
    allowed = profile.entitlement_map()
    blockers: list[str] = []
    expected_application_id = f"{profile.app_id_prefix}.{definition.bundle_id}"
    for key, claimed in definition.entitlements:
        if key not in allowed:
            blockers.append(f"entitlement_not_authorized:{key}")
            continue
        if key == "application-identifier" and claimed != expected_application_id:
            blockers.append("application_identifier_mismatch")
            continue
        if key == "com.apple.developer.team-identifier" and claimed != profile.team_id:
            blockers.append("team_identifier_entitlement_mismatch")
            continue
        if not _value_authorized(claimed, allowed[key]):
            blockers.append(f"entitlement_value_not_authorized:{key}")
    return tuple(sorted(set(blockers)))


def privacy_manifest_present(paths: Iterable[str]) -> bool:
    normalized = tuple(str(path).replace("\\", "/") for path in paths)
    return any(path == "PrivacyInfo.xcprivacy" or path.endswith("/PrivacyInfo.xcprivacy") for path in normalized)


def assess_apple_signing(
    definition: AppleArchiveDefinition,
    *,
    profile: AppleProvisioningProfileIdentity | None,
    certificate: AppleCertificateIdentity | None,
    workspace_paths: Iterable[str],
) -> AppleSigningAssessment:
    manifest_present = privacy_manifest_present(workspace_paths)
    blockers: list[str] = []
    if definition.privacy_manifest_required and not manifest_present:
        blockers.append("privacy_manifest_missing")

    if definition.signing_mode is AppleSigningMode.UNSIGNED_SIMULATOR:
        readiness = AppleSigningReadiness.BLOCKED if blockers else AppleSigningReadiness.SIMULATOR_UNSIGNED_READY
        return AppleSigningAssessment(
            readiness=readiness,
            archive_metadata_ready=not blockers,
            distribution_signing_capable=False,
            credentials_required=False,
            privacy_manifest_present=manifest_present,
            blockers=tuple(sorted(blockers)),
        )

    if definition.team_id is None:
        blockers.append("team_id_missing")
    if definition.profile_uuid is None:
        blockers.append("profile_uuid_missing")
    if definition.certificate_sha256 is None:
        blockers.append("certificate_identity_missing")
    if profile is None:
        blockers.append("profile_identity_missing")
    if certificate is None:
        blockers.append("certificate_public_identity_missing")

    if profile is not None:
        if definition.team_id is not None and profile.team_id != definition.team_id:
            blockers.append("profile_team_mismatch")
        if definition.profile_uuid is not None and profile.uuid != definition.profile_uuid:
            blockers.append("profile_uuid_mismatch")
        if not profile.matches_bundle_id(definition.bundle_id):
            blockers.append("profile_bundle_mismatch")
        blockers.extend(entitlement_blockers(definition, profile))
    if certificate is not None and profile is not None:
        if certificate.sha256 not in profile.certificate_sha256s:
            blockers.append("certificate_not_in_profile")
    if certificate is not None and definition.certificate_sha256 is not None:
        if certificate.sha256 != definition.certificate_sha256:
            blockers.append("certificate_identity_mismatch")

    blockers = sorted(set(blockers))
    if blockers:
        return AppleSigningAssessment(
            readiness=AppleSigningReadiness.BLOCKED,
            archive_metadata_ready=False,
            distribution_signing_capable=False,
            credentials_required=not definition.secrets.complete_for_distribution(),
            privacy_manifest_present=manifest_present,
            blockers=tuple(blockers),
        )

    credentials_required = not definition.secrets.complete_for_distribution()
    readiness = (
        AppleSigningReadiness.DISTRIBUTION_CREDENTIALS_REQUIRED
        if credentials_required
        else AppleSigningReadiness.DISTRIBUTION_READY
    )
    return AppleSigningAssessment(
        readiness=readiness,
        archive_metadata_ready=True,
        distribution_signing_capable=not credentials_required,
        credentials_required=credentials_required,
        privacy_manifest_present=manifest_present,
        blockers=(),
    )


def assert_definition_secret_safe(
    definition: AppleArchiveDefinition,
    *,
    known_secret_values: Sequence[str],
) -> None:
    assert_secret_refs_only(definition.to_dict(), definition.secrets.refs(), known_secret_values)


def render_export_options_plist(definition: AppleArchiveDefinition) -> str:
    if definition.export_method is AppleExportMethod.NONE:
        raise ValueError("unsigned simulator builds do not have distribution export options")
    if definition.team_id is None or definition.profile_uuid is None:
        raise ValueError("export metadata requires public team and provisioning profile identity")
    method = _XCODE_EXPORT_METHOD[definition.export_method]
    values = {
        "method": method,
        "signingStyle": "manual",
        "teamID": definition.team_id,
        "provisioningProfiles": {definition.bundle_id: definition.profile_uuid},
    }
    lines = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", '<plist version="1.0">', "<dict>"]
    for key in ("method", "signingStyle", "teamID"):
        lines.extend((f"  <key>{key}</key>", f"  <string>{values[key]}</string>"))
    lines.extend(("  <key>provisioningProfiles</key>", "  <dict>", f"    <key>{definition.bundle_id}</key>", f"    <string>{definition.profile_uuid}</string>", "  </dict>", "</dict>", "</plist>"))
    return "\n".join(lines) + "\n"


def _xcode_selector(project: Path) -> tuple[str, str]:
    return ("-workspace", str(project)) if project.suffix == ".xcworkspace" else ("-project", str(project))


def build_unsigned_archive_argv(
    boundary: MobileToolchainBoundary,
    xcodebuild: Path,
    *,
    project_file: Path,
    scheme: str,
    archive_path: Path,
) -> tuple[str, ...]:
    if _SCHEME_RE.fullmatch(scheme) is None:
        raise MobileBoundaryError("Xcode scheme is not a bounded stable identifier")
    tool = boundary.validate_tool(MobileToolKind.XCODEBUILD, xcodebuild)
    project = boundary.validate_xcode_container(project_file)
    archive = boundary.validate_staging_path(archive_path)
    if archive.suffix != ".xcarchive":
        raise MobileBoundaryError("Apple archive output must use the .xcarchive suffix")
    return (
        str(tool),
        *_xcode_selector(project),
        "-scheme",
        scheme,
        "-configuration",
        "Release",
        "-destination",
        "generic/platform=iOS",
        "-archivePath",
        str(archive),
        "CODE_SIGNING_ALLOWED=NO",
        "CODE_SIGNING_REQUIRED=NO",
        "archive",
    )


def build_export_archive_argv(
    boundary: MobileToolchainBoundary,
    xcodebuild: Path,
    *,
    archive_path: Path,
    export_path: Path,
    export_options_plist: Path,
) -> tuple[str, ...]:
    tool = boundary.validate_tool(MobileToolKind.XCODEBUILD, xcodebuild)
    archive = boundary.validate_staging_path(archive_path)
    export = boundary.validate_staging_path(export_path)
    options = boundary.validate_staging_path(export_options_plist)
    if archive.suffix != ".xcarchive":
        raise MobileBoundaryError("Apple archive input must use the .xcarchive suffix")
    if options.suffix != ".plist":
        raise MobileBoundaryError("Apple export options must use a .plist file")
    return (
        str(tool),
        "-exportArchive",
        "-archivePath",
        str(archive),
        "-exportPath",
        str(export),
        "-exportOptionsPlist",
        str(options),
    )
