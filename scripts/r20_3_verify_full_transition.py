from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from tuf.api.metadata import Metadata, Root, Snapshot, Targets, Timestamp

EXPECTED_ROOT_V1_SHA256 = (
    "892442754966aa643bbe15a2910aa3fef59032c8f5eade34fed62efd96aefee5"
)
EXPECTED_UNSIGNED_ROOT_V2_SHA256 = (
    "7ae909722149fe7f05380f93b7317c99347f8b3c1d102b7b6ddca64bbe1bbe1d"
)
EXPECTED_ROOT_V2_SHA256 = (
    "c92b2165bcbf39f74599fbdf8cc30e203f8c93cc2f24c5c74012821646850ee7"
)
EXPECTED_TARGETS_SHA256 = (
    "0b65bf34e50d43ed1f82f0f4a17875fb0a4bb597ed5b6066749dc9352e504e3f"
)
EXPECTED_SNAPSHOT_SHA256 = (
    "1fccbcc5721acf59188761a79b70d829fa1ae23e77e505d1c1e9867c110eced9"
)
EXPECTED_TIMESTAMP_SHA256 = (
    "74c815dc414ae946aba1f7c427ae044dbaa3a5e1fb15bbdb436e33881fc6e501"
)
EXPECTED_MANIFEST_SHA256 = (
    "bfd8ca6c1386911f6504410e42a4ef0b9e8243b13d5670a84738f572237e7d50"
)
EXPECTED_ZIP_SHA256 = (
    "7ee54d08d0dc11ce275705c877a0615b69bedd15a18747393ef7e1dbee58651e"
)
EXPECTED_SNAPSHOT_KEYID = (
    "fac1c790b4d6dbeb04ca4a803bd80e6fde19127fc7ada34003cef5d6b50506d8"
)
EXPECTED_TIMESTAMP_KEYID = (
    "8d81006fd9de63660d74c43b6926ed664b2e9f1bdf81a9556367232533d5a2ad"
)
EXPECTED_EXPIRES = "2026-10-08T21:44:18Z"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_object(data: bytes, *, label: str) -> dict[str, object]:
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def verify_full_transition() -> dict[str, object]:
    metadata_dir = Path("update-repository/metadata")
    roadmap_dir = Path("docs/roadmap")

    base_root_bytes = (roadmap_dir / "R20_3_ROOT_V1_BASE.json").read_bytes()
    unsigned_root_bytes = (roadmap_dir / "R20_3_ROOT_V2_UNSIGNED.json").read_bytes()
    root_bytes = (metadata_dir / "root.json").read_bytes()
    targets_bytes = (metadata_dir / "targets.json").read_bytes()
    snapshot_bytes = (metadata_dir / "snapshot.json").read_bytes()
    timestamp_bytes = (metadata_dir / "timestamp.json").read_bytes()
    manifest_bytes = (roadmap_dir / "R20_3_FULL_TRANSITION_MANIFEST.json").read_bytes()
    acceptance_bytes = (roadmap_dir / "R20_3_FULL_TRANSITION_ACCEPTANCE.json").read_bytes()

    expected_hashes = {
        "Root v1 base": (base_root_bytes, EXPECTED_ROOT_V1_SHA256),
        "unsigned Root v2": (unsigned_root_bytes, EXPECTED_UNSIGNED_ROOT_V2_SHA256),
        "Root v2": (root_bytes, EXPECTED_ROOT_V2_SHA256),
        "Targets v2": (targets_bytes, EXPECTED_TARGETS_SHA256),
        "Snapshot v4": (snapshot_bytes, EXPECTED_SNAPSHOT_SHA256),
        "Timestamp v4": (timestamp_bytes, EXPECTED_TIMESTAMP_SHA256),
        "transition manifest": (manifest_bytes, EXPECTED_MANIFEST_SHA256),
    }
    for label, (payload, expected) in expected_hashes.items():
        actual = _sha256(payload)
        if actual != expected:
            raise ValueError(f"{label} digest mismatch: {actual}")

    base_root = Metadata.from_bytes(base_root_bytes)
    unsigned_root = Metadata.from_bytes(unsigned_root_bytes)
    root = Metadata.from_bytes(root_bytes)
    targets = Metadata.from_bytes(targets_bytes)
    snapshot = Metadata.from_bytes(snapshot_bytes)
    timestamp = Metadata.from_bytes(timestamp_bytes)

    if not isinstance(base_root.signed, Root):
        raise ValueError("R20.3 Root v1 base has the wrong TUF type")
    if not isinstance(unsigned_root.signed, Root):
        raise ValueError("R20.3 unsigned Root v2 has the wrong TUF type")
    if not isinstance(root.signed, Root):
        raise ValueError("production root.json has the wrong TUF type")
    if not isinstance(targets.signed, Targets):
        raise ValueError("production targets.json has the wrong TUF type")
    if not isinstance(snapshot.signed, Snapshot):
        raise ValueError("production snapshot.json has the wrong TUF type")
    if not isinstance(timestamp.signed, Timestamp):
        raise ValueError("production timestamp.json has the wrong TUF type")

    base_root.signed.verify_delegate("root", base_root.signed_bytes, base_root.signatures)
    base_root.signed.verify_delegate("root", root.signed_bytes, root.signatures)
    root.signed.verify_delegate("root", root.signed_bytes, root.signatures)
    root.signed.verify_delegate("targets", targets.signed_bytes, targets.signatures)
    root.signed.verify_delegate("snapshot", snapshot.signed_bytes, snapshot.signatures)
    root.signed.verify_delegate("timestamp", timestamp.signed_bytes, timestamp.signatures)

    if root.signed_bytes != unsigned_root.signed_bytes:
        raise ValueError("signed Root v2 payload differs from accepted unsigned Root v2")
    if root.signed.version != base_root.signed.version + 1:
        raise ValueError("Root v2 is not sequential from Root v1")
    if root.signed.roles["root"] != base_root.signed.roles["root"]:
        raise ValueError("Root role policy changed during R20.3")
    if root.signed.roles["targets"] != base_root.signed.roles["targets"]:
        raise ValueError("Targets role policy changed during R20.3")
    if root.signed.roles["snapshot"].keyids != [EXPECTED_SNAPSHOT_KEYID]:
        raise ValueError("Root v2 Snapshot keyid mismatch")
    if root.signed.roles["timestamp"].keyids != [EXPECTED_TIMESTAMP_KEYID]:
        raise ValueError("Root v2 Timestamp keyid mismatch")

    versions = (
        root.signed.version,
        targets.signed.version,
        snapshot.signed.version,
        timestamp.signed.version,
    )
    if versions != (2, 2, 4, 4):
        raise ValueError(f"R20.3 metadata versions are not 2/2/4/4: {versions}")

    targets_ref = snapshot.signed.meta.get("targets.json")
    if targets_ref is None or targets_ref.version != 2:
        raise ValueError("Snapshot v4 does not reference Targets v2")
    targets_ref.verify_length_and_hashes(targets_bytes)

    snapshot_ref = timestamp.signed.snapshot_meta
    if snapshot_ref.version != 4:
        raise ValueError("Timestamp v4 does not reference Snapshot v4")
    snapshot_ref.verify_length_and_hashes(snapshot_bytes)

    expected_expiry = datetime.fromisoformat(EXPECTED_EXPIRES.replace("Z", "+00:00"))
    if snapshot.signed.expires != expected_expiry or timestamp.signed.expires != expected_expiry:
        raise ValueError("R20.3 online metadata expiry differs from accepted bridge expiry")
    now = datetime.now(UTC)
    if snapshot.signed.is_expired(now) or timestamp.signed.is_expired(now):
        raise ValueError("R20.3 transitioned online metadata is expired")

    manifest = _json_object(manifest_bytes, label="R20_3_FULL_TRANSITION_MANIFEST.json")
    acceptance = _json_object(
        acceptance_bytes, label="R20_3_FULL_TRANSITION_ACCEPTANCE.json"
    )
    if manifest.get("format") != "kodepoia-r20-3-root-online-role-transition":
        raise ValueError("unexpected R20.3 transition manifest format")
    if manifest.get("expires") != EXPECTED_EXPIRES or manifest.get("expiry_extended") is not False:
        raise ValueError("R20.3 transition expiry policy mismatch")
    if manifest.get("private_material_in_output") is not False:
        raise ValueError("R20.3 transition manifest reports private material")
    if manifest.get("root_or_targets_private_key_in_online_step") is not False:
        raise ValueError("R20.3 transition mixed offline keys into the online step")

    root_entry = manifest.get("root")
    snapshot_entry = manifest.get("snapshot")
    targets_entry = manifest.get("targets")
    timestamp_entry = manifest.get("timestamp")
    if not all(isinstance(item, dict) for item in (root_entry, snapshot_entry, targets_entry, timestamp_entry)):
        raise ValueError("R20.3 transition manifest role entries are malformed")
    assert isinstance(root_entry, dict)
    assert isinstance(snapshot_entry, dict)
    assert isinstance(targets_entry, dict)
    assert isinstance(timestamp_entry, dict)
    if root_entry.get("sha256") != EXPECTED_ROOT_V2_SHA256 or root_entry.get("version") != 2:
        raise ValueError("transition manifest Root binding mismatch")
    if snapshot_entry.get("sha256") != EXPECTED_SNAPSHOT_SHA256 or snapshot_entry.get("version") != 4:
        raise ValueError("transition manifest Snapshot binding mismatch")
    if timestamp_entry.get("sha256") != EXPECTED_TIMESTAMP_SHA256 or timestamp_entry.get("version") != 4:
        raise ValueError("transition manifest Timestamp binding mismatch")
    if targets_entry.get("sha256") != EXPECTED_TARGETS_SHA256 or targets_entry.get("modified") is not False:
        raise ValueError("transition manifest Targets binding mismatch")

    expected_acceptance = {
        "format": "kodepoia-r20-3-full-transition-acceptance",
        "uploaded_zip_sha256": EXPECTED_ZIP_SHA256,
        "root_sha256": EXPECTED_ROOT_V2_SHA256,
        "snapshot_sha256": EXPECTED_SNAPSHOT_SHA256,
        "timestamp_sha256": EXPECTED_TIMESTAMP_SHA256,
        "transition_manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "root_version": 2,
        "targets_version": 2,
        "snapshot_version": 4,
        "timestamp_version": 4,
        "old_root_threshold_verified": True,
        "new_root_threshold_verified": True,
        "snapshot_signature_verified": True,
        "timestamp_signature_verified": True,
        "targets_bytes_unchanged": True,
        "expiry_extended": False,
        "private_material_detected": False,
        "paid_provider_required": False,
        "production_main_effect": False,
        "status": "pass",
    }
    for key, value in expected_acceptance.items():
        if acceptance.get(key) != value:
            raise ValueError(f"full-transition acceptance mismatch for {key}")

    private_marker = b"PRIVATE" + b" KEY"
    combined = root_bytes + targets_bytes + snapshot_bytes + timestamp_bytes + manifest_bytes
    if private_marker in combined.upper():
        raise ValueError("private-key marker found in public transition material")

    return {
        "format": "kodepoia-r20-3-full-transition-verification",
        "schema_version": 1,
        "root_version": 2,
        "targets_version": 2,
        "snapshot_version": 4,
        "timestamp_version": 4,
        "root_sha256": EXPECTED_ROOT_V2_SHA256,
        "snapshot_sha256": EXPECTED_SNAPSHOT_SHA256,
        "timestamp_sha256": EXPECTED_TIMESTAMP_SHA256,
        "uploaded_zip_sha256": EXPECTED_ZIP_SHA256,
        "old_root_threshold_verified": True,
        "new_root_threshold_verified": True,
        "new_online_role_signatures_verified": True,
        "targets_unchanged": True,
        "expiry_extended": False,
        "private_material_detected": False,
        "status": "pass",
    }


def main() -> int:
    report = verify_full_transition()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
