from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from kodepoia.capability_truth import build_capability_matrix
from kodepoia.kodestudio.research_ux import (
    ResearchUxTranslator,
    default_empty_state_text,
    discovery_state_text,
    provider_summary_text,
)


REQUIRED_CHECKS = (
    "saved-search-semantics",
    "discovery-honesty",
    "new-project-empty-state",
    "provider-state-visibility",
    "guarded-fetch-preserved",
    "localized-actionable-copy",
    "raw-json-secondary",
    "workspace-scope",
)


def _git_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
    ).strip().lower()


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def build_report(root: Path, *, source_sha: str) -> dict[str, Any]:
    matrix = {row["capability_id"]: row for row in build_capability_matrix()}
    ui_source = (root / "src" / "kodepoia" / "kodestudio" / "research_panel.py").read_text(encoding="utf-8")
    workspace = (root / "docs" / "roadmap" / "V2_1_RESEARCH_WORKSPACE.md").read_text(encoding="utf-8")
    template = json.loads(
        (root / "docs" / "roadmap" / "V2_1_1_ACCEPTANCE_TEMPLATE.json").read_text(encoding="utf-8")
    )
    en = ResearchUxTranslator(locale="en")
    pseudo = ResearchUxTranslator(locale="qps-ploc")
    default_state = default_empty_state_text(en, report_count=0)
    provider_summary = provider_summary_text(en)
    discovery_state = discovery_state_text(en)

    checks = [
        _check(
            "saved-search-semantics",
            matrix["research.saved-reports-search"]["runtime_state"] == "ready"
            and en.text("research_ux.saved.button") == "Search saved research"
            and "stored in this project" in en.text("research_ux.saved.description")
            and "does not search the Internet" in en.text("research_ux.saved.description"),
            "Saved research remains a local persisted-report query and is labeled as such.",
        ),
        _check(
            "discovery-honesty",
            matrix["research.web-discovery"]["runtime_state"] == "not-implemented"
            and en.text("research_ux.discovery.button") == "Search sources"
            and "researchDiscoveryButton" in ui_source
            and "discovery_button.setEnabled(False)" in ui_source
            and "research.discover(" not in ui_source
            and "NOT IMPLEMENTED" in discovery_state,
            "V2.1.1 exposes discovery state without implementing or faking discovery.",
        ),
        _check(
            "new-project-empty-state",
            "No saved research exists in this project" in default_state
            and "Source discovery is not implemented" in default_state
            and "network-restricted" in default_state
            and "read-only credential" in default_state,
            "A new project explains saved-data, discovery, network and authentication states.",
        ),
        _check(
            "provider-state-visibility",
            "NOT-IMPLEMENTED" in provider_summary
            and "NETWORK-RESTRICTED" in provider_summary
            and "AUTH-REQUIRED" in provider_summary
            and "UNAVAILABLE" in provider_summary
            and "researchProviderSummary" in ui_source
            and "researchCapabilityDiagnostics" in ui_source,
            "Human-readable provider summary and detailed capability diagnostics use V2.0 truth states.",
        ),
        _check(
            "guarded-fetch-preserved",
            en.text("research_ux.fetch.button") == "Open/fetch source"
            and "request = ResearchFetchRequest" in ui_source
            and "research.fetch(request, cancellation=token)" in ui_source
            and "researchAllowNetwork" in ui_source,
            "Explicit-locator acquisition still uses the existing guarded ResearchService.fetch path.",
        ),
        _check(
            "localized-actionable-copy",
            pseudo.text("research_ux.saved.button").startswith("⟦")
            and pseudo.text("research_ux.discovery.button").startswith("⟦")
            and pseudo.text("research_ux.fetch.button").startswith("⟦")
            and "Check the explicit locator" in en.text("research_ux.fetch.blocked_action"),
            "New V2.1.1 labels/actions participate in the localization and pseudo-localization contract.",
        ),
        _check(
            "raw-json-secondary",
            "researchEmptyState" in ui_source
            and "researchProviderSummary" in ui_source
            and "researchTechnicalDetailsLabel" in ui_source
            and "details.setMaximumHeight(160)" in ui_source,
            "Human-readable state precedes bounded technical JSON details in the Research page.",
        ),
        _check(
            "workspace-scope",
            "V2.1.1 does **not** claim the full workflow complete" in workspace
            and "Search saved research" in workspace
            and "Search sources" in workspace
            and "Open/fetch source" in workspace
            and "V2.1.2 — Discovery providers" in workspace,
            "Implementation remains inside V2.1.1 and leaves real discovery to V2.1.2.",
        ),
    ]

    template_checks = tuple(template.get("required_checks") or ())
    template_ok = (
        template.get("schema") == "kodepoia.v2.1.1.acceptance-template"
        and int(template.get("schema_version", 0)) == 1
        and template.get("source_sha") == "<exact-40-char-commit-sha>"
        and template_checks == REQUIRED_CHECKS
    )
    if not template_ok:
        checks.append(
            _check(
                "acceptance-template",
                False,
                "V2.1.1 acceptance template does not match the required exact-head contract.",
            )
        )

    failed = [check["name"] for check in checks if check["status"] != "PASS"]
    return {
        "schema": "kodepoia.v2.1.1.acceptance",
        "schema_version": 1,
        "source_sha": source_sha,
        "status": "PASS" if not failed else "FAIL",
        "checks_total": len(checks),
        "checks_passed": len(checks) - len(failed),
        "failed_checks": failed,
        "checks": checks,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="V2.1.1 honest Research UX exact-head acceptance")
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
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
