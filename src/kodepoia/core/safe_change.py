from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .guardian import KodeGuardian
from .types import ActionKind, ActionRequest


@dataclass(frozen=True, slots=True)
class ChangeOperation:
    action: str
    path: Path
    content: bytes | None = None


@dataclass(frozen=True, slots=True)
class ChangePlan:
    project_root: Path
    operations: tuple[ChangeOperation, ...]

    @property
    def destructive_count(self) -> int:
        return sum(1 for op in self.operations if op.action == "delete")


class SafeChangeManager:
    """Applies atomic file changes behind KodeGuardian with pre-image protection."""

    def __init__(self, guardian: KodeGuardian, backup_root: Path) -> None:
        self.guardian = guardian
        self.backup_root = backup_root

    def plan_write(self, project_root: Path, path: Path, content: str | bytes) -> ChangePlan:
        payload = content.encode("utf-8") if isinstance(content, str) else content
        return ChangePlan(project_root.resolve(), (ChangeOperation("write", path.resolve(), payload),))

    def plan_delete(self, project_root: Path, paths: Iterable[Path]) -> ChangePlan:
        return ChangePlan(project_root.resolve(), tuple(ChangeOperation("delete", p.resolve()) for p in paths))

    def describe(self, plan: ChangePlan) -> dict[str, object]:
        return {"project_root": str(plan.project_root), "operations": [{"action": op.action, "path": str(op.path), "size": len(op.content) if op.content is not None else None} for op in plan.operations], "destructive_count": plan.destructive_count}

    def apply(self, plan: ChangePlan, *, actor: str, confirmed: bool = False) -> list[Path]:
        changed: list[Path] = []
        snapshot_dir = self._snapshot_dir(plan)
        for op in plan.operations:
            kind = ActionKind.FILE_WRITE if op.action == "write" else ActionKind.FILE_DELETE
            request = ActionRequest(kind, actor, plan.project_root, str(op.path), {"batch_delete_count": plan.destructive_count})
            decision = self.guardian.require_allowed(request, confirmed=confirmed)
            self._ensure_inside(plan.project_root, op.path)
            if decision.requires_snapshot and op.path.exists():
                self._copy_preimage(plan.project_root, op.path, snapshot_dir)
            if op.action == "write":
                self._atomic_write(op.path, op.content or b"")
            elif op.action == "delete":
                if op.path.is_dir():
                    shutil.rmtree(op.path)
                elif op.path.exists():
                    op.path.unlink()
            else:
                raise ValueError(f"unsupported operation: {op.action}")
            changed.append(op.path)
        return changed

    def _snapshot_dir(self, plan: ChangePlan) -> Path:
        digest = hashlib.sha256(json.dumps(self.describe(plan), sort_keys=True).encode()).hexdigest()[:12]
        path = self.backup_root / f"safe-change-{digest}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _ensure_inside(root: Path, path: Path) -> None:
        if path != root and not path.is_relative_to(root):
            raise PermissionError(f"path escapes project root: {path}")

    @staticmethod
    def _copy_preimage(root: Path, path: Path, snapshot_dir: Path) -> None:
        destination = snapshot_dir / path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            shutil.copytree(path, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(path, destination)

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, path)
        except BaseException:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise
