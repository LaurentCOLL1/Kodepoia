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
        description="Kodepoia V2.2.2 bounded semantic retrieval acceptance"
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    observed = _run(["git", "rev-parse", "HEAD"])
    observed_sha = observed.stdout.strip().lower()

    root = Path(__file__).resolve().parents[1]
    retrieval = (
        root / "src/kodepoia/intelligence/project_retrieval.py"
    ).read_text(encoding="utf-8")
    knowledge = (
        root / "src/kodepoia/intelligence/project_knowledge.py"
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
            "tests/test_v2_2_2_project_retrieval.py",
        ]
    )
    targeted_detail = (
        "targeted V2.2.2 tests passed"
        if targeted.returncode == 0
        else (targeted.stdout + targeted.stderr)[-3000:]
    )

    scope_index = retrieval.find(
        "if request.project_scope != catalog.project_scope"
    )
    provider_index = retrieval.find("identity = provider.identity")
    embed_index = retrieval.find("provider.embed(texts)")
    limit_index = retrieval.find(
        "if eligible_count > request.max_candidates"
    )

    checks = [
        _check("exact_head", observed.returncode == 0 and observed_sha == source_sha, observed_sha),
        _check("project_retrieval_tests", targeted.returncode == 0, targeted_detail),
        _check(
            "bounded_request_result_contracts",
            "class ProjectRetrievalRequest" in retrieval
            and "class ProjectRetrievalResult" in retrieval
            and "limit must be between 1" in retrieval
            and "max_candidates must be between 1" in retrieval,
            "request/result contracts bound result and candidate counts",
        ),
        _check(
            "explicit_provider_states",
            'READY = "ready"' in retrieval
            and 'EMPTY = "empty"' in retrieval
            and 'EMBEDDING_UNAVAILABLE = "embedding_unavailable"' in retrieval
            and 'CANDIDATE_LIMIT_EXCEEDED = "candidate_limit_exceeded"' in retrieval,
            "ready, valid-empty, unavailable and candidate-limit states are distinct",
        ),
        _check(
            "scope_before_scoring",
            -1 < scope_index < provider_index < embed_index
            and -1 < limit_index < provider_index,
            "project scope and candidate bounds are enforced before provider access/scoring",
        ),
        _check(
            "deterministic_semantic_scoring",
            "def _cosine(" in retrieval
            and "hits.sort(" in retrieval
            and "hit.content_sha256" in retrieval
            and "hit.primary_knowledge_id" in retrieval,
            "cosine scoring plus deterministic tie-break ordering is explicit",
        ),
        _check(
            "duplicate_provenance_preserved",
            "ProjectRetrievalSourceRef.from_item" in retrieval
            and "grouped.setdefault(item.content_sha256" in retrieval
            and '"provenance": self.provenance' in retrieval,
            "duplicate content is normalized while every source provenance reference survives",
        ),
        _check(
            "no_hidden_network_or_download",
            "Ollama" not in retrieval
            and "requests" not in retrieval
            and "httpx" not in retrieval
            and "urllib" not in retrieval
            and "download" not in retrieval.casefold(),
            "retriever consumes only an explicitly supplied embedding provider",
        ),
        _check(
            "no_retrieval_mutation",
            "ProjectKnowledgeStore" not in retrieval
            and ".save(" not in retrieval
            and ".add(" not in retrieval
            and "ProjectKnowledgeCatalog" in knowledge,
            "retrieval does not persist catalog or memory mutations",
        ),
        _check(
            "later_context_work_remains_out_of_scope",
            "ContextBuilder" not in retrieval
            and "V2.2.2 — Bounded semantic retrieval" in authority
            and "V2.2.3 — Explainable Context Builder" in authority,
            "V2.2.2 remains separate from Context Builder/context injection",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload = {
        "schema_version": 1,
        "subdivision": "V2.2.2",
        "title": "Bounded semantic retrieval",
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
