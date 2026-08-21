from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from kodepoia.core.sandbox import ManagedProcess, ProcessSandbox
from kodepoia.kodecode.protocol import ContentLengthJsonStream, FramedMessageChannel
from kodepoia.kodecode.workspace import WorkspaceBoundary

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class DapError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class DebugConfigurationSpec:
    config_id: str
    mode: str
    arguments: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not _ID.fullmatch(self.config_id):
            raise ValueError(f"Invalid debug configuration id: {self.config_id}")
        if self.mode not in {"launch", "attach"}:
            raise ValueError("Debug configuration mode must be launch or attach")


@dataclass(frozen=True, slots=True)
class DebugAdapterSpec:
    adapter_id: str
    argv: tuple[str, ...]
    cwd: str = "."
    env: Mapping[str, str] = field(default_factory=dict)
    configurations: tuple[DebugConfigurationSpec, ...] = ()

    def __post_init__(self) -> None:
        if not _ID.fullmatch(self.adapter_id):
            raise ValueError(f"Invalid debug adapter id: {self.adapter_id}")
        if not self.argv or not self.argv[0].strip():
            raise ValueError("Debug adapter argv cannot be empty")
        if any("\x00" in item for item in self.argv):
            raise ValueError("Debug adapter argv cannot contain NUL bytes")
        ids = [item.config_id for item in self.configurations]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate debug configuration id")


class DebugAdapterRegistry:
    def __init__(self, specs: Iterable[DebugAdapterSpec] = ()) -> None:
        self._specs: dict[str, DebugAdapterSpec] = {}
        for spec in specs:
            self.register(spec)

    def register(self, spec: DebugAdapterSpec) -> None:
        if spec.adapter_id in self._specs:
            raise ValueError(f"Duplicate debug adapter id: {spec.adapter_id}")
        self._specs[spec.adapter_id] = spec

    def get(self, adapter_id: str) -> DebugAdapterSpec:
        try:
            return self._specs[adapter_id]
        except KeyError as exc:
            raise KeyError(f"Unknown debug adapter: {adapter_id}") from exc

    def specs(self) -> tuple[DebugAdapterSpec, ...]:
        return tuple(self._specs.values())


class DapSession:
    """DAP 1.71 baseline client over the shared framed channel."""

    def __init__(
        self,
        spec: DebugAdapterSpec,
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
        self._seq = 0
        self.capabilities: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []
        self.initialized = False

    def initialize(self) -> dict[str, Any]:
        body = self.request(
            "initialize",
            {
                "clientID": "kodepoia",
                "clientName": "Kodepoia",
                "adapterID": self.spec.adapter_id,
                "pathFormat": "path",
                "linesStartAt1": True,
                "columnsStartAt1": True,
                "supportsVariableType": True,
                "supportsVariablePaging": True,
            },
        )
        self.capabilities = dict(body or {})
        self.initialized = True
        return self.capabilities

    def request(self, command: str, arguments: Mapping[str, Any] | None = None) -> Any:
        self._seq += 1
        request_seq = self._seq
        message: dict[str, Any] = {
            "seq": request_seq,
            "type": "request",
            "command": command,
        }
        if arguments is not None:
            message["arguments"] = dict(arguments)
        self.channel.send(message)

        while True:
            incoming = self.channel.receive(self.request_timeout)
            msg_type = incoming.get("type")
            if msg_type == "event":
                self.events.append(incoming)
                continue
            if msg_type == "request":
                self._reject_adapter_request(incoming)
                continue
            if msg_type != "response" or incoming.get("request_seq") != request_seq:
                continue
            if not bool(incoming.get("success", False)):
                raise DapError(str(incoming.get("message", f"DAP request failed: {command}")))
            return incoming.get("body")

    def start_configuration(self, config: DebugConfigurationSpec) -> Any:
        if not self.initialized:
            raise DapError("Debug adapter is not initialized")
        return self.request(config.mode, config.arguments)

    def set_breakpoints(self, source: Path, lines: Iterable[int]) -> Any:
        target = source.resolve(strict=True)
        self._require_inside_root(target)
        breakpoints = []
        for line in lines:
            if line < 1:
                raise ValueError("DAP breakpoint lines are 1-based")
            breakpoints.append({"line": int(line)})
        return self.request(
            "setBreakpoints",
            {"source": {"path": str(target)}, "breakpoints": breakpoints, "sourceModified": False},
        )

    def configuration_done(self) -> Any:
        return self.request("configurationDone", {})

    def threads(self) -> list[dict[str, Any]]:
        body = self.request("threads", {}) or {}
        return list(body.get("threads", [])) if isinstance(body, dict) else []

    def stack_trace(self, thread_id: int, *, start_frame: int = 0, levels: int = 50) -> list[dict[str, Any]]:
        if thread_id < 0 or start_frame < 0 or levels < 1:
            raise ValueError("Invalid DAP stackTrace arguments")
        body = self.request(
            "stackTrace",
            {"threadId": thread_id, "startFrame": start_frame, "levels": min(levels, 500)},
        ) or {}
        return list(body.get("stackFrames", [])) if isinstance(body, dict) else []

    def scopes(self, frame_id: int) -> list[dict[str, Any]]:
        if frame_id < 0:
            raise ValueError("frame_id must be non-negative")
        body = self.request("scopes", {"frameId": frame_id}) or {}
        return list(body.get("scopes", [])) if isinstance(body, dict) else []

    def variables(self, reference: int, *, start: int = 0, count: int = 100) -> list[dict[str, Any]]:
        if reference <= 0 or start < 0 or count < 1:
            raise ValueError("Invalid DAP variables arguments")
        body = self.request(
            "variables",
            {"variablesReference": reference, "start": start, "count": min(count, 1000)},
        ) or {}
        return list(body.get("variables", [])) if isinstance(body, dict) else []

    def disconnect(self, *, terminate_debuggee: bool = False) -> None:
        try:
            if self.initialized:
                self.request("disconnect", {"terminateDebuggee": terminate_debuggee})
        finally:
            self.initialized = False
            self.channel.close()
            if self.process is not None:
                self.process.close()

    def _reject_adapter_request(self, request: dict[str, Any]) -> None:
        self._seq += 1
        self.channel.send(
            {
                "seq": self._seq,
                "type": "response",
                "request_seq": request.get("seq"),
                "success": False,
                "command": request.get("command"),
                "message": "Adapter->client requests are not enabled in R4.4 baseline",
            }
        )

    def _require_inside_root(self, target: Path) -> None:
        if target != self.root and self.root not in target.parents:
            raise PermissionError(f"DAP source escapes workspace: {target}")


class DapTool:
    """Manager for explicitly registered debug adapters/configurations."""

    def __init__(self, boundary: WorkspaceBoundary, specs: Iterable[DebugAdapterSpec] = ()) -> None:
        self.boundary = boundary
        self.registry = DebugAdapterRegistry(specs)
        allowed = {Path(spec.argv[0]).name for spec in self.registry.specs()}
        self.sandbox = ProcessSandbox(boundary.root, allowed_executables=allowed)
        self._sessions: dict[str, DapSession] = {}

    def capabilities(self) -> list[dict[str, Any]]:
        result = []
        for spec in self.registry.specs():
            session = self._sessions.get(spec.adapter_id)
            result.append(
                {
                    "adapter_id": spec.adapter_id,
                    "executable": Path(spec.argv[0]).name,
                    "configurations": [asdict(item) | {"arguments": "<pre-registered>"} for item in spec.configurations],
                    "running": session is not None,
                    "initialized": bool(session and session.initialized),
                    "adapter_capabilities": dict(session.capabilities) if session else None,
                }
            )
        return result

    def start(self, adapter_id: str) -> dict[str, Any]:
        if adapter_id in self._sessions:
            return {"adapter_id": adapter_id, "started": False, "already_running": True}
        spec = self.registry.get(adapter_id)
        cwd = self.boundary.resolve(spec.cwd, must_exist=True)
        process = self.sandbox.spawn_piped(spec.argv, cwd=cwd, env=spec.env)
        session = DapSession(
            spec,
            self.boundary.root,
            FramedMessageChannel(ContentLengthJsonStream(process.stdout, process.stdin)),
            process=process,
        )
        try:
            capabilities = session.initialize()
        except Exception:
            session.disconnect()
            raise
        self._sessions[adapter_id] = session
        return {"adapter_id": adapter_id, "started": True, "capabilities": capabilities}

    def configure(self, adapter_id: str, config_id: str) -> Any:
        spec = self.registry.get(adapter_id)
        config = next((item for item in spec.configurations if item.config_id == config_id), None)
        if config is None:
            raise KeyError(f"Unknown debug configuration: {config_id}")
        return self._session(adapter_id).start_configuration(config)

    def stop(self, adapter_id: str, *, terminate_debuggee: bool = False) -> dict[str, bool]:
        session = self._sessions.pop(adapter_id, None)
        if session is None:
            return {"stopped": False}
        session.disconnect(terminate_debuggee=terminate_debuggee)
        return {"stopped": True}

    def set_breakpoints(self, adapter_id: str, path: str, lines: Iterable[int]) -> Any:
        target = self.boundary.resolve(path, must_exist=True)
        return self._session(adapter_id).set_breakpoints(target, lines)

    def threads(self, adapter_id: str) -> list[dict[str, Any]]:
        return self._session(adapter_id).threads()

    def stack(self, adapter_id: str, thread_id: int) -> list[dict[str, Any]]:
        return self._session(adapter_id).stack_trace(thread_id)

    def scopes(self, adapter_id: str, frame_id: int) -> list[dict[str, Any]]:
        return self._session(adapter_id).scopes(frame_id)

    def variables(self, adapter_id: str, reference: int) -> list[dict[str, Any]]:
        return self._session(adapter_id).variables(reference)

    def configuration_done(self, adapter_id: str) -> Any:
        return self._session(adapter_id).configuration_done()

    def _session(self, adapter_id: str) -> DapSession:
        try:
            return self._sessions[adapter_id]
        except KeyError as exc:
            raise DapError(f"Debug adapter is not running: {adapter_id}") from exc
