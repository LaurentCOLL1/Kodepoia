from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.kodestudio.model_lab_accelerator import accelerator_projection
from kodepoia.tuning.kaggle_live_qualification import (
    KaggleLiveProbeClient,
    KaggleLiveProbeRequest,
    KaggleLiveQualificationError,
    KaggleLiveQualificationRequest,
    build_private_probe_bundle,
    topology_report_from_probe,
    validate_live_evidence,
)
from kodepoia.tuning.kaggle_remote import CommandResult

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64
F = "f" * 64
SOURCE = "1" * 40


class FakeRunner:
    def __init__(self, results: list[CommandResult]) -> None:
        self.results = list(results)
        self.calls: list[list[str]] = []

    def run(self, argv: list[str], *, cwd=None, timeout: float = 120.0) -> CommandResult:
        del cwd, timeout
        self.calls.append(list(argv))
        return self.results.pop(0)


def _probe_request() -> KaggleLiveProbeRequest:
    return KaggleLiveProbeRequest(
        source_sha=SOURCE,
        kernel_id="fixture-user/kodepoia-v2-4-5-live",
    )


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
        kernel_id="fixture-user/kodepoia-v2-4-5-live",
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


def test_private_probe_bundle_bootstraps_before_final_lineage_and_is_secret_free(
    tmp_path: Path,
) -> None:
    request = _probe_request()
    root = build_private_probe_bundle(request, tmp_path / "probe")
    metadata = json.loads((root / "kernel-metadata.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "bundle-manifest.json").read_text(encoding="utf-8"))
    saved = json.loads((root / "probe-request.json").read_text(encoding="utf-8"))
    assert metadata["is_private"] is True
    assert metadata["machine_shape"] == "NvidiaTeslaT4"
    assert metadata["enable_internet"] is False
    assert manifest["source_sha"] == SOURCE
    assert saved["request_digest"] == request.digest
    assert "topology_digest" not in saved
    assert "training_plan_digest" not in saved
    serialized = json.dumps([metadata, manifest, saved]).lower()
    assert "kaggle_key" not in serialized
    assert "api_key" not in serialized
    assert "password" not in serialized


def test_probe_client_uses_only_fixed_kaggle_argv_and_revalidates_download(
    tmp_path: Path,
) -> None:
    request = _probe_request()
    bundle = build_private_probe_bundle(request, tmp_path / "bundle")
    output = tmp_path / "output"
    output.mkdir()
    probe = {
        "schema": "kodepoia.v2.4.5.kaggle-provider-probe",
        "schema_version": 1,
        "source_sha": request.source_sha,
        "request_digest": request.digest,
        "requested_shape": request.requested_shape,
        "kernel_id": request.kernel_id,
        "private_kernel": True,
        "backend_type": "cuda",
        "device_count": 2,
        "devices": [],
        "framework_versions": {"python": "3.12", "torch": "fixture", "cuda": "fixture"},
    }
    (output / "provider-probe.json").write_text(json.dumps(probe), encoding="utf-8")
    runner = FakeRunner(
        [
            CommandResult(0, "pushed", ""),
            CommandResult(0, "complete", ""),
            CommandResult(0, "downloaded", ""),
        ]
    )
    client = KaggleLiveProbeClient(runner=runner, kaggle_executable="kaggle-test")
    client.push(bundle)
    client.status(request)
    fetched = client.fetch_probe(request, output)
    assert fetched["source_sha"] == request.source_sha
    assert runner.calls == [
        ["kaggle-test", "kernels", "push", "--path", str(bundle.resolve())],
        ["kaggle-test", "kernels", "status", request.kernel_id],
        ["kaggle-test", "kernels", "output", request.kernel_id, "--path", str(output.resolve())],
    ]


def test_probe_client_rejects_tampered_download(tmp_path: Path) -> None:
    request = _probe_request()
    output = tmp_path / "output"
    output.mkdir()
    (output / "provider-probe.json").write_text(
        json.dumps(
            {
                "schema": "kodepoia.v2.4.5.kaggle-provider-probe",
                "source_sha": "2" * 40,
                "request_digest": request.digest,
                "kernel_id": request.kernel_id,
                "private_kernel": True,
            }
        ),
        encoding="utf-8",
    )
    client = KaggleLiveProbeClient(
        runner=FakeRunner([CommandResult(0, "downloaded", "")]),
        kaggle_executable="kaggle-test",
    )
    with pytest.raises(KaggleLiveQualificationError, match="source SHA mismatch"):
        client.fetch_probe(request, output)


def test_downloaded_probe_promotes_to_v241_topology_without_fabricating_devices() -> None:
    request = _probe_request()
    probe = {
        "schema": "kodepoia.v2.4.5.kaggle-provider-probe",
        "schema_version": 1,
        "source_sha": request.source_sha,
        "request_digest": request.digest,
        "requested_shape": request.requested_shape,
        "kernel_id": request.kernel_id,
        "private_kernel": True,
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
        "framework_versions": {"python": "3.12", "torch": "live", "cuda": "live"},
    }
    report = topology_report_from_probe(request, probe)
    assert report.disposition.value == "ready"
    assert report.request_digest == request.digest
    assert report.provider_request is not None
    assert report.provider_request.shape == "NvidiaTeslaT4"
    assert report.topology_digest is not None
    assert report.observed is not None
    assert [item.index for item in report.observed.devices] == [0, 1]
    assert [item.vram_total_bytes for item in report.observed.devices] == [
        16 * 1024**3,
        16 * 1024**3,
    ]


def test_complete_live_pair_is_qualified_only_after_download_revalidation() -> None:
    request = _request()
    report = validate_live_evidence(request, _evidence(request))
    assert report["status"] == "qualified"
    assert report["production_qualified"] is True
    assert report["blockers"] == []
    assert report["throughput_speedup_ratio"] == 1.4


def test_fixture_or_partial_provider_evidence_never_becomes_live_qualification() -> None:
    request = _request()
    evidence = _evidence(request)
    evidence["download_revalidated"] = False
    evidence["critical_regression_pass"] = False
    provider = dict(evidence["provider"])
    provider["authenticated"] = False
    evidence["provider"] = provider
    report = validate_live_evidence(request, evidence)
    assert report["production_qualified"] is False
    assert "download_revalidation_missing" in report["blockers"]
    assert "critical_regression_veto" in report["blockers"]
    assert "provider_auth_unavailable" in report["blockers"]


def test_topology_requires_two_separate_t4_devices_and_never_pools_vram() -> None:
    request = _request()
    evidence = _evidence(request)
    topology = dict(evidence["topology"])
    topology["device_count"] = 1
    topology["devices"] = list(topology["devices"])[:1]
    evidence["topology"] = topology
    report = validate_live_evidence(request, evidence)
    assert report["production_qualified"] is False
    assert "two_device_topology_not_proven" in report["blockers"]
    assert "pooled_vram_bytes" not in json.dumps(report)


def test_live_pair_rejects_subthreshold_or_quality_regression() -> None:
    request = _request()
    evidence = _evidence(request)
    runs = dict(evidence["runs"])
    replicated = dict(runs["replicated_data_parallel"])
    replicated["throughput_samples_per_second"] = 11.0
    replicated["eval_loss"] = 0.41
    runs["replicated_data_parallel"] = replicated
    evidence["runs"] = runs
    report = validate_live_evidence(request, evidence)
    assert "throughput_gain_below_threshold" in report["blockers"]
    assert "eval_loss_regression" in report["blockers"]
    assert report["production_qualified"] is False


def test_live_report_schema_accepts_qualified_report() -> None:
    report = validate_live_evidence(_request(), _evidence(_request()))
    schema = json.loads(
        Path("schemas/v2-4-5-kaggle-live-qualification.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(report)


def test_model_lab_accelerator_projection_keeps_devices_separate_and_strategy_visible(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    tuning = root / ".kodepoia" / "tuning"
    tuning.mkdir(parents=True)
    topology = {
        "schema": "kodepoia.v2.4.1.accelerator-topology",
        "disposition": "ready",
        "topology_digest": C,
        "provider_request": {
            "provider": "kaggle",
            "shape": "NvidiaTeslaT4",
            "expected_backend": "cuda",
            "expected_device_count": 2,
            "expected_name_contains": "T4",
        },
        "observed": _evidence(_request())["topology"],
    }
    (tuning / "topology.json").write_text(json.dumps(topology), encoding="utf-8")
    for strategy, digest, ordinals, world_size in (
        ("single_gpu", D, [0], 1),
        ("replicated_data_parallel", E, [0, 1], 2),
    ):
        payload = {
            "schema": "kodepoia.v2.4.2.execution-strategy-plan",
            "strategy": strategy,
            "strategy_plan_digest": digest,
            "training_plan_digest": A,
            "topology_report_digest": B,
            "topology_digest": C,
            "world_size": world_size,
            "device_ordinals": ordinals,
            "device_budgets": [],
            "per_device_batch_size": 1,
            "gradient_accumulation_steps": 4 // world_size,
            "effective_global_batch_size": 4,
        }
        (tuning / f"{strategy}.json").write_text(json.dumps(payload), encoding="utf-8")
    projection = accelerator_projection(root)
    assert projection["provider_request"]["shape"] == "NvidiaTeslaT4"
    assert len(projection["devices"]) == 2
    assert [item["vram_total_bytes"] for item in projection["devices"]] == [
        16 * 1024**3,
        16 * 1024**3,
    ]
    assert projection["pooled_vram_bytes"] is None
    assert {item["strategy"] for item in projection["strategies"]} == {
        "single_gpu",
        "replicated_data_parallel",
    }
