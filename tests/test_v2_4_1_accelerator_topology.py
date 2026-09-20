from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from jsonschema import Draft202012Validator

from kodepoia.core.kill_switch import KillSwitch
from kodepoia.core.sandbox import SandboxResult
from kodepoia.tuning import ResourceRequest, RuntimeRequest, TrainingBackend, TrainingRuntime
from kodepoia.tuning.kaggle_remote import KaggleRemoteConfig
from kodepoia.tuning.probe_worker import _base_result, _torch_probe
from kodepoia.tuning.topology import (
    AcceleratorDevice,
    AcceleratorTopologyReport,
    ObservedAcceleratorTopology,
    ProviderAcceleratorRequest,
    TopologyDisposition,
    evaluate_single_gpu_selection,
)


class FakeSandbox:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.calls = 0

    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        del argv, timeout
        assert cwd is not None
        assert env == {}
        self.calls += 1
        return SandboxResult(0, json.dumps(self.payload), "")


def _device(index: int, *, free: int | None = 8_000, total: int | None = 16_000) -> dict[str, object]:
    return {
        "backend_type": "cuda",
        "index": index,
        "name": "NVIDIA Tesla T4",
        "vram_free_bytes": free,
        "vram_total_bytes": total,
    }


def _worker_topology(devices: list[dict[str, object]]) -> dict[str, object]:
    first = devices[0] if devices else None
    return {
        "backend": "cuda",
        "backend_capability": "supported",
        "device": (
            None
            if first is None
            else {
                "backend_type": "cuda",
                "index": 0,
                "name": first["name"],
            }
        ),
        "dtype_supported": True,
        "four_bit_supported": None,
        "model_load": None,
        "packages": {"torch": "2.fixture"},
        "python_version": "3.12.fixture",
        "seed_applied": True,
        "topology": {
            "backend_type": "cuda",
            "device_count": len(devices),
            "devices": devices,
        },
        "torch_backend_version": "12.fixture",
        "vram_free_bytes": None if first is None else first["vram_free_bytes"],
        "vram_total_bytes": None if first is None else first["vram_total_bytes"],
    }


def _runtime(tmp_path: Path, devices: list[dict[str, object]]) -> TrainingRuntime:
    return TrainingRuntime(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=FakeSandbox(_worker_topology(devices)),
    )


def test_t4_provider_request_is_explicit_and_not_runtime_truth() -> None:
    config = KaggleRemoteConfig(
        username="fixtureUser",
        dataset_slug="fixture-data",
        kernel_slug="fixture-kernel",
    )
    request = config.topology_request()
    assert request.provider == "kaggle"
    assert request.shape == "NvidiaTeslaT4"
    assert request.expected_backend is TrainingBackend.CUDA
    assert request.expected_device_count == 2
    assert request.expected_name_contains == "T4"
    assert "observed" not in request.to_dict()


def test_probe_topology_matches_two_t4_devices_and_validates_schema(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, [_device(0, free=9_000), _device(1, free=7_000)])
    request = RuntimeRequest(backend=TrainingBackend.CUDA)
    provider = ProviderAcceleratorRequest(
        provider="kaggle",
        shape="NvidiaTeslaT4",
        expected_backend=TrainingBackend.CUDA,
        expected_device_count=2,
        expected_name_contains="T4",
    )
    report = runtime.probe_topology(request, provider_request=provider)
    assert report.disposition is TopologyDisposition.READY
    assert report.observed is not None
    assert report.observed.device_count == 2
    assert [item.vram_free_bytes for item in report.observed.devices] == [9_000, 7_000]
    assert report.topology_digest == report.observed.digest
    assert report.provider_request_digest == provider.digest

    schema = json.loads(
        Path("schemas/v2-4-1-accelerator-topology.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(report.to_dict())


def test_provider_device_count_and_name_mismatch_fail_closed(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, [_device(0)])
    provider = ProviderAcceleratorRequest(
        provider="kaggle",
        shape="NvidiaTeslaT4",
        expected_backend=TrainingBackend.CUDA,
        expected_device_count=2,
        expected_name_contains="T4",
    )
    report = runtime.probe_topology(
        RuntimeRequest(backend=TrainingBackend.CUDA),
        provider_request=provider,
    )
    assert report.disposition is TopologyDisposition.MISMATCH
    assert report.blockers == ("provider_device_count_mismatch",)

    wrong_name = _device(0)
    wrong_name["name"] = "Unexpected accelerator"
    runtime = _runtime(tmp_path / "wrong-name", [wrong_name, {**wrong_name, "index": 1}])
    report = runtime.probe_topology(
        RuntimeRequest(backend=TrainingBackend.CUDA),
        provider_request=provider,
    )
    assert report.disposition is TopologyDisposition.MISMATCH
    assert report.blockers == ("provider_device_name_mismatch",)


def test_topology_contract_rejects_duplicate_missing_and_noncontiguous_devices() -> None:
    first = AcceleratorDevice(TrainingBackend.CUDA, 0, "T4", 8_000, 16_000)
    duplicate = AcceleratorDevice(TrainingBackend.CUDA, 0, "T4", 8_000, 16_000)
    with pytest.raises(ValueError, match="unique, ordered and contiguous"):
        ObservedAcceleratorTopology(TrainingBackend.CUDA, (first, duplicate))

    skipped = AcceleratorDevice(TrainingBackend.CUDA, 2, "T4", 8_000, 16_000)
    with pytest.raises(ValueError, match="unique, ordered and contiguous"):
        ObservedAcceleratorTopology(TrainingBackend.CUDA, (first, skipped))


def test_single_gpu_preflight_never_pools_two_device_vram(tmp_path: Path) -> None:
    report = _runtime(tmp_path, [_device(0), _device(1)]).probe_topology(
        RuntimeRequest(backend=TrainingBackend.CUDA)
    )
    selection = evaluate_single_gpu_selection(
        report,
        ordinal=0,
        resources=ResourceRequest(vram_estimate_bytes=20_000),
    )
    assert selection.ready is False
    assert selection.device is not None
    assert selection.device.vram_total_bytes == 16_000
    assert "vram_budget_exceeded" in selection.blockers
    assert "aggregate_vram" not in json.dumps(selection.to_dict())


def test_single_gpu_selection_is_ordinal_specific_and_unknown_vram_blocks(tmp_path: Path) -> None:
    report = _runtime(
        tmp_path,
        [
            _device(0, free=2_000, total=16_000),
            _device(1, free=12_000, total=16_000),
        ],
    ).probe_topology(RuntimeRequest(backend=TrainingBackend.CUDA))
    first = evaluate_single_gpu_selection(
        report,
        ordinal=0,
        resources=ResourceRequest(vram_estimate_bytes=6_000),
    )
    second = evaluate_single_gpu_selection(
        report,
        ordinal=1,
        resources=ResourceRequest(vram_estimate_bytes=6_000),
    )
    assert first.ready is False
    assert first.blockers == ("vram_current_free_insufficient",)
    assert second.ready is True
    assert second.device is not None and second.device.index == 1
    assert first.topology_digest == second.topology_digest

    unknown = _runtime(tmp_path / "unknown", [_device(0, free=None, total=None)]).probe_topology(
        RuntimeRequest(backend=TrainingBackend.CUDA)
    )
    blocked = evaluate_single_gpu_selection(
        unknown,
        ordinal=0,
        resources=ResourceRequest(vram_estimate_bytes=1),
    )
    assert blocked.ready is False
    assert blocked.blockers == ("vram_budget_unknown",)


def test_probe_worker_observes_every_device_but_legacy_scalars_remain_device_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeTensor:
        def __matmul__(self, _other: object) -> "FakeTensor":
            return self

        def sum(self) -> "FakeTensor":
            return self

        def item(self) -> int:
            return 1

    class FakeCuda:
        def is_available(self) -> bool:
            return True

        def device_count(self) -> int:
            return 2

        def get_device_properties(self, index: int) -> object:
            return SimpleNamespace(name=f"NVIDIA Tesla T4 #{index}")

        def mem_get_info(self, index: int) -> tuple[int, int]:
            return ((9_000, 16_000), (7_000, 16_000))[index]

        def manual_seed_all(self, _seed: int) -> None:
            return None

    fake_torch = ModuleType("torch")
    fake_torch.version = SimpleNamespace(hip=None, cuda="12.fixture")  # type: ignore[attr-defined]
    fake_torch.cuda = FakeCuda()  # type: ignore[attr-defined]
    fake_torch.float32 = "float32"  # type: ignore[attr-defined]
    fake_torch.float16 = "float16"  # type: ignore[attr-defined]
    fake_torch.bfloat16 = "bfloat16"  # type: ignore[attr-defined]
    def fake_manual_seed(_seed: int) -> None:
        return None

    def fake_device(value: str) -> str:
        return value

    def fake_ones(*_args: object, **_kwargs: object) -> FakeTensor:
        return FakeTensor()

    fake_torch.manual_seed = fake_manual_seed  # type: ignore[attr-defined]
    fake_torch.device = fake_device  # type: ignore[attr-defined]
    fake_torch.ones = fake_ones  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    result = _base_result()
    _torch_probe(
        {
            "backend": "cuda",
            "dtype": "float16",
            "quantization": "none",
            "seeds": {"seed": 7},
        },
        result,
    )
    topology = result["topology"]
    assert isinstance(topology, dict)
    assert topology["device_count"] == 2
    assert [item["index"] for item in topology["devices"]] == [0, 1]  # type: ignore[index]
    assert result["vram_free_bytes"] == 9_000
    assert result["vram_total_bytes"] == 16_000


def test_cpu_topology_probe_is_unavailable_without_spawning_worker(tmp_path: Path) -> None:
    sandbox = FakeSandbox(_worker_topology([_device(0)]))
    runtime = TrainingRuntime(tmp_path, kill_switch=KillSwitch(), sandbox=sandbox)
    report = runtime.probe_topology(RuntimeRequest(backend=TrainingBackend.CPU))
    assert report.disposition is TopologyDisposition.UNAVAILABLE
    assert report.backend is TrainingBackend.CPU
    assert report.blockers == ("accelerator_backend_required",)
    assert sandbox.calls == 0


def test_topology_digest_is_observation_only_and_provider_digest_is_separate() -> None:
    observed = ObservedAcceleratorTopology(
        TrainingBackend.CUDA,
        (
            AcceleratorDevice(TrainingBackend.CUDA, 0, "T4", 8_000, 16_000),
            AcceleratorDevice(TrainingBackend.CUDA, 1, "T4", 8_000, 16_000),
        ),
    )
    first = AcceleratorTopologyReport(
        disposition=TopologyDisposition.READY,
        request_digest="a" * 64,
        backend=TrainingBackend.CUDA,
        provider_request=None,
        observed=observed,
    )
    provider = ProviderAcceleratorRequest(
        provider="kaggle",
        shape="NvidiaTeslaT4",
        expected_backend=TrainingBackend.CUDA,
        expected_device_count=2,
        expected_name_contains="T4",
    )
    second = AcceleratorTopologyReport(
        disposition=TopologyDisposition.READY,
        request_digest="a" * 64,
        backend=TrainingBackend.CUDA,
        provider_request=provider,
        observed=observed,
    )
    assert first.topology_digest == second.topology_digest
    assert first.digest != second.digest
    assert first.provider_request_digest is None
    assert second.provider_request_digest == provider.digest
