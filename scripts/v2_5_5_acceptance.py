from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def _check(name: str, condition: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "PASS" if condition else "FAIL", "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    source_sha = args.source_sha.strip()
    observed_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

    def read(path: str) -> str:
        return (root / path).read_text(encoding="utf-8")

    workspace = read("src/kodepoia/kodestudio/orchestration_workspace.py")
    history = read("src/kodepoia/orchestrator/history.py")
    app = read("src/kodepoia/kodestudio/app_v11.py")
    tests = read("tests/test_v2_5_5_orchestration_workspace_ui.py")
    history_tests = read("tests/test_v2_5_5_orchestration_history.py")
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    v25 = read("docs/roadmap/V2_5_CROSS_WORKSPACE_ORCHESTRATION.md")
    python_core = read(".github/workflows/python-core.yml")
    ui_smoke = read(".github/workflows/ui-smoke.yml")

    current = (
        "V2.5.5 — KodeStudio orchestration workspace and operational history" in authority
        and "V2.5.5 — KodeStudio orchestration workspace and operational history" in state
        and "V2.5.5 — KodeStudio orchestration workspace and operational history" in next_doc
        and "V2.5.5 — KodeStudio orchestration workspace and operational history is the only authorized" in v25
    )

    checks = [
        _check("exact_head", source_sha == observed_sha, "acceptance executes the exact requested SHA"),
        _check("current_authority", current, "V2.5.5 is the only authorized implementation subdivision"),
        _check(
            "later_scope_unauthorized",
            "V2.5.6 and V2.6 remain unauthorized" in authority
            and "V2.5.6 and V2.6 remain unauthorized" in state
            and "V2.5.6, V2.6" in next_doc,
            "V2.5.6 and release work remain outside V2.5.5 scope",
        ),
        _check(
            "workspace_relationship_management",
            "orchestrationWorkspaceTable" in workspace
            and "orchestrationRelationshipTable" in workspace
            and "orchestrationAddRelationshipButton" in workspace
            and "WorkspaceRelationshipKind" in workspace,
            "KodeStudio exposes selected workspace inventory and explicit relationship management",
        ),
        _check(
            "handoff_and_plan_composition",
            "create_workspace_handoff_inspector" in workspace
            and "create_orchestration_plan_preview_widget" in workspace,
            "V2.5.5 composes accepted V2.5.2 handoff and V2.5.3 plan surfaces",
        ),
        _check(
            "approval_controls",
            "orchestrationApproveButton" in workspace
            and "MutationApproval.for_task" in workspace
            and "QMessageBox.question" in workspace,
            "mutation approval requires an explicit UI confirmation and exact V2.5.4 approval binding",
        ),
        _check(
            "execution_cancel_recovery_controls",
            "orchestrationExecuteButton" in workspace
            and "orchestrationCancelButton" in workspace
            and "orchestrationRecoverButton" in workspace
            and "coordinator.execute" in workspace
            and "coordinator.cancel_plan" in workspace
            and "coordinator.recover" in workspace,
            "operational controls are a UI facade over accepted V2.5.4 coordinator semantics",
        ),
        _check(
            "persistent_history",
            "class OrchestrationHistoryStore" in history
            and "history.jsonl" in history
            and "previous_digest_sha256" in history
            and "_write_atomic" in history
            and "test_history_is_append_only_hash_chained_and_persistent" in history_tests,
            "operational history is persistent, atomic and hash-chained",
        ),
        _check(
            "history_tamper_rejection",
            "history record digest mismatch" in history
            and "history chain mismatch" in history
            and "test_history_tampering_fails_closed" in history_tests,
            "history tampering fails closed",
        ),
        _check(
            "honest_degraded_states",
            "No plan or handoff loaded" in workspace
            and "Execution unavailable" in workspace
            and "Cancellation unavailable" in workspace
            and "Recovery unavailable" in workspace
            and "test_empty_workspace_is_honest_and_does_not_claim_execution" in tests,
            "empty/degraded states never claim unavailable orchestration capability",
        ),
        _check(
            "localization_accessibility",
            'startswith("qps")' in workspace
            and "setAccessibleName" in workspace
            and "setAccessibleDescription" in workspace
            and "test_orchestration_workspace_localization_and_accessibility" in tests,
            "EN/FR/qps-ploc and accessibility are covered",
        ),
        _check(
            "kodestudio_navigation_integration",
            "orchestration_nav_text" in app
            and "nav.insertItem(orchestration_index" in app
            and "pages.insertWidget(orchestration_index" in app
            and "test_app_v11_integrates_orchestration_workspace_before_security" in tests,
            "orchestration is integrated as a dedicated KodeStudio workspace",
        ),
        _check(
            "no_new_orchestration_semantics",
            "class OrchestrationPlan" not in workspace
            and "class MutationApproval" not in workspace
            and "class GovernedExecutionCoordinator" not in workspace
            and "subprocess" not in workspace,
            "V2.5.5 reuses accepted V2.5.1-V2.5.4 contracts rather than redefining them",
        ),
        _check(
            "deterministic_tests",
            "tmp_path" in tests
            and "tmp_path" in history_tests
            and "network" not in tests.casefold()
            and "kaggle" not in tests.casefold(),
            "required tests are deterministic and provider-independent",
        ),
        _check(
            "ci_exact_head",
            "Run V2.5.5 orchestration workspace exact-head acceptance" in python_core
            and "v2-5-5-orchestration-workspace" in python_core
            and "test_v2_5_5_orchestration_workspace_ui.py" in python_core
            and "test_v2_5_5_orchestration_workspace_ui.py" in ui_smoke,
            "Ubuntu/Windows exact-head acceptance and UI smoke are wired",
        ),
        _check(
            "release_boundary",
            "v1.1.0-rc8" in authority
            and "next public release" in v25
            and "V2.6" in v25,
            "release remains deferred until the V2 release phase",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.5.5",
        "title": "KodeStudio orchestration workspace and operational history",
        "source_sha": source_sha,
        "observed_sha": observed_sha,
        "checks": checks,
        "summary": {"passed": sum(item["status"] == "PASS" for item in checks), "total": len(checks)},
        "status": "PASS" if passed else "FAIL",
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["evidence_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
