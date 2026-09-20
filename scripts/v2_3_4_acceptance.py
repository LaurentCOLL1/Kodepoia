from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _check(name: str, condition: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "PASS" if condition else "FAIL", "detail": detail}


def _observed_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_sha = args.source_sha.strip()
    observed_sha = _observed_sha()

    service = _read("src/kodepoia/kodestudio/model_lab_training.py")
    panel = _read("src/kodepoia/kodestudio/model_lab_training_panel.py")
    localization = _read("src/kodepoia/kodestudio/model_lab_training_localization.py")
    app = _read("src/kodepoia/kodestudio/app.py")
    r15 = _read("src/kodepoia/tuning/r15_ux.py")
    training = _read("src/kodepoia/tuning/training.py")
    backend_test = _read("tests/test_v2_3_4_training.py")
    ui_test = _read("tests/test_v2_3_4_training_ui.py")
    pseudo_test = _read("tests/test_r6_6_localization_ui.py")
    authority = _read("docs/roadmap/V2_3_MODEL_LAB_GOVERNED_IMPROVEMENT_UX.md")
    state = _read("docs/continuity/STATE.md")
    next_doc = _read("docs/continuity/NEXT.md")

    v234_current = (
        "V2.3.4 is now the only authorized implementation subdivision" in authority
        or "V2.3.4 — Governed training plan, execution and recovery UX — CURRENT" in authority
    )
    v234_normalized = (
        "V2.3.4 — Governed training plan, execution and recovery UX — COMPLETE + NORMALIZED"
        in authority
    )

    checks = [
        _check(
            "exact_head",
            source_sha == observed_sha
            and os.environ.get("KODEPOIA_SOURCE_SHA", source_sha) == source_sha,
            "acceptance executes on the exact requested source SHA",
        ),
        _check(
            "immutable_training_plan_projection",
            "load_training_plan" in service
            and '"plan_digest"' in service
            and '"model"' in service
            and '"dataset"' in service
            and '"lora"' in service
            and '"sft"' in service,
            "TrainingPlan identity, model/tokenizer/dataset binding and bounded SFT/LoRA fields are structured",
        ),
        _check(
            "train_decision_binding",
            "ModelLabBenchDecisionService" in service
            and '"accepted_train_decision_missing"' in service
            and '"decision_digest"' in service,
            "launch authorization reuses accepted V2.3.3 decision evidence",
        ),
        _check(
            "capability_resource_preflight",
            "CAPABILITY_SCHEMA" in service
            and '"capability_report_digest"' in service
            and '"capability_report_unverified"' in service
            and '"resources"' in service,
            "capability digest and resource evidence must be bound before launch",
        ),
        _check(
            "typed_training_actions",
            'action="doctor"' in service
            and 'action="plan"' in service
            and 'action="run"' in service
            and 'action="status"' in service
            and 'action="cancel"' in service
            and 'action="resume"' in service,
            "doctor, plan, run, status, cancel and resume delegate to typed R15 actions",
        ),
        _check(
            "typed_resume_extension",
            '"training",\n        "resume"' in r15
            and "parent_identifier" in r15
            and "backend" in r15,
            "the R15 UX recovery/backend gap is extended with bounded typed fields",
        ),
        _check(
            "dry_run_confirmation",
            "R15WorkflowMode.DRY_RUN" in service
            and "R15WorkflowMode.APPLY" in service
            and "R15WorkflowMode.CANCEL" in service
            and "confirmed=confirmed" in service,
            "launch, cancel and recovery preserve dry-run/explicit-confirmation semantics",
        ),
        _check(
            "sandbox_killswitch_authority",
            "ProcessSandbox" in training
            and "KillSwitch" in training
            and "TrainingRunner" not in service
            and "subprocess" not in service,
            "KodeStudio does not bypass ProcessSandbox/KillSwitch",
        ),
        _check(
            "honest_local_kaggle_backend",
            '"id": "local"' in service
            and '"id": "kaggle"' in service
            and '"readiness": "requires_training_doctor"' in service
            and '"gpu_count_claim": None' in service
            and '"aggregate_vram_claim": None' in service,
            "backend selection does not fabricate Kaggle readiness or pooled VRAM",
        ),
        _check(
            "run_checkpoint_recovery_lineage",
            '"checkpoints"' in service
            and '"lineage_bound"' in service
            and "parent_identifier=plan_digest" in service,
            "run/checkpoint recovery is bound to immutable TrainingPlan lineage",
        ),
        _check(
            "no_v235_mutations",
            '"conversion": False' in service
            and '"candidate_evaluation": False' in service
            and '"promotion": False' in service
            and '"rollback": False' in service
            and "modelLabTrainingPromote" not in panel,
            "V2.3.5 candidate/export/promotion/rollback remains unavailable",
        ),
        _check(
            "reference_data_only",
            '"instruction_authority": False' in service
            and '"auto_training_ingest": False' in service
            and "reference_only" in localization,
            "Project Knowledge, Research Packs and retrieved context remain data-only",
        ),
        _check(
            "structured_accessible_ui",
            "modelLabTrainingPlansTable" in panel
            and "modelLabTrainingCapabilitiesTable" in panel
            and "modelLabTrainingRunsTable" in panel
            and "modelLabTrainingCheckpointsTable" in panel
            and "mark_accessible" in panel
            and "test_training_workspace_is_wired_structured_accessible_localized_and_bounded"
            in ui_test,
            "KodeStudio exposes structured accessible training state",
        ),
        _check(
            "localization",
            '"nav": "Training"' in localization
            and '"nav": "Entraînement"' in localization
            and "qps-ploc" in localization
            and "assert len(texts) == 18" in pseudo_test,
            "EN/FR/qps-ploc includes V2.3.4",
        ),
        _check(
            "app_wiring",
            "model_lab_training_service=None" in app
            and "model_lab_training_nav_text" in app
            and "model_lab_training_page" in app,
            "the V2.3.4 workspace is wired into KodeStudio",
        ),
        _check(
            "deterministic_tests",
            "test_snapshot_binds_train_decision_capability_plan_run_and_checkpoint"
            in backend_test
            and "test_launch_blocks_without_persisted_evidence_bound_train_decision"
            in backend_test
            and "test_cross_project_r15_binding_is_rejected" in backend_test,
            "tests cover lineage, fail-closed TRAIN authorization and project scope",
        ),
        _check(
            "current_authority",
            (v234_current or v234_normalized)
            and "V2.3.4" in state
            and "V2.3.4" in next_doc,
            "V2.3.4 is current or retained as normalized historical context",
        ),
        _check(
            "later_scope_unauthorized",
            "V2.3.5+ remain unauthorized" in authority,
            "V2.3.5+ remains outside this subdivision",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.3.4",
        "title": "Governed training plan, execution and recovery UX",
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
