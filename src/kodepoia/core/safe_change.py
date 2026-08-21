from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ChangeItem:
    operation: str
    path: Path


@dataclass(frozen=True, slots=True)
class ChangePlan:
    items: tuple[ChangeItem, ...]

    @property
    def destructive_count(self) -> int:
        return sum(item.operation in {"delete", "replace"} for item in self.items)


class SafeChangeManager:
    def __init__(self, project_root: Path, snapshot_root: Path) -> None:
        self.project_root = project_root.resolve(strict=False)
        self.snapshot_root = snapshot_root.resolve(strict=False)
        self.snapshot_root.mkdir(parents=True, exist_ok=True)

    def ensure_inside_project(self, path: Path) -> Path:
        resolved = path.resolve(strict=False)
        if resolved != self.project_root and self.project_root not in resolved.parents:
            raise ValueError(f"Path escapes project root: {path}")
        return resolved

    def snapshot(self, paths: list[Path]) -> Path:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        destination = self.snapshot_root / stamp
        destination.mkdir(parents=True, exist_ok=False)
        manifest: list[str] = []
        for path in paths:
            source = self.ensure_inside_project(path)
            if not source.exists():
                continue
            relative = source.relative_to(self.project_root)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
            manifest.append(f"{relative.as_posix()} {self._hash(source) if source.is_file() else 'DIR'}")
        (destination / "MANIFEST.txt").write_text("\n".join(manifest), encoding="utf-8")
        return destination

    @staticmethod
    def _hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
