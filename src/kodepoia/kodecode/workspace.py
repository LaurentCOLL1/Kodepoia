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
    access a target outside the workspace.
    """

    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", self.root.resolve(strict=False))

    def resolve(self, user_path: str | Path = ".", *, must_exist: bool = False) -> Path:
        raw = Path(user_path)
        if raw.is_absolute():
            raise WorkspaceViolation(f"Absolute paths are not allowed: {raw}")

        candidate = (self.root / raw).resolve(strict=must_exist)
        if candidate != self.root and self.root not in candidate.parents:
            raise WorkspaceViolation(f"Path escapes workspace: {user_path}")
        return candidate

    def relative(self, path: Path) -> str:
        resolved = path.resolve(strict=False)
        if resolved != self.root and self.root not in resolved.parents:
            raise WorkspaceViolation(f"Path escapes workspace: {path}")
        relative = resolved.relative_to(self.root)
        return "." if relative == Path(".") else relative.as_posix()
