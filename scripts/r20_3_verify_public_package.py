from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from securesystemslib.signer import SSlibKey
from tuf.api.metadata import Metadata, Root

EXPECTED_ROOT_V1_SHA256 = (
    "892442754966aa643bbe15a2910aa3fef59032c8f5eade34fed62efd96aefee5"
)
EXPECTED_ZIP_SHA256 = (
    "4b26dbf702f93e1c2e6f813eae7c22771a06e97fd9d77bd6d57bff1b6c22b1db"
)
EXPECTED_PUBLIC_KEYS_SHA256 = (
    "4da09ab071e3efea2e831871c752a4469fb126caf05172d911983ad115308030"
)
EXPECTED_UNSIGNED_ROOT_SHA256 = (
    "7ae909722149fe7f05380f93b7317c99347f8b3c1d102b7b6ddca64bbe1bbe1d"
)
EXPECTED_ROTATION_MANIFEST_SHA256 = (
    "f691dfa880d85fdf92f1b4ad2cc3167b81b1920ea4267494865d0b6460334188"
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_object(data: bytes, *, label: str) -> dict[str, object]:
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _public_keyid(entry: object, *, role: str) -> tuple[str, SSlibKey]:
    if not isinstance(entry, dict):
        raise ValueError(f"{role} public entry is malformed")
    declared_keyid = entry.get("keyid")
    public_key = entry.get("public_key")
    if not isinstance(declared_keyid, str) or not isinstance(public_key, dict):
        raise ValueError(f"{role} keyid/public key is malformed")
    keyval = public_key.get("keyval")
    if not isinstance(keyval, dict):
        raise ValueError(f"{role} keyval is malformed")
    public_hex = keyval.get("public")
    if not isinstance(public_hex, str):
        raise ValueError(f"{role} public key bytes are malformed")
    try:
        crypto_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex))
    except ValueError as exc:
        raise ValueError(f"{role} public key is not valid Ed25519") from exc
    derived = SSlibKey.from_crypto(crypto_key)
    if derived.keyid != declared_keyid:
        raise ValueError(
            f"{role} keyid mismatch: declared {declared_keyid}, derived {derived.keyid}"
        )
    if derived.to_dict() != public_key:
        raise ValueError(f"{role} public key payload mismatch")
    public_sha256 = entry.get("public_sha256")
    if public_sha256 != _sha256(public_hex.encode("utf-8")):
        raise ValueError(f"{role} public_sha256 mismatch")
    return declared_keyid, derived


def verify_public_package(
    *,
    current_root_path: Path,
    public_keys_path: Path,
    unsigned_root_path: Path,
    rotation_manifest_path: Path,
    acceptance_path: Path,
) -> dict[str, object]:
    current_root_bytes = current_root_path.read_bytes()
    public_keys_bytes = public_keys_path.read_bytes()
    unsigned_root_bytes = unsigned_root_path.read_bytes()
    rotation_manifest_bytes = rotation_manifest_path.read_bytes()
    acceptance_bytes = acceptance_path.read_bytes()

    if _sha256(current_root_bytes) != EXPECTED_ROOT_V1_SHA256:
        raise ValueError("production Root v1 bytes changed")
    if _sha256(public_keys_bytes) != EXPECTED_PUBLIC_KEYS_SHA256:
        raise ValueError("committed R20.3 public-key manifest bytes changed")
    if _sha256(unsigned_root_bytes) != EXPECTED_UNSIGNED_ROOT_SHA256:
        raise ValueError("committed unsigned Root v2 bytes changed")
    if _sha256(rotation_manifest_bytes) != EXPECTED_ROTATION_MANIFEST_SHA256:
        raise ValueError("committed Root-rotation manifest bytes changed")

    public_keys = _json_object(public_keys_bytes, label="R20_3_PUBLIC_KEYS.json")
    rotation = _json_object(
        rotation_manifest_bytes, label="R20_3_ROOT_ROTATION_MANIFEST.json"
    )
    acceptance = _json_object(
        acceptance_bytes, label="R20_3_PUBLIC_PACKAGE_ACCEPTANCE.json"
    )

    if public_keys.get("format") != "kodepoia-r20-3-zero-cost-public-keys":
        raise ValueError("unexpected R20.3 public-key manifest format")
    if public_keys.get("provider") != "github-environment-secret":
        raise ValueError("unexpected R20.3 signer provider")
    if public_keys.get("environment") != "tuf-production-signing":
        raise ValueError("unexpected R20.3 signing environment")
    if public_keys.get("paid_provider_required") is not False:
        raise ValueError("R20.3 public manifest requires a paid provider")
    if public_keys.get("private_material_in_manifest") is not False:
        raise ValueError("R20.3 public manifest reports private material")

    snapshot_keyid, _ = _public_keyid(public_keys.get("snapshot"), role="snapshot")
    timestamp_keyid, _ = _public_keyid(public_keys.get("timestamp"), role="timestamp")
    if snapshot_keyid == timestamp_keyid:
        raise ValueError("Snapshot and Timestamp replacement keyids are not distinct")

    current = Metadata.from_bytes(current_root_bytes)
    proposed = Metadata.from_bytes(unsigned_root_bytes)
    if not isinstance(current.signed, Root) or not isinstance(proposed.signed, Root):
        raise ValueError("current/proposed metadata must both be Root metadata")
    current.signed.verify_delegate("root", current.signed_bytes, current.signatures)
    if proposed.signatures:
        raise ValueError("R20.3 proposed Root v2 must still be unsigned at this checkpoint")
    if proposed.signed.version != current.signed.version + 1:
        raise ValueError("Root v2 version is not sequential")
    if proposed.signed.roles["root"] != current.signed.roles["root"]:
        raise ValueError("Root role policy changed")
    if proposed.signed.roles["targets"] != current.signed.roles["targets"]:
        raise ValueError("Targets role policy changed")
    if proposed.signed.roles["snapshot"].threshold != 1:
        raise ValueError("Snapshot threshold changed")
    if proposed.signed.roles["timestamp"].threshold != 1:
        raise ValueError("Timestamp threshold changed")
    if proposed.signed.roles["snapshot"].keyids != [snapshot_keyid]:
        raise ValueError("Root v2 Snapshot keyid does not match public manifest")
    if proposed.signed.roles["timestamp"].keyids != [timestamp_keyid]:
        raise ValueError("Root v2 Timestamp keyid does not match public manifest")

    old_snapshot = current.signed.roles["snapshot"].keyids[0]
    old_timestamp = current.signed.roles["timestamp"].keyids[0]
    if old_snapshot in proposed.signed.keys or old_timestamp in proposed.signed.keys:
        raise ValueError("superseded online-role key remains in proposed Root v2")

    if rotation.get("package_id") != public_keys.get("root_rotation_package_id"):
        raise ValueError("rotation package id mismatch")
    proposed_root = rotation.get("proposed_root")
    current_root = rotation.get("current_root")
    online_roles = rotation.get("online_roles")
    if not isinstance(proposed_root, dict) or not isinstance(current_root, dict):
        raise ValueError("rotation Root references are malformed")
    if not isinstance(online_roles, dict):
        raise ValueError("rotation online role references are malformed")
    if current_root.get("sha256") != EXPECTED_ROOT_V1_SHA256:
        raise ValueError("rotation manifest current Root digest mismatch")
    if proposed_root.get("sha256") != EXPECTED_UNSIGNED_ROOT_SHA256:
        raise ValueError("rotation manifest proposed Root digest mismatch")
    if proposed_root.get("signed") is not False:
        raise ValueError("rotation manifest unexpectedly marks Root v2 signed")
    if rotation.get("offline_root_signatures_required") != 2:
        raise ValueError("rotation manifest Root threshold changed")
    if rotation.get("new_root_self_threshold_required") != 2:
        raise ValueError("rotation manifest new Root threshold changed")

    for role, expected_old, expected_new in (
        ("snapshot", old_snapshot, snapshot_keyid),
        ("timestamp", old_timestamp, timestamp_keyid),
    ):
        role_entry = online_roles.get(role)
        if not isinstance(role_entry, dict):
            raise ValueError(f"rotation manifest {role} role is malformed")
        if role_entry.get("previous_keyid") != expected_old:
            raise ValueError(f"rotation manifest {role} previous keyid mismatch")
        if role_entry.get("replacement_keyid") != expected_new:
            raise ValueError(f"rotation manifest {role} replacement keyid mismatch")
        if role_entry.get("threshold") != 1:
            raise ValueError(f"rotation manifest {role} threshold changed")

    forbidden_markers = (
        b"-----BEGIN PRIVATE KEY-----",
        b"-----BEGIN ENCRYPTED PRIVATE KEY-----",
        b"PASSPHRASE=",
        b"PASSWORD=",
    )
    combined_public = public_keys_bytes + unsigned_root_bytes + rotation_manifest_bytes
    upper_public = combined_public.upper()
    if any(marker in upper_public for marker in forbidden_markers):
        raise ValueError("private/secret marker detected in committed public package")

    expected_acceptance = {
        "uploaded_zip_sha256": EXPECTED_ZIP_SHA256,
        "public_keys_sha256": EXPECTED_PUBLIC_KEYS_SHA256,
        "unsigned_root_sha256": EXPECTED_UNSIGNED_ROOT_SHA256,
        "rotation_manifest_sha256": EXPECTED_ROTATION_MANIFEST_SHA256,
        "current_root_sha256": EXPECTED_ROOT_V1_SHA256,
        "current_root_version": 1,
        "proposed_root_version": 2,
        "root_threshold": 2,
        "snapshot_replacement_keyid": snapshot_keyid,
        "timestamp_replacement_keyid": timestamp_keyid,
        "replacement_keyids_distinct": True,
        "replacement_keyids_derived_from_public_keys": True,
        "root_policy_preserved": True,
        "targets_policy_preserved": True,
        "private_material_detected": False,
        "paid_provider_required": False,
        "production_effect": False,
        "status": "pass",
    }
    for key, value in expected_acceptance.items():
        if acceptance.get(key) != value:
            raise ValueError(f"public-package acceptance mismatch for {key}")

    return {
        "format": "kodepoia-r20-3-public-package-verification",
        "schema_version": 1,
        "uploaded_zip_sha256": EXPECTED_ZIP_SHA256,
        "current_root_version": current.signed.version,
        "proposed_root_version": proposed.signed.version,
        "snapshot_keyid": snapshot_keyid,
        "timestamp_keyid": timestamp_keyid,
        "root_policy_preserved": True,
        "targets_policy_preserved": True,
        "private_material_detected": False,
        "paid_provider_required": False,
        "production_effect": False,
        "status": "pass",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the committed public-only R20.3 online-key/Root-v2 package."
    )
    parser.add_argument(
        "--current-root",
        default="update-repository/metadata/root.json",
    )
    parser.add_argument(
        "--public-keys",
        default="docs/roadmap/R20_3_PUBLIC_KEYS.json",
    )
    parser.add_argument(
        "--unsigned-root",
        default="docs/roadmap/R20_3_ROOT_V2_UNSIGNED.json",
    )
    parser.add_argument(
        "--rotation-manifest",
        default="docs/roadmap/R20_3_ROOT_ROTATION_MANIFEST.json",
    )
    parser.add_argument(
        "--acceptance",
        default="docs/roadmap/R20_3_PUBLIC_PACKAGE_ACCEPTANCE.json",
    )
    args = parser.parse_args()

    report = verify_public_package(
        current_root_path=Path(args.current_root),
        public_keys_path=Path(args.public_keys),
        unsigned_root_path=Path(args.unsigned_root),
        rotation_manifest_path=Path(args.rotation_manifest),
        acceptance_path=Path(args.acceptance),
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
