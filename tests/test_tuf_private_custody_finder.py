from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CMD_LAUNCHER = REPOSITORY_ROOT / "scripts" / "Run-TufReleaseCeremony.cmd"
FINDER = REPOSITORY_ROOT / "scripts" / "Find-TufPrivateCustody.ps1"


def _powershell() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell.exe")


def test_cmd_exposes_custody_discovery_subcommand() -> None:
    source = CMD_LAUNCHER.read_text(encoding="utf-8")
    assert '"--find-custody"' in source
    assert '"--search-custody"' in source
    assert "Find-TufPrivateCustody.ps1" in source


def test_cmd_hardens_script_resolution_and_distinguishes_tooling_failure() -> None:
    source = CMD_LAUNCHER.read_text(encoding="utf-8")
    assert 'set "CALLER_CWD=%CD%"' in source
    assert 'set "SCRIPT_DIR=%~dp0"' in source
    assert '%REPO_ROOT%\\scripts\\Find-TufPrivateCustody.ps1' in source
    assert '%CALLER_CWD%\\scripts\\Find-TufPrivateCustody.ps1' in source
    assert "le helper de recherche TUF est introuvable" in source
    assert "Cette erreur concerne l'outillage local" in source
    assert "exit /b 2" in source


def test_cmd_does_not_forward_discovery_verb_via_percent_star() -> None:
    source = CMD_LAUNCHER.read_text(encoding="utf-8")
    assert '-File "%FINDER%" %2 %3 %4 %5 %6 %7 %8 %9' in source
    assert '-File "%FINDER%" %*' not in source
    assert "SHIFT does not" in source


def test_cmd_discovery_invocation_does_not_repass_find_verb_on_windows(
    tmp_path: Path,
) -> None:
    if os.name != "nt" or shutil.which("cmd.exe") is None:
        return

    completed = subprocess.run(
        [
            "cmd.exe",
            "/d",
            "/c",
            str(CMD_LAUNCHER),
            "--find-custody",
            "-SearchRoot",
            str(tmp_path),
        ],
        cwd=REPOSITORY_ROOT,
        input="\n",
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=60,
    )
    combined = completed.stdout + completed.stderr
    assert "NamedParameterNotFound" not in combined
    assert "TUF_SNAPSHOT_ED25519_SEED_B64.txt" in combined
    assert "TUF_TIMESTAMP_ED25519_SEED_B64.txt" in combined


def test_finder_uses_filesystem_drives_and_never_reads_secret_contents() -> None:
    source = FINDER.read_text(encoding="utf-8")
    assert "Get-PSDrive -PSProvider FileSystem" in source
    assert "TUF_SNAPSHOT_ED25519_SEED_B64.txt" in source
    assert "TUF_TIMESTAMP_ED25519_SEED_B64.txt" in source
    assert '-Filter "*.pem"' in source
    assert "Get-Content" not in source
    assert "Racine privée TUF trouvée" in source
    assert "Test-PathInside" in source


def test_finder_locates_complete_custody_tree(tmp_path: Path) -> None:
    pwsh = _powershell()
    if pwsh is None:
        return

    custody = tmp_path / "private" / "kodepoia-tuf-production"
    custody.mkdir(parents=True)
    (custody / "TUF_SNAPSHOT_ED25519_SEED_B64.txt").write_text(
        "DO-NOT-PRINT-SNAPSHOT-SECRET", encoding="utf-8"
    )
    (custody / "TUF_TIMESTAMP_ED25519_SEED_B64.txt").write_text(
        "DO-NOT-PRINT-TIMESTAMP-SECRET", encoding="utf-8"
    )
    (custody / "targets-authority.pem").write_text(
        "DO-NOT-PRINT-PEM", encoding="utf-8"
    )

    completed = subprocess.run(
        [
            pwsh,
            "-NoProfile",
            "-File",
            str(FINDER),
            "-SearchRoot",
            str(tmp_path),
            "-RepositoryRoot",
            str(REPOSITORY_ROOT),
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
    )
    combined = completed.stdout + completed.stderr
    assert completed.returncode == 0, combined
    assert str(custody) in combined
    assert "TUF" in combined
    assert "Run-TufReleaseCeremony.cmd" in combined
    assert "DO-NOT-PRINT-SNAPSHOT-SECRET" not in combined
    assert "DO-NOT-PRINT-TIMESTAMP-SECRET" not in combined
    assert "DO-NOT-PRINT-PEM" not in combined


def test_finder_rejects_incomplete_tree(tmp_path: Path) -> None:
    pwsh = _powershell()
    if pwsh is None:
        return

    incomplete = tmp_path / "incomplete"
    incomplete.mkdir()
    (incomplete / "TUF_SNAPSHOT_ED25519_SEED_B64.txt").write_text(
        "secret", encoding="utf-8"
    )

    completed = subprocess.run(
        [
            pwsh,
            "-NoProfile",
            "-File",
            str(FINDER),
            "-SearchRoot",
            str(tmp_path),
            "-RepositoryRoot",
            str(REPOSITORY_ROOT),
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
    )
    combined = completed.stdout + completed.stderr
    assert completed.returncode != 0
    assert "TUF_SNAPSHOT_ED25519_SEED_B64.txt" in combined
    assert "TUF_TIMESTAMP_ED25519_SEED_B64.txt" in combined
    assert ".pem" in combined
