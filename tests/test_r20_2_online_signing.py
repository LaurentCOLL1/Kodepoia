from __future__ import annotations

import json
from dataclasses import replace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from securesystemslib.signer import CryptoSigner
from tuf.api.metadata import Metadata, Root

from kodepoia.update.online_signing import (
    OnlineSignerConfig,
    OnlineSigningError,
    SyntheticSignerResolver,
    build_root_rotation_package,
    import_public_key_pem,
    resolve_online_signers,
    verify_signed_root_rotation,
)


def _signer(seed: int) -> CryptoSigner:
    return CryptoSigner(Ed25519PrivateKey.from_private_bytes(bytes([seed]) * 32))


def _serialize(metadata: Metadata[object]) -> bytes:
    return metadata.to_bytes() + b"\n"


def _root_fixture() -> tuple[bytes, dict[str, CryptoSigner]]:
    signers = {
        "root-1": _signer(1),
        "root-2": _signer(2),
        "root-3": _signer(3),
        "targets": _signer(4),
        "snapshot": _signer(5),
        "timestamp": _signer(6),
    }
    keys = {
        signer.public_key.keyid: signer.public_key.to_dict()
        for signer in signers.values()
    }
    root_keyids = [signers[name].public_key.keyid for name in ("root-1", "root-2", "root-3")]
    payload: dict[str, object] = {
        "_type": "root",
        "consistent_snapshot": False,
        "expires": "2027-09-08T14:59:19Z",
        "keys": keys,
        "roles": {
            "root": {"keyids": root_keyids, "threshold": 2},
            "targets": {"keyids": [signers["targets"].public_key.keyid], "threshold": 1},
            "snapshot": {"keyids": [signers["snapshot"].public_key.keyid], "threshold": 1},
            "timestamp": {"keyids": [signers["timestamp"].public_key.keyid], "threshold": 1},
        },
        "spec_version": "1.0.31",
        "version": 1,
    }
    metadata = Metadata.from_dict({"signatures": [], "signed": payload})
    metadata.sign(signers["root-1"])
    metadata.sign(signers["root-2"], append=True)
    return _serialize(metadata), signers


def _configs() -> tuple[OnlineSignerConfig, OnlineSignerConfig, dict[str, CryptoSigner]]:
    snapshot_signer = _signer(20)
    timestamp_signer = _signer(21)
    snapshot = OnlineSignerConfig(
        role="snapshot",
        provider="synthetic",
        resource="ci/snapshot-key-v2",
        public_key=snapshot_signer.public_key,
    )
    timestamp = OnlineSignerConfig(
        role="timestamp",
        provider="synthetic",
        resource="ci/timestamp-key-v2",
        public_key=timestamp_signer.public_key,
    )
    return snapshot, timestamp, {
        snapshot.resource: snapshot_signer,
        timestamp.resource: timestamp_signer,
    }


def test_import_public_key_pem_derives_same_tuf_keyid() -> None:
    signer = _signer(30)
    pem = signer._private_key.public_key().public_bytes(  # noqa: SLF001 - deterministic CI fixture
        Encoding.PEM,
        PublicFormat.SubjectPublicKeyInfo,
    )
    imported = import_public_key_pem(pem)
    assert imported.keyid == signer.public_key.keyid
    assert imported.to_dict() == signer.public_key.to_dict()


def test_runtime_resolution_is_provider_neutral_and_fail_closed() -> None:
    snapshot, timestamp, signers = _configs()
    resolved = resolve_online_signers(
        [snapshot, timestamp], SyntheticSignerResolver(signers)
    )
    assert resolved.snapshot.public_key.keyid == snapshot.keyid
    assert resolved.timestamp.public_key.keyid == timestamp.keyid

    wrong = _signer(22)
    bad_resolver = SyntheticSignerResolver(
        {snapshot.resource: wrong, timestamp.resource: signers[timestamp.resource]}
    )
    with pytest.raises(OnlineSigningError, match="Snapshot|snapshot"):
        resolve_online_signers([snapshot, timestamp], bad_resolver)


def test_runtime_resolution_rejects_missing_duplicate_and_shared_identity() -> None:
    snapshot, timestamp, signers = _configs()
    resolver = SyntheticSignerResolver(signers)
    with pytest.raises(OnlineSigningError, match="missing"):
        resolve_online_signers([snapshot], resolver)
    with pytest.raises(OnlineSigningError, match="duplicate"):
        resolve_online_signers([snapshot, snapshot, timestamp], resolver)
    with pytest.raises(OnlineSigningError, match="different public keys"):
        resolve_online_signers(
            [snapshot, replace(timestamp, public_key=snapshot.public_key)], resolver
        )


def test_root_rotation_package_is_public_deterministic_and_scope_limited() -> None:
    current_root, _ = _root_fixture()
    snapshot, timestamp, _ = _configs()
    first = build_root_rotation_package(
        current_root_bytes=current_root,
        snapshot=snapshot,
        timestamp=timestamp,
    )
    second = build_root_rotation_package(
        current_root_bytes=current_root,
        snapshot=snapshot,
        timestamp=timestamp,
    )
    assert first == second
    assert first.package_id == first.manifest["package_id"]

    current = Metadata.from_bytes(current_root)
    proposed = Metadata.from_bytes(first.unsigned_root_bytes)
    assert isinstance(current.signed, Root)
    assert isinstance(proposed.signed, Root)
    assert proposed.signed.version == current.signed.version + 1
    assert proposed.signatures == {}
    assert proposed.signed.roles["root"] == current.signed.roles["root"]
    assert proposed.signed.roles["targets"] == current.signed.roles["targets"]
    assert proposed.signed.roles["snapshot"].threshold == 1
    assert proposed.signed.roles["timestamp"].threshold == 1
    assert proposed.signed.roles["snapshot"].keyids == [snapshot.keyid]
    assert proposed.signed.roles["timestamp"].keyids == [timestamp.keyid]
    assert snapshot.keyid != timestamp.keyid

    combined = first.unsigned_root_bytes + first.manifest_bytes
    assert b"PRIVATE KEY" not in combined.upper()
    assert b"PASSPHRASE" not in combined.upper()
    assert first.manifest["private_key_material_in_package"] is False
    assert first.manifest["production_effect"] is False


def test_rotation_package_rejects_non_rotation_and_secret_like_resource() -> None:
    current_root, signers = _root_fixture()
    snapshot, timestamp, _ = _configs()
    with pytest.raises(OnlineSigningError, match="Snapshot replacement"):
        build_root_rotation_package(
            current_root_bytes=current_root,
            snapshot=replace(snapshot, public_key=signers["snapshot"].public_key),
            timestamp=timestamp,
        )
    with pytest.raises(OnlineSigningError, match="secret material"):
        OnlineSignerConfig(
            role="snapshot",
            provider="synthetic",
            resource="kms/key?token=do-not-store-this",
            public_key=snapshot.public_key,
        )


def test_signed_root_rotation_requires_old_and_new_thresholds() -> None:
    current_root, root_signers = _root_fixture()
    snapshot, timestamp, _ = _configs()
    package = build_root_rotation_package(
        current_root_bytes=current_root,
        snapshot=snapshot,
        timestamp=timestamp,
    )
    candidate = Metadata.from_bytes(package.unsigned_root_bytes)
    candidate.sign(root_signers["root-1"])
    candidate.sign(root_signers["root-2"], append=True)
    candidate_bytes = _serialize(candidate)

    evidence = verify_signed_root_rotation(
        current_root_bytes=current_root,
        candidate_root_bytes=candidate_bytes,
    )
    assert evidence["current_version"] == 1
    assert evidence["candidate_version"] == 2
    assert evidence["old_root_threshold_verified"] is True
    assert evidence["new_root_threshold_verified"] is True
    assert evidence["offline_roles_preserved"] is True


def test_signed_root_rotation_rejects_single_old_root_signature() -> None:
    current_root, root_signers = _root_fixture()
    snapshot, timestamp, _ = _configs()
    package = build_root_rotation_package(
        current_root_bytes=current_root,
        snapshot=snapshot,
        timestamp=timestamp,
    )
    candidate = Metadata.from_bytes(package.unsigned_root_bytes)
    candidate.sign(root_signers["root-1"])
    with pytest.raises(OnlineSigningError, match="current Root threshold"):
        verify_signed_root_rotation(
            current_root_bytes=current_root,
            candidate_root_bytes=_serialize(candidate),
        )


def test_package_manifest_is_json_and_contains_only_public_identifiers() -> None:
    current_root, _ = _root_fixture()
    snapshot, timestamp, _ = _configs()
    package = build_root_rotation_package(
        current_root_bytes=current_root,
        snapshot=snapshot,
        timestamp=timestamp,
    )
    manifest = json.loads(package.manifest_bytes)
    assert manifest["online_roles"]["snapshot"]["resource"] == snapshot.resource
    assert manifest["online_roles"]["timestamp"]["resource"] == timestamp.resource
    assert manifest["offline_root_signatures_required"] == 2
    assert manifest["new_root_self_threshold_required"] == 2
