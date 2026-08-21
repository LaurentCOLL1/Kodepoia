from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch


@dataclass(frozen=True, slots=True)
class SandboxResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    cancelled: bool = False


class ProcessSandbox:
    """Restricted subprocess launcher integrated with the global kill switch.

    This is a protected launcher, not a claim of full OS/container isolation.
    The caller still controls which executables are allowlisted and which root
    the process is allowed to use as its working directory.
    """

    def __init__(
        self,
        root: Path,
        allowed_executables: set[str] | None = None,
        kill_switch: KillSwitch | None = None,
    ) -> None:
        self.root = root.resolve(strict=False)
        self.allowed_executables = {item.lower() for item in (allowed_executables or set())}
        self.kill_switch = kill_switch or GLOBAL_KILL_SWITCH

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: Mapping[str, str] | None = None,
    ) -> SandboxResult:
        if not argv:
            raise ValueError("argv cannot be empty")
        if self.kill_switch.triggered:
            raise RuntimeError("Kodepoia kill switch is active")

        executable = Path(argv[0]).name.lower()
        if self.allowed_executables and executable not in self.allowed_executables:
            raise PermissionError(f"Executable not allowlisted: {executable}")

        workdir = (cwd or self.root).resolve(strict=False)
        if workdir != self.root and self.root not in workdir.parents:
            raise PermissionError(f"Working directory escapes sandbox root: {workdir}")

        clean_env = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "WINDIR": os.environ.get("WINDIR", ""),
            "TEMP": os.environ.get("TEMP", ""),
            "TMP": os.environ.get("TMP", ""),
            "HOME": os.environ.get("HOME", ""),
        }
        if env:
            clean_env.update({str(key): str(value) for key, value in env.items()})

        process = subprocess.Popen(
            list(argv),
            cwd=workdir,
            env=clean_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
        )
        self.kill_switch.register(process)
        start = time.monotonic()
        timed_out = False
        cancelled = False
        try:
            while process.poll() is None:
                if self.kill_switch.triggered:
                    cancelled = True
                    self.kill_switch._stop_process(process)
                    break
                if timeout >= 0 and time.monotonic() - start >= timeout:
                    timed_out = True
                    self.kill_switch._stop_process(process)
                    break
                time.sleep(0.02)
            stdout, stderr = process.communicate()
            if self.kill_switch.triggered and not timed_out and process.returncode != 0:
                cancelled = True
        finally:
            self.kill_switch.unregister(process)

        return SandboxResult(
            process.returncode if process.returncode is not None else -1,
            stdout,
            stderr,
            timed_out=timed_out,
            cancelled=cancelled,
        )
