from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator

from kodepoia.mobile.apple_xcode import (
    AppleExecutorDescriptor,
    AppleExecutorKind,
    AppleToolchainReadiness,
    current_apple_xcode_policy_snapshot,
    evaluate_apple_xcode_capability,
    parse_sdk_version,
    parse_simctl_device_count,
    parse_simctl_runtimes,
    parse_xcodebuild_version,
)
from kodepoia.mobile.boundary import MobileToolchainBoundary
from kodepoia.mobile.contracts import (
    MobileArchitecture,
    MobileCapabilityState,
    MobileHostOS,
    MobileToolKind,
    MobileToolchainIdentity,
)

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


def _run(argv: tuple[str, ...], *, timeout: int = 60) -> str:
    completed = subprocess.run(
        argv,
        check=True,
        capture_output=True,
        text=True,
        shell=False,
        timeout=timeout,
    )
    if completed.stderr and not completed.stdout:
        return completed.stderr
    return completed.stdout


def _architecture() -> MobileArchitecture:
    machine = platform.machine().casefold()
    if machine in {"arm64", "aarch64"}:
        return MobileArchitecture.ARM64
    if machine in {"x86_64", "amd64"}:
        return MobileArchitecture.X86_64
    raise RuntimeError(f"unsupported hosted macOS architecture: {machine}")


def _required_tool(name: str) -> Path:
    candidate = shutil.which(name)
    if candidate is None:
        raise RuntimeError(f"required hosted macOS tool is unavailable: {name}")
    return Path(candidate)


def build_acceptance_payload(source_sha: str, output_path: Path) -> dict[str, object]:
    if len(source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise ValueError("--source-sha must be an exact lowercase 40-hex Git SHA")
    if platform.system() != "Darwin":
        raise RuntimeError("R13.8 hosted acceptance requires macOS")

    xcodebuild_candidate = _required_tool("xcodebuild")
    xcrun_candidate = _required_tool("xcrun")
    allowed_roots = (Path("/usr/bin"), Path("/Applications"))
    boundary = MobileToolchainBoundary(
        allowed_runtime_roots=allowed_roots,
        project_root=ROOT,
        staging_root=output_path.parent,
    )
    xcodebuild = boundary.validate_tool(MobileToolKind.XCODEBUILD, xcodebuild_candidate)
    xcrun = boundary.validate_tool(MobileToolKind.XCRUN, xcrun_candidate)
    boundary.validate_staging_path(output_path)

    xcode_version, xcode_build = parse_xcodebuild_version(
        _run(boundary.build_probe_argv(MobileToolKind.XCODEBUILD, xcodebuild))
    )
    iphoneos_sdk = parse_sdk_version(
        _run(boundary.build_xcrun_sdk_version_argv(xcrun, sdk="iphoneos"))
    )
    simulator_sdk = parse_sdk_version(
        _run(boundary.build_xcrun_sdk_version_argv(xcrun, sdk="iphonesimulator"))
    )
    runtimes = parse_simctl_runtimes(
        _run(boundary.build_xcrun_simctl_runtimes_argv(xcrun))
    )
    device_count = parse_simctl_device_count(
        _run(boundary.build_xcrun_simctl_list_argv(xcrun))
    )

    architecture = _architecture()
    host_version = platform.mac_ver()[0]
    if not host_version:
        raise RuntimeError("hosted macOS version could not be determined")

    xcodebuild_identity = MobileToolchainIdentity(
        tool_kind=MobileToolKind.XCODEBUILD,
        executable_name=xcodebuild.name,
        executable_sha256=_sha256_file(xcodebuild),
        version=xcode_version,
        host_os=MobileHostOS.MACOS,
        architecture=architecture,
        capabilities=("fixed_probe", "project_list", "show_destinations"),
    )
    xcrun_identity = MobileToolchainIdentity(
        tool_kind=MobileToolKind.XCRUN,
        executable_name=xcrun.name,
        executable_sha256=_sha256_file(xcrun),
        version=xcode_build,
        host_os=MobileHostOS.MACOS,
        architecture=architecture,
        capabilities=("fixed_probe", "sdk_version", "simctl_list"),
    )
    report = evaluate_apple_xcode_capability(
        source_sha=source_sha,
        probed_on=date.today().isoformat(),
        policy=current_apple_xcode_policy_snapshot(),
        xcode_version=xcode_version,
        xcode_build=xcode_build,
        xcodebuild_identity=xcodebuild_identity,
        xcrun_identity=xcrun_identity,
        iphoneos_sdk_version=iphoneos_sdk,
        iphonesimulator_sdk_version=simulator_sdk,
        simulator_runtimes=runtimes,
        simulator_device_count=device_count,
        executor=AppleExecutorDescriptor(
            kind=AppleExecutorKind.GITHUB_HOSTED,
            provider="github-actions",
            host_os_version=host_version,
            architecture=architecture,
            timeout_seconds=900,
            cancellation_supported=True,
            interactive=False,
            network_allowed=False,
            staging_scope="runner-temp",
            output_scope="runner-temp",
        ),
    )

    if report.capability_state is not MobileCapabilityState.AVAILABLE:
        raise RuntimeError(f"hosted Xcode capability is not AVAILABLE: {report.blockers}")
    if report.readiness is not AppleToolchainReadiness.PRODUCTION_UPLOAD_TOOLCHAIN_READY:
        raise RuntimeError(
            "hosted stable Xcode toolchain did not prove production-upload toolchain readiness"
        )
    if not report.production_upload_toolchain_capable:
        raise RuntimeError("hosted Xcode probe did not prove stable production toolchain capability")
    if report.testflight_beta_toolchain_capable:
        raise RuntimeError("stable hosted Xcode probe was misclassified as TestFlight beta")
    if report.physical_device_capability_proven:
        raise RuntimeError("hosted R13.8 probe manufactured physical-device evidence")

    payload = report.to_dict()
    schema = json.loads(
        (ROOT / "schemas/r13/apple-xcode-capability.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    serialized = json.dumps(payload, sort_keys=True)
    forbidden = (
        "private_key",
        "provisioning_profile",
        "app_store_connect_token",
        "apple_team_id",
        "password",
    )
    if any(term in serialized.casefold() for term in forbidden):
        raise RuntimeError("R13.8 durable evidence contains forbidden credential/signing material")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="R13.8 hosted Apple/Xcode capability acceptance")
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
                "xcode_build": payload["xcode_build"],
                "channel": payload["channel"],
                "readiness": payload["readiness"],
                "production_upload_toolchain_capable": payload[
                    "production_upload_toolchain_capable"
                ],
                "physical_device_capability_proven": payload[
                    "physical_device_capability_proven"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
