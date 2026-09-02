from __future__ import annotations

from pathlib import Path

from kodepoia.kodegodot.beta_3d_acceptance import (
    MAX_FIXTURE_BYTES,
    MAX_FIXTURE_FILES,
    MAX_SINGLE_FILE_BYTES,
    build_3d_report,
)

ROOT = Path(__file__).resolve().parents[1]


def test_r16_11_static_3d_acceptance_passes_without_inventing_live_godot() -> None:
    report = build_3d_report(
        ROOT,
        source_sha="1" * 40,
        platform="pytest",
        godot_executable="",
    )

    assert report["security_claim"] is True
    assert report["critical_veto"] is False
    assert report["manual_state"] == "NONE"
    assert report["live_godot"]["available"] is False
    assert report["live_godot"]["status"] == "capability_absent"
    assert report["summary"]["failed"] == 0
    assert report["summary"]["total"] == 15

    names = {item["name"] for item in report["cases"]}
    assert {
        "resource-budget",
        "representative-3d-project",
        "3d-dependencies",
        "public-kodegodot-3d-analysis",
        "vault-lineage-aware-reference",
        "workspace-bounded-asset-reference",
        "external-reference-negative-control",
        "untrusted-3d-metadata-boundary",
        "bounded-cancellation-rollback",
        "multi-file-governed-3d-edit",
        "failed-edit-precondition",
        "integrity-bound-recovery-checkpoint",
        "safechange-3d-rollback",
        "audit-chain",
        "godot-3d-capability-probe",
    } == names

    budget = report["resource_budget"]
    assert budget["files"] <= MAX_FIXTURE_FILES
    assert budget["total_bytes"] <= MAX_FIXTURE_BYTES
    assert budget["max_file_bytes"] <= MAX_SINGLE_FILE_BYTES
    assert report["pre_change_project_sha256"] == report["cancel_restored_project_sha256"]
    assert report["pre_change_project_sha256"] == report["restored_project_sha256"]
    assert report["pre_change_project_sha256"] != report["changed_project_sha256"]
    assert report["asset_revision_id"].startswith("rev_")
    assert len(report["asset_content_sha256"]) == 64
    assert len(report["fixture_sha256"]) == 64
    assert len(report["diff_sha256"]) == 64
    assert len(report["diagnostic_sha256"]) == 64
    assert len(report["recovery_sha256"]) == 64
    assert len(report["semantic_sha256"]) == 64
    assert len(report["recovery_checkpoint_integrity_sha256"]) == 64
    assert len(report["evidence_sha256"]) == 64


def test_r16_11_semantic_and_fixture_evidence_is_deterministic() -> None:
    first = build_3d_report(
        ROOT,
        source_sha="2" * 40,
        platform="pytest",
        godot_executable="",
    )
    second = build_3d_report(
        ROOT,
        source_sha="2" * 40,
        platform="pytest",
        godot_executable="",
    )

    assert first["fixture_sha256"] == second["fixture_sha256"]
    assert first["asset_revision_id"] == second["asset_revision_id"]
    assert first["asset_content_sha256"] == second["asset_content_sha256"]
    assert first["diff_sha256"] == second["diff_sha256"]
    assert first["diagnostic_sha256"] == second["diagnostic_sha256"]
    assert first["recovery_sha256"] == second["recovery_sha256"]
    assert first["semantic_sha256"] == second["semantic_sha256"]
