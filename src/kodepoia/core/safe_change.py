from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
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
            manifest.append(
                f"{relative.as_posix()} {self._hash(source) if source.is_file() else 'DIR'}"
            )
        (destination / "MANIFEST.txt").write_text(
            "\n".join(manifest), encoding="utf-8"
        )
        return destination

    def restore(
        self,
        snapshot: Path,
        *,
        paths: list[Path] | None = None,
    ) -> tuple[Path, ...]:
        """Restore integrity-verified snapshot files with bounded atomic writes.

        Directory-only snapshot entries are intentionally not restorable because
        they do not carry per-file digests. Restores never delete files that are
        absent from the snapshot.
        """
        snapshot_path = snapshot.resolve(strict=True)
        snapshot_root = self.snapshot_root.resolve(strict=True)
        if snapshot_path == snapshot_root or snapshot_root not in snapshot_path.parents:
            raise ValueError(f"Snapshot escapes snapshot root: {snapshot}")
        if not snapshot_path.is_dir():
            raise ValueError("Snapshot must be a directory")

        manifest_path = snapshot_path / "MANIFEST.txt"
        if not manifest_path.is_file():
            raise ValueError("Snapshot manifest is missing")
        entries = self._manifest_entries(manifest_path)

        if paths is None:
            selected = tuple(sorted(entries))
        else:
            requested: list[str] = []
            for path in paths:
                target = self.ensure_inside_project(path)
                requested.append(target.relative_to(self.project_root).as_posix())
            selected = tuple(dict.fromkeys(requested))

        prepared: list[tuple[Path, Path, bytes, int]] = []
        for relative in selected:
            digest = entries.get(relative)
            if digest is None:
                raise ValueError(f"Snapshot manifest has no entry for: {relative}")
            if digest == "DIR":
                raise ValueError(
                    f"Directory-only snapshot entry cannot be restored safely: {relative}"
                )
            source = (snapshot_path / Path(relative)).resolve(strict=True)
            if snapshot_path not in source.parents or not source.is_file():
                raise ValueError(f"Snapshot file is invalid: {relative}")
            if self._hash(source) != digest:
                raise ValueError(f"Snapshot integrity verification failed: {relative}")
            target = self.ensure_inside_project(self.project_root / Path(relative))
            prepared.append((source, target, source.read_bytes(), source.stat().st_mode))

        restored: list[Path] = []
        for _source, target, content, mode in prepared:
            target.parent.mkdir(parents=True, exist_ok=True)
            self._atomic_replace(target, content, mode)
            restored.append(target)
        return tuple(restored)

    @staticmethod
    def _manifest_entries(manifest_path: Path) -> dict[str, str]:
        entries: dict[str, str] = {}
        for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                relative, digest = line.rsplit(" ", 1)
            except ValueError as exc:
                raise ValueError("Malformed snapshot manifest entry") from exc
            relative_path = Path(relative)
            if (
                not relative
                or relative_path.is_absolute()
                or ".." in relative_path.parts
                or relative in entries
            ):
                raise ValueError(f"Unsafe snapshot manifest path: {relative!r}")
            if digest != "DIR" and (
                len(digest) != 64
                or any(char not in "0123456789abcdef" for char in digest.lower())
            ):
                raise ValueError(f"Invalid snapshot manifest digest: {relative}")
            entries[relative_path.as_posix()] = digest.lower() if digest != "DIR" else digest
        return entries

    @staticmethod
    def _atomic_replace(target: Path, content: bytes, mode: int) -> None:
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=target.parent,
                prefix=".kodepoia-restore-",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
                temporary = Path(handle.name)
            os.chmod(temporary, mode)
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    @staticmethod
    def _hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
