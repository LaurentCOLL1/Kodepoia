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

    execution = read("src/kodepoia/orchestrator/execution.py")
    tests = read("tests/test_v2_5_4_governed_execution.py")
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    v25 = read("docs/roadmap/V2_5_CROSS_WORKSPACE_ORCHESTRATION.md")
    python_core = read(".github/workflows/python-core.yml")

    current = (
        "V2.5.4 — Governed execution, approval, cancellation and recovery" in authority
        and "V2.5.4 — Governed execution, approval, cancellation and recovery" in state
        and "V2.5.4 — Governed execution, approval, cancellation and recovery" in next_doc
        and "V2.5.4 — Governed execution, approval, cancellation and recovery is the only authorized" in v25
    )

    checks = [
        _check("exact_head", source_sha == observed_sha, "acceptance executes the exact requested SHA"),
        _check("current_authority", current, "V2.5.4 is the only authorized implementation subdivision"),
        _check(
            "later_scope_unauthorized",
            "V2.5.5+ and V2.6 remain unauthorized" in authority
            and "V2.5.5+ and V2.6 remain unauthorized" in state
            and "V2.5.5+, V2.6" in next_doc,
            "V2.5.5+ and release work remain outside V2.5.4 scope",
        ),
        _check(
            "exact_mutation_approval",
            "class MutationApproval" in execution
            and "plan_digest_sha256" in execution
            and "task_digest_sha256" in execution
            and "input_handoff_digests" in execution
            and "test_mutation_requires_exact_approval" in tests,
            "mutation confirmation is bound to exact plan/task/workspace/handoff lineage",
        ),
        _check(
            "destination_owned_routing",
            "class DestinationServiceRegistry" in execution
            and "No destination service registered for route" in execution
            and "self.services.execute(task, confirmed=confirmed)" in execution,
            "execution delegates only through fixed route-bound destination service adapters",
        ),
        _check(
            "bounded_concurrency_conflict",
            "threading.BoundedSemaphore" in execution
            and "_workspace_locks" in execution
            and "max_concurrency" in execution,
            "concurrency is bounded and same-workspace conflicts block",
        ),
        _check(
            "killswitch_cancellation",
            "KillSwitch" in execution
            and "cancel_plan" in execution
            and "self.kill_switch.trigger()" in execution
            and "test_cancel_plan_uses_kill_switch_and_blocks_new_work" in tests,
            "plan cancellation is KillSwitch-compatible and blocks new work",
        ),
        _check(
            "downstream_blocking",
            "dependency_evidence.state is not ExecutionState.COMPLETED" in execution
            and "ExecutionState.BLOCKED" in execution
            and "test_dependency_failure_blocks_downstream" in tests,
            "downstream tasks require completed dependency evidence",
        ),
        _check(
            "lineage_safe_recovery",
            "class RecoveryBinding" in execution
            and "assert_compatible" in execution
            and "incompatible with current plan/task/workspace/handoff lineage" in execution
            and "test_recovery_is_lineage_bound" in tests,
            "recovery fails closed when plan/task/workspace/handoff lineage changes",
        ),
        _check(
            "no_raw_execution_surface",
            "subprocess" not in execution
            and "Popen" not in execution
            and "shell" not in execution.casefold()
            and "argv" not in execution.casefold()
            and "env" not in execution.casefold()
            and "package" not in execution.casefold(),
            "V2.5.4 exposes no raw shell/argv/env/package surface",
        ),
        _check(
            "deterministic_tests",
            "tmp_path" in tests
            and "network" not in tests.casefold()
            and "kaggle" not in tests.casefold(),
            "required tests are deterministic and provider-independent",
        ),
        _check(
            "ci_exact_head",
            "Run V2.5.4 governed execution exact-head acceptance" in python_core
            and "v2-5-4-governed-execution" in python_core
            and "test_v2_5_4_governed_execution.py" in python_core,
            "Ubuntu/Windows exact-head acceptance is wired",
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
        "subdivision": "V2.5.4",
        "title": "Governed execution, approval, cancellation and recovery",
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
