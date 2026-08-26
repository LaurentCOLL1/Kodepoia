from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator

from kodepoia.desktop.app_model import canonical_sample_app
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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


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


def _canonical_definition() -> tuple[AppleScaffoldDefinition, object]:
    model = canonical_sample_app()
    dna = ProjectDNA(
        schema_version=1,
        name="Kodepoia iOS Acceptance",
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
            AppleStringCatalog(
                "en",
                (("app_name", "Kodepoia iOS Acceptance"), ("status_ready", "Ready")),
            ),
            AppleStringCatalog(
                "fr",
                (("app_name", "Acceptation iOS Kodepoia"), ("status_ready", "Prêt")),
            ),
        ),
    )
    return definition, model


def build_acceptance_payload(source_sha: str, output_path: Path) -> dict[str, object]:
    if len(source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise ValueError("--source-sha must be an exact lowercase 40-hex Git SHA")
    if platform.system() != "Darwin":
        raise RuntimeError("R13.9 hosted acceptance requires macOS")

    work_root = output_path.parent / f"r13_9_project_{source_sha[:12]}"
    derived_data = output_path.parent / f"r13_9_derived_{source_sha[:12]}"
    for path in (work_root, derived_data):
        if path.exists():
            shutil.rmtree(path)
    work_root.mkdir(parents=True)

    definition, model = _canonical_definition()
    lineage = AppleScaffoldLineage(
        _digest_text(source_sha + ":dna"),
        _digest_text(source_sha + ":product"),
    )
    engine = AppleScaffoldEngine()
    preview = engine.preview(work_root, definition, model, lineage)
    if preview.has_conflicts:
        raise RuntimeError("canonical R13.9 scaffold unexpectedly contains conflicts")
    manifest = engine.apply(work_root, preview)

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

    xcode_version, xcode_build = parse_xcodebuild_version(
        _run(boundary.build_probe_argv(MobileToolKind.XCODEBUILD, xcodebuild), timeout=60)
    )
    simulator_sdk = parse_sdk_version(
        _run(boundary.build_xcrun_sdk_version_argv(xcrun, sdk="iphonesimulator"), timeout=60)
    )

    project_file = work_root / AppleScaffoldEngine.PROJECT_PATH
    list_output = _run(
        boundary.build_xcodebuild_list_argv(xcodebuild, project_file=project_file),
        timeout=120,
    )
    listed = json.loads(list_output)
    schemes = listed.get("project", {}).get("schemes", [])
    if AppleScaffoldEngine.SCHEME_NAME not in schemes:
        raise RuntimeError("generated shared Xcode scheme was not discoverable")

    argv = build_ios_simulator_build_argv(
        boundary,
        xcodebuild,
        project_file=project_file,
        scheme=AppleScaffoldEngine.SCHEME_NAME,
        derived_data_path=derived_data,
    )
    _run(argv, timeout=900)

    executables = sorted(
        path
        for path in derived_data.rglob("KodepoiaIOS.app/KodepoiaIOS")
        if path.is_file()
    )
    if not executables:
        raise RuntimeError("hosted simulator build did not produce KodepoiaIOS.app executable")
    executable = executables[0]

    payload: dict[str, object] = {
        "schema_version": 1,
        "source_sha": source_sha,
        "definition_sha256": definition.digest(),
        "workspace_manifest_sha256": manifest.digest(),
        "app_model_sha256": model.digest(),
        "xcode_version": xcode_version,
        "xcode_build": xcode_build,
        "iphonesimulator_sdk_version": simulator_sdk,
        "destination": "generic/platform=iOS Simulator",
        "scheme": AppleScaffoldEngine.SCHEME_NAME,
        "build_configuration": "Debug",
        "code_signing_allowed": False,
        "code_signing_required": False,
        "build_succeeded": True,
        "app_bundle_present": True,
        "app_executable_sha256": _sha256_file(executable),
        "state_strategy": definition.state_strategy.value,
        "physical_device_capability_proven": False,
        "account_or_signing_credential_used": False,
        "blockers": [],
    }
    schema = json.loads(
        (ROOT / "schemas/r13/apple-swiftui-build-evidence.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    serialized = json.dumps(payload, sort_keys=True).casefold()
    forbidden = (
        "private_key",
        "provisioning_profile",
        "development_team",
        "app_store_connect_token",
        "password",
        "certificate_identity",
    )
    if any(term in serialized for term in forbidden):
        raise RuntimeError("R13.9 durable evidence contains forbidden signing/account material")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="R13.9 hosted SwiftUI/Xcode Simulator acceptance")
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
                "iphonesimulator_sdk_version": payload["iphonesimulator_sdk_version"],
                "build_succeeded": payload["build_succeeded"],
                "state_strategy": payload["state_strategy"],
                "physical_device_capability_proven": payload["physical_device_capability_proven"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
