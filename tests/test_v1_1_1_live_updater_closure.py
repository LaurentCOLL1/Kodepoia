from __future__ import annotations

import importlib.util
import tomllib
from pathlib import Path

from kodepoia.release.identity import CURRENT_RELEASE

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "v1_1_1_live_updater_closure.py"
WORKFLOW = ROOT / ".github" / "workflows" / "v1-1-1-live-updater-closure.yml"


def _module():
    spec = importlib.util.spec_from_file_location("v111_live_closure", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v111_exact_source_and_identity() -> None:
    module = _module()
    assert module.BASELINE_VERSION == module.baseline_identity().public_version == "1.1.0"
    assert module.BASELINE_SOURCE_SHA == "46ed800888b4f19da9e984232dd1ad6cdb639cc1"
    assert module.TARGET_VERSION == CURRENT_RELEASE.public_version == "1.1.1"
    assert CURRENT_RELEASE.is_newer_than(module.baseline_identity())
    assert module.TARGET_SOURCE_SHA == "aa1c80389b10f5ef44737241bf192c04f847e4ec"
    assert module.TARGET_SIZE == 38_880_869
    assert module.TARGET_SHA256 == (
        "c8e7949ead2e1e14adece7cb9826f0b1be689b81ac814eef2f041760b9f738cd"
    )
    assert module.TARGET_PATH == (
        "channels/stable/windows-x86_64/1.1.1/"
        "aa1c80389b10f5ef44737241bf192c04f847e4ec/KodepoiaSetup.exe"
    )


def test_v111_workflow_main_only_network_based_read_only() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in source
    assert "github.ref == 'refs/heads/main'" in source
    assert "permissions:\n  contents: read\n  actions: read" in source
    assert "windows-latest" in source
    assert "scripts/v1_1_1_live_updater_closure.py" in source
    assert "v1.1.0" in source and "v1.1.1" in source
    assert "Revalidate exact public 1.1.1 tag release and asset" in source
    assert "gh release create" not in source
    assert "gh release upload" not in source
    assert "contents: write" not in source
    assert "git push" not in source
    assert "/KODEPOIAUPDATE=1" in source
    assert "V1_1_1_LIVE_UPDATER_CLOSURE.json" in source


def test_v111_workflow_requires_installed_real_upgrade_and_cleanup() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    for marker in (
        "Install exact public baseline",
        "Discover and verify live stable update from installed baseline",
        "Upgrade installed baseline from live verified public bytes",
        "Prove stable 1.1.1 is current on the live updater",
        "Packaged smoke and uninstall live-upgraded Kodepoia",
        "Emit terminal 1.1.1 live closure evidence",
        'discovery_status -ne "update-available"',
        'discovery_status -ne "up-to-date"',
        "TARGET_SHA256",
        "BASELINE_SHA256",
        "custom_install_directory_preserved",
        "relaunch_observed",
        "production_tuf_versions",
        "winget_submission",
    ):
        assert marker in source, marker
    assert "$update.WaitForExit()" in source


def test_v111_closed_fail_guards_reject_stale_tuf_versions() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'expected_tuf = {"root_version": 2, "targets_version": 10, "snapshot_version": 12, "timestamp_version": 12}' in source
    assert 'raise SystemExit(f"live TUF {role} drift:' in source
    assert 'mode == "baseline"' in source
    assert 'PowerShellInstallerIdentityVerifier()' in source
    assert 'PolicyVerifiedUpdateDownloader(' in source
    assert 'NetworkUpdateTransport()' in source
    assert '"public_network_proof": True' in source
    assert '"production_metadata_mutated": False' in source
    assert '"public_release_mutated": False' in source

def test_windows_ui_dependency_stays_on_qualified_qt_series() -> None:
    """The 1.1.1 CI baseline passed on PySide6 6.11.2, not 6.12.0."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "PySide6>=6.10,<6.12" in pyproject["project"]["optional-dependencies"]["ui"]
