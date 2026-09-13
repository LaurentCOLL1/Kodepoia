from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = REPOSITORY_ROOT / "scripts" / "Run-TufReleaseCeremony.ps1"


def test_launcher_auto_adopts_installer_manifest_contract() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert '"installer-manifest.json"' in source
    assert "manifest.public_version" in source
    assert "manifest.source_sha" in source
    assert "manifest.sha256" in source
    assert "ExpectedAssetSize = [long](Get-Item -LiteralPath $resolvedAsset).Length" in source
    assert "installer-manifest.json ne décrit pas KodepoiaSetup.exe" in source


def test_launcher_rejects_explicit_identity_that_conflicts_with_manifest(
    tmp_path: Path,
) -> None:
    pwsh = shutil.which("pwsh") or shutil.which("powershell.exe")
    if pwsh is None:
        return

    asset = tmp_path / "KodepoiaSetup.exe"
    asset.write_bytes(b"synthetic-installer")
    (tmp_path / "installer-manifest.json").write_text(
        json.dumps(
            {
                "installer": "KodepoiaSetup.exe",
                "public_version": "1.1.0-rc6",
                "source_sha": "f" * 40,
                "sha256": "a" * 64,
            }
        ),
        encoding="utf-8",
    )
    custody = tmp_path / "custody"
    custody.mkdir()

    completed = subprocess.run(
        [
            pwsh,
            "-NoProfile",
            "-File",
            str(LAUNCHER),
            "-AssetPath",
            str(asset),
            "-PrivateCustodyDirectory",
            str(custody),
            "-PublicVersion",
            "1.1.0-rc999",
            "-SourceSha",
            "f" * 40,
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "installer-manifest.json" in combined
    assert "version publique" in combined.lower()
