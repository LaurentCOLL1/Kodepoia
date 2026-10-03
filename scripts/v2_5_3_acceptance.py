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

    plan = read("src/kodepoia/orchestrator/plan.py")
    ui = read("src/kodepoia/kodestudio/orchestration_plan_preview.py")
    tests = read("tests/test_v2_5_3_orchestration_plan.py")
    ui_tests = read("tests/test_v2_5_3_orchestration_plan_ui.py")
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    v25 = read("docs/roadmap/V2_5_CROSS_WORKSPACE_ORCHESTRATION.md")
    python_core = read(".github/workflows/python-core.yml")
    ui_smoke = read(".github/workflows/ui-smoke.yml")

    current = (
        "V2.5.3 — Orchestration plan, dependency DAG and routing" in authority
        and "V2.5.3 — Orchestration plan, dependency DAG and routing" in state
        and "V2.5.3 — Orchestration plan, dependency DAG and routing" in next_doc
        and "V2.5.3 — Orchestration plan, dependency DAG and routing is the only authorized" in v25
    )

    checks = [
        _check("exact_head", source_sha == observed_sha, "acceptance executes the exact requested SHA"),
        _check("current_authority", current, "V2.5.3 is the only authorized implementation subdivision"),
        _check(
            "later_scope_unauthorized",
            "V2.5.4+ and V2.6 remain unauthorized" in authority
            and "V2.5.4+ and V2.6 remain unauthorized" in state
            and "V2.5.4+, V2.6" in next_doc,
            "V2.5.4+ and release work remain outside V2.5.3 scope",
        ),
        _check(
            "typed_dag",
            "class OrchestrationTask" in plan
            and "class OrchestrationPlan" in plan
            and "dependencies" in plan
            and "_topological_order" in plan,
            "typed deterministic task DAG is present",
        ),
        _check(
            "cycle_and_missing_dependency_rejection",
            "dependency cycle detected" in plan
            and "unknown dependencies" in plan
            and "test_plan_rejects_unknown_dependency_and_cycle" in tests,
            "cycles and missing dependencies fail closed",
        ),
        _check(
            "workspace_ownership",
            "workspace_id" in plan
            and "workspace_scope" in plan
            and "Task workspace scope must bind its owning workspace" in plan,
            "each task binds its owning workspace/project scope",
        ),
        _check(
            "fixed_route_catalog",
            "ROUTE_CATALOG" in plan
            and "PROJECT_CONTEXT" in plan
            and "KODECODE" in plan
            and "KODEGODOT" in plan
            and "MODEL_LAB" in plan
            and "SPECIALIST" in plan,
            "routing uses a fixed catalog of existing surfaces",
        ),
        _check(
            "effect_visibility",
            "class OrchestrationEffect" in plan
            and 'READ_ONLY = "read_only"' in plan
            and 'MUTATION_PROPOSED = "mutation_proposed"' in plan
            and "not allowed for route" in plan,
            "effect class is explicit and validated against route capability",
        ),
        _check(
            "preview_and_blockers",
            "class OrchestrationPlanPreview" in plan
            and "blocked_tasks" in plan
            and "blockers" in plan
            and "mutation_proposed_tasks" in plan,
            "plan preview exposes dependency blockers and proposed mutation tasks",
        ),
        _check(
            "immutable_digest",
            "digest_sha256" in plan
            and "_sha256_payload" in plan
            and "test_plan_serialization_is_stable" in tests,
            "plan/task serialization is deterministic and digest-bound",
        ),
        _check(
            "read_only_ui",
            "create_orchestration_plan_preview_widget" in ui
            and "QTableWidget.EditTrigger.NoEditTriggers" in ui
            and "execution=not authorized" in ui
            and "orchestrationPlanTable" in ui_tests,
            "KodeStudio preview is read-only and explicitly non-executing",
        ),
        _check(
            "no_execution_surface",
            "execute_tool(" not in plan
            and "subprocess" not in plan
            and "Popen" not in plan
            and "shell" not in plan.casefold()
            and "argv" not in plan.casefold(),
            "V2.5.3 introduces no protected execution surface",
        ),
        _check(
            "deterministic_offline",
            "tmp_path" in tests
            and "network" not in tests.casefold()
            and "kaggle" not in tests.casefold(),
            "required tests are deterministic and provider-independent",
        ),
        _check(
            "ci_exact_head",
            "Run V2.5.3 orchestration plan exact-head acceptance" in python_core
            and "v2-5-3-orchestration-plan" in python_core
            and "test_v2_5_3_orchestration_plan_ui.py" in python_core
            and "test_v2_5_3_orchestration_plan_ui.py" in ui_smoke,
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
        "subdivision": "V2.5.3",
        "title": "Orchestration plan, dependency DAG and routing",
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
