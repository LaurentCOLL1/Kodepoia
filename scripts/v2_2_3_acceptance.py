from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True)


def _check(name: str, passed: bool, detail: str) -> dict[str, object]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Kodepoia V2.2.3 explainable Context Builder acceptance"
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    observed = _run(["git", "rev-parse", "HEAD"])
    observed_sha = observed.stdout.strip().lower()

    root = Path(__file__).resolve().parents[1]
    context = (
        root / "src/kodepoia/intelligence/project_context.py"
    ).read_text(encoding="utf-8")
    generic_context = (
        root / "src/kodepoia/intelligence/context.py"
    ).read_text(encoding="utf-8")
    preview = (
        root / "src/kodepoia/kodestudio/project_context_preview.py"
    ).read_text(encoding="utf-8")
    research_panel = (
        root / "src/kodepoia/kodestudio/research_panel.py"
    ).read_text(encoding="utf-8")
    authority = (
        root / "docs/roadmap/V2_2_PROJECT_KNOWLEDGE_CONTEXT_MEMORY.md"
    ).read_text(encoding="utf-8")

    targeted = _run(
        [
            "python",
            "-m",
            "pytest",
            "-q",
            "tests/test_v2_2_3_project_context.py",
            "tests/test_v2_2_3_context_ui.py",
        ]
    )
    targeted_detail = (
        "targeted V2.2.3 backend/UI tests passed"
        if targeted.returncode == 0
        else (targeted.stdout + targeted.stderr)[-4000:]
    )

    checks = [
        _check("exact_head", observed.returncode == 0 and observed_sha == source_sha, observed_sha),
        _check("v2_2_3_targeted_tests", targeted.returncode == 0, targeted_detail),
        _check(
            "context_candidate_contract",
            "class ProjectContextCandidate" in context
            and "retrieval_score" in context
            and "trust_classes" in context
            and "freshness" in context
            and "versions" in context
            and "estimated_tokens" in context,
            "candidate contract carries source/retrieval/trust/version/token metadata",
        ),
        _check(
            "selected_omitted_rationale",
            'SELECTED = "selected"' in context
            and 'OMITTED = "omitted"' in context
            and 'USER_EXCLUDED = "user_excluded"' in context
            and 'BUDGET_EXCEEDED = "budget_exceeded"' in context,
            "selected and omitted decisions expose deterministic reasons",
        ),
        _check(
            "budget_reuses_context_builder",
            "ContextBuilder(self.budget_tokens).build" in context
            and "selected_tokens" in context
            and "over_budget_tokens" in context,
            "existing ContextBuilder performs bounded assembly with explicit accounting",
        ),
        _check(
            "mandatory_does_not_promote_trust",
            "_context_item_for_hit(hit, mandatory=force)" in context
            and '"external"' in context
            and '"untrusted"' in context
            and "<UNTRUSTED_DATA>" in generic_context
            and "authority={metadata.authority.value}" in generic_context,
            "mandatory/include changes selection only while generic trust rendering stays data-only",
        ),
        _check(
            "source_citation_traceability",
            "SOURCE_TRACE:" in context
            and "knowledge_ids=" in context
            and "locators=" in context
            and "citations=" in context,
            "rendered context retains source, knowledge and citation traceability",
        ),
        _check(
            "explicit_override_before_assembly",
            "ProjectContextOverride" in context
            and "USER_INCLUDED" in context
            and "USER_EXCLUDED" in context
            and "if override is ProjectContextOverride.EXCLUDE" in context,
            "Auto/Include/Exclude overrides are applied before final assembly",
        ),
        _check(
            "kodestudio_preview",
            'object_name="projectContextCandidatesTable"' in preview
            and 'object_name="projectContextBudget"' in preview
            and 'object_name="projectContextRenderedPreview"' in preview
            and "project_context_widget = create_project_context_preview_widget()" in research_panel,
            "KodeStudio Research exposes source/reason/trust/budget context preview",
        ),
        _check(
            "no_lifecycle_or_workspace_consumption",
            "ProjectKnowledgeStore" not in context
            and ".save(" not in context
            and "MemoryStore" not in context
            and "workspace" not in preview.casefold(),
            "V2.2.3 does not pull forward lifecycle persistence or workspace consumption",
        ),
        _check(
            "authority_scope",
            "V2.2.3 — Explainable Context Builder" in authority
            and "V2.2.4 — Version-aware invalidation and derived-knowledge lifecycle" in authority,
            "V2.2.3 remains bounded from later lifecycle/workspace subdivisions",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload = {
        "schema_version": 1,
        "subdivision": "V2.2.3",
        "title": "Explainable Context Builder",
        "source_sha": source_sha,
        "observed_sha": observed_sha,
        "checks": checks,
        "summary": {
            "passed": sum(item["status"] == "PASS" for item in checks),
            "total": len(checks),
        },
        "status": "PASS" if passed else "FAIL",
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    payload["evidence_sha256"] = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
