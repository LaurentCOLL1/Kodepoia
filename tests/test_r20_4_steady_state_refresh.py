from __future__ import annotations

import hashlib
from datetime import UTC, datetime

import pytest
from securesystemslib.signer import CryptoSigner
from tuf.api.metadata import Metadata, Root, Snapshot, Timestamp

from kodepoia.update.steady_state_refresh import (
    REFRESH_THRESHOLD_HOURS,
    SNAPSHOT_EXPIRY_HOURS,
    TIMESTAMP_EXPIRY_HOURS,
    SteadyStateRefreshError,
    build_steady_state_metadata,
    evaluate_refresh,
    refresh_if_due,
)


def _serialize(metadata: Metadata[object]) -> bytes:
    return metadata.to_bytes() + b"\n"


def _signed(payload: dict[str, object], signer: CryptoSigner) -> bytes:
    metadata = Metadata.from_dict({"signatures": [], "signed": payload})
    metadata.sign(signer)
    return _serialize(metadata)


def _fixture(*, online_expires: str) -> dict[str, object]:
    root_signer = CryptoSigner.generate_ed25519()
    targets_signer = CryptoSigner.generate_ed25519()
    snapshot_signer = CryptoSigner.generate_ed25519()
    timestamp_signer = CryptoSigner.generate_ed25519()
    authority_expires = "2027-09-10T00:00:00Z"
    signers = {
        "root": root_signer,
        "targets": targets_signer,
        "snapshot": snapshot_signer,
        "timestamp": timestamp_signer,
    }
    keys = {signer.public_key.keyid: signer.public_key.to_dict() for signer in signers.values()}
    roles = {
        role: {"keyids": [signer.public_key.keyid], "threshold": 1}
        for role, signer in signers.items()
    }
    root_bytes = _signed(
        {
            "_type": "root",
            "consistent_snapshot": False,
            "expires": authority_expires,
            "keys": keys,
            "roles": roles,
            "spec_version": "1.0.31",
            "version": 2,
        },
        root_signer,
    )
    targets_bytes = _signed(
        {
            "_type": "targets",
            "expires": authority_expires,
            "spec_version": "1.0.31",
            "targets": {},
            "version": 2,
        },
        targets_signer,
    )
    snapshot_bytes = _signed(
        {
            "_type": "snapshot",
            "expires": online_expires,
            "meta": {
                "targets.json": {
                    "hashes": {"sha256": hashlib.sha256(targets_bytes).hexdigest()},
                    "length": len(targets_bytes),
                    "version": 2,
                }
            },
            "spec_version": "1.0.31",
            "version": 4,
        },
        snapshot_signer,
    )
    timestamp_bytes = _signed(
        {
            "_type": "timestamp",
            "expires": online_expires,
            "meta": {
                "snapshot.json": {
                    "hashes": {"sha256": hashlib.sha256(snapshot_bytes).hexdigest()},
                    "length": len(snapshot_bytes),
                    "version": 4,
                }
            },
            "spec_version": "1.0.31",
            "version": 4,
        },
        timestamp_signer,
    )
    return {
        "root": root_bytes,
        "targets": targets_bytes,
        "snapshot": snapshot_bytes,
        "timestamp": timestamp_bytes,
        "snapshot_signer": snapshot_signer,
        "timestamp_signer": timestamp_signer,
    }


def _decision(fixture: dict[str, object], now: datetime):
    return evaluate_refresh(
        root_bytes=fixture["root"],
        targets_bytes=fixture["targets"],
        snapshot_bytes=fixture["snapshot"],
        timestamp_bytes=fixture["timestamp"],
        reference_time=now,
    )


def _refresh(fixture: dict[str, object], now: datetime):
    return refresh_if_due(
        root_bytes=fixture["root"],
        targets_bytes=fixture["targets"],
        current_snapshot_bytes=fixture["snapshot"],
        current_timestamp_bytes=fixture["timestamp"],
        reference_time=now,
        snapshot_signer=fixture["snapshot_signer"],
        timestamp_signer=fixture["timestamp_signer"],
    )


def test_fresh_pair_is_idempotent_and_does_not_require_signers() -> None:
    now = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    fixture = _fixture(online_expires="2026-09-13T12:00:00Z")
    decision = _decision(fixture, now)
    assert not decision.refresh_required
    result = refresh_if_due(
        root_bytes=fixture["root"],
        targets_bytes=fixture["targets"],
        current_snapshot_bytes=fixture["snapshot"],
        current_timestamp_bytes=fixture["timestamp"],
        reference_time=now,
    )
    assert not result.refreshed
    assert result.snapshot_bytes == fixture["snapshot"]
    assert result.timestamp_bytes == fixture["timestamp"]


def test_pair_becomes_due_at_policy_threshold() -> None:
    now = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    fixture = _fixture(online_expires="2026-09-11T12:00:00Z")
    decision = _decision(fixture, now)
    assert decision.refresh_required
    assert decision.threshold_seconds == REFRESH_THRESHOLD_HOURS * 60 * 60


def test_refresh_advances_versions_and_applies_72h_48h_policy() -> None:
    now = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    fixture = _fixture(online_expires="2026-09-11T11:59:59Z")
    result = _refresh(fixture, now)
    assert result.refreshed
    snapshot = Metadata.from_bytes(result.snapshot_bytes)
    timestamp = Metadata.from_bytes(result.timestamp_bytes)
    assert isinstance(snapshot.signed, Snapshot)
    assert isinstance(timestamp.signed, Timestamp)
    assert snapshot.signed.version == 5
    assert timestamp.signed.version == 5
    assert snapshot.signed.expires == datetime(2026, 9, 13, 12, 0, tzinfo=UTC)
    assert timestamp.signed.expires == datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
    assert SNAPSHOT_EXPIRY_HOURS == 72
    assert TIMESTAMP_EXPIRY_HOURS == 48


def test_refresh_binds_exact_targets_then_exact_signed_snapshot() -> None:
    now = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    fixture = _fixture(online_expires="2026-09-11T00:00:00Z")
    result = _refresh(fixture, now)
    snapshot = Metadata.from_bytes(result.snapshot_bytes)
    timestamp = Metadata.from_bytes(result.timestamp_bytes)
    snapshot.signed.meta["targets.json"].verify_length_and_hashes(fixture["targets"])
    timestamp.signed.snapshot_meta.verify_length_and_hashes(result.snapshot_bytes)
    assert snapshot.signed.meta["targets.json"].version == 2
    assert timestamp.signed.snapshot_meta.version == 5


def test_refreshed_signatures_are_authorized_by_root_and_distinct() -> None:
    now = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    fixture = _fixture(online_expires="2026-09-11T00:00:00Z")
    result = _refresh(fixture, now)
    root = Metadata.from_bytes(fixture["root"])
    snapshot = Metadata.from_bytes(result.snapshot_bytes)
    timestamp = Metadata.from_bytes(result.timestamp_bytes)
    assert isinstance(root.signed, Root)
    root.signed.verify_delegate("snapshot", snapshot.signed_bytes, snapshot.signatures)
    root.signed.verify_delegate("timestamp", timestamp.signed_bytes, timestamp.signatures)
    assert fixture["snapshot_signer"].public_key.keyid != fixture["timestamp_signer"].public_key.keyid


def test_expired_online_pair_can_recover_while_offline_authority_is_valid() -> None:
    now = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    fixture = _fixture(online_expires="2026-09-10T11:00:00Z")
    result = _refresh(fixture, now)
    assert result.refreshed
    decision = evaluate_refresh(
        root_bytes=fixture["root"],
        targets_bytes=fixture["targets"],
        snapshot_bytes=result.snapshot_bytes,
        timestamp_bytes=result.timestamp_bytes,
        reference_time=now,
    )
    assert not decision.refresh_required


def test_due_refresh_requires_both_online_signers() -> None:
    now = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    fixture = _fixture(online_expires="2026-09-11T00:00:00Z")
    with pytest.raises(SteadyStateRefreshError, match="both online role signers"):
        refresh_if_due(
            root_bytes=fixture["root"],
            targets_bytes=fixture["targets"],
            current_snapshot_bytes=fixture["snapshot"],
            current_timestamp_bytes=fixture["timestamp"],
            reference_time=now,
        )


def test_wrong_snapshot_signer_fails_closed() -> None:
    now = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    fixture = _fixture(online_expires="2026-09-11T00:00:00Z")
    with pytest.raises(SteadyStateRefreshError, match="Snapshot signer"):
        build_steady_state_metadata(
            root_bytes=fixture["root"],
            targets_bytes=fixture["targets"],
            current_snapshot_bytes=fixture["snapshot"],
            current_timestamp_bytes=fixture["timestamp"],
            snapshot_signer=CryptoSigner.generate_ed25519(),
            timestamp_signer=fixture["timestamp_signer"],
            reference_time=now,
        )


def test_mutated_targets_or_snapshot_view_fails_closed() -> None:
    now = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    fixture = _fixture(online_expires="2026-09-11T00:00:00Z")
    with pytest.raises(SteadyStateRefreshError, match="targets.json"):
        evaluate_refresh(
            root_bytes=fixture["root"],
            targets_bytes=fixture["targets"] + b" ",
            snapshot_bytes=fixture["snapshot"],
            timestamp_bytes=fixture["timestamp"],
            reference_time=now,
        )
    with pytest.raises(SteadyStateRefreshError, match="snapshot.json"):
        evaluate_refresh(
            root_bytes=fixture["root"],
            targets_bytes=fixture["targets"],
            snapshot_bytes=fixture["snapshot"] + b" ",
            timestamp_bytes=fixture["timestamp"],
            reference_time=now,
        )


def test_refresh_never_extends_beyond_root_or_targets_authority() -> None:
    now = datetime(2027, 9, 8, 12, 0, tzinfo=UTC)
    fixture = _fixture(online_expires="2027-09-08T13:00:00Z")
    with pytest.raises(SteadyStateRefreshError, match="earlier than Root and Targets"):
        _refresh(fixture, now)
