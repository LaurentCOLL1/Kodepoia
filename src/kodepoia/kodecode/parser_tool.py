from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from kodepoia.kodecode.parsing import TreeSitterLanguageRegistry, TreeSitterParserService
from kodepoia.kodecode.workspace import WorkspaceBoundary


class ParserTool:
    """Workspace-scoped structured access to Tree-sitter capabilities and parsing."""

    def __init__(
        self,
        boundary: WorkspaceBoundary,
        *,
        registry: TreeSitterLanguageRegistry | None = None,
        max_parse_bytes: int = 2_000_000,
    ) -> None:
        if max_parse_bytes < 1:
            raise ValueError("max_parse_bytes must be positive")
        self.boundary = boundary
        self.registry = registry or TreeSitterLanguageRegistry()
        self.service = TreeSitterParserService(self.registry)
        self.max_parse_bytes = max_parse_bytes

    def capabilities(self) -> list[dict[str, Any]]:
        return [asdict(item) for item in self.registry.capabilities()]

    def parse_file(
        self,
        path: str,
        *,
        language: str | None = None,
        max_nodes: int = 200,
    ) -> dict[str, Any]:
        if not 1 <= max_nodes <= 2000:
            raise ValueError("max_nodes must be between 1 and 2000")

        target = self.boundary.resolve(path, must_exist=True)
        if not target.is_file():
            raise IsADirectoryError(path)
        size = target.stat().st_size
        if size > self.max_parse_bytes:
            raise ValueError(
                f"File exceeds parser limit ({size} > {self.max_parse_bytes} bytes): {path}"
            )

        selected_language = language or self.registry.detect_path(Path(path))
        if selected_language is None:
            raise ValueError(f"Cannot detect Tree-sitter language for: {path}")

        document = self.service.parse(target.read_bytes(), selected_language)
        summary = self.service.summarize(document, max_nodes=max_nodes)
        result = asdict(summary)
        result["path"] = self.boundary.relative(target)
        return result
