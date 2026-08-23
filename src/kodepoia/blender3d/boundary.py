from __future__ import annotations

import os
import platform
from collections.abc import Iterable, Mapping
from pathlib import Path

from .errors import BlenderBoundaryError

_ALLOWED_EXECUTABLE_NAMES = frozenset({"blender", "blender.exe"})
_ALLOWED_ENVIRONMENT_KEYS = frozenset({"KODEPOIA_RUN_ID", "TEMP", "TMP"})
_FORBIDDEN_ENVIRONMENT_KEYS = frozenset(
    {
        "PYTHONPATH",
        "PYTHONHOME",
        "BLENDER_USER_SCRIPTS",
        "BLENDER_SYSTEM_SCRIPTS",
        "BLENDER_SYSTEM_EXTENSIONS",
        "BLENDER_SYSTEM_PYTHON",
    }
)


def _is_within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def default_known_candidates() -> tuple[Path, ...]:
    system = platform.system().lower()
    candidates: list[Path] = []
    if system == "windows":
        for variable in ("ProgramFiles", "ProgramW6432"):
            value = os.environ.get(variable)
            if value:
                candidates.append(Path(value) / "Blender Foundation" / "Blender 5.2" / "blender.exe")
    elif system == "darwin":
        candidates.append(Path("/Applications/Blender.app/Contents/MacOS/Blender"))
    else:
        candidates.extend((Path("/usr/bin/blender"), Path("/usr/local/bin/blender"), Path("/snap/bin/blender")))
    return tuple(dict.fromkeys(candidates))


def default_known_roots() -> tuple[Path, ...]:
    return tuple(dict.fromkeys(candidate.parent.resolve(strict=False) for candidate in default_known_candidates()))


class BlenderExecutableBoundary:
    """Finite Blender executable/script boundary. This class never launches Blender."""

    def __init__(self, *, allowed_roots: Iterable[Path], staging_root: Path) -> None:
        roots = tuple(Path(root).resolve(strict=False) for root in allowed_roots)
        if not roots:
            raise ValueError("At least one Blender executable root must be configured")
        self.allowed_roots = roots
        self.staging_root = Path(staging_root).resolve(strict=False)

    def validate_candidate(self, candidate: Path) -> Path:
        try:
            resolved = Path(candidate).resolve(strict=True)
        except OSError as exc:
            raise BlenderBoundaryError(f"Blender executable is unavailable: {candidate}") from exc
        if not resolved.is_file():
            raise BlenderBoundaryError(f"Blender executable is not a regular file: {resolved}")
        if resolved.name.lower() not in _ALLOWED_EXECUTABLE_NAMES:
            raise BlenderBoundaryError(f"Unexpected Blender executable name: {resolved.name}")
        if not any(_is_within(resolved, root) for root in self.allowed_roots):
            raise BlenderBoundaryError(f"Blender executable escapes configured roots: {resolved}")
        return resolved

    def discover(self, explicit_candidates: Iterable[Path] = ()) -> tuple[Path, ...]:
        accepted: list[Path] = []
        seen: set[Path] = set()
        for candidate in tuple(explicit_candidates) + default_known_candidates():
            unresolved = Path(candidate)
            if unresolved in seen or not unresolved.exists():
                continue
            seen.add(unresolved)
            try:
                resolved = self.validate_candidate(unresolved)
            except BlenderBoundaryError:
                if unresolved in tuple(explicit_candidates):
                    raise
                continue
            if resolved not in accepted:
                accepted.append(resolved)
        return tuple(accepted)

    def validate_job_script(self, script: Path) -> Path:
        try:
            resolved = Path(script).resolve(strict=True)
        except OSError as exc:
            raise BlenderBoundaryError(f"Kodepoia Blender job script is unavailable: {script}") from exc
        if not resolved.is_file() or resolved.suffix.lower() != ".py":
            raise BlenderBoundaryError("Kodepoia Blender job script must be a regular .py file")
        if not _is_within(resolved, self.staging_root):
            raise BlenderBoundaryError(f"Kodepoia Blender job script escapes staging root: {resolved}")
        return resolved

    def build_job_argv(self, executable: Path, script: Path) -> tuple[str, ...]:
        blender = self.validate_candidate(executable)
        job_script = self.validate_job_script(script)
        return (
            str(blender),
            "--background",
            "--factory-startup",
            "--disable-autoexec",
            "--offline-mode",
            "--python-exit-code",
            "17",
            "--python",
            str(job_script),
        )


def validate_environment_overrides(overrides: Mapping[str, str] | None) -> dict[str, str]:
    if not overrides:
        return {}
    clean: dict[str, str] = {}
    for key, value in overrides.items():
        normalized = str(key).upper()
        if normalized in _FORBIDDEN_ENVIRONMENT_KEYS or normalized not in _ALLOWED_ENVIRONMENT_KEYS:
            raise BlenderBoundaryError(f"Blender environment override is not allowlisted: {key}")
        clean[normalized] = str(value)
    return clean
