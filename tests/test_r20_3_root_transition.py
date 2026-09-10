from __future__ import annotations

import hashlib
from datetime import UTC, datetime

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from securesystemslib.signer import CryptoSigner
from tuf.api.metadata import Metadata, Root, Snapshot, Timestamp

from kodepoia.update.online_signing import OnlineSignerConfig, build_root_rotation_package
from kodepoia.update.root_transition import (
    RootTransitionError,
    build_root_online_role_transition,
)
from kodepoia.update.zero_cost_signing import sign_root_rotation


def _signer(seed: int) -> CryptoSigner:
    return CryptoSigner(Ed25519PrivateKey.from_private_bytes(bytes([seed]) * 32))


def _serialize(metadata: Metadata[object]) -> bytes:
    return metadata.to_bytes() + b"\n"


def _signed_metadata(payload: dict[str, object], signer: CryptoSigner) -> bytes:
    metadata = Metadata.from_dict({"signatures": [], "signed": payload})
    metadata.sign(signer)
    return _serialize(metadata)


def _fixture() -> dict[str, object]:
    signers = {
        "root-1": _signer(1),
        "root-2": _signer(2),
        "root-3": _signer(3),
        "targets": _signer(4),
        "old-snapshot": _signer(5),
        "old-timestamp": _signer(6),
        "new-snapshot": _signer(20),
        "new-timestamp": _signer(21),
    }
    keys = {
        signer.public_key.keyid: signer.public_key.to_dict()
        for signer in signers.values()
        if not name_is_new_online(signer, signers)
    }
    root_keyids = [
        signers[name].public_key.keyid for name in ("root-1", "root-2", "root-3")
    ]
    root_payload: dict[str, object] = {
        "_type": "root",
        "consistent_snapshot": False,
        "expires": "2027-09-08T14:59:19Z",
        "keys": keys,
        "roles": {
            "root": {"keyids": root_keyids, "threshold": 2},
            "targets": {
                "keyids": [signers["targets"].public_key.keyid],
                "threshold": 1,
            },
            "snapshot": {
                "keyids": [signers["old-snapshot"].public_key.keyid],
                "threshold": 1,
            },
            "timestamp": {
                "keyids": [signers["old-timestamp"].public_key.keyid],
                "threshold": 1,
            },
        },
        "spec_version": "1.0.31",
        "version": 1,
    }
    root = Metadata.from_dict({"signatures": [], "signed": root_payload})
    root.sign(signers["root-1"])
    root.sign(signers["root-2"], append=True)
    root_bytes = _serialize(root)

    targets_payload: dict[str, object] = {
        "_type": "targets",
        "expires": "2027-09-08T17:32:00Z",
        "spec_version": "1.0.31",
        "targets": {},
        "version": 2,
    }
    targets_bytes = _signed_metadata(targets_payload, signers["targets"])

    expiry = "2026-10-08T21:44:18Z"
    snapshot_payload: dict[str, object] = {
        "_type": "snapshot",
        "expires": expiry,
        "meta": {
            "targets.json": {
                "hashes": {"sha256": hashlib.sha256(targets_bytes).hexdigest()},
                "length": len(targets_bytes),
                "version": 2,
            }
        },
        "spec_version": "1.0.31",
        "version": 3,
    }
    snapshot_bytes = _signed_metadata(snapshot_payload, signers["old-snapshot"])
    timestamp_payload: dict[str, object] = {
        "_type": "timestamp",
        "expires": expiry,
        "meta": {
            "snapshot.json": {
                "hashes": {"sha256": hashlib.sha256(snapshot_bytes).hexdigest()},
                "length": len(snapshot_bytes),
                "version": 3,
            }
        },
        "spec_version": "1.0.31",
        "version": 3,
    }
    timestamp_bytes = _signed_metadata(timestamp_payload, signers["old-timestamp"])

    snapshot_config = OnlineSignerConfig(
        role="snapshot",
        provider="github-environment-secret",
        resource="TUF_SNAPSHOT_ED25519_SEED_B64",
        public_key=signers["new-snapshot"].public_key,
    )
    timestamp_config = OnlineSignerConfig(
        role="timestamp",
        provider="github-environment-secret",
        resource="TUF_TIMESTAMP_ED25519_SEED_B64",
        public_key=signers["new-timestamp"].public_key,
    )
    rotation = build_root_rotation_package(
        current_root_bytes=root_bytes,
        snapshot=snapshot_config,
        timestamp=timestamp_config,
    )
    signed_root = sign_root_rotation(
        current_root_bytes=root_bytes,
        unsigned_root_bytes=rotation.unsigned_root_bytes,
        root_signers=[signers["root-1"], signers["root-2"]],
    ).signed_root_bytes
    return {
        "signers": signers,
        "root": root_bytes,
        "signed_root": signed_root,
        "targets": targets_bytes,
        "snapshot": snapshot_bytes,
        "timestamp": timestamp_bytes,
    }


def name_is_new_online(signer: CryptoSigner, signers: dict[str, CryptoSigner]) -> bool:
    return signer in (signers["new-snapshot"], signers["new-timestamp"])


def test_transition_rotates_online_signatures_without_extending_bridge_expiry() -> None:
    fixture = _fixture()
    signers = fixture["signers"]
    result = build_root_online_role_transition(
        current_root_bytes=fixture["root"],
        signed_root_v2_bytes=fixture["signed_root"],
        targets_bytes=fixture["targets"],
        current_snapshot_bytes=fixture["snapshot"],
        current_timestamp_bytes=fixture["timestamp"],
        snapshot_signer=signers["new-snapshot"],
        timestamp_signer=signers["new-timestamp"],
        reference_time=datetime(2026, 9, 9, 12, tzinfo=UTC),
    )

    root_v2 = Metadata.from_bytes(result.root_bytes)
    snapshot_v4 = Metadata.from_bytes(result.snapshot_bytes)
    timestamp_v4 = Metadata.from_bytes(result.timestamp_bytes)
    assert isinstance(root_v2.signed, Root)
    assert isinstance(snapshot_v4.signed, Snapshot)
    assert isinstance(timestamp_v4.signed, Timestamp)
    assert root_v2.signed.version == 2
    assert snapshot_v4.signed.version == 4
    assert timestamp_v4.signed.version == 4
    assert result.manifest["expiry_extended"] is False
    assert result.manifest["expires"] == "2026-10-08T21:44:18Z"
    assert result.manifest["targets"]["modified"] is False
    assert result.manifest["root"]["old_root_threshold_verified"] is True
    assert result.manifest["root"]["new_root_threshold_verified"] is True
    assert result.manifest["private_material_in_output"] is False
    assert result.manifest["production_effect"] is False

    root_v2.signed.verify_delegate(
        "snapshot", snapshot_v4.signed_bytes, snapshot_v4.signatures
    )
    root_v2.signed.verify_delegate(
        "timestamp", timestamp_v4.signed_bytes, timestamp_v4.signatures
    )
    snapshot_v4.signed.meta["targets.json"].verify_length_and_hashes(fixture["targets"])
    timestamp_v4.signed.snapshot_meta.verify_length_and_hashes(result.snapshot_bytes)


def test_transition_rejects_old_online_signer_after_root_rotation() -> None:
    fixture = _fixture()
    signers = fixture["signers"]
    with pytest.raises(RootTransitionError, match="Snapshot signer is not authorized"):
        build_root_online_role_transition(
            current_root_bytes=fixture["root"],
            signed_root_v2_bytes=fixture["signed_root"],
            targets_bytes=fixture["targets"],
            current_snapshot_bytes=fixture["snapshot"],
            current_timestamp_bytes=fixture["timestamp"],
            snapshot_signer=signers["old-snapshot"],
            timestamp_signer=signers["new-timestamp"],
            reference_time=datetime(2026, 9, 9, 12, tzinfo=UTC),
        )
