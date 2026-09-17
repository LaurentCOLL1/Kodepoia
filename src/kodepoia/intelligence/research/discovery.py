from __future__ import annotations

import hashlib
import http.client
import json
import socket
import ssl
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode, urlsplit

from kodepoia.core.guardian import ActionRequest, ActionType, DecisionKind, KodeGuardian
from kodepoia.core.permissions import Capability, PermissionGrant, PermissionSet
from kodepoia.core.secrets import KodeSecrets
from kodepoia.exceptions import PermissionDenied
from kodepoia.intelligence.research.github import (
    GITHUB_API_HOST,
    GITHUB_API_VERSION,
    GitHubApiTransport,
    GitHubCredentialRef,
)
from kodepoia.intelligence.research.service import (
    ResearchCancellation,
    ResearchCancelled,
    ResearchOperationStatus,
    ResearchServiceResult,
    ResearchViewItem,
)
from kodepoia.intelligence.research.web import (
    RawWebResponse,
    ResolvedWebTarget,
    Resolver,
    SingleRequestTransport,
    WebPolicy,
    WebPolicyViolation,
    WebTransportError,
    _PinnedHTTPSConnection,
    resolve_public_target,
    validate_raw_web_response,
)

BRAVE_API_HOST = "api.search.brave.com"
BRAVE_CREDENTIAL_NAMESPACE = "brave"
BRAVE_CREDENTIAL_KEY = "search_api_key"


def _candidate_id(provider_id: str, locator: str) -> str:
    return hashlib.sha256(f"{provider_id}\0{locator}".encode("utf-8")).hexdigest()


def _header_int(response: RawWebResponse, name: str) -> int | None:
    value = response.header(name).strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class DiscoveryProviderState:
    provider_id: str
    status: str
    reason: str = ""
    authentication: str = "not-required"
    result_count: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "status": self.status,
            "reason": self.reason,
            "authentication": self.authentication,
            "result_count": self.result_count,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class BraveSearchTransport:
    """Pinned HTTPS transport for Brave Search; the API key never enters a locator."""

    guardian: KodeGuardian
    api_key: str
    user_agent: str = "KodepoiaResearch/0.1"

    def send(self, target: ResolvedWebTarget, *, policy: WebPolicy) -> RawWebResponse:
        if target.scheme != "https" or target.hostname != BRAVE_API_HOST or target.port != 443:
            raise WebPolicyViolation("Brave Search transport is bound to https://api.search.brave.com:443")
        decision = self.guardian.authorize(
            ActionRequest(
                action=ActionType.NETWORK,
                actor="KodeResearch.BraveDiscovery",
                target=target.normalized_url,
                metadata={"host": target.hostname, "port": target.port},
            )
        )
        if decision.kind is not DecisionKind.ALLOW:
            raise PermissionDenied(f"Guardian denied Brave discovery: {decision.reason}")

        parsed = urlsplit(target.normalized_url)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        headers = {
            "Host": target.host_header,
            "User-Agent": self.user_agent,
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key,
            "Accept-Encoding": "identity",
            "Connection": "close",
        }
        connection = _PinnedHTTPSConnection(
            target.address,
            server_hostname=target.hostname,
            port=443,
            timeout=policy.timeout_seconds,
            context=ssl.create_default_context(),
        )
        try:
            connection.request("GET", path, headers=headers)
            response = connection.getresponse()
            response_headers = {key: value for key, value in response.getheaders()}
            content_encoding = response.getheader("Content-Encoding", "").strip().lower()
            if content_encoding not in {"", "identity"}:
                raise WebPolicyViolation("Encoded/compressed Brave Search responses are not accepted")
            content_length = response.getheader("Content-Length")
            if content_length:
                try:
                    declared = int(content_length)
                except ValueError:
                    declared = -1
                if declared > policy.max_response_bytes:
                    raise WebPolicyViolation("Brave Search Content-Length exceeds configured limit")
            body = response.read(policy.max_response_bytes + 1)
            if len(body) > policy.max_response_bytes:
                raise WebPolicyViolation("Brave Search response exceeds configured byte limit")
            return RawWebResponse(
                url=target.normalized_url,
                status_code=int(response.status),
                headers=response_headers,
                body=body,
            )
        except (socket.timeout, TimeoutError) as exc:
            raise WebTransportError("Brave Search request timed out") from exc
        except (OSError, http.client.HTTPException, ssl.SSLError) as exc:
            raise WebTransportError(f"Brave Search request failed: {type(exc).__name__}") from exc
        finally:
            connection.close()


@dataclass(slots=True)
class ResearchDiscoveryService:
    """Question-driven discovery that emits descriptor-only candidates, never evidence."""

    project_root: Path
    allow_network: bool = False
    secrets: KodeSecrets | None = None
    brave_transport: SingleRequestTransport | None = None
    github_transport: SingleRequestTransport | None = None
    resolver: Resolver | None = None
    policy: WebPolicy = field(
        default_factory=lambda: WebPolicy(
            allowed_ports=(443,),
            allowed_mime_types=("application/json", "application/vnd.github+json"),
            max_response_bytes=2 * 1024 * 1024,
        )
    )

    def __post_init__(self) -> None:
        self.project_root = Path(self.project_root).resolve(strict=False)

    def _guardian(self) -> KodeGuardian:
        permissions = PermissionSet()
        permissions.grant(PermissionGrant(Capability.NETWORK))
        return KodeGuardian(permissions)

    def _resolve(self, url: str) -> ResolvedWebTarget:
        if self.resolver is None:
            return resolve_public_target(url, policy=self.policy)
        return resolve_public_target(url, policy=self.policy, resolver=self.resolver)

    def _secret(self, namespace: str, key: str) -> str | None:
        if self.secrets is None:
            return None
        try:
            value = self.secrets.delegated_get(namespace, key)
        except Exception:
            return None
        return value or None

    @staticmethod
    def _decode_json(response: RawWebResponse, provider_id: str) -> Any:
        validate_raw_web_response(response, policy=WebPolicy(
            allowed_ports=(443,),
            allowed_mime_types=("application/json", "application/vnd.github+json"),
            max_response_bytes=2 * 1024 * 1024,
        ))
        try:
            return json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WebPolicyViolation(f"{provider_id} discovery response is not valid UTF-8 JSON") from exc

    @staticmethod
    def _candidate(
        *,
        provider_id: str,
        source_kind: str,
        locator: str,
        title: str,
        snippet: str,
        rank: int,
    ) -> ResearchViewItem:
        clean_locator = locator.strip()
        return ResearchViewItem(
            source_kind=source_kind,
            source_id=_candidate_id(provider_id, clean_locator),
            locator=clean_locator,
            status=ResearchOperationStatus.READY,
            freshness="unfetched",
            trust="candidate-only",
            title=title.strip(),
            text=snippet.strip()[:4000],
            reason=f"descriptor_only_not_fetched:{provider_id}:rank={rank}",
        )

    def _discover_brave(self, query: str, limit: int) -> tuple[DiscoveryProviderState, tuple[ResearchViewItem, ...]]:
        api_key = self._secret(BRAVE_CREDENTIAL_NAMESPACE, BRAVE_CREDENTIAL_KEY)
        if not api_key and self.brave_transport is None:
            return (
                DiscoveryProviderState(
                    "brave-web",
                    "auth-required",
                    reason="brave_search_api_key_missing",
                    authentication="required",
                ),
                (),
            )
        url = f"https://{BRAVE_API_HOST}/res/v1/web/search?{urlencode({'q': query, 'count': limit})}"
        transport = self.brave_transport or BraveSearchTransport(self._guardian(), api_key or "")
        response = transport.send(self._resolve(url), policy=self.policy)
        if response.status_code in {401, 402}:
            return DiscoveryProviderState("brave-web", "auth-required", "brave_authentication_failed", "required"), ()
        if response.status_code == 429:
            return DiscoveryProviderState(
                "brave-web",
                "rate-limited",
                "brave_rate_limited",
                "required",
                metadata={"retry_after": response.header("Retry-After")},
            ), ()
        if response.status_code < 200 or response.status_code >= 300:
            return DiscoveryProviderState(
                "brave-web", "unavailable", f"brave_http_status_{response.status_code}", "required"
            ), ()
        payload = self._decode_json(response, "brave-web")
        raw_results = payload.get("web", {}).get("results", []) if isinstance(payload, dict) else []
        if not isinstance(raw_results, list):
            raise WebPolicyViolation("Brave discovery web.results is not an array")
        items: list[ResearchViewItem] = []
        for rank, item in enumerate(raw_results[:limit], start=1):
            if not isinstance(item, dict):
                continue
            locator = str(item.get("url", "")).strip()
            if not locator.startswith(("https://", "http://")):
                continue
            items.append(
                self._candidate(
                    provider_id="brave-web",
                    source_kind="web",
                    locator=locator,
                    title=str(item.get("title", "")),
                    snippet=str(item.get("description", "")),
                    rank=rank,
                )
            )
        return DiscoveryProviderState(
            "brave-web", "ready", authentication="required", result_count=len(items)
        ), tuple(items)

    def _discover_github(self, query: str, limit: int) -> tuple[DiscoveryProviderState, tuple[ResearchViewItem, ...]]:
        token = self._secret("github", "api_token")
        if self.github_transport is None:
            credential = GitHubCredentialRef("github", "api_token") if token else None
            transport: SingleRequestTransport = GitHubApiTransport(
                self._guardian(),
                secrets=self.secrets,
                credential_ref=credential,
            )
        else:
            transport = self.github_transport
        url = f"https://{GITHUB_API_HOST}/search/repositories?{urlencode({'q': query, 'per_page': limit})}"
        response = transport.send(self._resolve(url), policy=self.policy)
        if response.status_code == 401:
            return DiscoveryProviderState(
                "github-public", "auth-required", "github_authentication_failed", "optional"
            ), ()
        remaining = _header_int(response, "X-RateLimit-Remaining")
        if response.status_code == 429 or (response.status_code == 403 and remaining == 0):
            return DiscoveryProviderState(
                "github-public",
                "rate-limited",
                "github_search_rate_limited",
                "optional",
                metadata={
                    "rate_limit_remaining": remaining,
                    "rate_limit_reset": _header_int(response, "X-RateLimit-Reset"),
                    "retry_after": response.header("Retry-After"),
                },
            ), ()
        if response.status_code < 200 or response.status_code >= 300:
            return DiscoveryProviderState(
                "github-public", "unavailable", f"github_http_status_{response.status_code}", "optional"
            ), ()
        payload = self._decode_json(response, "github-public")
        raw_results = payload.get("items", []) if isinstance(payload, dict) else []
        if not isinstance(raw_results, list):
            raise WebPolicyViolation("GitHub discovery items is not an array")
        items: list[ResearchViewItem] = []
        for rank, item in enumerate(raw_results[:limit], start=1):
            if not isinstance(item, dict):
                continue
            locator = str(item.get("html_url", "")).strip()
            if not locator.startswith("https://github.com/"):
                continue
            items.append(
                self._candidate(
                    provider_id="github-public",
                    source_kind="github",
                    locator=locator,
                    title=str(item.get("full_name", item.get("name", ""))),
                    snippet=str(item.get("description") or ""),
                    rank=rank,
                )
            )
        metadata = {
            "rate_limit_remaining": remaining,
            "rate_limit_reset": _header_int(response, "X-RateLimit-Reset"),
            "authenticated": bool(token),
        }
        return DiscoveryProviderState(
            "github-public", "ready", authentication="optional", result_count=len(items), metadata=metadata
        ), tuple(items)

    def discover(
        self,
        query: str,
        *,
        limit: int = 10,
        cancellation: ResearchCancellation | None = None,
    ) -> ResearchServiceResult:
        wanted = " ".join(query.split()).strip()
        if not wanted:
            raise ValueError("Discovery query must not be empty")
        if not 1 <= limit <= 20:
            raise ValueError("Discovery limit must be between 1 and 20")
        token = cancellation or ResearchCancellation()
        if not self.allow_network:
            states = (
                DiscoveryProviderState("brave-web", "network-restricted", "network_permission_not_granted", "required"),
                DiscoveryProviderState("github-public", "network-restricted", "network_permission_not_granted", "optional"),
            )
            return ResearchServiceResult(
                "discover",
                ResearchOperationStatus.BLOCKED,
                reason="network_permission_not_granted",
                metadata={
                    "candidate_only": True,
                    "fetched": False,
                    "persisted": False,
                    "providers": [state.to_dict() for state in states],
                },
            )
        try:
            token.require_active()
            states: list[DiscoveryProviderState] = []
            items: list[ResearchViewItem] = []
            for operation in (self._discover_brave, self._discover_github):
                token.require_active()
                try:
                    state, provider_items = operation(wanted, limit)
                except PermissionDenied as exc:
                    state, provider_items = DiscoveryProviderState(
                        "brave-web" if operation == self._discover_brave else "github-public",
                        "network-restricted",
                        str(exc),
                    ), ()
                except (WebPolicyViolation, WebTransportError) as exc:
                    state, provider_items = DiscoveryProviderState(
                        "brave-web" if operation == self._discover_brave else "github-public",
                        "unavailable",
                        str(exc),
                    ), ()
                states.append(state)
                items.extend(provider_items)
            token.require_active()
        except ResearchCancelled:
            return ResearchServiceResult(
                "discover",
                ResearchOperationStatus.CANCELLED,
                reason="cancelled",
                metadata={"candidate_only": True, "fetched": False, "persisted": False},
            )

        ready_states = [state for state in states if state.status == "ready"]
        if ready_states:
            status = ResearchOperationStatus.READY
            reason = "discovery_completed" if len(ready_states) == len(states) else "discovery_partial"
        else:
            status = ResearchOperationStatus.BLOCKED if any(
                state.status in {"network-restricted", "auth-required"} for state in states
            ) else ResearchOperationStatus.UNAVAILABLE
            reason = "discovery_providers_unavailable"
        deduplicated: list[ResearchViewItem] = []
        seen: set[str] = set()
        for item in items:
            if item.locator in seen:
                continue
            seen.add(item.locator)
            deduplicated.append(item)
            if len(deduplicated) >= limit:
                break
        return ResearchServiceResult(
            "discover",
            status,
            items=tuple(deduplicated),
            reason=reason,
            metadata={
                "query_sha256": hashlib.sha256(wanted.encode("utf-8")).hexdigest(),
                "candidate_only": True,
                "fetched": False,
                "persisted": False,
                "result_count": len(deduplicated),
                "providers": [state.to_dict() for state in states],
            },
        )
