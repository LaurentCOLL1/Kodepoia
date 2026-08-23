from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from kodepoia.cli import build_parser
from kodepoia.comfyui.boundary import ComfyEndpoint
from kodepoia.comfyui.contracts import ComfyCapabilityState
from kodepoia.comfyui.errors import ComfyGovernanceError
from kodepoia.comfyui.inventory import ComfyCapabilitySnapshot, ComfyModelInventory, normalize_node_inventory
from kodepoia.comfyui.packs import ProductionWorkflowFamily, WorkflowPackCompatibilityState
from kodepoia.comfyui.resources import (
    ComfyDeviceMemory,
    ComfyVramSnapshot,
    GpuAdmissionDecision,
    GpuAdmissionPolicy,
    GpuResourceProfile,
)
from kodepoia.comfyui.serialization import canonical_sha256
from kodepoia.comfyui.service import ComfyService


class _NoNetworkClient:
    def __init__(self) -> None:
        self.endpoint = ComfyEndpoint.parse("http://127.0.0.1:8188")

    def queue(self):
        return SimpleNamespace(running_prompt_ids=("kp_a",), pending_prompt_ids=("kp_b",))


class _StaticInventory:
    def __init__(self, snapshot: ComfyCapabilitySnapshot) -> None:
        self.snapshot = snapshot

    def capture(self) -> ComfyCapabilitySnapshot:
        return self.snapshot


class _StaticTelemetry:
    def __init__(self, snapshot: ComfyVramSnapshot) -> None:
        self.snapshot = snapshot

    def sample(self) -> ComfyVramSnapshot:
        return self.snapshot


class _StaticResources:
    def __init__(self, decision) -> None:
        self.decision = decision
        self.cleanup_called = False

    def evaluate(self, _profile):
        return _vram_snapshot(), self.decision

    def admit_with_cleanup(self, _profile):
        self.cleanup_called = True
        raise AssertionError("cleanup must not run without explicit authorization")


def _snapshot(*, state: ComfyCapabilityState = ComfyCapabilityState.CURRENT) -> ComfyCapabilitySnapshot:
    object_info = {
        "CheckpointLoaderSimple": {
            "input": {"required": {"ckpt_name": [["models/classic-a.safetensors", "models/classic-b.safetensors"]]}},
            "output": ["MODEL", "CLIP", "VAE"],
            "output_is_list": [False, False, False],
            "category": "loaders",
        },
        "CLIPTextEncode": {
            "input": {"required": {"text": ["STRING"], "clip": ["CLIP"]}},
            "output": ["CONDITIONING"],
            "output_is_list": [False],
            "category": "conditioning",
        },
        "EmptyLatentImage": {
            "input": {
                "required": {
                    "width": ["INT", {"min": 16, "max": 4096, "step": 8}],
                    "height": ["INT", {"min": 16, "max": 4096, "step": 8}],
                    "batch_size": ["INT", {"min": 1, "max": 64, "step": 1}],
                }
            },
            "output": ["LATENT"],
            "output_is_list": [False],
            "category": "latent",
        },
        "KSampler": {
            "input": {
                "required": {
                    "model": ["MODEL"],
                    "seed": ["INT", {"min": 0, "max": 18446744073709551615}],
                    "steps": ["INT", {"min": 1, "max": 1000}],
                    "cfg": ["FLOAT", {"min": 0.0, "max": 100.0}],
                    "sampler_name": [["euler", "dpmpp_2m"]],
                    "scheduler": [["normal", "karras"]],
                    "positive": ["CONDITIONING"],
                    "negative": ["CONDITIONING"],
                    "latent_image": ["LATENT"],
                    "denoise": ["FLOAT", {"min": 0.0, "max": 1.0}],
                }
            },
            "output": ["LATENT"],
            "output_is_list": [False],
            "category": "sampling",
        },
        "VAEDecode": {
            "input": {"required": {"samples": ["LATENT"], "vae": ["VAE"]}},
            "output": ["IMAGE"],
            "output_is_list": [False],
            "category": "latent",
        },
        "SaveImage": {
            "input": {"required": {"images": ["IMAGE"], "filename_prefix": ["STRING"]}},
            "output": [],
            "output_is_list": [],
            "category": "image",
            "output_node": True,
        },
    }
    nodes = normalize_node_inventory(object_info)
    models = (
        ComfyModelInventory(
            "checkpoints",
            ("models/classic-a.safetensors", "models/classic-b.safetensors"),
            canonical_sha256(
                {
                    "model_type": "checkpoints",
                    "tokens": ["models/classic-a.safetensors", "models/classic-b.safetensors"],
                }
            ),
        ),
    )
    system_digest = canonical_sha256({"system": "r9.10"})
    feature_digest = canonical_sha256({"features": "r9.10"})
    identity = {
        "endpoint": "http://127.0.0.1:8188",
        "comfyui_version": "0.test-r9.10",
        "python_version": "3.12.test",
        "system_digest_sha256": system_digest,
        "feature_digest_sha256": feature_digest,
        "nodes": [item.canonical() for item in nodes],
        "models": [item.canonical() for item in models],
        "unavailable": [],
    }
    return ComfyCapabilitySnapshot(
        state=state,
        endpoint="http://127.0.0.1:8188",
        captured_at="2026-08-23T14:00:00Z",
        comfyui_version="0.test-r9.10",
        python_version="3.12.test",
        system_digest_sha256=system_digest,
        feature_digest_sha256=feature_digest,
        nodes=nodes,
        models=models,
        unavailable=(),
        identity_sha256=canonical_sha256(identity),
    )


def _vram_snapshot(*, free_mib: int = 10_000, total_mib: int = 12_000) -> ComfyVramSnapshot:
    device = ComfyDeviceMemory(
        name="fixture-gpu",
        backend_type="fixture",
        index=0,
        vram_total_bytes=total_mib * 1024 * 1024,
        vram_free_bytes=free_mib * 1024 * 1024,
        torch_vram_total_bytes=None,
        torch_vram_free_bytes=None,
    )
    payload = {
        "endpoint": "http://127.0.0.1:8188",
        "comfyui_version": "0.test-r9.10",
        "python_version": "3.12.test",
        "devices": [device.canonical()],
    }
    return ComfyVramSnapshot(
        endpoint=payload["endpoint"],
        comfyui_version=payload["comfyui_version"],
        python_version=payload["python_version"],
        devices=(device,),
        digest_sha256=canonical_sha256(payload),
    )


def _request() -> dict[str, object]:
    return {
        "prompt": "governed concept",
        "negative_prompt": "artifacts",
        "width": 512,
        "height": 512,
        "output_count": 1,
        "seed": 42,
        "steps": 20,
        "cfg": 7.0,
    }


def _service(tmp_path: Path) -> ComfyService:
    service = ComfyService(tmp_path, client=_NoNetworkClient())
    service.inventory = _StaticInventory(_snapshot())
    service.telemetry = _StaticTelemetry(_vram_snapshot())
    return service


def test_service_is_single_typed_facade_without_raw_graph_entrypoint(tmp_path: Path) -> None:
    service = _service(tmp_path)
    try:
        families = service.workflow_families()
        assert tuple(item["family"] for item in families) == tuple(item.value for item in ProductionWorkflowFamily)
        assert not hasattr(service, "execute_graph")
        assert not hasattr(service, "run_json")
        parameters = inspect.signature(service.run_workflow).parameters
        assert "graph" not in parameters
        assert "workflow_json" not in parameters
        assert "endpoint" not in parameters
    finally:
        service.close()


def test_status_and_workflow_validation_expose_explicit_current_and_blocked_states(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.client = _NoNetworkClient()
    service.telemetry = _StaticTelemetry(_vram_snapshot())
    try:
        status = service.status()
        assert status.ready is True
        assert status.capability_state == "current"
        assert status.queue_running == 1
        assert status.queue_pending == 1
        assert status.vram_free_bytes == 10_000 * 1024 * 1024

        blocked = service.validate_workflow(ProductionWorkflowFamily.CONCEPT)
        assert blocked.state is WorkflowPackCompatibilityState.BLOCKED
        compatible = service.validate_workflow(
            ProductionWorkflowFamily.CONCEPT,
            model_selections={"checkpoint": "models/classic-a.safetensors"},
        )
        assert compatible.state is WorkflowPackCompatibilityState.COMPATIBLE
    finally:
        service.close()


def test_free_memory_requires_explicit_confirmation_before_any_side_effect(tmp_path: Path) -> None:
    service = _service(tmp_path)
    called = False

    def forbidden():
        nonlocal called
        called = True
        raise AssertionError("must not be called")

    service.lifecycle.request_free_memory = forbidden  # type: ignore[method-assign]
    try:
        with pytest.raises(ComfyGovernanceError, match="explicit confirmation"):
            service.free_memory(confirmed=False)
        assert called is False
    finally:
        service.close()


def test_deferred_gpu_admission_does_not_cleanup_or_submit_without_explicit_authorization(tmp_path: Path) -> None:
    service = _service(tmp_path)
    profile = GpuResourceProfile(
        estimate_bytes=8 * 1024**3,
        reserve_bytes=512 * 1024**2,
        headroom_bytes=512 * 1024**2,
    )
    decision = GpuAdmissionPolicy().decide(_vram_snapshot(free_mib=4_000), profile)
    assert decision.decision is GpuAdmissionDecision.DEFER
    resources = _StaticResources(decision)
    service.resources = resources  # type: ignore[assignment]

    called = False

    def forbidden_prepare(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("submission preparation must not happen")

    service.execution.prepare = forbidden_prepare  # type: ignore[method-assign]
    try:
        with pytest.raises(ComfyGovernanceError, match="GPU admission is defer"):
            service.run_workflow(
                ProductionWorkflowFamily.CONCEPT,
                parameters=_request(),
                model_selections={"checkpoint": "models/classic-a.safetensors"},
                allow_memory_cleanup=False,
            )
        assert resources.cleanup_called is False
        assert called is False
    finally:
        service.close()


def test_stale_snapshot_fails_workflow_validation_explicitly(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.inventory = _StaticInventory(_snapshot(state=ComfyCapabilityState.STALE))
    try:
        report = service.validate_workflow(
            ProductionWorkflowFamily.CONCEPT,
            model_selections={"checkpoint": "models/classic-a.safetensors"},
        )
        assert report.state is WorkflowPackCompatibilityState.STALE
    finally:
        service.close()


def test_r9_10_cli_has_typed_commands_and_rejects_raw_workflow_json() -> None:
    parser = build_parser()
    args = parser.parse_args(["comfy-workflow-list"])
    assert callable(args.func)
    args = parser.parse_args(
        [
            "comfy-workflow-run",
            "--family",
            "concept",
            "--model-checkpoint",
            "models/a.safetensors",
            "--prompt",
            "x",
            "--negative-prompt",
            "y",
            "--width",
            "512",
            "--height",
            "512",
            "--seed",
            "1",
        ]
    )
    assert args.family == "concept"
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "comfy-workflow-run",
                "--family",
                "concept",
                "--model-checkpoint",
                "models/a.safetensors",
                "--prompt",
                "x",
                "--negative-prompt",
                "y",
                "--width",
                "512",
                "--height",
                "512",
                "--seed",
                "1",
                "--workflow-json",
                "{}",
            ]
        )
