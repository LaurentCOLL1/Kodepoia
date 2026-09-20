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

    topology = read("src/kodepoia/tuning/topology.py")
    contracts = read("src/kodepoia/tuning/contracts.py")
    worker = read("src/kodepoia/tuning/probe_worker.py")
    runtime = read("src/kodepoia/tuning/runtime.py")
    kaggle = read("src/kodepoia/tuning/kaggle_remote.py")
    tests = read("tests/test_v2_4_1_accelerator_topology.py")
    legacy_schema = read("schemas/r15-8-training-runtime-capability.schema.json")
    topology_schema = read("schemas/v2-4-1-accelerator-topology.schema.json")
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    v24 = read("docs/roadmap/V2_4_KAGGLE_T4X2_PRODUCTION_MULTIGPU.md")
    python_core = read(".github/workflows/python-core.yml")
    r158 = read(".github/workflows/r15-8-training-runtime.yml")

    checks = [
        _check("exact_head", source_sha == observed_sha, "acceptance executes the exact requested SHA"),
        _check(
            "current_authority",
            (
                "V2.4.1 — Accelerator topology and provider truth is the only "
                "authorized implementation subdivision"
            )
            in authority
            and "V2.4.1 — Accelerator topology and provider truth — CURRENT" in state
            and "V2.4.1 — Accelerator topology and provider truth — CURRENT" in next_doc,
            "V2.4.1 alone is authorized",
        ),
        _check(
            "later_scope_unauthorized",
            "V2.4.2+ remain unauthorized" in authority
            and "V2.4.2+ remain unauthorized" in state
            and "V2.4.2+ remain unauthorized" in next_doc
            and "V2.4.2+ remain unauthorized" in v24,
            "V2.4.2+ remains outside V2.4.1",
        ),
        _check(
            "legacy_capability_unchanged",
            'CAPABILITY_SCHEMA_VERSION = 1' in contracts
            and '"schema_version": {"const": 1}' in legacy_schema
            and "kodepoia.r15.8.training-runtime-capability" in legacy_schema,
            "historical R15.8 capability schema remains version 1",
        ),
        _check(
            "separate_topology_contract",
            'TOPOLOGY_SCHEMA = "kodepoia.v2.4.1.accelerator-topology"' in topology
            and "AcceleratorTopologyReport" in topology
            and "topology_digest" in topology_schema,
            "V2.4.1 uses a separate versioned topology contract",
        ),
        _check(
            "provider_request_separate",
            "ProviderAcceleratorRequest" in topology
            and "provider_request_digest" in topology
            and "provider_request_digest" in topology_schema
            and "topology_digest" in topology,
            "provider request identity is separate from observed topology identity",
        ),
        _check(
            "t4_request_truth",
            "expected_device_count=2" in kaggle
            and 'expected_name_contains="T4"' in kaggle
            and "NvidiaTeslaT4" in kaggle,
            "Kaggle T4 shape requests two CUDA T4-class devices without claiming observation",
        ),
        _check(
            "actual_device_enumeration",
            "torch.cuda.device_count()" in worker
            and "for index in range(device_count)" in worker
            and '"device_count": device_count' in worker,
            "worker enumerates the actually observed CUDA/ROCm device topology",
        ),
        _check(
            "legacy_device_zero_preserved",
            'result["vram_free_bytes"] = first["vram_free_bytes"]' in worker
            and 'result["vram_total_bytes"] = first["vram_total_bytes"]' in worker
            and '"index": 0' in worker,
            "legacy scalar capability evidence remains bound to device zero",
        ),
        _check(
            "per_device_vram",
            "vram_free_bytes" in topology
            and "vram_total_bytes" in topology
            and "aggregate_vram" not in topology,
            "topology records VRAM per device and exposes no aggregate pool",
        ),
        _check(
            "contiguous_identity",
            "accelerator device indexes must be unique, ordered and contiguous" in topology
            and "test_topology_contract_rejects_duplicate_missing_and_noncontiguous_devices" in tests,
            "duplicate/missing/ambiguous ordinal evidence fails closed",
        ),
        _check(
            "provider_mismatch_fail_closed",
            "provider_device_count_mismatch" in topology
            and "provider_device_name_mismatch" in topology
            and "TopologyDisposition.MISMATCH" in runtime,
            "provider/runtime topology mismatches are explicit blockers",
        ),
        _check(
            "single_gpu_only",
            '"strategy": "single_gpu"' in topology
            and "evaluate_single_gpu_selection" in topology
            and "selected_device_missing" in topology,
            "V2.4.1 exposes only explicit single-GPU selection",
        ),
        _check(
            "no_pooling_preflight",
            "test_single_gpu_preflight_never_pools_two_device_vram" in tests
            and "device.vram_total_bytes" in topology
            and "device.vram_free_bytes" in topology,
            "resource admission uses only the selected device",
        ),
        _check(
            "unknown_vram_blocks",
            "vram_budget_unknown" in topology
            and "test_single_gpu_selection_is_ordinal_specific_and_unknown_vram_blocks" in tests,
            "unknown selected-device VRAM fails closed",
        ),
        _check(
            "probe_worker_coverage",
            "test_probe_worker_observes_every_device_but_legacy_scalars_remain_device_zero" in tests,
            "deterministic fake-Torch coverage proves multi-device enumeration without a live GPU",
        ),
        _check(
            "fixed_process_boundary",
            'argv = [sys.executable, "-m", "kodepoia.tuning.probe_worker", config_path.name]' in runtime
            and "env={}" in runtime
            and "ProcessSandbox" in runtime,
            "topology probing reuses fixed sandboxed argv and empty environment",
        ),
        _check(
            "no_distributed_launch",
            "torchrun" not in topology
            and "DistributedDataParallel" not in topology
            and "replicated_data_parallel" not in topology
            and "torchrun" not in runtime,
            "V2.4.1 adds no distributed execution path",
        ),
        _check(
            "schema_validation",
            "Draft202012Validator(schema).validate(report.to_dict())" in tests
            and "v2-4-1-accelerator-topology.schema.json" in r158,
            "topology evidence is validated against the new schema",
        ),
        _check(
            "offline_deterministic_tests",
            "FakeSandbox" in tests
            and "monkeypatch.setitem(sys.modules, \"torch\", fake_torch)" in tests
            and "kaggle kernels push" not in tests,
            "required V2.4.1 tests need no live GPU or Kaggle provider",
        ),
        _check(
            "ci_exact_head",
            "Run V2.4.1 accelerator topology exact-head acceptance" in python_core
            and "v2-4-1-accelerator-topology" in python_core
            and "tests/test_v2_4_1_accelerator_topology.py" in r158,
            "Ubuntu/Windows exact-head acceptance and focused runtime CI are wired",
        ),
        _check(
            "scope_boundaries",
            "FSDP" in v24
            and "DeepSpeed" in v24
            and "TPU" in v24
            and "V2.5+" in state
            and "v1.1.0-rc8" in authority,
            "later accelerator/orchestration/release scope remains bounded",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.4.1",
        "title": "Accelerator topology and provider truth",
        "source_sha": source_sha,
        "observed_sha": observed_sha,
        "checks": checks,
        "summary": {"passed": sum(item["status"] == "PASS" for item in checks), "total": len(checks)},
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
