from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from kodepoia.kodecode.files import FileTool
from kodepoia.kodecode.git_worktree import GitWorktreeTool
from kodepoia.kodecode.patch import PatchTool
from kodepoia.kodecode.search import SearchTool
from kodepoia.kodecode.workspace import WorkspaceBoundary


class KodeCodeToolAPI:
    """Explicit structured tool boundary for code/repository access.

    Agents invoke named operations with dictionaries. The catalog is intentionally
    small and explicit: no arbitrary filesystem path access and no arbitrary
    command execution are exposed here.
    """

    def __init__(self, root: Path) -> None:
        self.boundary = WorkspaceBoundary(root)
        self.files = FileTool(self.boundary)
        self.search_tool = SearchTool(self.boundary)
        self.patch = PatchTool(self.boundary)
        self.worktrees = GitWorktreeTool(self.boundary)
        self._dispatch: dict[str, Callable[[dict[str, Any]], Any]] = {
            "code.files.list": self._files_list,
            "code.files.read": self._files_read,
            "code.search": self._search,
            "code.patch.replace_once": self._patch_replace_once,
            "code.git.worktree.list": self._worktree_list,
            "code.git.worktree.add": self._worktree_add,
            "code.git.worktree.remove": self._worktree_remove,
        }

    def invoke(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        handler = self._dispatch.get(tool_name)
        if handler is None:
            raise KeyError(f"Unknown KodeCode tool: {tool_name}")
        return handler(dict(arguments or {}))

    def catalog(self) -> list[dict[str, Any]]:
        """Return Ollama-compatible function schemas for the R4.1 tool surface."""

        return [
            self._schema("code.files.list", "List workspace files", {"path": {"type": "string"}, "recursive": {"type": "boolean"}}),
            self._schema("code.files.read", "Read a UTF-8 workspace file", {"path": {"type": "string"}}, ["path"]),
            self._schema(
                "code.search",
                "Search workspace text",
                {
                    "query": {"type": "string"},
                    "paths": {"type": "array", "items": {"type": "string"}},
                    "regex": {"type": "boolean"},
                    "case_sensitive": {"type": "boolean"},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 2000},
                },
                ["query"],
            ),
            self._schema(
                "code.patch.replace_once",
                "Atomically replace one exact text occurrence with an optional SHA-256 precondition",
                {
                    "path": {"type": "string"},
                    "old_text": {"type": "string"},
                    "new_text": {"type": "string"},
                    "expected_sha256": {"type": ["string", "null"]},
                },
                ["path", "old_text", "new_text"],
            ),
            self._schema("code.git.worktree.list", "List Git worktrees using porcelain output", {}),
            self._schema(
                "code.git.worktree.add",
                "Create a managed linked Git worktree",
                {
                    "name": {"type": "string"},
                    "branch": {"type": ["string", "null"]},
                    "start_point": {"type": "string"},
                    "detach": {"type": "boolean"},
                },
                ["name"],
            ),
            self._schema(
                "code.git.worktree.remove",
                "Remove a clean managed linked Git worktree",
                {"name": {"type": "string"}},
                ["name"],
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

    def _files_list(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        entries = self.files.list_entries(
            str(args.get("path", ".")),
            recursive=bool(args.get("recursive", False)),
        )
        return [asdict(item) for item in entries]

    def _files_read(self, args: dict[str, Any]) -> dict[str, str]:
        path = str(args["path"])
        return {"path": path, "content": self.files.read_text(path)}

    def _search(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        matches = self.search_tool.search(
            str(args["query"]),
            paths=[str(item) for item in args.get("paths", ["."])],
            regex=bool(args.get("regex", False)),
            case_sensitive=bool(args.get("case_sensitive", True)),
            max_results=int(args.get("max_results", 200)),
        )
        return [asdict(item) for item in matches]

    def _patch_replace_once(self, args: dict[str, Any]) -> dict[str, Any]:
        return asdict(
            self.patch.replace_once(
                str(args["path"]),
                old_text=str(args["old_text"]),
                new_text=str(args["new_text"]),
                expected_sha256=str(args["expected_sha256"]) if args.get("expected_sha256") is not None else None,
            )
        )

    def _worktree_list(self, _args: dict[str, Any]) -> list[dict[str, Any]]:
        return [asdict(item) for item in self.worktrees.list()]

    def _worktree_add(self, args: dict[str, Any]) -> dict[str, Any]:
        return asdict(
            self.worktrees.add(
                str(args["name"]),
                branch=str(args["branch"]) if args.get("branch") is not None else None,
                start_point=str(args.get("start_point", "HEAD")),
                detach=bool(args.get("detach", False)),
            )
        )

    def _worktree_remove(self, args: dict[str, Any]) -> dict[str, bool]:
        self.worktrees.remove(str(args["name"]))
        return {"removed": True}
