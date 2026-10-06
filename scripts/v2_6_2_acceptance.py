from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from kodepoia.release import CURRENT_RELEASE
from kodepoia.release.terminal_freeze import TERMINAL_RELEASE_FREEZE
from kodepoia.release.terminal_hardening import (
    TerminalHardeningCheck,
    TerminalHardeningDecision,
)


def _contains_all(source: str, markers: tuple[str, ...]) -> bool:
    return all(marker in source for marker in markers)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    source_sha = args.source_sha.strip().lower()
    observed_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip().lower()

    def read(path: str) -> str:
        return (root / path).read_text(encoding="utf-8")

    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    roadmap = read("docs/roadmap/KODEPOIA_ROADMAP_V2.md")
    v26 = read("docs/roadmap/V2_6_HARDENING_NEXT_PUBLIC_WINDOWS_RELEASE.md")
    hardening_doc = read("docs/release/V2_6_2_TERMINAL_HARDENING.md")
    python_core = read(".github/workflows/python-core.yml")
    ui_smoke = read(".github/workflows/ui-smoke.yml")
    windows_installer = read(".github/workflows/windows-installer.yml")

    security = {
        "secret": read("tests/test_r16_secret_guard.py"),
        "prompt": read("tests/test_r16_prompt_injection.py"),
        "quarantine": read("tests/test_r16_workspace_quarantine.py"),
    }
    knowledge = {
        "research": read("tests/test_v2_1_6_researchguard_hardening.py"),
        "knowledge": read("tests/test_v2_2_6_project_knowledge_hardening.py"),
        "memory": read("tests/test_memory_r16_7.py"),
    }
    model_lab = {
        "governance": read("tests/test_v2_3_6_model_lab_hardening.py"),
        "production": read("tests/test_v2_4_6_production_hardening.py"),
    }
    orchestration = read("tests/test_v2_5_6_cross_workspace_hardening.py")
    resilience = {
        "recovery": read("tests/test_fault_recovery_r16_8.py"),
        "durability": read("tests/test_r16_15_project_durability.py"),
        "soak": read("tests/test_r16_16_resource_soak.py"),
    }
    updater = {
        "tuf": read("tests/test_r18_6_tuf_security.py"),
        "discovery": read("tests/test_r18_7_update_discovery.py"),
    }
    targets = read("docs/release/evidence/V2_6_4_PRETRANSITION_METADATA/targets.json")

    expected_acceptance_scripts = ["v2_0_acceptance.py"]
    for phase in range(1, 6):
        expected_acceptance_scripts.extend(
            f"v2_{phase}_{subdivision}_acceptance.py" for subdivision in range(1, 7)
        )
    expected_acceptance_scripts.append("v2_6_1_acceptance.py")

    full_pytest = "      - name: Test\n        run: pytest"
    terminal_acceptance = (
        "      - name: Run V2.6.2 terminal integrated hardening exact-head acceptance"
    )
    full_suite_before_evidence = (
        full_pytest in python_core
        and terminal_acceptance in python_core
        and python_core.index(full_pytest) < python_core.index(terminal_acceptance)
    )

    freeze = TERMINAL_RELEASE_FREEZE
    checks = [
        TerminalHardeningCheck(
            name="exact-head",
            domain="ci-evidence",
            passed=source_sha == observed_sha,
            detail="V2.6.2 evidence executes the exact requested Git head",
        ),
        TerminalHardeningCheck(
            name="current-authority",
            domain="release-freeze",
            passed=(
                (
                    "V2.6.2 — Full V2 integrated regression and adversarial hardening "
                    "is now the only authorized implementation subdivision"
                )
                in state
                and "Current next action — V2.6.2 only" in next_doc
                and "The only authorized implementation subdivision is **V2.6.2" in authority
                and "V2.6.2 CURRENT" in roadmap
                and (
                    "V2.6.2 — Full V2 integrated regression and adversarial hardening "
                    "is the only authorized implementation subdivision"
                )
                in v26
            ),
            detail="V2.6.1 is normalized and V2.6.2 alone is authorized",
        ),
        TerminalHardeningCheck(
            name="full-v2-regression-chain",
            domain="v2-regression",
            passed=all(
                f"python scripts/{script}" in python_core
                for script in expected_acceptance_scripts
            )
            and full_suite_before_evidence,
            detail=(
                "all accepted V2.0-V2.6.1 exact-head acceptances and complete pytest "
                "precede V2.6.2 evidence"
            ),
        ),
        TerminalHardeningCheck(
            name="security-privacy-adversarial",
            domain="security-privacy",
            passed=(
                _contains_all(
                    security["secret"],
                    (
                        "test_raw_secret_is_denied_in_argv_and_ordinary_env",
                        "test_artifact_scan_bounds_fail_closed",
                    ),
                )
                and _contains_all(
                    security["prompt"],
                    (
                        "test_external_content_cannot_self_promote_authority",
                        "test_guardian_denies_untrusted_content_driven_privileged_action_before_confirmation",
                    ),
                )
                and _contains_all(
                    security["quarantine"],
                    (
                        "test_external_symlink_escape_is_blocked_when_supported",
                        "test_critical_workspace_cannot_be_approved",
                    ),
                )
            ),
            detail="secret, prompt-injection and workspace-quarantine boundaries remain covered",
        ),
        TerminalHardeningCheck(
            name="workspace-memory-research-adversarial",
            domain="workspace-memory-research",
            passed=(
                _contains_all(
                    knowledge["research"],
                    (
                        "test_v216_private_local_and_metadata_targets_fail_closed",
                        "test_v216_adversarial_source_cannot_authorize_workspace_escape",
                    ),
                )
                and _contains_all(
                    knowledge["knowledge"],
                    (
                        "test_cross_project_retrieval_fails_before_embedding_provider_access",
                        "test_prompt_injection_from_pack_file_and_memory_stays_untrusted_data",
                    ),
                )
                and _contains_all(
                    knowledge["memory"],
                    (
                        "test_cross_project_scope_cannot_leak",
                        "test_authority_spoofing_is_rejected_before_persistence",
                    ),
                )
            ),
            detail="Research, Project Knowledge and Memory remain project-scoped, data-only and fail-closed",
        ),
        TerminalHardeningCheck(
            name="model-lab-adversarial",
            domain="model-lab",
            passed=(
                _contains_all(
                    model_lab["governance"],
                    (
                        "test_privacy_license_revocation_and_holdout_contamination_fail_closed",
                        "test_paired_evaluation_mismatch_and_critical_regression_veto_aggregate_gain",
                    ),
                )
                and _contains_all(
                    model_lab["production"],
                    (
                        (
                            "test_v246_live_evidence_fails_closed_for_provider_topology_"
                            "lineage_and_integrity_drift"
                        ),
                        "test_v246_launcher_and_security_boundaries_have_no_text_driven_escape_surface",
                    ),
                )
            ),
            detail="Model Lab governance, live-proof honesty and distributed lineage remain fail-closed",
        ),
        TerminalHardeningCheck(
            name="orchestration-adversarial",
            domain="orchestration",
            passed=_contains_all(
                orchestration,
                (
                    "test_v256_stale_revoked_and_tampered_handoffs_fail_closed",
                    "test_v256_unauthorized_destination_write_and_wrong_approval_fail_closed",
                    "test_v256_cancellation_cannot_become_partial_success_and_blocks_downstream",
                    "test_v256_incompatible_recovery_and_deleted_project_fail_closed",
                    "test_v256_secret_tainted_service_output_is_sanitized_before_evidence",
                ),
            ),
            detail=(
                "cross-workspace handoff, approval, cancellation, recovery and evidence "
                "boundaries remain enforced"
            ),
        ),
        TerminalHardeningCheck(
            name="packaged-windows-durability",
            domain="packaged-windows",
            passed=(
                "kodestudio-ui-windows" in python_core
                and "package-build-${{ matrix.os }}" in python_core
                and "test_v2_4_6_production_hardening_ui.py" in ui_smoke
                and "test_v2_5_6_cross_workspace_hardening_ui.py" in ui_smoke
                and "Silent custom-directory install, trusted updater smoke and uninstall"
                in windows_installer
                and '"/DIR=$installDir"' in windows_installer
                and "--smoke-test" in windows_installer
                and "test_r16_15_full_project_durability_report" in resilience["durability"]
            ),
            detail=(
                "Windows package/UI/custom-directory/uninstall and project durability "
                "coverage remains mandatory"
            ),
        ),
        TerminalHardeningCheck(
            name="cancellation-recovery-resource-soak",
            domain="resilience",
            passed=(
                _contains_all(
                    resilience["recovery"],
                    (
                        "test_checkpoint_integrity_tamper_blocks_recovery",
                        "test_killswitch_during_multistep_mutation_requires_recovery",
                    ),
                )
                and _contains_all(
                    resilience["soak"],
                    (
                        "test_budget_evaluator_rejects_overrun",
                        "test_full_bounded_resource_soak_acceptance",
                    ),
                )
            ),
            detail="KillSwitch, recovery integrity and bounded resource-soak regressions remain mandatory",
        ),
        TerminalHardeningCheck(
            name="updater-local-availability-fail-closed",
            domain="updater",
            passed=(
                _contains_all(
                    updater["tuf"],
                    (
                        "test_expired_timestamp_freeze_is_refused_with_fixed_clock",
                        "test_timestamp_rollback_is_refused_and_state_is_not_replaced",
                    ),
                )
                and _contains_all(
                    updater["discovery"],
                    (
                        "test_offline_is_non_blocking_and_distinct",
                        "test_expired_timestamp_has_specific_state",
                        "test_metadata_rollback_fails_closed",
                    ),
                )
                and freeze.production_tuf_repository_observation[
                    "expired_metadata_accepted_by_updater"
                ]
                is False
            ),
            detail=(
                "offline state stays explicit while expiry, rollback and tampering remain "
                "verification failures"
            ),
        ),
        TerminalHardeningCheck(
            name="terminal-release-freeze-unchanged",
            domain="release-freeze",
            passed=(
                freeze.public_baseline["public_version"] == "1.1.0-rc8"
                and freeze.successor_identity.public_version == "1.1.0"
                and CURRENT_RELEASE.public_version == "1.1.1"
                and CURRENT_RELEASE.is_newer_than(freeze.successor_identity)
                and freeze.successor["candidate_source_sha"] is None
                and freeze.authenticode["production_signing_verified"] is False
                and freeze.winget["decision"] == "out"
                and freeze.production_tuf_repository_observation["repository_metadata_fresh"]
                is False
                and freeze.production_tuf_repository_observation["resolution_phase"] == "V2.6.4"
                and all(value is False for value in freeze.effects.values())
                and "channels/stable/windows-x86_64/1.1.0/" not in targets
            ),
            detail="V2.6.1 identity/signing/WinGet/TUF truth remains frozen with no public effects",
        ),
        TerminalHardeningCheck(
            name="deterministic-exact-head-evidence",
            domain="ci-evidence",
            passed=(
                full_suite_before_evidence
                and "v2-6-2-terminal-hardening-${{ matrix.os }}-${{ env.KODEPOIA_SOURCE_SHA }}"
                in python_core
                and "retention-days: 30" in python_core
                and "provider-independent" in hardening_doc
                and "No public release effect is authorized by V2.6.2." in hardening_doc
            ),
            detail=(
                "Ubuntu/Windows evidence is exact-head, post-pytest, deterministic and "
                "provider-independent"
            ),
        ),
    ]

    decision = TerminalHardeningDecision.from_checks(source_sha, checks)
    payload = decision.to_dict()
    payload.update(
        {
            "observed_sha": observed_sha,
            "full_pytest_precedes_evidence": full_suite_before_evidence,
            "public_release_triggered": False,
            "public_tag_triggered": False,
            "production_tuf_mutation_triggered": False,
            "live_updater_activation_triggered": False,
            "winget_submission_triggered": False,
            "signing_secret_provisioned": False,
        }
    )
    payload.pop("evidence_sha256", None)
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
    return 0 if decision.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
