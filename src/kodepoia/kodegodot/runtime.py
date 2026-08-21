from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from kodepoia.core.sandbox import ProcessSandbox, SandboxResult
from kodepoia.kodecode.workspace import WorkspaceBoundary

_VERSION = re.compile(r"(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?(?P<tail>.*)")


class SandboxRunner(Protocol):
    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: dict[str, str] | None = None,
    ) -> SandboxResult: ...


@dataclass(frozen=True, slots=True)
class GodotVersionInfo:
    raw: str
    major: int
    minor: int
    patch: int | None
    suffix: str
    compatible_47: bool


@dataclass(frozen=True, slots=True)
class GodotInvocationResult:
    operation: str
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    cancelled: bool

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out and not self.cancelled


class GodotRuntime:
    """Restricted Godot 4.7 CLI facade backed by ProcessSandbox.

    Kodepoia constructs every command itself. Callers never provide arbitrary
    engine flags or argv fragments.
    """

    def __init__(
        self,
        root: Path,
        executable: str = "godot",
        *,
        runner: SandboxRunner | None = None,
    ) -> None:
        self.boundary = WorkspaceBoundary(root)
        self.executable = str(executable)
        executable_name = Path(self.executable).name.lower()
        self.runner = runner or ProcessSandbox(
            self.boundary.root,
            allowed_executables={executable_name},
        )

    def version(self, *, timeout: float = 15.0) -> GodotVersionInfo:
        result = self.runner.run(
            [self.executable, "--version"], cwd=self.boundary.root, timeout=timeout
        )
        if result.returncode != 0 or result.timed_out or result.cancelled:
            raise RuntimeError(
                f"Unable to query Godot version: rc={result.returncode} stderr={result.stderr.strip()}"
            )
        raw = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
        match = _VERSION.match(raw)
        if not match:
            raise RuntimeError(f"Unrecognized Godot version string: {raw!r}")
        major = int(match.group("major"))
        minor = int(match.group("minor"))
        patch_raw = match.group("patch")
        return GodotVersionInfo(
            raw=raw,
            major=major,
            minor=minor,
            patch=int(patch_raw) if patch_raw is not None else None,
            suffix=match.group("tail").lstrip(".-"),
            compatible_47=(major, minor) == (4, 7),
        )

    def require_47(self) -> GodotVersionInfo:
        info = self.version()
        if not info.compatible_47:
            raise RuntimeError(f"KodeGodot R5 requires Godot 4.7.x, got {info.raw}")
        return info

    def check_script(self, path: str, *, timeout: float = 60.0) -> GodotInvocationResult:
        target = self.boundary.resolve(path, must_exist=True)
        if not target.is_file() or target.suffix.lower() != ".gd":
            raise ValueError(f"GDScript file required: {path}")
        relative = self.boundary.relative(target)
        return self._invoke(
            "check-script",
            ["--headless", "--path", ".", "--check-only", "--script", relative],
            timeout=timeout,
        )

    def import_project(self, *, timeout: float = 300.0) -> GodotInvocationResult:
        self._require_project()
        return self._invoke("import", ["--headless", "--path", ".", "--import"], timeout=timeout)

    def smoke_project(
        self,
        *,
        scene: str | None = None,
        quit_after: int = 2,
        timeout: float = 60.0,
    ) -> GodotInvocationResult:
        self._require_project()
        if not 1 <= quit_after <= 600:
            raise ValueError("quit_after must be between 1 and 600")
        args = ["--headless", "--path", ".", "--quit-after", str(quit_after)]
        if scene is not None:
            target = self.boundary.resolve(scene, must_exist=True)
            if not target.is_file() or target.suffix.lower() not in {".tscn", ".scn"}:
                raise ValueError(f"Godot scene file required: {scene}")
            args.extend(["--scene", f"res://{self.boundary.relative(target)}"])
        return self._invoke("smoke-project", args, timeout=timeout)

    def _require_project(self) -> None:
        project = self.boundary.resolve("project.godot", must_exist=True)
        if not project.is_file():
            raise FileNotFoundError("project.godot is not a file")

    def _invoke(self, operation: str, args: list[str], *, timeout: float) -> GodotInvocationResult:
        result = self.runner.run(
            [self.executable, *args], cwd=self.boundary.root, timeout=timeout
        )
        return GodotInvocationResult(
            operation=operation,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=result.timed_out,
            cancelled=result.cancelled,
        )
