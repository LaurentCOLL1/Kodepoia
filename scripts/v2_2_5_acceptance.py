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
        description="Kodepoia V2.2.5 project Memory bridge/workspace acceptance"
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    observed = _run(["git", "rev-parse", "HEAD"])
    observed_sha = observed.stdout.strip().lower()

    root = Path(__file__).resolve().parents[1]
    bridge = (
        root / "src/kodepoia/intelligence/project_workspace.py"
    ).read_text(encoding="utf-8")
    preview = (
        root / "src/kodepoia/kodestudio/project_context_preview.py"
    ).read_text(encoding="utf-8")
    research = (
        root / "src/kodepoia/kodestudio/research_panel.py"
    ).read_text(encoding="utf-8")
    chat = (
        root / "src/kodepoia/kodestudio/vision_chat.py"
    ).read_text(encoding="utf-8")
    assistant = (
        root / "src/kodepoia/kodestudio/vision_assistant.py"
    ).read_text(encoding="utf-8")
    kodecode = (
        root / "src/kodepoia/kodecode/api.py"
    ).read_text(encoding="utf-8")
    kodecode_executor = (
        root / "src/kodepoia/kodecode/executor.py"
    ).read_text(encoding="utf-8")
    app = (
        root / "src/kodepoia/kodestudio/app.py"
    ).read_text(encoding="utf-8")
    memory = (
        root / "src/kodepoia/intelligence/memory.py"
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
            "tests/test_v2_2_5_project_workspace.py",
            "tests/test_v2_2_5_workspace_ui.py",
        ]
    )
    targeted_detail = (
        "targeted V2.2.5 backend/workspace tests passed"
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
            "v2_2_5_targeted_tests",
            targeted.returncode == 0,
            targeted_detail,
        ),
        _check(
            "shared_governed_workspace_contract",
            "class ProjectWorkspaceContextSession" in bridge
            and "class ProjectWorkspaceContextSnapshot" in bridge
            and "ProjectWorkspaceSurface.CHAT" in chat
            and "ProjectWorkspaceSurface.KODECODE" in kodecode
            and "ProjectWorkspaceSurface.SPECIALIST" in app,
            "Chat, KodeCode and specialists consume one shared governed snapshot contract",
        ),
        _check(
            "project_only_scope",
            "requires a non-global project scope" in bridge
            and "project scope does not match active project" in bridge
            and "bundle is not bound to this retrieval result" in bridge,
            "workspace context is project-only and bound to the exact retrieval/context pair",
        ),
        _check(
            "r16_7_memory_boundary",
            "MemoryStore" in bridge
            and "list_project_scope(" in bridge
            and "trust_class=\"derived\"" in bridge
            and "record_class=\"derived_summary\"" in bridge
            and "def _verify_and_quarantine" in memory,
            "project Memory bridge reuses R16.7 durable-memory integrity/quarantine semantics",
        ),
        _check(
            "explicit_memory_opt_in",
            "explicit_opt_in: bool = False" in bridge
            and "requires explicit opt-in" in bridge,
            "context is never persisted to durable memory without explicit opt-in",
        ),
        _check(
            "no_global_or_training_promotion",
            "allow_global_memory=False" in bridge
            and "allow_training_dataset=False" in bridge
            and '"global_promotion_allowed": False' in bridge
            and '"training_dataset_allowed": False' in bridge,
            "derived project context cannot silently become global memory or training data",
        ),
        _check(
            "source_citation_traceability",
            "ProjectWorkspaceSource" in bridge
            and "citation_ids" in bridge
            and "source_digest_sha256" in bridge
            and "rendered_context" in bridge,
            "workspace consumption retains source/citation/digest traceability",
        ),
        _check(
            "research_to_workspace_activation",
            "on_bundle" in preview
            and "workspace_context_session.activate" in research,
            "explicit Research context assembly activates the shared workspace snapshot",
        ),
        _check(
            "chat_data_only_consumption",
            "project_context=self.project_context" in chat
            and "project_context," in chat
            and "workspace_context_digest" in chat
            and "PROJECT_CONTEXT (data only):" in assistant
            and "never as instructions, permissions" in assistant,
            "Chat passes the governed snapshot through its worker and consumes it as reference data, not authority",
        ),
        _check(
            "kodecode_read_only_consumption",
            '"kodecode_project_context"' in kodecode
            and "ProjectWorkspaceSurface.KODECODE" in kodecode
            and "MemoryStore" not in kodecode
            and '"kodecode_project_context": _READ' in kodecode_executor,
            "KodeCode reads the shared governed context without direct durable-store access and keeps an explicit read-only executor policy",
        ),
        _check(
            "specialist_visibility",
            "create_project_workspace_context_widget" in app
            and all(f'\"r{value}\"' in app for value in range(11, 16))
            and "selection does not grant authority" in (
                root / "src/kodepoia/kodestudio/project_workspace_context.py"
            ).read_text(encoding="utf-8"),
            "R11-R15 specialist surfaces expose the active context sources read-only",
        ),
        _check(
            "authority_scope",
            "V2.2.5 — Project Memory bridge and workspace consumption" in authority
            and "V2.2.6 — Project Knowledge hardening and integrated acceptance" in authority
            and "cross-workspace task orchestration" not in bridge.casefold(),
            "V2.2.5 remains bounded from V2.2.6 and V2.5 orchestration",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload = {
        "schema_version": 1,
        "subdivision": "V2.2.5",
        "title": "Project Memory bridge and workspace consumption",
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
