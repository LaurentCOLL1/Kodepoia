from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class SandboxResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


class ProcessSandbox:
    """Restricted subprocess launcher, not a claim of full OS/container isolation."""

    def __init__(self, root: Path, allowed_executables: set[str] | None = None) -> None:
        self.root = root.resolve(strict=False)
        self.allowed_executables = {item.lower() for item in (allowed_executables or set())}

    def run(self, argv: Sequence[str], *, cwd: Path | None = None, timeout: float = 60.0, env: Mapping[str, str] | None = None) -> SandboxResult:
        if not argv:
            raise ValueError("argv cannot be empty")
        executable = Path(argv[0]).name.lower()
        if self.allowed_executables and executable not in self.allowed_executables:
            raise PermissionError(f"Executable not allowlisted: {executable}")
        workdir = (cwd or self.root).resolve(strict=False)
        if workdir != self.root and self.root not in workdir.parents:
            raise PermissionError(f"Working directory escapes sandbox root: {workdir}")
        clean_env = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "WINDIR": os.environ.get("WINDIR", ""), "TEMP": os.environ.get("TEMP", ""), "TMP": os.environ.get("TMP", ""), "HOME": os.environ.get("HOME", "")}
        if env:
            clean_env.update({str(k): str(v) for k, v in env.items()})
        try:
            process = subprocess.run(list(argv), cwd=workdir, env=clean_env, capture_output=True, text=True, shell=False, timeout=timeout, check=False)
            return SandboxResult(process.returncode, process.stdout, process.stderr)
        except subprocess.TimeoutExpired as exc:
            return SandboxResult(-1, exc.stdout or "", exc.stderr or "", timed_out=True)
