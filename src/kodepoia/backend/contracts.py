from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_HOST_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _stable_id(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable identifier")
    return value


def _bounded_text(value: str, *, field: str, maximum: int = 512) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > maximum
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise ValueError(f"{field} must be non-empty, bounded text")
    return value


def _sha256(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be lowercase SHA-256")
    return value


def _normalize_host(value: str) -> str:
    _bounded_text(value, field="host", maximum=253)
    if any(char in value for char in "/\\@?#"):
        raise ValueError("host must be a bare host name or IP literal")
    try:
        return ipaddress.ip_address(value).compressed.lower()
    except ValueError:
        pass
    if ":" in value:
        raise ValueError("host must be a valid host name or IP literal")
    try:
        ascii_host = value.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError("host must be a valid IDNA host name") from exc
    if len(ascii_host) > 253 or ascii_host.startswith(".") or ascii_host.endswith("."):
        raise ValueError("host must be a bounded fully specified host name")
    labels = ascii_host.split(".")
    if len(labels) < 2 or any(_HOST_LABEL_RE.fullmatch(label) is None for label in labels):
        raise ValueError("host must be a valid fully specified host name")
    return ascii_host


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        text = json.dumps(
            dict(payload),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("backend canonical payload is not serializable") from exc
    return text.encode("utf-8")


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


class BackendEnvironmentKind(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class BackendServiceKind(StrEnum):
    AUTH = "auth"
    DATABASE = "database"
    AUTHORITATIVE_SERVER = "authoritative_server"
    MATCHMAKING = "matchmaking"
    CLOUD_SAVE = "cloud_save"
    PROGRESSION = "progression"
    ENTITLEMENT = "entitlement"
    REMOTE_CONFIG = "remote_config"
    CONTENT_DELIVERY = "content_delivery"
    EVENTS = "events"
    LIVEOPS = "liveops"


class BackendCapabilityState(StrEnum):
    NOT_PROBED = "NOT_PROBED"
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class BackendEnvironmentIdentity:
    environment_id: str
    kind: BackendEnvironmentKind

    def __post_init__(self) -> None:
        _stable_id(self.environment_id, field="environment_id")

    def canonical(self) -> dict[str, Any]:
        return {"environment_id": self.environment_id, "kind": self.kind.value}

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class BackendServiceIdentity:
    service_id: str
    service_kind: BackendServiceKind
    provider_id: str = "provider-neutral"

    def __post_init__(self) -> None:
        _stable_id(self.service_id, field="service_id")
        _stable_id(self.provider_id, field="provider_id")

    def canonical(self) -> dict[str, Any]:
        return {
            "service_id": self.service_id,
            "service_kind": self.service_kind.value,
            "provider_id": self.provider_id,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class BackendRuntimeBudget:
    connect_timeout_ms: int = 2_000
    read_timeout_ms: int = 5_000
    total_timeout_ms: int = 10_000
    max_retries: int = 1
    retry_backoff_ms: int = 250
    max_response_bytes: int = 4 * 1024 * 1024

    def __post_init__(self) -> None:
        bounded = {
            "connect_timeout_ms": (self.connect_timeout_ms, 1, 60_000),
            "read_timeout_ms": (self.read_timeout_ms, 1, 300_000),
            "total_timeout_ms": (self.total_timeout_ms, 1, 600_000),
            "max_retries": (self.max_retries, 0, 8),
            "retry_backoff_ms": (self.retry_backoff_ms, 0, 60_000),
            "max_response_bytes": (self.max_response_bytes, 1, 64 * 1024 * 1024),
        }
        for field, (value, minimum, maximum) in bounded.items():
            if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
                raise ValueError(f"{field} must be an integer in [{minimum}, {maximum}]")
        if self.total_timeout_ms < self.connect_timeout_ms:
            raise ValueError("total_timeout_ms cannot be shorter than connect_timeout_ms")
        if self.total_timeout_ms < self.read_timeout_ms:
            raise ValueError("total_timeout_ms cannot be shorter than read_timeout_ms")

    def canonical(self) -> dict[str, Any]:
        return {
            "connect_timeout_ms": self.connect_timeout_ms,
            "read_timeout_ms": self.read_timeout_ms,
            "total_timeout_ms": self.total_timeout_ms,
            "max_retries": self.max_retries,
            "retry_backoff_ms": self.retry_backoff_ms,
            "max_response_bytes": self.max_response_bytes,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class BackendEndpointDefinition:
    endpoint_id: str
    service_id: str
    environment_id: str
    scheme: str
    host: str
    port: int
    base_path: str = "/"
    allow_redirects: bool = False

    def __post_init__(self) -> None:
        _stable_id(self.endpoint_id, field="endpoint_id")
        _stable_id(self.service_id, field="service_id")
        _stable_id(self.environment_id, field="environment_id")
        normalized_scheme = self.scheme.lower() if isinstance(self.scheme, str) else ""
        if normalized_scheme not in {"http", "https"}:
            raise ValueError("scheme must be explicitly http or https")
        object.__setattr__(self, "scheme", normalized_scheme)
        object.__setattr__(self, "host", _normalize_host(self.host))
        if isinstance(self.port, bool) or not isinstance(self.port, int) or not 1 <= self.port <= 65535:
            raise ValueError("port must be an integer in [1, 65535]")
        if (
            not isinstance(self.base_path, str)
            or not self.base_path.startswith("/")
            or "?" in self.base_path
            or "#" in self.base_path
            or "\\" in self.base_path
            or any(ord(char) < 32 or ord(char) == 127 for char in self.base_path)
            or any(segment == ".." for segment in self.base_path.split("/"))
            or len(self.base_path) > 1024
        ):
            raise ValueError("base_path must be a bounded absolute path without traversal/query/fragment")
        if not isinstance(self.allow_redirects, bool):
            raise ValueError("allow_redirects must be boolean")

    def canonical(self) -> dict[str, Any]:
        return {
            "endpoint_id": self.endpoint_id,
            "service_id": self.service_id,
            "environment_id": self.environment_id,
            "scheme": self.scheme,
            "host": self.host,
            "port": self.port,
            "base_path": self.base_path,
            "allow_redirects": self.allow_redirects,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class BackendCapabilitySnapshot:
    snapshot_id: str
    environment_id: str
    provider_id: str
    state: BackendCapabilityState
    capabilities: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    service_digests: tuple[str, ...] = ()
    endpoint_digests: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.snapshot_id, field="snapshot_id")
        _stable_id(self.environment_id, field="environment_id")
        _stable_id(self.provider_id, field="provider_id")
        capabilities = tuple(sorted({_stable_id(item, field="capability") for item in self.capabilities}))
        blockers = tuple(sorted({_bounded_text(item, field="blocker", maximum=256) for item in self.blockers}))
        service_digests = tuple(sorted({_sha256(item, field="service_digest") for item in self.service_digests}))
        endpoint_digests = tuple(sorted({_sha256(item, field="endpoint_digest") for item in self.endpoint_digests}))
        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(self, "blockers", blockers)
        object.__setattr__(self, "service_digests", service_digests)
        object.__setattr__(self, "endpoint_digests", endpoint_digests)

        if self.state is BackendCapabilityState.AVAILABLE and not capabilities:
            raise ValueError("AVAILABLE requires at least one observed capability")
        if self.state is BackendCapabilityState.DEGRADED and (not capabilities or not blockers):
            raise ValueError("DEGRADED requires capabilities and blockers")
        if self.state in {
            BackendCapabilityState.UNAVAILABLE,
            BackendCapabilityState.UNSUPPORTED,
            BackendCapabilityState.BLOCKED,
            BackendCapabilityState.FAILED,
        } and not blockers:
            raise ValueError(f"{self.state.value} requires at least one blocker")
        if self.state is BackendCapabilityState.NOT_PROBED and (
            capabilities or service_digests or endpoint_digests
        ):
            raise ValueError("NOT_PROBED cannot contain observed capabilities or service/endpoint evidence")

    def canonical(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "environment_id": self.environment_id,
            "provider_id": self.provider_id,
            "state": self.state.value,
            "capabilities": list(self.capabilities),
            "blockers": list(self.blockers),
            "service_digests": list(self.service_digests),
            "endpoint_digests": list(self.endpoint_digests),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class BackendNetworkAuthorization:
    authorization_id: str
    endpoint_digest: str
    environment_id: str
    resolved_ips: tuple[str, ...]
    runtime_budget_digest: str
    redirects_allowed: bool = False

    def __post_init__(self) -> None:
        _stable_id(self.authorization_id, field="authorization_id")
        _sha256(self.endpoint_digest, field="endpoint_digest")
        _stable_id(self.environment_id, field="environment_id")
        _sha256(self.runtime_budget_digest, field="runtime_budget_digest")
        normalized: set[str] = set()
        for value in self.resolved_ips:
            try:
                normalized.add(ipaddress.ip_address(value).compressed.lower())
            except ValueError as exc:
                raise ValueError("resolved_ips must contain only IP literals") from exc
        if not normalized:
            raise ValueError("resolved_ips must contain at least one verified IP")
        object.__setattr__(self, "resolved_ips", tuple(sorted(normalized)))
        if self.redirects_allowed:
            raise ValueError("R14.1 network authorizations must keep redirects disabled")

    def canonical(self) -> dict[str, Any]:
        return {
            "authorization_id": self.authorization_id,
            "endpoint_digest": self.endpoint_digest,
            "environment_id": self.environment_id,
            "resolved_ips": list(self.resolved_ips),
            "runtime_budget_digest": self.runtime_budget_digest,
            "redirects_allowed": self.redirects_allowed,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())
