from __future__ import annotations

import os
import sys
from pathlib import Path

from kodepoia.kodegodot.process_diagnostic import _sanitized_env, run_diagnostic


def _write_fixture(repo_root: Path) -> None:
    project = repo_root / ".kodepoia" / "r5-acceptance" / "project"
    project.mkdir(parents=True)
    (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")


def test_sanitized_environment_keeps_no_arbitrary_secret(monkeypatch) -> None:
    monkeypatch.setenv("APPDATA", "C:/Users/Test/AppData/Roaming")
    monkeypatch.setenv("KODEPOIA_DIAGNOSTIC_SECRET", "do-not-copy")
    env = _sanitized_env()
    assert env["APPDATA"] == "C:/Users/Test/AppData/Roaming"
    assert "KODEPOIA_DIAGNOSTIC_SECRET" not in env


def test_process_diagnostic_is_bounded_and_writes_no_environment_values(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    output = tmp_path / ".kodepoia" / "benchmarks" / "diagnostic.json"
    payload = run_diagnostic(tmp_path, sys.executable, output=output, timeout=3.0)

    assert payload["metadata"]["phase"] == "R5-godot-process-diagnostic"
    assert payload["metadata"]["environment_keys_recorded"] is False
    assert payload["metadata"]["environment_values_recorded"] is False
    assert payload["summary"]["total"] == 6
    assert payload["summary"]["failed"] == 0
    assert output.is_file()

    names = {case["name"] for case in payload["cases"]}
    assert names == {
        "inherited_repo_pipe",
        "inherited_project_pipe",
        "sanitized_empty_pipe",
        "sanitized_project_pipe",
        "sanitized_project_file",
        "process_sandbox_project",
    }
    assert all("Python" in (case["stdout"] + case["stderr"]) for case in payload["cases"])


def test_process_diagnostic_rejects_missing_fixture(tmp_path: Path) -> None:
    try:
        run_diagnostic(tmp_path, sys.executable, timeout=2.0)
    except FileNotFoundError as exc:
        assert "acceptance fixture" in str(exc)
    else:
        raise AssertionError("missing fixture should be rejected")
