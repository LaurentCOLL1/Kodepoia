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
        description="Kodepoia V2.2.4 version-aware Project Knowledge lifecycle acceptance"
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    observed = _run(["git", "rev-parse", "HEAD"])
    observed_sha = observed.stdout.strip().lower()

    root = Path(__file__).resolve().parents[1]
    lifecycle = (
        root / "src/kodepoia/intelligence/project_knowledge_lifecycle.py"
    ).read_text(encoding="utf-8")
    retrieval = (
        root / "src/kodepoia/intelligence/project_retrieval.py"
    ).read_text(encoding="utf-8")
    lifecycle_ui = (
        root / "src/kodepoia/kodestudio/project_knowledge_lifecycle.py"
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
            "tests/test_v2_2_4_project_knowledge_lifecycle.py",
            "tests/test_v2_2_4_lifecycle_ui.py",
        ]
    )
    targeted_detail = (
        "targeted V2.2.4 backend/UI tests passed"
        if targeted.returncode == 0
        else (targeted.stdout + targeted.stderr)[-4000:]
    )

    checks = [
        _check(
            "exact_head",
            observed.returncode == 0 and observed_sha == source_sha,
            observed_sha,
        ),
        _check(
            "v2_2_4_targeted_tests",
            targeted.returncode == 0,
            targeted_detail,
        ),
        _check(
            "version_fingerprint_contract",
            "class ProjectKnowledgeVersionInputs" in lifecycle
            and "version_keys" in lifecycle
            and "version_fingerprint_sha256" in lifecycle
            and "_source_fingerprint" in lifecycle,
            "derived knowledge carries explicit source and relevant version fingerprints",
        ),
        _check(
            "deterministic_stale_invalidation",
            'STALE = "stale"' in lifecycle
            and 'INVALIDATED = "invalidated"' in lifecycle
            and 'SOURCE_CHANGED = "source_changed"' in lifecycle
            and 'VERSION_CHANGED = "version_changed"' in lifecycle,
            "source/version changes have deterministic visible lifecycle reasons",
        ),
        _check(
            "affected_only_version_dependencies",
            "subset_digest" in lifecycle
            and "version_dependencies" in lifecycle
            and "version_keys=keys" in lifecycle,
            "version invalidation is scoped to declared per-item dependency keys",
        ),
        _check(
            "refresh_rebuild_derived_only",
            "def refresh(" in lifecycle
            and "def rebuild(" in lifecycle
            and "ProjectKnowledgeBuilder" in lifecycle
            and "_catalog_store.save(effective)" in lifecycle,
            "refresh/rebuild recreates the derived catalog through accepted Project Knowledge primitives",
        ),
        _check(
            "bounded_delete_source_separation",
            "max_delete_items" in lifecycle
            and "delete_derived" in lifecycle
            and "source_records_deleted=False" in lifecycle
            and "source_paths_touched=()" in lifecycle,
            "delete-derived is bounded and cannot represent source deletion",
        ),
        _check(
            "persistent_include_exclude",
            "ProjectKnowledgeSelection" in lifecycle
            and 'INCLUDE = "include"' in lifecycle
            and 'EXCLUDE = "exclude"' in lifecycle
            and "selection=selection" in lifecycle,
            "include/exclude is persisted in lifecycle state and reapplied after refresh",
        ),
        _check(
            "stale_not_fresh_context",
            "ProjectKnowledgeState.INVALIDATED" in lifecycle
            and "_ELIGIBLE_STATES" in retrieval
            and "ProjectKnowledgeState.ACTIVE" in retrieval
            and "ProjectKnowledgeState.INCLUDED" in retrieval,
            "stale/invalidated derived knowledge is excluded by the accepted retrieval eligibility gate",
        ),
        _check(
            "kodestudio_lifecycle_controls",
            'object_name="projectKnowledgeLifecycleTable"' in lifecycle_ui
            and 'object_name="projectKnowledgeAutoButton"' in lifecycle_ui
            and 'object_name="projectKnowledgeIncludeButton"' in lifecycle_ui
            and 'object_name="projectKnowledgeExcludeButton"' in lifecycle_ui
            and 'object_name="projectKnowledgeRefreshButton"' in lifecycle_ui
            and 'object_name="projectKnowledgeDeleteDerivedButton"' in lifecycle_ui
            and "projectKnowledgeSourceDeleteBoundary" in lifecycle_ui
            and "create_project_knowledge_lifecycle_widget()" in research_panel,
            "KodeStudio Research exposes lifecycle state plus explicit include/exclude/refresh/delete-derived controls",
        ),
        _check(
            "immutable_source_boundary",
            "never deletes Research Packs" in lifecycle_ui
            and "source_records_deleted" in lifecycle
            and "ResearchPackStore" not in lifecycle,
            "lifecycle operations do not rewrite immutable Research Pack source evidence",
        ),
        _check(
            "no_workspace_consumption_pull_forward",
            "workspace consumption" not in lifecycle.casefold()
            and "Chat" not in lifecycle
            and "KodeCode" not in lifecycle,
            "V2.2.4 does not implement V2.2.5 workspace consumption or Memory bridge behavior",
        ),
        _check(
            "authority_scope",
            "V2.2.4 — Version-aware invalidation and derived-knowledge lifecycle" in authority
            and "V2.2.5 — Project Memory bridge and workspace consumption" in authority,
            "V2.2.4 remains bounded from V2.2.5+ authority",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload = {
        "schema_version": 1,
        "subdivision": "V2.2.4",
        "title": "Version-aware invalidation and derived-knowledge lifecycle",
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
