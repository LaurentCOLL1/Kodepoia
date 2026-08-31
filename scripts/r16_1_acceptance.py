from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from kodepoia.quality.redteam import (
    CasePolarity,
    ExpectedDecision,
    HarnessStatus,
    RedTeamRunner,
    load_redteam_corpus,
    policy_sha256,
)

_POLICY = {
    "version": "r16.1-v1",
    "invariants": (
        "instruction-data-separation",
        "least-privilege",
        "no-secret-as-context-default",
        "network-off-by-default",
        "memory-is-evidence-not-policy",
        "typed-operations-over-shell-text",
        "workspace-boundary",
        "bounded-resource-consumption",
        "client-input-is-intent",
        "recovery-before-continuation",
        "critical-veto",
    ),
    "security_claim_in_baseline": False,
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _git_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        encoding="utf-8",
    ).strip().lower()


def build_acceptance(*, root: Path, source_sha: str, corpus_path: Path) -> dict[str, Any]:
    exact_source = source_sha.strip().lower()
    if _git_head(root) != exact_source:
        raise RuntimeError("R16.1 acceptance source SHA does not match checked-out HEAD")

    corpus = load_redteam_corpus(corpus_path, repository_root=root)
    policy_digest = policy_sha256(_POLICY)
    runner = RedTeamRunner(corpus)
    baseline = runner.run(source_sha=exact_source, policy_sha256=policy_digest)

    def bypass(case):
        if case.polarity is CasePolarity.ADVERSARIAL:
            return ExpectedDecision.ALLOW
        return case.expected_decision

    negative_control = runner.run(
        source_sha=exact_source,
        policy_sha256=policy_digest,
        evaluator=bypass,
    )

    coverage = corpus.coverage()
    checks = {
        "exact_source_bound": baseline.source_sha == exact_source,
        "corpus_declared_immutable": corpus.metadata.get("immutable") is True,
        "corpus_synthetic_only": corpus.metadata.get("synthetic_only") is True,
        "corpus_digest_bound": baseline.corpus_sha256 == corpus.corpus_sha256,
        "case_set_digest_bound": baseline.case_set_sha256 == corpus.case_set_sha256,
        "policy_digest_bound": baseline.policy_sha256 == policy_digest,
        "baseline_mutation_free": baseline.mode == "mutation-free-contract",
        "baseline_not_security_claim": baseline.security_claim is False,
        "baseline_harness_pass": baseline.status is HarnessStatus.PASS,
        "critical_boundary_coverage": all(
            int(item["benign"]) >= 1 and int(item["adversarial"]) >= 1
            for item in coverage.values()
            if bool(item["critical"])
        ),
        "negative_control_fails": negative_control.status is HarnessStatus.FAIL,
        "negative_control_critical_veto": negative_control.critical_veto is True,
        "negative_control_has_failed_cases": any(
            item.passed is False for item in negative_control.results
        ),
    }
    if not all(checks.values()):
        failed = sorted(name for name, passed in checks.items() if not passed)
        raise RuntimeError(f"R16.1 acceptance failed: {', '.join(failed)}")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "source_sha": exact_source,
        "policy_sha256": policy_digest,
        "corpus_sha256": corpus.corpus_sha256,
        "case_set_sha256": corpus.case_set_sha256,
        "boundary_count": len(corpus.boundaries),
        "case_count": len(corpus.cases),
        "checks": checks,
        "baseline": baseline.to_dict(),
        "negative_control": {
            "status": negative_control.status.value,
            "critical_veto": negative_control.critical_veto,
            "failed_case_ids": [
                item.id for item in negative_control.results if item.passed is False
            ],
            "semantic_sha256": negative_control.semantic_sha256,
        },
        "secrets_exposed": False,
        "manual_state": "NONE",
    }
    payload["acceptance_sha256"] = hashlib.sha256(
        _canonical_json(payload).encode("utf-8")
    ).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic R16.1 red-team harness acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument(
        "--corpus",
        default="tests/fixtures/r16/redteam-corpus.json",
    )
    parser.add_argument(
        "--output",
        default="artifacts/r16_1_acceptance.json",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    corpus_path = Path(args.corpus)
    if not corpus_path.is_absolute():
        corpus_path = root / corpus_path
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path

    payload = build_acceptance(
        root=root,
        source_sha=args.source_sha,
        corpus_path=corpus_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
