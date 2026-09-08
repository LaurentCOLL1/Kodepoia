from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from tuf.api.metadata import Metadata, Root, Snapshot, Targets, Timestamp

from kodepoia.release.identity import CURRENT_RELEASE
from kodepoia.update.bootstrap import (
    load_production_packaged_root,
    load_synthetic_packaged_root,
)
from kodepoia.update.repository_bootstrap import (
    TOP_LEVEL_TUF_ROLES,
    assert_repository_safe_payload,
    build_target_binding,
    default_production_repository_contract,
)
from kodepoia.update.trust import UpdateTargetSpec

_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SYNTHETIC_INSTALLER = b"synthetic-r19-2-kodepoia-installer\n"
_METADATA_DIR = Path("update-repository/metadata")
_EXPECTED_ROOT_SHA256 = "892442754966aa643bbe15a2910aa3fef59032c8f5eade34fed62efd96aefee5"


def _require_source_sha(value: str) -> str:
    source_sha = value.strip().lower()
    if not _SOURCE_SHA_RE.fullmatch(source_sha):
        raise ValueError("source SHA must be an exact 40-character lowercase Git commit")
    return source_sha


def _load_metadata(name: str) -> Metadata[object]:
    return Metadata.from_bytes((_METADATA_DIR / name).read_bytes())


def build_report(source_sha: str) -> dict[str, object]:
    source_sha = _require_source_sha(source_sha)
    contract = default_production_repository_contract()
    target = UpdateTargetSpec.from_release(
        CURRENT_RELEASE,
        source_sha=source_sha,
        platform="windows-x86_64",
    )
    binding = build_target_binding(
        target,
        _SYNTHETIC_INSTALLER,
        release_notes_summary="R19.2 deterministic acceptance.",
        signing_status="synthetic-test-only",
        provenance_status="synthetic-verified",
    )

    production = load_production_packaged_root()
    synthetic = load_synthetic_packaged_root(allow_synthetic=True)
    root_md = _load_metadata("root.json")
    targets_md = _load_metadata("targets.json")
    snapshot_md = _load_metadata("snapshot.json")
    timestamp_md = _load_metadata("timestamp.json")
    if not isinstance(root_md.signed, Root):
        raise RuntimeError("public root.json is not Root metadata")
    if not isinstance(targets_md.signed, Targets):
        raise RuntimeError("public targets.json is not Targets metadata")
    if not isinstance(snapshot_md.signed, Snapshot):
        raise RuntimeError("public snapshot.json is not Snapshot metadata")
    if not isinstance(timestamp_md.signed, Timestamp):
        raise RuntimeError("public timestamp.json is not Timestamp metadata")

    root = root_md.signed
    root.verify_delegate("root", root_md.signed_bytes, root_md.signatures)
    root.verify_delegate("targets", targets_md.signed_bytes, targets_md.signatures)
    root.verify_delegate("snapshot", snapshot_md.signed_bytes, snapshot_md.signatures)
    root.verify_delegate("timestamp", timestamp_md.signed_bytes, timestamp_md.signatures)
    snapshot_md.signed.meta["targets.json"].verify_length_and_hashes(
        (_METADATA_DIR / "targets.json").read_bytes()
    )
    timestamp_md.signed.snapshot_meta.verify_length_and_hashes(
        (_METADATA_DIR / "snapshot.json").read_bytes()
    )

    rendered = contract.to_bytes()
    assert_repository_safe_payload(rendered)
    assert_repository_safe_payload(json.dumps(binding.to_dict(), sort_keys=True))

    key_scopes = [set(root.roles[role].keyids) for role in TOP_LEVEL_TUF_ROLES]
    checks = {
        "metadata_https": contract.metadata_base_url.startswith("https://"),
        "payload_https": binding.payload_url.startswith("https://"),
        "top_level_roles_complete": tuple(policy.role for policy in contract.role_policies)
        == TOP_LEVEL_TUF_ROLES,
        "target_binding_complete": (
            binding.length == len(_SYNTHETIC_INSTALLER)
            and len(binding.sha256) == 64
            and binding.custom["source_sha"] == source_sha
            and binding.custom["channel"] == CURRENT_RELEASE.channel
            and binding.custom["public_version"] == CURRENT_RELEASE.public_version
        ),
        "production_root_active": production.production_trust_claim,
        "production_root_digest_pinned": production.pin.sha256 == _EXPECTED_ROOT_SHA256,
        "public_root_matches_package": (_METADATA_DIR / "root.json").read_bytes()
        == production.root_bytes,
        "production_root_distinct_from_synthetic": production.pin.sha256 != synthetic.pin.sha256,
        "root_threshold_two_of_three": root.roles["root"].threshold == 2
        and len(root.roles["root"].keyids) == 3,
        "role_key_scopes_separate": sum(len(scope) for scope in key_scopes)
        == len(set().union(*key_scopes)),
        "metadata_chain_verified": True,
        "repository_safe_private_key_boundary": True,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError(f"R19.2 acceptance failed: {failed[0]}")

    return {
        "format": "kodepoia-r19-2-update-repository-acceptance",
        "schema_version": 2,
        "source_sha": source_sha,
        "cases_total": len(checks),
        "cases_passed": len(checks),
        "checks": checks,
        "metadata_base_url": contract.metadata_base_url,
        "release_asset_base_url": contract.release_asset_base_url,
        "production_root_state": "active",
        "production_root_version": production.pin.version,
        "production_root_sha256": hashlib.sha256(production.root_bytes).hexdigest(),
        "synthetic_root_production_trust": False,
        "private_keys_persisted": False,
        "private_keys_used_by_acceptance": False,
        "initial_targets_count": len(targets_md.signed.targets),
        "r19_3_started": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit exact-head R19.2 repository acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = build_report(args.source_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
