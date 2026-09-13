from __future__ import annotations

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
    )
    combined = completed.stdout + completed.stderr
    assert completed.returncode == 0, combined
    assert str(custody) in combined
    assert "Racine privée TUF trouvée" in combined
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
    )
    assert completed.returncode != 0
    assert "Aucune racine privée TUF complète" in (completed.stdout + completed.stderr)
