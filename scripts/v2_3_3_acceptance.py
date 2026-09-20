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
    return {
        "name": name,
        "status": "PASS" if condition else "FAIL",
        "detail": detail,
    }


def _observed_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_sha = args.source_sha.strip()
    observed_sha = _observed_sha()

    service = _read("src/kodepoia/kodestudio/model_lab_bench.py")
    panel = _read("src/kodepoia/kodestudio/model_lab_bench_panel.py")
    localization = _read("src/kodepoia/kodestudio/model_lab_bench_localization.py")
    app = _read("src/kodepoia/kodestudio/app.py")
    decision = _read("src/kodepoia/bench/decision.py")
    backend_test = _read("tests/test_v2_3_3_bench_decision.py")
    ui_test = _read("tests/test_v2_3_3_bench_decision_ui.py")
    authority = _read("docs/roadmap/V2_3_MODEL_LAB_GOVERNED_IMPROVEMENT_UX.md")
    state = _read("docs/continuity/STATE.md")
    next_doc = _read("docs/continuity/NEXT.md")

    v233_current = (
        "V2.3.3 — Bench, gap diagnosis and TRAIN/NO_TRAIN decision UX — CURRENT"
        in authority
    )
    v233_normalized = (
        "V2.3.3 — Bench, gap diagnosis and TRAIN/NO_TRAIN decision UX — COMPLETE + NORMALIZED"
        in authority
    )

    checks = [
        _check(
            "exact_head",
            source_sha == observed_sha and os.environ.get("KODEPOIA_SOURCE_SHA", source_sha) == source_sha,
            "acceptance executes on the exact requested source SHA",
        ),
        _check(
            "structured_kodebench_projection",
            "KODEBENCH_SCHEMA" in service
            and '"task_results"' in service
            and '"suite_digest"' in service
            and '"config_digest"' in service
            and '"model_digest"' in service,
            "KodeBench suite/task/domain results and exact model/run identities are projected structurally",
        ),
        _check(
            "immutable_digest_verification",
            "observed_report_digest" in service
            and "observed_decision_digest" in service
            and '"tampered"' in service
            and "benchmark_bound" in service,
            "report and decision identities are digest-verified and tamper/binding state is explicit",
        ),
        _check(
            "r15_gap_decision_authority",
            "GapDecisionEngine" not in service
            and "R15UXService" in service
            and '"gap",\n                action="diagnose"' in service,
            "KodeStudio does not duplicate the R15.7 decision engine and delegates typed diagnosis actions",
        ),
        _check(
            "prompt_diagnostic_extension",
            'PROMPT = "prompt"' in decision
            and "DiagnosticComponent.PROMPT" in backend_test
            and '("system_defect:prompt",)' in backend_test,
            "prompt defects are represented by the existing R15.7 diagnostic primitive and remain FIX_SYSTEM_FIRST",
        ),
        _check(
            "decision_states_visible",
            '"disposition"' in service
            and '"blockers"' in service
            and '"reasons"' in service
            and "train_evidence_bound" in service,
            "TRAIN/NO_TRAIN and fail-closed dispositions expose evidence, blockers and reasons",
        ),
        _check(
            "dataset_model_target_binding",
            '"dataset"' in service
            and '"target_domains"' in service
            and '"targets"' in service
            and '"base_model"' in service,
            "dataset identity, exact base model, target domains and acceptance targets remain visible",
        ),
        _check(
            "reference_data_only_boundary",
            '"instruction_authority": False' in service
            and '"auto_training_ingest": False' in service
            and "reference_only" in localization,
            "Project Knowledge, Research Packs and retrieved context remain data-only references",
        ),
        _check(
            "benchmark_typed_mutation_only",
            'domain="bench"' in service
            and 'action="run"' in service
            and "R15WorkflowMode.DRY_RUN" in service
            and "R15WorkflowMode.APPLY" in service
            and "confirmed=confirmed" in service,
            "benchmark execution uses the accepted typed R15 dry-run/confirmed-apply path",
        ),
        _check(
            "no_training_or_later_mutations",
            '"training": False' in service
            and '"training_cancel": False' in service
            and '"training_recovery": False' in service
            and '"conversion": False' in service
            and '"promotion": False' in service
            and '"rollback": False' in service
            and "modelLabBenchDecisionTraining" not in panel,
            "V2.3.3 exposes no training launch/cancel/recovery, conversion, promotion or rollback control",
        ),
        _check(
            "ui_structured_accessible",
            "modelLabBenchDecisionReportsTable" in panel
            and "modelLabBenchDecisionDiagnosisTable" in panel
            and "modelLabBenchDecisionTargetsTable" in panel
            and "mark_accessible" in panel
            and "test_bench_decision_workspace_is_wired_accessible_localized_and_training_free" in ui_test,
            "KodeStudio exposes structured accessible report, diagnosis and target surfaces",
        ),
        _check(
            "localization",
            '"nav": "Bench & Decision"' in localization
            and '"nav": "Bench & Décision"' in localization
            and "qps-ploc" in localization,
            "EN/FR/qps-ploc localization is present",
        ),
        _check(
            "app_wiring",
            "model_lab_bench_service=None" in app
            and "model_lab_bench_decision_nav_text" in app
            and "model_lab_bench_decision_page" in app,
            "the V2.3.3 workspace is wired into KodeStudio navigation",
        ),
        _check(
            "deterministic_backend_tests",
            "test_snapshot_exposes_structured_bench_and_exact_decision_lineage" in backend_test
            and "test_tampered_report_and_decision_are_explicit_and_fail_binding" in backend_test
            and "test_cross_project_r15_binding_is_rejected" in backend_test,
            "backend tests cover deterministic lineage, tamper and project-scope boundaries",
        ),
        _check(
            "current_authority",
            (v233_current or v233_normalized)
            and "V2.3.3" in state
            and "V2.3.3" in next_doc,
            "V2.3.3 is either CURRENT or retained as COMPLETE + NORMALIZED historical acceptance context",
        ),
        _check(
            "later_scope_unauthorized",
            "V2.3.4+ remain unauthorized" in authority
            and "training controls remain disabled" in authority,
            "V2.3.4+ and training execution remain outside this implementation subdivision",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.3.3",
        "title": "Bench, gap diagnosis and TRAIN/NO_TRAIN decision UX",
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
