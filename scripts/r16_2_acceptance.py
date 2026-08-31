from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from kodepoia.quality.prompt_injection import (
    PromptInjectionStatus,
    load_supplemental_cases,
    run_prompt_injection_acceptance,
)
from kodepoia.quality.redteam import load_redteam_corpus


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_CORPUS = ROOT / "tests" / "fixtures" / "r16" / "redteam-corpus.json"
SUPPLEMENTAL_CASES = ROOT / "tests" / "fixtures" / "r16" / "prompt-injection-cases.json"


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).strip().lower()


def build_acceptance(source_sha: str) -> dict[str, Any]:
    source = source_sha.strip().lower()
    actual = _git_head()
    if actual != source:
        raise ValueError(f"exact-source mismatch: expected {source}, got {actual}")
    corpus = load_redteam_corpus(CANONICAL_CORPUS, repository_root=ROOT)
    supplemental = load_supplemental_cases(SUPPLEMENTAL_CASES, repository_root=ROOT)
    report = run_prompt_injection_acceptance(
        source_sha=source,
        corpus=corpus,
        supplemental_cases=supplemental,
    )
    payload = {
        "phase": "R16.2",
        "title": "Prompt-injection and untrusted-content hardening",
        "source_sha": source,
        "manual_state": "NONE",
        "synthetic_only": True,
        "live_secrets": False,
        "destructive_actions": False,
        "report": report.to_dict(),
        "summary": {
            "status": report.status.value,
            "security_claim": report.security_claim,
            "critical_veto": report.critical_veto,
            "cases": len(report.results),
            "passed": sum(item.passed for item in report.results),
            "failed": sum(not item.passed for item in report.results),
        },
    }
    if report.status is not PromptInjectionStatus.PASS:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit exact-source R16.2 prompt-injection acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = build_acceptance(args.source_sha)
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
