from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from kodepoia.kodecode.workspace import WorkspaceBoundary, WorkspaceViolation


@dataclass(frozen=True, slots=True)
class SearchMatch:
    path: str
    line: int
    column: int
    text: str


class SearchTool:
    """Deterministic text search over workspace files.

    Generated/cache directories are skipped by default. Binary/non-UTF-8 files
    are ignored rather than decoded lossy.
    """

    DEFAULT_EXCLUDED_PARTS = frozenset(
        {".git", ".venv", "venv", "node_modules", ".godot", ".import", "__pycache__"}
    )

    def __init__(self, boundary: WorkspaceBoundary) -> None:
        self.boundary = boundary

    def search(
        self,
        query: str,
        *,
        paths: list[str] | None = None,
        regex: bool = False,
        case_sensitive: bool = True,
        max_results: int = 200,
    ) -> list[SearchMatch]:
        if not query:
            raise ValueError("query cannot be empty")
        if max_results < 1:
            raise ValueError("max_results must be positive")

        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(query if regex else re.escape(query), flags)
        roots = [self.boundary.resolve(item, must_exist=True) for item in (paths or ["."])]
        matches: list[SearchMatch] = []

        for root in roots:
            candidates = [root] if root.is_file() else sorted(root.rglob("*"), key=lambda p: p.as_posix())
            for candidate in candidates:
                if not candidate.is_file() or self._excluded(candidate):
                    continue
                try:
                    relative = self.boundary.relative(candidate)
                    content = candidate.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError, WorkspaceViolation):
                    continue

                for line_number, line in enumerate(content.splitlines(), start=1):
                    for found in pattern.finditer(line):
                        matches.append(
                            SearchMatch(
                                path=relative,
                                line=line_number,
                                column=found.start() + 1,
                                text=line,
                            )
                        )
                        if len(matches) >= max_results:
                            return matches
        return matches

    def _excluded(self, candidate: Path) -> bool:
        try:
            relative = candidate.resolve(strict=False).relative_to(self.boundary.root)
        except ValueError:
            return True
        parts = set(relative.parts)
        if parts & self.DEFAULT_EXCLUDED_PARTS:
            return True
        return len(relative.parts) >= 2 and relative.parts[0] == ".kodepoia" and relative.parts[1] in {
            "benchmarks",
            "worktrees",
        }
