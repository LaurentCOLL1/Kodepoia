from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

import pytest

from kodepoia.core.backup import BackupManager
from kodepoia.core.fault_injection import (
    DeterministicFaultInjector,
    FaultRule,
    InjectedFault,
)
from kodepoia.core.kill_switch import KillSwitch
from kodepoia.core.recovery import RecoveryJournal
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.core.sandbox import ProcessSandbox


def test_fault_injector_exact_occurrence() -> None:
    injector = DeterministicFaultInjector(
        [FaultRule("component", "write", occurrence=2, reason="disk denied")]
    )
    injector.hit("component", "write")
    with pytest.raises(InjectedFault, match="disk denied"):
        injector.hit("component", "write")
    assert [event.injected for event in injector.events] == [False, True]


def test_recovery_journal_rejects_semantic_tamper(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    journal = RecoveryJournal(path)
    journal.save("task", "write", {"step": 1})
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["checkpoint"]["state"]["step"] = 999
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        journal.load()


def test_recovery_interrupted_commit_preserves_previous(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    journal = RecoveryJournal(path)
    journal.save("task", "stable", {"step": 1})
    previous = path.read_bytes()
    injector = DeterministicFaultInjector(
        [FaultRule("recovery.save", "commit", reason="power loss")]
    )
    failing = RecoveryJournal(path, fault_injector=injector)
    with pytest.raises(InjectedFault, match="power loss"):
        failing.save("task", "new", {"step": 2})
    assert path.read_bytes() == previous
    assert journal.load().phase == "stable"


def test_safechange_restore_rolls_back_injected_partial_restore(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    first = project / "first.txt"
    second = project / "second.txt"
    first.write_text("known-a", encoding="utf-8")
    second.write_text("known-b", encoding="utf-8")

    manager = SafeChangeManager(project, tmp_path / "snapshots")
    snapshot = manager.snapshot([first, second])
    first.write_text("current-a", encoding="utf-8")
    second.write_text("current-b", encoding="utf-8")

    injector = DeterministicFaultInjector(
        [FaultRule("safe_change.restore", "write", occurrence=2, reason="interrupted write")]
    )
    failing = SafeChangeManager(project, tmp_path / "snapshots", injector)
    with pytest.raises(InjectedFault, match="interrupted write"):
        failing.restore_snapshot(snapshot)

    assert first.read_text(encoding="utf-8") == "current-a"
    assert second.read_text(encoding="utf-8") == "current-b"

    manager.restore_snapshot(snapshot)
    assert first.read_text(encoding="utf-8") == "known-a"
    assert second.read_text(encoding="utf-8") == "known-b"


def test_safechange_snapshot_contract_preserves_unsnapshotted_state(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    data = project / "data.txt"
    trust = project / "tool-trust.json"
    data.write_text("known", encoding="utf-8")
    trust.write_text("deny", encoding="utf-8")
    manager = SafeChangeManager(project, tmp_path / "snapshots")
    snapshot = manager.snapshot([data])

    data.write_text("broken", encoding="utf-8")
    trust.write_text("updated-policy", encoding="utf-8")
    manager.restore_snapshot(snapshot)

    assert data.read_text(encoding="utf-8") == "known"
    assert trust.read_text(encoding="utf-8") == "updated-policy"


def test_safechange_restores_path_that_was_missing_at_snapshot(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    future = project / "future.txt"
    manager = SafeChangeManager(project, tmp_path / "snapshots")
    snapshot = manager.snapshot([future])
    future.write_text("partial", encoding="utf-8")
    manager.restore_snapshot(snapshot)
    assert not future.exists()


def test_backup_restore_failure_preserves_existing_destination(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.txt").write_text("known-a", encoding="utf-8")
    (source / "b.txt").write_text("known-b", encoding="utf-8")
    backup_root = tmp_path / "backups"
    archive = BackupManager(backup_root).create_archive(source)

    destination = tmp_path / "restore"
    destination.mkdir()
    (destination / "existing.txt").write_text("trusted", encoding="utf-8")
    injector = DeterministicFaultInjector(
        [FaultRule("backup.restore", "commit", occurrence=2, reason="commit interrupted")]
    )
    manager = BackupManager(backup_root, injector)
    with pytest.raises(InjectedFault, match="commit interrupted"):
        manager.restore(archive, destination, overwrite=True)

    assert sorted(path.name for path in destination.iterdir()) == ["existing.txt"]
    assert (destination / "existing.txt").read_text(encoding="utf-8") == "trusted"


def test_backup_corruption_is_rejected_before_destination_mutation(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "data.txt").write_text("known", encoding="utf-8")
    manager = BackupManager(tmp_path / "backups")
    archive = manager.create_archive(source)

    corrupted = tmp_path / "corrupted.zip"
    with zipfile.ZipFile(archive, "r") as original, zipfile.ZipFile(corrupted, "w") as output:
        for name in original.namelist():
            payload = original.read(name)
            if name == "data.txt":
                payload = b"tampered"
            output.writestr(name, payload)

    destination = tmp_path / "restore"
    destination.mkdir()
    (destination / "existing.txt").write_text("trusted", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid or corrupted"):
        manager.restore(corrupted, destination, overwrite=True)
    assert (destination / "existing.txt").read_text(encoding="utf-8") == "trusted"


def test_backup_known_good_restore_revalidates_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "data.txt").write_text("known", encoding="utf-8")
    manager = BackupManager(tmp_path / "backups")
    archive = manager.create_archive(source)
    destination = manager.restore(archive, tmp_path / "restore")
    assert (destination / "data.txt").read_text(encoding="utf-8") == "known"
    assert manager.verify(archive)


def test_static_corrupt_checkpoint_fixture_is_rejected(tmp_path: Path) -> None:
    fixture = Path(__file__).parent / "fixtures" / "r16_8" / "checkpoint-corrupt.json"
    path = tmp_path / "checkpoint.json"
    shutil.copy2(fixture, path)
    with pytest.raises(ValueError, match="integrity"):
        RecoveryJournal(path).load()


def _python_sandbox(tmp_path: Path, switch: KillSwitch) -> ProcessSandbox:
    return ProcessSandbox(
        tmp_path,
        allowed_executables={Path(sys.executable).name},
        kill_switch=switch,
    )


def test_kill_switch_blocks_launch_before_process_creation(tmp_path: Path) -> None:
    switch = KillSwitch()
    switch.trigger()
    sandbox = _python_sandbox(tmp_path, switch)
    with pytest.raises(RuntimeError, match="kill switch"):
        sandbox.run([sys.executable, "-c", "print('never')"])


def test_sandbox_reports_subprocess_crash(tmp_path: Path) -> None:
    switch = KillSwitch()
    result = _python_sandbox(tmp_path, switch).run(
        [sys.executable, "-c", "raise SystemExit(7)"],
        timeout=5.0,
    )
    assert result.returncode == 7
    assert not result.timed_out
    assert not result.cancelled
    assert switch.active_count == 0


def test_sandbox_timeout_is_bounded_and_unregisters(tmp_path: Path) -> None:
    switch = KillSwitch()
    result = _python_sandbox(tmp_path, switch).run(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        timeout=0.1,
    )
    assert result.timed_out
    assert result.returncode != 0
    assert switch.active_count == 0


def test_kill_switch_stops_registered_process(tmp_path: Path) -> None:
    switch = KillSwitch()
    sandbox = _python_sandbox(tmp_path, switch)
    managed = sandbox.spawn_piped(
        [sys.executable, "-c", "import time; time.sleep(10)"]
    )
    try:
        assert switch.active_count == 1
        assert switch.trigger() == 1
        managed.process.wait(timeout=5.0)
        assert managed.returncode is not None
    finally:
        managed.close()
    assert switch.active_count == 0
