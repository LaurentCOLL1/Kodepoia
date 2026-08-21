from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Iterable

from kodepoia.kodecode.dap import DapTool, DebugAdapterSpec
from kodepoia.kodecode.files import FileTool
from kodepoia.kodecode.git_worktree import GitWorktreeTool
from kodepoia.kodecode.lsp import LanguageServerSpec, LspTool
from kodepoia.kodecode.parser_tool import ParserTool
from kodepoia.kodecode.patch import PatchTool
from kodepoia.kodecode.search import SearchTool
from kodepoia.kodecode.workspace import WorkspaceBoundary


class KodeCodeToolAPI:
    """Explicit structured tool boundary for code/repository access."""

    def __init__(
        self,
        root: Path,
        *,
        language_servers: Iterable[LanguageServerSpec] = (),
        debug_adapters: Iterable[DebugAdapterSpec] = (),
    ) -> None:
        self.boundary = WorkspaceBoundary(root)
        self.files = FileTool(self.boundary)
        self.search_tool = SearchTool(self.boundary)
        self.patch = PatchTool(self.boundary)
        self.worktrees = GitWorktreeTool(self.boundary)
        self.parser = ParserTool(self.boundary)
        self.lsp = LspTool(self.boundary, language_servers)
        self.dap = DapTool(self.boundary, debug_adapters)
        self._dispatch: dict[str, Callable[[dict[str, Any]], Any]] = {
            "kodecode_files_list": self._files_list,
            "kodecode_files_read": self._files_read,
            "kodecode_search": self._search,
            "kodecode_patch_replace_once": self._patch_replace_once,
            "kodecode_git_worktree_list": self._worktree_list,
            "kodecode_git_worktree_add": self._worktree_add,
            "kodecode_git_worktree_remove": self._worktree_remove,
            "kodecode_parser_capabilities": self._parser_capabilities,
            "kodecode_parser_parse": self._parser_parse,
            "kodecode_lsp_capabilities": self._lsp_capabilities,
            "kodecode_lsp_start": self._lsp_start,
            "kodecode_lsp_stop": self._lsp_stop,
            "kodecode_lsp_symbols": self._lsp_symbols,
            "kodecode_lsp_definition": self._lsp_definition,
            "kodecode_lsp_references": self._lsp_references,
            "kodecode_lsp_diagnostics": self._lsp_diagnostics,
            "kodecode_dap_capabilities": self._dap_capabilities,
            "kodecode_dap_start": self._dap_start,
            "kodecode_dap_configure": self._dap_configure,
            "kodecode_dap_configuration_done": self._dap_configuration_done,
            "kodecode_dap_set_breakpoints": self._dap_set_breakpoints,
            "kodecode_dap_threads": self._dap_threads,
            "kodecode_dap_stack": self._dap_stack,
            "kodecode_dap_scopes": self._dap_scopes,
            "kodecode_dap_variables": self._dap_variables,
            "kodecode_dap_stop": self._dap_stop,
        }

    def invoke(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        handler = self._dispatch.get(tool_name)
        if handler is None:
            raise KeyError(f"Unknown KodeCode tool: {tool_name}")
        return handler(dict(arguments or {}))

    def catalog(self) -> list[dict[str, Any]]:
        return [
            self._schema(
                "kodecode_files_list", "List workspace files",
                {"path": {"type": "string"}, "recursive": {"type": "boolean"}},
            ),
            self._schema(
                "kodecode_files_read", "Read a UTF-8 workspace file",
                {"path": {"type": "string"}}, ["path"],
            ),
            self._schema(
                "kodecode_search", "Search workspace text",
                {
                    "query": {"type": "string"},
                    "paths": {"type": "array", "items": {"type": "string"}},
                    "regex": {"type": "boolean"},
                    "case_sensitive": {"type": "boolean"},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 2000},
                }, ["query"],
            ),
            self._schema(
                "kodecode_patch_replace_once",
                "Atomically replace one exact text occurrence with a SHA-256 precondition",
                {
                    "path": {"type": "string"},
                    "old_text": {"type": "string"},
                    "new_text": {"type": "string"},
                    "expected_sha256": {"type": ["string", "null"]},
                }, ["path", "old_text", "new_text"],
            ),
            self._schema("kodecode_git_worktree_list", "List Git worktrees", {}),
            self._schema(
                "kodecode_git_worktree_add", "Create a managed linked Git worktree",
                {
                    "name": {"type": "string"},
                    "branch": {"type": ["string", "null"]},
                    "start_point": {"type": "string"},
                    "detach": {"type": "boolean"},
                }, ["name"],
            ),
            self._schema(
                "kodecode_git_worktree_remove", "Remove a clean managed linked Git worktree",
                {"name": {"type": "string"}}, ["name"],
            ),
            self._schema(
                "kodecode_parser_capabilities",
                "Report installed Tree-sitter grammar capabilities and ABI compatibility", {},
            ),
            self._schema(
                "kodecode_parser_parse", "Parse a workspace source file with Tree-sitter",
                {
                    "path": {"type": "string"},
                    "language": {"type": ["string", "null"]},
                    "max_nodes": {"type": "integer", "minimum": 1, "maximum": 2000},
                }, ["path"],
            ),
            self._schema("kodecode_lsp_capabilities", "List configured/running LSP servers", {}),
            self._schema(
                "kodecode_lsp_start", "Start one explicitly registered language server",
                {"server_id": {"type": "string"}}, ["server_id"],
            ),
            self._schema(
                "kodecode_lsp_stop", "Gracefully stop one running language server",
                {"server_id": {"type": "string"}}, ["server_id"],
            ),
            self._schema(
                "kodecode_lsp_symbols", "Request document symbols from a running language server",
                {"server_id": {"type": "string"}, "path": {"type": "string"}},
                ["server_id", "path"],
            ),
            self._position_schema("kodecode_lsp_definition", "Request go-to-definition"),
            self._position_schema(
                "kodecode_lsp_references", "Request references",
                extra={"include_declaration": {"type": "boolean"}},
            ),
            self._schema(
                "kodecode_lsp_diagnostics", "Return captured diagnostics for a workspace document",
                {"server_id": {"type": "string"}, "path": {"type": "string"}},
                ["server_id", "path"],
            ),
            self._schema("kodecode_dap_capabilities", "List registered debug adapters/configurations", {}),
            self._schema(
                "kodecode_dap_start", "Start one explicitly registered debug adapter",
                {"adapter_id": {"type": "string"}}, ["adapter_id"],
            ),
            self._schema(
                "kodecode_dap_configure", "Start a pre-registered launch/attach configuration",
                {"adapter_id": {"type": "string"}, "config_id": {"type": "string"}},
                ["adapter_id", "config_id"],
            ),
            self._schema(
                "kodecode_dap_configuration_done", "Notify adapter that breakpoint configuration is done",
                {"adapter_id": {"type": "string"}}, ["adapter_id"],
            ),
            self._schema(
                "kodecode_dap_set_breakpoints", "Set source breakpoints in a workspace file",
                {
                    "adapter_id": {"type": "string"},
                    "path": {"type": "string"},
                    "lines": {
                        "type": "array", "minItems": 1, "maxItems": 500,
                        "items": {"type": "integer", "minimum": 1},
                    },
                }, ["adapter_id", "path", "lines"],
            ),
            self._schema(
                "kodecode_dap_threads", "List debugger threads",
                {"adapter_id": {"type": "string"}}, ["adapter_id"],
            ),
            self._schema(
                "kodecode_dap_stack", "Get a debugger stack trace",
                {"adapter_id": {"type": "string"}, "thread_id": {"type": "integer", "minimum": 0}},
                ["adapter_id", "thread_id"],
            ),
            self._schema(
                "kodecode_dap_scopes", "Get scopes for a stack frame",
                {"adapter_id": {"type": "string"}, "frame_id": {"type": "integer", "minimum": 0}},
                ["adapter_id", "frame_id"],
            ),
            self._schema(
                "kodecode_dap_variables", "Get variables for a DAP variablesReference",
                {
                    "adapter_id": {"type": "string"},
                    "variables_reference": {"type": "integer", "minimum": 1},
                }, ["adapter_id", "variables_reference"],
            ),
            self._schema(
                "kodecode_dap_stop", "Disconnect a running debug adapter",
                {"adapter_id": {"type": "string"}, "terminate_debuggee": {"type": "boolean"}},
                ["adapter_id"],
            ),
        ]

    @staticmethod
    def _schema(
        name: str, description: str, properties: dict[str, Any],
        required: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object", "properties": properties,
                    "required": required or [], "additionalProperties": False,
                },
            },
        }

    @classmethod
    def _position_schema(
        cls, name: str, description: str, *, extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        properties: dict[str, Any] = {
            "server_id": {"type": "string"}, "path": {"type": "string"},
            "line": {"type": "integer", "minimum": 0},
            "character": {"type": "integer", "minimum": 0},
        }
        properties.update(extra or {})
        return cls._schema(name, description, properties, ["server_id", "path", "line", "character"])

    def _files_list(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        return [asdict(item) for item in self.files.list_entries(
            str(args.get("path", ".")), recursive=bool(args.get("recursive", False))
        )]

    def _files_read(self, args: dict[str, Any]) -> dict[str, str]:
        path = str(args["path"])
        return {"path": path, "content": self.files.read_text(path)}

    def _search(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        return [asdict(item) for item in self.search_tool.search(
            str(args["query"]), paths=[str(item) for item in args.get("paths", ["."])],
            regex=bool(args.get("regex", False)), case_sensitive=bool(args.get("case_sensitive", True)),
            max_results=int(args.get("max_results", 200)),
        )]

    def _patch_replace_once(self, args: dict[str, Any]) -> dict[str, Any]:
        expected = args.get("expected_sha256")
        return asdict(self.patch.replace_once(
            str(args["path"]), old_text=str(args["old_text"]), new_text=str(args["new_text"]),
            expected_sha256=str(expected) if expected is not None else None,
        ))

    def _worktree_list(self, _args: dict[str, Any]) -> list[dict[str, Any]]:
        return [asdict(item) for item in self.worktrees.list()]

    def _worktree_add(self, args: dict[str, Any]) -> dict[str, Any]:
        branch = args.get("branch")
        return asdict(self.worktrees.add(
            str(args["name"]), branch=str(branch) if branch is not None else None,
            start_point=str(args.get("start_point", "HEAD")), detach=bool(args.get("detach", False)),
        ))

    def _worktree_remove(self, args: dict[str, Any]) -> dict[str, bool]:
        self.worktrees.remove(str(args["name"]))
        return {"removed": True}

    def _parser_capabilities(self, _args: dict[str, Any]) -> list[dict[str, Any]]:
        return self.parser.capabilities()

    def _parser_parse(self, args: dict[str, Any]) -> dict[str, Any]:
        language = args.get("language")
        return self.parser.parse_file(
            str(args["path"]), language=str(language) if language is not None else None,
            max_nodes=int(args.get("max_nodes", 200)),
        )

    def _lsp_capabilities(self, _args: dict[str, Any]) -> list[dict[str, Any]]:
        return self.lsp.capabilities()

    def _lsp_start(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.lsp.start(str(args["server_id"]))

    def _lsp_stop(self, args: dict[str, Any]) -> dict[str, bool]:
        return self.lsp.stop(str(args["server_id"]))

    def _lsp_symbols(self, args: dict[str, Any]) -> Any:
        return self.lsp.symbols(str(args["server_id"]), str(args["path"]))

    def _lsp_definition(self, args: dict[str, Any]) -> Any:
        return self.lsp.definition(
            str(args["server_id"]), str(args["path"]), int(args["line"]), int(args["character"])
        )

    def _lsp_references(self, args: dict[str, Any]) -> Any:
        return self.lsp.references(
            str(args["server_id"]), str(args["path"]), int(args["line"]), int(args["character"]),
            include_declaration=bool(args.get("include_declaration", True)),
        )

    def _lsp_diagnostics(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        return self.lsp.diagnostics(str(args["server_id"]), str(args["path"]))

    def _dap_capabilities(self, _args: dict[str, Any]) -> list[dict[str, Any]]:
        return self.dap.capabilities()

    def _dap_start(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.dap.start(str(args["adapter_id"]))

    def _dap_configure(self, args: dict[str, Any]) -> Any:
        return self.dap.configure(str(args["adapter_id"]), str(args["config_id"]))

    def _dap_configuration_done(self, args: dict[str, Any]) -> Any:
        return self.dap.configuration_done(str(args["adapter_id"]))

    def _dap_set_breakpoints(self, args: dict[str, Any]) -> Any:
        lines = [int(value) for value in args["lines"]]
        if not 1 <= len(lines) <= 500:
            raise ValueError("lines must contain between 1 and 500 breakpoints")
        return self.dap.set_breakpoints(str(args["adapter_id"]), str(args["path"]), lines)

    def _dap_threads(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        return self.dap.threads(str(args["adapter_id"]))

    def _dap_stack(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        return self.dap.stack(str(args["adapter_id"]), int(args["thread_id"]))

    def _dap_scopes(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        return self.dap.scopes(str(args["adapter_id"]), int(args["frame_id"]))

    def _dap_variables(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        return self.dap.variables(str(args["adapter_id"]), int(args["variables_reference"]))

    def _dap_stop(self, args: dict[str, Any]) -> dict[str, bool]:
        return self.dap.stop(
            str(args["adapter_id"]), terminate_debuggee=bool(args.get("terminate_debuggee", False))
        )
