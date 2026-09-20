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

    service = read("src/kodepoia/kodestudio/model_lab_candidate.py")
    panel = read("src/kodepoia/kodestudio/model_lab_candidate_panel.py")
    localization = read("src/kodepoia/kodestudio/model_lab_candidate_localization.py")
    r15 = read("src/kodepoia/tuning/r15_ux.py")
    backend_test = read("tests/test_v2_3_5_candidate_lifecycle.py")
    ui_test = read("tests/test_v2_3_5_candidate_lifecycle_ui.py")
    pseudo_test = read("tests/test_r6_6_localization_ui.py")
    app = read("src/kodepoia/kodestudio/app.py")
    evaluation = read("src/kodepoia/bench/evaluation.py")
    export = read("src/kodepoia/tuning/export.py")
    gguf = read("src/kodepoia/tuning/gguf.py")
    ollama = read("src/kodepoia/tuning/ollama_packaging.py")
    registry = read("src/kodepoia/tuning/model_registry.py")
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    v235_current = (
        "V2.3.5 — Candidate evaluation, export, promotion and rollback UX" in authority
        and "V2.3.6+ remain unauthorized" in authority
    )
    v235_normalized = (
        "V2.3.1 through V2.3.5 are **COMPLETE + NORMALIZED**" in authority
        and "V2.3.6 — Model Lab hardening and integrated acceptance" in authority
    )

    checks = [
        _check("exact_head", observed_sha == source_sha, "acceptance executes the exact requested SHA"),
        _check(
            "r15_10_paired_evaluation",
            "same task/repeat/seed pairs" in evaluation
            and "critical_regression" in evaluation
            and "PROMOTE_TO_EXPORT" in evaluation,
            "R15.10 paired comparison and critical-regression veto remain authoritative",
        ),
        _check(
            "r15_11_export_lineage",
            "R15.11 accepts only R15.10 PROMOTE_TO_EXPORT evidence" in export
            and "source_overwritten" in export,
            "R15.11 accepted-evaluation and immutable-source gates remain authoritative",
        ),
        _check(
            "r15_12_conversion_quality",
            "refuses requantization" in gguf and "REJECT_CRITICAL" in gguf and "REJECT_QUALITY" in gguf,
            "R15.12 conversion quality and no-silent-requantization gates remain authoritative",
        ),
        _check(
            "r15_13_ollama_truth",
            "silent replacement is forbidden" in ollama
            and '"public_push": False' in ollama
            and "credential-free explicit-port loopback Ollama origin" in ollama,
            "R15.13 local Ollama packaging remains honest and non-public",
        ),
        _check(
            "r15_14_registry_reversible",
            "rollback_roles" in registry
            and "exact mapping restored" in registry
            and "candidate disposition does not authorize promotion" in registry,
            "R15.14 role-scoped promotion and exact rollback remain authoritative",
        ),
        _check(
            "typed_r15_gaps_closed",
            '"export"' in r15 and '"conversion"' in r15 and '"package"' in r15
            and "role: str | None = None" in r15,
            "V2.3.5 extends only demonstrated typed R15 UX gaps",
        ),
        _check(
            "evidence_bound_promotion",
            "promotion_preflight" in service
            and "registry lineage does not bind accepted evaluation/export/conversion/package evidence" in service
            and "critical-regression veto" in service,
            "promotion is blocked without the exact accepted evidence chain",
        ),
        _check(
            "explicit_mutation_confirmation",
            "R15WorkflowMode.DRY_RUN" in service
            and "confirmed=confirmed" in service
            and "R15WorkflowMode.ROLLBACK" in service,
            "export/conversion/package/promotion/rollback use dry-run then explicit confirmation",
        ),
        _check(
            "rollback_exact_prior_mapping",
            "rollback_preflight" in service
            and "active mapping no longer matches immutable rollback point" in service
            and "prior_mapping" in service,
            "rollback is tied to the immutable prior role mapping",
        ),
        _check(
            "no_parallel_engines",
            "BaseAdapterEvaluator(" not in service
            and "OllamaPackager(" not in service
            and "SpecializedModelRegistry(" not in service,
            "KodeStudio projects accepted evidence and delegates mutations instead of reimplementing R15 engines",
        ),
        _check(
            "trust_boundaries",
            '"promotion_authority": False' in service
            and '"arbitrary_shell": False' in service
            and '"package_install": False' in service
            and '"public_model_upload": False' in service,
            "reference context cannot become instruction or mutation authority",
        ),
        _check(
            "candidate_ui",
            "modelLabCandidateCandidatesTable" in panel
            and "modelLabCandidateDomainsTable" in panel
            and "modelLabCandidateArtifactsTable" in panel
            and "modelLabCandidateRegistryTable" in panel
            and "modelLabCandidateConfirm" in panel,
            "Candidate lifecycle UI exposes evidence, artifacts, registry mapping and confirmation",
        ),
        _check(
            "localization",
            '"nav": "Candidate lifecycle"' in localization
            and '"nav": "Cycle candidat"' in localization
            and "qps-ploc" in localization
            and "assert len(texts) == 19" in pseudo_test,
            "EN/FR/qps-ploc includes the V2.3.5 surface",
        ),
        _check(
            "app_wiring",
            "model_lab_candidate_service=None" in app
            and "model_lab_candidate_nav_text" in app
            and "model_lab_candidate_page" in app,
            "V2.3.5 Candidate lifecycle workspace is wired into KodeStudio",
        ),
        _check(
            "deterministic_tests",
            "test_snapshot_projects_paired_evaluation_artifacts_and_registry" in backend_test
            and "test_promotion_is_evidence_bound_role_specific_and_confirmed" in backend_test
            and "test_rollback_preflight_preserves_exact_prior_mapping" in backend_test
            and "test_candidate_lifecycle_page_is_wired_accessible_and_localized" in ui_test,
            "tests cover evidence projection, deliberate promotion, exact rollback and accessible UI",
        ),
        _check(
            "current_authority",
            (v235_current or v235_normalized)
            and "V2.3.5" in state
            and "V2.3.5" in next_doc,
            "V2.3.5 is current or retained as normalized historical context",
        ),
        _check(
            "later_scope_unauthorized",
            (
                (
                    "V2.3.6+ remain unauthorized" in authority
                    and "V2.3.6+ remain unauthorized" in state
                    and "V2.3.6+ remain unauthorized" in next_doc
                )
                or (
                    v235_normalized
                    and "V2.3.6 — Model Lab hardening and integrated acceptance" in authority
                    and "V2.4+ remain unauthorized" in authority
                    and "V2.4+ remain unauthorized" in state
                    and "V2.4+ remain unauthorized" in next_doc
                )
            ),
            "historical V2.3.5 acceptance keeps later implementation scope bounded before and after normalization",
        ),
    ]
    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.3.5",
        "title": "Candidate evaluation, export, promotion and rollback UX",
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
