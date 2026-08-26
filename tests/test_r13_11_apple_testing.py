from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.mobile.apple_testing import (
    AppleEvidenceScope,
    AppleRemoteCapabilityState,
    AppleSimulatorDevice,
    AppleTestFlightCapability,
    AppleTestResult,
    AppleXCTestEvidence,
    AppleXCTestPlanDefinition,
    AppleXCTestSummary,
    build_simctl_boot_argv,
    build_simctl_bootstatus_argv,
    build_simctl_create_argv,
    build_xcresult_summary_argv,
    build_xctest_argv,
    parse_simctl_devices,
    parse_xcresult_summary,
    render_xctest_overlay,
    select_simulator,
)
from kodepoia.mobile.boundary import MobileBoundaryError, MobileToolchainBoundary
from kodepoia.mobile.contracts import MobileFormFactor, MobilePackageKind, MobileSourceKind
from kodepoia.mobile.ios_scaffold import AppleScaffoldDefinition, AppleScaffoldEngine, AppleScaffoldLineage
from kodepoia.project.dna import MobileProjectProfile, Platform, ProjectDNA, ProjectType

ROOT = Path(__file__).resolve().parents[1]


def _sha(ch: str) -> str:
    return ch * 64


def _plan() -> AppleXCTestPlanDefinition:
    return AppleXCTestPlanDefinition(
        plan_id="r13.11.canonical",
        scheme="KodepoiaIOS",
        workspace_manifest_sha256=_sha("a"),
        app_model_sha256=_sha("b"),
    )


def _simulator(*, os_version: str = "26.0", name: str = "iPhone 17 Pro") -> AppleSimulatorDevice:
    runtime = "com.apple.CoreSimulator.SimRuntime.iOS-" + os_version.replace(".", "-")
    return AppleSimulatorDevice(
        udid="12345678-1234-1234-1234-1234567890AB",
        name=name,
        runtime_identifier=runtime,
        os_version=os_version,
        device_type_identifier="com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro",
        state="Shutdown",
        available=True,
    )


def _definition() -> tuple[AppleScaffoldDefinition, object]:
    model = canonical_sample_app()
    dna = ProjectDNA(
        schema_version=1,
        name="R13.11 Fixture",
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
    return AppleScaffoldDefinition.from_project(dna, model), model


def test_r13_11_simctl_devices_are_strict_and_selection_is_deterministic() -> None:
    payload = {
        "devices": {
            "com.apple.CoreSimulator.SimRuntime.iOS-25-4": [
                {
                    "udid": "11111111-1111-1111-1111-111111111111",
                    "name": "iPhone 16",
                    "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-16",
                    "state": "Shutdown",
                    "isAvailable": True,
                }
            ],
            "com.apple.CoreSimulator.SimRuntime.iOS-26-0": [
                {
                    "udid": "22222222-2222-2222-2222-222222222222",
                    "name": "iPad Pro",
                    "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPad-Pro",
                    "state": "Shutdown",
                    "isAvailable": True,
                },
                {
                    "udid": "33333333-3333-3333-3333-333333333333",
                    "name": "iPhone 17 Pro",
                    "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro",
                    "state": "Shutdown",
                    "isAvailable": True,
                },
            ],
        }
    }
    devices = parse_simctl_devices(json.dumps(payload))
    selected = select_simulator(devices)
    assert selected.os_version == "26.0"
    assert selected.name == "iPhone 17 Pro"
    assert selected.udid == "33333333-3333-3333-3333-333333333333"
    assert selected.public_dict()["virtual"] is True
    assert selected.udid not in json.dumps(selected.public_dict())


def test_r13_11_simctl_rejects_malformed_or_unavailable_only_inputs() -> None:
    with pytest.raises(ValueError):
        parse_simctl_devices('{"devices":[],"extra":true}')
    unavailable = {
        "devices": {
            "com.apple.CoreSimulator.SimRuntime.iOS-26-0": [
                {
                    "udid": "22222222-2222-2222-2222-222222222222",
                    "name": "iPhone 17",
                    "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17",
                    "state": "Shutdown",
                    "isAvailable": False,
                }
            ]
        }
    }
    with pytest.raises(ValueError, match="no usable"):
        select_simulator(parse_simctl_devices(json.dumps(unavailable)))


def test_r13_11_xcresult_summary_is_bounded_and_truthful() -> None:
    summary = parse_xcresult_summary(
        json.dumps(
            {
                "result": "Passed",
                "totalTestCount": 2,
                "passedTests": 2,
                "failedTests": 0,
                "skippedTests": 0,
                "expectedFailures": 0,
                "devicesAndConfigurations": [],
            }
        )
    )
    assert summary.result is AppleTestResult.PASSED
    assert summary.total_test_count == 2
    with pytest.raises(ValueError):
        parse_xcresult_summary(
            json.dumps(
                {
                    "result": "Passed",
                    "totalTestCount": 1,
                    "passedTests": 0,
                    "failedTests": 1,
                    "skippedTests": 0,
                }
            )
        )
    with pytest.raises(ValueError, match="unsupported result"):
        parse_xcresult_summary('{"result":"Unknown"}')


def test_r13_11_testflight_without_credentials_is_unavailable_not_pass() -> None:
    state = AppleTestFlightCapability.without_credentials()
    assert state.state is AppleRemoteCapabilityState.UNAVAILABLE
    assert state.live_query_attempted is False
    assert state.remote_build_state_proven is False
    assert state.blockers == ("app_store_connect_credentials_unavailable",)
    ready = AppleTestFlightCapability.ready_to_query("apple_asc_ci")
    assert ready.state is AppleRemoteCapabilityState.READY_TO_QUERY
    assert ready.credential_reference_present is True
    assert ready.live_query_attempted is False
    assert ready.remote_build_state_proven is False


def test_r13_11_simulator_evidence_schema_cannot_claim_physical_or_testflight() -> None:
    summary = AppleXCTestSummary(AppleTestResult.PASSED, 2, 2, 0, 0)
    evidence = AppleXCTestEvidence(
        source_sha="1" * 40,
        plan_sha256=_plan().digest(),
        workspace_manifest_sha256=_sha("a"),
        app_model_sha256=_sha("b"),
        simulator=_simulator(),
        summary=summary,
        xcresult_tree_sha256=_sha("c"),
        testflight=AppleTestFlightCapability.without_credentials(),
    )
    payload = evidence.to_dict()
    assert payload["scope"] == AppleEvidenceScope.SIMULATOR.value
    assert payload["physical_device_capability_proven"] is False
    assert payload["testflight"]["remote_build_state_proven"] is False
    schema = json.loads((ROOT / "schemas/r13/apple-xctest-evidence.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    with pytest.raises(ValueError, match="physical"):
        AppleXCTestEvidence(
            source_sha="1" * 40,
            plan_sha256=_plan().digest(),
            workspace_manifest_sha256=_sha("a"),
            app_model_sha256=_sha("b"),
            simulator=_simulator(),
            summary=summary,
            xcresult_tree_sha256=_sha("c"),
            testflight=AppleTestFlightCapability.without_credentials(),
            physical_device_capability_proven=True,
        )


def test_r13_11_xctest_overlay_is_deterministic_and_binds_r13_9_model() -> None:
    definition, model = _definition()
    files, manifest = AppleScaffoldEngine().render(
        definition,
        model,
        AppleScaffoldLineage(_sha("d"), _sha("e")),
    )
    by_path = {item.path: item.content for item in files}
    plan = AppleXCTestPlanDefinition(
        plan_id="r13.11.canonical",
        scheme="KodepoiaIOS",
        workspace_manifest_sha256=manifest.digest(),
        app_model_sha256=model.digest(),
    )
    kwargs = {
        "pbxproj": by_path["KodepoiaIOS.xcodeproj/project.pbxproj"],
        "scheme": by_path["KodepoiaIOS.xcodeproj/xcshareddata/xcschemes/KodepoiaIOS.xcscheme"],
        "plan": plan,
    }
    overlay_a = render_xctest_overlay(**kwargs)
    overlay_b = render_xctest_overlay(**kwargs)
    assert overlay_a == overlay_b
    assert "KodepoiaIOSTests" in overlay_a["KodepoiaIOS.xcodeproj/project.pbxproj"]
    assert "E30000000000000000000001" in overlay_a[
        "KodepoiaIOS.xcodeproj/xcshareddata/xcschemes/KodepoiaIOS.xcscheme"
    ]
    test_source = overlay_a["KodepoiaIOSTests/KodepoiaIOSTests.swift"]
    assert "@testable import KodepoiaIOS" in test_source
    assert model.digest() in test_source
    assert manifest.digest() in test_source
    with pytest.raises(ValueError, match="already present"):
        render_xctest_overlay(
            pbxproj=overlay_a["KodepoiaIOS.xcodeproj/project.pbxproj"],
            scheme=overlay_a["KodepoiaIOS.xcodeproj/xcshareddata/xcschemes/KodepoiaIOS.xcscheme"],
            plan=plan,
        )


def test_r13_11_typed_argv_rejects_raw_destination_and_output_escape(tmp_path: Path) -> None:
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
    project = project_root / "KodepoiaIOS.xcodeproj"
    project.mkdir()
    boundary = MobileToolchainBoundary(
        allowed_runtime_roots=(runtime,),
        project_root=project_root,
        staging_root=staging,
    )
    udid = "12345678-1234-1234-1234-1234567890AB"
    argv = build_xctest_argv(
        boundary,
        xcodebuild,
        project_file=project,
        plan=_plan(),
        simulator_udid=udid,
        derived_data_path=staging / "DerivedData",
        result_bundle_path=staging / "Result.xcresult",
    )
    assert argv[-1] == "test"
    assert f"id={udid}" in argv
    assert "CODE_SIGNING_ALLOWED=NO" in argv
    assert "CODE_SIGNING_REQUIRED=NO" in argv
    assert build_simctl_boot_argv(boundary, xcrun, simulator_udid=udid)[1:3] == ("simctl", "boot")
    assert build_simctl_bootstatus_argv(boundary, xcrun, simulator_udid=udid)[1:3] == ("simctl", "bootstatus")
    create = build_simctl_create_argv(
        boundary,
        xcrun,
        device_type_identifier="com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro",
        runtime_identifier="com.apple.CoreSimulator.SimRuntime.iOS-26-0",
    )
    assert create[1:3] == ("simctl", "create")
    summary = build_xcresult_summary_argv(
        boundary,
        xcrun,
        result_bundle_path=staging / "Result.xcresult",
    )
    assert summary[1:5] == ("xcresulttool", "get", "test-results", "summary")
    with pytest.raises(MobileBoundaryError):
        build_xctest_argv(
            boundary,
            xcodebuild,
            project_file=project,
            plan=_plan(),
            simulator_udid="platform=iOS Simulator,name=evil -showBuildSettings",
            derived_data_path=staging / "DerivedData",
            result_bundle_path=staging / "Result.xcresult",
        )
    with pytest.raises(MobileBoundaryError):
        build_xctest_argv(
            boundary,
            xcodebuild,
            project_file=project,
            plan=_plan(),
            simulator_udid=udid,
            derived_data_path=staging / "DerivedData",
            result_bundle_path=tmp_path / "escape.xcresult",
        )


def test_r13_11_plan_rejects_identifier_and_digest_injection() -> None:
    with pytest.raises(ValueError):
        AppleXCTestPlanDefinition(
            plan_id="r13.11; rm -rf /",
            scheme="KodepoiaIOS",
            workspace_manifest_sha256=_sha("a"),
            app_model_sha256=_sha("b"),
        )
    with pytest.raises(ValueError):
        AppleXCTestPlanDefinition(
            plan_id="r13.11.canonical",
            scheme="KodepoiaIOS -showBuildSettings",
            workspace_manifest_sha256=_sha("a"),
            app_model_sha256=_sha("b"),
        )
