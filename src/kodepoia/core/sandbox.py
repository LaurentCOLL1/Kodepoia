from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Mapping, Sequence

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch


_BASE_ENVIRONMENT_KEYS = (
    "PATH",
    "SYSTEMROOT",
    "WINDIR",
    "TEMP",
    "TMP",
    "HOME",
    "USERPROFILE",
    "HOMEDRIVE",
    "HOMEPATH",
    "APPDATA",
    "LOCALAPPDATA",
    "XDG_DATA_HOME",
    "XDG_CONFIG_HOME",
    "XDG_CACHE_HOME",
)


@dataclass(frozen=True, slots=True)
class SandboxResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    cancelled: bool = False


class ManagedProcess:
    """Persistent subprocess registered with the global Kodepoia kill switch."""

    def __init__(self, process: subprocess.Popen[bytes], kill_switch: KillSwitch) -> None:
        self.process = process
        self.kill_switch = kill_switch
        self._closed = False

    @property
    def stdin(self) -> BinaryIO:
        if self.process.stdin is None:
            raise RuntimeError("Managed process has no stdin pipe")
        return self.process.stdin

    @property
    def stdout(self) -> BinaryIO:
        if self.process.stdout is None:
            raise RuntimeError("Managed process has no stdout pipe")
        return self.process.stdout

    @property
    def stderr(self) -> BinaryIO:
        if self.process.stderr is None:
            raise RuntimeError("Managed process has no stderr pipe")
        return self.process.stderr

    @property
    def returncode(self) -> int | None:
        return self.process.poll()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            if self.process.poll() is None:
                self.kill_switch._stop_process(self.process)
            try:
                self.process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2.0)
        finally:
            self.kill_switch.unregister(self.process)
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                if stream is not None:
                    stream.close()

    def __enter__(self) -> ManagedProcess:
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        self.close()


class ProcessSandbox:
    """Restricted subprocess launcher integrated with the global kill switch.

    This is a protected launcher, not a claim of full OS/container isolation.
    The caller still controls which executables are allowlisted and which root
    the process is allowed to use as its working directory. Only a bounded set
    of non-secret OS path variables is inherited by default so desktop tools
    such as Godot can locate their normal user data/settings directories.
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

    def _validate_launch(
        self,
        argv: Sequence[str],
        cwd: Path | None,
        env: Mapping[str, str] | None,
    ) -> tuple[Path, dict[str, str]]:
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

        clean_env = {key: os.environ.get(key, "") for key in _BASE_ENVIRONMENT_KEYS}
        if env:
            clean_env.update({str(key): str(value) for key, value in env.items()})
        return workdir, clean_env

    def spawn_piped(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> ManagedProcess:
        """Launch a persistent binary stdio process under sandbox/kill-switch policy."""

        workdir, clean_env = self._validate_launch(argv, cwd, env)
        process = subprocess.Popen(
            list(argv),
            cwd=workdir,
            env=clean_env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            shell=False,
            bufsize=0,
        )
        self.kill_switch.register(process)
        return ManagedProcess(process, self.kill_switch)

    def spawn_background(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> ManagedProcess:
        """Launch a persistent network/background process without unused stdio pipes.

        This is intended for services such as Godot's loopback LSP/DAP servers,
        where communication happens over sockets. Redirecting unused stdout/stderr
        pipes can otherwise block a verbose child on pipe backpressure.
        """

        workdir, clean_env = self._validate_launch(argv, cwd, env)
        process = subprocess.Popen(
            list(argv),
            cwd=workdir,
            env=clean_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=False,
            shell=False,
        )
        self.kill_switch.register(process)
        return ManagedProcess(process, self.kill_switch)

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: Mapping[str, str] | None = None,
    ) -> SandboxResult:
        workdir, clean_env = self._validate_launch(argv, cwd, env)
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
        timed_out = False
        cancelled = False
        try:
            try:
                stdout, stderr = process.communicate(timeout=None if timeout < 0 else timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                self.kill_switch._stop_process(process)
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
