from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from kodepoia.update.seamless import INNO_UPDATE_ARGUMENTS

ROOT = Path(__file__).resolve().parents[1]


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def build_report(source_sha: str) -> dict[str, object]:
    actual = _git_head()
    if actual != source_sha:
        raise SystemExit(f"exact-source mismatch: expected {source_sha}, got {actual}")

    inno = (ROOT / "packaging" / "windows" / "Kodepoia.iss").read_text(encoding="utf-8")
    settings = (
        ROOT / "src" / "kodepoia" / "kodestudio" / "update_settings.py"
    ).read_text(encoding="utf-8")
    startup = (ROOT / "src" / "kodepoia" / "update" / "startup.py").read_text(encoding="utf-8")

    checks = {
        "fixed_inno_arguments": INNO_UPDATE_ARGUMENTS
        == (
            "/SP-",
            "/SILENT",
            "/NORESTART",
            "/CLOSEAPPLICATIONS",
            "/NORESTARTAPPLICATIONS",
            "/KODEPOIAUPDATE=1",
        ),
        "inno_update_marker": "{param:KODEPOIAUPDATE|0}" in inno,
        "inno_original_user_relaunch": "runasoriginaluser" in inno,
        "inno_automatic_restart_disabled": "RestartApplications=no" in inno,
        "ui_shutdown_after_successful_handoff": "shutdown_after_launch" in settings
        and "app.quit()" in settings,
        "startup_reconciles_previous_handoff": "reconcile_startup(CURRENT_RELEASE.public_version)"
        in startup,
        "startup_uses_seamless_coordinator": "SeamlessUpdateInstallCoordinator(" in startup,
        "no_update_url_in_launcher_arguments": all(
            "http" not in item.lower() for item in INNO_UPDATE_ARGUMENTS
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise SystemExit("R19.4 acceptance failed: " + ", ".join(failed))

    return {
        "schema_version": 1,
        "subdivision": "R19.4",
        "source_sha": source_sha,
        "status": "PASS",
        "checks": checks,
        "manual_intervention_required": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = build_report(args.source_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
