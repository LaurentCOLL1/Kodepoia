from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from kodepoia.release.identity import ReleaseIdentity
from kodepoia.update.bootstrap import load_production_packaged_root
from kodepoia.update.discovery import UpdateDiscoveryService
from kodepoia.update.startup import build_packaged_update_services
from kodepoia.update.trust import (
    MemoryUpdateTransport,
    PackagedRootPin,
    SyntheticUpdateRepositoryBuilder,
    UpdateTargetSpec,
)

REFERENCE_TIME = datetime(2026, 9, 11, 21, 40, tzinfo=UTC)
PLATFORM = "windows-x86_64"
RC2_SOURCE = "2" * 40
RC3_SOURCE = "3" * 40
RC2_INSTALLER = b"r20-fresh-bootstrap-rc2\n"
RC3_INSTALLER = b"r20-fresh-bootstrap-rc3\n"

INSTALLED_RC2 = ReleaseIdentity(
    schema_version=1,
    product="Kodepoia",
    package="kodepoia",
    channel="beta",
    build_type="prerelease",
    source_binding="exact-head",
    major=1,
    minor=1,
    patch=0,
    stage="rc",
    serial=2,
)


class NoNetworkTransport:
    def fetch_metadata(self, name: str) -> bytes:
        raise AssertionError(f"startup unexpectedly fetched metadata {name!r}")

    def fetch_target(self, path: str) -> bytes:
        raise AssertionError(f"startup unexpectedly fetched target {path!r}")


def _target(version: str, source_sha: str) -> UpdateTargetSpec:
    return UpdateTargetSpec(
        channel="beta",
        platform=PLATFORM,
        public_version=version,
        source_sha=source_sha,
    )


def test_packaged_startup_seeds_embedded_root_without_network(tmp_path: Path) -> None:
    packaged = load_production_packaged_root()

    services = build_packaged_update_services(
        state_dir=tmp_path,
        platform_name="linux",
        transport_factory=lambda _policy: NoNetworkTransport(),
    )

    seeded_root = tmp_path / "discovery" / "tuf-discovery" / "root.json"
    assert seeded_root.read_bytes() == packaged.root_bytes
    assert services.discovery is not None


def test_fresh_rc2_state_can_rotate_seeded_root_v1_to_root_v2_and_discover_rc3(
    tmp_path: Path,
) -> None:
    builder = SyntheticUpdateRepositoryBuilder()
    rc2_repository = builder.build(
        _target("1.1.0-rc2", RC2_SOURCE),
        RC2_INSTALLER,
        root_version=1,
        timestamp_version=4,
        snapshot_version=4,
        targets_version=2,
    )
    builder.rotate_root_keys()
    rc3_repository = builder.build(
        _target("1.1.0-rc3", RC3_SOURCE),
        RC3_INSTALLER,
        root_version=2,
        timestamp_version=5,
        snapshot_version=5,
        targets_version=3,
    )

    packaged_root = load_production_packaged_root()
    del packaged_root
    state_base = tmp_path / "updates"
    discovery_state = state_base / "discovery" / "tuf-discovery"
    discovery_state.mkdir(parents=True, exist_ok=True)
    (discovery_state / "root.json").write_bytes(rc2_repository.root)

    service = UpdateDiscoveryService(
        state_base / "discovery",
        root_pin=PackagedRootPin.from_root(rc2_repository.root),
        transport=MemoryUpdateTransport.from_repository(rc3_repository),
        platform=PLATFORM,
        installed_release=INSTALLED_RC2,
        reference_time=REFERENCE_TIME,
    )

    result = service.check("beta")

    assert result.status == "update-available"
    assert result.candidate is not None
    assert result.candidate.target.public_version == "1.1.0-rc3"
    assert result.candidate.target.source_sha == RC3_SOURCE
    assert result.candidate.sha256
    assert (discovery_state / "root.json").read_bytes() == rc3_repository.root
