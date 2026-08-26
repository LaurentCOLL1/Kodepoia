from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from .boundary import MobileBoundaryError, MobileToolchainBoundary
from .contracts import MobileToolKind, canonical_json_bytes

_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_STABLE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,127}$")
_UDID_RE = re.compile(r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$")
_RUNTIME_ID_RE = re.compile(r"^com\.apple\.CoreSimulator\.SimRuntime\.[A-Za-z0-9._-]{1,128}$")
_DEVICE_TYPE_ID_RE = re.compile(r"^com\.apple\.CoreSimulator\.SimDeviceType\.[A-Za-z0-9._-]{1,128}$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}$")
_MAX_TEXT = 1_048_576
_MAX_DEVICES = 2048
_MAX_TESTS = 1_000_000


class AppleEvidenceScope(StrEnum):
    SIMULATOR = "SIMULATOR"
    PHYSICAL_DEVICE = "PHYSICAL_DEVICE"
    TESTFLIGHT = "TESTFLIGHT"


class AppleTestResult(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"


class AppleRemoteCapabilityState(StrEnum):
    UNAVAILABLE = "UNAVAILABLE"
    READY_TO_QUERY = "READY_TO_QUERY"
    QUERY_FAILED = "QUERY_FAILED"
    REMOTE_STATE_PROVEN = "REMOTE_STATE_PROVEN"


def _sha256(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable identifier")
    return value


def _bounded_json(output: str, *, field: str) -> Mapping[str, Any]:
    if not isinstance(output, str) or len(output) > _MAX_TEXT or "\x00" in output:
        raise ValueError(f"{field} is invalid or too large")
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field} is not valid JSON") from exc
    if not isinstance(payload, Mapping):
        raise ValueError(f"{field} must be a JSON object")
    return payload


def _runtime_version(runtime_identifier: str) -> str:
    if _RUNTIME_ID_RE.fullmatch(runtime_identifier) is None:
        raise ValueError("invalid simulator runtime identifier")
    marker = ".iOS-"
    if marker not in runtime_identifier:
        raise ValueError("R13.11 supports iOS simulator runtimes only")
    raw = runtime_identifier.split(marker, 1)[1].replace("-", ".")
    if _VERSION_RE.fullmatch(raw) is None:
        raise ValueError("simulator runtime version is invalid")
    return raw


def _version_key(value: str) -> tuple[int, ...]:
    if _VERSION_RE.fullmatch(value) is None:
        raise ValueError("invalid numeric version")
    return tuple(int(part) for part in value.split("."))


@dataclass(frozen=True, slots=True)
class AppleSimulatorDevice:
    udid: str
    name: str
    runtime_identifier: str
    os_version: str
    device_type_identifier: str
    state: str
    available: bool

    def __post_init__(self) -> None:
        if _UDID_RE.fullmatch(self.udid) is None:
            raise ValueError("invalid simulator UDID")
        if not isinstance(self.name, str) or not self.name.strip() or len(self.name) > 128:
            raise ValueError("invalid simulator name")
        if _RUNTIME_ID_RE.fullmatch(self.runtime_identifier) is None:
            raise ValueError("invalid simulator runtime identifier")
        if _VERSION_RE.fullmatch(self.os_version) is None:
            raise ValueError("invalid simulator OS version")
        if _DEVICE_TYPE_ID_RE.fullmatch(self.device_type_identifier) is None:
            raise ValueError("invalid simulator device type identifier")
        if self.state not in {"Booted", "Shutdown", "Creating", "Shutting Down"}:
            raise ValueError("unsupported simulator state")
        if not isinstance(self.available, bool):
            raise ValueError("simulator availability must be boolean")

    @property
    def udid_sha256(self) -> str:
        return hashlib.sha256(self.udid.lower().encode("ascii")).hexdigest()

    def public_dict(self) -> dict[str, object]:
        return {
            "device_id_sha256": self.udid_sha256,
            "name": self.name,
            "runtime_identifier": self.runtime_identifier,
            "os_version": self.os_version,
            "device_type_identifier": self.device_type_identifier,
            "virtual": True,
        }


@dataclass(frozen=True, slots=True)
class AppleXCTestPlanDefinition:
    plan_id: str
    scheme: str
    workspace_manifest_sha256: str
    app_model_sha256: str
    minimum_os_version: str = "17.0"
    test_target: str = "KodepoiaIOSTests"

    def __post_init__(self) -> None:
        _stable_id(self.plan_id, field="plan_id")
        _stable_id(self.scheme, field="scheme")
        _stable_id(self.test_target, field="test_target")
        _sha256(self.workspace_manifest_sha256, field="workspace_manifest_sha256")
        _sha256(self.app_model_sha256, field="app_model_sha256")
        if _VERSION_RE.fullmatch(self.minimum_os_version) is None:
            raise ValueError("minimum_os_version must be numeric dotted form")

    def to_dict(self) -> dict[str, object]:
        return {
            "plan_id": self.plan_id,
            "scheme": self.scheme,
            "workspace_manifest_sha256": self.workspace_manifest_sha256,
            "app_model_sha256": self.app_model_sha256,
            "minimum_os_version": self.minimum_os_version,
            "test_target": self.test_target,
        }

    def digest(self) -> str:
        return hashlib.sha256(canonical_json_bytes(self.to_dict())).hexdigest()


@dataclass(frozen=True, slots=True)
class AppleXCTestSummary:
    result: AppleTestResult
    total_test_count: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    expected_failures: int = 0

    def __post_init__(self) -> None:
        values = (
            self.total_test_count,
            self.passed_tests,
            self.failed_tests,
            self.skipped_tests,
            self.expected_failures,
        )
        if any(not isinstance(value, int) or value < 0 or value > _MAX_TESTS for value in values):
            raise ValueError("XCTest counts are outside bounded range")
        if self.passed_tests + self.failed_tests + self.skipped_tests > self.total_test_count:
            raise ValueError("XCTest component counts exceed total")
        if self.result is AppleTestResult.PASSED and self.failed_tests != 0:
            raise ValueError("PASSED XCTest summary cannot contain failed tests")
        if self.result is AppleTestResult.FAILED and self.failed_tests < 1:
            raise ValueError("FAILED XCTest summary requires failed tests")

    def to_dict(self) -> dict[str, object]:
        return {
            "result": self.result.value,
            "total_test_count": self.total_test_count,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "expected_failures": self.expected_failures,
        }


@dataclass(frozen=True, slots=True)
class AppleTestFlightCapability:
    state: AppleRemoteCapabilityState
    credential_reference_present: bool
    live_query_attempted: bool
    remote_build_state_proven: bool
    blockers: tuple[str, ...]

    def __post_init__(self) -> None:
        blockers = tuple(sorted(set(self.blockers)))
        for blocker in blockers:
            _stable_id(blocker, field="blocker")
        object.__setattr__(self, "blockers", blockers)
        if self.state is AppleRemoteCapabilityState.UNAVAILABLE:
            if self.credential_reference_present or self.live_query_attempted or self.remote_build_state_proven:
                raise ValueError("UNAVAILABLE TestFlight capability cannot claim credentials/query/state")
            if not blockers:
                raise ValueError("UNAVAILABLE TestFlight capability requires a blocker")
        elif self.state is AppleRemoteCapabilityState.READY_TO_QUERY:
            if not self.credential_reference_present or self.live_query_attempted or self.remote_build_state_proven:
                raise ValueError("READY_TO_QUERY requires only an explicit credential reference")
            if blockers:
                raise ValueError("READY_TO_QUERY cannot contain blockers")
        elif self.state is AppleRemoteCapabilityState.QUERY_FAILED:
            if not self.credential_reference_present or not self.live_query_attempted or self.remote_build_state_proven:
                raise ValueError("QUERY_FAILED state is inconsistent")
            if not blockers:
                raise ValueError("QUERY_FAILED requires a blocker")
        elif self.state is AppleRemoteCapabilityState.REMOTE_STATE_PROVEN:
            if not self.credential_reference_present or not self.live_query_attempted or not self.remote_build_state_proven:
                raise ValueError("REMOTE_STATE_PROVEN requires credentialed live evidence")
            if blockers:
                raise ValueError("REMOTE_STATE_PROVEN cannot contain blockers")

    @classmethod
    def without_credentials(cls) -> "AppleTestFlightCapability":
        return cls(
            AppleRemoteCapabilityState.UNAVAILABLE,
            False,
            False,
            False,
            ("app_store_connect_credentials_unavailable",),
        )

    @classmethod
    def ready_to_query(cls, credential_reference: str) -> "AppleTestFlightCapability":
        _stable_id(credential_reference, field="credential_reference")
        return cls(AppleRemoteCapabilityState.READY_TO_QUERY, True, False, False, ())

    def to_dict(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "credential_reference_present": self.credential_reference_present,
            "live_query_attempted": self.live_query_attempted,
            "remote_build_state_proven": self.remote_build_state_proven,
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True, slots=True)
class AppleXCTestEvidence:
    source_sha: str
    plan_sha256: str
    workspace_manifest_sha256: str
    app_model_sha256: str
    simulator: AppleSimulatorDevice
    summary: AppleXCTestSummary
    xcresult_tree_sha256: str
    testflight: AppleTestFlightCapability
    physical_device_capability_proven: bool = False
    signing_credential_used: bool = False

    def __post_init__(self) -> None:
        if _SOURCE_SHA_RE.fullmatch(self.source_sha) is None:
            raise ValueError("source_sha must be an exact lowercase 40-hex Git SHA")
        _sha256(self.plan_sha256, field="plan_sha256")
        _sha256(self.workspace_manifest_sha256, field="workspace_manifest_sha256")
        _sha256(self.app_model_sha256, field="app_model_sha256")
        _sha256(self.xcresult_tree_sha256, field="xcresult_tree_sha256")
        if self.physical_device_capability_proven:
            raise ValueError("simulator XCTest evidence cannot certify a physical device")
        if self.signing_credential_used:
            raise ValueError("R13.11 simulator acceptance must not use signing credentials")
        if self.summary.result is not AppleTestResult.PASSED:
            raise ValueError("accepted XCTest evidence requires a passing summary")
        if self.testflight.remote_build_state_proven:
            raise ValueError("core simulator evidence must not contain live TestFlight proof")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "source_sha": self.source_sha,
            "scope": AppleEvidenceScope.SIMULATOR.value,
            "plan_sha256": self.plan_sha256,
            "workspace_manifest_sha256": self.workspace_manifest_sha256,
            "app_model_sha256": self.app_model_sha256,
            "simulator": self.simulator.public_dict(),
            "summary": self.summary.to_dict(),
            "xcresult_tree_sha256": self.xcresult_tree_sha256,
            "physical_device_capability_proven": self.physical_device_capability_proven,
            "signing_credential_used": self.signing_credential_used,
            "testflight": self.testflight.to_dict(),
            "blockers": [],
        }

    def digest(self) -> str:
        return hashlib.sha256(canonical_json_bytes(self.to_dict())).hexdigest()


def parse_simctl_devices(output: str) -> tuple[AppleSimulatorDevice, ...]:
    payload = _bounded_json(output, field="simctl devices output")
    if set(payload) != {"devices"} or not isinstance(payload["devices"], Mapping):
        raise ValueError("simctl devices payload must contain only a devices object")
    groups = payload["devices"]
    if len(groups) > 128:
        raise ValueError("too many simulator runtime groups")
    result: list[AppleSimulatorDevice] = []
    for runtime_identifier, raw_devices in groups.items():
        if not isinstance(runtime_identifier, str) or ".iOS-" not in runtime_identifier:
            continue
        version = _runtime_version(runtime_identifier)
        if not isinstance(raw_devices, list):
            raise ValueError("simctl runtime device group must be a list")
        for raw in raw_devices:
            if not isinstance(raw, Mapping):
                raise ValueError("simctl device entry must be an object")
            udid = raw.get("udid")
            name = raw.get("name")
            device_type = raw.get("deviceTypeIdentifier")
            state = raw.get("state")
            available = raw.get("isAvailable", True)
            if not all(isinstance(item, str) for item in (udid, name, device_type, state)):
                raise ValueError("simctl device entry is missing public identity fields")
            if not isinstance(available, bool):
                raise ValueError("simctl device availability must be boolean")
            result.append(
                AppleSimulatorDevice(
                    udid=udid,
                    name=name,
                    runtime_identifier=runtime_identifier,
                    os_version=version,
                    device_type_identifier=device_type,
                    state=state,
                    available=available,
                )
            )
            if len(result) > _MAX_DEVICES:
                raise ValueError("too many simulator devices")
    return tuple(result)


def select_simulator(devices: tuple[AppleSimulatorDevice, ...]) -> AppleSimulatorDevice:
    candidates = [item for item in devices if item.available and item.state in {"Booted", "Shutdown"}]
    if not candidates:
        raise ValueError("no usable iOS Simulator device is available")

    def preference(item: AppleSimulatorDevice) -> tuple[tuple[int, ...], int, str, str]:
        phone_rank = 1 if item.name.startswith("iPhone") else 0
        return (_version_key(item.os_version), phone_rank, item.name, item.udid)

    return max(candidates, key=preference)


def build_simctl_boot_argv(
    boundary: MobileToolchainBoundary,
    xcrun: Path,
    *,
    simulator_udid: str,
) -> tuple[str, ...]:
    if _UDID_RE.fullmatch(simulator_udid) is None:
        raise MobileBoundaryError("simulator UDID is invalid")
    tool = boundary.validate_tool(MobileToolKind.XCRUN, xcrun)
    return (str(tool), "simctl", "boot", simulator_udid.upper())


def build_simctl_bootstatus_argv(
    boundary: MobileToolchainBoundary,
    xcrun: Path,
    *,
    simulator_udid: str,
) -> tuple[str, ...]:
    if _UDID_RE.fullmatch(simulator_udid) is None:
        raise MobileBoundaryError("simulator UDID is invalid")
    tool = boundary.validate_tool(MobileToolKind.XCRUN, xcrun)
    return (str(tool), "simctl", "bootstatus", simulator_udid.upper(), "-b")


def build_simctl_create_argv(
    boundary: MobileToolchainBoundary,
    xcrun: Path,
    *,
    device_type_identifier: str,
    runtime_identifier: str,
) -> tuple[str, ...]:
    if _DEVICE_TYPE_ID_RE.fullmatch(device_type_identifier) is None:
        raise MobileBoundaryError("simulator device type identifier is invalid")
    if _RUNTIME_ID_RE.fullmatch(runtime_identifier) is None or ".iOS-" not in runtime_identifier:
        raise MobileBoundaryError("simulator runtime identifier is invalid")
    tool = boundary.validate_tool(MobileToolKind.XCRUN, xcrun)
    return (
        str(tool),
        "simctl",
        "create",
        "Kodepoia-R13-11",
        device_type_identifier,
        runtime_identifier,
    )


def build_xctest_argv(
    boundary: MobileToolchainBoundary,
    xcodebuild: Path,
    *,
    project_file: Path,
    plan: AppleXCTestPlanDefinition,
    simulator_udid: str,
    derived_data_path: Path,
    result_bundle_path: Path,
) -> tuple[str, ...]:
    if _UDID_RE.fullmatch(simulator_udid) is None:
        raise MobileBoundaryError("simulator UDID is invalid")
    tool = boundary.validate_tool(MobileToolKind.XCODEBUILD, xcodebuild)
    project = boundary.validate_xcode_container(project_file)
    derived = boundary.validate_staging_path(derived_data_path)
    result = boundary.validate_staging_path(result_bundle_path)
    if result.suffix != ".xcresult":
        raise MobileBoundaryError("XCTest result bundle must use .xcresult suffix")
    selector = "-workspace" if project.suffix == ".xcworkspace" else "-project"
    return (
        str(tool),
        selector,
        str(project),
        "-scheme",
        plan.scheme,
        "-configuration",
        "Debug",
        "-destination",
        f"id={simulator_udid.upper()}",
        "-derivedDataPath",
        str(derived),
        "-resultBundlePath",
        str(result),
        "CODE_SIGNING_ALLOWED=NO",
        "CODE_SIGNING_REQUIRED=NO",
        "test",
    )


def build_xcresult_summary_argv(
    boundary: MobileToolchainBoundary,
    xcrun: Path,
    *,
    result_bundle_path: Path,
) -> tuple[str, ...]:
    tool = boundary.validate_tool(MobileToolKind.XCRUN, xcrun)
    result = boundary.validate_staging_path(result_bundle_path)
    if result.suffix != ".xcresult":
        raise MobileBoundaryError("xcresulttool input must use .xcresult suffix")
    return (
        str(tool),
        "xcresulttool",
        "get",
        "test-results",
        "summary",
        "--format",
        "json",
        "--path",
        str(result),
    )


def parse_xcresult_summary(output: str) -> AppleXCTestSummary:
    payload = _bounded_json(output, field="xcresulttool summary output")
    raw_result = payload.get("result")
    if raw_result == "Passed":
        result = AppleTestResult.PASSED
    elif raw_result == "Failed":
        result = AppleTestResult.FAILED
    else:
        raise ValueError("xcresulttool summary has unsupported result state")

    def count(name: str) -> int:
        value = payload.get(name, 0)
        if not isinstance(value, int):
            raise ValueError(f"xcresulttool summary field {name} must be integer")
        return value

    expected = count("expectedFailures")
    devices = payload.get("devicesAndConfigurations", [])
    if not isinstance(devices, list) or len(devices) > 128:
        raise ValueError("xcresulttool devicesAndConfigurations is invalid or too large")
    return AppleXCTestSummary(
        result=result,
        total_test_count=count("totalTestCount"),
        passed_tests=count("passedTests"),
        failed_tests=count("failedTests"),
        skipped_tests=count("skippedTests"),
        expected_failures=expected,
    )


def render_xctest_overlay(
    *,
    pbxproj: str,
    scheme: str,
    plan: AppleXCTestPlanDefinition,
) -> dict[str, str]:
    if not isinstance(pbxproj, str) or len(pbxproj) > _MAX_TEXT or "\x00" in pbxproj:
        raise ValueError("pbxproj is invalid or too large")
    if not isinstance(scheme, str) or len(scheme) > 256_000 or "\x00" in scheme:
        raise ValueError("Xcode scheme is invalid or too large")
    if "KodepoiaIOSTests" in pbxproj or "BlueprintIdentifier=\"E30000000000000000000001\"" in scheme:
        raise ValueError("R13.11 XCTest overlay is already present")

    def replace_once(text: str, old: str, new: str, *, label: str) -> str:
        if text.count(old) != 1:
            raise ValueError(f"canonical R13.9 {label} marker drift detected")
        return text.replace(old, new, 1)

    pbx = pbxproj
    pbx = replace_once(
        pbx,
        "/* Begin PBXBuildFile section */\n",
        "/* Begin PBXBuildFile section */\n"
        "\t\tB30000000000000000000001 /* KodepoiaIOSTests.swift in Sources */ = {isa = PBXBuildFile; fileRef = A30000000000000000000001 /* KodepoiaIOSTests.swift */; };\n",
        label="PBXBuildFile",
    )
    pbx = replace_once(
        pbx,
        "/* Begin PBXFileReference section */\n",
        "/* Begin PBXContainerItemProxy section */\n"
        "\t\tA30000000000000000000004 /* PBXContainerItemProxy */ = {\n"
        "\t\t\tisa = PBXContainerItemProxy;\n"
        "\t\t\tcontainerPortal = E20000000000000000000001 /* Project object */;\n"
        "\t\t\tproxyType = 1;\n"
        "\t\t\tremoteGlobalIDString = E10000000000000000000001;\n"
        "\t\t\tremoteInfo = KodepoiaIOS;\n"
        "\t\t};\n"
        "/* End PBXContainerItemProxy section */\n\n"
        "/* Begin PBXFileReference section */\n"
        "\t\tA30000000000000000000001 /* KodepoiaIOSTests.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = KodepoiaIOSTests.swift; sourceTree = \"<group>\"; };\n"
        "\t\tA30000000000000000000002 /* Info.plist */ = {isa = PBXFileReference; lastKnownFileType = text.plist.xml; path = Info.plist; sourceTree = \"<group>\"; };\n"
        "\t\tA30000000000000000000003 /* KodepoiaIOSTests.xctest */ = {isa = PBXFileReference; explicitFileType = wrapper.cfbundle; includeInIndex = 0; path = KodepoiaIOSTests.xctest; sourceTree = BUILT_PRODUCTS_DIR; };\n",
        label="PBXFileReference",
    )
    pbx = replace_once(
        pbx,
        "/* End PBXFrameworksBuildPhase section */",
        "\t\tC30000000000000000000001 /* Frameworks */ = {\n"
        "\t\t\tisa = PBXFrameworksBuildPhase;\n"
        "\t\t\tbuildActionMask = 2147483647;\n"
        "\t\t\tfiles = (\n\t\t\t);\n"
        "\t\t\trunOnlyForDeploymentPostprocessing = 0;\n"
        "\t\t};\n"
        "/* End PBXFrameworksBuildPhase section */",
        label="PBXFrameworksBuildPhase",
    )
    pbx = replace_once(
        pbx,
        "\t\t\t\tD10000000000000000000002 /* KodepoiaIOS */,\n\t\t\t\tD10000000000000000000003 /* Products */,",
        "\t\t\t\tD10000000000000000000002 /* KodepoiaIOS */,\n"
        "\t\t\t\tD30000000000000000000001 /* KodepoiaIOSTests */,\n"
        "\t\t\t\tD10000000000000000000003 /* Products */,",
        label="root group",
    )
    pbx = replace_once(
        pbx,
        "\t\t\t\tA10000000000000000000007 /* KodepoiaIOS.app */,",
        "\t\t\t\tA10000000000000000000007 /* KodepoiaIOS.app */,\n"
        "\t\t\t\tA30000000000000000000003 /* KodepoiaIOSTests.xctest */,",
        label="products group",
    )
    pbx = replace_once(
        pbx,
        "/* End PBXGroup section */",
        "\t\tD30000000000000000000001 /* KodepoiaIOSTests */ = {\n"
        "\t\t\tisa = PBXGroup;\n"
        "\t\t\tchildren = (\n"
        "\t\t\t\tA30000000000000000000001 /* KodepoiaIOSTests.swift */,\n"
        "\t\t\t\tA30000000000000000000002 /* Info.plist */,\n"
        "\t\t\t);\n"
        "\t\t\tpath = KodepoiaIOSTests;\n"
        "\t\t\tsourceTree = \"<group>\";\n"
        "\t\t};\n"
        "/* End PBXGroup section */",
        label="PBXGroup",
    )
    pbx = replace_once(
        pbx,
        "/* End PBXNativeTarget section */",
        "\t\tE30000000000000000000001 /* KodepoiaIOSTests */ = {\n"
        "\t\t\tisa = PBXNativeTarget;\n"
        "\t\t\tbuildConfigurationList = E30000000000000000000002 /* Build configuration list for PBXNativeTarget \"KodepoiaIOSTests\" */;\n"
        "\t\t\tbuildPhases = (\n"
        "\t\t\t\tF30000000000000000000001 /* Sources */,\n"
        "\t\t\t\tC30000000000000000000001 /* Frameworks */,\n"
        "\t\t\t\tF30000000000000000000002 /* Resources */,\n"
        "\t\t\t);\n"
        "\t\t\tbuildRules = (\n\t\t\t);\n"
        "\t\t\tdependencies = (\n"
        "\t\t\t\tA30000000000000000000005 /* PBXTargetDependency */,\n"
        "\t\t\t);\n"
        "\t\t\tname = KodepoiaIOSTests;\n"
        "\t\t\tproductName = KodepoiaIOSTests;\n"
        "\t\t\tproductReference = A30000000000000000000003 /* KodepoiaIOSTests.xctest */;\n"
        "\t\t\tproductType = \"com.apple.product-type.bundle.unit-test\";\n"
        "\t\t};\n"
        "/* End PBXNativeTarget section */",
        label="PBXNativeTarget",
    )
    pbx = replace_once(
        pbx,
        "\t\t\t\t\tE10000000000000000000001 = {\n\t\t\t\t\t\tCreatedOnToolsVersion = 26.0;\n\t\t\t\t\t};",
        "\t\t\t\t\tE10000000000000000000001 = {\n\t\t\t\t\t\tCreatedOnToolsVersion = 26.0;\n\t\t\t\t\t};\n"
        "\t\t\t\t\tE30000000000000000000001 = {\n"
        "\t\t\t\t\t\tCreatedOnToolsVersion = 26.0;\n"
        "\t\t\t\t\t\tTestTargetID = E10000000000000000000001;\n"
        "\t\t\t\t\t};",
        label="TargetAttributes",
    )
    pbx = replace_once(
        pbx,
        "\t\t\t\tE10000000000000000000001 /* KodepoiaIOS */,\n\t\t\t);",
        "\t\t\t\tE10000000000000000000001 /* KodepoiaIOS */,\n"
        "\t\t\t\tE30000000000000000000001 /* KodepoiaIOSTests */,\n"
        "\t\t\t);",
        label="project targets",
    )
    pbx = replace_once(
        pbx,
        "/* End PBXResourcesBuildPhase section */",
        "\t\tF30000000000000000000002 /* Resources */ = {\n"
        "\t\t\tisa = PBXResourcesBuildPhase;\n"
        "\t\t\tbuildActionMask = 2147483647;\n"
        "\t\t\tfiles = (\n\t\t\t);\n"
        "\t\t\trunOnlyForDeploymentPostprocessing = 0;\n"
        "\t\t};\n"
        "/* End PBXResourcesBuildPhase section */",
        label="PBXResourcesBuildPhase",
    )
    pbx = replace_once(
        pbx,
        "/* End PBXSourcesBuildPhase section */",
        "\t\tF30000000000000000000001 /* Sources */ = {\n"
        "\t\t\tisa = PBXSourcesBuildPhase;\n"
        "\t\t\tbuildActionMask = 2147483647;\n"
        "\t\t\tfiles = (\n"
        "\t\t\t\tB30000000000000000000001 /* KodepoiaIOSTests.swift in Sources */,\n"
        "\t\t\t);\n"
        "\t\t\trunOnlyForDeploymentPostprocessing = 0;\n"
        "\t\t};\n"
        "/* End PBXSourcesBuildPhase section */\n\n"
        "/* Begin PBXTargetDependency section */\n"
        "\t\tA30000000000000000000005 /* PBXTargetDependency */ = {\n"
        "\t\t\tisa = PBXTargetDependency;\n"
        "\t\t\ttarget = E10000000000000000000001 /* KodepoiaIOS */;\n"
        "\t\t\ttargetProxy = A30000000000000000000004 /* PBXContainerItemProxy */;\n"
        "\t\t};\n"
        "/* End PBXTargetDependency section */",
        label="PBXSourcesBuildPhase",
    )
    pbx = replace_once(
        pbx,
        "\t\t\t\tCURRENT_PROJECT_VERSION = 1;\n\t\t\t\tGENERATE_INFOPLIST_FILE = NO;",
        "\t\t\t\tCURRENT_PROJECT_VERSION = 1;\n\t\t\t\tENABLE_TESTABILITY = YES;\n\t\t\t\tGENERATE_INFOPLIST_FILE = NO;",
        label="app Debug testability",
    )
    test_config = f'''\t\t030000000000000000000001 /* Debug */ = {{
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {{
\t\t\t\tALWAYS_EMBED_SWIFT_STANDARD_LIBRARIES = YES;
\t\t\t\tBUNDLE_LOADER = "$(TEST_HOST)";
\t\t\t\tGENERATE_INFOPLIST_FILE = NO;
\t\t\t\tINFOPLIST_FILE = KodepoiaIOSTests/Info.plist;
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = {plan.minimum_os_version};
\t\t\t\tLD_RUNPATH_SEARCH_PATHS = ("$(inherited)", "@executable_path/Frameworks", "@loader_path/Frameworks");
\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = "com.kodepoia.acceptance.tests";
\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";
\t\t\t\tSDKROOT = iphoneos;
\t\t\t\tSUPPORTED_PLATFORMS = "iphoneos iphonesimulator";
\t\t\t\tSWIFT_VERSION = 5.0;
\t\t\t\tTARGETED_DEVICE_FAMILY = "1,2";
\t\t\t\tTEST_HOST = "$(BUILT_PRODUCTS_DIR)/KodepoiaIOS.app/KodepoiaIOS";
\t\t\t}};
\t\t\tname = Debug;
\t\t}};
\t\t030000000000000000000002 /* Release */ = {{
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {{
\t\t\t\tALWAYS_EMBED_SWIFT_STANDARD_LIBRARIES = YES;
\t\t\t\tBUNDLE_LOADER = "$(TEST_HOST)";
\t\t\t\tGENERATE_INFOPLIST_FILE = NO;
\t\t\t\tINFOPLIST_FILE = KodepoiaIOSTests/Info.plist;
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = {plan.minimum_os_version};
\t\t\t\tLD_RUNPATH_SEARCH_PATHS = ("$(inherited)", "@executable_path/Frameworks", "@loader_path/Frameworks");
\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = "com.kodepoia.acceptance.tests";
\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";
\t\t\t\tSDKROOT = iphoneos;
\t\t\t\tSUPPORTED_PLATFORMS = "iphoneos iphonesimulator";
\t\t\t\tSWIFT_VERSION = 5.0;
\t\t\t\tTARGETED_DEVICE_FAMILY = "1,2";
\t\t\t\tTEST_HOST = "$(BUILT_PRODUCTS_DIR)/KodepoiaIOS.app/KodepoiaIOS";
\t\t\t}};
\t\t\tname = Release;
\t\t}};
'''
    pbx = replace_once(
        pbx,
        "/* Begin XCBuildConfiguration section */\n",
        "/* Begin XCBuildConfiguration section */\n" + test_config,
        label="XCBuildConfiguration",
    )
    pbx = replace_once(
        pbx,
        "/* End XCConfigurationList section */",
        "\t\tE30000000000000000000002 /* Build configuration list for PBXNativeTarget \"KodepoiaIOSTests\" */ = {\n"
        "\t\t\tisa = XCConfigurationList;\n"
        "\t\t\tbuildConfigurations = (\n"
        "\t\t\t\t030000000000000000000001 /* Debug */,\n"
        "\t\t\t\t030000000000000000000002 /* Release */,\n"
        "\t\t\t);\n"
        "\t\t\tdefaultConfigurationIsVisible = 0;\n"
        "\t\t\tdefaultConfigurationName = Release;\n"
        "\t\t};\n"
        "/* End XCConfigurationList section */",
        label="XCConfigurationList",
    )

    scheme_text = replace_once(
        scheme,
        "    </BuildActionEntries>",
        "      <BuildActionEntry buildForTesting=\"YES\" buildForRunning=\"NO\" buildForProfiling=\"NO\" buildForArchiving=\"NO\" buildForAnalyzing=\"NO\">\n"
        "        <BuildableReference BuildableIdentifier=\"primary\" BlueprintIdentifier=\"E30000000000000000000001\" BuildableName=\"KodepoiaIOSTests.xctest\" BlueprintName=\"KodepoiaIOSTests\" ReferencedContainer=\"container:KodepoiaIOS.xcodeproj\"/>\n"
        "      </BuildActionEntry>\n"
        "    </BuildActionEntries>",
        label="scheme BuildAction",
    )
    scheme_text = replace_once(
        scheme_text,
        "  <TestAction buildConfiguration=\"Debug\" selectedDebuggerIdentifier=\"Xcode.DebuggerFoundation.Debugger.LLDB\" selectedLauncherIdentifier=\"Xcode.DebuggerFoundation.Launcher.LLDB\" shouldUseLaunchSchemeArgsEnv=\"YES\"/>",
        "  <TestAction buildConfiguration=\"Debug\" selectedDebuggerIdentifier=\"Xcode.DebuggerFoundation.Debugger.LLDB\" selectedLauncherIdentifier=\"Xcode.DebuggerFoundation.Launcher.LLDB\" shouldUseLaunchSchemeArgsEnv=\"YES\">\n"
        "    <Testables>\n"
        "      <TestableReference skipped=\"NO\" parallelizable=\"NO\">\n"
        "        <BuildableReference BuildableIdentifier=\"primary\" BlueprintIdentifier=\"E30000000000000000000001\" BuildableName=\"KodepoiaIOSTests.xctest\" BlueprintName=\"KodepoiaIOSTests\" ReferencedContainer=\"container:KodepoiaIOS.xcodeproj\"/>\n"
        "      </TestableReference>\n"
        "    </Testables>\n"
        "  </TestAction>",
        label="scheme TestAction",
    )

    test_source = f'''import XCTest
@testable import KodepoiaIOS

final class KodepoiaR13_11Tests: XCTestCase {{
    func testCanonicalSharedAppModelBinding() {{
        XCTAssertEqual(KodepoiaAppModelContract.logicalModelSHA256, "{plan.app_model_sha256}")
        XCTAssertFalse(KodepoiaAppModelContract.routePaths.isEmpty)
    }}

    func testSimulatorEvidenceScopeCannotImplyPhysicalDevice() {{
        let evidenceScope = "SIMULATOR"
        XCTAssertNotEqual(evidenceScope, "PHYSICAL_DEVICE")
        XCTAssertEqual("{plan.workspace_manifest_sha256}".count, 64)
    }}
}}
'''
    test_plist = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleExecutable</key>
  <string>$(EXECUTABLE_NAME)</string>
  <key>CFBundleIdentifier</key>
  <string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>$(PRODUCT_NAME)</string>
  <key>CFBundlePackageType</key>
  <string>BNDL</string>
</dict>
</plist>
'''
    return {
        "KodepoiaIOS.xcodeproj/project.pbxproj": pbx,
        "KodepoiaIOS.xcodeproj/xcshareddata/xcschemes/KodepoiaIOS.xcscheme": scheme_text,
        "KodepoiaIOSTests/KodepoiaIOSTests.swift": test_source,
        "KodepoiaIOSTests/Info.plist": test_plist,
    }
