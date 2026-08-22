from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kodepoia.core.sandbox import ManagedProcess, ProcessSandbox
from kodepoia.kodecode.dap import DapSession, DebugAdapterSpec, DebugConfigurationSpec
from kodepoia.kodecode.lsp import LanguageServerSpec, LspSession
from kodepoia.kodecode.protocol import ContentLengthJsonStream, FramedMessageChannel
from kodepoia.kodecode.workspace import WorkspaceBoundary


@dataclass(frozen=True, slots=True)
class GodotServicePorts:
    lsp: int = 6005
    dap: int = 6006
    debug: int = 6007

    def __post_init__(self) -> None:
        values = (("lsp", self.lsp), ("dap", self.dap), ("debug", self.debug))
        for name, value in values:
            if not 1024 <= value <= 49151:
                raise ValueError(f"{name} port must be between 1024 and 49151")
        if len({self.lsp, self.dap, self.debug}) != 3:
            raise ValueError("LSP, DAP and debug ports must differ")


class _SocketChannelOwner:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.reader = sock.makefile("rb", buffering=0)
        self.writer = sock.makefile("wb", buffering=0)
        self.channel = FramedMessageChannel(ContentLengthJsonStream(self.reader, self.writer))

    def close(self) -> None:
        self.channel.close()
        for stream in (self.reader, self.writer):
            try:
                stream.close()
            except OSError:
                pass
        try:
            self.sock.close()
        except OSError:
            pass


class GodotEditorServices:
    """Start Godot 4.7 editor services and connect LSP/DAP only over loopback."""

    def __init__(self, root: Path, *, executable: str = "godot", sandbox: ProcessSandbox | None = None) -> None:
        self.boundary = WorkspaceBoundary(root)
        self.executable = str(executable)
        self.sandbox = sandbox or ProcessSandbox(
            self.boundary.root,
            allowed_executables={Path(self.executable).name.lower()},
        )
        self.process: ManagedProcess | None = None
        self.ports: GodotServicePorts | None = None
        self._lsp_owner: _SocketChannelOwner | None = None
        self._dap_owner: _SocketChannelOwner | None = None
        self.lsp: LspSession | None = None
        self.dap: DapSession | None = None

    def start(self, ports: GodotServicePorts | None = None, *, timeout: float = 30.0) -> dict[str, Any]:
        if self.process is not None:
            return {
                "started": False,
                "already_running": True,
                "ports": self._ports_dict(),
                "lsp_initialized": bool(self.lsp and self.lsp.initialized),
                "dap_initialized": bool(self.dap and self.dap.initialized),
            }
        if not 1.0 <= timeout <= 120.0:
            raise ValueError("startup timeout must be between 1 and 120 seconds")
        project = self.boundary.resolve("project.godot", must_exist=True)
        if not project.is_file():
            raise FileNotFoundError("project.godot is not a file")
        selected = ports or GodotServicePorts()
        argv = [
            self.executable,
            "--headless",
            "--editor",
            "--path",
            ".",
            "--lsp-port",
            str(selected.lsp),
            "--dap-port",
            str(selected.dap),
            "--debug-server",
            f"tcp://127.0.0.1:{selected.debug}",
        ]
        # Godot LSP/DAP communicate over loopback sockets, not stdio. Using
        # stdout/stderr PIPE here risks blocking a verbose editor before it opens
        # the ports. Keep the process sandboxed and kill-switch registered, but
        # discard unused stdio streams.
        self.process = self.sandbox.spawn_background(argv, cwd=self.boundary.root)
        self.ports = selected
        deadline = time.monotonic() + timeout
        try:
            self.connect_lsp(timeout=self._remaining(deadline))
            self.connect_dap(timeout=self._remaining(deadline))
        except Exception:
            self.close()
            raise
        return {
            "started": True,
            "already_running": False,
            "ports": self._ports_dict(),
            "lsp_initialized": True,
            "dap_initialized": True,
        }

    def connect_lsp(self, *, timeout: float = 10.0) -> LspSession:
        if self.lsp is not None:
            return self.lsp
        port = self._require_ports().lsp
        owner = self._connect_retry(port, timeout)
        spec = LanguageServerSpec("godot-gdscript", "gdscript", ("godot-loopback",))
        session = LspSession(spec, self.boundary.root, owner.channel, request_timeout=timeout)
        try:
            session.initialize()
        except Exception:
            owner.close()
            raise
        self._lsp_owner = owner
        self.lsp = session
        return session

    def connect_dap(self, *, timeout: float = 10.0) -> DapSession:
        if self.dap is not None:
            return self.dap
        ports = self._require_ports()
        owner = self._connect_retry(ports.dap, timeout)
        config = DebugConfigurationSpec(
            "project",
            "launch",
            {
                "project": str(self.boundary.root),
                "address": "127.0.0.1",
                "port": ports.debug,
                "scene": "main",
            },
        )
        spec = DebugAdapterSpec("godot", ("godot-loopback",), configurations=(config,))
        session = DapSession(spec, self.boundary.root, owner.channel, request_timeout=timeout)
        try:
            session.initialize()
        except Exception:
            owner.close()
            raise
        self._dap_owner = owner
        self.dap = session
        return session

    def close(self) -> None:
        if self.lsp is not None:
            try:
                self.lsp.close()
            except Exception:
                pass
            self.lsp = None
        if self._lsp_owner is not None:
            self._lsp_owner.close()
            self._lsp_owner = None
        if self.dap is not None:
            try:
                self.dap.disconnect()
            except Exception:
                pass
            self.dap = None
        if self._dap_owner is not None:
            self._dap_owner.close()
            self._dap_owner = None
        if self.process is not None:
            self.process.close()
            self.process = None
        self.ports = None

    def _require_ports(self) -> GodotServicePorts:
        if self.process is None or self.ports is None:
            raise RuntimeError("Godot editor services are not running")
        if self.process.returncode is not None:
            raise RuntimeError(f"Managed Godot editor process exited with code {self.process.returncode}")
        return self.ports

    def _ports_dict(self) -> dict[str, int] | None:
        return None if self.ports is None else {
            "lsp": self.ports.lsp,
            "dap": self.ports.dap,
            "debug": self.ports.debug,
        }

    def _connect_retry(self, port: int, timeout: float) -> _SocketChannelOwner:
        if not 0.1 <= timeout <= 120.0:
            raise ValueError("connection timeout must be between 0.1 and 120 seconds")
        deadline = time.monotonic() + timeout
        last_error: OSError | None = None
        while time.monotonic() < deadline:
            if self.process is not None and self.process.returncode is not None:
                raise RuntimeError(
                    f"Managed Godot editor process exited with code {self.process.returncode} before port {port} was ready"
                )
            try:
                sock = socket.create_connection(("127.0.0.1", port), timeout=min(0.5, max(0.1, deadline - time.monotonic())))
                return _SocketChannelOwner(sock)
            except OSError as exc:
                last_error = exc
                time.sleep(0.05)
        raise TimeoutError(f"Godot loopback service on port {port} did not become ready: {last_error}")

    @staticmethod
    def _remaining(deadline: float) -> float:
        remaining = deadline - time.monotonic()
        if remaining <= 0.1:
            raise TimeoutError("Godot editor services startup timed out")
        return min(120.0, remaining)
