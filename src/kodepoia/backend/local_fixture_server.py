from __future__ import annotations

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
