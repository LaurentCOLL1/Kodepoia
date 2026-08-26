from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.mobile.devicelab import (
    DeviceLabCapabilityState,
    DeviceLabDeviceSpec,
    DeviceLabLease,
    DeviceLabMatrixDefinition,
    DeviceLabOrientation,
    DeviceLabPlatform,
    DeviceLabProviderCapability,
    DeviceLabProviderKind,
    DeviceLabResultState,
    DeviceLabTargetClass,
    normalize_verified_provider_result,
    select_provider,
)
from kodepoia.mobile.devicelab_evidence import DeviceLabEvidenceBundle

SHA_A = "a" * 64
SHA_B = "b" * 64
SOURCE_SHA = "c" * 40


def build_bundle(*, cleanup_complete: bool = True) -> DeviceLabEvidenceBundle:
    definition = DeviceLabMatrixDefinition(
        matrix_id="canonical.matrix",
        platform=DeviceLabPlatform.ANDROID,
        artifact_sha256=SHA_A,
        test_execution_id="canonical.tests",
        devices=(
            DeviceLabDeviceSpec(
                model="Pixel 9",
                os_version="16.0",
                locale="en-US",
                orientation=DeviceLabOrientation.PORTRAIT,
                target_class=DeviceLabTargetClass.VIRTUAL,
            ),
        ),
    )
    capability = DeviceLabProviderCapability(
        provider=DeviceLabProviderKind.LOCAL_ANDROID,
        platform=DeviceLabPlatform.ANDROID,
        target_classes=(DeviceLabTargetClass.VIRTUAL,),
        state=DeviceLabCapabilityState.AVAILABLE,
    )
    route = select_provider(definition, (capability,))
    lease = DeviceLabLease(
        lease_id="lease.canonical",
        route_sha256=route.digest(),
        matrix_sha256=definition.digest(),
        artifact_sha256=definition.artifact_sha256,
    )
    result = normalize_verified_provider_result(
        source_sha=SOURCE_SHA,
        matrix=definition,
        route=route,
        provider_result_sha256=SHA_B,
        result=DeviceLabResultState.PASSED,
        target_class=DeviceLabTargetClass.VIRTUAL,
    )
    return DeviceLabEvidenceBundle(
        schema_version=1,
        matrix=definition,
        route=route,
        lease=lease,
        results=(result,),
        cleanup_complete=cleanup_complete,
    )


def test_bundle_is_deterministic_and_schema_valid() -> None:
    bundle = build_bundle()
    assert bundle.digest() == build_bundle().digest()
    schema = json.loads(Path("schemas/r13/devicelab-evidence.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(bundle.to_dict())


def test_bundle_requires_cleanup() -> None:
    with pytest.raises(ValueError, match="cleanup"):
        build_bundle(cleanup_complete=False)
