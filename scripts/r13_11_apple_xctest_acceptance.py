from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator

from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.mobile.apple_testing import (
    AppleTestFlightCapability,
    AppleTestResult,
    AppleXCTestEvidence,
    AppleXCTestPlanDefinition,
    build_simctl_boot_argv,
    build_simctl_bootstatus_argv,
    build_xcresult_summary_argv,
    build_xctest_argv,
    parse_simctl_devices,
    parse_xcresult_summary,
    select_simulator,
)
from kodepoia.mobile.apple_xctest_overlay import render_xctest_overlay
from kodepoia.mobile.boundary import MobileToolchainBoundary
from kodepoia.mobile.contracts import MobileFormFactor, MobilePackageKind, MobileSourceKind, MobileToolKind
from kodepoia.mobile.ios_scaffold import (
    AppleScaffoldDefinition,
    AppleScaffoldEngine,
    AppleScaffoldLineage,
    AppleStringCatalog,
)
from kodepoia.project.dna import MobileProjectProfile, Platform, ProjectDNA, ProjectType

ROOT = Path(__file__).resolve().parents[1]


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


def _write_overlay(work_root: Path, overlay: dict[str, str]) -> None:
    root = work_root.resolve(strict=True)
    for relative, content in sorted(overlay.items()):
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise RuntimeError("R13.11 overlay contains an unsafe relative path")
        target = (root / candidate).resolve(strict=False)
        if target != root and root not in target.parents:
            raise RuntimeError("R13.11 overlay escapes canonical project root")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")


def _xcresult_tree_sha256(root: Path) -> str:
    root = root.resolve(strict=True)
    if not root.is_dir() or root.suffix != ".xcresult":
        raise RuntimeError("XCTest result bundle is unavailable")
    digest = hashlib.sha256()
    entries = sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())
    if len(entries) > 200_000:
        raise RuntimeError("XCTest result bundle contains too many entries")
    total_bytes = 0
    for entry in entries:
        relative = entry.relative_to(root).as_posix().encode("utf-8")
        if entry.is_symlink():
            target = os.readlink(entry)
            if len(target) > 4096 or "\x00" in target:
                raise RuntimeError("XCTest result bundle contains an unsafe symlink")
            digest.update(b"L\x00" + relative + b"\x00" + target.encode("utf-8") + b"\x00")
            continue
        if not entry.is_file():
            continue
        digest.update(b"F\x00" + relative + b"\x00")
        with entry.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > 512 * 1024 * 1024:
                    raise RuntimeError("XCTest result bundle exceeds evidence budget")
                digest.update(chunk)
        digest.update(b"\x00")
    return digest.hexdigest()


def build_acceptance_payload(
    source_sha: str,
    output_path: Path,
    result_bundle_path: Path,
) -> dict[str, object]:
    if len(source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise ValueError("--source-sha must be an exact lowercase 40-hex Git SHA")
    if platform.system() != "Darwin":
        raise RuntimeError("R13.11 hosted acceptance requires macOS")

    staging_root = output_path.parent.resolve(strict=False)
    output_path = output_path.resolve(strict=False)
    result_bundle_path = result_bundle_path.resolve(strict=False)
    if output_path.parent != staging_root or result_bundle_path.parent != staging_root:
        raise ValueError("R13.11 output and result bundle must share one bounded staging root")
    if result_bundle_path.suffix != ".xcresult":
        raise ValueError("--result-bundle must use .xcresult suffix")

    work_root = staging_root / f"r13_11_project_{source_sha[:12]}"
    derived_data = staging_root / f"r13_11_derived_{source_sha[:12]}"
    for path in (work_root, derived_data, result_bundle_path):
        if path.exists() or path.is_symlink():
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
    work_root.mkdir(parents=True)

    definition, model = _canonical_definition()
    lineage = AppleScaffoldLineage(
        _digest_text(source_sha + ":dna"),
        _digest_text(source_sha + ":product"),
    )
    engine = AppleScaffoldEngine()
    preview = engine.preview(work_root, definition, model, lineage)
    if preview.has_conflicts:
        raise RuntimeError("canonical R13.11 SwiftUI fixture unexpectedly contains conflicts")
    manifest = engine.apply(work_root, preview)

    plan = AppleXCTestPlanDefinition(
        plan_id="r13.11.canonical",
        scheme=AppleScaffoldEngine.SCHEME_NAME,
        workspace_manifest_sha256=manifest.digest(),
        app_model_sha256=model.digest(),
        minimum_os_version=definition.minimum_os_version,
    )
    pbx_path = work_root / "KodepoiaIOS.xcodeproj/project.pbxproj"
    scheme_path = work_root / "KodepoiaIOS.xcodeproj/xcshareddata/xcschemes/KodepoiaIOS.xcscheme"
    overlay = render_xctest_overlay(
        pbxproj=pbx_path.read_text(encoding="utf-8"),
        scheme=scheme_path.read_text(encoding="utf-8"),
        plan=plan,
    )
    _write_overlay(work_root, overlay)

    xcodebuild_candidate = _required_tool("xcodebuild")
    xcrun_candidate = _required_tool("xcrun")
    boundary = MobileToolchainBoundary(
        allowed_runtime_roots=(Path("/usr/bin"), Path("/Applications")),
        project_root=work_root,
        staging_root=staging_root,
    )
    xcodebuild = boundary.validate_tool(MobileToolKind.XCODEBUILD, xcodebuild_candidate)
    xcrun = boundary.validate_tool(MobileToolKind.XCRUN, xcrun_candidate)
    boundary.validate_staging_path(output_path)
    boundary.validate_staging_path(result_bundle_path)

    devices_output = _run(boundary.build_xcrun_simctl_list_argv(xcrun), timeout=120)
    simulator = select_simulator(parse_simctl_devices(devices_output))
    if simulator.state != "Booted":
        _run(build_simctl_boot_argv(boundary, xcrun, simulator_udid=simulator.udid), timeout=120)
    _run(build_simctl_bootstatus_argv(boundary, xcrun, simulator_udid=simulator.udid), timeout=300)

    project_file = work_root / AppleScaffoldEngine.PROJECT_PATH
    test_argv = build_xctest_argv(
        boundary,
        xcodebuild,
        project_file=project_file,
        plan=plan,
        simulator_udid=simulator.udid,
        derived_data_path=derived_data,
        result_bundle_path=result_bundle_path,
    )
    _run(test_argv, timeout=1200)
    if not result_bundle_path.is_dir():
        raise RuntimeError("xcodebuild test did not produce the requested .xcresult bundle")

    summary_output = _run(
        build_xcresult_summary_argv(
            boundary,
            xcrun,
            result_bundle_path=result_bundle_path,
        ),
        timeout=120,
    )
    summary = parse_xcresult_summary(summary_output)
    if summary.result is not AppleTestResult.PASSED or summary.total_test_count < 2:
        raise RuntimeError("canonical R13.11 XCTest suite did not pass both required tests")

    evidence = AppleXCTestEvidence(
        source_sha=source_sha,
        plan_sha256=plan.digest(),
        workspace_manifest_sha256=manifest.digest(),
        app_model_sha256=model.digest(),
        simulator=simulator,
        summary=summary,
        xcresult_tree_sha256=_xcresult_tree_sha256(result_bundle_path),
        testflight=AppleTestFlightCapability.without_credentials(),
    )
    payload = evidence.to_dict()
    schema = json.loads(
        (ROOT / "schemas/r13/apple-xctest-evidence.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)

    serialized = json.dumps(payload, sort_keys=True).casefold()
    if simulator.udid.casefold() in serialized:
        raise RuntimeError("durable R13.11 evidence leaked raw simulator UDID")
    forbidden = (
        "private_key",
        "provisioning_profile",
        "app_store_connect_token",
        "password",
        "certificate_identity",
    )
    if any(term in serialized for term in forbidden):
        raise RuntimeError("R13.11 durable evidence contains forbidden account/signing material")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="R13.11 hosted iOS Simulator/XCTest acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--result-bundle", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    result_bundle = Path(args.result_bundle)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = build_acceptance_payload(args.source_sha, output, result_bundle)
    output.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
