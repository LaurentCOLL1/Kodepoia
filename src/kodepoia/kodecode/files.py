from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kodepoia.kodecode.workspace import WorkspaceBoundary


@dataclass(frozen=True, slots=True)
class FileEntry:
    path: str
    is_dir: bool
    size: int | None


class FileTool:
    """Read and enumerate files strictly inside a KodeCode workspace."""

    def __init__(self, boundary: WorkspaceBoundary, *, max_read_bytes: int = 2_000_000) -> None:
        self.boundary = boundary
        self.max_read_bytes = max_read_bytes

    def read_text(self, path: str, *, encoding: str = "utf-8") -> str:
        target = self.boundary.resolve(path, must_exist=True)
        if not target.is_file():
            raise IsADirectoryError(path)
        size = target.stat().st_size
        if size > self.max_read_bytes:
            raise ValueError(f"File exceeds read limit ({size} > {self.max_read_bytes} bytes): {path}")
        return target.read_text(encoding=encoding)

    def list_entries(
        self,
        path: str = ".",
        *,
        recursive: bool = False,
        max_entries: int = 2000,
    ) -> list[FileEntry]:
        root = self.boundary.resolve(path, must_exist=True)
        if not root.is_dir():
            raise NotADirectoryError(path)

        iterator = root.rglob("*") if recursive else root.iterdir()
        entries: list[FileEntry] = []
        for candidate in sorted(iterator, key=lambda item: item.as_posix().lower()):
            if len(entries) >= max_entries:
                raise ValueError(f"Entry limit exceeded ({max_entries})")
            is_dir = candidate.is_dir()
            entries.append(
                FileEntry(
                    path=self.boundary.relative(candidate),
                    is_dir=is_dir,
                    size=None if is_dir else candidate.stat().st_size,
                )
            )
        return entries
