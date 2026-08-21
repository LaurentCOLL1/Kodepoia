from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class WorkspaceViolation(PermissionError):
    """Raised when a KodeCode operation attempts to escape its workspace root."""


@dataclass(frozen=True, slots=True)
class WorkspaceBoundary:
    """Resolve user-provided relative paths without allowing workspace escape.

    Absolute paths are rejected. Existing symlinks are resolved before the
    containment check, so a symlink inside the workspace cannot be used to
    access a target outside the workspace. Confinement is checked before any
    strict existence resolution, so escaped missing paths cannot leak a
    FileNotFoundError in place of a workspace-policy denial.
    """

    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", self.root.resolve(strict=False))

    def _require_inside(self, candidate: Path, user_path: str | Path) -> Path:
        if candidate != self.root and self.root not in candidate.parents:
            raise WorkspaceViolation(f"Path escapes workspace: {user_path}")
        return candidate

    def resolve(self, user_path: str | Path = ".", *, must_exist: bool = False) -> Path:
        raw = Path(user_path)
        if raw.is_absolute():
            raise WorkspaceViolation(f"Absolute paths are not allowed: {raw}")

        non_strict = (self.root / raw).resolve(strict=False)
        self._require_inside(non_strict, user_path)
        if not must_exist:
            return non_strict

        strict = (self.root / raw).resolve(strict=True)
        return self._require_inside(strict, user_path)

    def relative(self, path: Path) -> str:
        resolved = path.resolve(strict=False)
        self._require_inside(resolved, path)
        relative = resolved.relative_to(self.root)
        return "." if relative == Path(".") else relative.as_posix()
