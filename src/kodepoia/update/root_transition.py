from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from securesystemslib.signer import Signer
from tuf.api.metadata import Metadata, Root, Snapshot, Targets, Timestamp

from kodepoia.update.online_signing import OnlineSigningError, verify_signed_root_rotation

TRANSITION_FORMAT = "kodepoia-r20-3-root-online-role-transition"
TRANSITION_SCHEMA_VERSION = 1


class RootTransitionError(ValueError):
    """Raised when the R20.3 Root/online-role transition is not safe."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _iso(value: datetime) -> str:
    return _as_utc(value).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(data: bytes, expected_type: type[Any], label: str) -> Metadata[Any]:
    try:
        metadata = Metadata.from_bytes(data)
    except Exception as exc:
        raise RootTransitionError(f"{label} is not valid TUF JSON: {exc}") from exc
    if not isinstance(metadata.signed, expected_type):
        raise RootTransitionError(f"{label} has unexpected metadata type")
    return metadata


def _verify_role(root: Root, role: str, metadata: Metadata[Any]) -> None:
    try:
        root.verify_delegate(role, metadata.signed_bytes, metadata.signatures)
    except Exception as exc:
        raise RootTransitionError(f"{role} metadata signature threshold failed: {exc}") from exc


def _verify_exact_reference(reference: Any, data: bytes, *, label: str) -> None:
    try:
        reference.verify_length_and_hashes(data)
    except Exception as exc:
        raise RootTransitionError(f"{label} hash/length binding failed: {exc}") from exc


def _serialize(metadata: Metadata[Any]) -> bytes:
    return metadata.to_bytes() + b"\n"


def _new_metadata(payload: dict[str, object], signer: Signer) -> bytes:
    envelope = Metadata.from_dict({"signatures": [], "signed": payload})
    envelope.sign(signer)
    return _serialize(envelope)


@dataclass(frozen=True, slots=True)
class RootTransitionResult:
    root_bytes: bytes
    snapshot_bytes: bytes
    timestamp_bytes: bytes
    manifest: dict[str, object]


def build_root_online_role_transition(
    *,
    current_root_bytes: bytes,
    signed_root_v2_bytes: bytes,
    targets_bytes: bytes,
    current_snapshot_bytes: bytes,
    current_timestamp_bytes: bytes,
    snapshot_signer: Signer,
    timestamp_signer: Signer,
    reference_time: datetime,
) -> RootTransitionResult:
    """Create the first Snapshot/Timestamp generation authorized by signed Root v2."""

    now = _as_utc(reference_time).replace(microsecond=0)
    current_root_md = _parse(current_root_bytes, Root, "current root.json")
    new_root_md = _parse(signed_root_v2_bytes, Root, "signed root v2")
    targets_md = _parse(targets_bytes, Targets, "targets.json")
    current_snapshot_md = _parse(current_snapshot_bytes, Snapshot, "current snapshot.json")
    current_timestamp_md = _parse(current_timestamp_bytes, Timestamp, "current timestamp.json")

    current_root = current_root_md.signed
    new_root = new_root_md.signed
    targets = targets_md.signed
    current_snapshot = current_snapshot_md.signed
    current_timestamp = current_timestamp_md.signed

    _verify_role(current_root, "root", current_root_md)
    _verify_role(current_root, "targets", targets_md)
    _verify_role(current_root, "snapshot", current_snapshot_md)
    _verify_role(current_root, "timestamp", current_timestamp_md)

    try:
        rotation_evidence = verify_signed_root_rotation(
            current_root_bytes=current_root_bytes,
            candidate_root_bytes=signed_root_v2_bytes,
        )
    except OnlineSigningError as exc:
        raise RootTransitionError(f"signed Root v2 transition verification failed: {exc}") from exc

    _verify_role(new_root, "root", new_root_md)
    _verify_role(new_root, "targets", targets_md)

    if current_root.is_expired(now) or new_root.is_expired(now):
        raise RootTransitionError("Root metadata is expired at transition time")
    if targets.is_expired(now):
        raise RootTransitionError("Targets metadata is expired at transition time")
    if current_snapshot.is_expired(now) or current_timestamp.is_expired(now):
        raise RootTransitionError("current online metadata is expired at transition time")

    current_targets_ref = current_snapshot.meta.get("targets.json")
    if current_targets_ref is None:
        raise RootTransitionError("current snapshot does not reference targets.json")
    if current_targets_ref.version != targets.version:
        raise RootTransitionError("current snapshot targets version does not match targets.json")
    _verify_exact_reference(current_targets_ref, targets_bytes, label="current targets")
    if current_timestamp.snapshot_meta.version != current_snapshot.version:
        raise RootTransitionError("current timestamp snapshot version mismatch")
    _verify_exact_reference(
        current_timestamp.snapshot_meta,
        current_snapshot_bytes,
        label="current snapshot",
    )

    snapshot_keyids = set(new_root.roles["snapshot"].keyids)
    timestamp_keyids = set(new_root.roles["timestamp"].keyids)
    if snapshot_signer.public_key.keyid not in snapshot_keyids:
        raise RootTransitionError("new Snapshot signer is not authorized by Root v2")
    if timestamp_signer.public_key.keyid not in timestamp_keyids:
        raise RootTransitionError("new Timestamp signer is not authorized by Root v2")
    if snapshot_signer.public_key.keyid == timestamp_signer.public_key.keyid:
        raise RootTransitionError("Snapshot and Timestamp must use distinct keys")

    transition_expiry = min(
        _as_utc(current_snapshot.expires),
        _as_utc(current_timestamp.expires),
    )
    authority_expiry = min(_as_utc(new_root.expires), _as_utc(targets.expires))
    if transition_expiry >= authority_expiry:
        raise RootTransitionError("online transition expiry must precede Root/Targets expiry")
    if transition_expiry <= now:
        raise RootTransitionError("online transition expiry is not in the future")

    snapshot_version = current_snapshot.version + 1
    timestamp_version = current_timestamp.version + 1
    snapshot_payload: dict[str, object] = {
        "_type": "snapshot",
        "expires": _iso(transition_expiry),
        "meta": {
            "targets.json": {
                "hashes": {"sha256": _sha256(targets_bytes)},
                "length": len(targets_bytes),
                "version": targets.version,
            }
        },
        "spec_version": current_snapshot.spec_version,
        "version": snapshot_version,
    }
    new_snapshot_bytes = _new_metadata(snapshot_payload, snapshot_signer)
    new_snapshot_md = _parse(new_snapshot_bytes, Snapshot, "new snapshot.json")
    _verify_role(new_root, "snapshot", new_snapshot_md)

    timestamp_payload: dict[str, object] = {
        "_type": "timestamp",
        "expires": _iso(transition_expiry),
        "meta": {
            "snapshot.json": {
                "hashes": {"sha256": _sha256(new_snapshot_bytes)},
                "length": len(new_snapshot_bytes),
                "version": snapshot_version,
            }
        },
        "spec_version": current_timestamp.spec_version,
        "version": timestamp_version,
    }
    new_timestamp_bytes = _new_metadata(timestamp_payload, timestamp_signer)
    new_timestamp_md = _parse(new_timestamp_bytes, Timestamp, "new timestamp.json")
    _verify_role(new_root, "timestamp", new_timestamp_md)

    new_targets_ref = new_snapshot_md.signed.meta.get("targets.json")
    if new_targets_ref is None:
        raise RootTransitionError("new snapshot unexpectedly lacks targets.json")
    _verify_exact_reference(new_targets_ref, targets_bytes, label="new targets")
    _verify_exact_reference(
        new_timestamp_md.signed.snapshot_meta,
        new_snapshot_bytes,
        label="new snapshot",
    )

    manifest: dict[str, object] = {
        "format": TRANSITION_FORMAT,
        "schema_version": TRANSITION_SCHEMA_VERSION,
        "purpose": "atomic R20.3 Root v2 and new online-role signer transition",
        "created_at": _iso(now),
        "expires": _iso(transition_expiry),
        "expiry_extended": False,
        "root": {
            "previous_version": current_root.version,
            "version": new_root.version,
            "sha256": _sha256(signed_root_v2_bytes),
            "length": len(signed_root_v2_bytes),
            "old_root_threshold_verified": rotation_evidence[
                "old_root_threshold_verified"
            ],
            "new_root_threshold_verified": rotation_evidence[
                "new_root_threshold_verified"
            ],
        },
        "targets": {
            "version": targets.version,
            "sha256": _sha256(targets_bytes),
            "length": len(targets_bytes),
            "modified": False,
        },
        "snapshot": {
            "previous_version": current_snapshot.version,
            "version": snapshot_version,
            "sha256": _sha256(new_snapshot_bytes),
            "length": len(new_snapshot_bytes),
            "keyid": snapshot_signer.public_key.keyid,
        },
        "timestamp": {
            "previous_version": current_timestamp.version,
            "version": timestamp_version,
            "sha256": _sha256(new_timestamp_bytes),
            "length": len(new_timestamp_bytes),
            "keyid": timestamp_signer.public_key.keyid,
        },
        "private_material_in_output": False,
        "root_or_targets_private_key_in_online_step": False,
        "production_effect": False,
    }
    return RootTransitionResult(
        root_bytes=signed_root_v2_bytes,
        snapshot_bytes=new_snapshot_bytes,
        timestamp_bytes=new_timestamp_bytes,
        manifest=manifest,
    )


def transition_manifest_bytes(manifest: dict[str, object]) -> bytes:
    return (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
