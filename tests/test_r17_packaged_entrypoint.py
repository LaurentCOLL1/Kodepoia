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
