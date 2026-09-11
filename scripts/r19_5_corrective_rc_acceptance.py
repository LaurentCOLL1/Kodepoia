from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tomllib
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from tuf.api.metadata import Metadata, Root, Snapshot, Targets, Timestamp

from kodepoia.release.corrective_rc import (
    CORRECTIVE_PUBLIC_VERSION,
    PREVIOUS_PUBLIC_VERSION,
    REQUIRED_TUF_ROLE_VERSIONS,
)
from kodepoia.release.identity import CURRENT_RELEASE, ReleaseIdentity

ROOT_DIR = Path(__file__).resolve().parents[1]
CUSTODY_ROOT_SHA256 = (
    "892442754966aa643bbe15a2910aa3fef59032c8f5eade34fed62efd96aefee5"
)
EVIDENCE_PATH = ROOT_DIR / "configs" / "r19_5_release_evidence.json"
METADATA_DIR = ROOT_DIR / "update-repository" / "metadata"
GITHUB_API = "https://api.github.com/repos/LaurentCOLL1/Kodepoia"


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT_DIR, text=True
    ).strip()


def _is_ancestor(ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT_DIR,
        check=False,
    )
    return result.returncode == 0


def _load_metadata(name: str) -> Metadata[object]:
    return Metadata.from_bytes((METADATA_DIR / name).read_bytes())


def _github_json(url: str) -> dict[str, object]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Kodepoia-R19.5-acceptance",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"GitHub API returned non-object payload for {url}")
    return payload


def _verify_public_release(
    evidence: dict[str, object], release_source_sha: str
) -> dict[str, bool]:
    expected = dict(evidence["public_release"])
    tag = str(expected["tag"])
    release = _github_json(f"{GITHUB_API}/releases/tags/{tag}")
    tag_ref = _github_json(f"{GITHUB_API}/git/ref/tags/{tag}")
    tag_object = dict(tag_ref["object"])
    annotated_tag = _github_json(f"{GITHUB_API}/git/tags/{tag_object['sha']}")
    annotated_target = dict(annotated_tag["object"])

    expected_assets = dict(expected["assets"])
    actual_assets = {
        str(asset["name"]): asset
        for asset in release.get("assets", [])
        if isinstance(asset, dict) and "name" in asset
    }
    asset_checks = []
    for name, raw_expected_asset in expected_assets.items():
        expected_asset = dict(raw_expected_asset)
        actual_asset = actual_assets.get(name)
        if not isinstance(actual_asset, dict):
            asset_checks.append(False)
            continue
        asset_checks.append(
            actual_asset.get("id") == expected_asset["asset_id"]
            and actual_asset.get("size") == expected_asset["length"]
            and actual_asset.get("digest")
            == f"sha256:{expected_asset['sha256']}"
            and actual_asset.get("state") == "uploaded"
        )

    return {
        "public_release_recorded": evidence["public_release_created"] is True,
        "public_release_identity_verified": (
            release.get("id") == expected["release_id"]
            and release.get("tag_name") == tag
            and release.get("name") == expected["name"]
            and release.get("draft") is False
            and release.get("prerelease") is True
            and release.get("published_at") == expected["published_at"]
        ),
        "public_release_tag_verified": (
            tag_object.get("type") == "tag"
            and tag_object.get("sha") == expected["tag_object_sha"]
            and annotated_tag.get("tag") == tag
            and annotated_target.get("type") == "commit"
            and annotated_target.get("sha") == release_source_sha
            and annotated_target.get("sha") == expected["target_commit_sha"]
        ),
        "public_release_assets_verified": (
            set(actual_assets) == set(expected_assets) and all(asset_checks)
        ),
    }


def _historical_rc2_identity() -> ReleaseIdentity:
    return ReleaseIdentity(
        schema_version=1,
        product="Kodepoia",
        package="kodepoia",
        channel="beta",
        build_type="prerelease",
        source_binding="exact-head",
        major=1,
        minor=1,
        patch=0,
        stage="rc",
        serial=2,
    )


def _generation_matches_or_advances(
    *, current_version: int, current_bytes: bytes, historical_version: int, historical_sha256: str
) -> bool:
    if current_version < historical_version:
        return False
    if current_version == historical_version:
        return hashlib.sha256(current_bytes).hexdigest() == historical_sha256
    return True


def build_report(source_sha: str) -> dict[str, object]:
    actual = _git_head()
    if actual != source_sha:
        raise SystemExit(f"exact-source mismatch: expected {source_sha}, got {actual}")

    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    release_source_sha = str(evidence["release_source_sha"])
    installer_evidence = dict(evidence["installer"])
    tuf_evidence = dict(evidence["tuf"])
    actions_evidence = dict(evidence["github_actions"])

    pyproject = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8"))
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
        raise SystemExit("R19.5 current root.json is not Root metadata")
    if not isinstance(targets_md.signed, Targets):
        raise SystemExit("R19.5 current targets.json is not Targets metadata")
    if not isinstance(snapshot_md.signed, Snapshot):
        raise SystemExit("R19.5 current snapshot.json is not Snapshot metadata")
    if not isinstance(timestamp_md.signed, Timestamp):
        raise SystemExit("R19.5 current timestamp.json is not Timestamp metadata")

    root = root_md.signed
    root.verify_delegate("root", root_md.signed_bytes, root_md.signatures)
    root.verify_delegate("targets", targets_md.signed_bytes, targets_md.signatures)
    root.verify_delegate("snapshot", snapshot_md.signed_bytes, snapshot_md.signatures)
    root.verify_delegate(
        "timestamp", timestamp_md.signed_bytes, timestamp_md.signatures
    )
    snapshot_md.signed.meta["targets.json"].verify_length_and_hashes(targets_bytes)
    timestamp_md.signed.snapshot_meta.verify_length_and_hashes(snapshot_bytes)

    expected_target_path = (
        "channels/beta/windows-x86_64/"
        f"{CORRECTIVE_PUBLIC_VERSION}/{release_source_sha}/KodepoiaSetup.exe"
    )
    target = targets_md.signed.targets.get(expected_target_path)
    if target is None:
        raise SystemExit("R19.5 historical rc2 target is no longer authorized")
    target_custom = dict(target.custom or {})
    expected_payload_url = (
        "https://github.com/LaurentCOLL1/Kodepoia/releases/download/"
        f"v{CORRECTIVE_PUBLIC_VERSION}/KodepoiaSetup.exe"
    )

    corrective_identity = _historical_rc2_identity()
    current_not_older = (
        CURRENT_RELEASE.pep440_version == corrective_identity.pep440_version
        or CURRENT_RELEASE.is_newer_than(corrective_identity)
    )
    historical_hashes_well_formed = all(
        isinstance(tuf_evidence.get(name), str)
        and len(str(tuf_evidence[name])) == 64
        and all(char in "0123456789abcdef" for char in str(tuf_evidence[name]))
        for name in (
            "root_sha256",
            "targets_sha256",
            "snapshot_sha256",
            "timestamp_sha256",
        )
    )

    now = datetime.now(UTC)
    checks = {
        "canonical_public_version": current_not_older,
        "canonical_pep440_version": current_not_older,
        "package_version_synchronized": (
            pyproject["project"]["version"] == CURRENT_RELEASE.pep440_version
        ),
        "installer_uses_canonical_version": (
            "KODEPOIA_PUBLIC_VERSION" in installer_workflow
            and '-Version $env:KODEPOIA_PUBLIC_VERSION' in installer_workflow
        ),
        "historical_previous_rc": PREVIOUS_PUBLIC_VERSION == "1.1.0-rc1",
        "historical_corrective_rc": (
            corrective_identity.public_version == CORRECTIVE_PUBLIC_VERSION
            and str(evidence["public_version"]) == CORRECTIVE_PUBLIC_VERSION
        ),
        "release_source_is_ancestor_of_metadata_head": _is_ancestor(
            release_source_sha, source_sha
        ),
        "release_artifact_run_pinned": (
            actions_evidence["workflow_run_id"] == 34249968626
            and actions_evidence["artifact_id"] == 10066516267
        ),
        "release_artifact_zip_digest_pinned": (
            actions_evidence["artifact_zip_sha256"]
            == "ec326d6549b7d63cbe874d9d8c656162fec8ce49c914c320fa08b295567f1172"
        ),
        "user_custodied_root_adopted": (
            tuf_evidence["root_sha256"] == CUSTODY_ROOT_SHA256
            and root_md.signed.version >= int(tuf_evidence["root_version"])
        ),
        "final_tuf_versions": (
            targets_md.signed.version >= REQUIRED_TUF_ROLE_VERSIONS["targets"]
            and snapshot_md.signed.version >= REQUIRED_TUF_ROLE_VERSIONS["snapshot"]
            and timestamp_md.signed.version >= REQUIRED_TUF_ROLE_VERSIONS["timestamp"]
        ),
        "final_tuf_signatures_verified": True,
        "final_tuf_cross_bindings_verified": True,
        "final_metadata_hashes_pinned": (
            historical_hashes_well_formed
            and _generation_matches_or_advances(
                current_version=root_md.signed.version,
                current_bytes=root_bytes,
                historical_version=int(tuf_evidence["root_version"]),
                historical_sha256=str(tuf_evidence["root_sha256"]),
            )
            and _generation_matches_or_advances(
                current_version=targets_md.signed.version,
                current_bytes=targets_bytes,
                historical_version=int(tuf_evidence["targets_version"]),
                historical_sha256=str(tuf_evidence["targets_sha256"]),
            )
            and _generation_matches_or_advances(
                current_version=snapshot_md.signed.version,
                current_bytes=snapshot_bytes,
                historical_version=int(tuf_evidence["snapshot_version"]),
                historical_sha256=str(tuf_evidence["snapshot_sha256"]),
            )
            and _generation_matches_or_advances(
                current_version=timestamp_md.signed.version,
                current_bytes=timestamp_bytes,
                historical_version=int(tuf_evidence["timestamp_version"]),
                historical_sha256=str(tuf_evidence["timestamp_sha256"]),
            )
        ),
        "final_target_path_exact": expected_target_path in targets_md.signed.targets,
        "final_target_installer_binding": (
            target.length == installer_evidence["length"]
            and target.hashes.get("sha256") == installer_evidence["sha256"]
        ),
        "final_target_identity_binding": (
            target_custom.get("source_sha") == release_source_sha
            and target_custom.get("channel") == "beta"
            and target_custom.get("public_version") == CORRECTIVE_PUBLIC_VERSION
            and target_custom.get("payload_url") == expected_payload_url
            and target_custom.get("withdrawn") is False
        ),
        "unsigned_status_truthful": (
            evidence["production_signed"] is False
            and "unsigned" in str(target_custom.get("signing_status", "")).lower()
        ),
        "metadata_not_expired": (
            root_md.signed.expires > now
            and targets_md.signed.expires > now
            and snapshot_md.signed.expires > now
            and timestamp_md.signed.expires > now
        ),
    }
    checks.update(_verify_public_release(evidence, release_source_sha))
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise SystemExit("R19.5 acceptance failed: " + ", ".join(failed))

    return {
        "schema_version": 5,
        "subdivision": "R19.5",
        "source_sha": source_sha,
        "release_source_sha": release_source_sha,
        "status": "PASS_PUBLIC_RELEASE_VERIFIED",
        "checks": checks,
        "corrective_public_version": CORRECTIVE_PUBLIC_VERSION,
        "current_public_version": CURRENT_RELEASE.public_version,
        "previous_public_version": PREVIOUS_PUBLIC_VERSION,
        "custody_root_sha256": CUSTODY_ROOT_SHA256,
        "installer_sha256": installer_evidence["sha256"],
        "installer_size": installer_evidence["length"],
        "historical_metadata_versions": dict(REQUIRED_TUF_ROLE_VERSIONS),
        "current_metadata_versions": {
            "root": root_md.signed.version,
            "targets": targets_md.signed.version,
            "snapshot": snapshot_md.signed.version,
            "timestamp": timestamp_md.signed.version,
        },
        "manual_intervention_required": False,
        "publication_triggered": True,
        "public_release_id": dict(evidence["public_release"])["release_id"],
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
