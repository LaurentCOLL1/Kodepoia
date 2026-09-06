from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from kodepoia.release.identity import CURRENT_RELEASE
from kodepoia.update.discovery import UpdateDiscoveryService
from kodepoia.update.trust import (
    MemoryUpdateTransport,
    PackagedRootPin,
    SyntheticUpdateRepositoryBuilder,
    UpdateTargetSpec,
)

REFERENCE_TIME = datetime(2026, 9, 6, 12, 0, tzinfo=UTC)
PLATFORM = "windows-x86_64"
SOURCE_SHA = "b" * 40
INSTALLER = b"r18.7-metadata-only-installer-fixture\n"


class MetadataOnlyTransport:
    def __init__(self, transport: MemoryUpdateTransport) -> None:
        self.transport = transport
        self.target_fetches = 0

    def fetch_metadata(self, name: str) -> bytes:
        return self.transport.fetch_metadata(name)

    def fetch_target(self, path: str) -> bytes:
        self.target_fetches += 1
        raise AssertionError(f"R18.7 discovery must not download target {path!r}")


def _target(*, channel: str = "beta", version: str = "1.1.0-rc2") -> UpdateTargetSpec:
    return UpdateTargetSpec(
        channel=channel,
        platform=PLATFORM,
        public_version=version,
        source_sha=SOURCE_SHA,
    )


def _service(tmp_path, repository, *, transport=None) -> tuple[UpdateDiscoveryService, object]:
    wrapped = transport or MetadataOnlyTransport(MemoryUpdateTransport.from_repository(repository))
    return (
        UpdateDiscoveryService(
            tmp_path,
            root_pin=PackagedRootPin.from_root(repository.root),
            transport=wrapped,
            platform=PLATFORM,
            reference_time=REFERENCE_TIME,
        ),
        wrapped,
    )


def test_beta_discovery_uses_only_verified_metadata_and_never_fetches_installer(tmp_path) -> None:
    target = _target()
    repository = SyntheticUpdateRepositoryBuilder().build(target, INSTALLER)
    service, transport = _service(tmp_path, repository)

    result = service.check("beta")

    assert result.status == "update-available"
    assert result.candidate is not None
    assert result.candidate.target == target
    assert result.candidate.size_bytes == len(INSTALLER)
    assert result.candidate.sha256 == hashlib.sha256(INSTALLER).hexdigest()
    assert result.candidate.source_verification_state == "tuf-verified-metadata"
    assert transport.target_fetches == 0


def test_same_version_is_up_to_date(tmp_path) -> None:
    target = UpdateTargetSpec.from_release(
        CURRENT_RELEASE,
        source_sha=SOURCE_SHA,
        platform=PLATFORM,
    )
    repository = SyntheticUpdateRepositoryBuilder().build(target, INSTALLER)
    service, _ = _service(tmp_path, repository)

    result = service.check("beta")

    assert result.status == "up-to-date"
    assert result.candidate is not None
    assert result.candidate.target.public_version == CURRENT_RELEASE.public_version


def test_stable_release_after_installed_rc_is_update_available(tmp_path) -> None:
    target = _target(channel="stable", version="1.1.0")
    repository = SyntheticUpdateRepositoryBuilder().build(target, INSTALLER)
    service, _ = _service(tmp_path, repository)

    result = service.check("stable")

    assert result.status == "update-available"
    assert result.candidate is not None
    assert result.candidate.target.channel == "stable"


def test_unpublished_selected_channel_is_distinct_from_verification_failure(tmp_path) -> None:
    target = _target(channel="beta")
    repository = SyntheticUpdateRepositoryBuilder().build(target, INSTALLER)
    service, _ = _service(tmp_path, repository)

    result = service.check("stable")

    assert result.status == "channel-unavailable"
    assert result.candidate is None


def test_offline_is_non_blocking_and_distinct(tmp_path) -> None:
    target = _target()
    repository = SyntheticUpdateRepositoryBuilder().build(target, INSTALLER)
    memory = MemoryUpdateTransport.from_repository(repository)
    memory.online = False
    service, _ = _service(tmp_path, repository, transport=memory)

    result = service.check("beta")

    assert result.status == "offline"
    assert result.candidate is None


def test_expired_timestamp_has_specific_state(tmp_path) -> None:
    target = _target()
    repository = SyntheticUpdateRepositoryBuilder().build(
        target,
        INSTALLER,
        timestamp_expires=datetime(2026, 9, 5, 12, 0, tzinfo=UTC),
    )
    service, _ = _service(tmp_path, repository)

    result = service.check("beta")

    assert result.status == "metadata-expired"
    assert result.candidate is None


def test_tampered_targets_metadata_fails_closed(tmp_path) -> None:
    target = _target()
    repository = SyntheticUpdateRepositoryBuilder().build(target, INSTALLER)
    memory = MemoryUpdateTransport.from_repository(repository)
    memory.metadata["targets.json"] += b"tamper"
    service, _ = _service(tmp_path, repository, transport=memory)

    result = service.check("beta")

    assert result.status == "verification-failed"
    assert result.candidate is None


def test_metadata_rollback_fails_closed(tmp_path) -> None:
    target = _target()
    builder = SyntheticUpdateRepositoryBuilder()
    first = builder.build(
        target,
        INSTALLER,
        timestamp_version=2,
        snapshot_version=2,
        targets_version=2,
    )
    service, _ = _service(tmp_path, first)
    assert service.check("beta").status == "update-available"

    rollback = builder.build(
        target,
        INSTALLER,
        timestamp_version=1,
        snapshot_version=1,
        targets_version=1,
    )
    service.transport = MemoryUpdateTransport.from_repository(rollback)

    result = service.check("beta")

    assert result.status == "verification-failed"
    assert "rollback" in result.detail
