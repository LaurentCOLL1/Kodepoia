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

    distributed = read("src/kodepoia/tuning/distributed.py")
    worker = read("src/kodepoia/tuning/distributed_worker.py")
    training_worker = read("src/kodepoia/tuning/train_worker.py")
    sandbox = read("src/kodepoia/core/sandbox.py")
    tests = read("tests/test_v2_4_3_distributed_execution.py")
    schema = read("schemas/v2-4-3-distributed-training.schema.json")
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    v24 = read("docs/roadmap/V2_4_KAGGLE_T4X2_PRODUCTION_MULTIGPU.md")
    python_core = read(".github/workflows/python-core.yml")
    r159 = read(".github/workflows/r15-9-qlora-sft.yml")

    current = (
        "V2.4.3 — Governed explicit two-GPU execution is the only authorized "
        "implementation subdivision" in authority
        and "V2.4.3 — Governed explicit two-GPU execution — CURRENT" in state
        and "V2.4.3 — Governed explicit two-GPU execution — CURRENT" in next_doc
    )
    normalized = (
        "V2.4.3 is COMPLETE + NORMALIZED" in authority
        and "V2.4.3 — Governed explicit two-GPU execution — COMPLETE + NORMALIZED" in state
        and "V2.4.4 — Distributed checkpoint, cancellation and recovery — CURRENT" in next_doc
    )

    checks = [
        _check("exact_head", source_sha == observed_sha, "acceptance executes exact requested SHA"),
        _check(
            "current_authority",
            current or normalized,
            "V2.4.3 is current or retained as normalized historical context",
        ),
        _check(
            "later_scope_unauthorized",
            (
                current
                and "V2.4.4+ remain unauthorized" in authority
                and "V2.4.4+ remain unauthorized" in state
                and "V2.4.4+ remain unauthorized" in next_doc
                and "V2.4.4+ remain unauthorized" in v24
            )
            or (
                normalized
                and "V2.4.5+ remain unauthorized" in authority
                and "V2.4.5+ remain unauthorized" in state
                and "V2.4.5+ remain unauthorized" in next_doc
                and "V2.4.5+ remain unauthorized" in v24
            ),
            "later distributed recovery/live qualification scope remains bounded",
        ),
        _check(
            "v242_normalized_precondition",
            (
                "V2.4.2 is COMPLETE + NORMALIZED" in authority
                or "V2.4 planning, V2.4.1 and V2.4.2 are COMPLETE + NORMALIZED"
                in authority
                or "V2.4 planning, V2.4.1, V2.4.2 and **V2.4.3 are COMPLETE + NORMALIZED**"
                in authority
            )
            and "V2.4.2 — Strategy, effective-batch and resource planning contract — COMPLETE + NORMALIZED"
            in state,
            "V2.4.3 builds only on normalized V2.4.2 authority",
        ),
        _check(
            "qualified_benchmark_required",
            "StrategyBenchmarkDisposition.QUALIFIED" in distributed
            and "benchmark candidate strategy lineage mismatch" in distributed
            and "benchmark_report_digest" in distributed,
            "only exact qualified V2.4.2 benchmark evidence can enter launch planning",
        ),
        _check(
            "fixed_world_size_two",
            "world_size != 2" in distributed
            and '"--nproc-per-node=2"' in distributed
            and '"--nnodes=1"' in distributed,
            "launch is fixed to one node and exactly two ranks",
        ),
        _check(
            "fixed_repository_launcher",
            '"torch.distributed.run"' in distributed
            and '"--standalone"' in distributed
            and '"--max-restarts=0"' in distributed
            and '"--module"' in distributed
            and '"kodepoia.tuning.distributed_worker"' in distributed,
            "repository owns a fixed torchrun module launch with no restarts",
        ),
        _check(
            "bounded_launcher_environment",
            'env = {"CUDA_VISIBLE_DEVICES":' in distributed
            and "CUDA_VISIBLE_DEVICES does not match accepted device ordinals" in worker
            and "--rdzv-endpoint" not in distributed
            and "--rdzv-conf" not in distributed,
            "only accepted device visibility is injected; rendezvous is not caller-controlled",
        ),
        _check(
            "trusted_rank_identity",
            '_env_int("RANK")' in worker
            and '_env_int("LOCAL_RANK")' in worker
            and '_env_int("WORLD_SIZE")' in worker
            and '_env_int("LOCAL_WORLD_SIZE")' in worker
            and "rank != local_rank" in worker
            and "TORCHELASTIC_RESTART_COUNT" in worker,
            "rank/local-rank/world-size come only from trusted torchrun state and fail closed",
        ),
        _check(
            "strategy_seed_sampler_binding",
            "strategy rank/data seed lineage mismatch" in distributed
            and "shared_sampler_seed" in distributed
            and 'seeds["seed"] = int(seed["seed"])' in worker
            and 'seeds["data_seed"] = int(execution["shared_sampler_seed"])' in worker,
            "rank RNG and shared distributed sampler seed are strategy-bound",
        ),
        _check(
            "canonical_rank_zero",
            "canonical_rank != 0" in distributed
            and "canonical_output=rank == 0" in worker
            and "only completed rank zero may bind canonical output digest" in distributed,
            "only rank zero may emit canonical run output",
        ),
        _check(
            "subordinate_rank_evidence",
            "DistributedRankEvidence" in distributed
            and 'rank-{rank:05d}.json' in worker
            and "rank strategy lineage mismatch" in distributed
            and "rank topology lineage mismatch" in distributed,
            "every rank emits exact integrity-bound subordinate evidence",
        ),
        _check(
            "whole_group_terminal",
            "run_process_group" in distributed
            and "rank_group_failed" in distributed
            and "TIMED_OUT" in distributed
            and "CANCELLED" in distributed
            and "distributed rank did not complete" in distributed,
            "nonzero rank group, timeout, cancellation or missing rank prevents partial success",
        ),
        _check(
            "process_group_kill_switch",
            "class ManagedProcessGroup" in sandbox
            and "os.killpg" in sandbox
            and "CREATE_NEW_PROCESS_GROUP" in sandbox
            and "taskkill" in sandbox
            and "self.kill_switch.register(group)" in sandbox,
            "sandbox registers and terminates the complete launcher process group",
        ),
        _check(
            "r159_worker_reuse",
            "from .train_worker import _run_real" in worker
            and "canonical_output: bool = True" in training_worker
            and "trusted_local_rank" in training_worker,
            "V2.4.3 reuses the accepted R15.9 training worker implementation",
        ),
        _check(
            "distributed_resume_not_claimed",
            "resume_authorized: bool = False" in distributed
            and "distributed resume remains unauthorized until V2.4.4" in distributed
            and "resume checkpoint" not in tests.lower(),
            "V2.4.3 does not claim distributed checkpoint recovery",
        ),
        _check(
            "no_sharded_or_tpu_scope",
            "DeepSpeed" not in distributed
            and "FullyShardedDataParallel" not in distributed
            and "TpuV5E8" not in distributed
            and "torch_xla" not in distributed.lower()
            and "pipeline_parallel" not in distributed.lower(),
            "V2.4.3 adds no sharded-memory, pipeline or TPU strategy",
        ),
        _check(
            "offline_deterministic_tests",
            "FakeDistributedSandbox" in tests
            and "test_runner_uses_fixed_two_rank_torchrun_boundary_and_bounded_env" in tests
            and "test_rank_failure_missing_or_mismatched_evidence_never_partially_succeeds" in tests
            and "torch.cuda" not in tests,
            "mandatory tests use deterministic fakes and no live GPU/Kaggle",
        ),
        _check(
            "schema_validation",
            "Draft202012Validator(schema).validate(report.to_dict())" in tests
            and "v2-4-3-distributed-training.schema.json" in r159
            and "kodepoia.v2.4.3.distributed-training-report" in schema,
            "distributed report has a strict validated JSON schema",
        ),
        _check(
            "exact_head_ci",
            "Run V2.4.3 distributed execution exact-head acceptance" in python_core
            and "v2-4-3-distributed-execution" in python_core
            and "tests/test_v2_4_3_distributed_execution.py" in r159,
            "Ubuntu/Windows exact-head acceptance and focused R15.9 CI are wired",
        ),
        _check(
            "public_import_lightweight",
            'assert "torch" not in sys.modules' in tests
            and 'assert "accelerate" not in sys.modules' in tests,
            "public tuning imports remain usable without optional ML packages",
        ),
        _check(
            "public_release_boundary",
            "v1.1.0-rc8" in authority
            and "V2.5+" in state
            and "R20" in state,
            "V2.4.3 does not mutate release/TUF/R20 authority",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.4.3",
        "title": "Governed explicit two-GPU execution",
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
