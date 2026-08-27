from __future__ import annotations

import pytest

from kodepoia.mobile.devicelab import (
    DeviceLabCapabilityState,
    DeviceLabDeviceSpec,
    DeviceLabLease,
    DeviceLabMatrixDefinition,
    DeviceLabNormalizedResult,
    DeviceLabOrientation,
    DeviceLabPlatform,
    DeviceLabProviderCapability,
    DeviceLabProviderKind,
    DeviceLabResultState,
    DeviceLabTargetClass,
    normalize_verified_provider_result,
    select_provider,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SOURCE_SHA = "d" * 40


def device(
    *,
    model: str = "Pixel 9",
    os_version: str = "16.0",
    locale: str = "en-US",
    orientation: DeviceLabOrientation = DeviceLabOrientation.PORTRAIT,
    target_class: DeviceLabTargetClass = DeviceLabTargetClass.VIRTUAL,
) -> DeviceLabDeviceSpec:
    return DeviceLabDeviceSpec(model, os_version, locale, orientation, target_class)


def matrix(
    *,
    platform: DeviceLabPlatform = DeviceLabPlatform.ANDROID,
    artifact_sha256: str = SHA_A,
    devices: tuple[DeviceLabDeviceSpec, ...] | None = None,
) -> DeviceLabMatrixDefinition:
    return DeviceLabMatrixDefinition(
        matrix_id="canonical.matrix",
        platform=platform,
        artifact_sha256=artifact_sha256,
        test_execution_id="canonical.tests",
        devices=devices or (device(),),
    )


def local_android(*classes: DeviceLabTargetClass) -> DeviceLabProviderCapability:
    return DeviceLabProviderCapability(
        provider=DeviceLabProviderKind.LOCAL_ANDROID,
        platform=DeviceLabPlatform.ANDROID,
        target_classes=classes or (DeviceLabTargetClass.VIRTUAL,),
        state=DeviceLabCapabilityState.AVAILABLE,
    )


def xcode_simulator() -> DeviceLabProviderCapability:
    return DeviceLabProviderCapability(
        provider=DeviceLabProviderKind.XCODE_SIMULATOR,
        platform=DeviceLabPlatform.IOS,
        target_classes=(DeviceLabTargetClass.VIRTUAL,),
        state=DeviceLabCapabilityState.AVAILABLE,
    )


def firebase(
    *,
    platform: DeviceLabPlatform,
    classes: tuple[DeviceLabTargetClass, ...],
    cost: int = 100,
) -> DeviceLabProviderCapability:
    return DeviceLabProviderCapability(
        provider=DeviceLabProviderKind.FIREBASE_TEST_LAB,
        platform=platform,
        target_classes=classes,
        state=DeviceLabCapabilityState.AVAILABLE,
        account_reference_present=True,
        project_scope_sha256=SHA_C,
        quota_remaining=5,
        estimated_cost_micros=cost,
    )


def test_matrix_identity_is_deterministic_across_device_input_order() -> None:
    first = device(model="Pixel 9", locale="en-US")
    second = device(model="Pixel 8", locale="fr-FR", orientation=DeviceLabOrientation.LANDSCAPE)
    left = matrix(devices=(first, second))
    right = matrix(devices=(second, first))
    assert left.to_dict() == right.to_dict()
    assert left.digest() == right.digest()


def test_matrix_rejects_duplicate_device_configuration() -> None:
    same = device()
    with pytest.raises(ValueError, match="duplicate"):
        matrix(devices=(same, same))


def test_matrix_rejects_unbounded_or_invalid_locale() -> None:
    with pytest.raises(ValueError, match="locale"):
        device(locale="../../etc/passwd")


def test_local_android_wins_for_zero_cost_virtual_matrix() -> None:
    definition = matrix()
    route = select_provider(
        definition,
        (
            firebase(
                platform=DeviceLabPlatform.ANDROID,
                classes=(DeviceLabTargetClass.VIRTUAL, DeviceLabTargetClass.PHYSICAL),
            ),
            local_android(DeviceLabTargetClass.VIRTUAL),
        ),
    )
    assert route.provider is DeviceLabProviderKind.LOCAL_ANDROID
    assert route.artifact_sha256 == definition.artifact_sha256


def test_ios_virtual_matrix_routes_to_xcode_simulator_not_firebase() -> None:
    ios_virtual = matrix(
        platform=DeviceLabPlatform.IOS,
        devices=(device(model="iPhone Air", os_version="26.5"),),
    )
    route = select_provider(
        ios_virtual,
        (
            firebase(platform=DeviceLabPlatform.IOS, classes=(DeviceLabTargetClass.PHYSICAL,), cost=0),
            xcode_simulator(),
        ),
    )
    assert route.provider is DeviceLabProviderKind.XCODE_SIMULATOR


def test_firebase_ios_rejects_synthetic_virtual_capability() -> None:
    with pytest.raises(ValueError, match="physical-device only"):
        firebase(
            platform=DeviceLabPlatform.IOS,
            classes=(DeviceLabTargetClass.VIRTUAL,),
            cost=0,
        )


def test_physical_android_requires_explicit_available_provider_and_budget() -> None:
    physical = matrix(devices=(device(target_class=DeviceLabTargetClass.PHYSICAL),))
    cloud = firebase(
        platform=DeviceLabPlatform.ANDROID,
        classes=(DeviceLabTargetClass.PHYSICAL, DeviceLabTargetClass.VIRTUAL),
        cost=250,
    )
    with pytest.raises(ValueError, match="no available DeviceLab provider"):
        select_provider(physical, (cloud,), max_cost_micros=249)
    assert select_provider(physical, (cloud,), max_cost_micros=250).provider is DeviceLabProviderKind.FIREBASE_TEST_LAB


def test_firebase_without_account_is_explicit_and_not_routable() -> None:
    capability = DeviceLabProviderCapability.firebase_without_account(DeviceLabPlatform.ANDROID)
    assert capability.state is DeviceLabCapabilityState.ACCOUNT_REQUIRED
    assert capability.account_reference_present is False
    assert capability.blockers == ("firebase_account_reference_required",)
    with pytest.raises(ValueError, match="no available DeviceLab provider"):
        select_provider(matrix(), (capability,))


def test_quota_exhaustion_cannot_be_available() -> None:
    with pytest.raises(ValueError, match="exhausted quota"):
        DeviceLabProviderCapability(
            provider=DeviceLabProviderKind.FIREBASE_TEST_LAB,
            platform=DeviceLabPlatform.ANDROID,
            target_classes=(DeviceLabTargetClass.VIRTUAL,),
            state=DeviceLabCapabilityState.AVAILABLE,
            account_reference_present=True,
            project_scope_sha256=SHA_C,
            quota_remaining=0,
        )


def test_normalized_result_is_bound_to_matrix_and_artifact() -> None:
    definition = matrix()
    route = select_provider(definition, (local_android(DeviceLabTargetClass.VIRTUAL),))
    result = normalize_verified_provider_result(
        source_sha=SOURCE_SHA,
        matrix=definition,
        route=route,
        provider_result_sha256=SHA_B,
        result=DeviceLabResultState.PASSED,
        target_class=DeviceLabTargetClass.VIRTUAL,
    )
    result.assert_bound_to(definition)
    with pytest.raises(ValueError, match="another matrix"):
        result.assert_bound_to(matrix(artifact_sha256=SHA_C))


def test_virtual_result_cannot_manufacture_physical_device_proof() -> None:
    definition = matrix()
    route = select_provider(definition, (local_android(DeviceLabTargetClass.VIRTUAL),))
    with pytest.raises(ValueError, match="virtual evidence"):
        normalize_verified_provider_result(
            source_sha=SOURCE_SHA,
            matrix=definition,
            route=route,
            provider_result_sha256=SHA_B,
            result=DeviceLabResultState.PASSED,
            target_class=DeviceLabTargetClass.VIRTUAL,
            physical_device_proven=True,
        )


def test_hosted_ci_cannot_advertise_physical_device_support() -> None:
    with pytest.raises(ValueError, match="cannot manufacture physical-device"):
        DeviceLabProviderCapability(
            provider=DeviceLabProviderKind.HOSTED_CI,
            platform=DeviceLabPlatform.ANDROID,
            target_classes=(DeviceLabTargetClass.PHYSICAL,),
            state=DeviceLabCapabilityState.AVAILABLE,
        )


def test_lease_rejects_matrix_or_route_substitution() -> None:
    definition = matrix()
    route = select_provider(definition, (local_android(DeviceLabTargetClass.VIRTUAL),))
    lease = DeviceLabLease(
        lease_id="lease.canonical",
        route_sha256=route.digest(),
        matrix_sha256=definition.digest(),
        artifact_sha256=definition.artifact_sha256,
        timeout_seconds=900,
        retry_limit=2,
    )
    lease.assert_matches(definition, route)
    with pytest.raises(ValueError, match="substitution"):
        lease.assert_matches(matrix(artifact_sha256=SHA_C), route)


def test_failed_result_requires_explicit_blocker() -> None:
    with pytest.raises(ValueError, match="requires an explicit blocker"):
        DeviceLabNormalizedResult(
            source_sha=SOURCE_SHA,
            provider=DeviceLabProviderKind.LOCAL_ANDROID,
            matrix_sha256=SHA_A,
            artifact_sha256=SHA_A,
            provider_result_sha256=SHA_B,
            result=DeviceLabResultState.FAILED,
            target_class=DeviceLabTargetClass.VIRTUAL,
            physical_device_proven=False,
        )
