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
    observed_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

    def read(path: str) -> str:
        return (root / path).read_text(encoding="utf-8")

    recovery = read("src/kodepoia/tuning/distributed_recovery.py")
    distributed = read("src/kodepoia/tuning/distributed.py")
    worker = read("src/kodepoia/tuning/distributed_worker.py")
    training_worker = read("src/kodepoia/tuning/train_worker.py")
    tests = read("tests/test_v2_4_4_distributed_recovery.py")
    checkpoint_schema = read("schemas/v2-4-4-distributed-checkpoint.schema.json")
    recovery_schema = read("schemas/v2-4-4-distributed-recovery.schema.json")
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    v24 = read("docs/roadmap/V2_4_KAGGLE_T4X2_PRODUCTION_MULTIGPU.md")
    python_core = read(".github/workflows/python-core.yml")
    r159 = read(".github/workflows/r15-9-qlora-sft.yml")

    current = (
        "V2.4.4 — Distributed checkpoint, cancellation and recovery is the only authorized implementation subdivision"
        in authority
        and "V2.4.4 — Distributed checkpoint, cancellation and recovery — CURRENT" in state
        and "V2.4.4 — Distributed checkpoint, cancellation and recovery — CURRENT" in next_doc
    )
    normalized = (
        "V2.4.4 is COMPLETE + NORMALIZED" in authority
        and "V2.4.4 — Distributed checkpoint, cancellation and recovery — COMPLETE + NORMALIZED"
        in state
        and "V2.4.5 — Model Lab accelerator UX and live Kaggle qualification — CURRENT" in next_doc
    )

    checks = [
        _check("exact_head", source_sha == observed_sha, "acceptance executes exact requested SHA"),
        _check("current_authority", current or normalized, "V2.4.4 is current or retained after normalization"),
        _check(
            "later_scope_unauthorized",
            (
                current
                and "V2.4.5+ remain unauthorized" in authority
                and "V2.4.5+ remain unauthorized" in state
                and "V2.4.5+ remain unauthorized" in next_doc
                and "V2.4.5+ remain unauthorized" in v24
            )
            or (
                normalized
                and "V2.4.6+ remain unauthorized" in authority
                and "V2.4.6+ remain unauthorized" in state
                and "V2.4.6+ remain unauthorized" in next_doc
                and "V2.4.6+ remain unauthorized" in v24
            ),
            "later live-provider/hardening scope remains bounded",
        ),
        _check(
            "v243_execution_reused",
            "build_distributed_execution_plan" in recovery
            and "DISTRIBUTED_LAUNCH_POLICY" in recovery
            and '"torch.distributed.run"' in recovery
            and '"kodepoia.tuning.distributed_worker"' in recovery,
            "recovery reuses the accepted V2.4.3 execution plan and fixed worker boundary",
        ),
        _check(
            "historical_v243_resume_false",
            "resume_authorized: bool = False" in distributed
            and "distributed resume remains unauthorized until V2.4.4" in distributed,
            "historical V2.4.3 execution/report contract remains unchanged",
        ),
        _check(
            "rank_zero_checkpoint_lineage",
            "canonical_rank: int = 0" in recovery
            and "canonical-worker-output.json" in recovery
            and "ranks[0].canonical_output_digest" in recovery
            and "rank_evidence_digests" in recovery,
            "checkpoint manifest derives only from canonical rank-zero output plus both rank evidences",
        ),
        _check(
            "checkpoint_artifact_integrity",
            "checkpoint_metadata_digest" in recovery
            and "checkpoint_artifact_digest" in recovery
            and "distributed checkpoint metadata does not match canonical checkpoint" in recovery
            and "recovery checkpoint artifact digest mismatch" in recovery,
            "checkpoint metadata and adapter artifact are independently digest-bound",
        ),
        _check(
            "exact_lineage_binding",
            "execution_plan_digest" in recovery
            and "training_plan_digest" in recovery
            and "strategy_plan_digest" in recovery
            and "benchmark_report_digest" in recovery
            and "topology_digest" in recovery,
            "checkpoint/recovery identity binds exact execution/training/strategy/benchmark/topology lineage",
        ),
        _check(
            "world_device_binding",
            "world_size != 2" in recovery
            and "device_ordinals" in recovery
            and "topology/world-size identity mismatch" in recovery,
            "recovery cannot silently change world size or selected devices",
        ),
        _check(
            "resume_pre_max_only",
            "must precede max_steps" in recovery
            and "already at or beyond max_steps" in recovery,
            "only a checkpoint strictly before declared max_steps is resumable",
        ),
        _check(
            "worker_defense_in_depth",
            "DISTRIBUTED_RECOVERY_WORKER_CONFIG_SCHEMA" in recovery
            and "distributed-recovery-worker-config" in worker
            and "checkpoint metadata digest mismatch" in worker
            and "checkpoint artifact digest mismatch" in worker,
            "worker revalidates accepted recovery lineage and checkpoint files",
        ),
        _check(
            "fixed_launcher_no_escape",
            '"--standalone"' in recovery
            and '"--nnodes=1"' in recovery
            and '"--nproc-per-node=2"' in recovery
            and '"--max-restarts=0"' in recovery
            and "--rdzv-endpoint" not in recovery
            and "--rdzv-conf" not in recovery,
            "recovery launcher remains fixed one-node/two-rank with no caller rendezvous surface",
        ),
        _check(
            "bounded_environment",
            'env = {"CUDA_VISIBLE_DEVICES":' in recovery,
            "recovery injects only accepted device visibility",
        ),
        _check(
            "r159_worker_resume",
            "training_plan.worker_payload" in recovery
            and "resume_checkpoint" in training_worker
            and "resume_from_checkpoint" in training_worker
            and "from .train_worker import _run_real" in worker,
            "recovery reuses accepted R15.9 resume semantics rather than a new training engine",
        ),
        _check(
            "rank_recovery_evidence",
            "DistributedRecoveryRankEvidence" in recovery
            and "checkpoint_manifest_digest" in recovery
            and "resumed_from_checkpoint_id" in recovery
            and "resumed_from_step" in recovery,
            "each rank emits recovery-specific subordinate evidence",
        ),
        _check(
            "whole_group_terminal",
            "TIMED_OUT" in recovery
            and "CANCELLED" in recovery
            and "rank_group_failed" in recovery
            and "did not produce exactly two rank evidences" in recovery,
            "timeout/cancel/nonzero/missing-rank evidence cannot yield partial success",
        ),
        _check(
            "completed_requires_both_ranks",
            "completed recovery requires both rank evidences" in recovery
            and "completed recovery requires every rank completed" in recovery,
            "completed recovery requires the full two-rank group",
        ),
        _check(
            "tampered_rank_manifest_rejected",
            "recovery rank checkpoint manifest mismatch" in recovery
            and "recovery rank checkpoint lineage mismatch" in recovery
            and "bad_manifest_digest" in tests,
            "tampered per-rank recovery lineage fails closed",
        ),
        _check(
            "schema_validation",
            "Draft202012Validator(schema).validate(manifest.to_dict())" in tests
            and "Draft202012Validator(schema).validate(report.to_dict())" in tests
            and "distributed-checkpoint-manifest" in checkpoint_schema
            and "distributed-recovery-report" in recovery_schema,
            "checkpoint and recovery evidence have strict schemas",
        ),
        _check(
            "offline_deterministic_tests",
            "SourceCheckpointSandbox" in tests
            and "RecoverySandbox" in tests
            and "test_cancel_timeout_and_rank_failure_are_whole_group_terminal" in tests
            and "torch.cuda" not in tests,
            "mandatory recovery tests are deterministic and need no live GPU/Kaggle",
        ),
        _check(
            "exact_head_ci",
            "Run V2.4.4 distributed recovery exact-head acceptance" in python_core
            and "v2-4-4-distributed-recovery" in python_core
            and "tests/test_v2_4_4_distributed_recovery.py" in r159,
            "Ubuntu/Windows exact-head acceptance and focused R15.9 CI are wired",
        ),
        _check(
            "no_live_provider_scope",
            "kaggle" not in recovery.lower()
            and "Model Lab" not in recovery,
            "V2.4.4 contains no live-provider or Model Lab qualification path",
        ),
        _check(
            "no_sharded_tpu_scope",
            "DeepSpeed" not in recovery
            and "FullyShardedDataParallel" not in recovery
            and "torch_xla" not in recovery.lower()
            and "pipeline_parallel" not in recovery.lower(),
            "V2.4.4 adds no sharded-memory, pipeline or TPU strategy",
        ),
        _check(
            "public_import_lightweight",
            'assert "torch" not in sys.modules' in tests
            and 'assert "accelerate" not in sys.modules' in tests,
            "public tuning imports remain lightweight",
        ),
        _check(
            "public_release_boundary",
            "v1.1.0-rc8" in authority and "V2.5+" in state and "R20" in state,
            "V2.4.4 does not mutate public release/TUF/R20 authority",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.4.4",
        "title": "Distributed checkpoint, cancellation and recovery",
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
    output.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
