from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kodepoia.release.identity import CURRENT_RELEASE
from kodepoia.release.tuf_security import TufVerificationError
from kodepoia.update.trust import (
    MemoryUpdateTransport,
    PackagedRootPin,
    SyntheticUpdateRepositoryBuilder,
    UpdateClient,
    UpdateTargetSpec,
)

REFERENCE_TIME = datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
SOURCE_SHA = "a" * 40
PLATFORM = "windows-x86_64"
INSTALLER = b"synthetic-kodepoia-installer-v1\n"


def _target(*, channel: str | None = None) -> UpdateTargetSpec:
    if channel is None:
        return UpdateTargetSpec.from_release(
            CURRENT_RELEASE,
            source_sha=SOURCE_SHA,
            platform=PLATFORM,
        )
    return UpdateTargetSpec(
        channel=channel,
        platform=PLATFORM,
        public_version=CURRENT_RELEASE.public_version,
        source_sha=SOURCE_SHA,
    )


def test_target_path_binds_channel_platform_release_identity_and_source() -> None:
    target = _target()
    assert CURRENT_RELEASE.channel == "beta"
    assert target.path == (
        f"channels/beta/windows-x86_64/{CURRENT_RELEASE.public_version}/"
        f"{SOURCE_SHA}/KodepoiaSetup.exe"
    )


def test_channel_specific_installer_refresh_verifies_and_persists_candidate(tmp_path) -> None:
    target = _target()
    builder = SyntheticUpdateRepositoryBuilder()
    repository = builder.build(target, INSTALLER)
    client = UpdateClient(
        tmp_path,
        root_pin=PackagedRootPin.from_root(repository.root),
        reference_time=REFERENCE_TIME,
    )

    result = client.check(MemoryUpdateTransport.from_repository(repository), target)
    assert result.status == "verified"
    assert result.candidate is not None
    assert result.candidate.target == target
    assert result.candidate.size_bytes == len(INSTALLER)
    assert result.candidate.sha256 == result.candidate.tuf_state.target_sha256


def test_compromised_mirror_target_is_refused_and_last_verified_candidate_survives(tmp_path) -> None:
    target = _target()
    builder = SyntheticUpdateRepositoryBuilder()
    repository = builder.build(target, INSTALLER)
    transport = MemoryUpdateTransport.from_repository(repository)
    client = UpdateClient(
        tmp_path,
        root_pin=PackagedRootPin.from_root(repository.root),
        reference_time=REFERENCE_TIME,
    )
    assert client.check(transport, target).status == "verified"

    transport.targets[target.path] = b"malicious mirror replacement\n"
    result = client.check(transport, target)
    assert result.status == "verification-failed"
    assert result.candidate is not None
