from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from kodepoia.exceptions import PermissionDenied


class Capability(StrEnum):
    FILE_READ = "file.read"
    FILE_WRITE = "file.write"
    FILE_DELETE = "file.delete"
    PROCESS_EXECUTE = "process.execute"
    NETWORK = "network"
    SECRET_READ = "secret.read"
    SECRET_WRITE = "secret.write"
    INSTALL = "install"


@dataclass(frozen=True, slots=True)
class PermissionGrant:
    capability: Capability
    roots: tuple[Path, ...] = ()
    executables: tuple[str, ...] = ()

    def allows_path(self, path: Path) -> bool:
        if not self.roots:
            return True
        resolved = path.resolve(strict=False)
        for root in self.roots:
            candidate = root.resolve(strict=False)
            if resolved == candidate or candidate in resolved.parents:
                return True
        return False


@dataclass(slots=True)
class PermissionSet:
    grants: dict[Capability, PermissionGrant] = field(default_factory=dict)

    def grant(self, grant: PermissionGrant) -> None:
        self.grants[grant.capability] = grant

    def revoke(self, capability: Capability) -> None:
        self.grants.pop(capability, None)

    def require(self, capability: Capability, path: Path | None = None, executable: str | None = None) -> None:
        grant = self.grants.get(capability)
        if grant is None:
            raise PermissionDenied(f"Capability not granted: {capability}")
        if path is not None and not grant.allows_path(path):
            raise PermissionDenied(f"Path outside permitted roots: {path}")
        if executable is not None and grant.executables and executable.lower() not in {
            item.lower() for item in grant.executables
        }:
            raise PermissionDenied(f"Executable is not allowlisted: {executable}")
