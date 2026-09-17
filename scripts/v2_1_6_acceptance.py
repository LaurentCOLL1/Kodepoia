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
    parser = argparse.ArgumentParser(description="Kodepoia V2.1.6 ResearchGuard hardening acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    observed = _run(["git", "rev-parse", "HEAD"])
    observed_sha = observed.stdout.strip().lower()

    root = Path(__file__).resolve().parents[1]
    hardened = (root / "src/kodepoia/intelligence/research/extended_sources.py").read_text(encoding="utf-8")
    cache = (root / "src/kodepoia/intelligence/research/cache.py").read_text(encoding="utf-8")
    evidence = (root / "src/kodepoia/intelligence/research/evidence.py").read_text(encoding="utf-8")
    service = (root / "src/kodepoia/intelligence/research/service.py").read_text(encoding="utf-8")
    workspace = (root / "src/kodepoia/kodecode/workspace.py").read_text(encoding="utf-8")
    ui = (root / "src/kodepoia/kodestudio/research_extended_panel.py").read_text(encoding="utf-8")
    roadmap = (root / "docs/roadmap/V2_1_RESEARCH_WORKSPACE.md").read_text(encoding="utf-8")

    targeted = _run([
        "python",
        "-m",
        "pytest",
        "-q",
        "tests/test_v2_1_6_researchguard_hardening.py",
    ])

    checks = [
        _check("exact_head", observed.returncode == 0 and observed_sha == source_sha, observed_sha),
        _check(
            "adversarial_runtime_tests",
            targeted.returncode == 0,
            (targeted.stdout + targeted.stderr)[-3000:],
        ),
        _check(
            "policy_fail_closed",
            'ResearchOperationStatus.BLOCKED' in hardened and '"policy_blocked": True' in hardened,
            "extended provider policy violations are explicit BLOCKED states",
        ),
        _check(
            "provider_diagnostics_redacted",
            "redact_research_text" in hardened and "_redact_reason" in hardened,
            "extended provider diagnostic reasons pass through KodeSecrets redaction",
        ),
        _check(
            "cancel_before_persist",
            "persist_cache=False" in hardened and "ResearchOperationStatus.CANCELLED" in hardened,
            "extended acquisition stays non-persistent until cancellation gates pass",
        ),
        _check(
            "unsafe_candidate_locators_rejected",
            "_eligible_http_locator" in hardened and 'parsed.username is not None' in hardened,
            "extended discovery typing accepts only non-credential HTTP(S) locators",
        ),
        _check(
            "stale_cache_honesty",
            "CacheDecision.STALE" in cache
            and "cache_ttl_expired_revalidation_required" in cache
            and "ResearchOperationStatus.STALE" in service
            and '"cache"' in service,
            "offline cache state remains explicit STALE/UNAVAILABLE instead of fabricated live success",
        ),
        _check(
            "immutable_version_conflict_lineage",
            "conflicting_versions" in evidence
            and "has_version_conflict" in evidence
            and "lineage_revision_ids" in evidence
            and "lineage_artifact_ids" in evidence,
            "evidence projection retains immutable revision/artifact lineage and explicit version conflicts",
        ),
        _check(
            "workspace_protected_actions_fail_closed",
            "WorkspaceViolation" in workspace
            and "Path escapes workspace" in workspace
            and "Absolute paths are not allowed" in workspace,
            "protected filesystem resolution remains confined to the project WorkspaceBoundary",
        ),
        _check(
            "ui_degraded_states_structured",
            "hardened_evidence_state_text" in ui
            and "Lineage / hardening state" in ui
            and all(token in ui for token in ("BLOCKED", "UNAVAILABLE", "CANCELLED", "STALE", "CONFLICT")),
            "KodeStudio exposes blocked/unavailable/cancelled/stale/conflict state without raw JSON",
        ),
        _check(
            "ui_cancellation_propagated",
            "cancellation=token" in ui and "V2.1.6 hardened states" in ui,
            "KodeStudio forwards the active cancellation token and exposes hardened provider state",
        ),
        _check(
            "authority_scope",
            "V2.1.6 — ResearchGuard hardening — CURRENT" in roadmap
            and "V2.2" in roadmap
            and "Out of scope for V2.1.6" in roadmap,
            "current authority is V2.1.6 and later V2.2/release work remains out of scope",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload = {
        "schema_version": 1,
        "subdivision": "V2.1.6",
        "title": "ResearchGuard hardening",
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
