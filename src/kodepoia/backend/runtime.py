from __future__ import annotations

import http.client
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from kodepoia.core.kill_switch import KillSwitch
from kodepoia.core.sandbox import ManagedProcess, ProcessSandbox
from kodepoia.core.secrets import KodeSecrets

from .contracts import BackendEnvironmentKind
from .health import BackendHealthSnapshot, BackendHealthState, probe_backend_health
from .local_config import BackendLocalConfig
from .scaffold import BackendScaffoldEngine


@dataclass(slots=True)
class BackendRuntimeHandle:
    config: BackendLocalConfig
    process: ManagedProcess
    workspace_root: Path
    host: str
    port: int
    ready_path: Path
    log_path: Path
    stopped: bool = False

    @property
    def pid(self) -> int:
        return self.process.process.pid


class BackendLocalRuntime:
    """Repository-owned local/test fixture runtime governed by ProcessSandbox/KillSwitch."""

    def __init__(
        self,
        workspace_root: Path,
        *,
        secrets: KodeSecrets | None = None,
        kill_switch: KillSwitch | None = None,
    ) -> None:
        self.workspace_root = workspace_root.resolve(strict=False)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.secrets = secrets or KodeSecrets()
        executable = Path(sys.executable).name.lower()
        self.sandbox = ProcessSandbox(
            self.workspace_root,
            allowed_executables={executable},
            kill_switch=kill_switch,
        )
        self.scaffold = BackendScaffoldEngine()

    def start(
        self,
        config: BackendLocalConfig,
        *,
        startup_timeout: float = 8.0,
    ) -> BackendRuntimeHandle:
        if config.environment.kind not in {BackendEnvironmentKind.LOCAL, BackendEnvironmentKind.TEST}:
            raise PermissionError("R14.3 runtime may start only LOCAL or TEST environments")
        if startup_timeout <= 0:
            raise ValueError("startup_timeout must be positive")
        config.assert_secret_boundary(self.secrets)
        self.scaffold.generate(self.workspace_root, config, secrets=self.secrets)
        config_path = self.workspace_root / self.scaffold.RUNTIME_CONFIG_PATH
        run_root = self.workspace_root / ".kodepoia" / "backend" / "run"
        run_root.mkdir(parents=True, exist_ok=True)
        ready_path = run_root / "ready.json"
        log_path = run_root / "runtime.log"
        ready_path.unlink(missing_ok=True)
        log_path.unlink(missing_ok=True)
        argv = (
            sys.executable,
            "-m",
            "kodepoia.backend.local_fixture_server",
            "--config",
            str(config_path),
            "--ready-file",
            str(ready_path),
            "--log-file",
            str(log_path),
        )
        managed = self.sandbox.spawn_background(argv, cwd=self.workspace_root)
        deadline = time.monotonic() + startup_timeout
        snapshot: BackendHealthSnapshot | None = None
        try:
            while time.monotonic() < deadline:
                if ready_path.is_file():
                    try:
                        snapshot = BackendHealthSnapshot.from_dict(
                            json.loads(ready_path.read_text(encoding="utf-8"))
                        )
                    except (OSError, json.JSONDecodeError, ValueError):
                        snapshot = None
                    if snapshot is not None:
                        break
                if managed.returncode is not None:
                    detail = self._redacted_log_path(log_path)
                    raise RuntimeError(
                        f"local backend exited before readiness (returncode={managed.returncode}): {detail}"
                    )
                time.sleep(0.025)
            if snapshot is None:
                raise TimeoutError("local backend did not become ready within startup_timeout")
            if snapshot.host != config.host:
                raise RuntimeError("local backend readiness host differs from governed config")
            observed = probe_backend_health(snapshot.host, snapshot.port, timeout=2.0)
            if not observed.live or not observed.ready or observed.state is not BackendHealthState.READY:
                raise RuntimeError("local backend failed readiness validation")
            return BackendRuntimeHandle(
                config=config,
                process=managed,
                workspace_root=self.workspace_root,
                host=snapshot.host,
                port=snapshot.port,
                ready_path=ready_path,
                log_path=log_path,
            )
        except Exception:
            managed.close()
            raise

    def probe(self, handle: BackendRuntimeHandle, *, timeout: float = 2.0) -> BackendHealthSnapshot:
        if handle.stopped:
            return self._stopped_snapshot(handle)
        return probe_backend_health(handle.host, handle.port, timeout=timeout)

    def stop(
        self,
        handle: BackendRuntimeHandle,
        *,
        shutdown_timeout: float = 4.0,
    ) -> BackendHealthSnapshot:
        if shutdown_timeout <= 0:
            raise ValueError("shutdown_timeout must be positive")
        if handle.stopped:
            return self._stopped_snapshot(handle)
        try:
            connection = http.client.HTTPConnection(handle.host, handle.port, timeout=1.5)
            try:
                connection.request("POST", "/__shutdown", body=b"", headers={"Connection": "close"})
                response = connection.getresponse()
                response.read(4096)
                if response.status != 202:
                    raise RuntimeError(f"local backend shutdown returned HTTP {response.status}")
            finally:
                connection.close()
            try:
                handle.process.process.wait(timeout=shutdown_timeout)
            except subprocess.TimeoutExpired:
                pass
        finally:
            handle.process.close()
            handle.stopped = True
        return self._stopped_snapshot(handle)

    def redacted_log(self, handle: BackendRuntimeHandle) -> str:
        return self._redacted_log_path(handle.log_path)

    def _redacted_log_path(self, path: Path) -> str:
        if not path.is_file():
            return ""
        return self.secrets.redact(path.read_text(encoding="utf-8", errors="replace"))

    @staticmethod
    def _stopped_snapshot(handle: BackendRuntimeHandle) -> BackendHealthSnapshot:
        return BackendHealthSnapshot(
            service_id=f"{handle.config.project_id}.local",
            environment_id=handle.config.environment.environment_id,
            state=BackendHealthState.STOPPED,
            live=False,
            ready=False,
            host=handle.host,
            port=handle.port,
        )
