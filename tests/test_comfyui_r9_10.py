from __future__ import annotations

import inspect
from pathlib import Path

from kodepoia.cli import build_parser
from kodepoia.comfyui.contracts import ComfyCapabilityState
from kodepoia.comfyui.inventory import ComfyCapabilitySnapshot
from kodepoia.comfyui.packs import ProductionWorkflowFamily
from kodepoia.comfyui.serialization import canonical_sha256
from kodepoia.comfyui.service import ComfyService


def _unavailable_snapshot() -> ComfyCapabilitySnapshot:
    payload = {
        "endpoint": "http://127.0.0.1:8188",
        "comfyui_version": None,
        "python_version": None,
        "system_digest_sha256": None,
        "feature_digest_sha256": None,
        "nodes": [],
        "models": [],
        "unavailable": ["fixture"],
    }
    return ComfyCapabilitySnapshot(
        state=ComfyCapabilityState.UNAVAILABLE,
        endpoint=payload["endpoint"],
        captured_at="2026-08-23T17:00:00Z",
        comfyui_version=None,
        python_version=None,
        system_digest_sha256=None,
        feature_digest_sha256=None,
        nodes=(),
        models=(),
        unavailable=("fixture",),
        identity_sha256=canonical_sha256(payload),
    )


def test_comfy_service_exposes_only_accepted_r9_9_pack_families(tmp_path: Path) -> None:
    service = ComfyService(tmp_path)
    result = service.workflows(refresh_inventory=False)
    assert [item["family"] for item in result["packs"]] == [item.value for item in ProductionWorkflowFamily]
    assert all(item["compatibility"]["state"] == "unknown" for item in result["packs"])


def test_comfy_service_preserves_explicit_unavailable_capability_state(tmp_path: Path) -> None:
    service = ComfyService(tmp_path)
    snapshot = _unavailable_snapshot()
    service.snapshot_store.save("current", snapshot)
    result = service.validate(ProductionWorkflowFamily.CONCEPT, refresh_inventory=False)
    assert result["compatibility"]["state"] == "unavailable"
    assert result["compatibility"]["capability_identity_sha256"] == snapshot.identity_sha256


def test_r9_10_cli_registers_complete_governed_surface() -> None:
    parser = build_parser()
    cases = (
        ["comfy", "status"],
        ["comfy", "inventory", "--cached"],
        ["comfy", "workflows"],
        ["comfy", "validate", "concept", "--cached"],
        [
            "comfy", "run", "concept",
            "--prompt", "concept art",
            "--negative-prompt", "artifacts",
        ],
        ["comfy", "run-status", "run_" + "0" * 32, "--no-reconcile"],
        ["comfy", "cancel", "run_" + "0" * 32],
        ["comfy", "vram", "--family", "concept"],
        ["comfy", "free-memory"],
        ["comfy", "evidence", "run_" + "0" * 32],
    )
    for argv in cases:
        args = parser.parse_args(argv)
        assert callable(args.func)


def test_r9_10_cli_has_no_arbitrary_endpoint_graph_process_or_installer_surface() -> None:
    import kodepoia.comfyui.service_cli as service_cli

    source = inspect.getsource(service_cli)
    forbidden = (
        "--endpoint",
        "--url",
        "--workflow-file",
        "--workflow-root",
        "subprocess",
        "ProcessSandbox",
        "model-install",
        "model-download",
        "graph-json",
    )
    assert not any(item in source for item in forbidden)


def test_comfy_panel_accesses_comfyui_only_through_service_facade() -> None:
    import kodepoia.kodestudio.comfy_panel as comfy_panel

    source = inspect.getsource(comfy_panel)
    forbidden = (
        "from kodepoia.comfyui.client import",
        "from kodepoia.comfyui.transport import",
        "ComfyUIClient(",
        "_FixedHTTPTransport",
        "import requests",
        "import socket",
        "import subprocess",
    )
    assert not any(item in source for item in forbidden)
    assert "ComfyService" in source
    assert "QRunnable" in source
    assert "QThreadPool" in source
