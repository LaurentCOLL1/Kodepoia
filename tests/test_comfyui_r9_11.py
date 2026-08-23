from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import pytest

import kodepoia.comfyui.service as service_module
from kodepoia.comfyui import (
    ComfyBoundaryError,
    ComfyEndpoint,
    ComfyFreeMemoryEvidence,
    ComfyGovernanceError,
    ComfyOutputCaptureService,
    ComfyOutputReference,
    ComfyProtocolError,
    ComfyService,
    ComfyUIClient,
)
from kodepoia.comfyui.packs import ProductionWorkflowFamily, ProductionWorkflowPackCatalog
from kodepoia.comfyui.service_cli import register_comfy_service_commands


def _request() -> dict[str, object]:
    return {
        "prompt": "bounded concept",
        "negative_prompt": "artifacts",
        "width": 512,
        "height": 512,
        "output_count": 1,
        "seed": 42,
        "steps": 24,
        "cfg": 7.0,
    }


def test_r911_public_service_and_client_surfaces_have_no_arbitrary_transport_or_process_escape() -> None:
    client_public = {name for name in dir(ComfyUIClient) if not name.startswith("_")}
    service_public = {name for name in dir(ComfyService) if not name.startswith("_")}
    forbidden = {
        "request",
        "get",
        "post",
        "urlopen",
        "execute",
        "spawn",
        "run_process",
        "install",
        "download",
        "install_model",
        "install_custom_node",
        "execute_graph",
    }
    assert not (client_public & forbidden)
    assert not (service_public & forbidden)
    assert {
        "status",
        "inventory",
        "workflows",
        "validate",
        "run",
        "run_status",
        "cancel",
        "vram",
        "free_memory",
        "evidence",
        "fork",
    } <= service_public


def test_r911_service_default_endpoint_is_fixed_loopback_and_non_loopback_is_rejected(tmp_path: Path) -> None:
    service = ComfyService(tmp_path / "project")
    assert service.client.endpoint.origin == "http://127.0.0.1:8188"
    with pytest.raises(ComfyBoundaryError):
        ComfyEndpoint.parse("http://192.168.1.2:8188")
    with pytest.raises(ComfyBoundaryError):
        ComfyEndpoint.parse("http://localhost:8188")


def test_r911_cli_rejects_an_arbitrary_endpoint_option() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    register_comfy_service_commands(commands)
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["comfy", "status", "--endpoint", "http://127.0.0.1:9999"])
    assert exc.value.code == 2


def test_r911_workflow_request_rejects_graph_url_command_and_install_injection() -> None:
    pack = ProductionWorkflowPackCatalog().get(ProductionWorkflowFamily.CONCEPT)
    for field, value in (
        ("graph", {"99": {"class_type": "Hostile"}}),
        ("url", "https://example.invalid/prompt"),
        ("command", "calc.exe"),
        ("model_download", "https://example.invalid/model.safetensors"),
        ("custom_node_install", "hostile-node"),
    ):
        hostile = _request()
        hostile[field] = value
        with pytest.raises(ComfyGovernanceError, match="fields are invalid"):
            pack.validate_request(hostile)


def test_r911_model_selection_surface_is_single_governed_checkpoint_token() -> None:
    assert ComfyService._selections(None) == {}
    assert ComfyService._selections("models/a.safetensors") == {
        "checkpoint": "models/a.safetensors"
    }


def test_r911_cross_run_output_reference_fails_closed() -> None:
    manifest = SimpleNamespace(prompt_id="kp_" + "a" * 32)
    foreign = ComfyOutputReference(
        "kp_" + "b" * 32,
        "7",
        0,
        "foreign.png",
        "",
        "output",
    )
    with pytest.raises(ComfyProtocolError, match="different prompt"):
        ComfyOutputCaptureService._verify_reference(manifest, foreign)


def test_r911_free_memory_remains_ack_only_and_bound_to_known_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    class Lifecycle:
        def __init__(self) -> None:
            self.calls: list[tuple[tuple[str, ...], bool, bool]] = []

        def request_free_memory(
            self,
            *,
            known_run_ids: tuple[str, ...],
            unload_models: bool,
            free_memory: bool,
        ) -> ComfyFreeMemoryEvidence:
            self.calls.append((known_run_ids, unload_models, free_memory))
            return ComfyFreeMemoryEvidence(
                endpoint="http://127.0.0.1:8188",
                unload_models=unload_models,
                free_memory=free_memory,
                request_digest_sha256="a" * 64,
                before_system_digest_sha256="b" * 64,
                after_system_digest_sha256="c" * 64,
                request_acknowledged=True,
                reclaimed_bytes=None,
            )

    service = object.__new__(ComfyService)
    lifecycle = Lifecycle()
    service.lifecycle = lifecycle
    monkeypatch.setattr(ComfyService, "_known_run_ids", lambda self: ("run_a", "run_b"))
    result = service.free_memory()
    assert lifecycle.calls == [("run_a", "run_b"), True, True]
    assert result["state"] == "requested"
    assert result["evidence"]["reclaimed_bytes"] is None


def test_r911_known_run_enumeration_is_deterministically_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Store:
        def __init__(self, root: Path) -> None:
            self.root = root

        def load(self, run_id: str) -> object:
            return SimpleNamespace(run_id=run_id)

    service = object.__new__(ComfyService)
    service.run_store = Store(tmp_path)
    monkeypatch.setattr(service_module, "_MAX_RUNS_IN_EVIDENCE", 4)

    for index in (3, 1, 4, 2):
        (tmp_path / f"run_{index}.json").write_text("{}", encoding="utf-8")
    assert service._known_run_ids() == ("run_1", "run_2", "run_3", "run_4")

    (tmp_path / "run_5.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ComfyProtocolError, match="exceeds the accepted bound"):
        service._known_run_ids()


def test_r911_vram_reserve_and_headroom_cannot_escape_service_bounds() -> None:
    for value in (-1, 65_537, True):
        with pytest.raises(ValueError, match="between 0 and 65536"):
            ComfyService._bounded_mib(value, "reserve_mib")
    assert ComfyService._bounded_mib(0, "headroom_mib") == 0
    assert ComfyService._bounded_mib(65_536, "headroom_mib") == 65_536
