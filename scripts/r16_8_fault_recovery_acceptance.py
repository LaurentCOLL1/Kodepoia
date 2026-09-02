from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from kodepoia.core.backup import BackupManager
from kodepoia.core.fault_recovery import (
    FaultInjector,
    FaultMode,
    FaultSpec,
    FaultStage,
    FileRecoveryDrill,
    RecoveryBlockedError,
    RecoveryRequiredError,
)
from kodepoia.core.kill_switch import KillSwitch
from kodepoia.core.recovery import RecoveryJournal
from kodepoia.core.sandbox import ProcessSandbox


def _case(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "detail": detail}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _new_drill(
    base: Path,
    *,
    injector: FaultInjector | None = None,
    kill_switch: KillSwitch | None = None,
) -> tuple[Path, RecoveryJournal, FileRecoveryDrill]:
    root = base / "project"
    root.mkdir(parents=True)
    journal = RecoveryJournal(base / "state" / "recovery.json")
    drill = FileRecoveryDrill(
        root,
        base / "snapshots",
        journal,
        injector=injector,
        kill_switch=kill_switch or KillSwitch(),
    )
    return root, journal, drill


def _fault_stage_case(stage: FaultStage) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix=f"kodepoia-r16-8-{stage.value}-") as tmp:
        base = Path(tmp)
        injector = FaultInjector((FaultSpec(stage, case_id=f"FI-{stage.value.upper()}"),))
        root, journal, drill = _new_drill(base, injector=injector)
        target = root / "state.txt"
        target.write_text("before", encoding="utf-8")
        required = False
        try:
            drill.mutate_file(f"task-{stage.value}", "state.txt", b"after")
        except RecoveryRequiredError:
            required = True
        if not required or not journal.path.exists():
            return False, f"{stage.value} did not leave explicit recovery authority"
        result = drill.recover(f"task-{stage.value}")
        passed = (
            result.status == "recovered"
            and target.read_text(encoding="utf-8") == "before"
            and not journal.path.exists()
        )
        return passed, f"{stage.value} -> RECOVERY_REQUIRED -> verified rollback"


def _resource_denial_case() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-8-resource-") as tmp:
        base = Path(tmp)
        injector = FaultInjector(
            (FaultSpec(FaultStage.WRITE, FaultMode.RESOURCE_DENIED, "FI-ENOSPC"),)
        )
        root, _, drill = _new_drill(base, injector=injector)
        target = root / "state.txt"
        target.write_text("before", encoding="utf-8")
        cause_is_oserror = False
        try:
            drill.mutate_file("task-resource", "state.txt", b"after")
        except RecoveryRequiredError as exc:
            cause_is_oserror = isinstance(exc.__cause__, OSError)
        drill.recover("task-resource")
        return (
            cause_is_oserror and target.read_text(encoding="utf-8") == "before",
            "synthetic ENOSPC is fail-closed and recovers to verified pre-mutation state",
        )


def _checkpoint_corruption_case() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-8-checkpoint-") as tmp:
        base = Path(tmp)
        injector = FaultInjector((FaultSpec(FaultStage.COMMIT, case_id="FI-CHECKPOINT"),))
        root, journal, drill = _new_drill(base, injector=injector)
        (root / "state.txt").write_text("before", encoding="utf-8")
        required = False
        try:
            drill.mutate_file("task-checkpoint", "state.txt", b"after")
        except RecoveryRequiredError:
            required = True
        if not required:
            return False, "commit fault did not require recovery"
        raw = json.loads(journal.path.read_text(encoding="utf-8"))
        raw["phase"] = "forged-complete"
        journal.path.write_text(json.dumps(raw), encoding="utf-8")
        blocked = False
        try:
            drill.recover("task-checkpoint")
        except RecoveryBlockedError:
            blocked = True
        return (
            blocked and journal.path.exists(),
            "tampered integrity-bound checkpoint is blocked and preserved for diagnosis",
        )


def _snapshot_corruption_case() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-8-snapshot-") as tmp:
        base = Path(tmp)
        injector = FaultInjector((FaultSpec(FaultStage.COMMIT, case_id="FI-SNAPSHOT"),))
        root, journal, drill = _new_drill(base, injector=injector)
        (root / "state.txt").write_text("before", encoding="utf-8")
        required = False
        try:
            drill.mutate_file("task-snapshot", "state.txt", b"after")
        except RecoveryRequiredError:
            required = True
        if not required:
            return False, "snapshot fault did not require recovery"
        checkpoint = journal.load(
            require_integrity=True,
            expected_task_id="task-snapshot",
        )
        if checkpoint is None:
            return False, "missing recovery checkpoint"
        snapshot = drill.snapshot_root / str(checkpoint.state["snapshot"]) / "state.txt"
        snapshot.write_text("corrupted", encoding="utf-8")
        blocked = False
        try:
            drill.recover("task-snapshot")
        except RecoveryBlockedError:
            blocked = True
        return (
            blocked and journal.path.exists(),
            "corrupted known-good snapshot cannot be promoted as recovery authority",
        )


def _task_binding_case() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-8-binding-") as tmp:
        base = Path(tmp)
        injector = FaultInjector((FaultSpec(FaultStage.PREPARE, case_id="FI-BINDING"),))
        root, journal, drill = _new_drill(base, injector=injector)
        (root / "state.txt").write_text("before", encoding="utf-8")
        required = False
        try:
            drill.mutate_file("right-task", "state.txt", b"after")
        except RecoveryRequiredError:
            required = True
        if not required:
            return False, "binding fault did not require recovery"
        blocked = False
        try:
            drill.recover("wrong-task")
        except RecoveryBlockedError:
            blocked = True
        still_pending = journal.path.exists()
        drill.recover("right-task")
        return (
            blocked and still_pending and not journal.path.exists(),
            "recovery authority is bound to the exact task and cannot be consumed cross-task",
        )


def _narrow_restore_case() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-8-narrow-") as tmp:
        base = Path(tmp)
        injector = FaultInjector((FaultSpec(FaultStage.COMMIT, case_id="FI-NARROW"),))
        root, _, drill = _new_drill(base, injector=injector)
        target = root / "state.txt"
        authority = root / "authority.json"
        target.write_text("before", encoding="utf-8")
        authority.write_text('{"permission":"old"}', encoding="utf-8")
        required = False
        try:
            drill.mutate_file("task-narrow", "state.txt", b"after")
        except RecoveryRequiredError:
            required = True
        if not required:
            return False, "narrow-scope fault did not require recovery"
        authority.write_text('{"permission":"current"}', encoding="utf-8")
        drill.recover("task-narrow")
        return (
            target.read_text(encoding="utf-8") == "before"
            and authority.read_text(encoding="utf-8") == '{"permission":"current"}',
            "single-file recovery does not roll back unrelated permission/secret/tool-trust state",
        )


def _killswitch_prelaunch_case() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-8-prelaunch-") as tmp:
        root = Path(tmp)
        kill_switch = KillSwitch()
        kill_switch.trigger()
        sandbox = ProcessSandbox(
            root,
            allowed_executables={Path(sys.executable).name.lower()},
            kill_switch=kill_switch,
        )
        blocked = False
        try:
            sandbox.run([sys.executable, "-c", "print('never')"])
        except RuntimeError:
            blocked = True
        return blocked, "active KillSwitch rejects subprocess launch before execution"


def _killswitch_process_case() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-8-process-") as tmp:
        root = Path(tmp)
        kill_switch = KillSwitch()
        sandbox = ProcessSandbox(
            root,
            allowed_executables={Path(sys.executable).name.lower()},
            kill_switch=kill_switch,
        )
        process = sandbox.spawn_background(
            [sys.executable, "-c", "import time; time.sleep(30)"]
        )
        active_before = kill_switch.active_count
        triggered = kill_switch.trigger()
        try:
            process.process.wait(timeout=5)
        finally:
            process.close()
        return (
            active_before == 1
            and triggered == 1
            and process.returncode is not None
            and kill_switch.active_count == 0,
            "registered hanging subprocess is terminated and unregistered by KillSwitch",
        )


def _killswitch_mutation_case() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-8-killmutation-") as tmp:
        base = Path(tmp)
        kill_switch = KillSwitch()

        class KillAtWrite(FaultInjector):
            def hit(self, stage: FaultStage) -> None:
                if stage is FaultStage.WRITE and not kill_switch.triggered:
                    kill_switch.trigger()

        root, journal, drill = _new_drill(
            base,
            injector=KillAtWrite(),
            kill_switch=kill_switch,
        )
        target = root / "state.txt"
        target.write_text("before", encoding="utf-8")
        required = False
        try:
            drill.mutate_file("task-kill", "state.txt", b"after")
        except RecoveryRequiredError:
            required = True
        pending = journal.path.exists()
        kill_switch.reset()
        drill.recover("task-kill")
        return (
            required
            and pending
            and target.read_text(encoding="utf-8") == "before",
            "KillSwitch during multi-step mutation forces verified recovery before continuation",
        )


def _timeout_case() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-8-timeout-") as tmp:
        root = Path(tmp)
        sandbox = ProcessSandbox(
            root,
            allowed_executables={Path(sys.executable).name.lower()},
            kill_switch=KillSwitch(),
        )
        result = sandbox.run(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            timeout=0.05,
        )
        return (
            result.timed_out and result.returncode != 0,
            "subprocess hang is bounded by timeout and terminated without shell execution",
        )


def _backup_case() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-8-backup-") as tmp:
        base = Path(tmp)
        root = base / "project"
        root.mkdir()
        (root / "state.txt").write_text("known-good", encoding="utf-8")
        manager = BackupManager(base / "archives")
        archive = manager.create_archive(root, "r16-8")
        initial_hash = _sha256(archive)
        restored = base / "restored"
        manager.restore(archive, restored)
        restored_ok = (restored / "state.txt").read_text(encoding="utf-8") == "known-good"
        corrupted = base / "archives" / "corrupted.zip"
        corrupted.write_bytes(archive.read_bytes()[:-16])
        return (
            manager.verify(archive)
            and _sha256(archive) == initial_hash
            and restored_ok
            and not manager.verify(corrupted),
            "known-good archive restores with hashes; truncated synthetic backup is rejected",
        )


def _legacy_checkpoint_case() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-8-legacy-") as tmp:
        path = Path(tmp) / "legacy.json"
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
        readable = journal.load() is not None
        blocked = False
        try:
            journal.load(require_integrity=True)
        except ValueError:
            blocked = True
        return (
            readable and blocked,
            "legacy checkpoint remains readable as data but cannot become integrity authority",
        )


def build_report(source_sha: str) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for stage in FaultStage:
        passed, detail = _fault_stage_case(stage)
        cases.append(_case(f"fault_stage_{stage.value}_recovers", passed, detail))

    checks: tuple[tuple[str, Callable[[], tuple[bool, str]]], ...] = (
        ("resource_denial_recovers", _resource_denial_case),
        ("checkpoint_corruption_blocked", _checkpoint_corruption_case),
        ("snapshot_corruption_blocked", _snapshot_corruption_case),
        ("recovery_task_binding", _task_binding_case),
        ("narrow_restore_scope", _narrow_restore_case),
        ("killswitch_prelaunch", _killswitch_prelaunch_case),
        ("killswitch_hanging_process", _killswitch_process_case),
        ("killswitch_multistep_mutation", _killswitch_mutation_case),
        ("subprocess_timeout_hang", _timeout_case),
        ("backup_integrity_restore", _backup_case),
        ("legacy_checkpoint_non_authoritative", _legacy_checkpoint_case),
    )
    for name, check in checks:
        passed, detail = check()
        cases.append(_case(name, passed, detail))

    semantic = {
        "schema": "kodepoia.r16.8.fault-recovery-acceptance.v1",
        "cases": cases,
        "critical_veto": any(not item["pass"] for item in cases),
        "manual": "NONE",
        "security_claim": True,
        "synthetic_only": True,
        "network_calls": False,
        "live_secrets": False,
        "live_destructive_host_actions": False,
        "production_disaster_recovery_claim": False,
        "recovery_point_objective": "repository-local:last-verified-pre-mutation-snapshot",
        "fault_stages": [stage.value for stage in FaultStage],
    }
    semantic_bytes = json.dumps(
        semantic,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
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
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["summary"]["passed"] == report["summary"]["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
