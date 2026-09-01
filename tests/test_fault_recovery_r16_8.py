from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from kodepoia.core.backup import BackupManager
from kodepoia.core.fault_recovery import (
    FaultInjector,
    FaultMode,
    FaultSpec,
    FaultStage,
    FileRecoveryDrill,
    InjectedFault,
    RecoveryBlockedError,
    RecoveryRequiredError,
)
from kodepoia.core.kill_switch import KillSwitch
from kodepoia.core.recovery import RecoveryJournal
from kodepoia.core.sandbox import ProcessSandbox


def _drill(
    tmp_path: Path,
    *,
    injector: FaultInjector | None = None,
    kill_switch: KillSwitch | None = None,
) -> tuple[Path, RecoveryJournal, FileRecoveryDrill]:
    root = tmp_path / "project"
    root.mkdir()
    journal = RecoveryJournal(tmp_path / "state" / "recovery.json")
    drill = FileRecoveryDrill(
        root,
        tmp_path / "snapshots",
        journal,
        injector=injector,
        kill_switch=kill_switch or KillSwitch(),
    )
    return root, journal, drill


def test_fault_injector_is_deterministic_and_one_shot() -> None:
    spec = FaultSpec(FaultStage.WRITE, case_id="write-once")
    injector = FaultInjector((spec,))
    injector.hit(FaultStage.PREPARE)
    with pytest.raises(InjectedFault):
        injector.hit(FaultStage.WRITE)
    injector.hit(FaultStage.WRITE)
    assert injector.fired_case_ids == ("write-once",)


@pytest.mark.parametrize("stage", list(FaultStage))
def test_every_fault_stage_requires_and_validates_recovery(
    tmp_path: Path,
    stage: FaultStage,
) -> None:
    injector = FaultInjector((FaultSpec(stage, case_id=f"fault-{stage.value}"),))
    root, journal, drill = _drill(tmp_path, injector=injector)
    target = root / "state.txt"
    target.write_text("before", encoding="utf-8")

    with pytest.raises(RecoveryRequiredError):
        drill.mutate_file("task-1", "state.txt", b"after")

    assert journal.path.exists()
    recovered = drill.recover("task-1")
    assert recovered.status == "recovered"
    assert recovered.recovery_point == "last-verified-pre-mutation-snapshot"
    assert target.read_text(encoding="utf-8") == "before"
    assert not journal.path.exists()


def test_resource_denial_simulation_fails_to_verified_recovery(tmp_path: Path) -> None:
    injector = FaultInjector(
        (FaultSpec(FaultStage.WRITE, FaultMode.RESOURCE_DENIED, "synthetic-enospc"),)
    )
    root, _, drill = _drill(tmp_path, injector=injector)
    target = root / "state.txt"
    target.write_text("before", encoding="utf-8")

    with pytest.raises(RecoveryRequiredError) as error:
        drill.mutate_file("task-resource", "state.txt", b"after")

    assert isinstance(error.value.__cause__, OSError)
    drill.recover("task-resource")
    assert target.read_text(encoding="utf-8") == "before"


def test_checkpoint_integrity_tamper_blocks_recovery(tmp_path: Path) -> None:
    injector = FaultInjector((FaultSpec(FaultStage.COMMIT, case_id="after-commit"),))
    root, journal, drill = _drill(tmp_path, injector=injector)
    target = root / "state.txt"
    target.write_text("before", encoding="utf-8")

    with pytest.raises(RecoveryRequiredError):
        drill.mutate_file("task-corrupt", "state.txt", b"after")

    raw = json.loads(journal.path.read_text(encoding="utf-8"))
    raw["phase"] = "complete"
    journal.path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(RecoveryBlockedError):
        drill.recover("task-corrupt")
    assert journal.path.exists()


def test_corrupted_snapshot_blocks_recovery_without_silent_acceptance(tmp_path: Path) -> None:
    injector = FaultInjector((FaultSpec(FaultStage.COMMIT, case_id="snapshot-corrupt"),))
    root, journal, drill = _drill(tmp_path, injector=injector)
    target = root / "state.txt"
    target.write_text("before", encoding="utf-8")

    with pytest.raises(RecoveryRequiredError):
        drill.mutate_file("task-snapshot", "state.txt", b"after")

    checkpoint = journal.load(require_integrity=True, expected_task_id="task-snapshot")
    assert checkpoint is not None
    snapshot = drill.snapshot_root / str(checkpoint.state["snapshot"]) / "state.txt"
    snapshot.write_text("tampered", encoding="utf-8")

    with pytest.raises(RecoveryBlockedError):
        drill.recover("task-snapshot")
    assert journal.path.exists()


def test_wrong_task_cannot_consume_pending_recovery(tmp_path: Path) -> None:
    injector = FaultInjector((FaultSpec(FaultStage.PREPARE, case_id="bind-task"),))
    root, journal, drill = _drill(tmp_path, injector=injector)
    (root / "state.txt").write_text("before", encoding="utf-8")

    with pytest.raises(RecoveryRequiredError):
        drill.mutate_file("right-task", "state.txt", b"after")
    with pytest.raises(RecoveryBlockedError):
        drill.recover("wrong-task")

    assert journal.path.exists()
    drill.recover("right-task")
    assert not journal.path.exists()


def test_recovery_is_narrow_and_does_not_restore_unrelated_authority(tmp_path: Path) -> None:
    injector = FaultInjector((FaultSpec(FaultStage.COMMIT, case_id="narrow-scope"),))
    root, _, drill = _drill(tmp_path, injector=injector)
    target = root / "state.txt"
    authority = root / "authority.json"
    target.write_text("before", encoding="utf-8")
    authority.write_text('{"permission":"old"}', encoding="utf-8")

    with pytest.raises(RecoveryRequiredError):
        drill.mutate_file("task-narrow", "state.txt", b"after")

    authority.write_text('{"permission":"current"}', encoding="utf-8")
    drill.recover("task-narrow")
    assert target.read_text(encoding="utf-8") == "before"
    assert authority.read_text(encoding="utf-8") == '{"permission":"current"}'


def test_killswitch_blocks_process_before_launch(tmp_path: Path) -> None:
    kill_switch = KillSwitch()
    kill_switch.trigger()
    sandbox = ProcessSandbox(
        tmp_path,
        allowed_executables={Path(sys.executable).name.lower()},
        kill_switch=kill_switch,
    )
    with pytest.raises(RuntimeError, match="kill switch is active"):
        sandbox.run([sys.executable, "-c", "print('never')"])


def test_killswitch_stops_registered_hanging_process(tmp_path: Path) -> None:
    kill_switch = KillSwitch()
    sandbox = ProcessSandbox(
        tmp_path,
        allowed_executables={Path(sys.executable).name.lower()},
        kill_switch=kill_switch,
    )
    process = sandbox.spawn_background(
        [sys.executable, "-c", "import time; time.sleep(30)"]
    )
    try:
        assert kill_switch.active_count == 1
        assert kill_switch.trigger() == 1
        process.process.wait(timeout=5)
    finally:
        process.close()
    assert process.returncode is not None
    assert kill_switch.active_count == 0


def test_killswitch_during_multistep_mutation_requires_recovery(tmp_path: Path) -> None:
    kill_switch = KillSwitch()

    class KillAtWrite(FaultInjector):
        def hit(self, stage: FaultStage) -> None:
            if stage is FaultStage.WRITE and not kill_switch.triggered:
                kill_switch.trigger()

    root, journal, drill = _drill(
        tmp_path,
        injector=KillAtWrite(),
        kill_switch=kill_switch,
    )
    target = root / "state.txt"
    target.write_text("before", encoding="utf-8")

    with pytest.raises(RecoveryRequiredError):
        drill.mutate_file("task-kill", "state.txt", b"after")

    assert journal.path.exists()
    kill_switch.reset()
    drill.recover("task-kill")
    assert target.read_text(encoding="utf-8") == "before"


def test_process_timeout_reports_hang_without_host_escape(tmp_path: Path) -> None:
    sandbox = ProcessSandbox(
        tmp_path,
        allowed_executables={Path(sys.executable).name.lower()},
        kill_switch=KillSwitch(),
    )
    result = sandbox.run(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        timeout=0.05,
    )
    assert result.timed_out
    assert result.returncode != 0


def test_backup_corruption_is_rejected_and_known_good_restore_verifies(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "state.txt").write_text("known-good", encoding="utf-8")
    manager = BackupManager(tmp_path / "archives")
    archive = manager.create_archive(root, "r16-8")
    assert manager.verify(archive)

    restored = tmp_path / "restored"
    manager.restore(archive, restored)
    assert (restored / "state.txt").read_text(encoding="utf-8") == "known-good"

    corrupted = tmp_path / "archives" / "corrupted.zip"
    corrupted.write_bytes(archive.read_bytes()[:-16])
    assert not manager.verify(corrupted)


def test_recovery_journal_legacy_read_is_compatible_but_not_authoritative(tmp_path: Path) -> None:
    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps(
            {
                "task_id": "legacy",
                "phase": "old",
                "state": {"value": 1},
                "updated_at": "2026-01-01T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    journal = RecoveryJournal(path)
    assert journal.load() is not None
    with pytest.raises(ValueError, match="lacks integrity"):
        journal.load(require_integrity=True)
