from __future__ import annotations

import sys
from pathlib import Path

from kodepoia.kodestudio import app_v11_entry


def test_smoke_report_argument_is_opt_in(monkeypatch, tmp_path: Path) -> None:
    report = tmp_path / "smoke.txt"
    monkeypatch.setattr(sys, "argv", ["KodepoiaStudio.exe", "--smoke-test"])
    assert app_v11_entry._smoke_report_path() is None
    monkeypatch.setattr(
        sys,
        "argv",
        ["KodepoiaStudio.exe", "--smoke-test", f"--smoke-report={report}"],
    )
    assert app_v11_entry._smoke_report_path() == report


def test_windows_build_and_ci_use_diagnostic_entrypoint() -> None:
    root = Path(__file__).resolve().parents[1]
    build = (root / "scripts" / "build_windows_installer.ps1").read_text(encoding="utf-8")
    workflow = (root / ".github" / "workflows" / "windows-installer.yml").read_text(
        encoding="utf-8"
    )
    assert "app_v11_entry.py" in build
    assert "--windows-console-mode=disable" in build
    assert "--smoke-report=$smokeReport" in workflow
    assert "Kodepoia-smoke-cwd" in workflow
    assert "Developer Python is still visible during packaged smoke" in workflow
    assert "still exists after successful uninstaller exit" in workflow


def test_windows_package_embeds_trusted_update_resources() -> None:
    root = Path(__file__).resolve().parents[1]
    build = (root / "scripts" / "build_windows_installer.ps1").read_text(encoding="utf-8")
    workflow = (root / ".github" / "workflows" / "windows-installer.yml").read_text(
        encoding="utf-8"
    )
    required = (
        "trusted_root.production.json",
        "trusted_root.production.manifest.json",
        "trusted_root.synthetic.json",
        "trusted_root.synthetic.manifest.json",
    )

    assert "--include-package-data=kodepoia.update" in build
    for filename in required:
        assert filename in build
        assert filename in workflow


def test_windows_installer_always_offers_destination_selection() -> None:
    root = Path(__file__).resolve().parents[1]
    installer = (root / "packaging" / "windows" / "Kodepoia.iss").read_text(encoding="utf-8")
    workflow = (root / ".github" / "workflows" / "windows-installer.yml").read_text(
        encoding="utf-8"
    )

    assert "DisableDirPage=no" in installer
    assert "UsePreviousAppDir=yes" in installer
    assert "AlwaysShowDirOnReadyPage=yes" in installer
    assert "/DIR=$installDir" in workflow
    assert "Kodepoia-installed-custom-name" in workflow
