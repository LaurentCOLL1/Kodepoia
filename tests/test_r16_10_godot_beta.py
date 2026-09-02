from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.kodegodot.beta_acceptance import build_report

ROOT = Path(__file__).resolve().parents[1]


def test_safechange_restore_is_integrity_verified_and_bounded(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    first = project / "first.txt"
    nested = project / "nested" / "second.txt"
    nested.parent.mkdir()
    first.write_text("before-first", encoding="utf-8")
    nested.write_text("before-second", encoding="utf-8")

    manager = SafeChangeManager(project, project / ".kodepoia" / "snapshots")
    snapshot = manager.snapshot([first, nested])
    first.write_text("changed-first", encoding="utf-8")
    nested.write_text("changed-second", encoding="utf-8")

    restored = manager.restore(snapshot)
    assert {path.relative_to(project).as_posix() for path in restored} == {
        "first.txt",
        "nested/second.txt",
    }
    assert first.read_text(encoding="utf-8") == "before-first"
    assert nested.read_text(encoding="utf-8") == "before-second"


def test_safechange_restore_rejects_tampered_snapshot_before_write(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    first = project / "first.txt"
    second = project / "second.txt"
    first.write_text("before-first", encoding="utf-8")
    second.write_text("before-second", encoding="utf-8")

    manager = SafeChangeManager(project, project / ".kodepoia" / "snapshots")
    snapshot = manager.snapshot([first, second])
    first.write_text("changed-first", encoding="utf-8")
    second.write_text("changed-second", encoding="utf-8")
    (snapshot / "second.txt").write_text("tampered", encoding="utf-8")

    with pytest.raises(ValueError, match="integrity verification failed"):
        manager.restore(snapshot)

    assert first.read_text(encoding="utf-8") == "changed-first"
    assert second.read_text(encoding="utf-8") == "changed-second"


def test_r16_10_static_acceptance_passes_without_inventing_live_godot() -> None:
    report = build_report(
        ROOT,
        source_sha="1" * 40,
        platform="pytest",
        godot_executable="",
    )

    assert report["security_claim"] is True
    assert report["critical_veto"] is False
    assert report["manual_state"] == "NONE"
    assert report["live_godot"]["available"] is False
    assert report["live_godot"]["status"] == "capability_absent"
    assert report["pre_change_project_sha256"] == report["restored_project_sha256"]
    assert report["pre_change_project_sha256"] != report["changed_project_sha256"]
    assert report["fixture_sha256"] == "e87b912f36b960e724b4d2eb6367794c6933ae0255353b5cbcbb400294c66b95"
    assert report["changed_project_sha256"] == (
        "0312025cdbfef593ba21a4280d9d897c4ef8aa37ec8201ceeec9c9b9b96f054e"
    )
    assert report["diff_sha256"] == "4226629a0be5da2ba2dfb3f344d56b973d9893462ef8cba64c7bc8b37a450542"
    assert report["diagnostic_sha256"] == "f61d0af7376d7deda7ad2ac65b5debdf47154f432403d41c150d351a59fc6b07"
    assert report["recovery_sha256"] == "6f107c6ff1c683ad31597e400512fb247ed56b6e4d035c1a9f0e4dce5ab5a7d5"
    assert report["semantic_sha256"] == "25b95aa0ae5ccd909a1b93e9e0d3540482a2f6c6c01491c6fd7845fd80bbe095"
    assert len(report["recovery_checkpoint_integrity_sha256"]) == 64
    assert len(report["evidence_sha256"]) == 64
    assert report["summary"]["failed"] == 0
