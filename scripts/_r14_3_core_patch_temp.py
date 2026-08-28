from pathlib import Path

FILES = {
"src/kodepoia/backend/local_config.py": r'''from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from kodepoia.core.secrets import SecretRef, assert_secret_refs_only, KodeSecrets

from .contracts import (
    BackendEnvironmentIdentity,
    BackendEnvironmentKind,
    BackendServiceKind,
    canonical_sha256,
)
from .intent import BackendRuntimeIntent

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class BackendLogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


def _validate_port(port: int) -> None:
    if isinstance(port, bool) or not isinstance(port, int):
        raise ValueError("backend local port must be an integer")
    if port != 0 and not 1024 <= port <= 65535:
        raise ValueError("backend local port must be 0 or in [1024, 65535]")


def _validate_loopback_host(host: str) -> str:
    if not isinstance(host, str) or host != host.strip() or not host:
        raise ValueError("backend local host must be a bare loopback IP literal")
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("backend local host must be a bare loopback IP literal") from exc
    if address.version != 4 or not address.is_loopback:
        raise ValueError("R14.3 backend runtime must bind IPv4 loopback only")
    return address.compressed


def _normalize_services(services: tuple[BackendServiceKind, ...]) -> tuple[BackendServiceKind, ...]:
    if not isinstance(services, tuple) or not services:
        raise ValueError("backend local config requires at least one service")
    if any(not isinstance(item, BackendServiceKind) for item in services):
        raise ValueError("backend local services must use BackendServiceKind")
    return tuple(sorted(set(services), key=lambda item: item.value))


def _normalize_refs(refs: tuple[SecretRef, ...]) -> tuple[SecretRef, ...]:
    if not isinstance(refs, tuple):
        raise ValueError("secret_refs must be an immutable tuple")
    if any(not isinstance(item, SecretRef) for item in refs):
        raise ValueError("secret_refs must contain SecretRef values")
    return tuple(sorted(set(refs), key=lambda item: (item.namespace, item.key)))


@dataclass(frozen=True, slots=True)
class BackendLocalConfig:
    project_id: str
    environment: BackendEnvironmentIdentity
    services: tuple[BackendServiceKind, ...]
    host: str = "127.0.0.1"
    port: int = 0
    log_level: BackendLogLevel = BackendLogLevel.INFO
    secret_refs: tuple[SecretRef, ...] = ()
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported backend local config schema version")
        if not isinstance(self.project_id, str) or _STABLE_ID_RE.fullmatch(self.project_id) is None:
            raise ValueError("project_id must be a stable identifier")
        if not isinstance(self.environment, BackendEnvironmentIdentity):
            raise ValueError("environment must be BackendEnvironmentIdentity")
        object.__setattr__(self, "services", _normalize_services(self.services))
        object.__setattr__(self, "host", _validate_loopback_host(self.host))
        _validate_port(self.port)
        if not isinstance(self.log_level, BackendLogLevel):
            raise ValueError("log_level must be BackendLogLevel")
        object.__setattr__(self, "secret_refs", _normalize_refs(self.secret_refs))

    def canonical(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "environment": self.environment.canonical(),
            "services": [item.value for item in self.services],
            "bind": {"host": self.host, "port": self.port},
            "log_level": self.log_level.value,
            "secret_refs": [item.to_dict() for item in self.secret_refs],
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())

    def assert_secret_boundary(self, secrets: KodeSecrets) -> None:
        assert_secret_refs_only(self.canonical(), self.secret_refs, secrets.known_values())

    @classmethod
    def from_dict(cls, raw: object) -> "BackendLocalConfig":
        if not isinstance(raw, dict):
            raise ValueError("backend local config must be an object")
        expected = {
            "schema_version",
            "project_id",
            "environment",
            "services",
            "bind",
            "log_level",
            "secret_refs",
        }
        if set(raw) != expected:
            raise ValueError("backend local config has unknown or missing keys")
        environment = raw["environment"]
        bind = raw["bind"]
        services = raw["services"]
        refs = raw["secret_refs"]
        if not isinstance(environment, dict) or set(environment) != {"environment_id", "kind"}:
            raise ValueError("backend local environment has invalid keys")
        if not isinstance(bind, dict) or set(bind) != {"host", "port"}:
            raise ValueError("backend local bind has invalid keys")
        if not isinstance(services, list):
            raise ValueError("backend local services must be an array")
        if not isinstance(refs, list):
            raise ValueError("backend local secret_refs must be an array")
        parsed_refs: list[SecretRef] = []
        for item in refs:
            if not isinstance(item, dict) or set(item) != {"namespace", "key"}:
                raise ValueError("backend local secret reference has invalid keys")
            parsed_refs.append(SecretRef(namespace=str(item["namespace"]), key=str(item["key"])))
        return cls(
            schema_version=int(raw["schema_version"]),
            project_id=str(raw["project_id"]),
            environment=BackendEnvironmentIdentity(
                environment_id=str(environment["environment_id"]),
                kind=BackendEnvironmentKind(str(environment["kind"])),
            ),
            services=tuple(BackendServiceKind(str(item)) for item in services),
            host=str(bind["host"]),
            port=int(bind["port"]),
            log_level=BackendLogLevel(str(raw["log_level"])),
            secret_refs=tuple(parsed_refs),
        )


@dataclass(frozen=True, slots=True)
class BackendConfigOverlay:
    environment: BackendEnvironmentIdentity | None = None
    port: int | None = None
    log_level: BackendLogLevel | None = None
    secret_refs: tuple[SecretRef, ...] | None = None

    def apply(self, base: BackendLocalConfig) -> BackendLocalConfig:
        if not isinstance(base, BackendLocalConfig):
            raise ValueError("backend overlay base must be BackendLocalConfig")
        port = base.port if self.port is None else self.port
        _validate_port(port)
        refs = base.secret_refs if self.secret_refs is None else _normalize_refs(self.secret_refs)
        level = base.log_level if self.log_level is None else self.log_level
        if not isinstance(level, BackendLogLevel):
            raise ValueError("backend overlay log_level must be BackendLogLevel")
        return BackendLocalConfig(
            project_id=base.project_id,
            environment=base.environment if self.environment is None else self.environment,
            services=base.services,
            host=base.host,
            port=port,
            log_level=level,
            secret_refs=refs,
        )


def local_config_from_runtime_intents(
    project_id: str,
    intents: tuple[BackendRuntimeIntent, ...],
    *,
    environment: BackendEnvironmentKind = BackendEnvironmentKind.LOCAL,
    port: int = 0,
    log_level: BackendLogLevel = BackendLogLevel.INFO,
    secret_refs: tuple[SecretRef, ...] = (),
) -> BackendLocalConfig:
    if not isinstance(intents, tuple) or not intents:
        raise ValueError("R14.3 local scaffold requires at least one R14.2 runtime intent")
    if any(not isinstance(item, BackendRuntimeIntent) for item in intents):
        raise ValueError("intents must contain BackendRuntimeIntent values")
    selected = {item.service_kind for item in intents}
    for intent in intents:
        missing = tuple(item for item in intent.dependencies if item not in selected)
        if missing:
            names = ", ".join(item.value for item in missing)
            raise ValueError(f"runtime intent dependencies missing from local config: {names}")
    return BackendLocalConfig(
        project_id=project_id,
        environment=BackendEnvironmentIdentity(environment_id=environment.value, kind=environment),
        services=tuple(selected),
        port=port,
        log_level=log_level,
        secret_refs=secret_refs,
    )
''',
"src/kodepoia/backend/scaffold.py": r'''from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from kodepoia.core.secrets import KodeSecrets

from .contracts import canonical_json_bytes, canonical_sha256
from .local_config import BackendLocalConfig


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _inside(root: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("backend scaffold path must be safe and relative")
    target = (root / path).resolve(strict=False)
    if target != root and root not in target.parents:
        raise ValueError("backend scaffold path escapes workspace root")
    return target


@dataclass(frozen=True, slots=True)
class BackendRenderedFile:
    path: str
    sha256: str

    def canonical(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class BackendWorkspaceManifest:
    project_id: str
    config_sha256: str
    template_sha256: str
    files: tuple[BackendRenderedFile, ...]
    schema_version: int = 1
    template_id: str = "kodepoia_local_backend"
    template_version: str = "1.0"

    def canonical(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "template_id": self.template_id,
            "template_version": self.template_version,
            "project_id": self.project_id,
            "config_sha256": self.config_sha256,
            "template_sha256": self.template_sha256,
            "files": [item.canonical() for item in self.files],
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.canonical())

    def digest(self) -> str:
        return canonical_sha256(self.canonical())

    @classmethod
    def from_dict(cls, raw: object) -> "BackendWorkspaceManifest":
        if not isinstance(raw, dict):
            raise ValueError("backend workspace manifest must be an object")
        expected = {
            "schema_version",
            "template_id",
            "template_version",
            "project_id",
            "config_sha256",
            "template_sha256",
            "files",
        }
        if set(raw) != expected:
            raise ValueError("backend workspace manifest has unknown or missing keys")
        files_raw = raw["files"]
        if not isinstance(files_raw, list):
            raise ValueError("backend workspace files must be an array")
        files: list[BackendRenderedFile] = []
        for item in files_raw:
            if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
                raise ValueError("backend workspace file entry has invalid keys")
            files.append(BackendRenderedFile(path=str(item["path"]), sha256=str(item["sha256"])))
        manifest = cls(
            schema_version=int(raw["schema_version"]),
            template_id=str(raw["template_id"]),
            template_version=str(raw["template_version"]),
            project_id=str(raw["project_id"]),
            config_sha256=str(raw["config_sha256"]),
            template_sha256=str(raw["template_sha256"]),
            files=tuple(files),
        )
        if manifest.schema_version != 1 or manifest.template_id != "kodepoia_local_backend":
            raise ValueError("unsupported backend workspace manifest identity")
        for digest in (manifest.config_sha256, manifest.template_sha256, *(item.sha256 for item in manifest.files)):
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise ValueError("backend workspace manifest digests must be lowercase SHA-256")
        if tuple(sorted(manifest.files, key=lambda item: item.path)) != manifest.files:
            raise ValueError("backend workspace files must be sorted")
        return manifest


class BackendScaffoldEngine:
    RUNTIME_CONFIG_PATH = ".kodepoia/backend/runtime.json"
    MANIFEST_PATH = ".kodepoia/backend/workspace-manifest.json"
    README_PATH = "backend/README.md"
    TEMPLATE_DESCRIPTOR = {
        "template_id": "kodepoia_local_backend",
        "template_version": "1.0",
        "paths": [RUNTIME_CONFIG_PATH, README_PATH],
        "runtime_owner": "kodepoia.backend.local_fixture_server",
    }

    def render(self, config: BackendLocalConfig) -> tuple[dict[str, bytes], BackendWorkspaceManifest]:
        if not isinstance(config, BackendLocalConfig):
            raise ValueError("backend scaffold requires BackendLocalConfig")
        config_bytes = canonical_json_bytes(config.canonical()) + b"\n"
        services = ", ".join(item.value for item in config.services)
        readme = (
            "# Kodepoia local backend workspace\n\n"
            f"Project: `{config.project_id}`\n\n"
            f"Environment: `{config.environment.kind.value}`\n\n"
            f"Service intents: `{services}`\n\n"
            "This workspace is generated for local/test development only. "
            "The executable runtime remains repository-owned by Kodepoia; no provider, "
            "deployment script, credential or production endpoint is generated here.\n"
        ).encode("utf-8")
        rendered = {
            self.RUNTIME_CONFIG_PATH: config_bytes,
            self.README_PATH: readme,
        }
        files = tuple(
            BackendRenderedFile(path=path, sha256=_sha256_bytes(content))
            for path, content in sorted(rendered.items())
        )
        manifest = BackendWorkspaceManifest(
            project_id=config.project_id,
            config_sha256=config.digest(),
            template_sha256=canonical_sha256(self.TEMPLATE_DESCRIPTOR),
            files=files,
        )
        return rendered, manifest

    def generate(
        self,
        project_root: Path,
        config: BackendLocalConfig,
        *,
        secrets: KodeSecrets | None = None,
    ) -> BackendWorkspaceManifest:
        root = project_root.resolve(strict=False)
        root.mkdir(parents=True, exist_ok=True)
        if secrets is not None:
            config.assert_secret_boundary(secrets)
        rendered, manifest = self.render(config)
        rendered_with_manifest = dict(rendered)
        rendered_with_manifest[self.MANIFEST_PATH] = manifest.canonical_bytes() + b"\n"
        for relative, content in sorted(rendered_with_manifest.items()):
            target = _inside(root, relative)
            if target.exists():
                if not target.is_file() or target.read_bytes() != content:
                    raise FileExistsError(
                        f"backend scaffold refuses to overwrite divergent file: {relative}"
                    )
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        return manifest

    def load_config(self, project_root: Path) -> BackendLocalConfig:
        root = project_root.resolve(strict=False)
        path = _inside(root, self.RUNTIME_CONFIG_PATH)
        return BackendLocalConfig.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def load_manifest(self, project_root: Path) -> BackendWorkspaceManifest:
        root = project_root.resolve(strict=False)
        path = _inside(root, self.MANIFEST_PATH)
        return BackendWorkspaceManifest.from_dict(json.loads(path.read_text(encoding="utf-8")))
''',
"src/kodepoia/backend/health.py": r'''from __future__ import annotations

import http.client
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .contracts import canonical_sha256


class BackendHealthState(StrEnum):
    STARTING = "starting"
    READY = "ready"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class BackendHealthSnapshot:
    service_id: str
    environment_id: str
    state: BackendHealthState
    live: bool
    ready: bool
    host: str
    port: int
    runtime_version: str = "r14.3-v1"
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported backend health schema version")
        if not self.service_id or not self.environment_id:
            raise ValueError("backend health identities cannot be empty")
        if not isinstance(self.live, bool) or not isinstance(self.ready, bool):
            raise ValueError("backend health live/ready values must be boolean")
        if isinstance(self.port, bool) or not isinstance(self.port, int) or not 1 <= self.port <= 65535:
            raise ValueError("backend health port must be in [1, 65535]")
        if self.ready and (not self.live or self.state is not BackendHealthState.READY):
            raise ValueError("ready backend health must be live and READY")
        if self.state is BackendHealthState.READY and not self.ready:
            raise ValueError("READY health state requires ready=true")
        if self.state is BackendHealthState.STOPPED and (self.live or self.ready):
            raise ValueError("STOPPED health cannot be live or ready")

    def canonical(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "service_id": self.service_id,
            "environment_id": self.environment_id,
            "state": self.state.value,
            "live": self.live,
            "ready": self.ready,
            "host": self.host,
            "port": self.port,
            "runtime_version": self.runtime_version,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())

    @classmethod
    def from_dict(cls, raw: object) -> "BackendHealthSnapshot":
        if not isinstance(raw, dict):
            raise ValueError("backend health payload must be an object")
        expected = {
            "schema_version",
            "service_id",
            "environment_id",
            "state",
            "live",
            "ready",
            "host",
            "port",
            "runtime_version",
        }
        if set(raw) != expected:
            raise ValueError("backend health payload has unknown or missing keys")
        return cls(
            schema_version=int(raw["schema_version"]),
            service_id=str(raw["service_id"]),
            environment_id=str(raw["environment_id"]),
            state=BackendHealthState(str(raw["state"])),
            live=raw["live"],
            ready=raw["ready"],
            host=str(raw["host"]),
            port=int(raw["port"]),
            runtime_version=str(raw["runtime_version"]),
        )


def probe_backend_health(host: str, port: int, *, timeout: float = 2.0) -> BackendHealthSnapshot:
    connection = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        connection.request("GET", "/healthz", headers={"Connection": "close"})
        response = connection.getresponse()
        body = response.read(64 * 1024 + 1)
        if response.status != 200:
            raise RuntimeError(f"backend health probe returned HTTP {response.status}")
        if len(body) > 64 * 1024:
            raise RuntimeError("backend health payload exceeded 64 KiB")
    finally:
        connection.close()
    import json

    return BackendHealthSnapshot.from_dict(json.loads(body.decode("utf-8")))
''',
"src/kodepoia/backend/local_fixture_server.py": r'''from __future__ import annotations

import argparse
import ipaddress
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .contracts import canonical_json_bytes
from .health import BackendHealthSnapshot, BackendHealthState
from .local_config import BackendLocalConfig


def _write_log(path: Path, event: str, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"event": event, **payload}
    with path.open("ab") as handle:
        handle.write(canonical_json_bytes(record) + b"\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")


class _FixtureHandler(BaseHTTPRequestHandler):
    server_version = "KodepoiaLocalBackend/1"
    sys_version = ""

    def log_message(self, _format: str, *_args: object) -> None:
        return

    @property
    def _snapshot(self) -> BackendHealthSnapshot:
        return self.server.runtime_snapshot  # type: ignore[attr-defined]

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = canonical_json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in {"/healthz", "/readyz", "/livez"}:
            self._send_json(200, self._snapshot.canonical())
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if path != "/__shutdown":
            self._send_json(404, {"error": "not_found"})
            return
        try:
            source = ipaddress.ip_address(self.client_address[0])
        except ValueError:
            self._send_json(403, {"error": "loopback_required"})
            return
        if not source.is_loopback:
            self._send_json(403, {"error": "loopback_required"})
            return
        self._send_json(202, {"status": "stopping"})
        threading.Thread(target=self.server.shutdown, daemon=True).start()


def run_fixture(config_path: Path, ready_file: Path, log_file: Path) -> int:
    try:
        config = BackendLocalConfig.from_dict(json.loads(config_path.read_text(encoding="utf-8")))
    except Exception as exc:
        _write_log(log_file, "config_failed", {"error_type": type(exc).__name__})
        return 2
    if config.environment.kind.value not in {"local", "test"}:
        _write_log(log_file, "environment_blocked", {"environment": config.environment.kind.value})
        return 3
    try:
        server = ThreadingHTTPServer((config.host, config.port), _FixtureHandler)
    except OSError as exc:
        _write_log(
            log_file,
            "bind_failed",
            {"host": config.host, "port": config.port, "error_type": type(exc).__name__},
        )
        return 4
    server.daemon_threads = True
    bound_host, bound_port = server.server_address[:2]
    snapshot = BackendHealthSnapshot(
        service_id=f"{config.project_id}.local",
        environment_id=config.environment.environment_id,
        state=BackendHealthState.READY,
        live=True,
        ready=True,
        host=str(bound_host),
        port=int(bound_port),
    )
    server.runtime_snapshot = snapshot  # type: ignore[attr-defined]
    _write_json(ready_file, snapshot.canonical())
    _write_log(
        log_file,
        "started",
        {
            "config_sha256": config.digest(),
            "host": snapshot.host,
            "port": snapshot.port,
            "environment": config.environment.kind.value,
            "secret_ref_count": len(config.secret_refs),
        },
    )
    try:
        server.serve_forever(poll_interval=0.1)
    finally:
        server.server_close()
        _write_log(log_file, "stopped", {"host": snapshot.host, "port": snapshot.port})
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kodepoia repository-owned R14.3 local fixture server")
    parser.add_argument("--config", required=True)
    parser.add_argument("--ready-file", required=True)
    parser.add_argument("--log-file", required=True)
    args = parser.parse_args(argv)
    return run_fixture(Path(args.config), Path(args.ready_file), Path(args.log_file))


if __name__ == "__main__":
    raise SystemExit(main())
''',
"src/kodepoia/backend/runtime.py": r'''from __future__ import annotations

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
''',
"schemas/r14/backend-local-config.schema.json": r'''{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://kodepoia.local/schemas/r14/backend-local-config.schema.json",
  "title": "Kodepoia R14.3 local backend config",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "project_id", "environment", "services", "bind", "log_level", "secret_refs"],
  "properties": {
    "schema_version": {"const": 1},
    "project_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"},
    "environment": {
      "type": "object",
      "additionalProperties": false,
      "required": ["environment_id", "kind"],
      "properties": {
        "environment_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"},
        "kind": {"enum": ["local", "test", "staging", "production"]}
      }
    },
    "services": {
      "type": "array",
      "minItems": 1,
      "uniqueItems": true,
      "items": {"enum": ["auth", "database", "authoritative_server", "matchmaking", "cloud_save", "progression", "catalog", "entitlement", "billing", "remote_config", "content_delivery", "events", "liveops"]}
    },
    "bind": {
      "type": "object",
      "additionalProperties": false,
      "required": ["host", "port"],
      "properties": {
        "host": {"type": "string", "pattern": "^127(?:\\.(?:25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])){3}$"},
        "port": {"type": "integer", "minimum": 0, "maximum": 65535, "anyOf": [{"const": 0}, {"minimum": 1024}]}
      }
    },
    "log_level": {"enum": ["debug", "info", "warning", "error"]},
    "secret_refs": {
      "type": "array",
      "uniqueItems": true,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["namespace", "key"],
        "properties": {
          "namespace": {"type": "string", "minLength": 1},
          "key": {"type": "string", "minLength": 1}
        }
      }
    }
  }
}
''',
"schemas/r14/backend-workspace-manifest.schema.json": r'''{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://kodepoia.local/schemas/r14/backend-workspace-manifest.schema.json",
  "title": "Kodepoia R14.3 local backend workspace manifest",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "template_id", "template_version", "project_id", "config_sha256", "template_sha256", "files"],
  "properties": {
    "schema_version": {"const": 1},
    "template_id": {"const": "kodepoia_local_backend"},
    "template_version": {"const": "1.0"},
    "project_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"},
    "config_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "template_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "files": {
      "type": "array",
      "minItems": 2,
      "uniqueItems": true,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["path", "sha256"],
        "properties": {
          "path": {"type": "string", "minLength": 1},
          "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}
        }
      }
    }
  }
}
''',
"schemas/r14/backend-health-snapshot.schema.json": r'''{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://kodepoia.local/schemas/r14/backend-health-snapshot.schema.json",
  "title": "Kodepoia R14.3 backend health snapshot",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "service_id", "environment_id", "state", "live", "ready", "host", "port", "runtime_version"],
  "properties": {
    "schema_version": {"const": 1},
    "service_id": {"type": "string", "minLength": 1},
    "environment_id": {"type": "string", "minLength": 1},
    "state": {"enum": ["starting", "ready", "stopping", "stopped", "failed"]},
    "live": {"type": "boolean"},
    "ready": {"type": "boolean"},
    "host": {"type": "string", "pattern": "^127(?:\\.(?:25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])){3}$"},
    "port": {"type": "integer", "minimum": 1, "maximum": 65535},
    "runtime_version": {"const": "r14.3-v1"}
  },
  "allOf": [
    {"if": {"properties": {"ready": {"const": true}}}, "then": {"properties": {"live": {"const": true}, "state": {"const": "ready"}}}},
    {"if": {"properties": {"state": {"const": "stopped"}}}, "then": {"properties": {"live": {"const": false}, "ready": {"const": false}}}}
  ]
}
''',
"tests/test_r14_3_local_backend_runtime.py": r'''from __future__ import annotations

import json
import socket
import time
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.backend.contracts import BackendEnvironmentIdentity, BackendEnvironmentKind, BackendServiceKind
from kodepoia.backend.health import BackendHealthSnapshot, BackendHealthState
from kodepoia.backend.intent import BackendProjectProfile
from kodepoia.backend.local_config import (
    BackendConfigOverlay,
    BackendLocalConfig,
    BackendLogLevel,
    local_config_from_runtime_intents,
)
from kodepoia.backend.runtime import BackendLocalRuntime
from kodepoia.backend.scaffold import BackendScaffoldEngine
from kodepoia.core.kill_switch import KillSwitch
from kodepoia.core.secrets import KodeSecrets, MemorySecretBackend

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "r14"


def _validator(name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _profile() -> BackendProjectProfile:
    return BackendProjectProfile(enabled=True, services=(BackendServiceKind.AUTH,))


def _config(*, port: int = 0, secret_refs=()) -> BackendLocalConfig:
    return local_config_from_runtime_intents(
        "r14_3_fixture",
        _profile().runtime_intents(),
        port=port,
        secret_refs=tuple(secret_refs),
    )


def test_r14_2_runtime_intents_bridge_to_deterministic_local_config() -> None:
    first = _config()
    second = _config()
    assert first == second
    assert first.digest() == second.digest()
    assert first.services == (BackendServiceKind.AUTH,)
    assert first.host == "127.0.0.1"
    assert first.port == 0


def test_empty_runtime_intents_do_not_manufacture_backend_workspace() -> None:
    with pytest.raises(ValueError, match="at least one R14.2 runtime intent"):
        local_config_from_runtime_intents("offline", ())


def test_non_loopback_and_privileged_bind_are_rejected() -> None:
    environment = BackendEnvironmentIdentity("local", BackendEnvironmentKind.LOCAL)
    with pytest.raises(ValueError, match="loopback"):
        BackendLocalConfig("demo", environment, (BackendServiceKind.AUTH,), host="0.0.0.0")
    with pytest.raises(ValueError, match="port"):
        BackendLocalConfig("demo", environment, (BackendServiceKind.AUTH,), port=80)


def test_environment_overlay_is_typed_and_cannot_widen_host() -> None:
    base = _config()
    test_environment = BackendEnvironmentIdentity("test", BackendEnvironmentKind.TEST)
    overlaid = BackendConfigOverlay(
        environment=test_environment,
        port=23456,
        log_level=BackendLogLevel.DEBUG,
    ).apply(base)
    assert overlaid.environment.kind is BackendEnvironmentKind.TEST
    assert overlaid.port == 23456
    assert overlaid.host == "127.0.0.1"
    assert overlaid.services == base.services


def test_config_roundtrip_is_strict_and_secret_ref_only() -> None:
    secrets = KodeSecrets(MemorySecretBackend())
    secrets.store("kodepoia.backend.test", "fixture-token", "VERY-SECRET-R14-3-VALUE")
    ref = secrets.ref("kodepoia.backend.test", "fixture-token")
    config = _config(secret_refs=(ref,))
    payload = config.canonical()
    config.assert_secret_boundary(secrets)
    serialized = json.dumps(payload, sort_keys=True)
    assert "VERY-SECRET-R14-3-VALUE" not in serialized
    assert "fixture-token" in serialized
    assert BackendLocalConfig.from_dict(payload) == config
    contaminated = dict(payload)
    contaminated["provider"] = "forbidden"
    with pytest.raises(ValueError, match="unknown or missing"):
        BackendLocalConfig.from_dict(contaminated)


def test_scaffold_generate_twice_is_byte_identical(tmp_path: Path) -> None:
    engine = BackendScaffoldEngine()
    config = _config()
    first = engine.generate(tmp_path, config)
    snapshot = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in sorted(tmp_path.rglob("*"))
        if path.is_file()
    }
    second = engine.generate(tmp_path, config)
    snapshot2 = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in sorted(tmp_path.rglob("*"))
        if path.is_file()
    }
    assert first == second
    assert first.digest() == second.digest()
    assert snapshot == snapshot2
    assert engine.load_config(tmp_path) == config
    assert engine.load_manifest(tmp_path) == first


def test_scaffold_refuses_divergent_owned_file(tmp_path: Path) -> None:
    engine = BackendScaffoldEngine()
    config = _config()
    engine.generate(tmp_path, config)
    readme = tmp_path / engine.README_PATH
    readme.write_text("user drift\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="refuses to overwrite"):
        engine.generate(tmp_path, config)


def test_r14_3_schemas_accept_canonical_documents() -> None:
    config = _config()
    engine = BackendScaffoldEngine()
    _rendered, manifest = engine.render(config)
    health = BackendHealthSnapshot(
        service_id="r14_3_fixture.local",
        environment_id="local",
        state=BackendHealthState.READY,
        live=True,
        ready=True,
        host="127.0.0.1",
        port=34567,
    )
    _validator("backend-local-config.schema.json").validate(config.canonical())
    _validator("backend-workspace-manifest.schema.json").validate(manifest.canonical())
    _validator("backend-health-snapshot.schema.json").validate(health.canonical())


def test_local_runtime_start_health_stop_is_bounded_and_killswitch_owned(tmp_path: Path) -> None:
    switch = KillSwitch()
    secrets = KodeSecrets(MemorySecretBackend())
    runtime = BackendLocalRuntime(tmp_path, secrets=secrets, kill_switch=switch)
    started = time.monotonic()
    handle = runtime.start(_config(), startup_timeout=10.0)
    try:
        assert time.monotonic() - started < 10.0
        assert switch.active_count == 1
        health = runtime.probe(handle)
        assert health.state is BackendHealthState.READY
        assert health.live is True
        assert health.ready is True
        assert health.host == "127.0.0.1"
        assert 1 <= health.port <= 65535
    finally:
        stopped = runtime.stop(handle, shutdown_timeout=5.0)
    assert stopped.state is BackendHealthState.STOPPED
    assert stopped.live is False
    assert stopped.ready is False
    assert switch.active_count == 0


def test_runtime_never_persists_or_logs_resolved_secret_value(tmp_path: Path) -> None:
    switch = KillSwitch()
    secrets = KodeSecrets(MemorySecretBackend())
    raw = "R14-3-SUPER-SECRET-MATERIAL"
    secrets.store("kodepoia.backend.test", "api-key", raw)
    ref = secrets.ref("kodepoia.backend.test", "api-key")
    runtime = BackendLocalRuntime(tmp_path, secrets=secrets, kill_switch=switch)
    handle = runtime.start(_config(secret_refs=(ref,)), startup_timeout=10.0)
    try:
        assert raw not in runtime.redacted_log(handle)
        for path in tmp_path.rglob("*"):
            if path.is_file():
                assert raw.encode("utf-8") not in path.read_bytes()
    finally:
        runtime.stop(handle)


def test_production_environment_cannot_start_local_fixture(tmp_path: Path) -> None:
    base = _config()
    production = BackendConfigOverlay(
        environment=BackendEnvironmentIdentity("production", BackendEnvironmentKind.PRODUCTION)
    ).apply(base)
    runtime = BackendLocalRuntime(
        tmp_path,
        secrets=KodeSecrets(MemorySecretBackend()),
        kill_switch=KillSwitch(),
    )
    with pytest.raises(PermissionError, match="LOCAL or TEST"):
        runtime.start(production)


def test_fixed_port_conflict_fails_closed_and_cleans_process(tmp_path: Path) -> None:
    switch = KillSwitch()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        port = int(occupied.getsockname()[1])
        runtime = BackendLocalRuntime(
            tmp_path,
            secrets=KodeSecrets(MemorySecretBackend()),
            kill_switch=switch,
        )
        with pytest.raises(RuntimeError, match="exited before readiness"):
            runtime.start(_config(port=port), startup_timeout=5.0)
    assert switch.active_count == 0
''',
"docs/roadmap/R14_3_DESIGN.md": r'''# R14.3 — Deterministic local backend scaffold/runtime design

## Scope

R14.3 provides only a reproducible **local/test** backend development surface. It does not implement authentication semantics, database persistence, authoritative gameplay/application logic, matchmaking, billing, public deployment, production TLS termination or managed hosting.

## Reused authorities

- `kodepoia.core.sandbox.ProcessSandbox` + `ManagedProcess` own the child process and register it with the existing KillSwitch.
- `kodepoia.core.secrets.KodeSecrets` / `SecretRef` remain the only secret boundary. Durable config contains references, never resolved values.
- R12 scaffold invariants are preserved: canonical bytes, SHA-256 lineage, sorted manifests, fail-closed path ownership and idempotent regeneration.
- R14.1 environment/service identities remain canonical; R14.2 `BackendRuntimeIntent` is the only bridge that can create a local backend config.

## Runtime architecture

`BackendLocalConfig` is strict and provider-neutral. It requires at least one R14.2 runtime intent, an explicit environment identity, IPv4 loopback bind, port `0` or an unprivileged fixed port, a typed log level and optional `SecretRef` values. Environment overlays may change environment/port/log level/secret references but cannot widen the bind address or mutate selected services.

`BackendScaffoldEngine` generates a canonical `.kodepoia/backend/runtime.json`, a deterministic workspace manifest and an explanatory README. Generation is idempotent; an already-owned file with divergent bytes is a hard conflict rather than an implicit overwrite.

`BackendLocalRuntime` starts the repository-owned module `kodepoia.backend.local_fixture_server` through `ProcessSandbox`, never through an arbitrary executable or shell command. The server binds loopback only, writes a bounded ready record, exposes `/healthz`, `/readyz` and `/livez`, and supports a loopback-only internal graceful shutdown request. Shutdown is attempted gracefully first and always falls back to the existing bounded ManagedProcess/KillSwitch cleanup.

Python 3.12 documents `ThreadingHTTPServer` as a basic threaded HTTP server and explicitly warns that `http.server` is not recommended for production. The same documentation shows explicit `--bind 127.0.0.1` usage. R14.3 therefore treats this server strictly as a deterministic local/test fixture, never as a production service.

Official reference: https://docs.python.org/3.12/library/http.server.html

## Secret boundary

No resolved secret is passed to the child process. Config and manifests retain `SecretRef(namespace,key)` only. Runtime logs contain service/config identity and secret-reference count, not values. `KodeSecrets.redact()` remains a defense-in-depth read boundary.

OWASP recommends centralized/controlled secret handling, notes that environment variables can leak through process/log/system surfaces, and states that secrets must never be logged. R14.3 therefore does not use environment variables as a secret transport.

Official reference: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html

## Failure semantics

- non-loopback bind: rejected before launch;
- privileged fixed port: rejected before launch;
- occupied fixed port: child exits, parent fails closed and unregisters the process;
- `staging`/`production`: representable by typed config overlays but forbidden from starting this local fixture;
- divergent generated file: fail closed;
- readiness timeout or early exit: ManagedProcess cleanup is mandatory;
- KillSwitch activation: existing global/injected process governance remains authoritative.

## Acceptance evidence

Focused tests cover R14.2-to-R14.3 intent bridging, deterministic config/scaffold digests, strict schemas, environment overlays, secret-reference-only durability, byte-identical double generation, ownership conflicts, loopback policy, bounded start/health/stop, KillSwitch ownership, production refusal and fixed-port collision cleanup on supported CI hosts.
''',
"docs/roadmap/R14_3_ACCEPTANCE.md": r'''# R14.3 — Acceptance evidence ledger

## Current state

**Status: IMPLEMENTATION_CANDIDATE_PENDING**

R14.3 starts exactly from R14.2 normalized `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d` on `r14/03-local-backend-runtime`. Mandatory START-sync completed before implementation on head `86dd7e43a2d2895909f8ecd95a743099fc37c55f`; cumulative START-sync changes are exactly `docs/roadmap/R14_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md`.

## Frozen claims

R14.3 may claim only:

- deterministic local/test backend workspace generation;
- typed provider-neutral local config and environment overlays;
- KodeSecrets reference-only durable configuration;
- loopback-first repository-owned fixture runtime;
- ProcessSandbox/KillSwitch process ownership;
- liveness/readiness/health observations;
- graceful-first bounded shutdown with governed fallback;
- deterministic scaffold/config/manifest identity and redacted logs.

R14.3 does not claim production serving, public deployment, production TLS, provider hosting, authentication semantics, database implementation, matchmaking, cloud saves, commerce, flags, content delivery, event ingestion or LiveOps.

## Required focused assertions

- zero R14.2 runtime intents cannot manufacture a backend workspace;
- enabled R14.2 runtime intents produce deterministic R14.3 local config;
- non-loopback and privileged bind requests are rejected;
- environment overlay cannot widen host or mutate service selection;
- raw secret values never enter config, manifest, generated files or runtime log;
- strict Draft 2020-12 config/manifest/health schemas accept canonical documents and reject extra fields;
- generate twice yields byte-identical tree and identical manifest digest;
- divergent owned file is not silently overwritten;
- runtime starts on loopback with ephemeral port and reaches READY within a bounded window;
- health/readiness/liveness are observable without external network access;
- runtime is registered with KillSwitch while active and unregistered after stop;
- graceful stop completes in a bounded window with ManagedProcess fallback;
- staging/production config cannot start the R14.3 local fixture;
- occupied fixed port fails closed and leaves no governed process behind;
- Windows and Ubuntu focused execution both pass before technical acceptance.

## Required technical candidate gates

After focused prevalidation, the first accepted immutable implementation candidate must bind one unchanged SHA to fresh:

1. R0 Repository Guard — COMPLETED / SUCCESS.
2. full Python Core — COMPLETED / SUCCESS, including Ubuntu/Windows core, both package builds and internal KodeStudio smoke.
3. KodeStudio UI Smoke — COMPLETED / SUCCESS.

Then END-sync may change only `R14_PLAN.md`, this ledger and continuity before fresh exact-head re-gates, merge with expected-head protection and exactly one continuity-only post-merge normalization.

## Manual intervention

**NONE.** No provider account, secret, paid quota, public endpoint, production certificate, managed host or device is required for R14.3 acceptance.
''',
}

for relative, content in FILES.items():
    path = Path(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise SystemExit(f"refusing to overwrite existing new R14.3 file: {relative}")
    path.write_text(content, encoding="utf-8", newline="\n")

init = Path("src/kodepoia/backend/__init__.py")
s = init.read_text(encoding="utf-8")
needle = "from .status import BackendErrorCode, BackendOperationStatus, BackendStatusSnapshot\n"
addition = '''from .health import BackendHealthSnapshot, BackendHealthState, probe_backend_health\nfrom .local_config import (\n    BackendConfigOverlay,\n    BackendLocalConfig,\n    BackendLogLevel,\n    local_config_from_runtime_intents,\n)\nfrom .runtime import BackendLocalRuntime, BackendRuntimeHandle\nfrom .scaffold import (\n    BackendRenderedFile,\n    BackendScaffoldEngine,\n    BackendWorkspaceManifest,\n)\n'''
if needle not in s:
    raise SystemExit("backend __init__ import marker not found")
s = s.replace(needle, addition + needle, 1)
exports = [
    "BackendConfigOverlay",
    "BackendHealthSnapshot",
    "BackendHealthState",
    "BackendLocalConfig",
    "BackendLocalRuntime",
    "BackendLogLevel",
    "BackendRenderedFile",
    "BackendRuntimeHandle",
    "BackendScaffoldEngine",
    "BackendWorkspaceManifest",
    "local_config_from_runtime_intents",
    "probe_backend_health",
]
marker = '    "canonical_json_bytes",\n'
if marker not in s:
    raise SystemExit("backend __init__ export marker not found")
s = s.replace(marker, "".join(f'    "{name}",\n' for name in exports) + marker, 1)
init.write_text(s, encoding="utf-8", newline="\n")

print(f"R14.3 core patch wrote {len(FILES)} new files and updated backend exports")
