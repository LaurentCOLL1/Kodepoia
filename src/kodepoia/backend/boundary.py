from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from typing import Callable, Iterable

from .contracts import (
    BackendEndpointDefinition,
    BackendEnvironmentIdentity,
    BackendEnvironmentKind,
    BackendNetworkAuthorization,
    BackendRuntimeBudget,
    canonical_sha256,
)


class BackendBoundaryError(ValueError):
    """Raised when an R14 backend boundary rejects an operation."""


Resolver = Callable[[str, int], Iterable[str]]


def _default_resolver(host: str, port: int) -> tuple[str, ...]:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise BackendBoundaryError("backend endpoint DNS resolution failed") from exc
    return tuple(info[4][0] for info in infos)


@dataclass(frozen=True, slots=True)
class BackendNetworkPolicy:
    environment_id: str
    allowed_endpoint_ids: tuple[str, ...]
    allowed_hosts: tuple[str, ...]
    permit_loopback: bool = False
    permit_private: bool = False

    def __post_init__(self) -> None:
        if not self.environment_id or not isinstance(self.environment_id, str):
            raise ValueError("environment_id must be non-empty")
        endpoint_ids = tuple(sorted(set(self.allowed_endpoint_ids)))
        hosts = tuple(sorted({item.lower() for item in self.allowed_hosts}))
        if not endpoint_ids or not hosts:
            raise ValueError("network policy requires explicit endpoint and host allowlists")
        if any(not item or item != item.strip() for item in endpoint_ids + hosts):
            raise ValueError("network policy allowlists must contain bounded exact values")
        object.__setattr__(self, "allowed_endpoint_ids", endpoint_ids)
        object.__setattr__(self, "allowed_hosts", hosts)
        if not isinstance(self.permit_loopback, bool) or not isinstance(self.permit_private, bool):
            raise ValueError("network policy address exceptions must be boolean")


class BackendNetworkBoundary:
    """Fail-closed resolver/authorization boundary; it never performs HTTP traffic."""

    def __init__(
        self,
        *,
        environments: Iterable[BackendEnvironmentIdentity],
        endpoints: Iterable[BackendEndpointDefinition],
        policies: Iterable[BackendNetworkPolicy],
        resolver: Resolver | None = None,
    ) -> None:
        self._environments = self._index_unique(
            ((item.environment_id, item) for item in environments), "environment"
        )
        self._endpoints = self._index_unique(
            ((item.endpoint_id, item) for item in endpoints), "endpoint"
        )
        self._policies = self._index_unique(
            ((item.environment_id, item) for item in policies), "network policy"
        )
        self._resolver = resolver or _default_resolver

        for endpoint in self._endpoints.values():
            if endpoint.environment_id not in self._environments:
                raise BackendBoundaryError("endpoint references an unknown environment")
        for environment_id, policy in self._policies.items():
            environment = self._environments.get(environment_id)
            if environment is None:
                raise BackendBoundaryError("network policy references an unknown environment")
            if environment.kind in {BackendEnvironmentKind.STAGING, BackendEnvironmentKind.PRODUCTION} and (
                policy.permit_loopback or policy.permit_private
            ):
                raise BackendBoundaryError(
                    "staging/production network policy cannot permit loopback/private addresses"
                )

    @staticmethod
    def _index_unique(items: Iterable[tuple[str, object]], label: str) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise BackendBoundaryError(f"duplicate {label} identity")
            result[key] = value
        return result

    def authorize(
        self,
        endpoint_id: str,
        *,
        budget: BackendRuntimeBudget,
    ) -> BackendNetworkAuthorization:
        endpoint = self._endpoints.get(endpoint_id)
        if endpoint is None:
            raise BackendBoundaryError("backend endpoint is not registered")
        environment = self._environments[endpoint.environment_id]
        policy = self._policies.get(endpoint.environment_id)
        if policy is None:
            raise BackendBoundaryError("network is denied by default for this environment")
        if endpoint.endpoint_id not in policy.allowed_endpoint_ids:
            raise BackendBoundaryError("backend endpoint is not present in the exact allowlist")
        if endpoint.host not in policy.allowed_hosts:
            raise BackendBoundaryError("backend host is not present in the exact allowlist")
        if endpoint.allow_redirects:
            raise BackendBoundaryError("redirect-following is disabled by the R14.1 network boundary")
        if environment.kind in {BackendEnvironmentKind.STAGING, BackendEnvironmentKind.PRODUCTION}:
            if endpoint.scheme != "https":
                raise BackendBoundaryError("staging/production backend endpoints require HTTPS")

        resolved_ips = self._resolve_all(endpoint.host, endpoint.port)
        for address in resolved_ips:
            self._validate_address(address, environment=environment, policy=policy)

        seed = {
            "endpoint_digest": endpoint.digest(),
            "environment_id": endpoint.environment_id,
            "resolved_ips": list(resolved_ips),
            "runtime_budget_digest": budget.digest(),
            "redirects_allowed": False,
        }
        authorization_id = f"network.auth.{canonical_sha256(seed)[:24]}"
        return BackendNetworkAuthorization(
            authorization_id=authorization_id,
            endpoint_digest=endpoint.digest(),
            environment_id=endpoint.environment_id,
            resolved_ips=resolved_ips,
            runtime_budget_digest=budget.digest(),
            redirects_allowed=False,
        )

    def _resolve_all(self, host: str, port: int) -> tuple[str, ...]:
        try:
            literal = ipaddress.ip_address(host)
        except ValueError:
            try:
                values = tuple(self._resolver(host, port))
            except BackendBoundaryError:
                raise
            except Exception as exc:
                raise BackendBoundaryError("backend endpoint resolver failed closed") from exc
        else:
            values = (literal.compressed,)

        normalized: set[str] = set()
        for value in values:
            try:
                normalized.add(ipaddress.ip_address(value).compressed.lower())
            except (TypeError, ValueError) as exc:
                raise BackendBoundaryError("resolver returned a non-IP result") from exc
        if not normalized:
            raise BackendBoundaryError("backend endpoint resolved to no addresses")
        return tuple(sorted(normalized))

    @staticmethod
    def _validate_address(
        address: str,
        *,
        environment: BackendEnvironmentIdentity,
        policy: BackendNetworkPolicy,
    ) -> None:
        ip = ipaddress.ip_address(address)
        if ip.is_unspecified or ip.is_multicast or ip.is_link_local or ip.is_reserved:
            raise BackendBoundaryError("backend endpoint resolved to a forbidden special-purpose address")
        if ip.is_loopback:
            if environment.kind not in {BackendEnvironmentKind.LOCAL, BackendEnvironmentKind.TEST}:
                raise BackendBoundaryError("loopback backend address is forbidden outside local/test")
            if not policy.permit_loopback:
                raise BackendBoundaryError("loopback backend address requires explicit local/test permission")
            return
        if ip.is_private:
            if environment.kind not in {BackendEnvironmentKind.LOCAL, BackendEnvironmentKind.TEST}:
                raise BackendBoundaryError("private backend address is forbidden outside local/test")
            if not policy.permit_private:
                raise BackendBoundaryError("private backend address requires explicit local/test permission")
            return
        if not ip.is_global:
            raise BackendBoundaryError("backend endpoint must resolve to a globally routable address")
