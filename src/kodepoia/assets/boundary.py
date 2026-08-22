from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from kodepoia.kodecode.workspace import WorkspaceBoundary, WorkspaceViolation


class VaultViolation(PermissionError):
    """Raised when a Vault operation attempts to escape its configured root."""


@dataclass(frozen=True, slots=True)
class VaultBoundary:
    """Confine Vault-managed relative paths beneath an explicit trusted root."""

    root: Path
    _boundary: WorkspaceBoundary = field(init=False, repr=False)

    def __post_init__(self) -> None:
        resolved_root = self.root.expanduser().resolve(strict=False)
        object.__setattr__(self, "root", resolved_root)
        object.__setattr__(self, "_boundary", WorkspaceBoundary(resolved_root))

    def resolve(self, user_path: str | Path = ".", *, must_exist: bool = False) -> Path:
        try:
            return self._boundary.resolve(user_path, must_exist=must_exist)
        except WorkspaceViolation as exc:
            raise VaultViolation(str(exc).replace("workspace", "vault")) from exc

    def relative(self, path: Path) -> str:
        try:
            return self._boundary.relative(path)
        except WorkspaceViolation as exc:
            raise VaultViolation(str(exc).replace("workspace", "vault")) from exc
