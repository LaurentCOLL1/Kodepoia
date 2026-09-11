from __future__ import annotations

from pathlib import Path

import pytest

from kodepoia.update.continuous_operations import (
    R20_6_FORMAT,
    R20_6_SCHEMA_VERSION,
    build_continuous_operations_report,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "c" * 40
EXPECTED_CASES = {
    "persisted_client_state_after_long_offline",
    "fresh_metadata_after_return",
    "installation_age_not_trust_input",
    "expired_server_metadata_rejected",
    "old_timestamp_replay_rejected",
    "snapshot_targets_mix_and_match_rejected",
    "signing_or_actions_outage_is_non_blocking",
    "scheduled_refresh_recovers_after_transient_outage",
    "concurrent_refresh_cannot_regress_versions",
    "compromised_timestamp_cannot_authorize_targets",
    "compromised_snapshot_cannot_authorize_target_bytes",
    "offline_root_targets_absent_from_actions",
    "single_online_role_rotation_preserves_target_authorization",
    "emergency_manual_refresh_runbook_tested",
    "localized_non_destructive_update_ux",
    "installed_settings_and_projects_survive",
    "mandatory_path_remains_zero_cost",
}


def test_r20_6_integrated_matrix_passes_without_privileged_live_effects() -> None:
    report = build_continuous_operations_report(ROOT, source_sha=SOURCE_SHA)
    assert report["format"] == R20_6_FORMAT
    assert report["schema_version"] == R20_6_SCHEMA_VERSION
    assert report["source_sha"] == SOURCE_SHA
    assert report["status"] == "PASS"
    assert report["cases_total"] == len(EXPECTED_CASES)
    assert report["cases_passed"] == len(EXPECTED_CASES)
    assert report["failed_cases"] == []
    assert set(report["matrix"]) == EXPECTED_CASES
    assert all(report["matrix"].values())
    assert report["manual_intervention_required"] is False
    assert report["privileged_live_drill_required"] is False
    assert report["production_effect"] is False


def test_r20_6_report_is_explicitly_synthetic_and_non_production() -> None:
    report = build_continuous_operations_report(ROOT, source_sha=SOURCE_SHA)
    details = report["details"]
    assert details["production_keys_used"] is False
    assert details["production_metadata_modified"] is False
    assert details["public_release_created"] is False
    assert details["live_rotation_performed"] is False
    assert details["paid_provider_required"] is False
    assert details["old_timestamp_version"] == 1
    assert details["fresh_timestamp_version"] == 2
    assert details["refresh_recovery_snapshot_version"] == 5
    assert details["refresh_recovery_timestamp_version"] == 5


def test_r20_6_source_sha_is_strict() -> None:
    with pytest.raises(ValueError, match="40-character Git SHA"):
        build_continuous_operations_report(ROOT, source_sha="main")
