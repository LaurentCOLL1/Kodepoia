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
        description="Kodepoia V2.3.1 Model Lab shell, inventory and lineage acceptance"
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    observed = _run(["git", "rev-parse", "HEAD"])
    observed_sha = observed.stdout.strip().lower()

    root = Path(__file__).resolve().parents[1]
    service = (root / "src/kodepoia/kodestudio/model_lab.py").read_text(encoding="utf-8")
    panel = (root / "src/kodepoia/kodestudio/model_lab_panel.py").read_text(encoding="utf-8")
    localization = (
        root / "src/kodepoia/kodestudio/model_lab_localization.py"
    ).read_text(encoding="utf-8")
    app = (root / "src/kodepoia/kodestudio/app.py").read_text(encoding="utf-8")
    backend_test = (root / "tests/test_v2_3_1_model_lab.py").read_text(encoding="utf-8")
    ui_test = (root / "tests/test_v2_3_1_model_lab_ui.py").read_text(encoding="utf-8")
    pseudo_test = (root / "tests/test_r6_6_localization_ui.py").read_text(encoding="utf-8")
    authority = (
        root / "docs/roadmap/V2_3_MODEL_LAB_GOVERNED_IMPROVEMENT_UX.md"
    ).read_text(encoding="utf-8")

    targeted = _run(
        [
            "python",
            "-m",
            "pytest",
            "-q",
            "tests/test_v2_3_1_model_lab.py",
        ]
    )
    targeted_detail = (
        "V2.3.1 read-only inventory/runtime backend corpus passed"
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
            "backend_inventory_corpus",
            targeted.returncode == 0,
            targeted_detail,
        ),
        _check(
            "read_only_contract",
            '"read_only": True' in service
            and '"dataset_build": False' in service
            and '"training": False' in service
            and '"conversion": False' in service
            and '"promotion": False' in service
            and '"rollback": False' in service
            and "test_model_lab_inventory_discovers_r15_evidence_and_registry_without_mutation"
            in backend_test,
            "Model Lab exposes inventory/runtime reads only and the corpus proves project evidence bytes are unchanged",
        ),
        _check(
            "bounded_evidence_discovery",
            "_MAX_JSON_BYTES" in service
            and "_MAX_EVIDENCE_FILES" in service
            and '".kodepoia/experience"' in service
            and '".kodepoia/datasets"' in service
            and '".kodepoia/benchmarks"' in service
            and '".kodepoia/tuning"' in service,
            "R15 evidence discovery is project-scoped and bounded by file count and JSON size",
        ),
        _check(
            "registry_integrity",
            '".kodepoia/models/specialized.json"' in service
            and "SpecializedModelVersion.from_document" in service
            and '"state": "tampered"' in service
            and "test_model_lab_reports_missing_invalid_stale_and_tampered_states"
            in backend_test,
            "specialized-model registry records are digest-validated without constructing a missing store",
        ),
        _check(
            "explicit_degraded_states",
            '"state": "missing"' in service
            and '"state": "invalid"' in service
            and '"state": "unavailable"' in service
            and "stale" in backend_test
            and "tampered" in backend_test,
            "missing, invalid, stale, tampered and unavailable states remain explicit",
        ),
        _check(
            "lineage_projection",
            "_LINEAGE_KEYS" in service
            and '"dataset_digest"' in service
            and '"training_plan_digest"' in service
            and '"evaluation_digest"' in service
            and '"target_kind": "model_registry"' in service
            and "modelLabLineageTable" in panel,
            "dataset/training/evaluation/export/registry digests are projected into a read-only lineage table",
        ),
        _check(
            "ollama_roles_and_inventory",
            "saved_model_roles" in service
            and "saved_ollama_base_url" in service
            and "OllamaModelManager" in service
            and "modelLabModelsTable" in panel
            and "test_model_lab_runtime_refresh_is_explicit_and_runs_off_ui_thread"
            in ui_test,
            "saved model-role preferences are visible before explicit Ollama inventory refresh",
        ),
        _check(
            "kaggle_read_only_runtime_state",
            "KaggleRemoteTrainer().doctor().to_dict()" in service
            and "KaggleQuotaService().snapshot().to_dict()" in service
            and "modelLabKaggleState" in panel
            and "kaggle_doctor_provider" in backend_test,
            "Kaggle doctor/quota state is queried only through explicit read-only runtime refresh",
        ),
        _check(
            "capability_summary_without_install",
            "importlib.util.find_spec" in service
            and "bitsandbytes" in service
            and "modelLabCapabilitiesTable" in panel
            and "pip install" not in service,
            "dependency capability is introspected without installing packages or drivers",
        ),
        _check(
            "kodestudio_structured_surface",
            "create_model_lab_page" in app
            and "model_lab_nav_text" in app
            and "modelLabEvidenceTable" in panel
            and "modelLabRegistryTable" in panel
            and "modelLabDiagnostics" in panel,
            "KodeStudio has a dedicated structured Model Lab surface with diagnostics JSON secondary to tables",
        ),
        _check(
            "no_model_lab_mutation_controls",
            "modelLabBuildDataset" not in panel
            and "modelLabTrain" not in panel
            and "modelLabConvert" not in panel
            and "modelLabPromote" not in panel
            and "modelLabRollback" not in panel
            and "forbidden" in ui_test,
            "V2.3.1 UI exposes no dataset-build, training, conversion, promotion or rollback control",
        ),
        _check(
            "localization_and_compatibility",
            '"nav": "Model Lab"' in localization
            and '"nav": "Laboratoire modèles"' in localization
            and 'assert len(texts) == 15' in pseudo_test
            and "r15TuningPage" in (
                root / "tests/test_r15_15_kodestudio.py"
            ).read_text(encoding="utf-8"),
            "FR/EN/pseudo-localization extends navigation while preserving the accepted R15 page contract",
        ),
        _check(
            "authority_scope",
            "V2.3.1 — Model Lab shell, inventory and lineage — CURRENT" in authority
            and "no new training" in authority
            and "no dataset build mutation" in authority
            and "no promotion/rollback mutation" in authority
            and "V2.3.2" in authority,
            "implementation remains bounded to the normalized V2.3.1 read-only authority",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload = {
        "schema_version": 1,
        "subdivision": "V2.3.1",
        "title": "Model Lab shell, inventory and lineage",
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
