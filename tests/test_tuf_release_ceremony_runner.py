from __future__ import annotations

import py_compile
import shutil
import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PYTHON_RUNNER = REPOSITORY_ROOT / "scripts" / "tuf_release_ceremony.py"
POWERSHELL_LAUNCHER = REPOSITORY_ROOT / "scripts" / "Run-TufReleaseCeremony.ps1"


def test_python_ceremony_runner_compiles_and_exposes_help(tmp_path: Path) -> None:
    py_compile.compile(
        str(PYTHON_RUNNER),
        cfile=str(tmp_path / "tuf_release_ceremony.pyc"),
        doraise=True,
    )
    completed = subprocess.run(
        [sys.executable, str(PYTHON_RUNNER), "--help"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "fail-closed" in completed.stdout
    assert "--offline-key-dir" in completed.stdout
    assert "--expected-root-sha256" in completed.stdout
    assert "--apply" in completed.stdout


def test_ceremony_sources_preserve_private_material_boundary() -> None:
    python_source = PYTHON_RUNNER.read_text(encoding="utf-8")
    powershell_source = POWERSHELL_LAUNCHER.read_text(encoding="utf-8")

    assert '"secret_values_emitted": False' in python_source
    assert '"private_key_paths_in_report": False' in python_source
    assert "Do not generate a replacement key" in python_source
    assert "n'envoyez jamais les clés, seeds ou passphrases" in python_source

    assert "TUF_SNAPSHOT_ED25519_SEED_B64.txt" in powershell_source
    assert "TUF_TIMESTAMP_ED25519_SEED_B64.txt" in powershell_source
    assert "Remove-Item Env:TUF_SNAPSHOT_ED25519_SEED_B64" in powershell_source
    assert "Remove-Item Env:TUF_TIMESTAMP_ED25519_SEED_B64" in powershell_source
    assert "Les clés/seeds privés ne seront jamais affichés" in powershell_source


def test_windows_launcher_parses_when_pwsh_is_available() -> None:
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        return
    command = (
        "$tokens=$null; $errors=$null; "
        "[System.Management.Automation.Language.Parser]::ParseFile("
        f"'{POWERSHELL_LAUNCHER.as_posix()}', [ref]$tokens, [ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }"
    )
    completed = subprocess.run(
        [pwsh, "-NoProfile", "-Command", command],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
