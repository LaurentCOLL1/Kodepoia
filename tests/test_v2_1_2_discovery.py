from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from kodepoia.intelligence.research.discovery import ResearchDiscoveryService
from kodepoia.intelligence.research.service import ResearchOperationStatus
from kodepoia.intelligence.research.web import RawWebResponse, ResolvedWebTarget, WebPolicy


PUBLIC_TEST_IP = "93.184.216.34"


def _resolver(_hostname: str, _port: int) -> tuple[str, ...]:
    return (PUBLIC_TEST_IP,)


@dataclass
class FixtureTransport:
    status_code: int
    payload: object
    headers: dict[str, str] | None = None

    def send(self, target: ResolvedWebTarget, *, policy: WebPolicy) -> RawWebResponse:
        headers = {"Content-Type": "application/json", **(self.headers or {})}
        return RawWebResponse(
            url=target.normalized_url,
            status_code=self.status_code,
            headers=headers,
            body=json.dumps(self.payload).encode("utf-8"),
        )


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / ".kodepoia").mkdir(parents=True)
    return root


def test_discovery_is_network_restricted_without_explicit_permission(tmp_path: Path) -> None:
    service = ResearchDiscoveryService(_root(tmp_path), resolver=_resolver)
    result = service.discover("godot rendering")
    assert result.status is ResearchOperationStatus.BLOCKED
    assert not result.items
    assert result.metadata["candidate_only"] is True
    assert result.metadata["fetched"] is False
    assert result.metadata["persisted"] is False
    assert {provider["status"] for provider in result.metadata["providers"]} == {"network-restricted"}


def test_github_public_success_is_not_hidden_by_missing_brave_key(tmp_path: Path) -> None:
    github = FixtureTransport(
        200,
        {
            "items": [
                {
                    "full_name": "godotengine/godot",
                    "html_url": "https://github.com/godotengine/godot",
                    "description": "Godot Engine",
                }
            ]
        },
        headers={"X-RateLimit-Remaining": "9", "X-RateLimit-Reset": "1900000000"},
    )
    service = ResearchDiscoveryService(
        _root(tmp_path),
        allow_network=True,
        github_transport=github,
        resolver=_resolver,
    )
    result = service.discover("godot engine")
    assert result.status is ResearchOperationStatus.READY
    assert result.reason == "discovery_partial"
    assert len(result.items) == 1
    item = result.items[0]
    assert item.locator == "https://github.com/godotengine/godot"
    assert item.trust == "candidate-only"
    assert item.freshness == "unfetched"
    assert item.artifact_id == ""
    states = {provider["provider_id"]: provider for provider in result.metadata["providers"]}
    assert states["brave-web"]["status"] == "auth-required"
    assert states["github-public"]["status"] == "ready"


def test_brave_success_survives_explicit_github_rate_limit(tmp_path: Path) -> None:
    brave = FixtureTransport(
        200,
        {
            "web": {
                "results": [
                    {
                        "title": "Godot docs",
                        "url": "https://docs.godotengine.org/en/stable/",
                        "description": "Official documentation",
                    }
                ]
            }
        },
    )
    github = FixtureTransport(
        403,
        {"message": "API rate limit exceeded"},
        headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1900000000"},
    )
    service = ResearchDiscoveryService(
        _root(tmp_path),
        allow_network=True,
        brave_transport=brave,
        github_transport=github,
        resolver=_resolver,
    )
    result = service.discover("godot docs")
    assert result.status is ResearchOperationStatus.READY
    assert result.reason == "discovery_partial"
    assert [item.source_kind for item in result.items] == ["web"]
    states = {provider["provider_id"]: provider for provider in result.metadata["providers"]}
    assert states["brave-web"]["status"] == "ready"
    assert states["github-public"]["status"] == "rate-limited"
    assert states["github-public"]["metadata"]["rate_limit_remaining"] == 0


def test_provider_failures_never_become_empty_success(tmp_path: Path) -> None:
    github = FixtureTransport(
        429,
        {"message": "too many requests"},
        headers={"Retry-After": "60"},
    )
    service = ResearchDiscoveryService(
        _root(tmp_path),
        allow_network=True,
        github_transport=github,
        resolver=_resolver,
    )
    result = service.discover("anything")
    assert result.status is ResearchOperationStatus.BLOCKED
    assert not result.items
    assert result.reason == "discovery_providers_unavailable"
    states = {provider["provider_id"]: provider["status"] for provider in result.metadata["providers"]}
    assert states == {"brave-web": "auth-required", "github-public": "rate-limited"}
