from __future__ import annotations

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
