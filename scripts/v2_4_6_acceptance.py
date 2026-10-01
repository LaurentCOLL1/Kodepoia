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
    observed_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()

    def read(path: str) -> str:
        return (root / path).read_text(encoding="utf-8")

    hardening = read("tests/test_v2_4_6_production_hardening.py")
    ui = read("tests/test_v2_4_6_production_hardening_ui.py")
    topology = read("src/kodepoia/tuning/topology.py")
    strategy = read("src/kodepoia/tuning/strategy.py")
    distributed = read("src/kodepoia/tuning/distributed.py")
    recovery = read("src/kodepoia/tuning/distributed_recovery.py")
    live = read("src/kodepoia/tuning/kaggle_live_qualification.py")
    accelerator = read("src/kodepoia/kodestudio/model_lab_accelerator.py")
    panel = read("src/kodepoia/kodestudio/model_lab_panel.py")
    sandbox = read("src/kodepoia/core/sandbox.py")
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    roadmap = read("docs/roadmap/KODEPOIA_ROADMAP_V2.md")
    v24 = read("docs/roadmap/V2_4_KAGGLE_T4X2_PRODUCTION_MULTIGPU.md")
    python_core = read(".github/workflows/python-core.yml")
    ui_smoke = read(".github/workflows/ui-smoke.yml")

    historical = {
        "topology": read("tests/test_v2_4_1_accelerator_topology.py"),
        "strategy": read("tests/test_v2_4_2_strategy_planning.py"),
        "execution": read("tests/test_v2_4_3_distributed_execution.py"),
        "recovery": read("tests/test_v2_4_4_distributed_recovery.py"),
        "live": read("tests/test_v2_4_5_model_lab_accelerator.py"),
        "live_pair": read("tests/test_v2_4_5_live_pair.py"),
    }

    current = (
        (
            "V2.4.6 — Production hardening and integrated acceptance "
            "is the only authorized implementation subdivision"
        )
        in authority
        and "V2.4.6 — Production hardening and integrated acceptance — CURRENT" in state
        and "V2.4.6 — Production hardening and integrated acceptance — CURRENT" in next_doc
        and "V2.4.6 CURRENT" in roadmap
        and (
            "V2.4.6 — Production hardening and integrated acceptance is now the only "
            "authorized implementation subdivision"
        )
        in v24
    )

    checks = [
        _check(
            "exact_head",
            source_sha == observed_sha,
            "acceptance executes the exact requested source SHA",
        ),
        _check(
            "current_authority",
            current,
            "V2.4.6 is the only authorized implementation subdivision",
        ),
        _check(
            "prior_chain_normalized",
            "V2.4.5 is COMPLETE + NORMALIZED" in authority
            and "V2.4.5 — Model Lab accelerator UX and live Kaggle qualification — COMPLETE + NORMALIZED"
            in state
            and "production_qualified=true" in state
            and "71e6a989db0426e0b33ac27c203bf3f812e4ed71" in state,
            "V2.4.1-V2.4.5 accepted truth remains normalized and terminal",
        ),
        _check(
            "provider_runtime_mismatch",
            "provider_device_count_mismatch" in topology
            and "provider_device_name_mismatch" in topology
            and "test_provider_device_count_and_name_mismatch_fail_closed"
            in historical["topology"],
            "provider metadata cannot substitute for observed runtime topology",
        ),
        _check(
            "duplicate_device_identity",
            "accelerator device indexes must be unique, ordered and contiguous" in topology
            and "test_topology_contract_rejects_duplicate_missing_and_noncontiguous_devices"
            in historical["topology"],
            "duplicate/missing/non-contiguous device ordinals fail closed",
        ),
        _check(
            "per_device_vram_no_pool",
            "vram_budget_unknown" in topology
            and "vram_current_free_insufficient" in topology
            and "aggregate_vram" not in topology
            and "test_replicated_strategy_rejects_pooled_vram_and_unknown_device_budget"
            in historical["strategy"]
            and '"pooled_vram_bytes": None' in accelerator,
            "VRAM remains per-device and unknown/insufficient devices cannot borrow an aggregate pool",
        ),
        _check(
            "strategy_world_device_binding",
            "world_size must equal selected device count" in strategy
            and "device_ordinals must be unique and sorted" in strategy
            and "test_strategy_requires_explicit_exact_ordinals_and_preserved_effective_batch"
            in historical["strategy"],
            "strategy, world size, device ordinals and effective batch remain exact lineage",
        ),
        _check(
            "thresholds_unchanged",
            "MIN_REPLICATED_THROUGHPUT_SPEEDUP_RATIO = 1.25" in strategy
            and "MAX_EVAL_LOSS_REGRESSION = 0.0" in strategy
            and "throughput_gain_below_threshold" in live
            and "eval_loss_regression" in live,
            ">=1.25x throughput and zero eval-loss regression remain unchanged",
        ),
        _check(
            "launcher_injection_boundary",
            '"torch.distributed.run"' in distributed
            and "--nproc-per-node=2" in distributed
            and "shell=False" in sandbox
            and "test_v246_launcher_and_security_boundaries_have_no_text_driven_escape_surface"
            in hardening,
            "distributed launch remains repository-owned, fixed and non-shell",
        ),
        _check(
            "rank_group_failures",
            "test_rank_failure_missing_or_mismatched_evidence_never_partially_succeeds"
            in historical["execution"]
            and "test_timeout_cancel_and_nonzero_are_whole_group_terminal"
            in historical["execution"]
            and "rank_group_failed" in distributed,
            "rank crash/timeout/cancellation cannot become partial success",
        ),
        _check(
            "orphan_process_boundary",
            "ManagedProcessGroup" in sandbox
            and "os.killpg" in sandbox
            and "taskkill" in sandbox
            and "test_process_sandbox_managed_group_executes_allowlisted_python"
            in historical["execution"],
            "launcher process groups are bounded by KillSwitch-compatible group termination",
        ),
        _check(
            "rank_evidence_disagreement",
            "canonical_rank" in distributed
            and "rank_evidence" in distributed
            and "canonical worker output digest mismatch" in distributed
            and "test_rank_failure_missing_or_mismatched_evidence_never_partially_succeeds"
            in historical["execution"],
            "rank-zero and per-rank evidence disagreement fails closed",
        ),
        _check(
            "tampered_lineage",
            "test_manifest_rejects_tampered_checkpoint_or_source_lineage"
            in historical["recovery"]
            and "test_missing_or_tampered_rank_recovery_evidence_never_succeeds"
            in historical["recovery"]
            and "checkpoint source topology lineage mismatch" in recovery,
            "tampered run/checkpoint/recovery lineage remains rejected",
        ),
        _check(
            "incompatible_recovery",
            "test_recovery_rejects_changed_topology_strategy_or_world_identity"
            in historical["recovery"]
            and "world_size" in recovery
            and "device_ordinals" in recovery
            and "strategy_plan_digest" in recovery,
            "recovery cannot silently change world size, device set or strategy",
        ),
        _check(
            "provider_degradation",
            "provider_auth_unavailable" in live
            and "test_v246_provider_degradation_remains_explicit_and_non_authorizing"
            in hardening
            and '"provider_state": str(kaggle.get("state", "not_checked"))' in accelerator,
            "auth/network/quota degradation remains explicit and non-authorizing",
        ),
        _check(
            "exact_source_live_separation",
            "source_sha_mismatch" in live
            and "request_digest_mismatch" in live
            and "download_revalidation_missing" in live
            and "secret_scan_not_proven" in live
            and "test_fixture_or_partial_provider_evidence_never_becomes_live_qualification"
            in historical["live"],
            "live production evidence is exact-source and separate from fixture/partial claims",
        ),
        _check(
            "integrated_adversarial_test",
            "test_v246_live_evidence_fails_closed_for_provider_topology_lineage_and_integrity_drift"
            in hardening
            and "test_v246_required_adversarial_contracts_remain_covered_by_v24_acceptance"
            in hardening,
            "V2.4.6 adds integrated adversarial regression proof over the accepted chain",
        ),
        _check(
            "degraded_ui",
            "test_v246_empty_accelerator_state_is_accessible_missing_and_non_authorizing" in ui
            and "test_v246_blocked_live_evidence_is_rendered_as_blocked_not_qualified" in ui
            and "modelLabAcceleratorLiveQualification" in panel
            and "modelLabAcceleratorDevices" in panel,
            "KodeStudio missing/blocked accelerator evidence remains accessible and honest",
        ),
        _check(
            "deterministic_provider_independent",
            "kaggle kernels push" not in hardening.lower()
            and "torch.cuda" not in hardening
            and "KaggleLiveProbeClient(" not in hardening
            and "KaggleLivePairClient(" not in hardening,
            "mandatory V2.4.6 tests require no live Kaggle/GPU provider",
        ),
        _check(
            "no_parallel_engine",
            not (root / "src/kodepoia/tuning/v2_4_6.py").exists()
            and not (root / "src/kodepoia/kodestudio/model_lab_hardening_v246.py").exists(),
            "hardening proves existing V2.4 services rather than creating a replacement engine",
        ),
        _check(
            "ci_wiring",
            "Run V2.4.6 production hardening exact-head acceptance" in python_core
            and "v2-4-6-production-hardening" in python_core
            and "tests/test_v2_4_6_production_hardening_ui.py" in python_core
            and "tests/test_v2_4_6_production_hardening_ui.py" in ui_smoke,
            "Ubuntu/Windows exact-head evidence and UI smoke are mandatory",
        ),
        _check(
            "security_authority",
            all(
                name in v24
                for name in (
                    "ResearchGuard",
                    "KodeSecrets",
                    "WorkspaceBoundary",
                    "ProcessSandbox",
                    "KillSwitch",
                )
            )
            and "Prompt/source/model text can never become distributed launcher argv" in v24,
            "existing trust boundaries remain authoritative",
        ),
        _check(
            "later_scope_unauthorized",
            "V2.5+ remain unauthorized" in authority
            and "V2.5+ remain unauthorized" in state
            and "release/TUF/updater" in next_doc
            and "R20.7" in next_doc
            and "v1.1.0-rc8" in authority,
            "V2.5+, release/TUF/updater mutation and R20 reopening remain outside scope",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.4.6",
        "title": "Production hardening and integrated acceptance",
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
