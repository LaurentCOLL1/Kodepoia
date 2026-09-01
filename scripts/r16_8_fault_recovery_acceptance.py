from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from kodepoia.core.backup import BackupManager
from kodepoia.core.fault_injection import (
    FAULT_STAGES,
    DeterministicFaultInjector,
    FaultRule,
    InjectedFault,
)
from kodepoia.core.kill_switch import KillSwitch
from kodepoia.core.recovery import RecoveryJournal
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.core.sandbox import ProcessSandbox


def _case(
    name: str,
    passed: bool,
    *,
    state: str,
    recovery_outcome: str,
    detail: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "pass": bool(passed),
        "state": state,
        "recovery_outcome": recovery_outcome,
        "detail": detail,
    }


def _python_sandbox(root: Path, switch: KillSwitch) -> ProcessSandbox:
    return ProcessSandbox(
        root,
        allowed_executables={Path(sys.executable).name},
        kill_switch=switch,
    )


def _fault_point_case() -> dict[str, Any]:
    observed: list[str] = []
    for stage in FAULT_STAGES:
        injector = DeterministicFaultInjector(
            [FaultRule("matrix", stage, reason=f"{stage} fault")]
        )
        try:
            injector.hit("matrix", stage)
        except InjectedFault:
            observed.append(stage)
    return _case(
        "deterministic_fault_point_matrix",
        tuple(observed) == FAULT_STAGES,
        state="stopped",
        recovery_outcome="blocked_state",
        detail="prepare/write/commit/verify/cleanup faults are explicit and deterministic",
    )


def build_report(source_sha: str) -> dict[str, Any]:
    cases: list[dict[str, Any]] = [_fault_point_case()]
    repository_root = Path(__file__).resolve().parents[1]
    fixture_root = repository_root / "tests" / "fixtures" / "r16_8"

    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-8-") as tmp:
        root = Path(tmp)

        pre_switch = KillSwitch()
        pre_switch.trigger()
        pre_blocked = False
        try:
            _python_sandbox(root, pre_switch).run(
                [sys.executable, "-c", "print('must-not-run')"],
                timeout=5.0,
            )
        except RuntimeError:
            pre_blocked = True
        cases.append(
            _case(
                "killswitch_before_launch",
                pre_blocked and pre_switch.active_count == 0,
                state="stopped",
                recovery_outcome="blocked_state",
                detail="active KillSwitch rejects process creation before launch",
            )
        )

        crash_switch = KillSwitch()
        crash = _python_sandbox(root, crash_switch).run(
            [sys.executable, "-c", "raise SystemExit(7)"],
            timeout=5.0,
        )
        cases.append(
            _case(
                "subprocess_crash_detected",
                crash.returncode == 7 and not crash.timed_out and crash_switch.active_count == 0,
                state="failed",
                recovery_outcome="blocked_state",
                detail="non-zero subprocess exit is explicit and no process registration leaks",
            )
        )

        timeout_switch = KillSwitch()
        timeout = _python_sandbox(root, timeout_switch).run(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            timeout=0.1,
        )
        cases.append(
            _case(
                "subprocess_hang_bounded",
                timeout.timed_out and timeout.returncode != 0 and timeout_switch.active_count == 0,
                state="stopped",
                recovery_outcome="blocked_state",
                detail="hung subprocess is terminated after a bounded timeout",
            )
        )

        live_switch = KillSwitch()
        managed = _python_sandbox(root, live_switch).spawn_piped(
            [sys.executable, "-c", "import time; time.sleep(10)"]
        )
        try:
            active_before = live_switch.active_count
            stopped_count = live_switch.trigger()
            managed.process.wait(timeout=5.0)
            live_stopped = (
                active_before == 1
                and stopped_count == 1
                and managed.returncode is not None
            )
        finally:
            managed.close()
        cases.append(
            _case(
                "killswitch_during_process",
                live_stopped and live_switch.active_count == 0,
                state="cancelled",
                recovery_outcome="blocked_state",
                detail="KillSwitch terminates registered work and cleanup unregisters it",
            )
        )

        checkpoint_path = root / "recovery" / "checkpoint.json"
        stable_journal = RecoveryJournal(checkpoint_path)
        stable_journal.save("task", "stable", {"step": 1})
        stable_bytes = checkpoint_path.read_bytes()
        interrupted = RecoveryJournal(
            checkpoint_path,
            DeterministicFaultInjector(
                [FaultRule("recovery.save", "commit", reason="interrupted commit")]
            ),
        )
        interrupted_seen = False
        try:
            interrupted.save("task", "new", {"step": 2})
        except InjectedFault:
            interrupted_seen = True
        recovered = stable_journal.load()
        cases.append(
            _case(
                "checkpoint_interrupted_commit_preserves_rpo",
                interrupted_seen
                and checkpoint_path.read_bytes() == stable_bytes
                and recovered is not None
                and recovered.phase == "stable",
                state="stopped",
                recovery_outcome="validated_recovery",
                detail="failed commit preserves the last validated checkpoint",
            )
        )

        shutil.copy2(fixture_root / "checkpoint-corrupt.json", checkpoint_path)
        corrupt_checkpoint_rejected = False
        try:
            stable_journal.load()
        except ValueError:
            corrupt_checkpoint_rejected = True
        cases.append(
            _case(
                "corrupted_checkpoint_rejected",
                corrupt_checkpoint_rejected,
                state="stopped",
                recovery_outcome="blocked_state",
                detail="integrity-invalid checkpoint cannot become recovery authority",
            )
        )

        source = root / "source"
        source.mkdir()
        (source / "a.txt").write_text("known-a", encoding="utf-8")
        (source / "b.txt").write_text("known-b", encoding="utf-8")
        backup_root = root / "backups"
        base_backup = BackupManager(backup_root)
        archive = base_backup.create_archive(source, label="r16-8")

        bad_archive = root / "fixture-corrupt.zip"
        fixture_manifest = (fixture_root / "backup-corrupt-manifest.json").read_text(
            encoding="utf-8"
        )
        with zipfile.ZipFile(bad_archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("data.txt", b"known")
            zf.writestr(BackupManager.MANIFEST_NAME, fixture_manifest)
        bad_destination = root / "bad-restore"
        bad_destination.mkdir()
        (bad_destination / "trusted.txt").write_text("trusted", encoding="utf-8")
        bad_rejected = False
        try:
            base_backup.restore(bad_archive, bad_destination, overwrite=True)
        except ValueError:
            bad_rejected = True
        cases.append(
            _case(
                "corrupted_backup_rejected_before_mutation",
                bad_rejected
                and (bad_destination / "trusted.txt").read_text(encoding="utf-8") == "trusted",
                state="stopped",
                recovery_outcome="blocked_state",
                detail="corrupt archive is rejected before trusted destination mutation",
            )
        )

        rollback_destination = root / "rollback-restore"
        rollback_destination.mkdir()
        (rollback_destination / "trusted.txt").write_text("trusted", encoding="utf-8")
        commit_fault = BackupManager(
            backup_root,
            DeterministicFaultInjector(
                [
                    FaultRule(
                        "backup.restore",
                        "commit",
                        occurrence=2,
                        reason="commit interruption",
                    )
                ]
            ),
        )
        rollback_seen = False
        try:
            commit_fault.restore(archive, rollback_destination, overwrite=True)
        except InjectedFault:
            rollback_seen = True
        cases.append(
            _case(
                "backup_commit_fault_rolls_back",
                rollback_seen
                and sorted(item.name for item in rollback_destination.iterdir())
                == ["trusted.txt"]
                and (rollback_destination / "trusted.txt").read_text(encoding="utf-8")
                == "trusted",
                state="stopped",
                recovery_outcome="clean_rollback",
                detail="failure after moving prior state restores the pre-restore destination",
            )
        )

        denial_destination = root / "denial-restore"
        denial_destination.mkdir()
        (denial_destination / "trusted.txt").write_text("trusted", encoding="utf-8")
        denial_manager = BackupManager(
            backup_root,
            DeterministicFaultInjector(
                [FaultRule("backup.restore", "write", reason="synthetic resource denial")]
            ),
        )
        denial_seen = False
        try:
            denial_manager.restore(archive, denial_destination, overwrite=True)
        except InjectedFault:
            denial_seen = True
        cases.append(
            _case(
                "bounded_resource_denial_simulation",
                denial_seen
                and (denial_destination / "trusted.txt").read_text(encoding="utf-8")
                == "trusted",
                state="stopped",
                recovery_outcome="clean_rollback",
                detail="synthetic write denial consumes no real resource and leaves authority unchanged",
            )
        )

        known_destination = base_backup.restore(archive, root / "known-restore")
        known_good = (
            (known_destination / "a.txt").read_text(encoding="utf-8") == "known-a"
            and (known_destination / "b.txt").read_text(encoding="utf-8") == "known-b"
            and base_backup.verify(archive)
        )
        cases.append(
            _case(
                "known_good_backup_restore_and_reverify",
                known_good,
                state="completed",
                recovery_outcome="validated_recovery",
                detail="known-good archive restores and all file digests revalidate",
            )
        )

        project = root / "safe-project"
        project.mkdir()
        first = project / "first.txt"
        second = project / "second.txt"
        trust = project / "tool-trust.json"
        first.write_text("known-a", encoding="utf-8")
        second.write_text("known-b", encoding="utf-8")
        trust.write_text("deny", encoding="utf-8")
        snapshots = root / "safe-snapshots"
        safe = SafeChangeManager(project, snapshots)
        snapshot = safe.snapshot([first, second])
        first.write_text("current-a", encoding="utf-8")
        second.write_text("current-b", encoding="utf-8")
        trust.write_text("updated-policy", encoding="utf-8")

        failing_safe = SafeChangeManager(
            project,
            snapshots,
            DeterministicFaultInjector(
                [
                    FaultRule(
                        "safe_change.restore",
                        "write",
                        occurrence=2,
                        reason="multi-step interruption",
                    )
                ]
            ),
        )
        safe_fault_seen = False
        try:
            failing_safe.restore_snapshot(snapshot)
        except InjectedFault:
            safe_fault_seen = True
        rollback_ok = (
            first.read_text(encoding="utf-8") == "current-a"
            and second.read_text(encoding="utf-8") == "current-b"
            and trust.read_text(encoding="utf-8") == "updated-policy"
        )
        cases.append(
            _case(
                "safechange_multistep_fault_rolls_back",
                safe_fault_seen and rollback_ok,
                state="stopped",
                recovery_outcome="clean_rollback",
                detail="partial snapshot restoration rolls back to the exact pre-attempt state",
            )
        )

        safe.restore_snapshot(snapshot)
        safe_restore_ok = (
            first.read_text(encoding="utf-8") == "known-a"
            and second.read_text(encoding="utf-8") == "known-b"
        )
        cases.append(
            _case(
                "safechange_known_good_restore",
                safe_restore_ok,
                state="completed",
                recovery_outcome="validated_recovery",
                detail="validated snapshot restores its declared authority",
            )
        )
        cases.append(
            _case(
                "snapshot_contract_does_not_restore_tool_trust",
                trust.read_text(encoding="utf-8") == "updated-policy",
                state="completed",
                recovery_outcome="validated_recovery",
                detail="unsnapshotted policy/tool-trust state is outside the restore contract",
            )
        )

        absent = project / "created-during-failure.txt"
        absent_snapshot = safe.snapshot([absent])
        absent.write_text("partial", encoding="utf-8")
        safe.restore_snapshot(absent_snapshot)
        cases.append(
            _case(
                "safechange_removes_partial_new_path",
                not absent.exists(),
                state="completed",
                recovery_outcome="clean_rollback",
                detail="snapshot records missing paths so later partial creations are removed",
            )
        )

    semantic = {
        "schema": "kodepoia.r16.8.fault-recovery-acceptance.v1",
        "cases": cases,
        "critical_veto": any(not item["pass"] for item in cases),
        "manual": "NONE",
        "synthetic_only": True,
        "network_calls": False,
        "live_secrets": False,
        "production_disaster_recovery_guarantee": False,
        "repository_local_rpo": "last validated checkpoint or backup before the injected fault",
        "fault_stages": list(FAULT_STAGES),
        "allowed_terminal_states": ["completed", "stopped", "failed", "cancelled"],
    }
    semantic_bytes = json.dumps(
        semantic,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        **semantic,
        "source_sha": source_sha.lower(),
        "semantic_sha256": hashlib.sha256(semantic_bytes).hexdigest(),
        "summary": {
            "passed": sum(item["pass"] for item in cases),
            "total": len(cases),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source_sha = args.source_sha.strip().lower()
    if len(source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise SystemExit("--source-sha must be a lowercase 40-character Git SHA")
    report = build_report(source_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["critical_veto"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
