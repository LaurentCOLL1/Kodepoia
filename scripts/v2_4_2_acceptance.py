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
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
    ).strip()

    def read(path: str) -> str:
        return (root / path).read_text(encoding="utf-8")

    strategy = read("src/kodepoia/tuning/strategy.py")
    topology = read("src/kodepoia/tuning/topology.py")
    training = read("src/kodepoia/tuning/training.py")
    tests = read("tests/test_v2_4_2_strategy_planning.py")
    plan_schema = read("schemas/v2-4-2-execution-strategy.schema.json")
    benchmark_schema = read("schemas/v2-4-2-strategy-benchmark.schema.json")
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    v24 = read("docs/roadmap/V2_4_KAGGLE_T4X2_PRODUCTION_MULTIGPU.md")
    python_core = read(".github/workflows/python-core.yml")
    r158 = read(".github/workflows/r15-8-training-runtime.yml")
    r159 = read(".github/workflows/r15-9-qlora-sft.yml")

    v242_current = (
        "V2.4.2 — Strategy, effective-batch and resource planning contract is the only "
        "authorized implementation subdivision"
        in authority
        and "V2.4.2 — Strategy, effective-batch and resource planning contract — CURRENT"
        in state
        and "V2.4.2 — Strategy, effective-batch and resource planning contract — CURRENT"
        in next_doc
    )
    v242_normalized = (
        "V2.4.2 is COMPLETE + NORMALIZED" in authority
        and "V2.4.2 — Strategy, effective-batch and resource planning contract — COMPLETE + NORMALIZED"
        in state
        and "V2.4.3 — Governed explicit two-GPU execution — CURRENT" in next_doc
    )

    checks = [
        _check("exact_head", source_sha == observed_sha, "acceptance executes exact requested SHA"),
        _check(
            "current_authority",
            v242_current or v242_normalized,
            "V2.4.2 is current or retained as normalized historical context",
        ),
        _check(
            "later_scope_unauthorized",
            (
                (
                    v242_current
                    and "V2.4.3+ remain unauthorized" in authority
                    and "V2.4.3+ remain unauthorized" in state
                    and "V2.4.3+ remain unauthorized" in next_doc
                    and "V2.4.3+ remain unauthorized" in v24
                )
                or (
                    v242_normalized
                    and "V2.4.4+ remain unauthorized" in authority
                    and "V2.4.4+ remain unauthorized" in state
                    and "V2.4.4+ remain unauthorized" in next_doc
                    and "V2.4.4+ remain unauthorized" in v24
                )
            ),
            "later V2.4 execution scope remains bounded",
        ),
        _check(
            "v241_topology_reused",
            "AcceleratorTopologyReport" in strategy
            and "TopologyDisposition.READY" in strategy
            and "topology_report.digest" in strategy
            and "topology_report.topology_digest" in strategy,
            "strategy plan reuses exact V2.4.1 topology evidence",
        ),
        _check(
            "training_plan_lineage",
            "training_plan_digest=training_plan.digest" in strategy
            and "TrainingPlan" in strategy
            and "training_plan_digest" in plan_schema,
            "strategy plan binds the immutable R15.9 TrainingPlan digest",
        ),
        _check(
            "typed_strategies_only",
            'SINGLE_GPU = "single_gpu"' in strategy
            and 'REPLICATED_DATA_PARALLEL = "replicated_data_parallel"' in strategy,
            "only single_gpu and replicated_data_parallel are represented",
        ),
        _check(
            "explicit_world_size_ordinals",
            "world_size" in strategy
            and "device_ordinals" in strategy
            and "expected_world_size = 1 if strategy is StrategyKind.SINGLE_GPU else 2" in strategy
            and "len(ordinals) != expected_world_size" in strategy,
            "world size and exact device ordinals are immutable strategy fields",
        ),
        _check(
            "per_device_vram_no_pool",
            "DeviceStrategyBudget" in strategy
            and "required_free_vram_bytes" in strategy
            and "aggregate_vram" not in strategy,
            "resource planning reasons about each selected device independently",
        ),
        _check(
            "host_resources_independent",
            "host_ram_required_bytes=training_plan.resources.ram_required_bytes" in strategy
            and "host_storage_required_bytes=training_plan.resources.disk_required_bytes" in strategy,
            "host RAM/storage remain single host budgets rather than world-size multiples",
        ),
        _check(
            "effective_batch_explicit",
            "per_device_batch_size" in strategy
            and "gradient_accumulation_steps" in strategy
            and "effective_global_batch_size" in strategy
            and "cannot preserve TrainingPlan effective global batch" in strategy,
            "per-device batch, accumulation and effective global batch are explicit",
        ),
        _check(
            "rank_seed_policy",
            'rank_seed_policy="offset_by_rank_v1"' in strategy
            and "SeedConfig" in strategy
            and "rank_seeds" in strategy,
            "rank/data seeds use a deterministic digest-bound offset policy",
        ),
        _check(
            "normative_threshold",
            "MIN_REPLICATED_THROUGHPUT_SPEEDUP_RATIO = 1.25" in strategy
            and "MAX_EVAL_LOSS_REGRESSION = 0.0" in strategy
            and "throughput_gain_below_threshold" in strategy,
            "replicated benchmark requires >=1.25x throughput with no eval-loss regression",
        ),
        _check(
            "paired_benchmark",
            "benchmark_config_mismatch" in strategy
            and "processed_samples_mismatch" in strategy
            and "effective_global_batch_mismatch" in strategy
            and "training_plan_mismatch" in strategy,
            "paired benchmark requires same work/config/plan/effective batch",
        ),
        _check(
            "integrity_gates",
            "run_integrity_failed" in strategy
            and "checkpoint_integrity_failed" in strategy
            and "peak_vram_exceeds_device_total" in strategy,
            "benchmark integrity and per-device resource evidence fail closed",
        ),
        _check(
            "inconclusive_state",
            'INCONCLUSIVE = "inconclusive"' in strategy
            and "eval_loss_missing" in strategy,
            "missing quality evidence is explicit rather than promoted",
        ),
        _check(
            "no_launch_authority",
            "launch_authorized: bool = False" in strategy
            and "V2.4.2 benchmark reports cannot authorize launch" in strategy
            and '"launch_authorized": {"const": false}' in benchmark_schema,
            "V2.4.2 benchmark evidence cannot authorize distributed launch",
        ),
        _check(
            "no_distributed_execution",
            "subprocess" not in strategy
            and "torchrun" not in strategy
            and "DistributedDataParallel" not in strategy
            and "accelerate launch" not in strategy,
            "strategy module contains no distributed execution path",
        ),
        _check(
            "no_training_engine_change",
            "replicated_data_parallel" not in training
            and "torchrun" not in training,
            "historical R15.9 TrainingRunner remains single-process and unchanged",
        ),
        _check(
            "deterministic_tests",
            "test_strategy_plans_bind_training_topology_world_size_batch_and_rank_seeds" in tests
            and "test_replicated_strategy_rejects_pooled_vram_and_unknown_device_budget" in tests
            and "test_paired_benchmark_qualifies_only_material_gain_without_quality_regression"
            in tests,
            "deterministic tests cover lineage, no pooling and paired qualification",
        ),
        _check(
            "schema_validation",
            "Draft202012Validator(schema).validate(single.to_dict())" in tests
            and "Draft202012Validator(schema).validate(report.to_dict())" in tests
            and "v2-4-2-execution-strategy.schema.json" in r158
            and "v2-4-2-strategy-benchmark.schema.json" in r159,
            "strategy plan and benchmark evidence have validated JSON schemas",
        ),
        _check(
            "exact_head_ci",
            "Run V2.4.2 strategy planning exact-head acceptance" in python_core
            and "v2-4-2-strategy-planning" in python_core
            and "tests/test_v2_4_2_strategy_planning.py" in r158
            and "tests/test_v2_4_2_strategy_planning.py" in r159,
            "Ubuntu/Windows exact-head acceptance and focused R15 CI are wired",
        ),
        _check(
            "offline_ci",
            "live Kaggle" not in tests
            and "torch.cuda" not in tests
            and "kaggle kernels push" not in tests,
            "required V2.4.2 tests need no live Kaggle or GPU",
        ),
        _check(
            "scope_boundaries",
            (
                "V2.4.3+" in state
                or (v242_normalized and "V2.4.4+" in state)
            )
            and "FSDP" in v24
            and "DeepSpeed" in v24
            and "TPU" in v24
            and "v1.1.0-rc8" in authority,
            "later distributed/sharded/TPU/release scope remains unauthorized",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.4.2",
        "title": "Strategy, effective-batch and resource planning contract",
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
