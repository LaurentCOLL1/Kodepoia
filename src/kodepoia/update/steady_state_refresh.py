from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from securesystemslib.signer import Signer
from tuf.api.metadata import Metadata, Root, Snapshot, Targets, Timestamp

SNAPSHOT_EXPIRY_HOURS = 72
TIMESTAMP_EXPIRY_HOURS = 48
REFRESH_THRESHOLD_HOURS = 24
REFRESH_FORMAT = "kodepoia-r20-4-steady-state-refresh"
REFRESH_SCHEMA_VERSION = 1


class SteadyStateRefreshError(ValueError):
    """Raised when an online metadata refresh would weaken or break TUF trust."""


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
        raise SteadyStateRefreshError(f"{label} is not valid TUF JSON: {exc}") from exc
    if not isinstance(metadata.signed, expected_type):
        raise SteadyStateRefreshError(f"{label} has unexpected metadata type")
    return metadata


def _verify_role(root: Root, role: str, metadata: Metadata[Any]) -> None:
    try:
        root.verify_delegate(role, metadata.signed_bytes, metadata.signatures)
    except Exception as exc:
        raise SteadyStateRefreshError(
            f"{role} metadata signature threshold failed: {exc}"
        ) from exc


def _verify_exact_reference(reference: Any, data: bytes, *, label: str) -> None:
    try:
        reference.verify_length_and_hashes(data)
    except Exception as exc:
        raise SteadyStateRefreshError(
            f"{label} hash/length binding failed: {exc}"
        ) from exc


def _serialize(metadata: Metadata[Any]) -> bytes:
    return metadata.to_bytes() + b"\n"


def _new_metadata(payload: dict[str, object], signer: Signer) -> bytes:
    envelope = Metadata.from_dict({"signatures": [], "signed": payload})
    envelope.sign(signer)
    return _serialize(envelope)


@dataclass(frozen=True, slots=True)
class RefreshDecision:
    refresh_required: bool
    reason: str
    snapshot_version: int
    timestamp_version: int
    snapshot_remaining_seconds: int
    timestamp_remaining_seconds: int
    threshold_seconds: int

    def to_dict(self) -> dict[str, object]:
        return {
            "refresh_required": self.refresh_required,
            "reason": self.reason,
            "snapshot_version": self.snapshot_version,
            "timestamp_version": self.timestamp_version,
            "snapshot_remaining_seconds": self.snapshot_remaining_seconds,
            "timestamp_remaining_seconds": self.timestamp_remaining_seconds,
            "threshold_seconds": self.threshold_seconds,
        }


@dataclass(frozen=True, slots=True)
class SteadyStateRefreshResult:
    snapshot_bytes: bytes
    timestamp_bytes: bytes
    refreshed: bool
    manifest: dict[str, object]


def _verified_state(
    *,
    root_bytes: bytes,
    targets_bytes: bytes,
    snapshot_bytes: bytes,
    timestamp_bytes: bytes,
    reference_time: datetime,
) -> tuple[Metadata[Root], Metadata[Targets], Metadata[Snapshot], Metadata[Timestamp]]:
    now = _as_utc(reference_time).replace(microsecond=0)
    root_md = _parse(root_bytes, Root, "root.json")
    targets_md = _parse(targets_bytes, Targets, "targets.json")
    snapshot_md = _parse(snapshot_bytes, Snapshot, "snapshot.json")
    timestamp_md = _parse(timestamp_bytes, Timestamp, "timestamp.json")

    root = root_md.signed
    targets = targets_md.signed
    snapshot = snapshot_md.signed
    timestamp = timestamp_md.signed

    _verify_role(root, "root", root_md)
    _verify_role(root, "targets", targets_md)
    _verify_role(root, "snapshot", snapshot_md)
    _verify_role(root, "timestamp", timestamp_md)

    if root.is_expired(now):
        raise SteadyStateRefreshError(
            "root.json is expired; online roles cannot extend Root authority"
        )
    if targets.is_expired(now):
        raise SteadyStateRefreshError(
            "targets.json is expired; online roles cannot extend Targets authority"
        )

    targets_ref = snapshot.meta.get("targets.json")
    if targets_ref is None:
        raise SteadyStateRefreshError("snapshot.json does not reference targets.json")
    if targets_ref.version != targets.version:
        raise SteadyStateRefreshError(
            "snapshot targets version does not match exact targets.json"
        )
    _verify_exact_reference(targets_ref, targets_bytes, label="targets.json")

    if timestamp.snapshot_meta.version != snapshot.version:
        raise SteadyStateRefreshError(
            "timestamp snapshot version does not match exact snapshot.json"
        )
    _verify_exact_reference(timestamp.snapshot_meta, snapshot_bytes, label="snapshot.json")

    return root_md, targets_md, snapshot_md, timestamp_md


def evaluate_refresh(
    *,
    root_bytes: bytes,
    targets_bytes: bytes,
    snapshot_bytes: bytes,
    timestamp_bytes: bytes,
    reference_time: datetime,
    threshold_hours: int = REFRESH_THRESHOLD_HOURS,
) -> RefreshDecision:
    """Validate the current metadata view and decide whether the pair needs renewal."""

    if threshold_hours <= 0:
        raise SteadyStateRefreshError("refresh threshold must be positive")

    now = _as_utc(reference_time).replace(microsecond=0)
    _, _, snapshot_md, timestamp_md = _verified_state(
        root_bytes=root_bytes,
        targets_bytes=targets_bytes,
        snapshot_bytes=snapshot_bytes,
        timestamp_bytes=timestamp_bytes,
        reference_time=now,
    )
    threshold_seconds = threshold_hours * 60 * 60
    snapshot_remaining = int((_as_utc(snapshot_md.signed.expires) - now).total_seconds())
    timestamp_remaining = int((_as_utc(timestamp_md.signed.expires) - now).total_seconds())
    due_roles: list[str] = []
    if snapshot_remaining <= threshold_seconds:
        due_roles.append("snapshot")
    if timestamp_remaining <= threshold_seconds:
        due_roles.append("timestamp")
    refresh_required = bool(due_roles)
    reason = (
        "remaining lifetime at or below policy threshold: " + ",".join(due_roles)
        if refresh_required
        else "both online roles remain above policy threshold"
    )
    return RefreshDecision(
        refresh_required=refresh_required,
        reason=reason,
        snapshot_version=snapshot_md.signed.version,
        timestamp_version=timestamp_md.signed.version,
        snapshot_remaining_seconds=snapshot_remaining,
        timestamp_remaining_seconds=timestamp_remaining,
        threshold_seconds=threshold_seconds,
    )


def build_steady_state_metadata(
    *,
    root_bytes: bytes,
    targets_bytes: bytes,
    current_snapshot_bytes: bytes,
    current_timestamp_bytes: bytes,
    snapshot_signer: Signer,
    timestamp_signer: Signer,
    reference_time: datetime,
    snapshot_expiry_hours: int = SNAPSHOT_EXPIRY_HOURS,
    timestamp_expiry_hours: int = TIMESTAMP_EXPIRY_HOURS,
) -> SteadyStateRefreshResult:
    """Build one monotonic Snapshot/Timestamp pair for atomic repository publication."""

    if snapshot_expiry_hours <= 0 or timestamp_expiry_hours <= 0:
        raise SteadyStateRefreshError("online metadata lifetime must be positive")
    if snapshot_expiry_hours <= timestamp_expiry_hours:
        raise SteadyStateRefreshError(
            "Snapshot lifetime must remain longer than Timestamp lifetime"
        )

    now = _as_utc(reference_time).replace(microsecond=0)
    root_md, targets_md, snapshot_md, timestamp_md = _verified_state(
        root_bytes=root_bytes,
        targets_bytes=targets_bytes,
        snapshot_bytes=current_snapshot_bytes,
        timestamp_bytes=current_timestamp_bytes,
        reference_time=now,
    )
    root = root_md.signed
    targets = targets_md.signed
    snapshot = snapshot_md.signed
    timestamp = timestamp_md.signed

    snapshot_keyids = set(root.roles["snapshot"].keyids)
    timestamp_keyids = set(root.roles["timestamp"].keyids)
    if snapshot_signer.public_key.keyid not in snapshot_keyids:
        raise SteadyStateRefreshError("provided Snapshot signer is not authorized by Root")
    if timestamp_signer.public_key.keyid not in timestamp_keyids:
        raise SteadyStateRefreshError("provided Timestamp signer is not authorized by Root")
    if snapshot_signer.public_key.keyid == timestamp_signer.public_key.keyid:
        raise SteadyStateRefreshError("Snapshot and Timestamp must use different signing keys")

    snapshot_expiry = now + timedelta(hours=snapshot_expiry_hours)
    timestamp_expiry = now + timedelta(hours=timestamp_expiry_hours)
    authority_expiry = min(_as_utc(root.expires), _as_utc(targets.expires))
    if snapshot_expiry >= authority_expiry or timestamp_expiry >= authority_expiry:
        raise SteadyStateRefreshError(
            "online metadata expiry must remain earlier than Root and Targets authority"
        )

    snapshot_version = snapshot.version + 1
    timestamp_version = timestamp.version + 1
    snapshot_payload: dict[str, object] = {
        "_type": "snapshot",
        "expires": _iso(snapshot_expiry),
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
        "expires": _iso(timestamp_expiry),
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
        raise SteadyStateRefreshError("new snapshot unexpectedly lacks targets.json")
    _verify_exact_reference(new_targets_ref, targets_bytes, label="new targets.json")
    _verify_exact_reference(
        new_timestamp_md.signed.snapshot_meta,
        new_snapshot_bytes,
        label="new snapshot.json",
    )

    manifest: dict[str, object] = {
        "format": REFRESH_FORMAT,
        "schema_version": REFRESH_SCHEMA_VERSION,
        "refreshed": True,
        "signed_at": _iso(now),
        "policy": {
            "snapshot_expiry_hours": snapshot_expiry_hours,
            "timestamp_expiry_hours": timestamp_expiry_hours,
            "refresh_threshold_hours": REFRESH_THRESHOLD_HOURS,
        },
        "root": {
            "version": root.version,
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
            "expires": _iso(snapshot_expiry),
            "length": len(new_snapshot_bytes),
            "sha256": _sha256(new_snapshot_bytes),
            "keyid": snapshot_signer.public_key.keyid,
        },
        "timestamp": {
            "previous_version": timestamp.version,
            "version": timestamp_version,
            "expires": _iso(timestamp_expiry),
            "length": len(new_timestamp_bytes),
            "sha256": _sha256(new_timestamp_bytes),
            "keyid": timestamp_signer.public_key.keyid,
            "snapshot_sha256": _sha256(new_snapshot_bytes),
        },
        "release_assets_modified": False,
        "private_material_in_output": False,
        "root_or_targets_private_key_required": False,
    }
    return SteadyStateRefreshResult(
        snapshot_bytes=new_snapshot_bytes,
        timestamp_bytes=new_timestamp_bytes,
        refreshed=True,
        manifest=manifest,
    )


def refresh_if_due(
    *,
    root_bytes: bytes,
    targets_bytes: bytes,
    current_snapshot_bytes: bytes,
    current_timestamp_bytes: bytes,
    reference_time: datetime,
    snapshot_signer: Signer | None = None,
    timestamp_signer: Signer | None = None,
) -> SteadyStateRefreshResult:
    """Return exact current bytes when fresh; otherwise require both online signers and renew."""

    decision = evaluate_refresh(
        root_bytes=root_bytes,
        targets_bytes=targets_bytes,
        snapshot_bytes=current_snapshot_bytes,
        timestamp_bytes=current_timestamp_bytes,
        reference_time=reference_time,
    )
    if not decision.refresh_required:
        return SteadyStateRefreshResult(
            snapshot_bytes=current_snapshot_bytes,
            timestamp_bytes=current_timestamp_bytes,
            refreshed=False,
            manifest={
                "format": REFRESH_FORMAT,
                "schema_version": REFRESH_SCHEMA_VERSION,
                "refreshed": False,
                "decision": decision.to_dict(),
                "release_assets_modified": False,
                "private_material_in_output": False,
            },
        )
    if snapshot_signer is None or timestamp_signer is None:
        raise SteadyStateRefreshError(
            "refresh is due but both online role signers were not supplied"
        )
    return build_steady_state_metadata(
        root_bytes=root_bytes,
        targets_bytes=targets_bytes,
        current_snapshot_bytes=current_snapshot_bytes,
        current_timestamp_bytes=current_timestamp_bytes,
        snapshot_signer=snapshot_signer,
        timestamp_signer=timestamp_signer,
        reference_time=reference_time,
    )


def manifest_bytes(manifest: dict[str, object]) -> bytes:
    return (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
