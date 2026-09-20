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
        description="Kodepoia V2.3.2 governed experience and dataset curation acceptance"
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    observed = _run(["git", "rev-parse", "HEAD"])
    observed_sha = observed.stdout.strip().lower()
    root = Path(__file__).resolve().parents[1]

    service = (
        root / "src/kodepoia/kodestudio/model_lab_curation.py"
    ).read_text(encoding="utf-8")
    panel = (
        root / "src/kodepoia/kodestudio/model_lab_curation_panel.py"
    ).read_text(encoding="utf-8")
    localization = (
        root / "src/kodepoia/kodestudio/model_lab_curation_localization.py"
    ).read_text(encoding="utf-8")
    app = (root / "src/kodepoia/kodestudio/app.py").read_text(encoding="utf-8")
    backend_test = (root / "tests/test_v2_3_2_curation.py").read_text(encoding="utf-8")
    ui_test = (root / "tests/test_v2_3_2_curation_ui.py").read_text(encoding="utf-8")
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
            "tests/test_experience_governance.py",
            "tests/test_experience_dedup.py",
            "tests/test_experience_dataset.py",
            "tests/test_v2_3_2_curation.py",
        ]
    )
    targeted_detail = (
        "R15 governance/dedup/dataset plus V2.3.2 curation corpus passed"
        if targeted.returncode == 0
        else (targeted.stdout + targeted.stderr)[-5000:]
    )

    v232_current = (
        "V2.3.2 — Governed experience and dataset curation workspace — CURRENT"
        in authority
    )
    v232_normalized = (
        "V2.3.2 — Governed experience and dataset curation workspace — COMPLETE + NORMALIZED"
        in authority
    )

    checks = [
        _check(
            "exact_head",
            observed.returncode == 0 and observed_sha == source_sha,
            observed_sha,
        ),
        _check(
            "governance_dedup_dataset_corpus",
            targeted.returncode == 0,
            targeted_detail,
        ),
        _check(
            "structured_curation_workspace",
            "create_model_lab_curation_page" in app
            and "model_lab_curation_nav_text" in app
            and "modelLabCurationExperiencesTable" in panel
            and "modelLabCurationEvidenceTable" in panel
            and "modelLabCurationDatasetsTable" in panel,
            "KodeStudio exposes structured experience, dedup/contamination and dataset surfaces",
        ),
        _check(
            "metadata_only_no_raw_payload",
            '"raw_payloads_exposed": False' in service
            and '"payload_read": False' in service
            and '"payload_rows_read": False' in service
            and "RAW-TRAINING-MARKER-MUST-NOT-BE-READ" in backend_test,
            (
                "curation inventory exposes governed metadata/digests without reading "
                "raw experience payloads or dataset rows"
            ),
        ),
        _check(
            "project_knowledge_not_training_authority",
            '"project_knowledge_auto_ingest": False' in service
            and "PROJECT-KNOWLEDGE-MUST-NOT-BECOME-TRAINING-DATA" in backend_test
            and ".kodepoia/knowledge" not in service,
            (
                "Project Knowledge/Research/context is not scanned or auto-ingested "
                "by the curation facade"
            ),
        ),
        _check(
            "eligibility_provenance_privacy_license",
            "_AUTHORIZATION_FIELDS" in service
            and '"license_expression"' in service
            and '"project_scope"' in service
            and '"sanitization"' in service
            and '"benchmark_protected"' in service,
            (
                "source identity/scope, consent, provenance, license, privacy, "
                "sanitization and benchmark protection are visible"
            ),
        ),
        _check(
            "revocation_quarantine_fail_closed",
            "_TERMINAL_BLOCKED_STATES" in service
            and "state:revoked" in backend_test
            and "license:missing" in backend_test
            and '"tampered"' in service,
            (
                "revoked/quarantined/expired/rejected, missing license and integrity "
                "failure remain explicit blockers"
            ),
        ),
        _check(
            "dedup_contamination_outcomes",
            '"match_types"' in service
            and '"review_required"' in service
            and '"quarantined_item_ids"' in service
            and '"benchmark_contamination"' in service
            and "Match types / members" in panel,
            (
                "exact/near contamination and dedup membership are structured "
                "without raw source content"
            ),
        ),
        _check(
            "dataset_preview_summary",
            "dataset_preview_summary" in service
            and '"candidate_rows"' in service
            and '"excluded_by_reason"' in service
            and '"licenses"' in service
            and '"domains"' in service
            and '"tasks"' in service
            and '"split_summary"' in service
            and "modelLabCurationDatasetPreview" in panel,
            (
                "non-mutating preview exposes row/exclusion/license/domain/task and "
                "honest split-policy state"
            ),
        ),
        _check(
            "typed_r15_curation_only",
            'domain="experience"' in service
            and 'action="curate"' in service
            and 'domain="dataset"' in service
            and 'action="build"' in service
            and "R15WorkflowRequest" in service
            and "R15UXService" in service,
            "curation and dataset build delegate to accepted typed R15 UX handlers",
        ),
        _check(
            "dry_run_and_confirmation",
            "R15WorkflowMode.DRY_RUN" in service
            and "R15WorkflowMode.APPLY" in service
            and "confirmed=confirmed" in service
            and "test_curation_and_dataset_mutations_delegate_only_to_r15_typed_handlers"
            in backend_test,
            "preview is non-mutating and apply remains confirmation-gated by R15",
        ),
        _check(
            "project_scope_binding",
            "R15 UX service project root does not match curation project root" in service
            and "test_curation_rejects_cross_project_r15_service_binding" in backend_test,
            "the curation facade cannot bind a mutation service from another project root",
        ),
        _check(
            "immutable_dataset_integrity",
            "_DATASET_SCHEMA" in service
            and "observed_dataset_digest" in service
            and "dataset_id == f\"ds_{expected}\"" in service
            and "test_dataset_manifest_tamper_is_explicit_without_reading_jsonl"
            in backend_test,
            "dataset identity/digest tamper is explicit while JSONL payload rows remain unread",
        ),
        _check(
            "no_later_mutation_surface",
            '"training": False' in service
            and '"conversion": False' in service
            and '"promotion": False' in service
            and '"rollback": False' in service
            and "modelLabCurationTraining" not in panel
            and "modelLabCurationPromote" not in panel
            and "modelLabCurationRollback" not in panel,
            "V2.3.2 exposes no training, conversion/package, promotion or rollback control",
        ),
        _check(
            "localization_accessibility_compatibility",
            '"nav": "Data Curation"' in localization
            and '"nav": "Curation des données"' in localization
            and "mark_accessible" in panel
            and (
                "assert len(texts) == 16" in pseudo_test
                or "assert len(texts) == 17" in pseudo_test
                or "assert len(texts) == 18" in pseudo_test
                or "assert len(texts) == 19" in pseudo_test
            )
            and 'window.findChild(QPushButton, "modelLabCurationRefresh")' in pseudo_test
            and "test_curation_workspace_is_wired_structured_accessible_and_localized"
            in ui_test,
            "FR/EN/qps-ploc and central accessibility contracts include the new workspace",
        ),
        _check(
            "authority_scope",
            (v232_current or v232_normalized)
            and "Project Knowledge/context may be linked for explanation but never auto-ingested."
            in authority
            and "V2.3.3+ remain unauthorized" in authority,
            "acceptance remains bounded to V2.3.2 while later V2.3 work stays unauthorized",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload = {
        "schema_version": 1,
        "subdivision": "V2.3.2",
        "title": "Governed experience and dataset curation workspace",
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
