from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ANDROID_APPLICATION_ID_RE = re.compile(
    r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$"
)
_APPLE_BUNDLE_ID_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9-]*(?:\.[A-Za-z0-9][A-Za-z0-9-]*)+$"
)
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}$")
_LOCALE_RE = re.compile(r"^[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*$")


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable identifier")
    return value


def _bounded_text(value: str, *, field: str, maximum: int = 512) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or "\x00" in value
    ):
        raise ValueError(f"{field} must be non-empty, bounded text")
    return value


def _sha256(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be lowercase SHA-256")
    return value


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        text = json.dumps(
            dict(payload),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("mobile canonical payload is not serializable") from exc
    return text.encode("utf-8")


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


class MobilePlatform(StrEnum):
    ANDROID = "android"
    IOS = "ios"
    IPADOS = "ipados"


class MobileHostOS(StrEnum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"


class MobileArchitecture(StrEnum):
    ARM64 = "arm64"
    X86_64 = "x86_64"


class MobileFormFactor(StrEnum):
    PHONE = "phone"
    TABLET = "tablet"


class MobileSourceKind(StrEnum):
    NATIVE = "native"
    GODOT_EXPORT = "godot_export"


class MobilePackageKind(StrEnum):
    APK = "apk"
    AAB = "aab"
    APP = "app"
    XCARCHIVE = "xcarchive"
    IPA = "ipa"


class MobileToolKind(StrEnum):
    JAVA = "java"
    GRADLE = "gradle"
    ADB = "adb"
    SDKMANAGER = "sdkmanager"
    APKSIGNER = "apksigner"
    KEYTOOL = "keytool"
    BUNDLETOOL = "bundletool"
    XCODEBUILD = "xcodebuild"
    XCRUN = "xcrun"


class MobileCapabilityState(StrEnum):
    NOT_PROBED = "NOT_PROBED"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class StoreReadinessState(StrEnum):
    NOT_EVALUATED = "NOT_EVALUATED"
    LOCAL_ONLY = "LOCAL_ONLY"
    TEST_READY = "TEST_READY"
    STORE_READY = "STORE_READY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class MobileTargetProfile:
    profile_id: str
    platform: MobilePlatform
    form_factors: tuple[MobileFormFactor, ...]
    source_kind: MobileSourceKind
    architecture: MobileArchitecture = MobileArchitecture.ARM64
    minimum_platform_version: str = "1.0"
    target_api_level: int | None = None
    package_kinds: tuple[MobilePackageKind, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.profile_id, field="profile_id")
        if _VERSION_RE.fullmatch(self.minimum_platform_version) is None:
            raise ValueError("minimum_platform_version must be a bounded numeric version")

        factors = tuple(sorted(set(self.form_factors), key=lambda item: item.value))
        if not factors:
            raise ValueError("form_factors must contain at least one item")
        object.__setattr__(self, "form_factors", factors)

        kinds = tuple(sorted(set(self.package_kinds), key=lambda item: item.value))
        if self.platform is MobilePlatform.ANDROID:
            if self.target_api_level is None or not 1 <= self.target_api_level <= 1000:
                raise ValueError("Android target requires a bounded target_api_level")
            if not kinds:
                kinds = (MobilePackageKind.APK, MobilePackageKind.AAB)
            if any(item not in {MobilePackageKind.APK, MobilePackageKind.AAB} for item in kinds):
                raise ValueError("Android targets only support APK/AAB package kinds")
        else:
            if self.target_api_level is not None:
                raise ValueError("Apple targets do not use Android target_api_level")
            if not kinds:
                kinds = (MobilePackageKind.APP, MobilePackageKind.XCARCHIVE)
            if any(
                item not in {
                    MobilePackageKind.APP,
                    MobilePackageKind.XCARCHIVE,
                    MobilePackageKind.IPA,
                }
                for item in kinds
            ):
                raise ValueError("Apple targets only support app/xcarchive/ipa package kinds")
        object.__setattr__(self, "package_kinds", kinds)

    def canonical(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "platform": self.platform.value,
            "form_factors": [item.value for item in self.form_factors],
            "source_kind": self.source_kind.value,
            "architecture": self.architecture.value,
            "minimum_platform_version": self.minimum_platform_version,
            "target_api_level": self.target_api_level,
            "package_kinds": [item.value for item in self.package_kinds],
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class MobileToolchainIdentity:
    tool_kind: MobileToolKind
    executable_name: str
    executable_sha256: str
    version: str
    host_os: MobileHostOS
    architecture: MobileArchitecture
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _bounded_text(self.executable_name, field="executable_name", maximum=128)
        _sha256(self.executable_sha256, field="executable_sha256")
        _bounded_text(self.version, field="version", maximum=128)
        capabilities = tuple(sorted(set(self.capabilities)))
        if len(capabilities) > 64:
            raise ValueError("capabilities must contain at most 64 entries")
        for capability in capabilities:
            _stable_id(capability, field="capability")
        object.__setattr__(self, "capabilities", capabilities)

    def canonical(self) -> dict[str, Any]:
        return {
            "tool_kind": self.tool_kind.value,
            "executable_name": self.executable_name,
            "executable_sha256": self.executable_sha256,
            "version": self.version,
            "host_os": self.host_os.value,
            "architecture": self.architecture.value,
            "capabilities": list(self.capabilities),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class MobileCapabilityReport:
    adapter_id: str
    platform: MobilePlatform
    state: MobileCapabilityState
    toolchains: tuple[MobileToolchainIdentity, ...] = ()
    capabilities: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.adapter_id, field="adapter_id")
        tools = tuple(sorted(self.toolchains, key=lambda item: item.digest()))
        capabilities = tuple(sorted(set(self.capabilities)))
        blockers = tuple(sorted(set(self.blockers)))
        if len(tools) > 32 or len(capabilities) > 64 or len(blockers) > 64:
            raise ValueError("capability report entries are not bounded")
        for item in capabilities:
            _stable_id(item, field="capability")
        for item in blockers:
            _stable_id(item, field="blocker")

        if self.state is MobileCapabilityState.AVAILABLE:
            if not tools:
                raise ValueError("AVAILABLE requires at least one probed toolchain identity")
            if blockers:
                raise ValueError("AVAILABLE cannot contain blockers")
        elif self.state is MobileCapabilityState.NOT_PROBED:
            if tools or capabilities or blockers:
                raise ValueError("NOT_PROBED cannot contain probed evidence")
        elif self.state in {
            MobileCapabilityState.UNAVAILABLE,
            MobileCapabilityState.UNSUPPORTED,
            MobileCapabilityState.BLOCKED,
            MobileCapabilityState.FAILED,
        } and not blockers:
            raise ValueError(f"{self.state.value} requires at least one blocker")

        object.__setattr__(self, "toolchains", tools)
        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(self, "blockers", blockers)

    def canonical(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "platform": self.platform.value,
            "state": self.state.value,
            "toolchains": [item.canonical() for item in self.toolchains],
            "capabilities": list(self.capabilities),
            "blockers": list(self.blockers),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class MobileApplicationIdentity:
    identity_id: str
    platform: MobilePlatform
    package_identifier: str

    def __post_init__(self) -> None:
        _stable_id(self.identity_id, field="identity_id")
        if self.platform is MobilePlatform.ANDROID:
            if _ANDROID_APPLICATION_ID_RE.fullmatch(self.package_identifier) is None:
                raise ValueError("invalid Android application id")
        elif _APPLE_BUNDLE_ID_RE.fullmatch(self.package_identifier) is None:
            raise ValueError("invalid Apple bundle identifier")

    def canonical(self) -> dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "platform": self.platform.value,
            "package_identifier": self.package_identifier,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class MobileArtifactDescriptor:
    artifact_id: str
    platform: MobilePlatform
    package_kind: MobilePackageKind
    sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        _stable_id(self.artifact_id, field="artifact_id")
        _sha256(self.sha256, field="sha256")
        if not isinstance(self.size_bytes, int) or not 0 <= self.size_bytes <= 20 * 1024**3:
            raise ValueError("size_bytes is outside the bounded artifact range")
        if self.platform is MobilePlatform.ANDROID and self.package_kind not in {
            MobilePackageKind.APK,
            MobilePackageKind.AAB,
        }:
            raise ValueError("Android artifact kind mismatch")
        if self.platform is not MobilePlatform.ANDROID and self.package_kind not in {
            MobilePackageKind.APP,
            MobilePackageKind.XCARCHIVE,
            MobilePackageKind.IPA,
        }:
            raise ValueError("Apple artifact kind mismatch")

    def canonical(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "platform": self.platform.value,
            "package_kind": self.package_kind.value,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class DeviceIdentity:
    device_id: str
    provider_id: str
    platform: MobilePlatform
    architecture: MobileArchitecture
    os_version: str
    model: str
    virtual: bool
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.device_id, field="device_id")
        _stable_id(self.provider_id, field="provider_id")
        if _VERSION_RE.fullmatch(self.os_version) is None:
            raise ValueError("os_version must be a numeric version")
        _bounded_text(self.model, field="model", maximum=128)
        capabilities = tuple(sorted(set(self.capabilities)))
        if len(capabilities) > 64:
            raise ValueError("device capabilities are not bounded")
        for item in capabilities:
            _stable_id(item, field="capability")
        object.__setattr__(self, "capabilities", capabilities)

    def canonical(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "provider_id": self.provider_id,
            "platform": self.platform.value,
            "architecture": self.architecture.value,
            "os_version": self.os_version,
            "model": self.model,
            "virtual": self.virtual,
            "capabilities": list(self.capabilities),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class DeviceTestMatrix:
    matrix_id: str
    platform: MobilePlatform
    device_digests: tuple[str, ...]
    locales: tuple[str, ...] = ("en-US",)
    orientations: tuple[str, ...] = ("portrait",)

    def __post_init__(self) -> None:
        _stable_id(self.matrix_id, field="matrix_id")
        devices = tuple(sorted(set(self.device_digests)))
        if not devices or len(devices) > 64:
            raise ValueError("device_digests must contain 1..64 entries")
        for item in devices:
            _sha256(item, field="device_digest")
        locales = tuple(sorted(set(self.locales)))
        if not locales or len(locales) > 32:
            raise ValueError("locales must contain 1..32 entries")
        for locale in locales:
            if _LOCALE_RE.fullmatch(locale) is None:
                raise ValueError("invalid locale")
        orientations = tuple(sorted(set(self.orientations)))
        if not orientations or not set(orientations) <= {"portrait", "landscape"}:
            raise ValueError("orientations must be portrait/landscape")
        object.__setattr__(self, "device_digests", devices)
        object.__setattr__(self, "locales", locales)
        object.__setattr__(self, "orientations", orientations)

    def canonical(self) -> dict[str, Any]:
        return {
            "matrix_id": self.matrix_id,
            "platform": self.platform.value,
            "device_digests": list(self.device_digests),
            "locales": list(self.locales),
            "orientations": list(self.orientations),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class StoreReleaseStatus:
    release_id: str
    platform: MobilePlatform
    readiness: StoreReadinessState
    artifact_digest: str | None = None
    compliance_snapshot_digest: str | None = None
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.release_id, field="release_id")
        if self.artifact_digest is not None:
            _sha256(self.artifact_digest, field="artifact_digest")
        if self.compliance_snapshot_digest is not None:
            _sha256(self.compliance_snapshot_digest, field="compliance_snapshot_digest")
        blockers = tuple(sorted(set(self.blockers)))
        for item in blockers:
            _stable_id(item, field="blocker")
        if self.readiness is StoreReadinessState.STORE_READY:
            if blockers or self.artifact_digest is None or self.compliance_snapshot_digest is None:
                raise ValueError("STORE_READY requires artifact/compliance evidence and no blockers")
        if self.readiness is StoreReadinessState.BLOCKED and not blockers:
            raise ValueError("BLOCKED requires at least one blocker")
        object.__setattr__(self, "blockers", blockers)

    def canonical(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "platform": self.platform.value,
            "readiness": self.readiness.value,
            "artifact_digest": self.artifact_digest,
            "compliance_snapshot_digest": self.compliance_snapshot_digest,
            "blockers": list(self.blockers),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())
