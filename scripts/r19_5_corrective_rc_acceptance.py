from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from tuf.api.metadata import Metadata, Root, Snapshot, Targets, Timestamp

from kodepoia.release.corrective_rc import (
    CORRECTIVE_PUBLIC_VERSION,
    PREVIOUS_PUBLIC_VERSION,
    REQUIRED_TUF_ROLE_VERSIONS,
)
from kodepoia.release.identity import CURRENT_RELEASE

ROOT_DIR = Path(__file__).resolve().parents[1]
CUSTODY_ROOT_SHA256 = "892442754966aa643bbe15a2910aa3fef59032c8f5eade34fed62efd96aefee5"
EVIDENCE_PATH = ROOT_DIR / "configs" / "r19_5_release_evidence.json"
METADATA_DIR = ROOT_DIR / "update-repository" / "metadata"


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT_DIR, text=True
    ).strip()


def _is_ancestor(ancestor: str, descendant: str) -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=ROOT_DIR,
            check=False,
        ).returncode
        == 0
    )


def _load_metadata(name: str) -> Metadata[object]:
    return Metadata.from_bytes((METADATA_DIR / name).read_bytes())


def build_report(source_sha: str) -> dict[str, object]:
    actual = _git_head()
    if actual != source_sha:
        raise SystemExit(f"exact-source mismatch: expected {source_sha}, got {actual}")

    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    release_source_sha = str(evidence["release_source_sha"])
    installer_evidence = dict(evidence["installer"])
    tuf_evidence = dict(evidence["tuf"])
    actions_evidence = dict(evidence["github_actions"])

    pyproject = (ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8")
    installer_workflow = (
        ROOT_DIR / ".github" / "workflows" / "windows-installer.yml"
    ).read_text(encoding="utf-8")

    root_bytes = (METADATA_DIR / "root.json").read_bytes()
    targets_bytes = (METADATA_DIR / "targets.json").read_bytes()
    snapshot_bytes = (METADATA_DIR / "snapshot.json").read_bytes()
    timestamp_bytes = (METADATA_DIR / "timestamp.json").read_bytes()

    root_md = _load_metadata("root.json")
    targets_md = _load_metadata("targets.json")
    snapshot_md = _load_metadata("snapshot.json")
    timestamp_md = _load_metadata("timestamp.json")
    if not isinstance(root_md.signed, Root):
        raise SystemExit("R19.5 final root.json is not Root metadata")
    if not isinstance(targets_md.signed, Targets):
        raise SystemExit("R19.5 final targets.json is not Targets metadata")
    if not isinstance(snapshot_md.signed, Snapshot):
        raise SystemExit("R19.5 final snapshot.json is not Snapshot metadata")
    if not isinstance(timestamp_md.signed, Timestamp):
        raise SystemExit("R19.5 final timestamp.json is not Timestamp metadata")

    root = root_md.signed
    root.verify_delegate("root", root_md.signed_bytes, root_md.signatures)
    root.verify_delegate("targets", targets_md.signed_bytes, targets_md.signatures)
    root.verify_delegate("snapshot", snapshot_md.signed_bytes, snapshot_md.signatures)
    root.verify_delegate("timestamp", timestamp_md.signed_bytes, timestamp_md.signatures)
    snapshot_md.signed.meta["targets.json"].verify_length_and_hashes(targets_bytes)
    timestamp_md.signed.snapshot_meta.verify_length_and_hashes(snapshot_bytes)

    target_entries = targets_md.signed.targets
    if len(target_entries) != 1:
        raise SystemExit("R19.5 final Targets must authorize exactly one corrective target")
    target_path, target = next(iter(target_entries.items()))
    target_custom = dict(target.custom or {})
    expected_target_path = (
        "channels/beta/windows-x86_64/"
        f"{CORRECTIVE_PUBLIC_VERSION}/{release_source_sha}/KodepoiaSetup.exe"
    )
    expected_payload_url = (
        "https://github.com/LaurentCOLL1/Kodepoia/releases/download/"
        f"v{CORRECTIVE_PUBLIC_VERSION}/KodepoiaSetup.exe"
    )

    now = datetime.now(UTC)
    checks = {
        "canonical_public_version": CURRENT_RELEASE.public_version == CORRECTIVE_PUBLIC_VERSION,
        "canonical_pep440_version": CURRENT_RELEASE.pep440_version == "1.1.0rc2",
        "package_version_synchronized": 'version = "1.1.0rc2"' in pyproject,
        "installer_uses_canonical_version": "KODEPOIA_PUBLIC_VERSION" in installer_workflow
        and '-Version $env:KODEPOIA_PUBLIC_VERSION' in installer_workflow,
        "historical_previous_rc": PREVIOUS_PUBLIC_VERSION == "1.1.0-rc1",
        "release_source_is_ancestor_of_metadata_head": _is_ancestor(release_source_sha, source_sha),
        "release_artifact_run_pinned": actions_evidence["workflow_run_id"] == 34249968626
        and actions_evidence["artifact_id"] == 10066516267,
        "release_artifact_zip_digest_pinned": actions_evidence["artifact_zip_sha256"]
        == "ec326d6549b7d63cbe874d9d8c656162fec8ce49c914c320fa08b295567f1172",
        "user_custodied_root_adopted": hashlib.sha256(root_bytes).hexdigest()
        == CUSTODY_ROOT_SHA256
        == tuf_evidence["root_sha256"],
        "final_tuf_versions": targets_md.signed.version == REQUIRED_TUF_ROLE_VERSIONS["targets"]
        and snapshot_md.signed.version == REQUIRED_TUF_ROLE_VERSIONS["snapshot"]
        and timestamp_md.signed.version == REQUIRED_TUF_ROLE_VERSIONS["timestamp"],
        "final_tuf_signatures_verified": True,
        "final_tuf_cross_bindings_verified": True,
        "final_metadata_hashes_pinned": hashlib.sha256(targets_bytes).hexdigest()
        == tuf_evidence["targets_sha256"]
        and hashlib.sha256(snapshot_bytes).hexdigest() == tuf_evidence["snapshot_sha256"]
        and hashlib.sha256(timestamp_bytes).hexdigest() == tuf_evidence["timestamp_sha256"],
        "final_target_path_exact": target_path == expected_target_path,
        "final_target_installer_binding": target.length == installer_evidence["length"]
        and target.hashes.get("sha256") == installer_evidence["sha256"],
        "final_target_identity_binding": target_custom.get("source_sha") == release_source_sha
        and target_custom.get("channel") == "beta"
        and target_custom.get("public_version") == CORRECTIVE_PUBLIC_VERSION
        and target_custom.get("payload_url") == expected_payload_url
        and target_custom.get("withdrawn") is False,
        "unsigned_status_truthful": evidence["production_signed"] is False
        and "unsigned" in str(target_custom.get("signing_status", "")).lower(),
        "metadata_not_expired": root_md.signed.expires > now
        and targets_md.signed.expires > now
        and snapshot_md.signed.expires > now
        and timestamp_md.signed.expires > now,
        "public_release_not_yet_claimed": evidence["public_release_created"] is False,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise SystemExit("R19.5 acceptance failed: " + ", ".join(failed))

    return {
        "schema_version": 3,
        "subdivision": "R19.5",
        "source_sha": source_sha,
        "release_source_sha": release_source_sha,
        "status": "PASS_TO_PUBLIC_RELEASE_EFFECT",
        "checks": checks,
        "corrective_public_version": CORRECTIVE_PUBLIC_VERSION,
        "previous_public_version": PREVIOUS_PUBLIC_VERSION,
        "custody_root_sha256": CUSTODY_ROOT_SHA256,
        "installer_sha256": installer_evidence["sha256"],
        "installer_size": installer_evidence["length"],
        "metadata_versions": dict(REQUIRED_TUF_ROLE_VERSIONS),
        "manual_intervention_required": False,
        "publication_triggered": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.source_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
