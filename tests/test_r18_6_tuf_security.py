from __future__ import annotations

from datetime import datetime, timezone

import pytest

from kodepoia.release.tuf_security import (
    SyntheticTufRepositoryBuilder,
    TufUpdateVerifier,
    TufVerificationError,
)

REFERENCE_TIME = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


def _versions(state) -> tuple[int, int, int, int]:
    return (
        state.root_version,
        state.timestamp_version,
        state.snapshot_version,
        state.targets_version,
    )


def test_valid_update_from_persisted_trusted_state_passes(tmp_path) -> None:
    builder = SyntheticTufRepositoryBuilder()
    first = builder.build(timestamp_version=1, snapshot_version=1, targets_version=1)
    verifier = TufUpdateVerifier(tmp_path, reference_time=REFERENCE_TIME)
    assert _versions(verifier.verify(first, bootstrap_root=first.root)) == (1, 1, 1, 1)

    second = builder.build(
        timestamp_version=2,
        snapshot_version=2,
        targets_version=2,
        target_data=b'{"release":"v1.1.0-rc2"}\n',
    )
    assert _versions(verifier.verify(second)) == (1, 2, 2, 2)


def test_timestamp_rollback_is_refused_and_state_is_not_replaced(tmp_path) -> None:
    builder = SyntheticTufRepositoryBuilder()
    trusted = builder.build(timestamp_version=2, snapshot_version=2, targets_version=2)
    verifier = TufUpdateVerifier(tmp_path, reference_time=REFERENCE_TIME)
    verifier.verify(trusted, bootstrap_root=trusted.root)

    rollback = builder.build(timestamp_version=1, snapshot_version=3, targets_version=3)
    with pytest.raises(TufVerificationError, match="timestamp rollback"):
        verifier.verify(rollback)
    assert verifier.load_state().timestamp_version == 2


def test_snapshot_rollback_is_refused(tmp_path) -> None:
    builder = SyntheticTufRepositoryBuilder()
    trusted = builder.build(timestamp_version=2, snapshot_version=2, targets_version=2)
    verifier = TufUpdateVerifier(tmp_path, reference_time=REFERENCE_TIME)
    verifier.verify(trusted, bootstrap_root=trusted.root)

    rollback = builder.build(timestamp_version=3, snapshot_version=1, targets_version=3)
    with pytest.raises(TufVerificationError, match="snapshot rollback"):
        verifier.verify(rollback)


def test_expired_timestamp_freeze_is_refused_with_fixed_clock(tmp_path) -> None:
    builder = SyntheticTufRepositoryBuilder()
    trusted = builder.build(timestamp_version=1, snapshot_version=1, targets_version=1)
    verifier = TufUpdateVerifier(tmp_path, reference_time=REFERENCE_TIME)
    verifier.verify(trusted, bootstrap_root=trusted.root)

    expired = builder.build(
        timestamp_version=2,
        snapshot_version=2,
        targets_version=2,
        timestamp_expires=datetime(2026, 9, 4, tzinfo=timezone.utc),
    )
    with pytest.raises(TufVerificationError, match="timestamp metadata is expired"):
        verifier.verify(expired)


def test_targets_metadata_wrong_digest_is_refused(tmp_path) -> None:
    builder = SyntheticTufRepositoryBuilder()
    trusted = builder.build(timestamp_version=1, snapshot_version=1, targets_version=1)
    verifier = TufUpdateVerifier(tmp_path, reference_time=REFERENCE_TIME)
    verifier.verify(trusted, bootstrap_root=trusted.root)

    corrupted = builder.build(
        timestamp_version=2,
        snapshot_version=2,
        targets_version=2,
        corrupt_targets_reference=True,
    )
    with pytest.raises(TufVerificationError, match="targets metadata hash/length"):
        verifier.verify(corrupted)


def test_root_without_required_threshold_is_refused(tmp_path) -> None:
    builder = SyntheticTufRepositoryBuilder(root_threshold=2)
    trusted = builder.build(
        root_version=1,
        timestamp_version=1,
        snapshot_version=1,
        targets_version=1,
    )
    verifier = TufUpdateVerifier(tmp_path, reference_time=REFERENCE_TIME)
    verifier.verify(trusted, bootstrap_root=trusted.root)

    under_signed = builder.build(
        root_version=2,
        root_signature_count=1,
        timestamp_version=2,
        snapshot_version=2,
        targets_version=2,
    )
    with pytest.raises(TufVerificationError, match="root metadata did not satisfy"):
        verifier.verify(under_signed)


def test_trusted_state_is_restored_after_restart(tmp_path) -> None:
    builder = SyntheticTufRepositoryBuilder()
    first = builder.build(timestamp_version=1, snapshot_version=1, targets_version=1)
    first_process = TufUpdateVerifier(tmp_path, reference_time=REFERENCE_TIME)
    first_process.verify(first, bootstrap_root=first.root)

    second = builder.build(
        timestamp_version=2,
        snapshot_version=2,
        targets_version=2,
        target_data=b'{"release":"restart-proof"}\n',
    )
    restarted_process = TufUpdateVerifier(tmp_path, reference_time=REFERENCE_TIME)
    state = restarted_process.verify(second)
    assert _versions(state) == (1, 2, 2, 2)
    assert restarted_process.load_state() == state


def test_snapshot_hash_reference_mismatch_is_refused(tmp_path) -> None:
    builder = SyntheticTufRepositoryBuilder()
    first = builder.build(timestamp_version=1, snapshot_version=1, targets_version=1)
    verifier = TufUpdateVerifier(tmp_path, reference_time=REFERENCE_TIME)
    verifier.verify(first, bootstrap_root=first.root)

    corrupted = builder.build(
        timestamp_version=2,
        snapshot_version=2,
        targets_version=2,
        corrupt_snapshot_reference=True,
    )
    with pytest.raises(TufVerificationError, match="snapshot metadata hash/length"):
        verifier.verify(corrupted)
