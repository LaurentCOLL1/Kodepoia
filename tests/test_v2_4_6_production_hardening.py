from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from kodepoia.kodestudio.model_lab_accelerator import (
    accelerator_projection,
    provider_runtime_projection,
)
from kodepoia.tuning.kaggle_live_qualification import (
    KaggleLiveQualificationRequest,
    validate_live_evidence,
)


A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64
F = "f" * 64
SOURCE = "1" * 40


def _request() -> KaggleLiveQualificationRequest:
    return KaggleLiveQualificationRequest(
        source_sha=SOURCE,
        training_plan_digest=A,
        topology_report_digest=B,
        topology_digest=C,
        single_strategy_plan_digest=D,
        replicated_strategy_plan_digest=E,
        benchmark_report_digest=F,
        execution_plan_digest=A,
        recovery_plan_digest=B,
        kernel_id="fixture-user/kodepoia-v2-4-6-hardening",
    )


def _evidence(request: KaggleLiveQualificationRequest) -> dict[str, object]:
    common = {
        "benchmark_config_digest": C,
        "checkpoint_integrity": True,
        "effective_global_batch_size": 4,
        "processed_samples": 1000,
        "run_integrity": True,
        "topology_digest": request.topology_digest,
        "training_plan_digest": request.training_plan_digest,
    }
    return {
        "source_sha": request.source_sha,
        "request_digest": request.digest,
        "provider": {
            "authenticated": True,
            "kernel_id": request.kernel_id,
            "private_kernel": True,
            "requested_shape": "NvidiaTeslaT4",
        },
        "topology": {
            "backend_type": "cuda",
            "device_count": 2,
            "devices": [
                {
                    "backend_type": "cuda",
                    "index": 0,
                    "name": "NVIDIA Tesla T4",
                    "vram_free_bytes": 12 * 1024**3,
                    "vram_total_bytes": 16 * 1024**3,
                },
                {
                    "backend_type": "cuda",
                    "index": 1,
                    "name": "NVIDIA Tesla T4",
                    "vram_free_bytes": 11 * 1024**3,
                    "vram_total_bytes": 16 * 1024**3,
                },
            ],
        },
        "runs": {
            "single_gpu": {
                **common,
                "eval_loss": 0.4,
                "state": "completed",
                "strategy": "single_gpu",
                "strategy_plan_digest": request.single_strategy_plan_digest,
                "throughput_samples_per_second": 10.0,
            },
            "replicated_data_parallel": {
                **common,
                "eval_loss": 0.4,
                "execution_plan_digest": request.execution_plan_digest,
                "state": "completed",
                "strategy": "replicated_data_parallel",
                "strategy_plan_digest": request.replicated_strategy_plan_digest,
                "throughput_samples_per_second": 14.0,
            },
        },
        "recovery_plan_digest": request.recovery_plan_digest,
        "critical_regression_pass": True,
        "download_revalidated": True,
        "secret_scan_pass": True,
    }


def test_v246_required_adversarial_contracts_remain_covered_by_v24_acceptance() -> None:
    root = Path(__file__).resolve().parents[1]
    topology = (root / "tests/test_v2_4_1_accelerator_topology.py").read_text(encoding="utf-8")
    strategy = (root / "tests/test_v2_4_2_strategy_planning.py").read_text(encoding="utf-8")
    execution = (root / "tests/test_v2_4_3_distributed_execution.py").read_text(encoding="utf-8")
    recovery = (root / "tests/test_v2_4_4_distributed_recovery.py").read_text(encoding="utf-8")
    live = (root / "tests/test_v2_4_5_model_lab_accelerator.py").read_text(encoding="utf-8")
    live_pair = (root / "tests/test_v2_4_5_live_pair.py").read_text(encoding="utf-8")

    required = (
        (topology, "test_provider_device_count_and_name_mismatch_fail_closed"),
        (topology, "test_topology_contract_rejects_duplicate_missing_and_noncontiguous_devices"),
        (topology, "test_single_gpu_preflight_never_pools_two_device_vram"),
        (topology, "test_single_gpu_selection_is_ordinal_specific_and_unknown_vram_blocks"),
        (strategy, "test_replicated_strategy_rejects_pooled_vram_and_unknown_device_budget"),
        (strategy, "test_strategy_requires_explicit_exact_ordinals_and_preserved_effective_batch"),
        (execution, "test_rank_failure_missing_or_mismatched_evidence_never_partially_succeeds"),
        (execution, "test_timeout_cancel_and_nonzero_are_whole_group_terminal"),
        (execution, "test_process_sandbox_managed_group_executes_allowlisted_python"),
        (recovery, "test_manifest_rejects_tampered_checkpoint_or_source_lineage"),
        (recovery, "test_missing_or_tampered_rank_recovery_evidence_never_succeeds"),
        (recovery, "test_recovery_rejects_changed_topology_strategy_or_world_identity"),
        (live, "test_fixture_or_partial_provider_evidence_never_becomes_live_qualification"),
        (live, "test_topology_requires_two_separate_t4_devices_and_never_pools_vram"),
        (live, "test_live_pair_rejects_subthreshold_or_quality_regression"),
        (live_pair, "test_live_pair_download_preserves_honest_benchmark_rejection"),
    )
    for source, marker in required:
        assert marker in source, marker


def test_v246_live_evidence_fails_closed_for_provider_topology_lineage_and_integrity_drift() -> None:
    request = _request()
    evidence = _evidence(request)
    evidence["source_sha"] = "2" * 40
    evidence["download_revalidated"] = False
    evidence["secret_scan_pass"] = False
    evidence["critical_regression_pass"] = False

    provider = dict(evidence["provider"])
    provider["authenticated"] = False
    evidence["provider"] = provider

    topology = deepcopy(evidence["topology"])
    devices = deepcopy(topology["devices"])
    devices[1]["index"] = 0
    devices[1]["vram_free_bytes"] = 17 * 1024**3
    topology["devices"] = devices
    evidence["topology"] = topology

    runs = deepcopy(evidence["runs"])
    replicated = dict(runs["replicated_data_parallel"])
    replicated["strategy"] = "single_gpu"
    replicated["topology_digest"] = F
    replicated["execution_plan_digest"] = F
    replicated["run_integrity"] = False
    replicated["checkpoint_integrity"] = False
    replicated["throughput_samples_per_second"] = 11.0
    replicated["eval_loss"] = 0.41
    runs["replicated_data_parallel"] = replicated
    evidence["runs"] = runs
    evidence["recovery_plan_digest"] = F

    report = validate_live_evidence(request, evidence)
    blockers = set(report["blockers"])
    assert report["production_qualified"] is False
    assert {
        "source_sha_mismatch",
        "provider_auth_unavailable",
        "device_ordinals_invalid",
        "device_vram_invalid",
        "replicated_strategy_mismatch",
        "replicated_topology_mismatch",
        "replicated_run_integrity_failed",
        "replicated_checkpoint_integrity_failed",
        "execution_plan_mismatch",
        "recovery_plan_mismatch",
        "throughput_gain_below_threshold",
        "eval_loss_regression",
        "critical_regression_veto",
        "download_revalidation_missing",
        "secret_scan_not_proven",
    } <= blockers


def test_v246_provider_degradation_remains_explicit_and_non_authorizing() -> None:
    accelerator = {
        "schema": "kodepoia.v2.4.5.model-lab-accelerator",
        "live_qualification": {
            "state": "missing",
            "production_qualified": False,
            "blockers": [],
        },
        "pooled_vram_bytes": None,
    }
    projected = provider_runtime_projection(
        accelerator,
        {
            "state": "unavailable",
            "detail": "authentication/network/quota unavailable",
            "doctor": {
                "authenticated": False,
                "cli_available": True,
                "version": "fixture",
            },
            "quota": {"entries": []},
        },
    )
    assert projected["provider_state"] == "unavailable"
    assert projected["authenticated"] is False
    assert projected["gpu_quota"] is None
    assert projected["live_qualification"]["production_qualified"] is False
    assert projected["pooled_vram_bytes"] is None


def test_v246_projection_keeps_missing_or_blocked_live_evidence_honest(tmp_path: Path) -> None:
    root = tmp_path / "project"
    tuning = root / ".kodepoia" / "tuning"
    tuning.mkdir(parents=True)

    missing = accelerator_projection(root)
    assert missing["topology_state"] == "missing"
    assert missing["devices"] == []
    assert missing["strategies"] == []
    assert missing["live_qualification"]["state"] == "missing"
    assert missing["live_qualification"]["production_qualified"] is False
    assert missing["pooled_vram_bytes"] is None

    blocked = {
        "schema": "kodepoia.v2.4.5.kaggle-live-qualification-report",
        "schema_version": 1,
        "source_sha": SOURCE,
        "status": "blocked",
        "production_qualified": False,
        "blockers": ["provider_auth_unavailable", "download_revalidation_missing"],
        "report_digest": A,
    }
    (tuning / "live-blocked.json").write_text(
        json.dumps(blocked, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    projected = accelerator_projection(root)
    assert projected["live_qualification"]["state"] == "blocked"
    assert projected["live_qualification"]["production_qualified"] is False
    assert projected["live_qualification"]["source_sha"] == SOURCE
    assert set(projected["live_qualification"]["blockers"]) == {
        "provider_auth_unavailable",
        "download_revalidation_missing",
    }
    assert projected["pooled_vram_bytes"] is None


def test_v246_launcher_and_security_boundaries_have_no_text_driven_escape_surface() -> None:
    root = Path(__file__).resolve().parents[1]
    distributed = (root / "src/kodepoia/tuning/distributed.py").read_text(encoding="utf-8")
    worker = (root / "src/kodepoia/tuning/distributed_worker.py").read_text(encoding="utf-8")
    sandbox = (root / "src/kodepoia/core/sandbox.py").read_text(encoding="utf-8")
    runtime = (root / "src/kodepoia/tuning/runtime.py").read_text(encoding="utf-8")

    assert '"torch.distributed.run"' in distributed
    assert "--nproc-per-node=2" in distributed
    assert "shell=False" in sandbox
    assert "ManagedProcessGroup" in sandbox
    assert "TORCHELASTIC_RESTART_COUNT" in worker
    assert "_CUDA_RUNTIME_ENV_KEYS = (" in runtime
    for forbidden in (
        "ResearchPack",
        "ProjectKnowledge",
        "prompt_launcher_args",
        "model_launcher_args",
        "package_install_request",
        "rendezvous_endpoint_from_text",
    ):
        assert forbidden not in distributed
