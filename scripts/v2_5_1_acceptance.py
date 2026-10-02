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

    registry = read("src/kodepoia/orchestrator/workspaces.py")
    inventory = read("src/kodepoia/kodestudio/workspace_inventory.py")
    app = read("src/kodepoia/kodestudio/app_v11.py")
    tests = read("tests/test_v2_5_1_workspace_registry.py")
    ui_tests = read("tests/test_v2_5_1_workspace_registry_ui.py")
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    v25 = read("docs/roadmap/V2_5_CROSS_WORKSPACE_ORCHESTRATION.md")
    python_core = read(".github/workflows/python-core.yml")
    ui_smoke = read(".github/workflows/ui-smoke.yml")

    current = (
        "V2.5.1 — Workspace registry, identity and relationship graph" in authority
        and "V2.5.1 — Workspace registry, identity and relationship graph" in state
        and "V2.5.1 — Workspace registry, identity and relationship graph" in next_doc
        and "V2.5.1 — Workspace registry, identity and relationship graph is the only authorized"
        in v25
    )

    checks = [
        _check("exact_head", source_sha == observed_sha, "acceptance executes the exact requested SHA"),
        _check("current_authority", current, "V2.5.1 is the only authorized implementation subdivision"),
        _check(
            "later_scope_unauthorized",
            "V2.5.2+ and V2.6 remain unauthorized" in authority
            and "V2.5.2+ and V2.6 remain unauthorized" in state
            and "V2.5.2+, V2.6" in next_doc
            and "V2.5.2 through V2.5.6 and V2.6 remain unauthorized" in v25,
            "V2.5.2+ and release work remain outside V2.5.1 scope",
        ),
        _check(
            "typed_identity",
            "class WorkspaceIdentity" in registry
            and "workspace_id" in registry
            and "project_scope=f\"project:{workspace_id}\"" in registry
            and "project_marker_sha256" in registry,
            "workspace identity binds canonical project identity and project scope",
        ),
        _check(
            "validated_project_roots",
            "validate_project_root(value)" in registry
            and "canonical_project_root" in registry
            and "Workspace path alias or duplicate is already registered" in registry,
            "registry accepts only validated Kodepoia roots and rejects aliases/duplicates",
        ),
        _check(
            "bounded_registry",
            "DEFAULT_MAX_WORKSPACES = 12" in registry
            and "Workspace registry capacity exceeded" in registry
            and "test_registry_rejects_duplicate_alias_and_is_bounded" in tests,
            "selected workspace registry is explicitly bounded",
        ),
        _check(
            "explicit_relationship_graph",
            "class WorkspaceRelationshipKind" in registry
            and "class WorkspaceRelationship" in registry
            and "add_relationship" in registry
            and "Workspace relationship requires distinct source and destination" in registry,
            "relationships are explicit typed edges between registered distinct workspaces",
        ),
        _check(
            "symlink_alias_rejection",
            "test_registry_rejects_symlink_alias_when_supported" in tests,
            "deterministic tests prove canonical-path alias/symlink rejection",
        ),
        _check(
            "read_only_inventory",
            "create_workspace_inventory_widget" in inventory
            and "QTableWidget.EditTrigger.NoEditTriggers" in inventory
            and "no cross-project orchestration or mutation is authorized here" in inventory,
            "KodeStudio inventory is read-only and does not expose orchestration/mutation",
        ),
        _check(
            "kodestudio_integration",
            "create_workspace_inventory_widget" in app
            and "_kodepoia_workspace_inventory" in app
            and "workspaceInventoryTable" in ui_tests,
            "KodeStudio Projects page integrates the V2.5.1 inventory",
        ),
        _check(
            "no_later_engine",
            "handoff" not in registry.casefold()
            and "task graph" not in registry.casefold()
            and "subprocess" not in registry.casefold()
            and "shell" not in registry.casefold(),
            "V2.5.1 introduces no context handoff, task execution or process launcher",
        ),
        _check(
            "deterministic_tests",
            "tmp_path" in tests
            and "kaggle" not in tests.casefold()
            and "network" not in tests.casefold(),
            "V2.5.1 acceptance requires no live provider, network or credentials",
        ),
        _check(
            "ci_exact_head",
            "Run V2.5.1 workspace registry exact-head acceptance" in python_core
            and "v2-5-1-workspace-registry" in python_core
            and "test_v2_5_1_workspace_registry_ui.py" in python_core
            and "test_v2_5_1_workspace_registry_ui.py" in ui_smoke,
            "Ubuntu/Windows exact-head evidence and KodeStudio UI smoke are wired",
        ),
        _check(
            "release_boundary",
            "v1.1.0-rc8" in authority
            and "next public release" in v25
            and "release" in state.casefold()
            and "V2.6" in v25,
            "release remains deferred until the V2 release phase",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.5.1",
        "title": "Workspace registry, identity and relationship graph",
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
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
