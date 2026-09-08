from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from kodepoia.release.corrective_rc import (
    CORRECTIVE_PUBLIC_VERSION,
    PREVIOUS_PUBLIC_VERSION,
    REQUIRED_TUF_ROLE_VERSIONS,
    build_corrective_rc_handoff,
)
from kodepoia.release.identity import CURRENT_RELEASE

ROOT = Path(__file__).resolve().parents[1]
CUSTODY_ROOT_SHA256 = "892442754966aa643bbe15a2910aa3fef59032c8f5eade34fed62efd96aefee5"


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def build_report(source_sha: str) -> dict[str, object]:
    actual = _git_head()
    if actual != source_sha:
        raise SystemExit(f"exact-source mismatch: expected {source_sha}, got {actual}")

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    installer_workflow = (
        ROOT / ".github" / "workflows" / "windows-installer.yml"
    ).read_text(encoding="utf-8")
    metadata_dir = ROOT / "update-repository" / "metadata"
    root_bytes = (metadata_dir / "root.json").read_bytes()
    targets = json.loads((metadata_dir / "targets.json").read_text(encoding="utf-8"))
    snapshot = json.loads((metadata_dir / "snapshot.json").read_text(encoding="utf-8"))
    timestamp = json.loads((metadata_dir / "timestamp.json").read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as directory:
        fixture = Path(directory) / "KodepoiaSetup.exe"
        fixture.write_bytes(b"r19.5-exact-head-handoff-fixture")
        handoff = build_corrective_rc_handoff(fixture, source_sha=source_sha)

    target_entries = dict(targets["signed"]["targets"])
    staged_target_path = next(iter(target_entries), "")
    staged_target = target_entries.get(staged_target_path, {})
    staged_custom = dict(staged_target.get("custom", {})) if isinstance(staged_target, dict) else {}
    staged_source_sha = str(staged_custom.get("source_sha", ""))

    checks = {
        "canonical_public_version": CURRENT_RELEASE.public_version == CORRECTIVE_PUBLIC_VERSION,
        "canonical_pep440_version": CURRENT_RELEASE.pep440_version == "1.1.0rc2",
        "package_version_synchronized": 'version = "1.1.0rc2"' in pyproject,
        "installer_uses_canonical_version": "KODEPOIA_PUBLIC_VERSION" in installer_workflow
        and '-Version $env:KODEPOIA_PUBLIC_VERSION' in installer_workflow,
        "installer_rc1_literal_removed": '-Version "1.1.0-rc1"' not in installer_workflow,
        "historical_previous_rc": PREVIOUS_PUBLIC_VERSION == "1.1.0-rc1",
        "handoff_exact_source": handoff.source_sha == source_sha,
        "handoff_rc2_target": f"/1.1.0-rc2/{source_sha}/KodepoiaSetup.exe"
        in handoff.target_path,
        "handoff_no_public_effect": handoff.publication_triggered is False,
        "handoff_unsigned_truthful": handoff.production_signed is False
        and "unsigned" in str(handoff.target_custom["signing_status"]).lower(),
        "manual_tuf_boundary_explicit": handoff.manual_boundary["required"] is True
        and handoff.tuf_role_versions == REQUIRED_TUF_ROLE_VERSIONS,
        "user_custodied_root_adopted": hashlib.sha256(root_bytes).hexdigest()
        == CUSTODY_ROOT_SHA256,
        "custody_targets_staged_v2": targets["signed"]["version"] == 2
        and len(target_entries) == 1,
        "custody_snapshot_staged_v2": snapshot["signed"]["version"] == 2,
        "custody_timestamp_staged_v2": timestamp["signed"]["version"] == 2,
        "staged_metadata_requires_exact_head_resign": bool(staged_source_sha)
        and staged_source_sha != source_sha,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise SystemExit("R19.5 acceptance failed: " + ", ".join(failed))

    return {
        "schema_version": 2,
        "subdivision": "R19.5",
        "source_sha": source_sha,
        "status": "PASS_TO_FINAL_TUF_RESIGN_BOUNDARY",
        "checks": checks,
        "corrective_public_version": CORRECTIVE_PUBLIC_VERSION,
        "previous_public_version": PREVIOUS_PUBLIC_VERSION,
        "custody_root_sha256": CUSTODY_ROOT_SHA256,
        "staged_metadata_source_sha": staged_source_sha,
        "manual_intervention_required": True,
        "manual_boundary": {
            **handoff.manual_boundary,
            "reason": (
                "The user-custodied Root is now embedded in source. Rebuild exact-head rc2, then "
                "re-sign Targets/Snapshot/Timestamp with the existing private role keys so the "
                "metadata binds the final installer bytes and final source SHA."
            ),
            "generate_new_root_keys": False,
        },
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
