from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from kodepoia.core.sandbox import ProcessSandbox, SandboxResult
from kodepoia.kodecode.workspace import WorkspaceBoundary
from kodepoia.kodegodot.exporting import GodotExportPresetInspector

_VERSION = re.compile(r"(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?(?P<tail>.*)")
_OUTPUT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,127}$")

# Godot 4.7 has a documented Windows startup regression around probing drives.
# Keep the process kill-switch controlled, but allow enough time for the CLI to
# return on affected Windows 11 systems instead of misclassifying startup delay
# as an incompatible engine.
VERSION_TIMEOUT_SECONDS = 90.0
CHECK_SCRIPT_TIMEOUT_SECONDS = 120.0


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


@dataclass(frozen=True, slots=True)
class GodotBenchmarkResult:
    scene: str | None
    frames: int
    elapsed_seconds: float
    effective_fps: float
    invocation: GodotInvocationResult


class GodotRuntime:
    """Restricted Godot 4.7 CLI facade backed by ProcessSandbox."""

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

    def version(self, *, timeout: float = VERSION_TIMEOUT_SECONDS) -> GodotVersionInfo:
        if not 1.0 <= float(timeout) <= 300.0:
            raise ValueError("Godot version timeout must be between 1 and 300 seconds")
        result = self.runner.run([self.executable, "--version"], cwd=self.boundary.root, timeout=timeout)
        if result.returncode != 0 or result.timed_out or result.cancelled:
            raise RuntimeError(
                "Unable to query Godot version: "
                f"rc={result.returncode} timed_out={result.timed_out} "
                f"cancelled={result.cancelled} timeout={float(timeout):g}s "
                f"stderr={result.stderr.strip()}"
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

    def check_script(self, path: str, *, timeout: float = CHECK_SCRIPT_TIMEOUT_SECONDS) -> GodotInvocationResult:
        target = self.boundary.resolve(path, must_exist=True)
        if not target.is_file() or target.suffix.lower() != ".gd":
            raise ValueError(f"GDScript file required: {path}")
        return self._invoke(
            "check-script",
            ["--headless", "--path", ".", "--check-only", "--script", self.boundary.relative(target)],
            timeout=timeout,
        )

    def import_project(self, *, timeout: float = 300.0) -> GodotInvocationResult:
        self._require_project()
        return self._invoke("import", ["--headless", "--path", ".", "--import"], timeout=timeout)

    def smoke_project(self, *, scene: str | None = None, quit_after: int = 2, timeout: float = 60.0) -> GodotInvocationResult:
        self._require_project()
        if not 1 <= quit_after <= 600:
            raise ValueError("quit_after must be between 1 and 600")
        args = ["--headless", "--path", ".", "--quit-after", str(quit_after)]
        if scene is not None:
            args.extend(["--scene", self._scene_uri(scene)])
        return self._invoke("smoke-project", args, timeout=timeout)

    def export_project(
        self,
        *,
        preset: str,
        output_name: str,
        mode: str = "release",
        timeout: float = 900.0,
    ) -> GodotInvocationResult:
        self._require_project()
        GodotExportPresetInspector(self.boundary.root).require(preset)
        output_name = self._safe_output_name(output_name)
        flag = {"release": "--export-release", "debug": "--export-debug", "pack": "--export-pack"}.get(mode)
        if flag is None:
            raise ValueError("export mode must be release, debug or pack")
        output_dir = self.boundary.root / ".kodepoia" / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        relative = (output_dir / output_name).relative_to(self.boundary.root).as_posix()
        return self._invoke("export", ["--headless", "--path", ".", flag, preset, relative], timeout=timeout)

    def capture_movie(
        self,
        *,
        scene: str,
        output_name: str,
        frames: int = 60,
        fps: int = 30,
        timeout: float = 900.0,
    ) -> GodotInvocationResult:
        self._require_project()
        if not 1 <= frames <= 36000:
            raise ValueError("frames must be between 1 and 36000")
        if not 1 <= fps <= 240:
            raise ValueError("fps must be between 1 and 240")
        output_name = self._safe_output_name(output_name)
        if not output_name.lower().endswith(".avi"):
            raise ValueError("R5.5 movie output must use .avi")
        output_dir = self.boundary.root / ".kodepoia" / "captures"
        output_dir.mkdir(parents=True, exist_ok=True)
        relative = (output_dir / output_name).relative_to(self.boundary.root).as_posix()
        # Movie Maker requires an actual renderer. Godot's --headless mode uses a
        # dummy RenderingServer, which cannot provide the frame textures required
        # by --write-movie and can crash in texture_2d_get(). Keep the command
        # sandboxed, but allow the platform display/render driver for capture.
        return self._invoke(
            "capture-movie",
            [
                "--path", ".", "--write-movie", relative,
                "--fixed-fps", str(fps), "--quit-after", str(frames), "--scene", self._scene_uri(scene),
            ],
            timeout=timeout,
        )

    def benchmark_scene(self, *, scene: str | None = None, frames: int = 120, timeout: float = 300.0) -> GodotBenchmarkResult:
        if not 1 <= frames <= 3600:
            raise ValueError("benchmark frames must be between 1 and 3600")
        started = time.monotonic()
        invocation = self.smoke_project(scene=scene, quit_after=frames, timeout=timeout)
        elapsed = max(time.monotonic() - started, 1e-9)
        return GodotBenchmarkResult(scene=scene, frames=frames, elapsed_seconds=elapsed, effective_fps=frames / elapsed, invocation=invocation)

    def _scene_uri(self, scene: str) -> str:
        target = self.boundary.resolve(scene, must_exist=True)
        if not target.is_file() or target.suffix.lower() not in {".tscn", ".scn"}:
            raise ValueError(f"Godot scene file required: {scene}")
        return f"res://{self.boundary.relative(target)}"

    @staticmethod
    def _safe_output_name(value: str) -> str:
        if not _OUTPUT_NAME.fullmatch(value) or value in {".", ".."}:
            raise ValueError("output_name must be a simple file name")
        return value

    def _require_project(self) -> None:
        project = self.boundary.resolve("project.godot", must_exist=True)
        if not project.is_file():
            raise FileNotFoundError("project.godot is not a file")

    def _invoke(self, operation: str, args: list[str], *, timeout: float) -> GodotInvocationResult:
        if not 1.0 <= float(timeout) <= 1800.0:
            raise ValueError("Godot invocation timeout must be between 1 and 1800 seconds")
        result = self.runner.run([self.executable, *args], cwd=self.boundary.root, timeout=timeout)
        return GodotInvocationResult(
            operation=operation,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=result.timed_out,
            cancelled=result.cancelled,
        )
