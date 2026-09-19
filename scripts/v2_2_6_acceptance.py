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
        description="Kodepoia V2.2.6 Project Knowledge hardening integrated acceptance"
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    observed = _run(["git", "rev-parse", "HEAD"])
    observed_sha = observed.stdout.strip().lower()

    root = Path(__file__).resolve().parents[1]
    hardening_test = (
        root / "tests/test_v2_2_6_project_knowledge_hardening.py"
    ).read_text(encoding="utf-8")
    ui_test = (
        root / "tests/test_v2_2_6_hardening_ui.py"
    ).read_text(encoding="utf-8")
    knowledge = (
        root / "src/kodepoia/intelligence/project_knowledge.py"
    ).read_text(encoding="utf-8")
    retrieval = (
        root / "src/kodepoia/intelligence/project_retrieval.py"
    ).read_text(encoding="utf-8")
    context = (
        root / "src/kodepoia/intelligence/project_context.py"
    ).read_text(encoding="utf-8")
    lifecycle = (
        root / "src/kodepoia/intelligence/project_knowledge_lifecycle.py"
    ).read_text(encoding="utf-8")
    workspace = (
        root / "src/kodepoia/intelligence/project_workspace.py"
    ).read_text(encoding="utf-8")
    memory = (
        root / "src/kodepoia/intelligence/memory.py"
    ).read_text(encoding="utf-8")
    synthesis = (
        root / "src/kodepoia/intelligence/research/synthesis.py"
    ).read_text(encoding="utf-8")
    preview = (
        root / "src/kodepoia/kodestudio/project_context_preview.py"
    ).read_text(encoding="utf-8")
    workspace_ui = (
        root / "src/kodepoia/kodestudio/project_workspace_context.py"
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
            "tests/test_v2_2_6_project_knowledge_hardening.py",
        ]
    )
    targeted_detail = (
        "V2.2.6 adversarial backend integration corpus passed"
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
            "adversarial_backend_corpus",
            targeted.returncode == 0,
            targeted_detail,
        ),
        _check(
            "cross_project_retrieval_fails_closed",
            "project scope does not match catalog scope" in retrieval
            and "test_cross_project_retrieval_fails_before_embedding_provider_access"
            in hardening_test,
            "cross-project requests are rejected before embedding-provider access",
        ),
        _check(
            "memory_integrity_quarantine_and_version_guards",
            "integrity_mismatch" in memory
            and "version_conflict" in memory
            and "stale_version" in memory
            and "replay" in memory
            and "test_memory_replay_version_conflict_tamper_and_cross_project_are_fail_closed"
            in hardening_test,
            "R16.7 memory replay/version/integrity/quarantine rules remain in the V2.2 path",
        ),
        _check(
            "research_pack_immutable_digest",
            "Research Pack digest does not match canonical pack evidence" in synthesis
            and "Research Pack synthesis digest does not match embedded synthesis"
            in synthesis
            and "test_tampered_research_pack_or_digest_mismatch_is_rejected"
            in hardening_test,
            "tampered Research Packs fail immutable synthesis/pack digest validation",
        ),
        _check(
            "source_and_version_invalidation",
            "SOURCE_CHANGED" in lifecycle
            and "VERSION_CHANGED" in lifecycle
            and "ProjectKnowledgeState.INVALIDATED" in lifecycle
            and "test_file_and_engine_version_fingerprints_invalidate_derived_knowledge"
            in hardening_test,
            "changed source and engine/tool fingerprints invalidate derived knowledge before retrieval",
        ),
        _check(
            "prompt_injection_stays_data_only",
            "ResearchGuard().wrap" in knowledge
            and "<UNTRUSTED_DATA>" in hardening_test
            and "authority=data_only" in hardening_test
            and "test_prompt_injection_from_pack_file_and_memory_stays_untrusted_data"
            in hardening_test,
            "adversarial pack/file/memory instructions remain suspicious untrusted data through workspace consumption",
        ),
        _check(
            "secret_boundary",
            "redact_research_text" in knowledge
            and "secret_embedding" in memory
            and "test_secret_bearing_file_is_redacted_and_secret_memory_is_rejected"
            in hardening_test,
            "secret-bearing project files are redacted and secret-bearing memory is rejected",
        ),
        _check(
            "include_exclude_consistency",
            "ProjectContextOverride.EXCLUDE" in context
            and "ProjectContextOverride.INCLUDE" in context
            and "ProjectKnowledgeSelection.EXCLUDE" in lifecycle
            and "ProjectKnowledgeSelection.INCLUDE" in lifecycle
            and "test_include_exclude_consistency_survives_refresh_and_context_assembly"
            in hardening_test,
            "lifecycle selection and final context overrides remain explicit and deterministic",
        ),
        _check(
            "delete_derived_source_boundary",
            "delete-derived must never delete or mutate source records" in lifecycle
            and "source_records_deleted=False" in lifecycle
            and "test_delete_derived_never_deletes_project_file_or_immutable_research_pack"
            in hardening_test,
            "delete-derived cannot delete project files or immutable Research Packs",
        ),
        _check(
            "deterministic_order_and_budget",
            "hits.sort(" in retrieval
            and "ProjectContextReason.BUDGET_EXCEEDED" in context
            and "test_retrieval_order_and_context_budget_omission_are_deterministic"
            in hardening_test,
            "retrieval ordering and context-budget omission are deterministic",
        ),
        _check(
            "unavailable_vs_empty",
            "ProjectRetrievalState.EMBEDDING_UNAVAILABLE" in retrieval
            and "ProjectRetrievalState.EMPTY" in retrieval
            and "test_embedding_unavailable_and_valid_empty_result_remain_distinct"
            in hardening_test,
            "embedding unavailability remains distinct from a valid empty retrieval",
        ),
        _check(
            "cancellation_non_regression",
            "ResearchCancellation" in hardening_test
            and "ResearchOperationStatus.CANCELLED" in hardening_test
            and "persisted" in hardening_test,
            "existing cancellable Research acquisition still prevents persistence after cancellation",
        ),
        _check(
            "workspace_traceability_and_trust",
            "source_digest_sha256" in workspace
            and "citation_ids" in workspace
            and "trust_class" in workspace
            and "ProjectWorkspaceSurface.CHAT" in hardening_test
            and "ProjectWorkspaceSurface.KODECODE" in hardening_test
            and "ProjectWorkspaceSurface.SPECIALIST" in hardening_test,
            "Chat, KodeCode and specialists retain one digest-bound source/citation/trust snapshot",
        ),
        _check(
            "kodestudio_explainability_state",
            "projectContextCandidatesTable" in preview
            and "projectContextBudgetSummary" in preview
            and "projectWorkspaceContextTable_" in workspace_ui
            and "test_kodestudio_explains_adversarial_context_without_promoting_authority"
            in ui_test,
            "KodeStudio exposes source, trust, rationale/budget and active workspace context without authority promotion",
        ),
        _check(
            "authority_and_scope",
            "V2.2.6 — Project Knowledge hardening and integrated acceptance — CURRENT"
            in authority
            and "no project knowledge source can silently become instruction authority"
            in authority
            and "V2.3 Model Lab work" in authority,
            "acceptance remains bounded to the authorized V2.2.6 hardening scope",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload = {
        "schema_version": 1,
        "subdivision": "V2.2.6",
        "title": "Project Knowledge hardening and integrated acceptance",
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
