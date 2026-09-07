from __future__ import annotations

import argparse
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
    targets = json.loads(
        (ROOT / "update-repository" / "metadata" / "targets.json").read_text(
            encoding="utf-8"
        )
    )
    snapshot = json.loads(
        (ROOT / "update-repository" / "metadata" / "snapshot.json").read_text(
            encoding="utf-8"
        )
    )
    timestamp = json.loads(
        (ROOT / "update-repository" / "metadata" / "timestamp.json").read_text(
            encoding="utf-8"
        )
    )

    with tempfile.TemporaryDirectory() as directory:
        fixture = Path(directory) / "KodepoiaSetup.exe"
        fixture.write_bytes(b"r19.5-exact-head-handoff-fixture")
        handoff = build_corrective_rc_handoff(fixture, source_sha=source_sha)

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
        "production_targets_not_prematurely_mutated": targets["signed"]["version"] == 1
        and targets["signed"]["targets"] == {},
        "production_snapshot_not_prematurely_mutated": snapshot["signed"]["version"] == 1,
        "production_timestamp_not_prematurely_mutated": timestamp["signed"]["version"] == 1,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise SystemExit("R19.5 acceptance failed: " + ", ".join(failed))

    return {
        "schema_version": 1,
        "subdivision": "R19.5",
        "source_sha": source_sha,
        "status": "PASS_TO_MANUAL_BOUNDARY",
        "checks": checks,
        "corrective_public_version": CORRECTIVE_PUBLIC_VERSION,
        "previous_public_version": PREVIOUS_PUBLIC_VERSION,
        "manual_intervention_required": True,
        "manual_boundary": handoff.manual_boundary,
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
