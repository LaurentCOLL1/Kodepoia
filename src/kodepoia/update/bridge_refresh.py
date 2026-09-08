from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from securesystemslib.signer import Signer
from tuf.api.metadata import Metadata, Root, Snapshot, Targets, Timestamp

BRIDGE_EXPIRY_DAYS = 30
BRIDGE_SCHEMA_VERSION = 1
BRIDGE_FORMAT = "kodepoia-r20-1-bridge-metadata"


class BridgeRefreshError(ValueError):
    """Raised when a bridge refresh would weaken or break TUF trust."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse(data: bytes, expected_type: type[Any], label: str) -> Metadata[Any]:
    try:
        metadata = Metadata.from_bytes(data)
    except Exception as exc:
        raise BridgeRefreshError(f"{label} is not valid TUF JSON: {exc}") from exc
    if not isinstance(metadata.signed, expected_type):
        raise BridgeRefreshError(f"{label} has unexpected metadata type")
    return metadata


def _verify_role(root: Root, role: str, metadata: Metadata[Any]) -> None:
    try:
        root.verify_delegate(role, metadata.signed_bytes, metadata.signatures)
    except Exception as exc:
        raise BridgeRefreshError(f"{role} metadata signature threshold failed: {exc}") from exc


def _verify_exact_reference(reference: Any, data: bytes, *, label: str) -> None:
    try:
        reference.verify_length_and_hashes(data)
    except Exception as exc:
        raise BridgeRefreshError(f"{label} hash/length binding failed: {exc}") from exc


def _iso(value: datetime) -> str:
    return _as_utc(value).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _serialize(metadata: Metadata[Any]) -> bytes:
    return metadata.to_bytes() + b"\n"


def _new_metadata(payload: dict[str, object], signer: Signer) -> bytes:
    envelope = Metadata.from_dict({"signatures": [], "signed": payload})
    envelope.sign(signer)
    return _serialize(envelope)


@dataclass(frozen=True, slots=True)
class BridgeMetadataResult:
    snapshot_bytes: bytes
    timestamp_bytes: bytes
    manifest: dict[str, object]


def build_bridge_metadata(
    *,
    root_bytes: bytes,
    targets_bytes: bytes,
    current_snapshot_bytes: bytes,
    current_timestamp_bytes: bytes,
    snapshot_signer: Signer,
    timestamp_signer: Signer,
    reference_time: datetime,
    bridge_days: int = BRIDGE_EXPIRY_DAYS,
) -> BridgeMetadataResult:
    """Create a monotonic Snapshot/Timestamp bridge without changing Root/Targets."""

    if bridge_days < 2 or bridge_days > BRIDGE_EXPIRY_DAYS:
        raise BridgeRefreshError(
            f"bridge lifetime must be between 2 and {BRIDGE_EXPIRY_DAYS} days"
        )

    now = _as_utc(reference_time).replace(microsecond=0)
    bridge_expiry = now + timedelta(days=bridge_days)

    root_md = _parse(root_bytes, Root, "root.json")
    targets_md = _parse(targets_bytes, Targets, "targets.json")
    snapshot_md = _parse(current_snapshot_bytes, Snapshot, "snapshot.json")
    timestamp_md = _parse(current_timestamp_bytes, Timestamp, "timestamp.json")

    root = root_md.signed
    targets = targets_md.signed
    snapshot = snapshot_md.signed
    timestamp = timestamp_md.signed

    _verify_role(root, "root", root_md)
    _verify_role(root, "targets", targets_md)
    _verify_role(root, "snapshot", snapshot_md)
    _verify_role(root, "timestamp", timestamp_md)

    if root.is_expired(now):
        raise BridgeRefreshError("root.json is already expired and cannot authorize a bridge")
    if targets.is_expired(now):
        raise BridgeRefreshError("targets.json is already expired and requires offline Targets renewal")
    if bridge_expiry >= min(root.expires, targets.expires):
        raise BridgeRefreshError("bridge expiry must remain earlier than Root and Targets expiry")

    current_targets_ref = snapshot.meta.get("targets.json")
    if current_targets_ref is None:
        raise BridgeRefreshError("current snapshot does not reference targets.json")
    if current_targets_ref.version != targets.version:
        raise BridgeRefreshError("current snapshot targets version does not match targets.json")
    _verify_exact_reference(current_targets_ref, targets_bytes, label="current targets")

    if timestamp.snapshot_meta.version != snapshot.version:
        raise BridgeRefreshError("current timestamp snapshot version does not match snapshot.json")
    _verify_exact_reference(
        timestamp.snapshot_meta,
        current_snapshot_bytes,
        label="current snapshot",
    )

    snapshot_keyids = set(root.roles["snapshot"].keyids)
    timestamp_keyids = set(root.roles["timestamp"].keyids)
    if snapshot_signer.public_key.keyid not in snapshot_keyids:
        raise BridgeRefreshError("provided Snapshot signer is not authorized by Root")
    if timestamp_signer.public_key.keyid not in timestamp_keyids:
        raise BridgeRefreshError("provided Timestamp signer is not authorized by Root")
    if snapshot_signer.public_key.keyid == timestamp_signer.public_key.keyid:
        raise BridgeRefreshError("Snapshot and Timestamp must not share the same signing key")

    snapshot_version = snapshot.version + 1
    timestamp_version = timestamp.version + 1
    snapshot_payload: dict[str, object] = {
        "_type": "snapshot",
        "expires": _iso(bridge_expiry),
        "meta": {
            "targets.json": {
                "hashes": {"sha256": _sha256(targets_bytes)},
                "length": len(targets_bytes),
                "version": targets.version,
            }
        },
        "spec_version": snapshot.spec_version,
        "version": snapshot_version,
    }
    new_snapshot_bytes = _new_metadata(snapshot_payload, snapshot_signer)
    new_snapshot_md = _parse(new_snapshot_bytes, Snapshot, "new snapshot.json")
    _verify_role(root, "snapshot", new_snapshot_md)

    timestamp_payload: dict[str, object] = {
        "_type": "timestamp",
        "expires": _iso(bridge_expiry),
        "meta": {
            "snapshot.json": {
                "hashes": {"sha256": _sha256(new_snapshot_bytes)},
                "length": len(new_snapshot_bytes),
                "version": snapshot_version,
            }
        },
        "spec_version": timestamp.spec_version,
        "version": timestamp_version,
    }
    new_timestamp_bytes = _new_metadata(timestamp_payload, timestamp_signer)
    new_timestamp_md = _parse(new_timestamp_bytes, Timestamp, "new timestamp.json")
    _verify_role(root, "timestamp", new_timestamp_md)

    new_targets_ref = new_snapshot_md.signed.meta.get("targets.json")
    if new_targets_ref is None:
        raise BridgeRefreshError("new snapshot unexpectedly lacks targets.json")
    _verify_exact_reference(new_targets_ref, targets_bytes, label="new targets")
    _verify_exact_reference(
        new_timestamp_md.signed.snapshot_meta,
        new_snapshot_bytes,
        label="new snapshot",
    )

    manifest: dict[str, object] = {
        "format": BRIDGE_FORMAT,
        "schema_version": BRIDGE_SCHEMA_VERSION,
        "purpose": "temporary R20.1 freshness bridge before online signer migration",
        "bridge_days": bridge_days,
        "signed_at": _iso(now),
        "expires": _iso(bridge_expiry),
        "root": {
            "version": root.version,
            "length": len(root_bytes),
            "sha256": _sha256(root_bytes),
            "modified": False,
        },
        "targets": {
            "version": targets.version,
            "length": len(targets_bytes),
            "sha256": _sha256(targets_bytes),
            "modified": False,
        },
        "snapshot": {
            "previous_version": snapshot.version,
            "version": snapshot_version,
            "length": len(new_snapshot_bytes),
            "sha256": _sha256(new_snapshot_bytes),
            "keyid": snapshot_signer.public_key.keyid,
        },
        "timestamp": {
            "previous_version": timestamp.version,
            "version": timestamp_version,
            "length": len(new_timestamp_bytes),
            "sha256": _sha256(new_timestamp_bytes),
            "keyid": timestamp_signer.public_key.keyid,
        },
        "private_keys_in_output": False,
        "root_or_targets_private_key_required": False,
    }
    return BridgeMetadataResult(
        snapshot_bytes=new_snapshot_bytes,
        timestamp_bytes=new_timestamp_bytes,
        manifest=manifest,
    )


def manifest_bytes(manifest: dict[str, object]) -> bytes:
    return (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
