from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import pytest

from kodepoia.core.backup import BackupManager
from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.core.recovery import RecoveryJournal
from kodepoia.core.sandbox import ProcessSandbox


def test_default_sandbox_uses_process_global_kill_switch(tmp_path: Path) -> None:
    assert ProcessSandbox(tmp_path).kill_switch is GLOBAL_KILL_SWITCH


def test_kill_switch_terminates_active_sandbox_process(tmp_path: Path) -> None:
    switch = KillSwitch()
    sandbox = ProcessSandbox(tmp_path, {Path(sys.executable).name}, switch)
    holder = {}

    def run_long_process() -> None:
        holder["result"] = sandbox.run(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            timeout=30,
        )

    thread = threading.Thread(target=run_long_process, daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    while switch.active_count == 0 and time.monotonic() < deadline:
        time.sleep(0.02)
    assert switch.active_count == 1

    stopped = switch.trigger()
    thread.join(timeout=5)

    assert stopped == 1
    assert not thread.is_alive()
    assert holder["result"].cancelled
    assert switch.active_count == 0
    with pytest.raises(RuntimeError):
        sandbox.run([sys.executable, "-c", "print('blocked')"])

    switch.reset()
    assert not switch.triggered


def test_sandbox_drains_stdout_and_stderr_while_process_runs(tmp_path: Path) -> None:
    switch = KillSwitch()
    sandbox = ProcessSandbox(tmp_path, {Path(sys.executable).name}, switch)
    payload_size = 512 * 1024
    script = (
        "import sys;"
        f"sys.stdout.write('x'*{payload_size});sys.stdout.flush();"
        f"sys.stderr.write('y'*{payload_size});sys.stderr.flush()"
    )

    result = sandbox.run([sys.executable, "-c", script], timeout=5)

    assert result.returncode == 0
    assert not result.timed_out
    assert not result.cancelled
    assert len(result.stdout) == payload_size
    assert len(result.stderr) == payload_size


def test_background_process_discards_unused_output_without_backpressure(tmp_path: Path) -> None:
    switch = KillSwitch()
    sandbox = ProcessSandbox(tmp_path, {Path(sys.executable).name}, switch)
    payload_size = 2 * 1024 * 1024
    script = (
        "import sys;"
        f"sys.stdout.write('x'*{payload_size});sys.stdout.flush();"
        f"sys.stderr.write('y'*{payload_size});sys.stderr.flush()"
    )
    process = sandbox.spawn_background([sys.executable, "-c", script])
    deadline = time.monotonic() + 5
    while process.returncode is None and time.monotonic() < deadline:
        time.sleep(0.02)
    try:
        assert process.returncode == 0
        assert switch.active_count == 1
    finally:
        process.close()
    assert switch.active_count == 0


def test_backup_verifies_and_restores(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "a.txt").write_text("alpha", encoding="utf-8")
    nested = project / "nested"
    nested.mkdir()
    (nested / "b.bin").write_bytes(b"beta\x00gamma")

    manager = BackupManager(tmp_path / "backups")
    archive = manager.create_archive(project, "acceptance")

    assert manager.verify(archive)
    restored = manager.restore(archive, tmp_path / "restored")
    assert (restored / "a.txt").read_text(encoding="utf-8") == "alpha"
    assert (restored / "nested" / "b.bin").read_bytes() == b"beta\x00gamma"


def test_recovery_survives_reinstantiation_and_resumes(tmp_path: Path) -> None:
    path = tmp_path / "recovery" / "active.json"
    first_runtime = RecoveryJournal(path)
    first_runtime.save("task-42", "patching", {"completed": ["a.py"], "next": "b.py"})

    # Simulate a crash/restart by discarding the first object and constructing a
    # brand-new runtime over the same durable checkpoint file.
    second_runtime = RecoveryJournal(path)
    checkpoint = second_runtime.load()
    assert checkpoint is not None
    assert checkpoint.task_id == "task-42"
    assert checkpoint.phase == "patching"
    assert checkpoint.state["next"] == "b.py"

    resumed = second_runtime.resume(lambda item: f"resume:{item.state['next']}")
    assert resumed == "resume:b.py"
    assert second_runtime.load() is None
