from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol

from cryptography.hazmat.primitives.serialization import load_pem_public_key
from securesystemslib.signer import SSlibKey, Signature, Signer
from tuf.api.metadata import Metadata, Root

ONLINE_TUF_ROLES = frozenset({"snapshot", "timestamp"})
ROTATION_FORMAT = "kodepoia-r20-2-root-rotation-package"
ROTATION_SCHEMA_VERSION = 1


class OnlineSigningError(ValueError):
    """Raised when R20.2 signer or Root-rotation invariants are violated."""


@dataclass(frozen=True, slots=True)
class OnlineSignerConfig:
    """Public runtime configuration for one non-exportable online signer."""

    role: str
    provider: str
    resource: str
    public_key: SSlibKey

    def __post_init__(self) -> None:
        if self.role not in ONLINE_TUF_ROLES:
            raise OnlineSigningError(f"unsupported online TUF role: {self.role!r}")
        _validate_public_identifier(self.provider, label="provider")
        _validate_public_identifier(self.resource, label="resource")

    @property
    def keyid(self) -> str:
        return self.public_key.keyid

    def public_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "provider": self.provider,
            "resource": self.resource,
            "keyid": self.keyid,
            "public_key": self.public_key.to_dict(),
        }


class OnlineSignerResolver(Protocol):
    """Provider-neutral runtime boundary: public config in, Signer out."""

    def __call__(self, config: OnlineSignerConfig) -> Signer: ...


@dataclass(frozen=True, slots=True)
class ResolvedOnlineSigners:
    snapshot: Signer
    timestamp: Signer


@dataclass(frozen=True, slots=True)
class RootRotationPackage:
    """Immutable public-only package prepared before the offline Root ceremony."""

    unsigned_root_bytes: bytes
    manifest_bytes: bytes
    package_id: str

    @property
    def manifest(self) -> dict[str, object]:
        value = json.loads(self.manifest_bytes)
        if not isinstance(value, dict):
            raise OnlineSigningError("rotation manifest is not a JSON object")
        return value


class SyntheticSignerResolver:
    """Deterministic in-memory resolver for tests/CI only, never production custody."""

    def __init__(self, signers: Mapping[str, Signer]) -> None:
        self._signers = dict(signers)

    def __call__(self, config: OnlineSignerConfig) -> Signer:
        try:
            return self._signers[config.resource]
        except KeyError as exc:
            raise OnlineSigningError(
                f"no synthetic signer registered for {config.role}"
            ) from exc


def _validate_public_identifier(value: str, *, label: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise OnlineSigningError(f"{label} must be a non-empty normalized string")
    if any(character in value for character in ("\n", "\r", "\t")):
        raise OnlineSigningError(f"{label} must be a single-line public identifier")
    lowered = value.lower()
    forbidden = (
        "-----begin private key-----",
        "-----begin encrypted private key-----",
        "password=",
        "passphrase=",
        "secret=",
        "token=",
    )
    if any(marker in lowered for marker in forbidden):
        raise OnlineSigningError(f"{label} appears to contain secret material")


def import_public_key_pem(pem_bytes: bytes) -> SSlibKey:
    """Import SubjectPublicKeyInfo PEM and derive its TUF/securesystemslib keyid."""

    try:
        crypto_key = load_pem_public_key(pem_bytes)
        key = SSlibKey.from_crypto(crypto_key)
    except Exception as exc:
        raise OnlineSigningError(f"invalid public key PEM: {exc}") from exc
    return key


def resolve_online_signers(
    configs: Iterable[OnlineSignerConfig],
    resolver: OnlineSignerResolver,
) -> ResolvedOnlineSigners:
    """Resolve both online roles fail-closed before any signing side effect."""

    mapped: dict[str, OnlineSignerConfig] = {}
    for config in configs:
        if config.role in mapped:
            raise OnlineSigningError(f"duplicate online signer config for {config.role}")
        mapped[config.role] = config

    missing = ONLINE_TUF_ROLES.difference(mapped)
    if missing:
        raise OnlineSigningError(
            "missing online signer config for " + ", ".join(sorted(missing))
        )
    if mapped["snapshot"].keyid == mapped["timestamp"].keyid:
        raise OnlineSigningError("Snapshot and Timestamp must use different public keys")
    if (
        mapped["snapshot"].provider == mapped["timestamp"].provider
        and mapped["snapshot"].resource == mapped["timestamp"].resource
    ):
        raise OnlineSigningError("Snapshot and Timestamp must use different signer resources")

    resolved: dict[str, Signer] = {}
    for role in ("snapshot", "timestamp"):
        config = mapped[role]
        try:
            signer = resolver(config)
        except OnlineSigningError:
            raise
        except Exception as exc:
            raise OnlineSigningError(f"failed to resolve {role} signer") from exc
        if signer.public_key.keyid != config.keyid:
            raise OnlineSigningError(
                f"resolved {role} signer public identity does not match configured keyid"
            )
        if signer.public_key.to_dict() != config.public_key.to_dict():
            raise OnlineSigningError(
                f"resolved {role} signer public key does not match configured key"
            )
        resolved[role] = signer

    return ResolvedOnlineSigners(
        snapshot=resolved["snapshot"],
        timestamp=resolved["timestamp"],
    )


def sign_online_payload(
    payload: bytes,
    config: OnlineSignerConfig,
    resolver: OnlineSignerResolver,
) -> Signature:
    """Sign already-canonical payload bytes through the provider-neutral boundary."""

    signer = resolver(config)
    if signer.public_key.keyid != config.keyid:
        raise OnlineSigningError(
            f"resolved {config.role} signer public identity does not match configured keyid"
        )
    return signer.sign(payload)


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_root(data: bytes, *, label: str) -> Metadata[Root]:
    try:
        metadata = Metadata.from_bytes(data)
    except Exception as exc:
        raise OnlineSigningError(f"{label} is not valid TUF JSON: {exc}") from exc
    if not isinstance(metadata.signed, Root):
        raise OnlineSigningError(f"{label} is not Root metadata")
    return metadata


def _verify_root_self(metadata: Metadata[Root], *, label: str) -> None:
    try:
        metadata.signed.verify_delegate(
            "root", metadata.signed_bytes, metadata.signatures
        )
    except Exception as exc:
        raise OnlineSigningError(f"{label} Root signature threshold failed: {exc}") from exc


def _root_payload_dict(root_bytes: bytes) -> dict[str, object]:
    try:
        envelope = json.loads(root_bytes)
        payload = envelope["signed"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise OnlineSigningError("current Root JSON envelope is malformed") from exc
    if not isinstance(payload, dict):
        raise OnlineSigningError("current Root signed payload is not an object")
    return json.loads(json.dumps(payload))


def _role_dict(payload: dict[str, object], role: str) -> dict[str, object]:
    roles = payload.get("roles")
    if not isinstance(roles, dict):
        raise OnlineSigningError("Root roles are malformed")
    role_value = roles.get(role)
    if not isinstance(role_value, dict):
        raise OnlineSigningError(f"Root role {role!r} is malformed")
    return role_value


def _single_role_keyid(payload: dict[str, object], role: str) -> str:
    role_value = _role_dict(payload, role)
    keyids = role_value.get("keyids")
    threshold = role_value.get("threshold")
    if threshold != 1 or not isinstance(keyids, list) or len(keyids) != 1:
        raise OnlineSigningError(f"{role} must remain threshold 1 with exactly one key")
    keyid = keyids[0]
    if not isinstance(keyid, str) or not keyid:
        raise OnlineSigningError(f"{role} keyid is malformed")
    return keyid


def _drop_unreferenced_key(payload: dict[str, object], keyid: str) -> None:
    roles = payload.get("roles")
    keys = payload.get("keys")
    if not isinstance(roles, dict) or not isinstance(keys, dict):
        raise OnlineSigningError("Root keys/roles are malformed")
    for role_value in roles.values():
        if isinstance(role_value, dict):
            role_keyids = role_value.get("keyids")
            if isinstance(role_keyids, list) and keyid in role_keyids:
                return
    keys.pop(keyid, None)


def build_root_rotation_package(
    *,
    current_root_bytes: bytes,
    snapshot: OnlineSignerConfig,
    timestamp: OnlineSignerConfig,
) -> RootRotationPackage:
    """Prepare unsigned Root N+1 with only Snapshot/Timestamp public-key rotation."""

    if snapshot.role != "snapshot" or timestamp.role != "timestamp":
        raise OnlineSigningError("rotation package requires Snapshot and Timestamp configs")
    if snapshot.keyid == timestamp.keyid:
        raise OnlineSigningError("Snapshot and Timestamp replacement keys must differ")
    if snapshot.provider == timestamp.provider and snapshot.resource == timestamp.resource:
        raise OnlineSigningError("Snapshot and Timestamp signer resources must differ")

    current = _parse_root(current_root_bytes, label="current root.json")
    _verify_root_self(current, label="current")
    payload = _root_payload_dict(current_root_bytes)

    old_snapshot_keyid = _single_role_keyid(payload, "snapshot")
    old_timestamp_keyid = _single_role_keyid(payload, "timestamp")
    if snapshot.keyid == old_snapshot_keyid:
        raise OnlineSigningError("Snapshot replacement key must differ from current key")
    if timestamp.keyid == old_timestamp_keyid:
        raise OnlineSigningError("Timestamp replacement key must differ from current key")

    root_role_before = json.loads(json.dumps(_role_dict(payload, "root")))
    targets_role_before = json.loads(json.dumps(_role_dict(payload, "targets")))
    root_keyids_before = tuple(root_role_before.get("keyids", []))
    targets_keyids_before = tuple(targets_role_before.get("keyids", []))

    keys = payload.get("keys")
    if not isinstance(keys, dict):
        raise OnlineSigningError("Root key store is malformed")
    keys[snapshot.keyid] = snapshot.public_key.to_dict()
    keys[timestamp.keyid] = timestamp.public_key.to_dict()
    _role_dict(payload, "snapshot")["keyids"] = [snapshot.keyid]
    _role_dict(payload, "timestamp")["keyids"] = [timestamp.keyid]
    _role_dict(payload, "snapshot")["threshold"] = 1
    _role_dict(payload, "timestamp")["threshold"] = 1
    _drop_unreferenced_key(payload, old_snapshot_keyid)
    _drop_unreferenced_key(payload, old_timestamp_keyid)

    current_version = current.signed.version
    payload["version"] = current_version + 1
    unsigned_envelope = {"signatures": [], "signed": payload}
    unsigned_root_bytes = _canonical_json(unsigned_envelope) + b"\n"
    proposed = _parse_root(unsigned_root_bytes, label="unsigned proposed root.json")

    proposed_payload = _root_payload_dict(unsigned_root_bytes)
    if _role_dict(proposed_payload, "root") != root_role_before:
        raise OnlineSigningError("Root role policy changed during online-role rotation")
    if _role_dict(proposed_payload, "targets") != targets_role_before:
        raise OnlineSigningError("Targets role policy changed during online-role rotation")
    if tuple(_role_dict(proposed_payload, "root").get("keyids", [])) != root_keyids_before:
        raise OnlineSigningError("Root key identities changed during online-role rotation")
    if tuple(_role_dict(proposed_payload, "targets").get("keyids", [])) != targets_keyids_before:
        raise OnlineSigningError("Targets key identities changed during online-role rotation")
    if proposed.signed.consistent_snapshot != current.signed.consistent_snapshot:
        raise OnlineSigningError("consistent_snapshot policy changed during rotation")
    if proposed.signed.spec_version != current.signed.spec_version:
        raise OnlineSigningError("TUF spec_version changed during rotation")

    package_material = {
        "current_root_sha256": _sha256(current_root_bytes),
        "proposed_root_sha256": _sha256(unsigned_root_bytes),
        "snapshot": snapshot.public_dict(),
        "timestamp": timestamp.public_dict(),
    }
    package_id = _sha256(_canonical_json(package_material))
    manifest: dict[str, object] = {
        "format": ROTATION_FORMAT,
        "schema_version": ROTATION_SCHEMA_VERSION,
        "package_id": package_id,
        "current_root": {
            "version": current_version,
            "sha256": _sha256(current_root_bytes),
            "root_threshold": current.signed.roles["root"].threshold,
            "root_keyids": list(current.signed.roles["root"].keyids),
        },
        "proposed_root": {
            "version": proposed.signed.version,
            "sha256": _sha256(unsigned_root_bytes),
            "signed": False,
            "root_threshold": proposed.signed.roles["root"].threshold,
            "root_keyids": list(proposed.signed.roles["root"].keyids),
        },
        "online_roles": {
            "snapshot": {
                "previous_keyid": old_snapshot_keyid,
                "replacement_keyid": snapshot.keyid,
                "provider": snapshot.provider,
                "resource": snapshot.resource,
                "threshold": 1,
            },
            "timestamp": {
                "previous_keyid": old_timestamp_keyid,
                "replacement_keyid": timestamp.keyid,
                "provider": timestamp.provider,
                "resource": timestamp.resource,
                "threshold": 1,
            },
        },
        "offline_root_signatures_required": current.signed.roles["root"].threshold,
        "new_root_self_threshold_required": proposed.signed.roles["root"].threshold,
        "private_key_material_in_package": False,
        "production_effect": False,
    }
    return RootRotationPackage(
        unsigned_root_bytes=unsigned_root_bytes,
        manifest_bytes=_canonical_json(manifest) + b"\n",
        package_id=package_id,
    )


def verify_signed_root_rotation(
    *, current_root_bytes: bytes, candidate_root_bytes: bytes
) -> dict[str, object]:
    """Verify the mandatory old-threshold + new-threshold sequential Root update."""

    current = _parse_root(current_root_bytes, label="current root.json")
    candidate = _parse_root(candidate_root_bytes, label="candidate root.json")
    _verify_root_self(current, label="current")
    if candidate.signed.version != current.signed.version + 1:
        raise OnlineSigningError("candidate Root version must be exactly current version + 1")

    try:
        current.signed.verify_delegate(
            "root", candidate.signed_bytes, candidate.signatures
        )
    except Exception as exc:
        raise OnlineSigningError(
            f"candidate Root is not signed by the current Root threshold: {exc}"
        ) from exc
    try:
        candidate.signed.verify_delegate(
            "root", candidate.signed_bytes, candidate.signatures
        )
    except Exception as exc:
        raise OnlineSigningError(
            f"candidate Root does not satisfy its own Root threshold: {exc}"
        ) from exc

    current_payload = _root_payload_dict(current_root_bytes)
    candidate_payload = _root_payload_dict(candidate_root_bytes)
    for role in ("root", "targets"):
        if _role_dict(candidate_payload, role) != _role_dict(current_payload, role):
            raise OnlineSigningError(f"candidate Root changes offline {role} role policy")
    if candidate.signed.consistent_snapshot != current.signed.consistent_snapshot:
        raise OnlineSigningError("candidate Root changes consistent_snapshot policy")
    if candidate.signed.spec_version != current.signed.spec_version:
        raise OnlineSigningError("candidate Root changes spec_version")

    snapshot_keyid = _single_role_keyid(candidate_payload, "snapshot")
    timestamp_keyid = _single_role_keyid(candidate_payload, "timestamp")
    if snapshot_keyid == timestamp_keyid:
        raise OnlineSigningError("candidate Root reuses one key for Snapshot and Timestamp")
    if snapshot_keyid == _single_role_keyid(current_payload, "snapshot"):
        raise OnlineSigningError("candidate Root did not rotate Snapshot key")
    if timestamp_keyid == _single_role_keyid(current_payload, "timestamp"):
        raise OnlineSigningError("candidate Root did not rotate Timestamp key")

    return {
        "current_version": current.signed.version,
        "candidate_version": candidate.signed.version,
        "old_root_threshold_verified": True,
        "new_root_threshold_verified": True,
        "snapshot_keyid": snapshot_keyid,
        "timestamp_keyid": timestamp_keyid,
        "offline_roles_preserved": True,
    }
