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
    assert len(report["diff_sha256"]) == 64
    assert len(report["diagnostic_sha256"]) == 64
    assert len(report["recovery_sha256"]) == 64
    assert len(report["semantic_sha256"]) == 64
    assert len(report["evidence_sha256"]) == 64
    assert report["summary"]["failed"] == 0
