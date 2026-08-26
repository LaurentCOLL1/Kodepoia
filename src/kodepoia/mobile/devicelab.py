from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from .contracts import canonical_json_bytes

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_STABLE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,127}$")
_MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._()+-]{0,127}$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}$")
_LOCALE_RE = re.compile(r"^[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*$")
_MAX_MATRIX_DEVICES = 64
_MAX_QUOTA = 1_000_000
_MAX_COST_MICROS = 10_000_000_000


class DeviceLabPlatform(StrEnum):
    ANDROID = "ANDROID"
    IOS = "IOS"


class DeviceLabProviderKind(StrEnum):
    LOCAL_ANDROID = "LOCAL_ANDROID"
    XCODE_SIMULATOR = "XCODE_SIMULATOR"
    HOSTED_CI = "HOSTED_CI"
    FIREBASE_TEST_LAB = "FIREBASE_TEST_LAB"


class DeviceLabTargetClass(StrEnum):
    VIRTUAL = "VIRTUAL"
    PHYSICAL = "PHYSICAL"


class DeviceLabOrientation(StrEnum):
    PORTRAIT = "PORTRAIT"
    LANDSCAPE = "LANDSCAPE"


class DeviceLabCapabilityState(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ACCOUNT_REQUIRED = "ACCOUNT_REQUIRED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    UNSUPPORTED = "UNSUPPORTED"


class DeviceLabResultState(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"


def _sha256(value: str, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _stable_id(value: str, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable identifier")
    return value


def _digest(payload: object) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _provider_rank(provider: DeviceLabProviderKind) -> int:
    return {
        DeviceLabProviderKind.LOCAL_ANDROID: 0,
        DeviceLabProviderKind.XCODE_SIMULATOR: 0,
        DeviceLabProviderKind.HOSTED_CI: 1,
        DeviceLabProviderKind.FIREBASE_TEST_LAB: 2,
    }[provider]


@dataclass(frozen=True, slots=True)
class DeviceLabDeviceSpec:
    model: str
    os_version: str
    locale: str
    orientation: DeviceLabOrientation
    target_class: DeviceLabTargetClass

    def __post_init__(self) -> None:
        if _MODEL_RE.fullmatch(self.model) is None:
            raise ValueError("device model is invalid or unbounded")
        if _VERSION_RE.fullmatch(self.os_version) is None:
            raise ValueError("device OS version must use bounded numeric dotted form")
        if _LOCALE_RE.fullmatch(self.locale) is None:
            raise ValueError("device locale is invalid")

    def to_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "os_version": self.os_version,
            "locale": self.locale,
            "orientation": self.orientation.value,
            "target_class": self.target_class.value,
        }

    def digest(self) -> str:
        return _digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class DeviceLabMatrixDefinition:
    matrix_id: str
    platform: DeviceLabPlatform
    artifact_sha256: str
    test_execution_id: str
    devices: tuple[DeviceLabDeviceSpec, ...]

    def __post_init__(self) -> None:
        _stable_id(self.matrix_id, "matrix_id")
        _stable_id(self.test_execution_id, "test_execution_id")
        _sha256(self.artifact_sha256, "artifact_sha256")
        devices = tuple(self.devices)
        if not devices or len(devices) > _MAX_MATRIX_DEVICES:
            raise ValueError("DeviceLab matrix requires 1..64 device configurations")
        ordered = tuple(sorted(devices, key=lambda item: canonical_json_bytes(item.to_dict())))
        if len({item.digest() for item in ordered}) != len(ordered):
            raise ValueError("DeviceLab matrix cannot contain duplicate device configurations")
        object.__setattr__(self, "devices", ordered)

    @property
    def target_classes(self) -> tuple[DeviceLabTargetClass, ...]:
        return tuple(sorted({item.target_class for item in self.devices}, key=lambda item: item.value))

    def to_dict(self) -> dict[str, object]:
        return {
            "matrix_id": self.matrix_id,
            "platform": self.platform.value,
            "artifact_sha256": self.artifact_sha256,
            "test_execution_id": self.test_execution_id,
            "devices": [item.to_dict() for item in self.devices],
        }

    def digest(self) -> str:
        return _digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class DeviceLabProviderCapability:
    provider: DeviceLabProviderKind
    platform: DeviceLabPlatform
    target_classes: tuple[DeviceLabTargetClass, ...]
    state: DeviceLabCapabilityState
    account_reference_present: bool = False
    project_scope_sha256: str | None = None
    quota_remaining: int | None = None
    estimated_cost_micros: int = 0
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        classes = tuple(sorted(set(self.target_classes), key=lambda item: item.value))
        if not classes:
            raise ValueError("provider capability requires at least one target class")
        object.__setattr__(self, "target_classes", classes)
        blockers = tuple(sorted(set(self.blockers)))
        for blocker in blockers:
            _stable_id(blocker, "blocker")
        object.__setattr__(self, "blockers", blockers)
        if self.project_scope_sha256 is not None:
            _sha256(self.project_scope_sha256, "project_scope_sha256")
        if self.quota_remaining is not None and not 0 <= self.quota_remaining <= _MAX_QUOTA:
            raise ValueError("provider quota is outside bounded range")
        if not 0 <= self.estimated_cost_micros <= _MAX_COST_MICROS:
            raise ValueError("provider estimated cost is outside bounded range")

        if self.provider is DeviceLabProviderKind.LOCAL_ANDROID:
            if self.platform is not DeviceLabPlatform.ANDROID:
                raise ValueError("local Android provider cannot certify iOS")
        elif self.provider is DeviceLabProviderKind.XCODE_SIMULATOR:
            if self.platform is not DeviceLabPlatform.IOS or classes != (DeviceLabTargetClass.VIRTUAL,):
                raise ValueError("Xcode Simulator provider is iOS virtual-only")
        elif self.provider is DeviceLabProviderKind.HOSTED_CI:
            if DeviceLabTargetClass.PHYSICAL in classes:
                raise ValueError("hosted CI capability cannot manufacture physical-device support")
        elif self.provider is DeviceLabProviderKind.FIREBASE_TEST_LAB:
            if self.platform is DeviceLabPlatform.IOS and DeviceLabTargetClass.VIRTUAL in classes:
                raise ValueError("Firebase Test Lab iOS capability is physical-device only")

        if self.state is DeviceLabCapabilityState.AVAILABLE:
            if blockers:
                raise ValueError("AVAILABLE provider capability cannot contain blockers")
            if self.provider is DeviceLabProviderKind.FIREBASE_TEST_LAB:
                if not self.account_reference_present or self.project_scope_sha256 is None:
                    raise ValueError("available Firebase capability requires account reference and project scope")
                if self.quota_remaining is not None and self.quota_remaining < 1:
                    raise ValueError("available Firebase capability cannot have exhausted quota")
        else:
            if not blockers:
                raise ValueError("unavailable provider capability requires an explicit blocker")
            if self.state is DeviceLabCapabilityState.ACCOUNT_REQUIRED and self.account_reference_present:
                raise ValueError("ACCOUNT_REQUIRED cannot claim an account reference")
            if self.state is DeviceLabCapabilityState.QUOTA_EXCEEDED and self.quota_remaining not in {0, None}:
                raise ValueError("QUOTA_EXCEEDED cannot report positive quota")

    @classmethod
    def firebase_without_account(cls, platform: DeviceLabPlatform) -> "DeviceLabProviderCapability":
        classes = (
            (DeviceLabTargetClass.PHYSICAL, DeviceLabTargetClass.VIRTUAL)
            if platform is DeviceLabPlatform.ANDROID
            else (DeviceLabTargetClass.PHYSICAL,)
        )
        return cls(
            provider=DeviceLabProviderKind.FIREBASE_TEST_LAB,
            platform=platform,
            target_classes=classes,
            state=DeviceLabCapabilityState.ACCOUNT_REQUIRED,
            blockers=("firebase_account_reference_required",),
        )

    def supports(self, matrix: DeviceLabMatrixDefinition) -> bool:
        return (
            self.state is DeviceLabCapabilityState.AVAILABLE
            and self.platform is matrix.platform
            and set(matrix.target_classes).issubset(self.target_classes)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider.value,
            "platform": self.platform.value,
            "target_classes": [item.value for item in self.target_classes],
            "state": self.state.value,
            "account_reference_present": self.account_reference_present,
            "project_scope_sha256": self.project_scope_sha256,
            "quota_remaining": self.quota_remaining,
            "estimated_cost_micros": self.estimated_cost_micros,
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True, slots=True)
class DeviceLabRouteDecision:
    matrix_sha256: str
    artifact_sha256: str
    provider: DeviceLabProviderKind
    provider_capability_sha256: str
    target_classes: tuple[DeviceLabTargetClass, ...]

    def __post_init__(self) -> None:
        _sha256(self.matrix_sha256, "matrix_sha256")
        _sha256(self.artifact_sha256, "artifact_sha256")
        _sha256(self.provider_capability_sha256, "provider_capability_sha256")
        classes = tuple(sorted(set(self.target_classes), key=lambda item: item.value))
        if not classes:
            raise ValueError("route decision requires target classes")
        object.__setattr__(self, "target_classes", classes)

    def to_dict(self) -> dict[str, object]:
        return {
            "matrix_sha256": self.matrix_sha256,
            "artifact_sha256": self.artifact_sha256,
            "provider": self.provider.value,
            "provider_capability_sha256": self.provider_capability_sha256,
            "target_classes": [item.value for item in self.target_classes],
        }

    def digest(self) -> str:
        return _digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class DeviceLabLease:
    lease_id: str
    route_sha256: str
    matrix_sha256: str
    artifact_sha256: str
    timeout_seconds: int = 900
    retry_limit: int = 1

    def __post_init__(self) -> None:
        _stable_id(self.lease_id, "lease_id")
        _sha256(self.route_sha256, "route_sha256")
        _sha256(self.matrix_sha256, "matrix_sha256")
        _sha256(self.artifact_sha256, "artifact_sha256")
        if not 1 <= self.timeout_seconds <= 7200:
            raise ValueError("DeviceLab lease timeout outside bounded range")
        if not 0 <= self.retry_limit <= 3:
            raise ValueError("DeviceLab retry limit outside bounded range")

    def assert_matches(self, matrix: DeviceLabMatrixDefinition, route: DeviceLabRouteDecision) -> None:
        if self.matrix_sha256 != matrix.digest() or self.artifact_sha256 != matrix.artifact_sha256:
            raise ValueError("DeviceLab lease matrix/artifact substitution rejected")
        if self.route_sha256 != route.digest() or route.matrix_sha256 != matrix.digest():
            raise ValueError("DeviceLab lease route substitution rejected")

    def to_dict(self) -> dict[str, object]:
        return {
            "lease_id": self.lease_id,
            "route_sha256": self.route_sha256,
            "matrix_sha256": self.matrix_sha256,
            "artifact_sha256": self.artifact_sha256,
            "timeout_seconds": self.timeout_seconds,
            "retry_limit": self.retry_limit,
        }


@dataclass(frozen=True, slots=True)
class DeviceLabNormalizedResult:
    source_sha: str
    provider: DeviceLabProviderKind
    matrix_sha256: str
    artifact_sha256: str
    provider_result_sha256: str
    result: DeviceLabResultState
    target_class: DeviceLabTargetClass
    physical_device_proven: bool
    cost_micros: int = 0
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if _SOURCE_SHA_RE.fullmatch(self.source_sha) is None:
            raise ValueError("source_sha must be an exact lowercase 40-hex Git SHA")
        _sha256(self.matrix_sha256, "matrix_sha256")
        _sha256(self.artifact_sha256, "artifact_sha256")
        _sha256(self.provider_result_sha256, "provider_result_sha256")
        if not 0 <= self.cost_micros <= _MAX_COST_MICROS:
            raise ValueError("DeviceLab result cost is outside bounded range")
        blockers = tuple(sorted(set(self.blockers)))
        for blocker in blockers:
            _stable_id(blocker, "blocker")
        object.__setattr__(self, "blockers", blockers)
        if self.result is DeviceLabResultState.PASSED and blockers:
            raise ValueError("passing DeviceLab result cannot contain blockers")
        if self.result is DeviceLabResultState.FAILED and not blockers:
            raise ValueError("failed DeviceLab result requires an explicit blocker")
        if self.physical_device_proven and self.target_class is not DeviceLabTargetClass.PHYSICAL:
            raise ValueError("virtual evidence cannot manufacture physical-device proof")
        if self.provider in {DeviceLabProviderKind.XCODE_SIMULATOR, DeviceLabProviderKind.HOSTED_CI} and self.physical_device_proven:
            raise ValueError("simulator/hosted-CI provider cannot manufacture physical-device proof")

    def assert_bound_to(self, matrix: DeviceLabMatrixDefinition) -> None:
        if self.matrix_sha256 != matrix.digest():
            raise ValueError("provider result replay against another matrix rejected")
        if self.artifact_sha256 != matrix.artifact_sha256:
            raise ValueError("provider result replay against another artifact rejected")
        if self.target_class not in matrix.target_classes:
            raise ValueError("provider result target class is absent from matrix")

    def to_dict(self) -> dict[str, object]:
        return {
            "source_sha": self.source_sha,
            "provider": self.provider.value,
            "matrix_sha256": self.matrix_sha256,
            "artifact_sha256": self.artifact_sha256,
            "provider_result_sha256": self.provider_result_sha256,
            "result": self.result.value,
            "target_class": self.target_class.value,
            "physical_device_proven": self.physical_device_proven,
            "cost_micros": self.cost_micros,
            "blockers": list(self.blockers),
        }

    def digest(self) -> str:
        return _digest(self.to_dict())


def select_provider(
    matrix: DeviceLabMatrixDefinition,
    capabilities: Iterable[DeviceLabProviderCapability],
    *,
    max_cost_micros: int = 0,
) -> DeviceLabRouteDecision:
    if not 0 <= max_cost_micros <= _MAX_COST_MICROS:
        raise ValueError("DeviceLab max cost is outside bounded range")
    candidates: list[DeviceLabProviderCapability] = []
    for capability in capabilities:
        if not capability.supports(matrix):
            continue
        if capability.estimated_cost_micros > max_cost_micros:
            continue
        candidates.append(capability)
    if not candidates:
        raise ValueError("no available DeviceLab provider satisfies platform/target/budget constraints")
    selected = min(
        candidates,
        key=lambda item: (_provider_rank(item.provider), item.estimated_cost_micros, item.provider.value),
    )
    return DeviceLabRouteDecision(
        matrix_sha256=matrix.digest(),
        artifact_sha256=matrix.artifact_sha256,
        provider=selected.provider,
        provider_capability_sha256=_digest(selected.to_dict()),
        target_classes=matrix.target_classes,
    )


def normalize_verified_provider_result(
    *,
    source_sha: str,
    matrix: DeviceLabMatrixDefinition,
    route: DeviceLabRouteDecision,
    provider_result_sha256: str,
    result: DeviceLabResultState,
    target_class: DeviceLabTargetClass,
    physical_device_proven: bool = False,
    cost_micros: int = 0,
    blockers: tuple[str, ...] = (),
) -> DeviceLabNormalizedResult:
    if route.matrix_sha256 != matrix.digest() or route.artifact_sha256 != matrix.artifact_sha256:
        raise ValueError("route cannot normalize evidence for a different matrix/artifact")
    normalized = DeviceLabNormalizedResult(
        source_sha=source_sha,
        provider=route.provider,
        matrix_sha256=matrix.digest(),
        artifact_sha256=matrix.artifact_sha256,
        provider_result_sha256=provider_result_sha256,
        result=result,
        target_class=target_class,
        physical_device_proven=physical_device_proven,
        cost_micros=cost_micros,
        blockers=blockers,
    )
    normalized.assert_bound_to(matrix)
    return normalized
