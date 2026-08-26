from __future__ import annotations

import argparse
import hashlib
import json
import platform
import plistlib
import shutil
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator

from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.mobile.apple_signing import (
    AppleArchiveDefinition,
    AppleCapability,
    AppleCertificateIdentity,
    AppleProvisioningProfileIdentity,
    AppleSigningMode,
    AppleSigningReadiness,
    assess_apple_signing,
    build_export_archive_argv,
    build_unsigned_archive_argv,
    render_export_options_plist,
)
from kodepoia.mobile.apple_xcode import parse_sdk_version, parse_xcodebuild_version
from kodepoia.mobile.boundary import MobileToolchainBoundary
from kodepoia.mobile.contracts import MobileFormFactor, MobilePackageKind, MobileSourceKind, MobileToolKind
from kodepoia.mobile.ios_scaffold import (
    AppleScaffoldDefinition,
    AppleScaffoldEngine,
    AppleScaffoldLineage,
    AppleStringCatalog,
    build_ios_simulator_build_argv,
)
from kodepoia.project.dna import MobileProjectProfile, Platform, ProjectDNA, ProjectType

ROOT = Path(__file__).resolve().parents[1]
TEAM_ID = "A1B2C3D4E5"
PROFILE_UUID = "11111111-2222-3333-4444-555555555555"
CERT_SHA256 = "a" * 64


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _run(argv: tuple[str, ...], *, timeout: int) -> str:
    completed = subprocess.run(
        argv,
        check=True,
        capture_output=True,
        text=True,
        shell=False,
        timeout=timeout,
    )
    return completed.stdout if completed.stdout else completed.stderr


def _required_tool(name: str) -> Path:
    candidate = shutil.which(name)
    if candidate is None:
        raise RuntimeError(f"required hosted macOS tool is unavailable: {name}")
    return Path(candidate)


def _canonical_scaffold() -> tuple[AppleScaffoldDefinition, object]:
    model = canonical_sample_app()
    dna = ProjectDNA(
        schema_version=1,
        name="Kodepoia Apple Signing Acceptance",
        project_type=ProjectType.MOBILE_APP,
        platforms=[Platform.IOS],
        mobile=MobileProjectProfile(
            source_kind=MobileSourceKind.NATIVE,
            form_factors=(MobileFormFactor.PHONE, MobileFormFactor.TABLET),
            apple_bundle_id="com.kodepoia.acceptance",
            apple_min_version="17.0",
            apple_target_version="26.0",
            package_kinds=(MobilePackageKind.APP,),
        ),
    )
    definition = AppleScaffoldDefinition.from_project(
        dna,
        model,
        catalogs=(
            AppleStringCatalog("en", (("app_name", "Kodepoia Signing Acceptance"),)),
            AppleStringCatalog("fr", (("app_name", "Acceptation signature Kodepoia"),)),
        ),
    )
    return definition, model


def _write_minimal_privacy_manifest(path: Path) -> None:
    payload = {
        "NSPrivacyTracking": False,
        "NSPrivacyTrackingDomains": [],
        "NSPrivacyCollectedDataTypes": [],
        "NSPrivacyAccessedAPITypes": [],
    }
    path.write_bytes(plistlib.dumps(payload, fmt=plistlib.FMT_XML, sort_keys=True))


def build_acceptance_payload(source_sha: str, output_path: Path) -> dict[str, object]:
    if len(source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise ValueError("--source-sha must be an exact lowercase 40-hex Git SHA")
    if platform.system() != "Darwin":
        raise RuntimeError("R13.10 hosted acceptance requires macOS")

    work_root = output_path.parent / f"r13_10_project_{source_sha[:12]}"
    staging = output_path.parent / f"r13_10_staging_{source_sha[:12]}"
    for path in (work_root, staging):
        if path.exists():
            shutil.rmtree(path)
    work_root.mkdir(parents=True)
    staging.mkdir(parents=True)

    scaffold_definition, model = _canonical_scaffold()
    lineage = AppleScaffoldLineage(
        _digest_text(source_sha + ":dna"),
        _digest_text(source_sha + ":product"),
    )
    engine = AppleScaffoldEngine()
    preview = engine.preview(work_root, scaffold_definition, model, lineage)
    if preview.has_conflicts:
        raise RuntimeError("canonical R13.10 scaffold unexpectedly contains conflicts")
    workspace_manifest = engine.apply(work_root, preview)
    privacy_manifest = work_root / "KodepoiaIOS" / "PrivacyInfo.xcprivacy"
    _write_minimal_privacy_manifest(privacy_manifest)

    xcodebuild_candidate = _required_tool("xcodebuild")
    xcrun_candidate = _required_tool("xcrun")
    boundary = MobileToolchainBoundary(
        allowed_runtime_roots=(Path("/usr/bin"), Path("/Applications")),
        project_root=work_root,
        staging_root=output_path.parent,
    )
    xcodebuild = boundary.validate_tool(MobileToolKind.XCODEBUILD, xcodebuild_candidate)
    xcrun = boundary.validate_tool(MobileToolKind.XCRUN, xcrun_candidate)
    boundary.validate_staging_path(output_path)

    xcode_version, _xcode_build = parse_xcodebuild_version(
        _run(boundary.build_probe_argv(MobileToolKind.XCODEBUILD, xcodebuild), timeout=60)
    )
    iphoneos_sdk = parse_sdk_version(
        _run(boundary.build_xcrun_sdk_version_argv(xcrun, sdk="iphoneos"), timeout=60)
    )
    simulator_sdk = parse_sdk_version(
        _run(boundary.build_xcrun_sdk_version_argv(xcrun, sdk="iphonesimulator"), timeout=60)
    )

    project_file = work_root / AppleScaffoldEngine.PROJECT_PATH
    derived_data = staging / "DerivedData"
    simulator_argv = build_ios_simulator_build_argv(
        boundary,
        xcodebuild,
        project_file=project_file,
        scheme=AppleScaffoldEngine.SCHEME_NAME,
        derived_data_path=derived_data,
    )
    _run(simulator_argv, timeout=900)

    archive_path = staging / "KodepoiaIOS.xcarchive"
    archive_argv = build_unsigned_archive_argv(
        boundary,
        xcodebuild,
        project_file=project_file,
        scheme=AppleScaffoldEngine.SCHEME_NAME,
        archive_path=archive_path,
    )
    _run(archive_argv, timeout=900)
    archive_info = archive_path / "Info.plist"
    archive_product = archive_path / "Products" / "Applications" / "KodepoiaIOS.app"
    if not archive_info.is_file():
        raise RuntimeError("unsigned hosted archive did not produce Info.plist")
    if not archive_product.is_dir():
        raise RuntimeError("unsigned hosted archive did not produce the application product")

    public_profile = AppleProvisioningProfileIdentity.from_public_metadata(
        uuid=PROFILE_UUID,
        team_id=TEAM_ID,
        app_id_prefix=TEAM_ID,
        bundle_id_pattern="com.kodepoia.*",
        certificate_sha256s=(CERT_SHA256,),
        entitlements={
            "application-identifier": f"{TEAM_ID}.com.kodepoia.*",
            "com.apple.developer.team-identifier": TEAM_ID,
            "aps-environment": "production",
            "com.apple.developer.associated-domains": ("applinks:example.com",),
        },
    )
    public_certificate = AppleCertificateIdentity(CERT_SHA256, "R13.10 public test identity")
    definition = AppleArchiveDefinition.create(
        bundle_id="com.kodepoia.acceptance",
        scheme=AppleScaffoldEngine.SCHEME_NAME,
        signing_mode=AppleSigningMode.APP_STORE,
        team_id=TEAM_ID,
        profile_uuid=PROFILE_UUID,
        certificate_sha256=CERT_SHA256,
        capabilities=(AppleCapability.PUSH_NOTIFICATIONS, AppleCapability.ASSOCIATED_DOMAINS),
        entitlements={
            "application-identifier": f"{TEAM_ID}.com.kodepoia.acceptance",
            "com.apple.developer.team-identifier": TEAM_ID,
            "aps-environment": "production",
            "com.apple.developer.associated-domains": ("applinks:example.com",),
        },
    )
    workspace_paths = tuple(
        str(path.relative_to(work_root)).replace("\\", "/")
        for path in work_root.rglob("*")
        if path.is_file()
    )
    assessment = assess_apple_signing(
        definition,
        profile=public_profile,
        certificate=public_certificate,
        workspace_paths=workspace_paths,
    )
    if assessment.readiness is not AppleSigningReadiness.DISTRIBUTION_CREDENTIALS_REQUIRED:
        raise RuntimeError(f"unexpected R13.10 readiness: {assessment.readiness.value}")
    if assessment.blockers:
        raise RuntimeError(f"unexpected R13.10 blockers: {assessment.blockers}")

    export_options = staging / "ExportOptions.plist"
    export_options.write_text(render_export_options_plist(definition), encoding="utf-8", newline="\n")
    export_argv = build_export_archive_argv(
        boundary,
        xcodebuild,
        archive_path=archive_path,
        export_path=staging / "Export",
        export_options_plist=export_options,
    )
    if any("password" in item.casefold() or "private_key" in item.casefold() for item in export_argv):
        raise RuntimeError("R13.10 export argv contains forbidden secret-shaped material")

    payload: dict[str, object] = {
        "schema_version": 1,
        "source_sha": source_sha,
        "definition_sha256": definition.digest(),
        "workspace_manifest_sha256": workspace_manifest.digest(),
        "xcode_version": xcode_version,
        "iphoneos_sdk_version": iphoneos_sdk,
        "iphonesimulator_sdk_version": simulator_sdk,
        "simulator_build_succeeded": True,
        "unsigned_archive_succeeded": True,
        "archive_info_present": True,
        "archive_product_present": True,
        "code_signing_allowed": False,
        "code_signing_required": False,
        "archive_metadata_readiness": assessment.readiness.value,
        "distribution_signing_capable": assessment.distribution_signing_capable,
        "distribution_credentials_required": assessment.credentials_required,
        "export_method": definition.export_method.value,
        "export_options_prepared": True,
        "export_attempted": False,
        "account_or_signing_credential_used": False,
        "physical_device_capability_proven": False,
        "live_app_store_acceptance_claimed": False,
        "blockers": list(assessment.blockers),
    }
    schema = json.loads(
        (ROOT / "schemas/r13/apple-signing-archive-evidence.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="R13.10 hosted Apple signing/archive acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = build_acceptance_payload(args.source_sha, output)
    output.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "output": str(output),
                "source_sha": payload["source_sha"],
                "xcode_version": payload["xcode_version"],
                "iphoneos_sdk_version": payload["iphoneos_sdk_version"],
                "archive_metadata_readiness": payload["archive_metadata_readiness"],
                "export_attempted": payload["export_attempted"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
