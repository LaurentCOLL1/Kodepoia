from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from kodepoia.mobile.apple_xcode import (
    AppleExecutorDescriptor,
    AppleExecutorKind,
    ApplePolicyFreshness,
    AppleToolchainReadiness,
    AppleXcodeChannel,
    current_apple_xcode_policy_snapshot,
    evaluate_apple_xcode_capability,
    parse_sdk_version,
    parse_simctl_device_count,
    parse_simctl_runtimes,
    parse_xcodebuild_version,
)
from kodepoia.mobile.boundary import MobileBoundaryError, MobileToolchainBoundary
from kodepoia.mobile.contracts import (
    MobileArchitecture,
    MobileCapabilityState,
    MobileHostOS,
    MobileToolKind,
    MobileToolchainIdentity,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "a" * 40


def _identity(kind: MobileToolKind, *, architecture: MobileArchitecture = MobileArchitecture.ARM64):
    return MobileToolchainIdentity(
        tool_kind=kind,
        executable_name=kind.value,
        executable_sha256=("11" if kind is MobileToolKind.XCODEBUILD else "22") * 32,
        version="26.6" if kind is MobileToolKind.XCODEBUILD else "17G86",
        host_os=MobileHostOS.MACOS,
        architecture=architecture,
        capabilities=("probe",),
    )


def _executor(*, architecture: MobileArchitecture = MobileArchitecture.ARM64):
    return AppleExecutorDescriptor(
        kind=AppleExecutorKind.GITHUB_HOSTED,
        provider="github-actions",
        host_os_version="26.0",
        architecture=architecture,
    )


def _runtimes():
    return parse_simctl_runtimes(
        json.dumps(
            {
                "runtimes": [
                    {
                        "identifier": "com.apple.CoreSimulator.SimRuntime.iOS-26-5",
                        "name": "iOS 26.5",
                        "version": "26.5",
                        "isAvailable": True,
                    },
                    {
                        "identifier": "com.apple.CoreSimulator.SimRuntime.watchOS-26-0",
                        "name": "watchOS 26.0",
                        "version": "26.0",
                        "isAvailable": True,
                    },
                ]
            }
        )
    )


def _evaluate(**overrides):
    args = {
        "source_sha": SOURCE,
        "probed_on": "2026-08-26",
        "policy": current_apple_xcode_policy_snapshot(),
        "xcode_version": "26.6",
        "xcode_build": "17G86",
        "xcodebuild_identity": _identity(MobileToolKind.XCODEBUILD),
        "xcrun_identity": _identity(MobileToolKind.XCRUN),
        "iphoneos_sdk_version": "26.5",
        "iphonesimulator_sdk_version": "26.5",
        "simulator_runtimes": _runtimes(),
        "simulator_device_count": 4,
        "executor": _executor(),
    }
    args.update(overrides)
    return evaluate_apple_xcode_capability(**args)


def test_r13_8_parses_public_xcode_and_sdk_identity() -> None:
    assert parse_xcodebuild_version("Xcode 26.6\nBuild version 17G86\n") == ("26.6", "17G86")
    assert parse_sdk_version("26.5\n") == "26.5"
    with pytest.raises(ValueError, match="unexpected xcodebuild"):
        parse_xcodebuild_version("Xcode 26.6; rm -rf /\nBuild version 17G86\n")
    with pytest.raises(ValueError, match="one version"):
        parse_sdk_version("26.5\n--destination evil\n")


def test_r13_8_stable_xcode26_can_claim_only_toolchain_production_readiness() -> None:
    report = _evaluate()
    assert report.channel is AppleXcodeChannel.STABLE
    assert report.capability_state is MobileCapabilityState.AVAILABLE
    assert report.readiness is AppleToolchainReadiness.PRODUCTION_UPLOAD_TOOLCHAIN_READY
    assert report.production_upload_toolchain_capable is True
    assert report.testflight_beta_toolchain_capable is False
    assert report.physical_device_capability_proven is False
    assert report.blockers == ()


def test_r13_8_beta_xcode27_never_manufactures_stable_production_readiness() -> None:
    report = _evaluate(
        xcode_version="27.0",
        xcode_build="18A5319f",
        xcodebuild_identity=MobileToolchainIdentity(
            MobileToolKind.XCODEBUILD,
            "xcodebuild",
            "11" * 32,
            "27.0",
            MobileHostOS.MACOS,
            MobileArchitecture.ARM64,
            ("probe",),
        ),
        xcrun_identity=MobileToolchainIdentity(
            MobileToolKind.XCRUN,
            "xcrun",
            "22" * 32,
            "18A5319f",
            MobileHostOS.MACOS,
            MobileArchitecture.ARM64,
            ("probe",),
        ),
        iphoneos_sdk_version="27.0",
        iphonesimulator_sdk_version="27.0",
    )
    assert report.channel is AppleXcodeChannel.BETA
    assert report.readiness is AppleToolchainReadiness.TESTFLIGHT_BETA_TOOLCHAIN_READY
    assert report.testflight_beta_toolchain_capable is True
    assert report.production_upload_toolchain_capable is False


def test_r13_8_unverified_future_xcode_fails_closed_until_policy_updates() -> None:
    report = _evaluate(
        xcode_version="28.0",
        xcode_build="19A1",
        xcodebuild_identity=MobileToolchainIdentity(
            MobileToolKind.XCODEBUILD,
            "xcodebuild",
            "11" * 32,
            "28.0",
            MobileHostOS.MACOS,
            MobileArchitecture.ARM64,
            ("probe",),
        ),
        iphoneos_sdk_version="28.0",
        iphonesimulator_sdk_version="28.0",
    )
    assert report.channel is AppleXcodeChannel.UNVERIFIED
    assert report.capability_state is MobileCapabilityState.UNSUPPORTED
    assert report.readiness is AppleToolchainReadiness.BLOCKED
    assert "xcode_channel_unverified" in report.blockers
    assert report.production_upload_toolchain_capable is False


def test_r13_8_stale_policy_cannot_claim_production_or_testflight() -> None:
    report = _evaluate(probed_on="2026-10-01")
    assert report.policy_freshness is ApplePolicyFreshness.STALE
    assert report.readiness is AppleToolchainReadiness.BLOCKED
    assert "policy_snapshot_stale" in report.blockers
    assert report.production_upload_toolchain_capable is False
    assert report.testflight_beta_toolchain_capable is False


def test_r13_8_simctl_runtime_and_device_parsers_are_bounded_and_ios_scoped() -> None:
    runtimes = _runtimes()
    assert len(runtimes) == 1
    assert runtimes[0].name == "iOS 26.5"
    devices = parse_simctl_device_count(
        json.dumps(
            {
                "devices": {
                    "com.apple.CoreSimulator.SimRuntime.iOS-26-5": [
                        {"name": "iPhone 17", "isAvailable": True},
                        {"name": "iPad Pro", "isAvailable": True},
                        {"name": "Unavailable old device", "isAvailable": False},
                    ]
                }
            }
        )
    )
    assert devices == 2
    with pytest.raises(ValueError, match="invalid JSON"):
        parse_simctl_runtimes("not-json")


def test_r13_8_missing_runtime_or_device_is_not_available() -> None:
    no_runtime = _evaluate(simulator_runtimes=())
    assert no_runtime.capability_state is MobileCapabilityState.UNSUPPORTED
    assert "ios_simulator_runtime_unavailable" in no_runtime.blockers
    no_device = _evaluate(simulator_device_count=0)
    assert no_device.capability_state is MobileCapabilityState.UNSUPPORTED
    assert "simulator_device_unavailable" in no_device.blockers


def test_r13_8_boundary_builders_allow_only_fixed_apple_operations(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    project_root = tmp_path / "project"
    staging = tmp_path / "staging"
    runtime.mkdir()
    project_root.mkdir()
    staging.mkdir()
    xcodebuild = runtime / "xcodebuild"
    xcrun = runtime / "xcrun"
    xcodebuild.write_text("fixture", encoding="utf-8")
    xcrun.write_text("fixture", encoding="utf-8")
    project = project_root / "Kodepoia.xcodeproj"
    project.mkdir()

    boundary = MobileToolchainBoundary(
        allowed_runtime_roots=(runtime,),
        project_root=project_root,
        staging_root=staging,
    )
    sdk_argv = boundary.build_xcrun_sdk_version_argv(xcrun, sdk="iphoneos")
    assert sdk_argv[-3:] == ("--sdk", "iphoneos", "--show-sdk-version")
    runtime_argv = boundary.build_xcrun_simctl_runtimes_argv(xcrun)
    assert runtime_argv[-4:] == ("simctl", "list", "runtimes", "--json")
    destinations = boundary.build_xcodebuild_show_destinations_argv(
        xcodebuild,
        project_file=project,
        scheme="Kodepoia",
    )
    assert destinations[-3:] == ("-scheme", "Kodepoia", "-showdestinations")

    with pytest.raises(MobileBoundaryError, match="SDK"):
        boundary.build_xcrun_sdk_version_argv(xcrun, sdk="iphoneos;rm")
    with pytest.raises(MobileBoundaryError, match="scheme"):
        boundary.build_xcodebuild_show_destinations_argv(
            xcodebuild,
            project_file=project,
            scheme="Kodepoia -destination platform=iOS",
        )
    substituted = runtime / "bash"
    substituted.write_text("fixture", encoding="utf-8")
    with pytest.raises(MobileBoundaryError, match="unexpected tool"):
        boundary.build_probe_argv(MobileToolKind.XCODEBUILD, substituted)


def test_r13_8_executor_contract_is_bounded_noninteractive_and_no_secret_fields() -> None:
    executor = _executor()
    payload = executor.to_dict()
    assert payload["interactive"] is False
    assert payload["network_allowed"] is False
    assert "credential" not in payload
    with pytest.raises(ValueError, match="non-interactive"):
        AppleExecutorDescriptor(
            AppleExecutorKind.REMOTE_GOVERNED,
            "remote-mac",
            "26.0",
            MobileArchitecture.ARM64,
            interactive=True,
        )


def test_r13_8_identity_architecture_substitution_is_rejected() -> None:
    with pytest.raises(ValueError, match="architecture substitution"):
        _evaluate(
            xcrun_identity=_identity(
                MobileToolKind.XCRUN, architecture=MobileArchitecture.X86_64
            )
        )


def test_r13_8_report_digest_is_deterministic() -> None:
    first = _evaluate()
    second = _evaluate()
    assert first.to_dict() == second.to_dict()
    assert first.digest() == second.digest()


def test_r13_8_report_schema_is_strict_and_rejects_account_or_signing_material() -> None:
    schema = json.loads(
        (ROOT / "schemas/r13/apple-xcode-capability.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    payload = _evaluate().to_dict()
    Draft202012Validator(schema).validate(payload)
    payload["apple_team_id"] = "FORBIDDEN"
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(payload)
