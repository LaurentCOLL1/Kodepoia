from __future__ import annotations

from pathlib import Path

from kodepoia.release import CURRENT_RELEASE
from kodepoia.release.terminal_freeze import TERMINAL_RELEASE_FREEZE

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v262_full_v2_acceptance_chain_precedes_terminal_gate() -> None:
    workflow = _read(".github/workflows/python-core.yml")
    full_pytest = workflow.index("      - name: Test\n        run: pytest")
    expected = (
        "v2_0_acceptance.py",
        "v2_1_1_acceptance.py",
        "v2_1_2_acceptance.py",
        "v2_1_3_acceptance.py",
        "v2_1_4_acceptance.py",
        "v2_1_5_acceptance.py",
        "v2_1_6_acceptance.py",
        "v2_2_1_acceptance.py",
        "v2_2_2_acceptance.py",
        "v2_2_3_acceptance.py",
        "v2_2_4_acceptance.py",
        "v2_2_5_acceptance.py",
        "v2_2_6_acceptance.py",
        "v2_3_1_acceptance.py",
        "v2_3_2_acceptance.py",
        "v2_3_3_acceptance.py",
        "v2_3_4_acceptance.py",
        "v2_3_5_acceptance.py",
        "v2_3_6_acceptance.py",
        "v2_4_1_acceptance.py",
        "v2_4_2_acceptance.py",
        "v2_4_3_acceptance.py",
        "v2_4_4_acceptance.py",
        "v2_4_5_acceptance.py",
        "v2_4_6_acceptance.py",
        "v2_5_1_acceptance.py",
        "v2_5_2_acceptance.py",
        "v2_5_3_acceptance.py",
        "v2_5_4_acceptance.py",
        "v2_5_5_acceptance.py",
        "v2_5_6_acceptance.py",
        "v2_6_1_acceptance.py",
    )
    prefix = workflow[:full_pytest]
    for script in expected:
        assert f"python scripts/{script} --source-sha" in prefix

    focused = workflow.index("Run V2.6.2 terminal integrated hardening focused tests")
    acceptance = workflow.index("Run V2.6.2 terminal integrated hardening exact-head acceptance")
    upload = workflow.index("Upload V2.6.2 exact-head evidence")
    assert full_pytest < focused < acceptance < upload


def test_v262_critical_fail_closed_domains_remain_covered() -> None:
    required = {
        "tests/test_v2_1_6_researchguard_hardening.py": (
            "test_v216_mixed_public_private_dns_fails_closed",
            "test_v216_adversarial_source_cannot_authorize_workspace_escape",
        ),
        "tests/test_v2_2_6_project_knowledge_hardening.py": (
            "test_cross_project_retrieval_fails_before_embedding_provider_access",
            "test_secret_bearing_file_is_redacted_and_secret_memory_is_rejected",
        ),
        "tests/test_v2_3_6_model_lab_hardening.py": (
            "test_privacy_license_revocation_and_holdout_contamination_fail_closed",
            "test_quantization_packaging_and_registry_integrity_veto_unsafe_activation",
        ),
        "tests/test_v2_4_6_production_hardening.py": (
            "test_v246_live_evidence_fails_closed_for_provider_topology_lineage_and_integrity_drift",
            "test_v246_launcher_and_security_boundaries_have_no_text_driven_escape_surface",
        ),
        "tests/test_v2_5_6_cross_workspace_hardening.py": (
            "test_v256_missing_or_invalid_handoff_evidence_blocks_execution",
            "test_v256_cancellation_cannot_become_partial_success_and_blocks_downstream",
            "test_v256_secret_tainted_service_output_is_sanitized_before_evidence",
        ),
        "tests/test_r16_prompt_injection.py": (
            "test_external_content_cannot_self_promote_authority",
            "test_guardian_denies_untrusted_content_driven_privileged_action_before_confirmation",
        ),
        "tests/test_r16_secret_guard.py": (
            "test_raw_secret_is_denied_in_argv_and_ordinary_env",
            "test_artifact_scan_bounds_fail_closed",
        ),
        "tests/test_memory_r16_7.py": (
            "test_cross_project_scope_cannot_leak",
            "test_authority_spoofing_is_rejected_before_persistence",
        ),
        "tests/test_fault_recovery_r16_8.py": (
            "test_killswitch_stops_registered_hanging_process",
            "test_checkpoint_integrity_tamper_blocks_recovery",
        ),
    }
    for path, markers in required.items():
        source = _read(path)
        for marker in markers:
            assert marker in source, f"{path}: {marker}"


def test_v262_durability_packaged_windows_and_updater_invariants_remain_required() -> None:
    durability = _read("tests/test_r16_15_project_durability.py")
    soak = _read("tests/test_r16_16_resource_soak.py")
    packaged = _read("tests/test_r17_packaged_entrypoint.py")
    installer = _read(".github/workflows/windows-installer.yml")
    updater = _read("tests/test_r18_7_update_discovery.py")
    delivery = _read("tests/test_r18_8_verified_delivery.py")

    assert "test_r16_15_full_project_durability_report" in durability
    assert "test_full_bounded_resource_soak_acceptance" in soak
    assert "test_budget_evaluator_rejects_overrun" in soak
    assert "test_windows_installer_always_offers_destination_selection" in packaged
    assert "Silent custom-directory install, trusted updater smoke and uninstall" in installer
    assert "Installed trusted update resource missing" in installer
    assert "test_offline_is_non_blocking_and_distinct" in updater
    assert "test_expired_timestamp_has_specific_state" in updater
    assert "test_metadata_rollback_fails_closed" in updater
    assert "test_r18_8_wrong_hash_fails_before_executable_finalize" in delivery
    assert "test_r18_8_failed_stage_does_not_modify_project_data" in delivery


def test_v262_preserves_terminal_release_freeze_and_no_public_effects() -> None:
    freeze = TERMINAL_RELEASE_FREEZE
    assert CURRENT_RELEASE.public_version == "1.1.0-rc8"
    assert freeze.successor_identity.public_version == "1.1.0"
    assert freeze.successor["candidate_source_sha"] is None
    assert freeze.authenticode["production_signing_verified"] is False
    assert freeze.winget["decision"] == "out"
    assert freeze.production_tuf_repository_observation["repository_metadata_fresh"] is False
    assert freeze.production_tuf_repository_observation[
        "production_metadata_mutation_authorized"
    ] is False
    assert all(value is False for value in freeze.effects.values())


def test_v262_is_hardening_only_and_provider_independent() -> None:
    authority = _read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    next_doc = _read("docs/continuity/NEXT.md")
    contract = _read("docs/release/V2_6_2_INTEGRATED_HARDENING.md").casefold()

    assert "V2.6.2 — Full V2 integrated regression and adversarial hardening" in authority
    assert "Current next action — V2.6.2 only" in next_doc
    assert "no new product capability" in contract
    assert "no live provider" in contract
    assert not (ROOT / "src/kodepoia/release/v2_6_2.py").exists()
