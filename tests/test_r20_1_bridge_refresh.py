from __future__ import annotations

import hashlib
from datetime import UTC, datetime

import pytest
from securesystemslib.signer import CryptoSigner
from tuf.api.metadata import Metadata, Root, Snapshot, Timestamp

from kodepoia.update.bridge_refresh import BridgeRefreshError, build_bridge_metadata


def _serialize(metadata: Metadata[object]) -> bytes:
    return metadata.to_bytes() + b"\n"


def _signed(payload: dict[str, object], signer: CryptoSigner) -> bytes:
    metadata = Metadata.from_dict({"signatures": [], "signed": payload})
    metadata.sign(signer)
    return _serialize(metadata)


def _fixture() -> dict[str, object]:
    root_signer = CryptoSigner.generate_ed25519()
    targets_signer = CryptoSigner.generate_ed25519()
    snapshot_signer = CryptoSigner.generate_ed25519()
    timestamp_signer = CryptoSigner.generate_ed25519()
    expires = "2027-09-01T00:00:00Z"
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
            "expires": expires,
            "keys": keys,
            "roles": roles,
            "spec_version": "1.0.31",
            "version": 1,
        },
        root_signer,
    )
    targets_bytes = _signed(
        {
            "_type": "targets",
            "expires": expires,
            "spec_version": "1.0.31",
            "targets": {},
            "version": 2,
        },
        targets_signer,
    )
    snapshot_bytes = _signed(
        {
            "_type": "snapshot",
            "expires": "2026-09-09T17:32:00Z",
            "meta": {
                "targets.json": {
                    "hashes": {"sha256": hashlib.sha256(targets_bytes).hexdigest()},
                    "length": len(targets_bytes),
                    "version": 2,
                }
            },
            "spec_version": "1.0.31",
            "version": 2,
        },
        snapshot_signer,
    )
    timestamp_bytes = _signed(
        {
            "_type": "timestamp",
            "expires": "2026-09-09T17:32:00Z",
            "meta": {
                "snapshot.json": {
                    "hashes": {"sha256": hashlib.sha256(snapshot_bytes).hexdigest()},
                    "length": len(snapshot_bytes),
                    "version": 2,
                }
            },
            "spec_version": "1.0.31",
            "version": 2,
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


def _build(fixture: dict[str, object]):
    return build_bridge_metadata(
        root_bytes=fixture["root"],
        targets_bytes=fixture["targets"],
        current_snapshot_bytes=fixture["snapshot"],
        current_timestamp_bytes=fixture["timestamp"],
        snapshot_signer=fixture["snapshot_signer"],
        timestamp_signer=fixture["timestamp_signer"],
        reference_time=datetime(2026, 9, 8, 20, 0, tzinfo=UTC),
    )


def test_bridge_advances_only_snapshot_and_timestamp() -> None:
    fixture = _fixture()
    result = _build(fixture)
    snapshot = Metadata.from_bytes(result.snapshot_bytes)
    timestamp = Metadata.from_bytes(result.timestamp_bytes)
    assert isinstance(snapshot.signed, Snapshot)
    assert isinstance(timestamp.signed, Timestamp)
    assert snapshot.signed.version == 3
    assert timestamp.signed.version == 3
    assert snapshot.signed.expires == datetime(2026, 10, 8, 20, 0, tzinfo=UTC)
    assert timestamp.signed.expires == datetime(2026, 10, 8, 20, 0, tzinfo=UTC)
    assert result.manifest["root"]["modified"] is False
    assert result.manifest["targets"]["modified"] is False


def test_bridge_binds_exact_targets_then_exact_snapshot() -> None:
    fixture = _fixture()
    result = _build(fixture)
    snapshot = Metadata.from_bytes(result.snapshot_bytes)
    timestamp = Metadata.from_bytes(result.timestamp_bytes)
    targets_ref = snapshot.signed.meta["targets.json"]
    targets_ref.verify_length_and_hashes(fixture["targets"])
    timestamp.signed.snapshot_meta.verify_length_and_hashes(result.snapshot_bytes)
    assert targets_ref.version == 2
    assert timestamp.signed.snapshot_meta.version == 3


def test_bridge_signatures_are_authorized_by_root() -> None:
    fixture = _fixture()
    result = _build(fixture)
    root = Metadata.from_bytes(fixture["root"])
    snapshot = Metadata.from_bytes(result.snapshot_bytes)
    timestamp = Metadata.from_bytes(result.timestamp_bytes)
    assert isinstance(root.signed, Root)
    root.signed.verify_delegate("snapshot", snapshot.signed_bytes, snapshot.signatures)
    root.signed.verify_delegate("timestamp", timestamp.signed_bytes, timestamp.signatures)


def test_bridge_rejects_wrong_snapshot_key() -> None:
    fixture = _fixture()
    fixture["snapshot_signer"] = CryptoSigner.generate_ed25519()
    with pytest.raises(BridgeRefreshError, match="Snapshot signer"):
        _build(fixture)


def test_bridge_rejects_wrong_timestamp_key() -> None:
    fixture = _fixture()
    fixture["timestamp_signer"] = CryptoSigner.generate_ed25519()
    with pytest.raises(BridgeRefreshError, match="Timestamp signer"):
        _build(fixture)


def test_bridge_rejects_mutated_targets_bytes() -> None:
    fixture = _fixture()
    fixture["targets"] = fixture["targets"] + b" "
    with pytest.raises(BridgeRefreshError, match="current targets"):
        _build(fixture)


def test_bridge_lifetime_is_bounded() -> None:
    fixture = _fixture()
    with pytest.raises(BridgeRefreshError, match="bridge lifetime"):
        build_bridge_metadata(
            root_bytes=fixture["root"],
            targets_bytes=fixture["targets"],
            current_snapshot_bytes=fixture["snapshot"],
            current_timestamp_bytes=fixture["timestamp"],
            snapshot_signer=fixture["snapshot_signer"],
            timestamp_signer=fixture["timestamp_signer"],
            reference_time=datetime(2026, 9, 8, 20, 0, tzinfo=UTC),
            bridge_days=365,
        )
