from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.blender3d.errors import BlenderBoundaryError
from kodepoia.blender3d.service import (
    BlenderCancellation,
    BlenderService,
    BlenderUXState,
)


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "docs" / "roadmap").mkdir(parents=True)
    return root


def _write_evidence(root: Path, name: str = "R10_10_LOCAL_ACCEPTANCE.json") -> None:
    payload = {
        "schema": "kodepoia.r10.gltf_local_acceptance",
        "version": 1,
        "source_sha": "8" * 40,
        "status": "pass",
        "blockers": [],
        "blender": {
            "version": "5.2.0 LTS",
            "background": True,
            "online_access": False,
        },
        "godot": {
            "version": {
                "raw": "4.7.2.stable",
                "major": 4,
                "minor": 7,
                "patch": 2,
                "compatible_47": True,
            }
        },
    }
    (root / "docs" / "roadmap" / name).write_text(
        json.dumps(payload, separators=(",", ":")),
        encoding="utf-8",
    )


def test_status_capabilities_and_api_inventory_are_explicit(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _write_evidence(root)
    service = BlenderService(root)

    status = service.status()
    assert status.state is BlenderUXState.READY
    assert status.payload["manual_intervention"] == "NONE"
    runtime = status.payload["runtime_evidence"]
    assert runtime["blender_version"] == "5.2.0 LTS"
    assert runtime["godot_version"] == "4.7.2.stable"

    capabilities = service.capabilities()
    assert capabilities.state is BlenderUXState.READY
    inventory = capabilities.payload["api_inventory"]
    assert inventory["identifiers_only"] is True
    assert inventory["raw_python_surface"] is False
    assert inventory["raw_process_surface"] is False
    assert inventory["raw_path_surface"] is False
    assert set(inventory["operations"]) == {
        "status",
        "capabilities",
        "inspect",
        "validate_geometry",
        "qa",
        "rig",
        "animation",
        "lod",
        "export",
        "evidence",
    }


def test_geometry_validation_resolves_only_managed_recipe_ids(tmp_path: Path) -> None:
    root = _root(tmp_path)
    service = BlenderService(root)
    service.recipe_root.mkdir(parents=True)
    recipe = {
        "version": 1,
        "recipe_id": "demo.cube",
        "units": "METERS",
        "forward_axis": "-Z",
        "up_axis": "Y",
        "steps": [
            {"operation": "reset_scene", "params": {}},
            {
                "operation": "create_primitive",
                "params": {
                    "object_id": "cube",
                    "primitive": "cube",
                    "display_name": "Cube",
                },
            },
        ],
    }
    (service.recipe_root / "demo.cube.json").write_text(
        json.dumps(recipe),
        encoding="utf-8",
    )

    result = service.validate_geometry("demo.cube")
    assert result.state is BlenderUXState.READY
    assert result.payload["recipe_id"] == "demo.cube"
    assert result.payload["steps"] == 2
    assert len(result.payload["digest"]) == 64

    with pytest.raises(BlenderBoundaryError):
        service.validate_geometry("../escape")
    with pytest.raises(BlenderBoundaryError):
        service.validate_geometry("C:\\Windows\\System32")


def test_reports_are_kind_and_identifier_bound(tmp_path: Path) -> None:
    root = _root(tmp_path)
    service = BlenderService(root)
    report_dir = service.report_root / "qa"
    report_dir.mkdir(parents=True)
    (report_dir / "mesh.demo.json").write_text(
        json.dumps({"status": "pass", "passed_rules": ["non_manifold"]}),
        encoding="utf-8",
    )

    result = service.qa("mesh.demo")
    assert result.state is BlenderUXState.READY
    assert result.payload["kind"] == "qa"
    assert result.payload["report"]["status"] == "pass"

    missing = service.rig("mesh.demo")
    assert missing.state is BlenderUXState.MISSING
    assert missing.reason == "managed_report_missing"

    with pytest.raises(BlenderBoundaryError):
        service.inspect("process", "mesh.demo")


def test_allowlisted_evidence_and_cancellation_are_fail_closed(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _write_evidence(root)
    service = BlenderService(root)

    accepted = service.evidence("r10.10")
    assert accepted.state is BlenderUXState.READY
    assert accepted.payload["evidence"]["status"] == "pass"

    with pytest.raises(BlenderBoundaryError):
        service.evidence("r10.99")

    cancellation = BlenderCancellation()
    cancellation.cancel()
    cancelled = service.capabilities(cancellation=cancellation)
    assert cancelled.state is BlenderUXState.CANCELLED
    assert cancelled.reason == "cancelled"


def test_managed_json_is_bounded_and_malformed_content_never_becomes_ready(tmp_path: Path) -> None:
    root = _root(tmp_path)
    service = BlenderService(root)
    report_dir = service.report_root / "export"
    report_dir.mkdir(parents=True)
    (report_dir / "broken.json").write_text("{", encoding="utf-8")
    with pytest.raises(BlenderBoundaryError):
        service.export("broken")


def test_service_source_has_no_runtime_execution_or_blender_operator_surface() -> None:
    import inspect

    import kodepoia.blender3d.service as module

    source = inspect.getsource(module)
    forbidden = (
        "import subprocess",
        "from subprocess",
        "ProcessSandbox",
        "bpy.",
        "os.system",
        "shell=True",
        "eval(",
        "exec(",
        "--python",
        "--expr",
    )
    for token in forbidden:
        assert token not in source
