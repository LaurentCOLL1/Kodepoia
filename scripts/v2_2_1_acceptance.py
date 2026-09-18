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
        description="Kodepoia V2.2.1 Project Knowledge catalog and contracts acceptance"
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    observed = _run(["git", "rev-parse", "HEAD"])
    observed_sha = observed.stdout.strip().lower()

    root = Path(__file__).resolve().parents[1]
    knowledge = (root / "src/kodepoia/intelligence/project_knowledge.py").read_text(encoding="utf-8")
    memory = (root / "src/kodepoia/intelligence/memory.py").read_text(encoding="utf-8")
    packs = (root / "src/kodepoia/intelligence/research/synthesis.py").read_text(encoding="utf-8")
    workspace = (root / "src/kodepoia/kodecode/workspace.py").read_text(encoding="utf-8")
    authority = (root / "docs/roadmap/V2_2_PROJECT_KNOWLEDGE_CONTEXT_MEMORY.md").read_text(
        encoding="utf-8"
    )

    targeted = _run(
        [
            "python",
            "-m",
            "pytest",
            "-q",
            "tests/test_v2_2_1_project_knowledge.py",
        ]
    )
    targeted_detail = (
        "targeted V2.2.1 tests passed"
        if targeted.returncode == 0
        else (targeted.stdout + targeted.stderr)[-3000:]
    )

    checks = [
        _check("exact_head", observed.returncode == 0 and observed_sha == source_sha, observed_sha),
        _check("project_knowledge_tests", targeted.returncode == 0, targeted_detail),
        _check(
            "typed_contracts",
            "class ProjectKnowledgeItem" in knowledge
            and "class ProjectKnowledgeCatalog" in knowledge
            and "class ProjectKnowledgeState" in knowledge,
            "typed item/catalog/state contracts are present",
        ),
        _check(
            "deterministic_identity_and_digest",
            '"project_scope": scope' in knowledge
            and '"source_kind": self.source_kind.value' in knowledge
            and "digest_sha256" in knowledge,
            "knowledge identity is project-scoped and catalog/item digests are canonical",
        ),
        _check(
            "research_packs_immutable",
            "ResearchPackStore" in knowledge
            and "pack.digest_sha256 != path.stem" in knowledge
            and "Research Pack digest collision" in packs,
            "Research Packs are loaded and projected without rewriting immutable pack provenance",
        ),
        _check(
            "workspace_confined_files",
            "WorkspaceBoundary" in knowledge
            and "Project Knowledge cannot recursively index its derived catalog" in knowledge
            and "Path escapes workspace" in workspace,
            "project files stay inside WorkspaceBoundary and cannot self-index the derived catalog",
        ),
        _check(
            "verified_project_memory_only",
            "memory.list(scope=self.project_scope" in knowledge
            and "record.project_scope != self.project_scope" in knowledge
            and "integrity_digest" in memory,
            "memory projection is bounded to verified active-project MemoryStore records",
        ),
        _check(
            "derived_catalog_atomic_persistence",
            '".kodepoia/knowledge/catalog-v1.json"' in knowledge
            and "temporary.replace(path)" in knowledge,
            "only the derived catalog is atomically persisted below project metadata",
        ),
        _check(
            "secrets_and_untrusted_data",
            "redact_research_text" in knowledge
            and "ResearchGuard().wrap" in knowledge
            and "external_guarded_untrusted" in knowledge
            and "project_untrusted" in knowledge,
            "project knowledge remains redacted, guarded and explicitly non-authoritative",
        ),
        _check(
            "no_semantic_retrieval_or_context_injection",
            "semantic_search(" not in knowledge
            and "ContextBuilder" not in knowledge
            and ".add(" not in knowledge,
            "V2.2.1 does not implement semantic ranking, context injection or memory writes",
        ),
        _check(
            "authority_scope",
            "V2.2.1 — Project Knowledge catalog and contracts" in authority
            and "V2.2.2 — Bounded semantic retrieval" in authority
            and "V2.2.1 may begin only" in authority,
            "normalized authority permits V2.2.1 while later V2.2 subdivisions remain separate",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload = {
        "schema_version": 1,
        "subdivision": "V2.2.1",
        "title": "Project Knowledge catalog and contracts",
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
