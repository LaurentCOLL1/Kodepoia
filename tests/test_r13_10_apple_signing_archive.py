from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.core.secrets import KodeSecrets, MemorySecretBackend
from kodepoia.mobile.apple_signing import (
    AppleArchiveDefinition,
    AppleCapability,
    AppleCertificateIdentity,
    AppleExportMethod,
    AppleProvisioningProfileIdentity,
    AppleSigningMode,
    AppleSigningReadiness,
    AppleSigningSecretRefs,
    assess_apple_signing,
    assert_definition_secret_safe,
    build_export_archive_argv,
    build_unsigned_archive_argv,
    entitlement_keys_for_capabilities,
    normalize_entitlements,
    privacy_manifest_present,
    render_export_options_plist,
)
from kodepoia.mobile.boundary import MobileBoundaryError, MobileToolchainBoundary

ROOT = Path(__file__).resolve().parents[1]
TEAM = "A1B2C3D4E5"
PROFILE_UUID = "11111111-2222-3333-4444-555555555555"
CERT_SHA = "a" * 64


def _profile(*, team: str = TEAM, bundle: str = "com.kodepoia.*", cert: str = CERT_SHA):
    return AppleProvisioningProfileIdentity.from_public_metadata(
        uuid=PROFILE_UUID,
        team_id=team,
        app_id_prefix=team,
        bundle_id_pattern=bundle,
        certificate_sha256s=(cert,),
        entitlements={
            "application-identifier": f"{team}.com.kodepoia.*",
            "com.apple.developer.team-identifier": team,
            "aps-environment": "production",
            "com.apple.developer.associated-domains": ("applinks:example.com",),
            "com.apple.security.application-groups": (f"group.{team}.*",),
            "keychain-access-groups": (f"{team}.*",),
        },
    )


def _definition(*, secrets: AppleSigningSecretRefs | None = None):
    return AppleArchiveDefinition.create(
        bundle_id="com.kodepoia.fixture",
        scheme="KodepoiaIOS",
        signing_mode=AppleSigningMode.APP_STORE,
        team_id=TEAM,
        profile_uuid=PROFILE_UUID,
        certificate_sha256=CERT_SHA,
        capabilities=(AppleCapability.PUSH_NOTIFICATIONS, AppleCapability.ASSOCIATED_DOMAINS),
        entitlements={
            "application-identifier": f"{TEAM}.com.kodepoia.fixture",
            "com.apple.developer.team-identifier": TEAM,
            "aps-environment": "production",
            "com.apple.developer.associated-domains": ("applinks:example.com",),
        },
        secrets=secrets,
    )


def test_r13_10_definition_matches_strict_schema() -> None:
    schema = json.loads(
        (ROOT / "schemas/r13/apple-signing-archive.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(_definition().to_dict())


def test_r13_10_capability_mapping_is_explicit_and_unknown_entitlements_fail_closed() -> None:
    assert entitlement_keys_for_capabilities(
        (AppleCapability.PUSH_NOTIFICATIONS, AppleCapability.APP_GROUPS)
    ) == ("aps-environment", "com.apple.security.application-groups")
    with pytest.raises(ValueError, match="not allowlisted"):
        normalize_entitlements({"com.attacker.raw": True})
    with pytest.raises(ValueError, match="mapping is incomplete"):
        AppleArchiveDefinition.create(
            bundle_id="com.kodepoia.fixture",
            scheme="KodepoiaIOS",
            signing_mode=AppleSigningMode.APP_STORE,
            capabilities=(AppleCapability.PUSH_NOTIFICATIONS,),
            entitlements={},
        )


def test_r13_10_public_identity_validation_rejects_substitution_shapes() -> None:
    with pytest.raises(ValueError, match="Team ID"):
        _profile(team="../../BAD")
    with pytest.raises(ValueError, match="certificate SHA"):
        AppleCertificateIdentity("not-a-fingerprint")
    with pytest.raises(ValueError, match="bundle"):
        _profile(bundle="com.kodepoia.*.escape")


def test_r13_10_profile_allowlist_authorizes_only_bounded_claims() -> None:
    profile = _profile()
    definition = _definition()
    assessment = assess_apple_signing(
        definition,
        profile=profile,
        certificate=AppleCertificateIdentity(CERT_SHA, "Apple Distribution: Fixture"),
        workspace_paths=("KodepoiaIOS/PrivacyInfo.xcprivacy",),
    )
    assert assessment.readiness is AppleSigningReadiness.DISTRIBUTION_CREDENTIALS_REQUIRED
    assert assessment.archive_metadata_ready is True
    assert assessment.distribution_signing_capable is False
    assert assessment.credentials_required is True
    assert assessment.blockers == ()

    escalated = AppleArchiveDefinition.create(
        bundle_id="com.kodepoia.fixture",
        scheme="KodepoiaIOS",
        signing_mode=AppleSigningMode.APP_STORE,
        team_id=TEAM,
        profile_uuid=PROFILE_UUID,
        certificate_sha256=CERT_SHA,
        capabilities=(AppleCapability.ASSOCIATED_DOMAINS,),
        entitlements={
            "application-identifier": f"{TEAM}.com.kodepoia.fixture",
            "com.apple.developer.team-identifier": TEAM,
            "com.apple.developer.associated-domains": ("applinks:attacker.example",),
        },
    )
    blocked = assess_apple_signing(
        escalated,
        profile=profile,
        certificate=AppleCertificateIdentity(CERT_SHA),
        workspace_paths=("PrivacyInfo.xcprivacy",),
    )
    assert blocked.readiness is AppleSigningReadiness.BLOCKED
    assert "entitlement_value_not_authorized:com.apple.developer.associated-domains" in blocked.blockers


def test_r13_10_wrong_team_bundle_profile_or_certificate_fails_closed() -> None:
    definition = _definition()
    certificate = AppleCertificateIdentity(CERT_SHA)
    wrong_bundle = _profile(bundle="com.other.app")
    result = assess_apple_signing(
        definition,
        profile=wrong_bundle,
        certificate=certificate,
        workspace_paths=("PrivacyInfo.xcprivacy",),
    )
    assert result.readiness is AppleSigningReadiness.BLOCKED
    assert "profile_bundle_mismatch" in result.blockers

    wrong_cert = assess_apple_signing(
        definition,
        profile=_profile(),
        certificate=AppleCertificateIdentity("b" * 64),
        workspace_paths=("PrivacyInfo.xcprivacy",),
    )
    assert "certificate_not_in_profile" in wrong_cert.blockers
    assert "certificate_identity_mismatch" in wrong_cert.blockers


def test_r13_10_kodesecrets_refs_are_durable_but_values_never_are() -> None:
    secrets = KodeSecrets(MemorySecretBackend())
    secrets.store("apple", "certificate-p12", "P12-SECRET-VALUE")
    secrets.store("apple", "certificate-password", "PASSWORD-SECRET-VALUE")
    secrets.store("apple", "profile", "PROFILE-SECRET-VALUE")
    refs = AppleSigningSecretRefs(
        signing_certificate=secrets.ref("apple", "certificate-p12"),
        signing_certificate_password=secrets.ref("apple", "certificate-password"),
        provisioning_profile=secrets.ref("apple", "profile"),
    )
    definition = _definition(secrets=refs)
    assert_definition_secret_safe(definition, known_secret_values=secrets.known_values())
    serialized = json.dumps(definition.to_dict(), sort_keys=True)
    assert "P12-SECRET-VALUE" not in serialized
    assert "PASSWORD-SECRET-VALUE" not in serialized
    assert "PROFILE-SECRET-VALUE" not in serialized
    assert '"key": "certificate-p12"' in serialized

    assessment = assess_apple_signing(
        definition,
        profile=_profile(),
        certificate=AppleCertificateIdentity(CERT_SHA),
        workspace_paths=("KodepoiaIOS/PrivacyInfo.xcprivacy",),
    )
    assert assessment.readiness is AppleSigningReadiness.DISTRIBUTION_READY
    assert assessment.distribution_signing_capable is True


def test_r13_10_simulator_is_independent_of_distribution_signing() -> None:
    definition = AppleArchiveDefinition.create(
        bundle_id="com.kodepoia.fixture",
        scheme="KodepoiaIOS",
        signing_mode=AppleSigningMode.UNSIGNED_SIMULATOR,
        privacy_manifest_required=False,
    )
    assert definition.export_method is AppleExportMethod.NONE
    assessment = assess_apple_signing(
        definition,
        profile=None,
        certificate=None,
        workspace_paths=(),
    )
    assert assessment.readiness is AppleSigningReadiness.SIMULATOR_UNSIGNED_READY
    assert assessment.credentials_required is False
    with pytest.raises(ValueError, match="cannot carry"):
        AppleArchiveDefinition.create(
            bundle_id="com.kodepoia.fixture",
            scheme="KodepoiaIOS",
            signing_mode=AppleSigningMode.UNSIGNED_SIMULATOR,
            team_id=TEAM,
        )


def test_r13_10_privacy_manifest_check_is_path_bounded() -> None:
    assert privacy_manifest_present(("KodepoiaIOS/PrivacyInfo.xcprivacy",)) is True
    assert privacy_manifest_present(("KodepoiaIOS/Info.plist",)) is False
    missing = assess_apple_signing(
        _definition(),
        profile=_profile(),
        certificate=AppleCertificateIdentity(CERT_SHA),
        workspace_paths=("KodepoiaIOS/Info.plist",),
    )
    assert missing.readiness is AppleSigningReadiness.BLOCKED
    assert "privacy_manifest_missing" in missing.blockers


def test_r13_10_export_options_are_deterministic_public_metadata_only() -> None:
    definition = _definition()
    first = render_export_options_plist(definition)
    second = render_export_options_plist(definition)
    assert first == second
    assert "app-store-connect" in first
    assert TEAM in first
    assert PROFILE_UUID in first
    assert "password" not in first.casefold()
    assert "private" not in first.casefold()


def test_r13_10_unsigned_archive_and_export_argv_are_fixed_and_path_safe(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    project_root = tmp_path / "project"
    staging = tmp_path / "staging"
    runtime.mkdir()
    project_root.mkdir()
    staging.mkdir()
    tool = runtime / "xcodebuild"
    tool.write_text("fixture", encoding="utf-8")
    project = project_root / "KodepoiaIOS.xcodeproj"
    project.mkdir()
    boundary = MobileToolchainBoundary(
        allowed_runtime_roots=(runtime,),
        project_root=project_root,
        staging_root=staging,
    )
    archive = staging / "Fixture.xcarchive"
    argv = build_unsigned_archive_argv(
        boundary,
        tool,
        project_file=project,
        scheme="KodepoiaIOS",
        archive_path=archive,
    )
    assert "generic/platform=iOS" in argv
    assert "CODE_SIGNING_ALLOWED=NO" in argv
    assert "CODE_SIGNING_REQUIRED=NO" in argv
    assert argv[-1] == "archive"
    assert "DEVELOPMENT_TEAM" not in " ".join(argv)
    assert "PROVISIONING_PROFILE" not in " ".join(argv)

    options = staging / "ExportOptions.plist"
    export = staging / "Export"
    export_argv = build_export_archive_argv(
        boundary,
        tool,
        archive_path=archive,
        export_path=export,
        export_options_plist=options,
    )
    assert export_argv[1] == "-exportArchive"
    assert "-exportOptionsPlist" in export_argv
    with pytest.raises(MobileBoundaryError):
        build_unsigned_archive_argv(
            boundary,
            tool,
            project_file=project,
            scheme="KodepoiaIOS -showBuildSettings",
            archive_path=archive,
        )
    with pytest.raises(MobileBoundaryError):
        build_unsigned_archive_argv(
            boundary,
            tool,
            project_file=project,
            scheme="KodepoiaIOS",
            archive_path=tmp_path / "outside" / "Fixture.xcarchive",
        )
