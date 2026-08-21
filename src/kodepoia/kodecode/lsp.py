from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from kodepoia.core.sandbox import ManagedProcess, ProcessSandbox
from kodepoia.kodecode.protocol import ContentLengthJsonStream, FramedMessageChannel
from kodepoia.kodecode.workspace import WorkspaceBoundary

_SERVER_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class LspError(RuntimeError):
    """Base error for Language Server Protocol operations."""


class LspRpcError(LspError):
    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(f"LSP error {code}: {message}")
        self.code = code
        self.data = data


@dataclass(frozen=True, slots=True)
class LanguageServerSpec:
    server_id: str
    language_id: str
    argv: tuple[str, ...]
    cwd: str = "."
    env: Mapping[str, str] = field(default_factory=dict)
    initialization_options: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not _SERVER_ID.fullmatch(self.server_id):
            raise ValueError(f"Invalid language server id: {self.server_id}")
        if not self.language_id.strip():
            raise ValueError("language_id cannot be empty")
        if not self.argv or not self.argv[0].strip():
            raise ValueError("Language server argv cannot be empty")
        if any("\x00" in item for item in self.argv):
            raise ValueError("Language server argv cannot contain NUL bytes")


@dataclass(frozen=True, slots=True)
class LanguageServerCapability:
    server_id: str
    language_id: str
    executable: str
    running: bool
    initialized: bool
    server_capabilities: Mapping[str, Any] | None = None


class LanguageServerRegistry:
    def __init__(self, specs: Iterable[LanguageServerSpec] = ()) -> None:
        self._specs: dict[str, LanguageServerSpec] = {}
        for spec in specs:
            self.register(spec)

    def register(self, spec: LanguageServerSpec) -> None:
        if spec.server_id in self._specs:
            raise ValueError(f"Duplicate language server id: {spec.server_id}")
        self._specs[spec.server_id] = spec

    def get(self, server_id: str) -> LanguageServerSpec:
        try:
            return self._specs[server_id]
        except KeyError as exc:
            raise KeyError(f"Unknown language server: {server_id}") from exc

    def specs(self) -> tuple[LanguageServerSpec, ...]:
        return tuple(self._specs.values())


class LspSession:
    """Synchronous LSP 3.18 baseline over a timeout-capable framed channel."""

    def __init__(
        self,
        spec: LanguageServerSpec,
        root: Path,
        channel: FramedMessageChannel,
        *,
        process: ManagedProcess | None = None,
        request_timeout: float = 30.0,
    ) -> None:
        self.spec = spec
        self.root = root.resolve(strict=False)
        self.channel = channel
        self.process = process
        self.request_timeout = request_timeout
        self._request_id = 0
        self.initialized = False
        self.server_capabilities: dict[str, Any] = {}
        self._diagnostics: dict[str, list[dict[str, Any]]] = {}
        self._opened: set[str] = set()

    def initialize(self) -> dict[str, Any]:
        result = self.request(
            "initialize",
            {
                "processId": None,
                "clientInfo": {"name": "Kodepoia", "version": "0.1.0a4"},
                "rootUri": self.root.as_uri(),
                "capabilities": {
                    "textDocument": {
                        "documentSymbol": {},
                        "definition": {},
                        "references": {},
                        "publishDiagnostics": {"relatedInformation": True},
                    },
                    "workspace": {"workspaceFolders": True},
                },
                "workspaceFolders": [{"uri": self.root.as_uri(), "name": self.root.name}],
                "initializationOptions": dict(self.spec.initialization_options or {}),
            },
        )
        if not isinstance(result, dict):
            raise LspError("initialize result must be an object")
        capabilities = result.get("capabilities", {})
        if not isinstance(capabilities, dict):
            raise LspError("initialize capabilities must be an object")
        self.server_capabilities = capabilities
        self.notify("initialized", {})
        self.initialized = True
        return result

    def request(self, method: str, params: Any = None) -> Any:
        self._request_id += 1
        request_id = self._request_id
        message: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            message["params"] = params
        self.channel.send(message)

        while True:
            incoming = self.channel.receive(self.request_timeout)
            if "method" in incoming and "id" in incoming:
                self._handle_server_request(incoming)
                continue
            if "method" in incoming:
                self._handle_notification(incoming)
                continue
            if incoming.get("id") != request_id:
                continue
            error = incoming.get("error")
            if isinstance(error, dict):
                raise LspRpcError(
                    int(error.get("code", -32603)),
                    str(error.get("message", "Unknown LSP error")),
                    error.get("data"),
                )
            return incoming.get("result")

    def notify(self, method: str, params: Any = None) -> None:
        message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        self.channel.send(message)

    def open_document(self, path: Path, language_id: str | None = None) -> str:
        target = path.resolve(strict=True)
        if target != self.root and self.root not in target.parents:
            raise PermissionError(f"Document escapes LSP root: {target}")
        uri = target.as_uri()
        if uri in self._opened:
            return uri
        text = target.read_text(encoding="utf-8")
        self.notify(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": language_id or self.spec.language_id,
                    "version": 1,
                    "text": text,
                }
            },
        )
        self._opened.add(uri)
        return uri

    def document_symbols(self, path: Path) -> Any:
        uri = self.open_document(path)
        return self.request("textDocument/documentSymbol", {"textDocument": {"uri": uri}})

    def definition(self, path: Path, line: int, character: int) -> Any:
        uri = self.open_document(path)
        return self.request(
            "textDocument/definition",
            {
                "textDocument": {"uri": uri},
                "position": _position(line, character),
            },
        )

    def references(
        self,
        path: Path,
        line: int,
        character: int,
        *,
        include_declaration: bool = True,
    ) -> Any:
        uri = self.open_document(path)
        return self.request(
            "textDocument/references",
            {
                "textDocument": {"uri": uri},
                "position": _position(line, character),
                "context": {"includeDeclaration": include_declaration},
            },
        )

    def diagnostics(self, path: Path) -> list[dict[str, Any]]:
        uri = self.open_document(path)
        return list(self._diagnostics.get(uri, ()))

    def close(self) -> None:
        try:
            if self.initialized:
                try:
                    self.request("shutdown")
                finally:
                    self.notify("exit")
        finally:
            self.initialized = False
            self.channel.close()
            if self.process is not None:
                self.process.close()

    def _handle_notification(self, message: dict[str, Any]) -> None:
        if message.get("method") != "textDocument/publishDiagnostics":
            return
        params = message.get("params")
        if not isinstance(params, dict):
            return
        uri = params.get("uri")
        diagnostics = params.get("diagnostics")
        if isinstance(uri, str) and isinstance(diagnostics, list):
            self._diagnostics[uri] = [item for item in diagnostics if isinstance(item, dict)]

    def _handle_server_request(self, message: dict[str, Any]) -> None:
        request_id = message.get("id")
        method = message.get("method")
        if method == "workspace/configuration":
            result: Any = []
            response = {"jsonrpc": "2.0", "id": request_id, "result": result}
        elif method in {"client/registerCapability", "client/unregisterCapability"}:
            response = {"jsonrpc": "2.0", "id": request_id, "result": None}
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Unsupported server request: {method}"},
            }
        self.channel.send(response)


class LspTool:
    """Workspace-scoped manager for explicitly registered language servers."""

    def __init__(self, boundary: WorkspaceBoundary, specs: Iterable[LanguageServerSpec] = ()) -> None:
        self.boundary = boundary
        self.registry = LanguageServerRegistry(specs)
        allowed = {Path(spec.argv[0]).name for spec in self.registry.specs()}
        self.sandbox = ProcessSandbox(boundary.root, allowed_executables=allowed)
        self._sessions: dict[str, LspSession] = {}

    def capabilities(self) -> list[dict[str, Any]]:
        return [
            asdict(
                LanguageServerCapability(
                    server_id=spec.server_id,
                    language_id=spec.language_id,
                    executable=Path(spec.argv[0]).name,
                    running=spec.server_id in self._sessions,
                    initialized=(
                        self._sessions[spec.server_id].initialized
                        if spec.server_id in self._sessions
                        else False
                    ),
                    server_capabilities=(
                        self._sessions[spec.server_id].server_capabilities
                        if spec.server_id in self._sessions
                        else None
                    ),
                )
            )
            for spec in self.registry.specs()
        ]

    def start(self, server_id: str) -> dict[str, Any]:
        if server_id in self._sessions:
            return {"server_id": server_id, "started": False, "already_running": True}
        spec = self.registry.get(server_id)
        cwd = self.boundary.resolve(spec.cwd, must_exist=True)
        process = self.sandbox.spawn_piped(spec.argv, cwd=cwd, env=spec.env)
        channel = FramedMessageChannel(ContentLengthJsonStream(process.stdout, process.stdin))
        session = LspSession(spec, self.boundary.root, channel, process=process)
        try:
            result = session.initialize()
        except Exception:
            session.close()
            raise
        self._sessions[server_id] = session
        return {"server_id": server_id, "started": True, "initialize_result": result}

    def stop(self, server_id: str) -> dict[str, bool]:
        session = self._sessions.pop(server_id, None)
        if session is None:
            return {"stopped": False}
        session.close()
        return {"stopped": True}

    def symbols(self, server_id: str, path: str) -> Any:
        return self._session(server_id).document_symbols(self._target(path))

    def definition(self, server_id: str, path: str, line: int, character: int) -> Any:
        return self._session(server_id).definition(self._target(path), line, character)

    def references(
        self,
        server_id: str,
        path: str,
        line: int,
        character: int,
        *,
        include_declaration: bool = True,
    ) -> Any:
        return self._session(server_id).references(
            self._target(path),
            line,
            character,
            include_declaration=include_declaration,
        )

    def diagnostics(self, server_id: str, path: str) -> list[dict[str, Any]]:
        return self._session(server_id).diagnostics(self._target(path))

    def _target(self, path: str) -> Path:
        target = self.boundary.resolve(path, must_exist=True)
        if not target.is_file():
            raise IsADirectoryError(path)
        return target

    def _session(self, server_id: str) -> LspSession:
        try:
            return self._sessions[server_id]
        except KeyError as exc:
            raise LspError(f"Language server is not running: {server_id}") from exc


def _position(line: int, character: int) -> dict[str, int]:
    if line < 0 or character < 0:
        raise ValueError("LSP line and character must be non-negative")
    return {"line": line, "character": character}
