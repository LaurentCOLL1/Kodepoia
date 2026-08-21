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
    """Capability-limited subprocess boundary.

    R1 deliberately does not claim OS-level virtualization. Commands are argv-only,
    shell=False, cwd-scoped, allowlisted and Guardian-gated. Stronger Windows
    isolation backends can be plugged in later without changing this interface.
    """

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
        request = ActionRequest(ActionKind.PROCESS_RUN, actor, cwd, argv[0], {"argv": list(argv), "cwd": str(cwd)})
        self.guardian.require_allowed(request, confirmed=confirmed)
        child_env: dict[str, str] = dict(os.environ) if self.profile.inherit_environment else {}
        if env:
            child_env.update({str(k): str(v) for k, v in env.items()})
        child_env.setdefault("PATH", os.environ.get("PATH", ""))
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
