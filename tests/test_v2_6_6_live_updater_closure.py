from __future__ import annotations

from pathlib import Path

from kodepoia.release.identity import CURRENT_RELEASE
from scripts.v2_6_6_live_updater_closure import (
    RC8_SOURCE_SHA,
    RC8_VERSION,
    STABLE_SHA256,
    STABLE_SIZE,
    STABLE_SOURCE_SHA,
    STABLE_TARGET,
    STABLE_VERSION,
    rc8_identity,
)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "v2-6-6-live-updater-closure.yml"


def test_v266_live_closure_freezes_exact_public_identities() -> None:
    rc8 = rc8_identity()
    assert rc8.public_version == RC8_VERSION == "1.1.0-rc8"
    assert RC8_SOURCE_SHA == "fa787ab7ef76f2556b56ac1f058916a1425455af"

    assert CURRENT_RELEASE.public_version == STABLE_VERSION == "1.1.0"
    assert CURRENT_RELEASE.channel == "stable"
    assert CURRENT_RELEASE.build_type == "release"
    assert STABLE_SOURCE_SHA == "46ed800888b4f19da9e984232dd1ad6cdb639cc1"
    assert STABLE_SIZE == 38_834_833
    assert STABLE_SHA256 == (
        "8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef"
    )
    assert STABLE_TARGET == (
        "channels/stable/windows-x86_64/1.1.0/"
        "46ed800888b4f19da9e984232dd1ad6cdb639cc1/KodepoiaSetup.exe"
    )


def test_v266_live_closure_workflow_is_main_only_read_only_and_public() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in source
    assert "github.ref == 'refs/heads/main'" in source
    assert "permissions:\n  contents: read\n  actions: read" in source
    assert "windows-latest" in source
    assert "NetworkUpdateTransport" not in source
    assert "scripts/v2_6_6_live_updater_closure.py" in source
    assert "v1.1.0-rc8" in source
    assert "v1.1.0" in source
    assert "update-repository/metadata" not in source
    assert "gh release create" not in source
    assert "gh release upload" not in source
    assert "contents: write" not in source
    assert "git push" not in source
    assert "winget" not in source.lower() or "winget_submission" in source
    assert "V2_6_6_LIVE_UPDATER_CLOSURE.json" in source


def test_v266_live_closure_requires_real_install_and_post_upgrade_current_state() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    for marker in (
        "Install exact public rc8 baseline",
        "Discover and verify live stable update from installed rc8 baseline",
        "Upgrade installed rc8 from live verified public bytes",
        "Prove stable 1.1.0 is current on the live updater",
        "Packaged smoke and uninstall live-upgraded Kodepoia",
        "Emit terminal V2.6.6 live closure evidence",
    ):
        assert marker in source, marker
    assert "/KODEPOIAUPDATE=1" in source
    assert "$update.WaitForExit()" in source
    assert 'discovery_status -ne "update-available"' in source
    assert 'discovery_status -ne "up-to-date"' in source
