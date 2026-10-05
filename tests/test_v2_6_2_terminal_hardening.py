from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from kodepoia.release import CURRENT_RELEASE
from kodepoia.release.terminal_freeze import (
    TERMINAL_RELEASE_FREEZE,
    TerminalReleaseFreeze,
    TerminalReleaseFreezeError,
)
from kodepoia.release.terminal_hardening import (
    REQUIRED_CRITICAL_DOMAINS,
    TerminalHardeningCheck,
    TerminalHardeningDecision,
    TerminalHardeningError,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "a" * 40


def _passing_checks() -> list[TerminalHardeningCheck]:
    return [
        TerminalHardeningCheck(
            name=f"{domain}-proof",
            domain=domain,
            passed=True,
            detail=f"{domain} proof",
        )
        for domain in REQUIRED_CRITICAL_DOMAINS
    ]


def test_terminal_hardening_critical_veto_is_fail_closed() -> None:
    checks = _passing_checks()
    checks[3] = TerminalHardeningCheck(
        name="model-lab-proof",
        domain="model-lab",
        passed=False,
        detail="critical Model Lab regression",
    )

    decision = TerminalHardeningDecision.from_checks(SOURCE, checks)

    assert decision.status == "FAIL"
    assert decision.passed is False
    assert decision.to_dict()["critical_veto"] is True
    assert [check.name for check in decision.critical_vetoes] == ["model-lab-proof"]
    assert decision.domain_summary()["model-lab"]["status"] == "FAIL"


def test_terminal_hardening_requires_every_critical_domain() -> None:
    checks = _passing_checks()
    checks = [check for check in checks if check.domain != "updater"]

    with pytest.raises(TerminalHardeningError, match="missing terminal hardening domains"):
        TerminalHardeningDecision.from_checks(SOURCE, checks)

    checks = _passing_checks()
    index = next(i for i, check in enumerate(checks) if check.domain == "updater")
    checks[index] = TerminalHardeningCheck(
        name="updater-proof",
        domain="updater",
        passed=True,
        critical=False,
        detail="non-critical updater observation",
    )
    with pytest.raises(TerminalHardeningError, match="requires a critical check"):
        TerminalHardeningDecision.from_checks(SOURCE, checks)


def test_terminal_hardening_digest_is_order_independent_and_source_bound() -> None:
    checks = _passing_checks()
    forward = TerminalHardeningDecision.from_checks(SOURCE, checks).to_dict()
    reverse = TerminalHardeningDecision.from_checks(SOURCE, list(reversed(checks))).to_dict()

    assert forward == reverse

    other = TerminalHardeningDecision.from_checks("b" * 40, checks).to_dict()
    assert forward["evidence_sha256"] != other["evidence_sha256"]


def test_v262_preserves_terminal_release_freeze_and_no_public_effects() -> None:
    freeze = TERMINAL_RELEASE_FREEZE
    target = freeze.successor_identity

    assert TERMINAL_RELEASE_FREEZE.public_baseline["public_version"] == "1.1.0-rc8"
    assert target == CURRENT_RELEASE
    assert target.public_version == "1.1.0"
    assert target.channel == "stable"
    assert freeze.successor["candidate_source_freeze_phase"] == "V2.6.3"
    assert freeze.successor["candidate_source_sha"] is None
    assert freeze.authenticode["production_signing_verified"] is False
    assert freeze.winget["decision"] == "out"
    assert freeze.production_tuf_repository_observation["repository_metadata_fresh"] is False
    assert (
        freeze.production_tuf_repository_observation["expired_metadata_accepted_by_updater"]
        is False
    )
    assert freeze.production_tuf_repository_observation["resolution_phase"] == "V2.6.4"
    assert all(value is False for value in freeze.effects.values())

    targets = (
        ROOT / "docs/release/evidence/V2_6_4_PRETRANSITION_METADATA/targets.json"
    ).read_text(encoding="utf-8")
    assert "channels/stable/windows-x86_64/1.1.0/" not in targets


def test_v262_full_v2_acceptance_chain_is_wired_before_terminal_evidence() -> None:
    workflow = (ROOT / ".github/workflows/python-core.yml").read_text(encoding="utf-8")
    expected = ["v2_0_acceptance.py"]
    for phase in range(1, 6):
        expected.extend(f"v2_{phase}_{subdivision}_acceptance.py" for subdivision in range(1, 7))
    expected.append("v2_6_1_acceptance.py")

    for script in expected:
        assert f"python scripts/{script}" in workflow, script

    full_pytest = "      - name: Test\n        run: pytest"
    terminal_acceptance = (
        "      - name: Run V2.6.2 terminal integrated hardening exact-head acceptance"
    )
    assert full_pytest in workflow
    assert terminal_acceptance in workflow
    assert workflow.index(full_pytest) < workflow.index(terminal_acceptance)
    assert (
        "v2-6-2-terminal-hardening-${{ matrix.os }}-${{ env.KODEPOIA_SOURCE_SHA }}"
        in workflow
    )


def test_v262_critical_adversarial_regression_suites_remain_present() -> None:
    required_markers = {
        "tests/test_r16_secret_guard.py": (
            "test_raw_secret_is_denied_in_argv_and_ordinary_env",
            "test_artifact_scan_bounds_fail_closed",
        ),
        "tests/test_r16_prompt_injection.py": (
            "test_external_content_cannot_self_promote_authority",
            "test_guardian_denies_untrusted_content_driven_privileged_action_before_confirmation",
        ),
        "tests/test_r16_workspace_quarantine.py": (
            "test_external_symlink_escape_is_blocked_when_supported",
            "test_critical_workspace_cannot_be_approved",
        ),
        "tests/test_memory_r16_7.py": (
            "test_cross_project_scope_cannot_leak",
            "test_authority_spoofing_is_rejected_before_persistence",
        ),
        "tests/test_v2_1_6_researchguard_hardening.py": (
            "test_v216_private_local_and_metadata_targets_fail_closed",
            "test_v216_adversarial_source_cannot_authorize_workspace_escape",
        ),
        "tests/test_v2_2_6_project_knowledge_hardening.py": (
            "test_cross_project_retrieval_fails_before_embedding_provider_access",
            "test_prompt_injection_from_pack_file_and_memory_stays_untrusted_data",
        ),
        "tests/test_v2_3_6_model_lab_hardening.py": (
            "test_privacy_license_revocation_and_holdout_contamination_fail_closed",
            "test_paired_evaluation_mismatch_and_critical_regression_veto_aggregate_gain",
        ),
        "tests/test_v2_4_6_production_hardening.py": (
            "test_v246_live_evidence_fails_closed_for_provider_topology_lineage_and_integrity_drift",
            "test_v246_launcher_and_security_boundaries_have_no_text_driven_escape_surface",
        ),
        "tests/test_v2_5_6_cross_workspace_hardening.py": (
            "test_v256_unauthorized_destination_write_and_wrong_approval_fail_closed",
            "test_v256_cancellation_cannot_become_partial_success_and_blocks_downstream",
        ),
        "tests/test_fault_recovery_r16_8.py": (
            "test_checkpoint_integrity_tamper_blocks_recovery",
            "test_killswitch_during_multistep_mutation_requires_recovery",
        ),
        "tests/test_r16_16_resource_soak.py": (
            "test_budget_evaluator_rejects_overrun",
            "test_full_bounded_resource_soak_acceptance",
        ),
        "tests/test_r18_6_tuf_security.py": (
            "test_expired_timestamp_freeze_is_refused_with_fixed_clock",
            "test_timestamp_rollback_is_refused_and_state_is_not_replaced",
        ),
        "tests/test_r18_7_update_discovery.py": (
            "test_offline_is_non_blocking_and_distinct",
            "test_expired_timestamp_has_specific_state",
            "test_metadata_rollback_fails_closed",
        ),
    }

    for relative, markers in required_markers.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in source, f"{relative}: {marker}"


def test_v262_packaged_windows_ui_and_project_durability_remain_mandatory() -> None:
    python_core = (ROOT / ".github/workflows/python-core.yml").read_text(encoding="utf-8")
    ui_smoke = (ROOT / ".github/workflows/ui-smoke.yml").read_text(encoding="utf-8")
    installer = (ROOT / ".github/workflows/windows-installer.yml").read_text(encoding="utf-8")
    durability = (ROOT / "tests/test_r16_15_project_durability.py").read_text(encoding="utf-8")

    assert "kodestudio-ui-windows" in python_core
    assert "package-build-${{ matrix.os }}" in python_core
    assert "test_v2_4_6_production_hardening_ui.py" in ui_smoke
    assert "test_v2_5_6_cross_workspace_hardening_ui.py" in ui_smoke
    assert "Silent custom-directory install, trusted updater smoke and uninstall" in installer
    assert '"/DIR=$installDir"' in installer
    assert "--smoke-test" in installer
    assert "Uninstaller failed" in installer
    assert "test_r16_15_full_project_durability_report" in durability


def test_v262_release_freeze_validation_still_rejects_promotion_drift() -> None:
    payload = copy.deepcopy(dict(TERMINAL_RELEASE_FREEZE.payload))
    payload["successor"] = dict(payload["successor"])
    payload["successor"]["candidate_source_sha"] = "c" * 40

    with pytest.raises(TerminalReleaseFreezeError, match="candidate source SHA cannot be preclaimed"):
        TerminalReleaseFreeze.from_mapping(payload)

    serialized = json.dumps(TERMINAL_RELEASE_FREEZE.payload, sort_keys=True)
    assert "candidate_source_sha" in serialized
    assert TERMINAL_RELEASE_FREEZE.authenticode[
        "production_signing_secret_provisioning_authorized"
    ] is False
