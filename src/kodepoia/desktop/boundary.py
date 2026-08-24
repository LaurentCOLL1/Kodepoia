from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

from .contracts import DesktopToolKind

_ALLOWED_EXECUTABLE_NAMES: dict[DesktopToolKind, frozenset[str]] = {
    DesktopToolKind.DOTNET: frozenset({"dotnet", "dotnet.exe"}),
    DesktopToolKind.MSBUILD: frozenset({"msbuild", "msbuild.exe"}),
    DesktopToolKind.CMAKE: frozenset({"cmake", "cmake.exe"}),
    DesktopToolKind.QT_PATHS: frozenset(
        {"qtpaths", "qtpaths.exe", "qtpaths6", "qtpaths6.exe"}
    ),
    DesktopToolKind.CARGO: frozenset({"cargo", "cargo.exe"}),
    DesktopToolKind.RUSTC: frozenset({"rustc", "rustc.exe"}),
}
_ALLOWED_ENV_KEYS = frozenset({"KODEPOIA_RUN_ID", "TEMP", "TMP"})
_MAX_ENV_VALUE = 4096


class DesktopBoundaryError(ValueError):
    pass


def _within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def validate_environment_overrides(
    overrides: Mapping[str, str] | None,
) -> dict[str, str]:
    if not overrides:
        return {}
    clean: dict[str, str] = {}
    for raw_key, raw_value in overrides.items():
        key = str(raw_key).upper()
        value = str(raw_value)
        if key not in _ALLOWED_ENV_KEYS:
            raise DesktopBoundaryError(f"environment override is not allowlisted: {raw_key}")
        if "\x00" in value or len(value) > _MAX_ENV_VALUE:
            raise DesktopBoundaryError("environment value is invalid or too large")
        clean[key] = value
    return clean


class DesktopToolchainBoundary:
    """Validate R12 desktop paths/toolchains and build fixed argv; never launch a process."""

    def __init__(
        self,
        *,
        allowed_runtime_roots: Iterable[Path],
        project_root: Path,
        staging_root: Path,
    ) -> None:
        roots = tuple(Path(item).resolve(strict=False) for item in allowed_runtime_roots)
        if not roots:
            raise ValueError("at least one desktop runtime root is required")
        self.allowed_runtime_roots = roots
        self.project_root = Path(project_root).resolve(strict=False)
        self.staging_root = Path(staging_root).resolve(strict=False)

    def validate_executable(self, kind: DesktopToolKind, candidate: Path) -> Path:
        try:
            resolved = Path(candidate).resolve(strict=True)
        except OSError as exc:
            raise DesktopBoundaryError(f"desktop toolchain executable is unavailable: {candidate}") from exc
        if not resolved.is_file():
            raise DesktopBoundaryError("desktop toolchain executable must be a regular file")
        if resolved.name.casefold() not in _ALLOWED_EXECUTABLE_NAMES[kind]:
            raise DesktopBoundaryError(
                f"unexpected executable for {kind.value}: {resolved.name}"
            )
        if not any(_within(resolved, root) for root in self.allowed_runtime_roots):
            raise DesktopBoundaryError("desktop toolchain executable escapes configured roots")
        return resolved

    def validate_project_file(
        self,
        path: Path,
        *,
        suffixes: frozenset[str],
    ) -> Path:
        try:
            resolved = Path(path).resolve(strict=True)
        except OSError as exc:
            raise DesktopBoundaryError("desktop project input is unavailable") from exc
        if not resolved.is_file() or not _within(resolved, self.project_root):
            raise DesktopBoundaryError("desktop project input escapes project root")
        if suffixes and resolved.suffix.casefold() not in suffixes:
            raise DesktopBoundaryError("desktop project input suffix is not allowlisted")
        return resolved

    def validate_staging_path(self, path: Path) -> Path:
        resolved = Path(path).resolve(strict=False)
        if not _within(resolved, self.staging_root):
            raise DesktopBoundaryError("desktop output escapes staging root")
        return resolved

    def build_probe_argv(
        self,
        kind: DesktopToolKind,
        executable: Path,
    ) -> tuple[str, ...]:
        exe = self.validate_executable(kind, executable)
        args: dict[DesktopToolKind, tuple[str, ...]] = {
            DesktopToolKind.DOTNET: ("--version",),
            DesktopToolKind.MSBUILD: ("-version", "-nologo"),
            DesktopToolKind.CMAKE: ("--version",),
            DesktopToolKind.QT_PATHS: ("--qt-version",),
            DesktopToolKind.CARGO: ("--version",),
            DesktopToolKind.RUSTC: ("--version",),
        }
        return (str(exe), *args[kind])

    def build_dotnet_argv(
        self,
        executable: Path,
        *,
        operation: str,
        project_file: Path,
        configuration: str,
    ) -> tuple[str, ...]:
        if operation not in {"build", "test"}:
            raise DesktopBoundaryError("dotnet operation is not allowlisted")
        if configuration not in {"Debug", "Release"}:
            raise DesktopBoundaryError("dotnet configuration is not allowlisted")
        exe = self.validate_executable(DesktopToolKind.DOTNET, executable)
        project = self.validate_project_file(
            project_file,
            suffixes=frozenset({".csproj", ".sln", ".slnx"}),
        )
        return (
            str(exe),
            operation,
            str(project),
            "--no-restore",
            "--nologo",
            "--configuration",
            configuration,
        )

    def build_cmake_build_argv(
        self,
        executable: Path,
        *,
        build_directory: Path,
        configuration: str,
    ) -> tuple[str, ...]:
        if configuration not in {"Debug", "Release"}:
            raise DesktopBoundaryError("CMake configuration is not allowlisted")
        exe = self.validate_executable(DesktopToolKind.CMAKE, executable)
        build_dir = self.validate_staging_path(build_directory)
        return (
            str(exe),
            "--build",
            str(build_dir),
            "--config",
            configuration,
            "--parallel",
            "2",
        )

    def build_cargo_argv(
        self,
        executable: Path,
        *,
        operation: str,
        manifest_path: Path,
        target_directory: Path,
    ) -> tuple[str, ...]:
        if operation not in {"check", "build", "test"}:
            raise DesktopBoundaryError("Cargo operation is not allowlisted")
        exe = self.validate_executable(DesktopToolKind.CARGO, executable)
        manifest = self.validate_project_file(
            manifest_path,
            suffixes=frozenset({".toml"}),
        )
        if manifest.name != "Cargo.toml":
            raise DesktopBoundaryError("Cargo manifest must be Cargo.toml")
        target = self.validate_staging_path(target_directory)
        return (
            str(exe),
            operation,
            "--locked",
            "--offline",
            "--manifest-path",
            str(manifest),
            "--target-dir",
            str(target),
        )
