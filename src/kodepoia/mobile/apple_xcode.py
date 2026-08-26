from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Any, Mapping

from .contracts import (
    MobileArchitecture,
    MobileCapabilityState,
    MobileHostOS,
    MobileToolKind,
    MobileToolchainIdentity,
    canonical_sha256,
)

_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}$")
_BUILD_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_RUNTIME_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,255}$")
_MAX_TEXT = 1_048_576
_MAX_RUNTIMES = 128
_MAX_DEVICE_GROUPS = 128
_MAX_DEVICES = 2048


class AppleXcodeChannel(StrEnum):
    STABLE = "STABLE"
    BETA = "BETA"
    UNVERIFIED = "UNVERIFIED"


class AppleToolchainReadiness(StrEnum):
    DEVELOPMENT_READY = "DEVELOPMENT_READY"
    PRODUCTION_UPLOAD_TOOLCHAIN_READY = "PRODUCTION_UPLOAD_TOOLCHAIN_READY"
    TESTFLIGHT_BETA_TOOLCHAIN_READY = "TESTFLIGHT_BETA_TOOLCHAIN_READY"
    BLOCKED = "BLOCKED"


class AppleExecutorKind(StrEnum):
    GITHUB_HOSTED = "GITHUB_HOSTED"
    LOCAL_GOVERNED = "LOCAL_GOVERNED"
    REMOTE_GOVERNED = "REMOTE_GOVERNED"


class AppleSDKKind(StrEnum):
    IPHONEOS = "iphoneos"
    IPHONESIMULATOR = "iphonesimulator"


class ApplePolicyFreshness(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"


def _parse_date(value: str, *, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable identifier")
    return value


def _version(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _VERSION_RE.fullmatch(value.strip()) is None:
        raise ValueError(f"{field} must be a bounded numeric version")
    return value.strip()


def _major(value: str) -> int:
    return int(value.split(".", 1)[0])


def _bounded_output(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > _MAX_TEXT or "\x00" in value:
        raise ValueError(f"{field} is empty, malformed or too large")
    return value


@dataclass(frozen=True, slots=True)
class AppleXcodePolicySnapshot:
    snapshot_id: str
    retrieved_on: str
    expires_on: str
    production_effective_on: str
    production_min_xcode_major: int
    production_min_sdk_major: int
    stable_xcode_major: int
    testflight_beta_xcode_major: int
    sources: tuple[str, ...]

    def __post_init__(self) -> None:
        _stable_id(self.snapshot_id, field="snapshot_id")
        retrieved = _parse_date(self.retrieved_on, field="retrieved_on")
        expires = _parse_date(self.expires_on, field="expires_on")
        effective = _parse_date(self.production_effective_on, field="production_effective_on")
        if expires < retrieved or effective > expires:
            raise ValueError("Apple policy snapshot dates are inconsistent")
        for value in (
            self.production_min_xcode_major,
            self.production_min_sdk_major,
            self.stable_xcode_major,
            self.testflight_beta_xcode_major,
        ):
            if not isinstance(value, int) or not 1 <= value <= 999:
                raise ValueError("Apple policy major versions must be bounded positive integers")
        if self.stable_xcode_major < self.production_min_xcode_major:
            raise ValueError("stable Xcode major cannot be below the production minimum")
        if self.testflight_beta_xcode_major <= self.stable_xcode_major:
            raise ValueError("TestFlight beta Xcode major must be newer than stable")
        clean = tuple(sorted(set(self.sources)))
        if not clean or len(clean) > 16:
            raise ValueError("Apple policy sources must be non-empty and bounded")
        for source in clean:
            if not isinstance(source, str) or not source.startswith("https://") or len(source) > 512:
                raise ValueError("Apple policy sources must be bounded HTTPS URLs")
        object.__setattr__(self, "sources", clean)

    def freshness_on(self, evaluated_on: str) -> ApplePolicyFreshness:
        current = _parse_date(evaluated_on, field="evaluated_on")
        return (
            ApplePolicyFreshness.CURRENT
            if current <= _parse_date(self.expires_on, field="expires_on")
            else ApplePolicyFreshness.STALE
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "retrieved_on": self.retrieved_on,
            "expires_on": self.expires_on,
            "production_effective_on": self.production_effective_on,
            "production_min_xcode_major": self.production_min_xcode_major,
            "production_min_sdk_major": self.production_min_sdk_major,
            "stable_xcode_major": self.stable_xcode_major,
            "testflight_beta_xcode_major": self.testflight_beta_xcode_major,
            "sources": list(self.sources),
        }

    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


def current_apple_xcode_policy_snapshot() -> AppleXcodePolicySnapshot:
    return AppleXcodePolicySnapshot(
        snapshot_id="apple-xcode-policy-2026-08-26",
        retrieved_on="2026-08-26",
        expires_on="2026-09-30",
        production_effective_on="2026-04-28",
        production_min_xcode_major=26,
        production_min_sdk_major=26,
        stable_xcode_major=26,
        testflight_beta_xcode_major=27,
        sources=(
            "https://developer.apple.com/news/upcoming-requirements/",
            "https://developer.apple.com/help/app-store-connect/release-notes/",
        ),
    )


@dataclass(frozen=True, slots=True)
class AppleSDKIdentity:
    kind: AppleSDKKind
    version: str

    def __post_init__(self) -> None:
        _version(self.version, field="sdk version")

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind.value, "version": self.version}


@dataclass(frozen=True, slots=True)
class AppleSimulatorRuntime:
    identifier: str
    name: str
    version: str
    available: bool

    def __post_init__(self) -> None:
        if _RUNTIME_ID_RE.fullmatch(self.identifier) is None:
            raise ValueError("simulator runtime identifier is invalid")
        if not isinstance(self.name, str) or not self.name.strip() or len(self.name) > 128:
            raise ValueError("simulator runtime name is invalid")
        _version(self.version, field="simulator runtime version")
        if not isinstance(self.available, bool):
            raise ValueError("simulator runtime availability must be boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "identifier": self.identifier,
            "name": self.name,
            "version": self.version,
            "available": self.available,
        }


@dataclass(frozen=True, slots=True)
class AppleExecutorDescriptor:
    kind: AppleExecutorKind
    provider: str
    host_os_version: str
    architecture: MobileArchitecture
    timeout_seconds: int = 900
    cancellation_supported: bool = True
    interactive: bool = False
    network_allowed: bool = False
    staging_scope: str = "runner-temp"
    output_scope: str = "runner-temp"

    def __post_init__(self) -> None:
        _stable_id(self.provider, field="provider")
        _version(self.host_os_version, field="host_os_version")
        if not 1 <= self.timeout_seconds <= 3600:
            raise ValueError("executor timeout must be between 1 and 3600 seconds")
        if self.interactive:
            raise ValueError("R13.8 executor contract must be non-interactive")
        for field_name, value in (
            ("staging_scope", self.staging_scope),
            ("output_scope", self.output_scope),
        ):
            _stable_id(value, field=field_name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "provider": self.provider,
            "host_os_version": self.host_os_version,
            "architecture": self.architecture.value,
            "timeout_seconds": self.timeout_seconds,
            "cancellation_supported": self.cancellation_supported,
            "interactive": self.interactive,
            "network_allowed": self.network_allowed,
            "staging_scope": self.staging_scope,
            "output_scope": self.output_scope,
        }


@dataclass(frozen=True, slots=True)
class AppleXcodeCapabilityEvidence:
    schema_version: int
    source_sha: str
    probed_on: str
    policy: AppleXcodePolicySnapshot
    policy_freshness: ApplePolicyFreshness
    xcode_version: str
    xcode_build: str
    channel: AppleXcodeChannel
    xcodebuild_identity: MobileToolchainIdentity
    xcrun_identity: MobileToolchainIdentity
    sdks: tuple[AppleSDKIdentity, ...]
    simulator_runtimes: tuple[AppleSimulatorRuntime, ...]
    simulator_device_count: int
    executor: AppleExecutorDescriptor
    capability_state: MobileCapabilityState
    readiness: AppleToolchainReadiness
    production_upload_toolchain_capable: bool
    testflight_beta_toolchain_capable: bool
    physical_device_capability_proven: bool
    blockers: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported Apple Xcode evidence schema version")
        if _SOURCE_SHA_RE.fullmatch(self.source_sha) is None:
            raise ValueError("source_sha must be an exact lowercase 40-hex Git SHA")
        _parse_date(self.probed_on, field="probed_on")
        _version(self.xcode_version, field="xcode_version")
        if _BUILD_RE.fullmatch(self.xcode_build) is None:
            raise ValueError("xcode_build is invalid")
        if self.xcodebuild_identity.tool_kind is not MobileToolKind.XCODEBUILD:
            raise ValueError("xcodebuild identity kind mismatch")
        if self.xcrun_identity.tool_kind is not MobileToolKind.XCRUN:
            raise ValueError("xcrun identity kind mismatch")
        for identity in (self.xcodebuild_identity, self.xcrun_identity):
            if identity.host_os is not MobileHostOS.MACOS:
                raise ValueError("Apple tool identity must be macOS-scoped")
            if identity.architecture is not self.executor.architecture:
                raise ValueError("Apple tool architecture substitution detected")
        ordered_sdks = tuple(sorted(self.sdks, key=lambda item: item.kind.value))
        if {item.kind for item in ordered_sdks} != {
            AppleSDKKind.IPHONEOS,
            AppleSDKKind.IPHONESIMULATOR,
        }:
            raise ValueError("R13.8 evidence requires iphoneos and iphonesimulator SDK identities")
        object.__setattr__(self, "sdks", ordered_sdks)
        ordered_runtimes = tuple(
            sorted(self.simulator_runtimes, key=lambda item: (item.version, item.identifier))
        )
        if len(ordered_runtimes) > _MAX_RUNTIMES:
            raise ValueError("too many simulator runtimes")
        object.__setattr__(self, "simulator_runtimes", ordered_runtimes)
        if not 0 <= self.simulator_device_count <= _MAX_DEVICES:
            raise ValueError("simulator_device_count is out of bounds")
        if self.physical_device_capability_proven:
            raise ValueError("R13.8 hosted capability probe must not claim physical-device evidence")
        clean_blockers = tuple(sorted(set(self.blockers)))
        for blocker in clean_blockers:
            _stable_id(blocker, field="blocker")
        object.__setattr__(self, "blockers", clean_blockers)
        if self.capability_state is MobileCapabilityState.AVAILABLE and clean_blockers:
            raise ValueError("AVAILABLE Apple capability evidence cannot contain blockers")
        if self.production_upload_toolchain_capable and self.channel is not AppleXcodeChannel.STABLE:
            raise ValueError("non-stable Xcode channel cannot claim production upload toolchain capability")
        if self.production_upload_toolchain_capable and self.policy_freshness is not ApplePolicyFreshness.CURRENT:
            raise ValueError("stale policy cannot claim production upload toolchain capability")
        if self.testflight_beta_toolchain_capable and self.channel is not AppleXcodeChannel.BETA:
            raise ValueError("TestFlight beta capability requires beta channel")
        if self.readiness is AppleToolchainReadiness.PRODUCTION_UPLOAD_TOOLCHAIN_READY:
            if not self.production_upload_toolchain_capable:
                raise ValueError("production readiness requires production toolchain capability")
        if self.readiness is AppleToolchainReadiness.TESTFLIGHT_BETA_TOOLCHAIN_READY:
            if not self.testflight_beta_toolchain_capable:
                raise ValueError("TestFlight readiness requires beta toolchain capability")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_sha": self.source_sha,
            "probed_on": self.probed_on,
            "policy": self.policy.to_dict(),
            "policy_sha256": self.policy.digest(),
            "policy_freshness": self.policy_freshness.value,
            "xcode_version": self.xcode_version,
            "xcode_build": self.xcode_build,
            "channel": self.channel.value,
            "tools": {
                "xcodebuild": self.xcodebuild_identity.canonical(),
                "xcrun": self.xcrun_identity.canonical(),
            },
            "sdks": [item.to_dict() for item in self.sdks],
            "simulator_runtimes": [item.to_dict() for item in self.simulator_runtimes],
            "simulator_device_count": self.simulator_device_count,
            "executor": self.executor.to_dict(),
            "capability_state": self.capability_state.value,
            "readiness": self.readiness.value,
            "production_upload_toolchain_capable": self.production_upload_toolchain_capable,
            "testflight_beta_toolchain_capable": self.testflight_beta_toolchain_capable,
            "physical_device_capability_proven": self.physical_device_capability_proven,
            "blockers": list(self.blockers),
        }

    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


def parse_xcodebuild_version(output: str) -> tuple[str, str]:
    text = _bounded_output(output, field="xcodebuild output")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) != 2 or not lines[0].startswith("Xcode ") or not lines[1].startswith("Build version "):
        raise ValueError("unexpected xcodebuild -version output")
    version = _version(lines[0][len("Xcode ") :], field="xcode_version")
    build = lines[1][len("Build version ") :]
    if _BUILD_RE.fullmatch(build) is None:
        raise ValueError("unexpected Xcode build identifier")
    return version, build


def parse_sdk_version(output: str) -> str:
    text = _bounded_output(output, field="SDK version output").strip()
    if "\n" in text or "\r" in text:
        raise ValueError("SDK version output must contain one version")
    return _version(text, field="SDK version")


def parse_simctl_runtimes(output: str) -> tuple[AppleSimulatorRuntime, ...]:
    text = _bounded_output(output, field="simctl runtimes output")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("simctl runtimes output is invalid JSON") from exc
    if not isinstance(payload, Mapping) or set(payload) != {"runtimes"}:
        raise ValueError("simctl runtimes payload must contain only runtimes")
    values = payload["runtimes"]
    if not isinstance(values, list) or len(values) > _MAX_RUNTIMES:
        raise ValueError("simctl runtimes collection is invalid or too large")
    result: list[AppleSimulatorRuntime] = []
    for raw in values:
        if not isinstance(raw, Mapping):
            raise ValueError("simctl runtime entry must be an object")
        identifier = raw.get("identifier")
        name = raw.get("name")
        version = raw.get("version")
        if not isinstance(identifier, str) or not isinstance(name, str) or not isinstance(version, str):
            raise ValueError("simctl runtime entry is missing public identity fields")
        if ".iOS-" not in identifier and not name.startswith("iOS"):
            continue
        available_raw = raw.get("isAvailable", True)
        if not isinstance(available_raw, bool):
            raise ValueError("simctl runtime availability must be boolean")
        result.append(AppleSimulatorRuntime(identifier, name, version, available_raw))
    return tuple(sorted(result, key=lambda item: (item.version, item.identifier)))


def parse_simctl_device_count(output: str) -> int:
    text = _bounded_output(output, field="simctl devices output")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("simctl devices output is invalid JSON") from exc
    if not isinstance(payload, Mapping) or set(payload) != {"devices"}:
        raise ValueError("simctl devices payload must contain only devices")
    groups = payload["devices"]
    if not isinstance(groups, Mapping) or len(groups) > _MAX_DEVICE_GROUPS:
        raise ValueError("simctl devices collection is invalid or too large")
    count = 0
    for devices in groups.values():
        if not isinstance(devices, list):
            raise ValueError("simctl device group must be a list")
        for raw in devices:
            if not isinstance(raw, Mapping):
                raise ValueError("simctl device entry must be an object")
            available = raw.get("isAvailable", True)
            if not isinstance(available, bool):
                raise ValueError("simctl device availability must be boolean")
            if available:
                count += 1
                if count > _MAX_DEVICES:
                    raise ValueError("too many simulator devices")
    return count


def evaluate_apple_xcode_capability(
    *,
    source_sha: str,
    probed_on: str,
    policy: AppleXcodePolicySnapshot,
    xcode_version: str,
    xcode_build: str,
    xcodebuild_identity: MobileToolchainIdentity,
    xcrun_identity: MobileToolchainIdentity,
    iphoneos_sdk_version: str,
    iphonesimulator_sdk_version: str,
    simulator_runtimes: tuple[AppleSimulatorRuntime, ...],
    simulator_device_count: int,
    executor: AppleExecutorDescriptor,
) -> AppleXcodeCapabilityEvidence:
    if _SOURCE_SHA_RE.fullmatch(source_sha) is None:
        raise ValueError("source_sha must be an exact lowercase 40-hex Git SHA")
    _parse_date(probed_on, field="probed_on")
    xcode_version = _version(xcode_version, field="xcode_version")
    if _BUILD_RE.fullmatch(xcode_build) is None:
        raise ValueError("xcode_build is invalid")
    ios_sdk = _version(iphoneos_sdk_version, field="iphoneos_sdk_version")
    simulator_sdk = _version(
        iphonesimulator_sdk_version, field="iphonesimulator_sdk_version"
    )
    freshness = policy.freshness_on(probed_on)
    xcode_major = _major(xcode_version)
    sdk_major = min(_major(ios_sdk), _major(simulator_sdk))

    if xcode_major == policy.stable_xcode_major:
        channel = AppleXcodeChannel.STABLE
    elif xcode_major == policy.testflight_beta_xcode_major:
        channel = AppleXcodeChannel.BETA
    else:
        channel = AppleXcodeChannel.UNVERIFIED

    blockers: list[str] = []
    if freshness is ApplePolicyFreshness.STALE:
        blockers.append("policy_snapshot_stale")
    if channel is AppleXcodeChannel.UNVERIFIED:
        blockers.append("xcode_channel_unverified")
    if not any(item.available for item in simulator_runtimes):
        blockers.append("ios_simulator_runtime_unavailable")
    if simulator_device_count < 1:
        blockers.append("simulator_device_unavailable")

    production = (
        freshness is ApplePolicyFreshness.CURRENT
        and channel is AppleXcodeChannel.STABLE
        and xcode_major >= policy.production_min_xcode_major
        and sdk_major >= policy.production_min_sdk_major
    )
    beta = (
        freshness is ApplePolicyFreshness.CURRENT
        and channel is AppleXcodeChannel.BETA
        and xcode_major == policy.testflight_beta_xcode_major
        and sdk_major >= policy.testflight_beta_xcode_major
    )

    if blockers:
        state = MobileCapabilityState.UNSUPPORTED
        readiness = AppleToolchainReadiness.BLOCKED
        production = False
        beta = False
    elif production:
        state = MobileCapabilityState.AVAILABLE
        readiness = AppleToolchainReadiness.PRODUCTION_UPLOAD_TOOLCHAIN_READY
    elif beta:
        state = MobileCapabilityState.AVAILABLE
        readiness = AppleToolchainReadiness.TESTFLIGHT_BETA_TOOLCHAIN_READY
    else:
        state = MobileCapabilityState.AVAILABLE
        readiness = AppleToolchainReadiness.DEVELOPMENT_READY

    return AppleXcodeCapabilityEvidence(
        schema_version=1,
        source_sha=source_sha,
        probed_on=probed_on,
        policy=policy,
        policy_freshness=freshness,
        xcode_version=xcode_version,
        xcode_build=xcode_build,
        channel=channel,
        xcodebuild_identity=xcodebuild_identity,
        xcrun_identity=xcrun_identity,
        sdks=(
            AppleSDKIdentity(AppleSDKKind.IPHONEOS, ios_sdk),
            AppleSDKIdentity(AppleSDKKind.IPHONESIMULATOR, simulator_sdk),
        ),
        simulator_runtimes=simulator_runtimes,
        simulator_device_count=simulator_device_count,
        executor=executor,
        capability_state=state,
        readiness=readiness,
        production_upload_toolchain_capable=production,
        testflight_beta_toolchain_capable=beta,
        physical_device_capability_proven=False,
        blockers=tuple(blockers),
    )