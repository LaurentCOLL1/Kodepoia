from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from tuf.api.metadata import Metadata, Root, Snapshot, Targets, Timestamp

R20_3_ACCEPTED_HEAD = "8ebb87e0357c3fd1e9b2f1709780112847938ee8"
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


def _git_blob(commit: str, path: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"cannot read historical R20.3 blob {commit}:{path}: {detail}")
    return completed.stdout


def _parse_metadata(data: bytes, expected_type: type[object], label: str) -> Metadata[object]:
    metadata = Metadata.from_bytes(data)
    if not isinstance(metadata.signed, expected_type):
        raise ValueError(f"{label} has the wrong TUF type")
    return metadata


def _verify_current_successor_state() -> dict[str, object]:
    metadata_dir = Path("update-repository/metadata")
    root_bytes = (metadata_dir / "root.json").read_bytes()
    targets_bytes = (metadata_dir / "targets.json").read_bytes()
    snapshot_bytes = (metadata_dir / "snapshot.json").read_bytes()
    timestamp_bytes = (metadata_dir / "timestamp.json").read_bytes()

    if _sha256(root_bytes) != EXPECTED_ROOT_V2_SHA256:
        raise ValueError("current production Root is not the accepted Root v2")

    root = _parse_metadata(root_bytes, Root, "current root.json")
    targets = _parse_metadata(targets_bytes, Targets, "current targets.json")
    snapshot = _parse_metadata(snapshot_bytes, Snapshot, "current snapshot.json")
    timestamp = _parse_metadata(timestamp_bytes, Timestamp, "current timestamp.json")

    root.signed.verify_delegate("root", root.signed_bytes, root.signatures)
    root.signed.verify_delegate("targets", targets.signed_bytes, targets.signatures)
    root.signed.verify_delegate("snapshot", snapshot.signed_bytes, snapshot.signatures)
    root.signed.verify_delegate("timestamp", timestamp.signed_bytes, timestamp.signatures)

    if root.signed.version != 2:
        raise ValueError("current Root version must remain v2")
    if targets.signed.version < 2 or snapshot.signed.version < 4 or timestamp.signed.version < 4:
        raise ValueError("current metadata regressed below the accepted R20.3 generation")
    if root.signed.roles["snapshot"].keyids != [EXPECTED_SNAPSHOT_KEYID]:
        raise ValueError("current Root Snapshot authority drifted")
    if root.signed.roles["timestamp"].keyids != [EXPECTED_TIMESTAMP_KEYID]:
        raise ValueError("current Root Timestamp authority drifted")

    targets_ref = snapshot.signed.meta.get("targets.json")
    if targets_ref is None or targets_ref.version != targets.signed.version:
        raise ValueError("current Snapshot does not reference the exact current Targets version")
    targets_ref.verify_length_and_hashes(targets_bytes)

    snapshot_ref = timestamp.signed.snapshot_meta
    if snapshot_ref.version != snapshot.signed.version:
        raise ValueError("current Timestamp does not reference the exact current Snapshot version")
    snapshot_ref.verify_length_and_hashes(snapshot_bytes)

    now = datetime.now(UTC)
    if root.signed.is_expired(now):
        raise ValueError("current Root v2 is expired")
    if targets.signed.is_expired(now):
        raise ValueError("current Targets is expired")
    if snapshot.signed.is_expired(now) or timestamp.signed.is_expired(now):
        raise ValueError("current online metadata is expired")

    return {
        "root_version": root.signed.version,
        "targets_version": targets.signed.version,
        "snapshot_version": snapshot.signed.version,
        "timestamp_version": timestamp.signed.version,
        "root_sha256": _sha256(root_bytes),
        "targets_sha256": _sha256(targets_bytes),
        "snapshot_sha256": _sha256(snapshot_bytes),
        "timestamp_sha256": _sha256(timestamp_bytes),
        "metadata_chain_verified": True,
        "monotonic_from_r20_3": True,
        "online_roles_not_expired": True,
    }


def verify_full_transition() -> dict[str, object]:
    base_root_bytes = _git_blob(
        R20_3_ACCEPTED_HEAD, "docs/roadmap/R20_3_ROOT_V1_BASE.json"
    )
    unsigned_root_bytes = _git_blob(
        R20_3_ACCEPTED_HEAD, "docs/roadmap/R20_3_ROOT_V2_UNSIGNED.json"
    )
    root_bytes = _git_blob(R20_3_ACCEPTED_HEAD, "update-repository/metadata/root.json")
    targets_bytes = _git_blob(R20_3_ACCEPTED_HEAD, "update-repository/metadata/targets.json")
    snapshot_bytes = _git_blob(R20_3_ACCEPTED_HEAD, "update-repository/metadata/snapshot.json")
    timestamp_bytes = _git_blob(R20_3_ACCEPTED_HEAD, "update-repository/metadata/timestamp.json")
    manifest_bytes = _git_blob(
        R20_3_ACCEPTED_HEAD, "docs/roadmap/R20_3_FULL_TRANSITION_MANIFEST.json"
    )
    acceptance_bytes = _git_blob(
        R20_3_ACCEPTED_HEAD, "docs/roadmap/R20_3_FULL_TRANSITION_ACCEPTANCE.json"
    )

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
            raise ValueError(f"historical {label} digest mismatch: {actual}")

    base_root = _parse_metadata(base_root_bytes, Root, "R20.3 Root v1 base")
    unsigned_root = _parse_metadata(unsigned_root_bytes, Root, "R20.3 unsigned Root v2")
    root = _parse_metadata(root_bytes, Root, "R20.3 accepted Root v2")
    targets = _parse_metadata(targets_bytes, Targets, "R20.3 accepted Targets v2")
    snapshot = _parse_metadata(snapshot_bytes, Snapshot, "R20.3 accepted Snapshot v4")
    timestamp = _parse_metadata(timestamp_bytes, Timestamp, "R20.3 accepted Timestamp v4")

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
        raise ValueError(f"historical R20.3 metadata versions are not 2/2/4/4: {versions}")

    targets_ref = snapshot.signed.meta.get("targets.json")
    if targets_ref is None or targets_ref.version != 2:
        raise ValueError("historical Snapshot v4 does not reference Targets v2")
    targets_ref.verify_length_and_hashes(targets_bytes)

    snapshot_ref = timestamp.signed.snapshot_meta
    if snapshot_ref.version != 4:
        raise ValueError("historical Timestamp v4 does not reference Snapshot v4")
    snapshot_ref.verify_length_and_hashes(snapshot_bytes)

    expected_expiry = datetime.fromisoformat(EXPECTED_EXPIRES.replace("Z", "+00:00"))
    if snapshot.signed.expires != expected_expiry or timestamp.signed.expires != expected_expiry:
        raise ValueError("R20.3 historical online metadata expiry differs from accepted bridge expiry")

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
    role_entries = (root_entry, snapshot_entry, targets_entry, timestamp_entry)
    if not all(isinstance(item, dict) for item in role_entries):
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

    current = _verify_current_successor_state()

    return {
        "format": "kodepoia-r20-3-full-transition-verification",
        "schema_version": 2,
        "historical_source_sha": R20_3_ACCEPTED_HEAD,
        "historical_root_version": 2,
        "historical_targets_version": 2,
        "historical_snapshot_version": 4,
        "historical_timestamp_version": 4,
        "root_sha256": EXPECTED_ROOT_V2_SHA256,
        "historical_snapshot_sha256": EXPECTED_SNAPSHOT_SHA256,
        "historical_timestamp_sha256": EXPECTED_TIMESTAMP_SHA256,
        "uploaded_zip_sha256": EXPECTED_ZIP_SHA256,
        "old_root_threshold_verified": True,
        "new_root_threshold_verified": True,
        "historical_online_role_signatures_verified": True,
        "historical_targets_unchanged": True,
        "historical_expiry_extended": False,
        "private_material_detected": False,
        "current_successor": current,
        "status": "pass",
    }


def main() -> int:
    report = verify_full_transition()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
