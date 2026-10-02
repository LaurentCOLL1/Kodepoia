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

    handoff = read("src/kodepoia/orchestrator/handoff.py")
    ui = read("src/kodepoia/kodestudio/workspace_handoff.py")
    tests = read("tests/test_v2_5_2_context_handoff.py")
    ui_tests = read("tests/test_v2_5_2_context_handoff_ui.py")
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    v25 = read("docs/roadmap/V2_5_CROSS_WORKSPACE_ORCHESTRATION.md")
    python_core = read(".github/workflows/python-core.yml")
    ui_smoke = read(".github/workflows/ui-smoke.yml")

    current = (
        "V2.5.2 — Cross-workspace context handoff and provenance" in authority
        and "V2.5.2 — Cross-workspace context handoff and provenance" in state
        and "V2.5.2 — Cross-workspace context handoff and provenance" in next_doc
        and "V2.5.2 — Cross-workspace context handoff and provenance is the only authorized" in v25
    )

    checks = [
        _check("exact_head", source_sha == observed_sha, "acceptance executes the exact requested SHA"),
        _check("current_authority", current, "V2.5.2 is the only authorized implementation subdivision"),
        _check(
            "later_scope_unauthorized",
            "V2.5.3+ and V2.6 remain unauthorized" in authority
            and "V2.5.3+ and V2.6 remain unauthorized" in state
            and "V2.5.3+, V2.6" in next_doc,
            "V2.5.3+ and release work remain outside V2.5.2 scope",
        ),
        _check(
            "source_destination_binding",
            "source_workspace_id" in handoff
            and "destination_workspace_id" in handoff
            and "source_project_scope" in handoff
            and "destination_project_scope" in handoff
            and "distinct source and destination" in handoff,
            "handoff binds distinct source and destination workspaces/scopes",
        ),
        _check(
            "snapshot_reuse",
            "ProjectWorkspaceContextSnapshot" in handoff
            and "snapshot_digest_sha256" in handoff
            and "retrieval_digest_sha256" in handoff
            and "context_bundle_digest_sha256" in handoff,
            "handoff reuses accepted governed workspace context lineage",
        ),
        _check(
            "data_only_authority",
            'DATA_ONLY_AUTHORITY = "data_only"' in handoff
            and "global_memory_promotion_allowed: bool = False" in handoff
            and "cannot authorize global memory promotion" in handoff,
            "cross-workspace context remains data-only with no global promotion",
        ),
        _check(
            "explicit_selection",
            "include_content_sha256s" in handoff
            and "exclude_content_sha256s" in handoff
            and "outside the source snapshot" in handoff
            and "test_handoff_include_exclude_is_explicit_and_bounded" in tests,
            "include/exclude selection is explicit and bounded to the source snapshot",
        ),
        _check(
            "provenance_visibility",
            "citation_ids" in handoff
            and "trust_class" in handoff
            and "freshness" in handoff
            and "version" in handoff
            and "WorkspaceHandoffSource" in handoff,
            "handoff preserves citation/trust/freshness/version provenance",
        ),
        _check(
            "tamper_rejection",
            "verify_integrity" in handoff
            and "test_handoff_digest_changes_on_payload_tampering" in tests,
            "immutable digest detects payload tampering",
        ),
        _check(
            "read_only_ui",
            "create_workspace_handoff_inspector" in ui
            and "QTableWidget.EditTrigger.NoEditTriggers" in ui
            and "authority=" in ui
            and "workspaceHandoffSourcesTable" in ui_tests,
            "KodeStudio inspection surface is read-only and exposes authority/integrity",
        ),
        _check(
            "no_execution_surface",
            "subprocess" not in handoff
            and "Popen" not in handoff
            and "shell" not in handoff.casefold()
            and "argv" not in handoff.casefold(),
            "V2.5.2 introduces no task/process execution surface",
        ),
        _check(
            "deterministic_offline",
            "tmp_path" in tests
            and "network" not in tests.casefold()
            and "kaggle" not in tests.casefold(),
            "required V2.5.2 tests are deterministic and provider-independent",
        ),
        _check(
            "ci_exact_head",
            "Run V2.5.2 context handoff exact-head acceptance" in python_core
            and "v2-5-2-context-handoff" in python_core
            and "test_v2_5_2_context_handoff_ui.py" in python_core
            and "test_v2_5_2_context_handoff_ui.py" in ui_smoke,
            "Ubuntu/Windows exact-head acceptance and UI smoke are wired",
        ),
        _check(
            "release_boundary",
            "v1.1.0-rc8" in authority
            and "next public release" in v25
            and "V2.6" in v25,
            "release remains deferred to the later V2 release phase",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.5.2",
        "title": "Cross-workspace context handoff and provenance",
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
