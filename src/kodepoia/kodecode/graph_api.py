from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from kodepoia.kodecode.graphs import GraphTool
from kodepoia.kodecode.workspace import WorkspaceBoundary


class GraphToolAPI:
    """Bounded structured tool surface for KodeCode intelligence graphs."""

    def __init__(self, root: Path) -> None:
        self.boundary = WorkspaceBoundary(root)
        self.graphs = GraphTool(self.boundary)
        self._dispatch: dict[str, Callable[[dict[str, Any]], Any]] = {
            "kodecode_graph_refresh": self._refresh,
            "kodecode_graph_symbols": self._symbols,
            "kodecode_graph_calls": self._calls,
            "kodecode_graph_dependencies": self._dependencies,
        }

    def invoke(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        handler = self._dispatch.get(tool_name)
        if handler is None:
            raise KeyError(f"Unknown KodeCode graph tool: {tool_name}")
        return handler(dict(arguments or {}))

    def catalog(self) -> list[dict[str, Any]]:
        return [
            self._schema(
                "kodecode_graph_refresh",
                "Incrementally refresh symbol/call/dependency graphs for workspace source files",
                {
                    "paths": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 200,
                        "items": {"type": "string"},
                    }
                },
                ["paths"],
            ),
            self._query_schema(
                "kodecode_graph_symbols",
                "Query indexed code symbols with stable IDs and source provenance",
                include_name=True,
            ),
            self._query_schema(
                "kodecode_graph_calls",
                "Query indexed call edges, including unresolved/ambiguous targets",
                include_name=True,
            ),
            self._query_schema(
                "kodecode_graph_dependencies",
                "Query indexed import/dependency edges",
                include_name=True,
            ),
        ]

    @staticmethod
    def _schema(
        name: str,
        description: str,
        properties: dict[str, Any],
        required: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required or [],
                    "additionalProperties": False,
                },
            },
        }

    @classmethod
    def _query_schema(cls, name: str, description: str, *, include_name: bool) -> dict[str, Any]:
        properties: dict[str, Any] = {
            "path": {"type": ["string", "null"]},
            "max_results": {"type": "integer", "minimum": 1, "maximum": 500},
        }
        if include_name:
            properties["name"] = {"type": ["string", "null"]}
        return cls._schema(name, description, properties)

    def _refresh(self, args: dict[str, Any]) -> dict[str, Any]:
        paths = [str(item) for item in args["paths"]]
        if not 1 <= len(paths) <= 200:
            raise ValueError("paths must contain between 1 and 200 files")
        return self.graphs.refresh(paths)

    @staticmethod
    def _bounded(value: Any) -> int:
        limit = int(value if value is not None else 200)
        if not 1 <= limit <= 500:
            raise ValueError("max_results must be between 1 and 500")
        return limit

    def _symbols(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        snapshot = self.graphs.index.snapshot()
        path = args.get("path")
        name = args.get("name")
        limit = self._bounded(args.get("max_results"))
        result = []
        for item in snapshot.symbols:
            if path is not None and item.path != str(path):
                continue
            if name is not None and str(name).lower() not in item.name.lower():
                continue
            result.append(asdict(item))
            if len(result) >= limit:
                break
        return result

    def _calls(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        snapshot = self.graphs.index.snapshot()
        path = args.get("path")
        name = args.get("name")
        limit = self._bounded(args.get("max_results"))
        result = []
        for item in snapshot.calls:
            if path is not None and item.path != str(path):
                continue
            if name is not None and str(name).lower() not in item.target_name.lower():
                continue
            result.append(asdict(item))
            if len(result) >= limit:
                break
        return result

    def _dependencies(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        snapshot = self.graphs.index.snapshot()
        path = args.get("path")
        name = args.get("name")
        limit = self._bounded(args.get("max_results"))
        result = []
        for item in snapshot.dependencies:
            if path is not None and item.path != str(path):
                continue
            if name is not None and str(name).lower() not in item.module.lower():
                continue
            result.append(asdict(item))
            if len(result) >= limit:
                break
        return result
