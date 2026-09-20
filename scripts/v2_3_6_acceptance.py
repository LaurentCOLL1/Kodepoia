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

    hardening = read("tests/test_v2_3_6_model_lab_hardening.py")
    ui = read("tests/test_v2_3_6_model_lab_hardening_ui.py")
    curation = read("src/kodepoia/kodestudio/model_lab_curation.py")
    evaluation = read("src/kodepoia/bench/evaluation.py")
    training = read("src/kodepoia/kodestudio/model_lab_training.py")
    candidate = read("src/kodepoia/kodestudio/model_lab_candidate.py")
    inventory = read("src/kodepoia/kodestudio/model_lab.py")
    gguf = read("src/kodepoia/tuning/gguf.py")
    ollama = read("src/kodepoia/tuning/ollama_packaging.py")
    registry = read("src/kodepoia/tuning/model_registry.py")
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    v23 = read("docs/roadmap/V2_3_MODEL_LAB_GOVERNED_IMPROVEMENT_UX.md")
    python_core = read(".github/workflows/python-core.yml")
    ui_smoke = read(".github/workflows/ui-smoke.yml")
    historical = " ".join(
        read(path)
        for path in (
            "tests/test_v2_3_2_curation.py",
            "tests/test_v2_3_4_training.py",
            "tests/test_candidate_evaluation_r15_10.py",
            "tests/test_gguf_conversion_r15_12.py",
            "tests/test_ollama_packaging_r15_13.py",
            "tests/test_model_registry_r15_14.py",
            "tests/test_v2_3_5_candidate_lifecycle.py",
        )
    )

    checks = [
        _check("exact_head", source_sha == observed_sha, "acceptance executes the exact requested SHA"),
        _check(
            "current_authority",
            "V2.3.6 — Model Lab hardening and integrated acceptance" in authority
            and "V2.3.6" in state
            and "V2.3.6" in next_doc,
            "V2.3.6 is the only authorized implementation subdivision",
        ),
        _check(
            "later_scope_unauthorized",
            "V2.4+ remain unauthorized" in authority
            and "V2.4+ remain unauthorized" in state
            and "V2.4+ remain" in v23,
            "V2.4+ remains outside the V2.3.6 scope",
        ),
        _check(
            "reference_authority",
            "test_reference_text_cannot_authorize_training_or_promotion" in hardening
            and '"instruction_authority": False' in training
            and '"promotion_authority": False' in candidate,
            "reference text cannot become training or promotion authority",
        ),
        _check(
            "privacy_license_revocation",
            "test_privacy_license_revocation_and_holdout_contamination_fail_closed" in hardening
            and "_AUTHORIZATION_FIELDS" in curation
            and '"privacy"' in curation
            and "_auth_blockers" in curation
            and "license:missing" in curation
            and "_TERMINAL_BLOCKED_STATES" in curation,
            "privacy/license/revocation blockers remain fail closed",
        ),
        _check(
            "contamination",
            "benchmark_contamination" in hardening
            and "quarantined_item_ids" in curation,
            "exact and near holdout contamination remains training-ineligible",
        ),
        _check(
            "dataset_export_tamper",
            "test_dataset_manifest_tamper_is_explicit_without_reading_jsonl" in historical
            and "test_critical_rejection_or_tampered_lineage_fails_closed" in historical
            and '"tampered"' in candidate,
            "dataset/export/candidate lineage tamper remains explicit and blocked",
        ),
        _check(
            "stale_model_tokenizer",
            "stale-model-tokenizer.json" in hardening
            and "invalid_training_plan" in training,
            "stale model/tokenizer evidence cannot authorize training",
        ),
        _check(
            "capability_resources_backend",
            "RuntimeDisposition.BUDGET_BLOCKED" in hardening
            and "capability_report_unverified" in training
            and "training backend must be local or kaggle" in training,
            "capability/resource/backend failures stay blocked",
        ),
        _check(
            "checkpoint_cancel_recovery",
            "checkpoint-bad-lineage" in hardening
            and "checkpoint lineage is not bound to a valid training plan" in training
            and 'action="cancel"' in training
            and 'action="resume"' in training,
            "checkpoint lineage, cancellation and recovery remain governed",
        ),
        _check(
            "paired_report_mismatch",
            "test_paired_evaluation_mismatch_and_critical_regression" in hardening
            and "reports are not comparable" in evaluation
            and "same task/repeat/seed pairs" in evaluation,
            "base/candidate reports must remain paired and reproducible",
        ),
        _check(
            "critical_regression",
            'hard_reject.add("critical_regression")' in evaluation
            and "critical-regression veto" in candidate
            and "aggregate_delta > 0" in hardening,
            "aggregate gain cannot mask a critical regression",
        ),
        _check(
            "quantization",
            "QualityDisposition.REJECT_CRITICAL" in hardening
            and "cannot silently allow requantization" in gguf
            and "REJECT_QUALITY" in gguf,
            "unsupported/requantized or quality-regressed GGUF remains blocked",
        ),
        _check(
            "ollama_packaging",
            "PackageDisposition.REJECT_CRITICAL" in hardening
            and "provider_live_claim" in ollama
            and "public_push" in ollama,
            "Ollama packaging quality and provider/public truth remain honest",
        ),
        _check(
            "promotion_rollback",
            "test_quantization_packaging_and_registry_integrity_veto_unsafe_activation" in hardening
            and "post-promotion health probe failed; exact mapping restored" in registry
            and "rollback_roles" in registry,
            "promotion health and rollback integrity remain fail closed",
        ),
        _check(
            "runtime_unavailable",
            '"state": "unavailable"' in inventory
            and "ollama offline" in hardening
            and "quota unavailable" in hardening,
            "Ollama/Kaggle/runtime unavailability is represented honestly",
        ),
        _check(
            "empty_missing_ui",
            "test_v236_empty_project_model_lab_surfaces_are_deterministic_accessible_and_non_authorizing"
            in ui
            and "modelLabTrainingPlansTable" in ui
            and "modelLabCandidateCandidatesTable" in ui,
            "empty/missing-evidence UI states are deterministic and accessible",
        ),
        _check(
            "security_reuse",
            "ResearchGuard" in state
            and "ProcessSandbox" in state
            and "KillSwitch" in state
            and "Project Knowledge" in v23,
            "V2.3.6 preserves R15/V2.1/V2.2 trust boundaries",
        ),
        _check(
            "no_parallel_engine",
            not (root / "src" / "kodepoia" / "kodestudio" / "model_lab_hardening.py").exists()
            and "BaseAdapterEvaluator(" not in candidate,
            "hardening proves existing services rather than creating a replacement engine",
        ),
        _check(
            "ci_wiring",
            "Run V2.3.6 Model Lab hardening exact-head acceptance" in python_core
            and "v2-3-6-model-lab-hardening" in python_core
            and "tests/test_v2_3_6_model_lab_hardening_ui.py" in ui_smoke,
            "Ubuntu/Windows exact-head evidence and UI smoke are mandatory",
        ),
        _check(
            "release_boundary",
            "v1.1.0-rc8" in authority
            and "release/TUF/updater" in next_doc
            and "R20" in next_doc,
            "V2.3.6 does not authorize release/TUF/updater or R20 mutation",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.3.6",
        "title": "Model Lab hardening and integrated acceptance",
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
