from __future__ import annotations

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
