from __future__ import annotations

import errno
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.core.recovery import RecoveryJournal
from kodepoia.core.safe_change import SafeChangeManager


class FaultStage(StrEnum):
    PREPARE = "prepare"
    WRITE = "write"
    COMMIT = "commit"
    VERIFY = "verify"
    CLEANUP = "cleanup"


class FaultMode(StrEnum):
    ERROR = "error"
    INTERRUPT = "interrupt"
    RESOURCE_DENIED = "resource_denied"


@dataclass(frozen=True, slots=True)
class FaultSpec:
    stage: FaultStage
    mode: FaultMode = FaultMode.ERROR
    case_id: str = "synthetic-fault"

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("fault case_id cannot be empty")


class InjectedFault(RuntimeError):
    def __init__(self, spec: FaultSpec) -> None:
        super().__init__(f"injected {spec.mode.value} fault at {spec.stage.value}: {spec.case_id}")
        self.spec = spec


class FaultInjector:
    """Deterministic, one-shot synthetic fault injector for bounded test/drill paths."""

    def __init__(self, faults: tuple[FaultSpec, ...] = ()) -> None:
        self._faults = tuple(faults)
        self._fired: set[int] = set()

    @property
    def fired_case_ids(self) -> tuple[str, ...]:
        return tuple(
            spec.case_id for index, spec in enumerate(self._faults) if index in self._fired
        )

    def hit(self, stage: FaultStage) -> None:
        for index, spec in enumerate(self._faults):
            if index in self._fired or spec.stage is not stage:
                continue
            self._fired.add(index)
            if spec.mode is FaultMode.INTERRUPT:
                raise InterruptedError(
                    f"synthetic interruption at {stage.value}: {spec.case_id}"
                )
            if spec.mode is FaultMode.RESOURCE_DENIED:
                raise OSError(
                    errno.ENOSPC,
                    f"synthetic resource denial at {stage.value}: {spec.case_id}",
                )
            raise InjectedFault(spec)


class RecoveryRequiredError(RuntimeError):
    pass


class RecoveryBlockedError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RecoveryDrillResult:
    task_id: str
    status: str
    target: str
    baseline_sha256: str | None
    current_sha256: str | None
    recovery_point: str


class FileRecoveryDrill:
    """Bounded single-file mutation drill using SafeChange + integrity-bound recovery.

    This helper is intentionally narrow: it exercises repository-local recovery
    semantics for one project file. It does not claim production disaster recovery.
    """

    RECOVERY_POINT = "last-verified-pre-mutation-snapshot"

    def __init__(
        self,
        project_root: Path,
        snapshot_root: Path,
        journal: RecoveryJournal,
        *,
        kill_switch: KillSwitch = GLOBAL_KILL_SWITCH,
        injector: FaultInjector | None = None,
    ) -> None:
        self.project_root = project_root.resolve(strict=True)
        self.safe_change = SafeChangeManager(self.project_root, snapshot_root)
        self.snapshot_root = self.safe_change.snapshot_root
        self.journal = journal
        self.kill_switch = kill_switch
        self.injector = injector or FaultInjector()

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _target(self, relative_path: str) -> tuple[Path, str]:
        candidate = Path(relative_path)
        if candidate.is_absolute() or relative_path.strip() in {"", "."}:
            raise ValueError("recovery drill target must be a non-empty relative path")
        target = self.safe_change.ensure_inside_project(self.project_root / candidate)
        relative = target.relative_to(self.project_root).as_posix()
        if relative.startswith("../") or relative == "..":
            raise ValueError("recovery drill target escapes project root")
        if target.exists() and not target.is_file():
            raise ValueError("recovery drill supports file targets only")
        return target, relative

    def _record_failure(self, task_id: str, state: dict[str, object], stage: FaultStage) -> None:
        state = dict(state)
        state["failed_stage"] = stage.value
        self.journal.save(task_id, "recovery_required", state)

    def mutate_file(self, task_id: str, relative_path: str, payload: bytes) -> RecoveryDrillResult:
        if not task_id.strip():
            raise ValueError("task_id cannot be empty")
        if self.journal.path.exists():
            raise RecoveryRequiredError("pending recovery checkpoint must be resolved first")
        if self.kill_switch.triggered:
            raise RuntimeError("KillSwitch is active before recovery drill prepare")

        target, relative = self._target(relative_path)
        existed = target.exists()
        baseline = self._sha256(target) if existed else None
        snapshot = self.safe_change.snapshot([target])
        state: dict[str, object] = {
            "target": relative,
            "snapshot": snapshot.name,
            "existed": existed,
            "baseline_sha256": baseline,
            "candidate_sha256": hashlib.sha256(payload).hexdigest(),
        }
        stage = FaultStage.PREPARE
        self.journal.save(task_id, "prepared", state)
        try:
            self.injector.hit(stage)
            self._ensure_running(stage)

            target.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary_name = tempfile.mkstemp(
                prefix=f".{target.name}.",
                suffix=".r16-8.tmp",
                dir=target.parent,
            )
            temporary = Path(temporary_name)
            try:
                stage = FaultStage.WRITE
                with os.fdopen(fd, "wb") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                self.journal.save(task_id, "written", state)
                self.injector.hit(stage)
                self._ensure_running(stage)

                stage = FaultStage.COMMIT
                os.replace(temporary, target)
                self.journal.save(task_id, "committed", state)
                self.injector.hit(stage)
                self._ensure_running(stage)

                stage = FaultStage.VERIFY
                current = self._sha256(target)
                if current != state["candidate_sha256"]:
                    raise OSError("committed file failed candidate hash verification")
                self.journal.save(task_id, "verified", state)
                self.injector.hit(stage)
                self._ensure_running(stage)

                stage = FaultStage.CLEANUP
                temporary.unlink(missing_ok=True)
                self.injector.hit(stage)
                self._ensure_running(stage)
            finally:
                temporary.unlink(missing_ok=True)
        except Exception as exc:
            self._record_failure(task_id, state, stage)
            if isinstance(exc, RecoveryRequiredError):
                raise
            raise RecoveryRequiredError(
                f"recovery required after {stage.value} stage failure"
            ) from exc

        self.journal.clear()
        current = self._sha256(target)
        return RecoveryDrillResult(
            task_id=task_id,
            status="complete",
            target=relative,
            baseline_sha256=baseline,
            current_sha256=current,
            recovery_point=self.RECOVERY_POINT,
        )

    def _ensure_running(self, stage: FaultStage) -> None:
        if self.kill_switch.triggered:
            raise RecoveryRequiredError(f"KillSwitch triggered during {stage.value}")

    def recover(self, task_id: str) -> RecoveryDrillResult:
        try:
            checkpoint = self.journal.load(
                require_integrity=True,
                expected_task_id=task_id,
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RecoveryBlockedError("recovery checkpoint is invalid or corrupted") from exc
        if checkpoint is None:
            raise RecoveryBlockedError("no recovery checkpoint exists")

        state = checkpoint.state
        try:
            relative = str(state["target"])
            snapshot_name = str(state["snapshot"])
            existed = bool(state["existed"])
            baseline_value = state["baseline_sha256"]
            baseline = None if baseline_value is None else str(baseline_value)
        except (KeyError, TypeError, ValueError) as exc:
            raise RecoveryBlockedError("recovery checkpoint state is incomplete") from exc

        target, normalized_relative = self._target(relative)
        if normalized_relative != relative:
            raise RecoveryBlockedError("recovery target binding changed")
        snapshot = (self.snapshot_root / snapshot_name).resolve(strict=False)
        if snapshot.parent != self.snapshot_root:
            raise RecoveryBlockedError("recovery snapshot escapes snapshot root")

        source = snapshot / relative
        if existed:
            if (
                baseline is None
                or not source.is_file()
                or self._sha256(source) != baseline
            ):
                raise RecoveryBlockedError("known-good recovery snapshot failed integrity check")
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary_name = tempfile.mkstemp(
                prefix=f".{target.name}.",
                suffix=".restore.tmp",
                dir=target.parent,
            )
            temporary = Path(temporary_name)
            try:
                with os.fdopen(fd, "wb") as handle, source.open("rb") as input_handle:
                    for chunk in iter(lambda: input_handle.read(1024 * 1024), b""):
                        handle.write(chunk)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
            if self._sha256(target) != baseline:
                raise RecoveryBlockedError("restored target failed integrity verification")
            current = baseline
        else:
            if source.exists():
                raise RecoveryBlockedError(
                    "unexpected snapshot material for previously absent target"
                )
            target.unlink(missing_ok=True)
            current = None

        self.journal.clear()
        return RecoveryDrillResult(
            task_id=task_id,
            status="recovered",
            target=relative,
            baseline_sha256=baseline,
            current_sha256=current,
            recovery_point=self.RECOVERY_POINT,
        )
