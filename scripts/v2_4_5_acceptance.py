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

    accelerator = read("src/kodepoia/kodestudio/model_lab_accelerator.py")
    model_lab = read("src/kodepoia/kodestudio/model_lab.py")
    panel = read("src/kodepoia/kodestudio/model_lab_panel.py")
    localization = read("src/kodepoia/kodestudio/model_lab_localization.py")
    live = read("src/kodepoia/tuning/kaggle_live_qualification.py")
    bootstrap = read("src/kodepoia/tuning/kaggle_live_bootstrap.py")
    kaggle_remote = read("src/kodepoia/tuning/kaggle_remote.py")
    runtime = read("src/kodepoia/tuning/runtime.py")
    sandbox = read("src/kodepoia/core/sandbox.py")
    bootstrap_tests = read("tests/test_v2_4_5_live_bootstrap.py")
    runtime_tests = read("tests/test_tuning_r15_8.py")
    workload = read("qualification/v2_4_5/live_workload.json")
    tests = read("tests/test_v2_4_5_model_lab_accelerator.py")
    ui_tests = read("tests/test_v2_4_5_model_lab_accelerator_ui.py")
    schema = read("schemas/v2-4-5-kaggle-live-qualification.schema.json")
    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    v24 = read("docs/roadmap/V2_4_KAGGLE_T4X2_PRODUCTION_MULTIGPU.md")
    python_core = read(".github/workflows/python-core.yml")
    ui_smoke = read(".github/workflows/ui-smoke.yml")
    kaggle_ci = read(".github/workflows/r15-kaggle-remote-training.yml")

    current = (
        "V2.4.5 — Model Lab accelerator UX and live Kaggle qualification is the only authorized implementation subdivision"
        in authority
        and "V2.4.5 — Model Lab accelerator UX and live Kaggle qualification — CURRENT" in state
        and "V2.4.5 — Model Lab accelerator UX and live Kaggle qualification — CURRENT" in next_doc
    )
    normalized = (
        "V2.4.5 is COMPLETE + NORMALIZED" in authority
        and "V2.4.5 — Model Lab accelerator UX and live Kaggle qualification — COMPLETE + NORMALIZED" in state
        and "V2.4.6 — Production hardening and integrated acceptance — CURRENT" in next_doc
    )

    checks = [
        _check("exact_head", source_sha == observed_sha, "acceptance executes exact requested SHA"),
        _check("current_authority", current or normalized, "V2.4.5 is current or normalized historical context"),
        _check(
            "later_scope_unauthorized",
            (
                current
                and "V2.4.6+ remain unauthorized" in authority
                and "V2.4.6+ remain unauthorized" in state
                and "V2.4.6+ remain unauthorized" in next_doc
                and "V2.4.6+ remain unauthorized" in v24
            )
            or normalized,
            "V2.4.6 hardening remains outside V2.4.5 implementation",
        ),
        _check(
            "requested_vs_observed",
            "provider_request" in accelerator
            and "topology_state" in accelerator
            and "provider_state" in accelerator,
            "Model Lab distinguishes requested provider, observed topology and provider runtime state",
        ),
        _check(
            "separate_device_rows",
            "vram_free_bytes" in accelerator
            and "vram_total_bytes" in accelerator
            and '"pooled_vram_bytes": None' in accelerator
            and "modelLabAcceleratorDevices" in panel,
            "devices remain separate and no pooled 32 GiB value exists",
        ),
        _check(
            "strategy_projection_only",
            "modelLabAcceleratorStrategy" in panel
            and "effective_global_batch_size" in accelerator
            and "world_size" in accelerator
            and "device_ordinals" in accelerator
            and "modelLabAcceleratorLaunch" not in panel,
            "strategy selector is inspection-only and exposes batch/world/device mapping",
        ),
        _check(
            "no_startup_provider_call",
            "runtime inventory is refreshed only on explicit request" in model_lab
            and "Kaggle state is refreshed only on explicit request" in model_lab
            and "refresh_runtime.clicked.connect(refresh_runtime_now)" in panel,
            "Kaggle/Ollama provider calls remain explicit refresh only",
        ),
        _check(
            "honest_provider_states",
            "authenticated" in accelerator
            and "gpu_quota" in accelerator
            and "provider_detail" in accelerator,
            "auth/quota/unavailable detail remains structured",
        ),
        _check(
            "exact_source_live_request",
            "source_sha must be a full 40-character Git SHA" in live
            and "training_plan_digest" in live
            and "topology_report_digest" in live
            and "execution_plan_digest" in live
            and "recovery_plan_digest" in live,
            "live qualification request binds exact source and V2.4.1-V2.4.4 lineage",
        ),
        _check(
            "private_probe_bundle",
            "class KaggleLiveProbeRequest" in live
            and "kernel_id must be an exact Kaggle owner/kernel-slug reference" in live
            and '"title": request.kernel_id.split("/", 1)[1]' in live
            and "probe-request.json" in live
            and "embedded_request = json.dumps(" in live
            and 'Path("probe-request.json").read_text' not in live
            and "topology_report_from_probe" in live
            and '"is_private": True' in live
            and '"machine_shape": request.requested_shape' in live
            and '"enable_internet": False' in live
            and "provider-probe.json" in live
            and "KaggleLiveProbeClient" in live
            and '"kernels", "push"' in live
            and '"kernels", "output"' in live
            and '"--quiet"' in live,
            "provider probe bootstraps exact-source private topology before final lineage",
        ),
        _check(
            "two_t4_runtime_truth",
            "two_device_topology_not_proven" in live
            and "device_not_t4" in live
            and "device_vram_invalid" in live
            and "device_ordinals_invalid" in live,
            "live evidence must prove two separate usable T4 CUDA devices",
        ),
        _check(
            "paired_live_runs",
            'expected_strategy="single_gpu"' in live
            and 'expected_strategy="replicated_data_parallel"' in live
            and "paired_benchmark_config_mismatch" in live
            and "processed_samples_mismatch" in live,
            "single and replicated live runs are paired on common work/config",
        ),
        _check(
            "performance_quality_veto",
            "MIN_REPLICATED_THROUGHPUT_SPEEDUP_RATIO" in live
            and "throughput_gain_below_threshold" in live
            and "eval_loss_regression" in live
            and "critical_regression_veto" in live,
            "live qualification preserves throughput threshold and critical-regression/quality vetoes",
        ),
        _check(
            "download_revalidation_required",
            "download_revalidation_missing" in live
            and "secret_scan_not_proven" in live
            and "production_qualified" in live,
            "provider success alone cannot become production qualification",
        ),
        _check(
            "fixture_cannot_claim_live",
            "test_fixture_or_partial_provider_evidence_never_becomes_live_qualification" in tests
            and "production_qualified" in tests,
            "deterministic fixtures explicitly prove blocked live status when proof is incomplete",
        ),
        _check(
            "localization_accessibility",
            '"accelerator"' in localization
            and "_FR" in localization
            and "qps-ploc" in localization
            and "test_model_lab_accelerator_ui_is_structured_localized_and_accessible" in ui_tests,
            "accelerator UX is FR/EN/qps-ploc and accessibility-tested",
        ),
        _check(
            "schema_validation",
            "Draft202012Validator(schema).validate(report)" in tests
            and "kaggle-live-qualification-report" in schema,
            "live qualification report has strict schema validation",
        ),
        _check(
            "offline_ci",
            "tests/test_v2_4_5_model_lab_accelerator.py" in kaggle_ci
            and "tests/test_v2_4_5_model_lab_accelerator_ui.py" in ui_smoke
            and "Run V2.4.5 Model Lab accelerator exact-head acceptance" in python_core,
            "mandatory PR CI remains deterministic and includes backend/UI exact-head coverage",
        ),
        _check(
            "governed_live_bootstrap",
            "source_sha must be 40 lowercase hexadecimal characters" in bootstrap
            and 'QUALIFICATION_MODEL_REF = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"' in bootstrap
            and 'QUALIFICATION_MODEL_REVISION = "fe8a4ea1ffedaf415f4da2f062534de366a451e6"' in bootstrap
            and "build_live_qualification_dataset" in bootstrap
            and "def _validated_wheel_filename" in bootstrap
            and '"wheel_filename": self.wheel_filename' in bootstrap
            and '"wheel_sha256": self.wheel_sha256' in bootstrap
            and (
                "shutil.copy2(wheel_path, dataset_dir / wheel_filename)"
                in bootstrap
            )
            and "wheel = work / wheel_filename" in bootstrap
            and '"kodepoia.whl"' not in bootstrap
            and '"datasets",' in bootstrap
            and '"create",' in bootstrap
            and '"kernels",' in bootstrap
            and '"push",' in bootstrap
            and '"output",' in bootstrap
            and '"--quiet",' in bootstrap
            and 'child_env["PYTHONUTF8"] = "1"' in kaggle_remote
            and 'child_env["PYTHONIOENCODING"] = "utf-8"' in kaggle_remote
            and 'encoding="utf-8"' in kaggle_remote
            and 'errors="strict"' in kaggle_remote
            and "test_subprocess_runner_forces_utf8_for_kaggle_child"
            in bootstrap_tests
            and (
                "Bounded V2.4.5 R15.8 CUDA subprocess-environment repair amendment"
                in authority
            )
            and '_CUDA_RUNTIME_ENV_KEYS = (' in runtime
            and '"LD_LIBRARY_PATH",' in runtime
            and '"CUDA_VISIBLE_DEVICES",' in runtime
            and '"CUDA_DEVICE_ORDER",' in runtime
            and '"NVIDIA_VISIBLE_DEVICES",' in runtime
            and '"NVIDIA_DRIVER_CAPABILITIES",' in runtime
            and "env=_runtime_worker_environment()" in runtime
            and '"CUDA_VISIBLE_DEVICES"' not in sandbox
            and '"NVIDIA_VISIBLE_DEVICES"' not in sandbox
            and "test_runtime_forwards_only_fixed_cuda_parent_environment"
            in runtime_tests
            and "test_runtime_does_not_invent_absent_cuda_environment"
            in runtime_tests
            and (
                "Bounded V2.4.5 R15.8 local-snapshot model-load dry-run repair amendment"
                in authority
            )
            and 'QUALIFICATION_RUNTIME_MODEL_RELATIVE = "model-snapshot"' in bootstrap
            and "def stage_runtime_model_snapshot(" in bootstrap
            and "runtime_model_dir = stage_runtime_model_snapshot(" in bootstrap
            and "model_ref=QUALIFICATION_RUNTIME_MODEL_RELATIVE" in bootstrap
            and "model_revision=None" in bootstrap
            and "tokenizer_ref=QUALIFICATION_RUNTIME_MODEL_RELATIVE" in bootstrap
            and "local_files_only=True" in bootstrap
            and "trust_remote_code=False" in bootstrap
            and "HF_HOME" not in bootstrap
            and "HF_HUB_CACHE" not in bootstrap
            and "HF_TOKEN" not in bootstrap
            and "HUGGINGFACE_HUB_CACHE" not in bootstrap
            and "test_stage_runtime_model_snapshot_copies_exact_verified_files"
            in bootstrap_tests
            and (
                "test_stage_runtime_model_snapshot_rejects_incomplete_tampered_or_preexisting"
                in bootstrap_tests
            )
            and "GapDecisionEngine().evaluate" in bootstrap
            and "if decision.disposition is DecisionDisposition.TRAIN" in bootstrap
            and '"promotion_authorized": False' in bootstrap
            and '"qualification_only": True' in bootstrap
            and "--public" not in bootstrap
            and '"schema": "kodepoia.v2.4.5.live-qualification-workload"' in workload
            and "test_live_bootstrap_accepts_exact_git_sha" in bootstrap_tests
            and "test_live_bootstrap_client_uses_fixed_kaggle_argv" in bootstrap_tests
            and (
                "test_live_bootstrap_preserves_exact_wheel_filename_and_hashes_it"
                in bootstrap_tests
            )
            and "test_live_bootstrap_rejects_invalid_wheel_filename"
            in bootstrap_tests
            and "test_finalize_live_bootstrap_does_not_force_train" in bootstrap_tests,
            (
                "governed bootstrap preserves exact wheel identity, uses quiet "
                "UTF-8-fixed output retrieval, keeps R15.8 CUDA env propagation bounded, "
                "binds model dry-run to the verified local snapshot, stays private/"
                "non-promotable and is R15.7-gated"
            ),
        ),
        _check(
            "no_forbidden_scope",
            "DeepSpeed" not in live
            and "FullyShardedDataParallel" not in live
            and "torch_xla" not in live.lower()
            and "V2.5+" in state
            and "v1.1.0-rc8" in authority,
            "V2.4.5 adds no V2.4.6/V2.5/sharded/TPU/release scope",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.4.5",
        "title": "Model Lab accelerator UX and live Kaggle qualification",
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
    output.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
