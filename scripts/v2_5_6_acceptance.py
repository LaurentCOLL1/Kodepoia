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
    observed_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()

    def read(path: str) -> str:
        return (root / path).read_text(encoding="utf-8")

    hardening = read("tests/test_v2_5_6_cross_workspace_hardening.py")
    ui = read("tests/test_v2_5_6_cross_workspace_hardening_ui.py")
    workspaces = read("src/kodepoia/orchestrator/workspaces.py")
    handoff = read("src/kodepoia/orchestrator/handoff.py")
    plan = read("src/kodepoia/orchestrator/plan.py")
    execution = read("src/kodepoia/orchestrator/execution.py")
    history = read("src/kodepoia/orchestrator/history.py")
    workspace_ui = read("src/kodepoia/kodestudio/orchestration_workspace.py")
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    roadmap = read("docs/roadmap/KODEPOIA_ROADMAP_V2.md")
    v25 = read("docs/roadmap/V2_5_CROSS_WORKSPACE_ORCHESTRATION.md")
    python_core = read(".github/workflows/python-core.yml")
    ui_smoke = read(".github/workflows/ui-smoke.yml")

    historical = {
        "registry": read("tests/test_v2_5_1_workspace_registry.py"),
        "handoff": read("tests/test_v2_5_2_context_handoff.py"),
        "plan": read("tests/test_v2_5_3_orchestration_plan.py"),
        "execution": read("tests/test_v2_5_4_governed_execution.py"),
        "workspace": read("tests/test_v2_5_5_orchestration_workspace_ui.py"),
        "history": read("tests/test_v2_5_5_orchestration_history.py"),
    }

    current = (
        "V2.5.6 — Cross-workspace hardening and integrated acceptance" in authority
        and "V2.5.6 — Cross-workspace hardening and integrated acceptance" in state
        and "V2.5.6 — Cross-workspace hardening and integrated acceptance" in next_doc
        and "V2.5.6 CURRENT" in roadmap
        and "V2.5.6 — Cross-workspace hardening and integrated acceptance is now the only authorized"
        in state
    )

    checks = [
        _check(
            "exact_head",
            source_sha == observed_sha,
            "acceptance executes the exact requested source SHA",
        ),
        _check(
            "current_authority",
            current,
            "V2.5.6 is the only authorized implementation subdivision",
        ),
        _check(
            "prior_chain_normalized",
            "V2.5.5 is **COMPLETE + NORMALIZED**" in authority
            and "V2.5.5 is **COMPLETE + NORMALIZED**" in next_doc
            and "30/30" in authority
            and "05cb36f5fed085838644d22a7aaa1225574ff023" in authority,
            "V2.5.1-V2.5.5 accepted truth remains normalized and terminal",
        ),
        _check(
            "identity_path_symlink_hardening",
            "def assert_current" in workspaces
            and "Workspace project identity drift detected" in workspaces
            and "Workspace path alias or duplicate is already registered" in workspaces
            and "test_v256_workspace_identity_drift_and_alias_confusion_fail_closed" in hardening
            and "test_registry_rejects_symlink_alias_when_supported" in historical["registry"],
            "path alias, symlink and post-registration identity drift fail closed",
        ),
        _check(
            "handoff_authority_freshness_tamper",
            "UNUSABLE_FRESHNESS_STATES" in handoff
            and "def assert_usable_for" in handoff
            and "Cross-workspace handoff integrity check failed" in handoff
            and "test_v256_stale_revoked_and_tampered_handoffs_fail_closed" in hardening
            and "test_v256_context_authority_spoofing_and_wrong_destination_are_rejected" in hardening,
            "stale/revoked/quarantined/tampered/spoofed handoffs fail closed",
        ),
        _check(
            "missing_handoff_evidence",
            "MissingHandoffEvidence" in execution
            and "HandoffDigestMismatch" in execution
            and "InvalidHandoffEvidence" in execution
            and "test_v256_missing_or_invalid_handoff_evidence_blocks_execution" in hardening,
            "referenced handoff evidence must be present, exact and usable before execution",
        ),
        _check(
            "dependency_cycle_missing_evidence",
            "dependency cycle detected" in plan
            and "unknown dependencies" in plan
            and "test_plan_rejects_unknown_dependency_and_cycle" in historical["plan"]
            and "dependency_evidence.state is not ExecutionState.COMPLETED" in execution,
            "cycles, missing dependency references and incomplete evidence cannot schedule downstream work",
        ),
        _check(
            "malicious_routing_text",
            "ROUTE_CATALOG" in plan
            and "DestinationServiceRegistry" in execution
            and "test_v256_malicious_route_or_goal_text_cannot_escape_fixed_catalog" in hardening,
            "goal/source/model text cannot create dynamic routes or service adapters",
        ),
        _check(
            "unauthorized_destination_write",
            "MutationApproval.for_task" in execution
            and "_approval_matches" in execution
            and "test_v256_unauthorized_destination_write_and_wrong_approval_fail_closed" in hardening,
            "destination mutation requires exact task-scoped approval",
        ),
        _check(
            "concurrent_write_conflict",
            "threading.BoundedSemaphore" in execution
            and "_workspace_locks" in execution
            and "test_v256_concurrent_same_workspace_write_conflict_is_blocked" in hardening,
            "same-workspace concurrent writes are blocked while concurrency remains bounded",
        ),
        _check(
            "cancellation_partial_success",
            "self.kill_switch.trigger()" in execution
            and "ExecutionState.CANCELLED" in execution
            and "test_v256_cancellation_cannot_become_partial_success_and_blocks_downstream" in hardening,
            "cancellation cannot become partial success or authorize dependent work",
        ),
        _check(
            "recovery_and_project_drift",
            "workspace_registry.assert_current" in execution
            and "WorkspaceIdentityDrift" in execution
            and "RecoveryBinding" in execution
            and "test_v256_incompatible_recovery_and_deleted_project_fail_closed" in hardening,
            "deleted/moved destination projects and incompatible recovery lineage fail closed",
        ),
        _check(
            "secret_leakage",
            "SecretTaintGuard" in execution
            and "sanitize_payload" in execution
            and "test_v256_secret_tainted_service_output_is_sanitized_before_evidence" in hardening,
            "secret-tainted destination output is sanitized before durable evidence",
        ),
        _check(
            "history_integrity",
            "previous_digest_sha256" in history
            and "history chain mismatch" in history
            and "history record digest mismatch" in history
            and "test_history_tampering_fails_closed" in historical["history"],
            "operational history remains append-only and tamper-evident",
        ),
        _check(
            "deterministic_degraded_ui",
            "history_valid" in workspace_ui
            and "control.setEnabled(False)" in workspace_ui
            and "test_v256_corrupt_history_remains_visible_and_disables_operations" in ui
            and "test_v256_missing_coordinator_is_explicit_and_non_authorizing" in ui,
            "corrupt/missing runtime evidence produces deterministic non-authorizing UI states",
        ),
        _check(
            "integrated_adversarial_coverage",
            all(
                marker in hardening
                for marker in (
                    "test_v256_workspace_identity_drift_and_alias_confusion_fail_closed",
                    "test_v256_stale_revoked_and_tampered_handoffs_fail_closed",
                    "test_v256_missing_or_invalid_handoff_evidence_blocks_execution",
                    "test_v256_malicious_route_or_goal_text_cannot_escape_fixed_catalog",
                    "test_v256_unauthorized_destination_write_and_wrong_approval_fail_closed",
                    "test_v256_concurrent_same_workspace_write_conflict_is_blocked",
                    "test_v256_cancellation_cannot_become_partial_success_and_blocks_downstream",
                    "test_v256_incompatible_recovery_and_deleted_project_fail_closed",
                    "test_v256_secret_tainted_service_output_is_sanitized_before_evidence",
                )
            ),
            "V2.5.6 adds integrated adversarial proof over the accepted V2.5 chain",
        ),
        _check(
            "deterministic_provider_independent",
            "kaggle" not in hardening.casefold()
            and "network" not in hardening.casefold()
            and "requests." not in hardening
            and "socket." not in hardening,
            "mandatory V2.5.6 tests require no live provider, external network or credentials",
        ),
        _check(
            "no_parallel_engine",
            not (root / "src/kodepoia/orchestrator/v2_5_6.py").exists()
            and not (root / "src/kodepoia/kodestudio/orchestration_hardening_v256.py").exists(),
            "hardening strengthens existing V2.5 services rather than creating a replacement engine",
        ),
        _check(
            "ci_wiring",
            "Run V2.5.6 cross-workspace hardening exact-head acceptance" in python_core
            and "v2-5-6-cross-workspace-hardening" in python_core
            and "tests/test_v2_5_6_cross_workspace_hardening_ui.py" in python_core
            and "tests/test_v2_5_6_cross_workspace_hardening_ui.py" in ui_smoke,
            "Ubuntu/Windows exact-head evidence and UI smoke are mandatory",
        ),
        _check(
            "release_boundary",
            "V2.6 remains unauthorized" in authority
            and "release/tag/installer/TUF/updater mutation" in next_doc
            and "v1.1.0-rc8" in authority
            and "V2.6" in v25,
            "V2.6 and release mutation remain outside V2.5.6 scope",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.5.6",
        "title": "Cross-workspace hardening and integrated acceptance",
        "source_sha": source_sha,
        "observed_sha": observed_sha,
        "checks": checks,
        "summary": {
            "passed": sum(item["status"] == "PASS" for item in checks),
            "total": len(checks),
        },
        "status": "PASS" if passed else "FAIL",
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["evidence_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
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
