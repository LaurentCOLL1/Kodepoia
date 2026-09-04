from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import kodepoia
from kodepoia.release_identity import CURRENT_RELEASE, ReleaseIdentity


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, encoding="utf-8"
    ).strip().lower()


def _release(
    *,
    channel: str,
    stage: str,
    serial: int,
    major: int = 1,
    minor: int = 1,
    patch: int = 0,
) -> ReleaseIdentity:
    return ReleaseIdentity(
        schema_version=1,
        product="Kodepoia",
        channel=channel,
        major=major,
        minor=minor,
        patch=patch,
        stage=stage,
        serial=serial,
    )


def build_acceptance(*, root: Path, source_sha: str) -> dict[str, Any]:
    exact_source = source_sha.strip().lower()
    if _git_head(root) != exact_source:
        raise RuntimeError("R18.1 acceptance source SHA does not match checked-out HEAD")

    identity_path = root / "src/kodepoia/release_identity.json"
    identity_payload = json.loads(identity_path.read_text(encoding="utf-8"))
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    iss = (root / "packaging/windows/Kodepoia.iss").read_text(encoding="utf-8")
    build_script = (root / "scripts/build_windows_installer.ps1").read_text(encoding="utf-8")
    ui = (root / "src/kodepoia/kodestudio/app_v11.py").read_text(encoding="utf-8")

    cli = subprocess.run(
        [sys.executable, "-m", "kodepoia.cli", "--version"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    ordered = [
        _release(channel="nightly", stage="dev", serial=1),
        _release(channel="nightly", stage="dev", serial=2),
        _release(channel="beta", stage="a", serial=1),
        _release(channel="beta", stage="b", serial=1),
        _release(channel="beta", stage="rc", serial=1),
        _release(channel="stable", stage="final", serial=0),
    ]
    expected_pep440_order = [
        "1.1.0.dev1",
        "1.1.0.dev2",
        "1.1.0a1",
        "1.1.0b1",
        "1.1.0rc1",
        "1.1.0",
    ]
    next_nightly = _release(channel="nightly", stage="dev", serial=1, minor=2)

    checks = {
        "exact_source_bound": _git_head(root) == exact_source,
        "single_machine_identity_schema": identity_payload == {
            "schema_version": 1,
            "product": "Kodepoia",
            "channel": "beta",
            "version": {"major": 1, "minor": 1, "patch": 0, "stage": "rc", "serial": 1},
        },
        "canonical_channel_beta": CURRENT_RELEASE.channel == "beta",
        "canonical_pep440_version": CURRENT_RELEASE.pep440_version == "1.1.0rc1",
        "canonical_display_version": CURRENT_RELEASE.display_version == "1.1.0-rc1",
        "package_version_derived": kodepoia.__version__ == CURRENT_RELEASE.pep440_version,
        "pyproject_matches_canonical": pyproject["project"]["version"] == CURRENT_RELEASE.pep440_version,
        "cli_matches_canonical": cli == "kodepoia 1.1.0-rc1 (beta)",
        "inno_requires_external_canonical_version": (
            '#define AppVersion "1.1.0-rc1"' not in iss
            and "#error AppVersion must be supplied from the canonical Kodepoia release identity" in iss
            and "AppVersion={#AppVersion}" in iss
        ),
        "windows_builder_reads_and_validates_canonical": (
            '[string]$Version = ""' in build_script
            and "from kodepoia.release_identity import CURRENT_RELEASE" in build_script
            and "does not match canonical release identity" in build_script
            and "pep440_version" in build_script
            and "release_identity_schema" in build_script
        ),
        "ui_version_surface_bound": (
            'setProperty("kodepoiaReleaseVersion", CURRENT_RELEASE.display_version)' in ui
            and 'setProperty("kodepoiaReleaseChannel", CURRENT_RELEASE.channel)' in ui
        ),
        "pep440_precedence_contract": (
            [item.pep440_version for item in ordered] == expected_pep440_order
            and all(new.is_newer_than(old) for old, new in zip(ordered[:-1], ordered[1:], strict=True))
        ),
        "channel_transition_contract": (
            ordered[1].can_transition_to(ordered[4])
            and ordered[4].can_transition_to(ordered[5])
            and not ordered[5].can_transition_to(ordered[4])
            and ordered[5].can_transition_to(next_nightly)
        ),
        "no_external_release_effects": True,
    }
    if not all(checks.values()):
        failed = sorted(name for name, passed in checks.items() if not passed)
        raise RuntimeError(f"R18.1 acceptance failed: {', '.join(failed)}")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "R18.1",
        "source_sha": exact_source,
        "release_identity_sha256": _sha256(identity_path),
        "release": CURRENT_RELEASE.to_dict(),
        "cli_version": cli,
        "checks": checks,
        "production_signing_triggered": False,
        "public_github_release_triggered": False,
        "public_winget_submission_triggered": False,
        "manual_state": "NONE",
    }
    payload["acceptance_sha256"] = hashlib.sha256(
        _canonical_json(payload).encode("utf-8")
    ).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic R18.1 release identity acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", default="artifacts/r18_1_release_identity_acceptance.json")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path

    payload = build_acceptance(root=root, source_sha=args.source_sha)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
