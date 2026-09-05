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
        "channels/beta/windows-x86_64/1.1.0-rc1/"
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
    assert result.candidate.sha256 != __import__("hashlib").sha256(transport.targets[target.path]).hexdigest()


def test_wrong_channel_target_is_refused(tmp_path) -> None:
    beta_target = _target()
    stable_target = _target(channel="stable")
    builder = SyntheticUpdateRepositoryBuilder()
    repository = builder.build(beta_target, INSTALLER)
    client = UpdateClient(
        tmp_path,
        root_pin=PackagedRootPin.from_root(repository.root),
        reference_time=REFERENCE_TIME,
    )

    result = client.check(MemoryUpdateTransport.from_repository(repository), stable_target)
    assert result.status == "verification-failed"
    assert result.candidate is None
    assert "does not expose target" in result.detail


def test_offline_without_cache_is_non_blocking(tmp_path) -> None:
    target = _target()
    builder = SyntheticUpdateRepositoryBuilder()
    repository = builder.build(target, INSTALLER)
    transport = MemoryUpdateTransport.from_repository(repository)
    transport.online = False
    client = UpdateClient(
        tmp_path,
        root_pin=PackagedRootPin.from_root(repository.root),
        reference_time=REFERENCE_TIME,
    )

    result = client.check(transport, target)
    assert result.status == "offline-no-cache"
    assert result.candidate is None


def test_offline_after_success_returns_last_verified_candidate(tmp_path) -> None:
    target = _target()
    builder = SyntheticUpdateRepositoryBuilder()
    repository = builder.build(target, INSTALLER)
    transport = MemoryUpdateTransport.from_repository(repository)
    client = UpdateClient(
        tmp_path,
        root_pin=PackagedRootPin.from_root(repository.root),
        reference_time=REFERENCE_TIME,
    )
    verified = client.check(transport, target)
    assert verified.status == "verified"

    transport.online = False
    offline = client.check(transport, target)
    assert offline.status == "offline-cached"
    assert offline.candidate == verified.candidate


def test_root_key_rotation_is_accepted_only_with_old_and_new_thresholds(tmp_path) -> None:
    target = _target()
    builder = SyntheticUpdateRepositoryBuilder(root_threshold=2)
    first = builder.build(
        target,
        INSTALLER,
        root_version=1,
        timestamp_version=1,
        snapshot_version=1,
        targets_version=1,
    )
    client = UpdateClient(
        tmp_path,
        root_pin=PackagedRootPin.from_root(first.root),
        reference_time=REFERENCE_TIME,
    )
    assert client.check(MemoryUpdateTransport.from_repository(first), target).status == "verified"

    builder.rotate_root_keys()
    second = builder.build(
        target,
        b"synthetic-kodepoia-installer-v2\n",
        root_version=2,
        timestamp_version=2,
        snapshot_version=2,
        targets_version=2,
    )
    result = client.check(MemoryUpdateTransport.from_repository(second), target)
    assert result.status == "verified"
    assert result.candidate is not None
    assert result.candidate.tuf_state.root_version == 2


def test_packaged_root_pin_rejects_different_bootstrap_root(tmp_path) -> None:
    target = _target()
    trusted_builder = SyntheticUpdateRepositoryBuilder()
    trusted = trusted_builder.build(target, INSTALLER)
    attacker_builder = SyntheticUpdateRepositoryBuilder()
    attacker = attacker_builder.build(target, INSTALLER)
    client = UpdateClient(
        tmp_path,
        root_pin=PackagedRootPin.from_root(trusted.root),
        reference_time=REFERENCE_TIME,
    )

    with pytest.raises(TufVerificationError, match="packaged trusted-root pin"):
        client.verify_refresh(MemoryUpdateTransport.from_repository(attacker), target)
