from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kodepoia.capability_truth import build_capability_matrix
from kodepoia.intelligence.research.discovery import ResearchDiscoveryService
from kodepoia.intelligence.research.service import ResearchOperationStatus
from kodepoia.intelligence.research.web import RawWebResponse, ResolvedWebTarget, WebPolicy

REQUIRED_CHECKS = (
    "provider-contracts",
    "candidate-boundary",
    "partial-provider-failure",
    "provider-failure-not-empty-success",
    "ui-discovery-wiring",
    "guarded-fetch-separation",
    "capability-truth",
    "workspace-scope",
)
PUBLIC_TEST_IP = "93.184.216.34"


def _git_head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip().lower()


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def _resolver(_hostname: str, _port: int) -> tuple[str, ...]:
    return (PUBLIC_TEST_IP,)


@dataclass
class FixtureTransport:
    status_code: int
    payload: object
    headers: dict[str, str] | None = None

    def send(self, target: ResolvedWebTarget, *, policy: WebPolicy) -> RawWebResponse:
        return RawWebResponse(
            url=target.normalized_url,
            status_code=self.status_code,
            headers={"Content-Type": "application/json", **(self.headers or {})},
            body=json.dumps(self.payload).encode("utf-8"),
        )


def _fixture_results(root: Path) -> tuple[Any, Any]:
    project = root / ".kodepoia" / "acceptance" / "v2-1-2-fixture-project"
    (project / ".kodepoia").mkdir(parents=True, exist_ok=True)
    brave = FixtureTransport(
        200,
        {"web": {"results": [{"title": "Godot docs", "url": "https://docs.godotengine.org/en/stable/", "description": "Official docs"}]}},
    )
    github_rate_limited = FixtureTransport(
        403,
        {"message": "rate limit"},
        {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1900000000"},
    )
    partial = ResearchDiscoveryService(
        project,
        allow_network=True,
        brave_transport=brave,
        github_transport=github_rate_limited,
        resolver=_resolver,
    ).discover("godot docs")
    github_rate_limited_2 = FixtureTransport(
        429,
        {"message": "too many requests"},
        {"Retry-After": "60"},
    )
    failed = ResearchDiscoveryService(
        project,
        allow_network=True,
        github_transport=github_rate_limited_2,
        resolver=_resolver,
    ).discover("anything")
    return partial, failed


def build_report(root: Path, *, source_sha: str) -> dict[str, Any]:
    matrix = {row["capability_id"]: row for row in build_capability_matrix()}
    ui_source = (root / "src" / "kodepoia" / "kodestudio" / "research_panel.py").read_text(encoding="utf-8")
    discovery_source = (root / "src" / "kodepoia" / "intelligence" / "research" / "discovery.py").read_text(encoding="utf-8")
    workspace = (root / "docs" / "roadmap" / "V2_1_RESEARCH_WORKSPACE.md").read_text(encoding="utf-8")
    template = json.loads((root / "docs" / "roadmap" / "V2_1_2_ACCEPTANCE_TEMPLATE.json").read_text(encoding="utf-8"))
    partial, failed = _fixture_results(root)
    partial_states = {entry["provider_id"]: entry for entry in partial.metadata["providers"]}
    failed_states = {entry["provider_id"]: entry for entry in failed.metadata["providers"]}
    implementation_phase = "### V2.1.2 — Discovery providers — CURRENT" in workspace
    normalized_phase = "### V2.1.2 — Discovery providers — COMPLETE + NORMALIZED" in workspace
    discovery_mutation_boundary = (
        "candidate discovery alone performs no protected mutation" in workspace
        or "does not itself create evidence" in workspace
    )
    guarded_fetch_boundary = (
        "discovered URL still passes guarded fetch" in workspace
        or "Every acquisition still passes guarded fetch" in workspace
    )

    checks = [
        _check(
            "provider-contracts",
            "BRAVE_API_HOST = \"api.search.brave.com\"" in discovery_source
            and "X-Subscription-Token" in discovery_source
            and "/search/repositories" in discovery_source
            and "per_page" in discovery_source
            and "1 <= limit <= 20" in discovery_source,
            "Brave Web and official GitHub repository-search providers are bounded and explicit.",
        ),
        _check(
            "candidate-boundary",
            partial.status is ResearchOperationStatus.READY
            and len(partial.items) == 1
            and all(item.trust == "candidate-only" for item in partial.items)
            and all(item.freshness == "unfetched" for item in partial.items)
            and all(not item.artifact_id for item in partial.items)
            and partial.metadata["candidate_only"] is True
            and partial.metadata["fetched"] is False
            and partial.metadata["persisted"] is False,
            "Discovery emits descriptor-only candidates and does not create fetched/persisted evidence.",
        ),
        _check(
            "partial-provider-failure",
            partial.reason == "discovery_partial"
            and partial_states["brave-web"]["status"] == "ready"
            and partial_states["github-public"]["status"] == "rate-limited",
            "A useful provider result survives another provider's explicit rate-limit state.",
        ),
        _check(
            "provider-failure-not-empty-success",
            failed.status is not ResearchOperationStatus.READY
            and not failed.items
            and failed_states["brave-web"]["status"] == "auth-required"
            and failed_states["github-public"]["status"] == "rate-limited",
            "No-provider-success remains a blocked/unavailable state, never an empty success.",
        ),
        _check(
            "ui-discovery-wiring",
            "researchDiscoveryButton" in ui_source
            and "discovery.discover(query.text(), cancellation=token)" in ui_source
            and "discovery_status_text(" in ui_source
            and "candidate-only" in discovery_source,
            "KodeStudio Search sources invokes the discovery service and labels candidate-only results.",
        ),
        _check(
            "guarded-fetch-separation",
            "request = ResearchFetchRequest" in ui_source
            and "research.fetch(request, cancellation=token)" in ui_source
            and "discovery.fetch" not in ui_source
            and "ResearchService.fetch" not in discovery_source,
            "Discovery does not bypass or auto-invoke the existing guarded explicit-locator fetch.",
        ),
        _check(
            "capability-truth",
            set(matrix["research.web-discovery"]["classifications"]) == {"source-available", "experimental"}
            and matrix["research.web-discovery"]["runtime_state"] == "network-restricted"
            and matrix["research.github-discovery"]["runtime_state"] == "network-restricted"
            and "source-available" in matrix["research.github-discovery"]["classifications"],
            "Canonical V2 truth exposes live discovery source without claiming public rc8 or acceptance proof early.",
        ),
        _check(
            "workspace-scope",
            (implementation_phase or normalized_phase)
            and discovery_mutation_boundary
            and guarded_fetch_boundary,
            "V2.1.2 remains valid after normalization and later subdivisions while discovery/fetch boundaries stay explicit.",
        ),
    ]

    template_ok = (
        template.get("schema") == "kodepoia.v2.1.2.acceptance-template"
        and int(template.get("schema_version", 0)) == 1
        and template.get("source_sha") == "<exact-40-char-commit-sha>"
        and tuple(template.get("required_checks") or ()) == REQUIRED_CHECKS
    )
    if not template_ok:
        checks.append(_check("acceptance-template", False, "V2.1.2 acceptance template does not match the exact-head contract."))

    failed_checks = [check["name"] for check in checks if check["status"] != "PASS"]
    return {
        "schema": "kodepoia.v2.1.2.acceptance",
        "schema_version": 1,
        "source_sha": source_sha,
        "status": "PASS" if not failed_checks else "FAIL",
        "checks_total": len(checks),
        "checks_passed": len(checks) - len(failed_checks),
        "failed_checks": failed_checks,
        "checks": checks,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="V2.1.2 discovery providers exact-head acceptance")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = args.root.resolve(strict=True)
    expected = args.source_sha.strip().lower()
    actual = _git_head(root)
    if actual != expected:
        raise SystemExit(f"exact-source mismatch: expected {expected}, got {actual}")
    if len(expected) != 40 or any(character not in "0123456789abcdef" for character in expected):
        raise SystemExit("--source-sha must be an exact lowercase 40-character commit SHA")
    report = build_report(root, source_sha=expected)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
