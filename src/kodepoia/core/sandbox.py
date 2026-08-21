from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .guardian import KodeGuardian
from .types import ActionKind, ActionRequest


@dataclass(frozen=True, slots=True)
class SandboxProfile:
    allowed_executables: frozenset[str]
    allowed_roots: tuple[Path, ...]
    timeout_seconds: int = 60
    inherit_environment: bool = False


@dataclass(frozen=True, slots=True)
class SandboxResult:
    returncode: int
    stdout: str
    stderr: str


class SandboxViolation(RuntimeError):
    pass


class KodeSandbox:
    """Capability-limited subprocess boundary; stronger OS backends may replace it later."""

    def __init__(self, guardian: KodeGuardian, profile: SandboxProfile) -> None:
        self.guardian = guardian
        self.profile = profile
        self._children: set[subprocess.Popen[str]] = set()

    def run(self, argv: Sequence[str], *, cwd: Path, actor: str, confirmed: bool = False, env: Mapping[str, str] | None = None) -> SandboxResult:
        if not argv:
            raise SandboxViolation("empty command")
        executable = Path(argv[0]).name.casefold()
        allowed = {Path(item).name.casefold() for item in self.profile.allowed_executables}
        if executable not in allowed:
            raise SandboxViolation(f"executable is not allowlisted: {argv[0]}")
        cwd = cwd.resolve()
        if not any(cwd == root.resolve() or cwd.is_relative_to(root.resolve()) for root in self.profile.allowed_roots):
            raise SandboxViolation(f"working directory escapes sandbox roots: {cwd}")
        self.guardian.require_allowed(ActionRequest(ActionKind.PROCESS_RUN, actor, cwd, argv[0], {"argv": list(argv), "cwd": str(cwd)}), confirmed=confirmed)
        if self.profile.inherit_environment:
            child_env = dict(os.environ)
        else:
            safe_keys = ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "COMSPEC", "PATHEXT", "HOME", "LANG")
            child_env = {key: os.environ[key] for key in safe_keys if key in os.environ}
        if env:
            child_env.update({str(k): str(v) for k, v in env.items()})
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
        process = subprocess.Popen(list(argv), cwd=cwd, env=child_env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False, creationflags=creationflags)
        self._children.add(process)
        try:
            stdout, stderr = process.communicate(timeout=self.profile.timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise TimeoutError(f"sandbox command timed out after {self.profile.timeout_seconds}s")
        finally:
            self._children.discard(process)
        return SandboxResult(process.returncode, stdout, stderr)

    def kill_all(self) -> int:
        killed = 0
        for process in tuple(self._children):
            if process.poll() is None:
                process.kill()
                killed += 1
            self._children.discard(process)
        return killed
