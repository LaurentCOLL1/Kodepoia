from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from kodepoia.core.kill_switch import KillSwitch
from kodepoia.core.sandbox import SandboxResult
from kodepoia.tuning import (
    CapabilityState,
    DTypeName,
    QuantizationMode,
    ResourceRequest,
    RuntimeDisposition,
    RuntimeRequest,
    TrainingBackend,
    TrainingRuntime,
)
from kodepoia.tuning.contracts import TuningRuntimeError
from kodepoia.tuning.runtime import HostResources, redact_runtime_text


class FixedResources:
    def __init__(self, disk: int | None = 10_000, ram: int | None = 10_000) -> None:
        self.value = HostResources(disk, ram)

    def sample(self, _root: Path) -> HostResources:
        return self.value


class FakeSandbox:
    def __init__(self, probe: dict[str, object], model: dict[str, object] | None = None) -> None:
        self.probe_payload = probe
        self.model_payload = model or probe
        self.calls: list[tuple[list[str], dict[str, object]]] = []
        self.stderr = ""
        self.timed_out = False
        self.cancelled = False
        self.returncode = 0

    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        assert cwd is not None
        config = json.loads((cwd / argv[-1]).read_text(encoding="utf-8"))
        self.calls.append((list(argv), config))
        payload = self.model_payload if config["action"] == "model_load" else self.probe_payload
        return SandboxResult(
            self.returncode,
            json.dumps(payload),
            self.stderr,
            timed_out=self.timed_out,
            cancelled=self.cancelled,
        )


def worker_payload(
    *,
    backend: str = "cpu",
    capability: str = "supported",
    dtype: bool | None = True,
    four_bit: bool | None = None,
    free: int | None = None,
    total: int | None = None,
    model_load: str | None = None,
) -> dict[str, object]:
    return {
        "backend": backend,
        "backend_capability": capability,
        "device": {"backend_type": backend, "index": 0, "name": "fixture-device"},
        "dtype_supported": dtype,
        "four_bit_supported": four_bit,
        "model_load": model_load,
        "packages": {
            "bitsandbytes": "0.fixture" if four_bit is not None else None,
            "torch": "2.fixture",
            "transformers": "5.fixture",
        },
        "python_version": "3.12.fixture",
        "seed_applied": True,
        "torch_backend_version": backend,
        "vram_free_bytes": free,
        "vram_total_bytes": total,
    }


def test_cpu_supported_and_deterministic(tmp_path: Path) -> None:
    fake = FakeSandbox(worker_payload())
    request = RuntimeRequest()
    runtime = TrainingRuntime(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=fake,
        resource_probe=FixedResources(),
    )
    first = runtime.probe(request)
    second = runtime.probe(request)
    assert first.disposition is RuntimeDisposition.READY
    assert first.backend_capability is CapabilityState.SUPPORTED
    assert first.digest == second.digest
    assert len(fake.calls) == 2


def test_accelerator_vram_budget_blocks_before_model_load(tmp_path: Path) -> None:
    fake = FakeSandbox(worker_payload(backend="cuda", free=500, total=1000))
    request = RuntimeRequest(
        backend=TrainingBackend.CUDA,
        dtype=DTypeName.FLOAT16,
        resources=ResourceRequest(vram_estimate_bytes=700, vram_reserve_bytes=100),
        model_ref="org/model",
        model_load_dry_run=True,
    )
    report = TrainingRuntime(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=fake,
        resource_probe=FixedResources(),
    ).probe(request)
    assert report.disposition is RuntimeDisposition.BUDGET_BLOCKED
    assert "vram_current_free_insufficient" in report.blockers
    assert len(fake.calls) == 1


def test_host_budget_blocks_without_subprocess(tmp_path: Path) -> None:
    fake = FakeSandbox(worker_payload())
    request = RuntimeRequest(resources=ResourceRequest(disk_required_bytes=101, ram_required_bytes=101))
    report = TrainingRuntime(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=fake,
        resource_probe=FixedResources(100, 100),
    ).probe(request)
    assert report.disposition is RuntimeDisposition.BUDGET_BLOCKED
    assert set(report.blockers) == {"ram_budget_exceeded", "storage_budget_exceeded"}
    assert fake.calls == []


def test_unknown_requested_host_budget_blocks_without_subprocess(tmp_path: Path) -> None:
    fake = FakeSandbox(worker_payload())
    request = RuntimeRequest(resources=ResourceRequest(disk_required_bytes=1, ram_required_bytes=1))
    report = TrainingRuntime(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=fake,
        resource_probe=FixedResources(None, None),
    ).probe(request)
    assert report.disposition is RuntimeDisposition.BUDGET_BLOCKED
    assert set(report.blockers) == {"ram_budget_unknown", "storage_budget_unknown"}
    assert fake.calls == []


def test_requested_quantization_requires_actual_four_bit_operation(tmp_path: Path) -> None:
    fake = FakeSandbox(worker_payload(backend="rocm", free=900, total=1000, four_bit=False))
    request = RuntimeRequest(
        backend=TrainingBackend.ROCM,
        dtype=DTypeName.BFLOAT16,
        quantization=QuantizationMode.BNB_NF4,
        resources=ResourceRequest(vram_estimate_bytes=100),
    )
    report = TrainingRuntime(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=fake,
        resource_probe=FixedResources(),
    ).probe(request)
    assert report.disposition is RuntimeDisposition.UNSUPPORTED
    assert report.backend_capability is CapabilityState.SUPPORTED
    assert "four_bit_operation_unsupported" in report.blockers


def test_cpu_nf4_support_is_decided_by_actual_operation_probe(tmp_path: Path) -> None:
    fake = FakeSandbox(worker_payload(backend="cpu", four_bit=True))
    request = RuntimeRequest(
        backend=TrainingBackend.CPU,
        quantization=QuantizationMode.BNB_NF4,
    )
    report = TrainingRuntime(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=fake,
        resource_probe=FixedResources(),
    ).probe(request)
    assert report.disposition is RuntimeDisposition.READY
    assert report.backend_capability is CapabilityState.SUPPORTED
    assert report.four_bit_supported is True
    assert len(fake.calls) == 1


def test_model_load_is_second_local_only_worker_phase(tmp_path: Path) -> None:
    probe = worker_payload(backend="cuda", free=900, total=1000)
    model = worker_payload(backend="cuda", free=900, total=1000, model_load="supported")
    fake = FakeSandbox(probe, model)
    request = RuntimeRequest(
        backend=TrainingBackend.CUDA,
        dtype=DTypeName.FLOAT16,
        resources=ResourceRequest(vram_estimate_bytes=100),
        model_ref="org/model",
        model_revision="main",
        tokenizer_ref="org/tokenizer",
        model_load_dry_run=True,
    )
    report = TrainingRuntime(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=fake,
        resource_probe=FixedResources(),
    ).probe(request)
    assert report.disposition is RuntimeDisposition.READY
    assert report.model_load is CapabilityState.SUPPORTED
    assert [call[1]["action"] for call in fake.calls] == ["probe", "model_load"]
    for argv, _config in fake.calls:
        joined = " ".join(argv)
        assert "org/model" not in joined
        assert "org/tokenizer" not in joined
        assert "main" not in joined


def test_timeout_and_cancellation_are_terminal(tmp_path: Path) -> None:
    fake = FakeSandbox(worker_payload())
    fake.timed_out = True
    runtime = TrainingRuntime(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=fake,
        resource_probe=FixedResources(),
    )
    assert runtime.probe(RuntimeRequest()).disposition is RuntimeDisposition.TIMED_OUT

    fake.timed_out = False
    fake.cancelled = True
    assert runtime.probe(RuntimeRequest()).disposition is RuntimeDisposition.CANCELLED


def test_runtime_redacts_stderr_and_private_paths(tmp_path: Path) -> None:
    fake = FakeSandbox(worker_payload())
    fake.stderr = "api_key=supersecret user@example.com /home/alice/private/model"
    report = TrainingRuntime(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=fake,
        resource_probe=FixedResources(),
    ).probe(RuntimeRequest())
    assert "supersecret" not in report.stderr
    assert "user@example.com" not in report.stderr
    assert "/home/alice" not in report.stderr
    assert "<redacted>" in report.stderr
    assert "supersecret" not in json.dumps(report.to_dict())


def test_worker_failure_does_not_echo_unredacted_stdout(tmp_path: Path) -> None:
    fake = FakeSandbox(worker_payload())
    fake.returncode = 1
    fake.stderr = "password=hunter2"
    report = TrainingRuntime(
        tmp_path,
        kill_switch=KillSwitch(),
        sandbox=fake,
        resource_probe=FixedResources(),
    ).probe(RuntimeRequest())
    assert report.disposition is RuntimeDisposition.FAILED
    assert "hunter2" not in report.stderr


def test_contract_allows_cpu_nf4_probe_and_rejects_unsafe_refs() -> None:
    request = RuntimeRequest(
        backend=TrainingBackend.CPU,
        quantization=QuantizationMode.BNB_NF4,
    )
    assert request.quantization is QuantizationMode.BNB_NF4
    with pytest.raises(TuningRuntimeError):
        RuntimeRequest(model_ref="../outside")


def test_redactor_is_bounded() -> None:
    assert len(redact_runtime_text("x" * 20_000)) == 8192


def test_core_tuning_import_does_not_load_ml_packages() -> None:
    code = (
        "import sys; import kodepoia.tuning; "
        "bad={'torch','transformers','bitsandbytes','peft','trl'} & set(sys.modules); "
        "raise SystemExit(1 if bad else 0)"
    )
    completed = subprocess.run([sys.executable, "-c", code], check=False)
    assert completed.returncode == 0