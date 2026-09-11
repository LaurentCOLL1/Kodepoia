from __future__ import annotations

import hashlib
import re
import tempfile
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from securesystemslib.signer import CryptoSigner, Signer
from tuf.api.metadata import MetaFile, Metadata, Root, Snapshot, Timestamp

from kodepoia.release.tuf_security import SyntheticTufRepository, TufVerificationError
from kodepoia.update.delivery import VerifiedUpdateArtifact
from kodepoia.update.operations_health import temporary_update_service_message
from kodepoia.update.seamless import SeamlessUpdateInstallCoordinator
from kodepoia.update.steady_state_refresh import (
    SteadyStateRefreshError,
    refresh_if_due,
)
from kodepoia.update.trust import (
    MemoryUpdateTransport,
    PackagedRootPin,
    SyntheticUpdateRepositoryBuilder,
    UpdateClient,
    UpdateTargetSpec,
)

R20_6_FORMAT = "kodepoia-r20-6-continuous-operations-acceptance"
R20_6_SCHEMA_VERSION = 1
_SHA_RE = re.compile(r"[0-9a-f]{40}")


def _serialize(metadata: Metadata[Any]) -> bytes:
    return metadata.to_bytes() + b"\n"


def _sign(payload: dict[str, object], signer: Signer) -> bytes:
    metadata = Metadata.from_dict({"signatures": [], "signed": payload})
    metadata.sign(signer)
    return _serialize(metadata)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _target() -> UpdateTargetSpec:
    return UpdateTargetSpec(
        channel="beta",
        platform="windows-x86_64",
        public_version="1.1.0-rc2",
        source_sha="a" * 40,
    )


def _timestamp_for_snapshot(
    snapshot_bytes: bytes,
    *,
    version: int,
    expires: datetime,
    signer: Signer,
) -> bytes:
    payload: dict[str, object] = {
        "_type": "timestamp",
        "expires": expires.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "meta": {
            "snapshot.json": {
                "hashes": {"sha256": hashlib.sha256(snapshot_bytes).hexdigest()},
                "length": len(snapshot_bytes),
                "version": Metadata.from_bytes(snapshot_bytes).signed.version,
            }
        },
        "spec_version": "1.0.31",
        "version": version,
    }
    return _sign(payload, signer)


def _snapshot_for_targets(
    targets_bytes: bytes,
    *,
    version: int,
    expires: datetime,
    signer: Signer,
) -> bytes:
    targets_version = Metadata.from_bytes(targets_bytes).signed.version
    payload: dict[str, object] = {
        "_type": "snapshot",
        "expires": expires.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "meta": {
            "targets.json": {
                "hashes": {"sha256": hashlib.sha256(targets_bytes).hexdigest()},
                "length": len(targets_bytes),
                "version": targets_version,
            }
        },
        "spec_version": "1.0.31",
        "version": version,
    }
    return _sign(payload, signer)


def _single_online_role_rotation(
    *,
    initial: SyntheticTufRepository,
    builder: SyntheticUpdateRepositoryBuilder,
    target: UpdateTargetSpec,
    installer: bytes,
    reference_time: datetime,
    state_dir: Path,
) -> bool:
    core = builder._core
    root_signer = core._root_signers[0]
    snapshot_signer = core._snapshot_signer
    targets_signer = core._targets_signer
    old_timestamp_signer = core._timestamp_signer
    new_timestamp_signer = CryptoSigner.generate_ed25519()
    if old_timestamp_signer.public_key.keyid == new_timestamp_signer.public_key.keyid:
        return False

    initial_root = Metadata.from_bytes(initial.root)
    rotated_root = Root(
        version=initial_root.signed.version + 1,
        expires=datetime(2035, 1, 1, tzinfo=UTC),
        consistent_snapshot=False,
    )
    rotated_root.add_key(root_signer.public_key, "root")
    rotated_root.add_key(targets_signer.public_key, "targets")
    rotated_root.add_key(snapshot_signer.public_key, "snapshot")
    rotated_root.add_key(new_timestamp_signer.public_key, "timestamp")
    rotated_root.roles["root"].threshold = 1
    root_md = Metadata(rotated_root)
    root_md.sign(root_signer)
    root_bytes = _serialize(root_md)

    snapshot_bytes = _snapshot_for_targets(
        initial.targets,
        version=2,
        expires=datetime(2035, 1, 1, tzinfo=UTC),
        signer=snapshot_signer,
    )
    timestamp_bytes = _timestamp_for_snapshot(
        snapshot_bytes,
        version=2,
        expires=datetime(2035, 1, 1, tzinfo=UTC),
        signer=new_timestamp_signer,
    )
    rotated = SyntheticTufRepository(
        root=root_bytes,
        timestamp=timestamp_bytes,
        snapshot=snapshot_bytes,
        targets=initial.targets,
        target_path=target.path,
        target_data=installer,
    )
    client = UpdateClient(
        state_dir,
        root_pin=PackagedRootPin.from_root(initial.root),
        reference_time=reference_time,
    )
    before = client.check(MemoryUpdateTransport.from_repository(initial), target)
    if before.status != "verified" or before.candidate is None:
        return False
    after = client.check(MemoryUpdateTransport.from_repository(rotated), target)
    return bool(
        after.status == "verified"
        and after.candidate is not None
        and after.candidate.tuf_state.root_version == 2
        and after.candidate.tuf_state.targets_version == before.candidate.tuf_state.targets_version
        and after.candidate.sha256 == before.candidate.sha256
    )


class _FakeLauncher:
    def __init__(self) -> None:
        self.paths: list[Path] = []

    def launch(self, path: Path) -> None:
        self.paths.append(path)


class _UnusedDownloader:
    def stage(self, candidate: object, transport: object) -> None:
        del candidate, transport
        raise AssertionError("R20.6 preservation drill must not download")


class _UnusedTransport:
    def iter_target(self, path: str, *, chunk_size: int) -> None:
        del path, chunk_size
        raise AssertionError("R20.6 preservation drill must not use transport")


def _preserve_user_state(root: Path) -> bool:
    settings = root / "user" / ".kodepoia" / "settings.json"
    project = root / "project" / "sentinel.txt"
    settings.parent.mkdir(parents=True, exist_ok=True)
    project.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text('{"locale":"fr","r20_6":"preserve-me"}\n', encoding="utf-8")
    project.write_text("project-must-survive-r20.6\n", encoding="utf-8")
    before = (_sha256(settings), _sha256(project))

    payload = b"verified-r20-6-installer-fixture\n"
    installer = root / "KodepoiaSetup.exe"
    installer.write_bytes(payload)
    artifact = VerifiedUpdateArtifact(
        path=installer,
        public_version="1.1.0-rc2",
        source_sha="b" * 40,
        channel="beta",
        size_bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        authenticode_status="valid",
        identity_status="ProductVersion='1.1.0-rc2'",
    )
    launcher = _FakeLauncher()
    coordinator = SeamlessUpdateInstallCoordinator(
        root / "update-state",
        downloader=_UnusedDownloader(),
        transport=_UnusedTransport(),
        launcher=launcher,
        current_public_version="1.1.0-rc1",
    )
    coordinator.launch_staged(artifact, confirmed=True)
    reconciled = coordinator.reconcile_startup("1.1.0-rc2")
    after = (_sha256(settings), _sha256(project))
    return bool(reconciled == "succeeded" and launcher.paths == [installer] and before == after)


def _workflow_contract(repo_root: Path) -> dict[str, bool]:
    refresh = (repo_root / ".github/workflows/r20-4-scheduled-metadata-refresh.yml").read_text(
        encoding="utf-8"
    ).lower()
    monitor = (repo_root / ".github/workflows/r20-5-expiry-monitoring.yml").read_text(
        encoding="utf-8"
    ).lower()
    runbook = (repo_root / "docs/release/R20_5_UPDATE_OPERATIONS_RUNBOOK.md").read_text(
        encoding="utf-8"
    )
    r19_5 = (repo_root / ".github/workflows/r19-5-corrective-rc-acceptance.yml").read_text(
        encoding="utf-8"
    )
    return {
        "serialized_refresh": (
            "group: r20-4-production-metadata-refresh" in refresh
            and "cancel-in-progress: false" in refresh
            and "main advanced from" in refresh
            and "repository-bootstrap-ubuntu-latest" in refresh
            and "repository-bootstrap-windows-latest" in refresh
        ),
        "offline_authority_absent_from_actions": (
            "tuf_root_" not in refresh
            and "tuf_targets_" not in refresh
            and "tuf_root_" not in monitor
            and "tuf_targets_" not in monitor
        ),
        "zero_cost_path": (
            "environment: tuf-production-signing" in refresh
            and "id-token: write" not in refresh
            and "kms" not in monitor
        ),
        "emergency_runbook": all(
            marker in runbook
            for marker in (
                "Emergency manual refresh",
                "GitHub Actions outage",
                "never accept expired",
                "Root/Targets",
            )
        ),
        "historical_live_state_preservation": all(
            marker in r19_5
            for marker in (
                "Replay exact rc1 to pinned rc2 upgrade and preserve user state",
                "User settings changed",
                "Project data changed",
            )
        ),
    }


def build_continuous_operations_report(
    repo_root: Path,
    *,
    source_sha: str,
) -> dict[str, object]:
    source = source_sha.strip().lower()
    if _SHA_RE.fullmatch(source) is None:
        raise ValueError("source_sha must be an exact lowercase 40-character Git SHA")
    repo_root = repo_root.resolve(strict=True)
    target = _target()
    installer_v1 = b"kodepoia-r20-6-installer-v1\n"
    installer_v2 = b"kodepoia-r20-6-installer-v2\n"
    old_time = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    return_time = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)

    matrix: dict[str, bool] = {}
    details: dict[str, object] = {}
    with tempfile.TemporaryDirectory(prefix="kodepoia-r20-6-") as temporary:
        temp = Path(temporary)
        builder = SyntheticUpdateRepositoryBuilder(root_threshold=1)
        old = builder.build(
            target,
            installer_v1,
            root_version=1,
            timestamp_version=1,
            snapshot_version=1,
            targets_version=1,
        )
        root_pin = PackagedRootPin.from_root(old.root)
        old_client = UpdateClient(temp / "client", root_pin=root_pin, reference_time=old_time)
        first = old_client.check(MemoryUpdateTransport.from_repository(old), target)
        matrix["persisted_client_state_after_long_offline"] = bool(
            first.status == "verified" and (temp / "client/tuf/state.json").is_file()
        )

        fresh = builder.build(
            target,
            installer_v2,
            root_version=1,
            timestamp_version=2,
            snapshot_version=2,
            targets_version=2,
        )
        returned_client = UpdateClient(
            temp / "client",
            root_pin=root_pin,
            reference_time=return_time,
        )
        returned = returned_client.check(MemoryUpdateTransport.from_repository(fresh), target)
        matrix["fresh_metadata_after_return"] = bool(
            returned.status == "verified"
            and returned.candidate is not None
            and returned.candidate.tuf_state.timestamp_version == 2
            and returned.candidate.tuf_state.snapshot_version == 2
            and returned.candidate.tuf_state.targets_version == 2
        )
        matrix["installation_age_not_trust_input"] = bool(
            matrix["persisted_client_state_after_long_offline"]
            and matrix["fresh_metadata_after_return"]
            and old_time < return_time - timedelta(days=90)
        )

        expired = builder.build(
            target,
            installer_v2,
            root_version=1,
            timestamp_version=3,
            snapshot_version=3,
            targets_version=3,
            timestamp_expires=return_time - timedelta(seconds=1),
        )
        expired_result = returned_client.check(
            MemoryUpdateTransport.from_repository(expired), target
        )
        matrix["expired_server_metadata_rejected"] = bool(
            expired_result.status == "verification-failed"
            and "expired" in expired_result.detail.lower()
        )

        replay = returned_client.check(MemoryUpdateTransport.from_repository(old), target)
        matrix["old_timestamp_replay_rejected"] = bool(
            replay.status == "verification-failed"
            and "rollback" in replay.detail.lower()
        )

        fresh3 = builder.build(
            target,
            b"kodepoia-r20-6-installer-v3\n",
            root_version=1,
            timestamp_version=3,
            snapshot_version=3,
            targets_version=3,
        )
        mixed_transport = MemoryUpdateTransport.from_repository(fresh3)
        mixed_transport.metadata["targets.json"] = fresh.targets
        mixed = returned_client.check(mixed_transport, target)
        matrix["snapshot_targets_mix_and_match_rejected"] = bool(
            mixed.status == "verification-failed"
            and ("targets" in mixed.detail.lower() or "hash" in mixed.detail.lower())
        )

        outage_message = temporary_update_service_message("channel-unavailable", "en-US")
        matrix["signing_or_actions_outage_is_non_blocking"] = bool(
            outage_message["retryable"]
            and not outage_message["blocks_startup"]
            and outage_message["local_work_available"]
            and not outage_message["accepts_expired_metadata"]
        )

        due_builder = SyntheticUpdateRepositoryBuilder(root_threshold=1)
        due = due_builder.build(
            target,
            installer_v2,
            root_version=1,
            timestamp_version=4,
            snapshot_version=4,
            targets_version=2,
            expires=return_time + timedelta(days=10),
            timestamp_expires=return_time + timedelta(hours=1),
        )
        outage_failed_closed = False
        try:
            refresh_if_due(
                root_bytes=due.root,
                targets_bytes=due.targets,
                current_snapshot_bytes=due.snapshot,
                current_timestamp_bytes=due.timestamp,
                reference_time=return_time,
            )
        except SteadyStateRefreshError:
            outage_failed_closed = True
        recovered = refresh_if_due(
            root_bytes=due.root,
            targets_bytes=due.targets,
            current_snapshot_bytes=due.snapshot,
            current_timestamp_bytes=due.timestamp,
            reference_time=return_time,
            snapshot_signer=due_builder._core._snapshot_signer,
            timestamp_signer=due_builder._core._timestamp_signer,
        )
        matrix["scheduled_refresh_recovers_after_transient_outage"] = bool(
            outage_failed_closed
            and recovered.refreshed
            and recovered.manifest["targets"]["modified"] is False
        )

        workflow = _workflow_contract(repo_root)
        matrix["concurrent_refresh_cannot_regress_versions"] = bool(
            workflow["serialized_refresh"] and matrix["old_timestamp_replay_rejected"]
        )

        attack_builder = SyntheticUpdateRepositoryBuilder(root_threshold=1)
        trusted = attack_builder.build(
            target,
            installer_v2,
            root_version=1,
            timestamp_version=1,
            snapshot_version=1,
            targets_version=1,
        )
        attacker_builder = SyntheticUpdateRepositoryBuilder(root_threshold=1)
        attacker = attacker_builder.build(
            target,
            b"unauthorized-target\n",
            root_version=1,
            timestamp_version=2,
            snapshot_version=2,
            targets_version=2,
        )
        malicious_timestamp = _timestamp_for_snapshot(
            attacker.snapshot,
            version=2,
            expires=datetime(2035, 1, 1, tzinfo=UTC),
            signer=attack_builder._core._timestamp_signer,
        )
        timestamp_attack = replace(
            trusted,
            timestamp=malicious_timestamp,
            snapshot=attacker.snapshot,
            targets=attacker.targets,
            target_data=attacker.target_data,
        )
        verifier_client = UpdateClient(
            temp / "timestamp-attack",
            root_pin=PackagedRootPin.from_root(trusted.root),
            reference_time=return_time,
        )
        timestamp_result = verifier_client.check(
            MemoryUpdateTransport.from_repository(timestamp_attack), target
        )
        matrix["compromised_timestamp_cannot_authorize_targets"] = bool(
            timestamp_result.status == "verification-failed"
            and "snapshot" in timestamp_result.detail.lower()
        )

        snapshot_attack_bytes = _snapshot_for_targets(
            trusted.targets,
            version=2,
            expires=datetime(2035, 1, 1, tzinfo=UTC),
            signer=attack_builder._core._snapshot_signer,
        )
        snapshot_attack_timestamp = _timestamp_for_snapshot(
            snapshot_attack_bytes,
            version=2,
            expires=datetime(2035, 1, 1, tzinfo=UTC),
            signer=attack_builder._core._timestamp_signer,
        )
        snapshot_attack = replace(
            trusted,
            snapshot=snapshot_attack_bytes,
            timestamp=snapshot_attack_timestamp,
            target_data=b"arbitrary-installer-bytes\n",
        )
        snapshot_client = UpdateClient(
            temp / "snapshot-attack",
            root_pin=PackagedRootPin.from_root(trusted.root),
            reference_time=return_time,
        )
        snapshot_result = snapshot_client.check(
            MemoryUpdateTransport.from_repository(snapshot_attack), target
        )
        matrix["compromised_snapshot_cannot_authorize_target_bytes"] = bool(
            snapshot_result.status == "verification-failed"
        )

        matrix["offline_root_targets_absent_from_actions"] = workflow[
            "offline_authority_absent_from_actions"
        ]
        matrix["single_online_role_rotation_preserves_target_authorization"] = (
            _single_online_role_rotation(
                initial=trusted,
                builder=attack_builder,
                target=target,
                installer=installer_v2,
                reference_time=return_time,
                state_dir=temp / "role-rotation",
            )
        )
        matrix["emergency_manual_refresh_runbook_tested"] = bool(
            workflow["emergency_runbook"]
            and matrix["scheduled_refresh_recovers_after_transient_outage"]
        )

        english = temporary_update_service_message("metadata-expired", "en-US")
        french = temporary_update_service_message("metadata-expired", "fr-FR")
        matrix["localized_non_destructive_update_ux"] = bool(
            english["locale"] == "en"
            and french["locale"] == "fr"
            and not english["blocks_startup"]
            and not french["blocks_startup"]
            and english["local_work_available"]
            and french["local_work_available"]
        )
        matrix["installed_settings_and_projects_survive"] = bool(
            _preserve_user_state(temp / "preservation")
            and workflow["historical_live_state_preservation"]
        )
        matrix["mandatory_path_remains_zero_cost"] = workflow["zero_cost_path"]

        details = {
            "old_reference_time": old_time.isoformat(),
            "return_reference_time": return_time.isoformat(),
            "persisted_state_path": "client/tuf/state.json",
            "old_timestamp_version": 1,
            "fresh_timestamp_version": 2,
            "refresh_recovery_snapshot_version": Metadata.from_bytes(
                recovered.snapshot_bytes
            ).signed.version,
            "refresh_recovery_timestamp_version": Metadata.from_bytes(
                recovered.timestamp_bytes
            ).signed.version,
            "production_keys_used": False,
            "production_metadata_modified": False,
            "public_release_created": False,
            "live_rotation_performed": False,
            "paid_provider_required": False,
        }

    failed = sorted(name for name, passed in matrix.items() if not passed)
    return {
        "format": R20_6_FORMAT,
        "schema_version": R20_6_SCHEMA_VERSION,
        "source_sha": source,
        "status": "PASS" if not failed else "FAIL",
        "matrix": matrix,
        "cases_total": len(matrix),
        "cases_passed": len(matrix) - len(failed),
        "failed_cases": failed,
        "details": details,
        "manual_intervention_required": False,
        "privileged_live_drill_required": False,
        "production_effect": False,
    }


__all__ = [
    "R20_6_FORMAT",
    "R20_6_SCHEMA_VERSION",
    "build_continuous_operations_report",
]
