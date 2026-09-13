from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = REPOSITORY_ROOT / "scripts" / "Run-TufReleaseCeremony.ps1"
RELEASE_IDENTITY = REPOSITORY_ROOT / "src" / "kodepoia" / "release" / "release_identity.json"
REPORT = REPOSITORY_ROOT / "artifacts" / "tuf_ceremony" / "ceremony-report.json"


def _powershell() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell.exe")


def _public_version() -> str:
    payload = json.loads(RELEASE_IDENTITY.read_text(encoding="utf-8"))
    version = payload["version"]
    return (
        f"{version['major']}.{version['minor']}.{version['patch']}-"
        f"{version['stage']}{version['serial']}"
    )


def _write_fake_python(directory: Path) -> None:
    if os.name == "nt":
        (directory / "python.cmd").write_text(
            "@echo off\r\n"
            'if "%~1"=="-c" exit /b 0\r\n'
            "echo FAKE_PYTHON_ARGS:%*\r\n"
            "exit /b 1\r\n",
            encoding="utf-8",
        )
        return

    fake = directory / "python"
    fake.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "-c" ]; then exit 0; fi\n'
        "printf 'FAKE_PYTHON_ARGS:'\n"
        "printf ' <%s>' \"$@\"\n"
        "printf '\\n'\n"
        "exit 1\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)


def _write_failing_python_candidates(directory: Path) -> None:
    if os.name == "nt":
        body = "@echo off\r\nexit /b 1\r\n"
        (directory / "python.cmd").write_text(body, encoding="utf-8")
        (directory / "py.cmd").write_text(body, encoding="utf-8")
        return

    for name in ("python", "py"):
        fake = directory / name
        fake.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        fake.chmod(0o755)


def _write_manifest(asset: Path, source_sha: str) -> None:
    data = asset.read_bytes()
    (asset.parent / "installer-manifest.json").write_text(
        json.dumps(
            {
                "installer": "KodepoiaSetup.exe",
                "public_version": _public_version(),
                "source_sha": source_sha,
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        ),
        encoding="utf-8",
    )


def test_launcher_auto_adopts_installer_manifest_contract() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert '"installer-manifest.json"' in source
    assert "manifest.public_version" in source
    assert "manifest.source_sha" in source
    assert "manifest.sha256" in source
    assert "ExpectedAssetSize = [long](Get-Item -LiteralPath $resolvedAsset).Length" in source
    assert "installer-manifest.json ne décrit pas KodepoiaSetup.exe" in source


def test_launcher_serializes_asset_size_without_nullable_value_property() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert "$ExpectedAssetSize.Value" not in source
    assert '([long]$ExpectedAssetSize).ToString()' in source
    assert '$currentStage = "construction des arguments de cérémonie"' in source


def test_launcher_requires_tuf_ready_python_and_prefers_repo_venv() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert 'Join-Path $RepoRoot ".venv\\Scripts\\python.exe"' in source
    assert "from securesystemslib.signer import Signer" in source
    assert "from tuf.api.metadata import Metadata" in source
    assert "import kodepoia.update.online_signing" in source
    assert "import kodepoia.update.zero_cost_signing" in source
    assert '$currentStage = "détection de Python 3.12+ et des dépendances TUF"' in source
    assert source.index("Resolve-PythonCommand -RepoRoot $repoRoot") < source.index(
        '$currentStage = "découverte des seeds Snapshot/Timestamp"'
    )


def test_launcher_rejects_explicit_identity_that_conflicts_with_manifest(
    tmp_path: Path,
) -> None:
    pwsh = _powershell()
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
        errors="replace",
    )
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "installer-manifest.json" in combined
    assert "version publique" in combined.lower()


def test_launcher_passes_auto_asset_size_to_python_without_value_property(
    tmp_path: Path,
) -> None:
    pwsh = _powershell()
    if pwsh is None:
        return

    asset_bytes = b"synthetic-installer-for-nullable-size-regression"
    asset = tmp_path / "KodepoiaSetup.exe"
    asset.write_bytes(asset_bytes)
    source_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        text=True,
    ).strip()
    _write_manifest(asset, source_sha)

    custody = tmp_path / "custody"
    custody.mkdir()
    (custody / "TUF_SNAPSHOT_ED25519_SEED_B64.txt").write_text("snapshot-test", encoding="utf-8")
    (custody / "TUF_TIMESTAMP_ED25519_SEED_B64.txt").write_text("timestamp-test", encoding="utf-8")

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    _write_fake_python(fake_bin)
    env = os.environ.copy()
    env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")

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
        ],
        cwd=REPOSITORY_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=30,
    )
    combined = completed.stdout + completed.stderr
    assert "=== Kodepoia TUF Release Ceremony ===" in combined
    assert "FAKE_PYTHON_ARGS:" in combined
    assert "--expected-asset-size" in combined
    assert str(len(asset_bytes)) in combined
    assert "propriété « Value »" not in combined
    assert "property 'Value'" not in combined


def test_launcher_refreshes_blocked_report_when_python_dependencies_are_missing(
    tmp_path: Path,
) -> None:
    pwsh = _powershell()
    if pwsh is None:
        return

    asset = tmp_path / "KodepoiaSetup.exe"
    asset.write_bytes(b"synthetic-installer-for-python-dependency-preflight")
    source_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        text=True,
    ).strip()
    _write_manifest(asset, source_sha)
    custody = tmp_path / "custody"
    custody.mkdir()

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    _write_failing_python_candidates(fake_bin)
    env = os.environ.copy()
    env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")

    REPORT.unlink(missing_ok=True)
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
        ],
        cwd=REPOSITORY_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=30,
    )

    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "Aucun Python 3.12+" in combined
    assert "TUF" in combined
    payload = json.loads(REPORT.read_text(encoding="utf-8-sig"))
    assert payload["status"] == "BLOCKED"
    assert payload["generation"] is None
    assert payload["errors_encountered"][0]["code"] == "POWERSHELL_PREFLIGHT_BLOCKED"
    message = payload["errors_encountered"][0]["message"]
    assert "Python 3.12+" in message
    assert "TUF" in message
    assert payload["private_material_in_report"] is False
    assert payload["private_key_paths_in_report"] is False
    assert payload["secret_values_emitted"] is False
