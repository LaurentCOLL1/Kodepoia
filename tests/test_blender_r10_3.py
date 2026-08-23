from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.blender3d import BlenderExecutableBoundary
from kodepoia.blender3d.geometry_bootstrap import GEOMETRY_BOOTSTRAP_SOURCE
from kodepoia.blender3d.geometry_contracts import GeometryRecipe
from kodepoia.blender3d.geometry_runner import GeometryRunner
from kodepoia.blender3d.runner import BlenderRunner, RunnerProcessResult
from kodepoia.core.sandbox import ProcessSandbox
from kodepoia.blender3d.errors import BlenderBoundaryError

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "b" * 40


def recipe_payload() -> dict[str, object]:
    return {
        "version": 1,
        "recipe_id": "fixture.cube",
        "units": "METERS",
        "forward_axis": "-Z",
        "up_axis": "Y",
        "steps": [
            {"operation": "reset_scene", "params": {}},
            {"operation": "create_primitive", "params": {"object_id": "cube", "primitive": "cube", "display_name": "Cube Fixture"}},
            {"operation": "transform", "params": {"object_id": "cube", "location": [1, 2, 3], "scale": [2, 2, 2]}},
            {"operation": "apply_transform", "params": {"object_id": "cube", "location": False, "rotation": False, "scale": True}},
            {"operation": "triangulate", "params": {"object_id": "cube", "quad_method": "FIXED", "ngon_method": "EAR_CLIP"}},
            {"operation": "recalculate_normals", "params": {"object_id": "cube"}},
            {"operation": "set_origin", "params": {"object_id": "cube", "mode": "GEOMETRY"}},
        ],
    }


def test_r10_3_recipe_digest_is_stable_and_schema_valid() -> None:
    first = GeometryRecipe.from_dict(recipe_payload())
    second = GeometryRecipe.from_dict(json.loads(json.dumps(recipe_payload())))
    assert first.digest == second.digest
    assert len(first.digest) == 64
    schema = json.loads((ROOT / "schemas/r10-geometry-recipe-v1.schema.json").read_text())
    Draft202012Validator(schema).validate(first.to_dict())


def test_r10_3_rejects_unknown_operation_and_undeclared_object() -> None:
    bad_operation = recipe_payload()
    bad_operation["steps"] = [{"operation": "python_expr", "params": {}}]
    with pytest.raises(BlenderBoundaryError, match="Unsupported"):
        GeometryRecipe.from_dict(bad_operation)

    bad_reference = recipe_payload()
    bad_reference["steps"] = [
        {"operation": "reset_scene", "params": {}},
        {"operation": "transform", "params": {"object_id": "missing", "location": [0, 0, 0]}},
    ]
    with pytest.raises(BlenderBoundaryError, match="undeclared"):
        GeometryRecipe.from_dict(bad_reference)


def test_r10_3_rejects_modifier_escape_and_invalid_scale() -> None:
    bad_modifier = recipe_payload()
    bad_modifier["steps"] = list(bad_modifier["steps"]) + [
        {"operation": "add_modifier", "params": {"object_id": "cube", "name": "evil", "modifier": "geometry_nodes", "settings": {}}}
    ]
    with pytest.raises(BlenderBoundaryError, match="allowlisted"):
        GeometryRecipe.from_dict(bad_modifier)

    bad_scale = recipe_payload()
    bad_scale["steps"] = [
        {"operation": "reset_scene", "params": {}},
        {"operation": "create_primitive", "params": {"object_id": "cube", "primitive": "cube", "display_name": "Cube"}},
        {"operation": "transform", "params": {"object_id": "cube", "scale": [1, 0, 1]}},
    ]
    with pytest.raises(BlenderBoundaryError, match="scale"):
        GeometryRecipe.from_dict(bad_scale)


def test_r10_3_join_and_separate_identity_rules() -> None:
    joined = {
        "version": 1,
        "recipe_id": "join.fixture",
        "units": "METERS",
        "forward_axis": "-Z",
        "up_axis": "Y",
        "steps": [
            {"operation": "reset_scene", "params": {}},
            {"operation": "create_primitive", "params": {"object_id": "a", "primitive": "cube", "display_name": "A"}},
            {"operation": "create_primitive", "params": {"object_id": "b", "primitive": "cube", "display_name": "B"}},
            {"operation": "join", "params": {"object_id": "a", "sources": ["b"]}},
            {"operation": "separate_loose", "params": {"object_id": "a", "new_object_ids": ["b2"]}},
        ],
    }
    GeometryRecipe.from_dict(joined)

    duplicate = json.loads(json.dumps(joined))
    duplicate["steps"][-1]["params"]["new_object_ids"] = ["a"]
    with pytest.raises(BlenderBoundaryError, match="unique"):
        GeometryRecipe.from_dict(duplicate)


def _fake_runner(tmp_path: Path) -> tuple[GeometryRunner, Path, Path]:
    install = tmp_path / "install"
    work = tmp_path / "work"
    install.mkdir()
    work.mkdir()
    executable = install / ("blender.exe" if os.name == "nt" else "blender")
    executable.write_bytes(b"fake-blender-r10.3")
    boundary = BlenderExecutableBoundary(allowed_roots=(install,), staging_root=work)
    sandbox = ProcessSandbox(work, allowed_executables={"blender", "blender.exe"})

    class FakeBlenderRunner(BlenderRunner):
        def _run_process(self, argv: tuple[str, ...], cwd: Path) -> RunnerProcessResult:
            recipe = json.loads((cwd / "geometry_job.json").read_text())
            blend = b"r10.3-derived-blend"
            (cwd / "geometry_output.blend").write_bytes(blend)
            result = {
                "schema": "kodepoia.blender.geometry_result",
                "version": 1,
                "status": "pass",
                "blockers": [],
                "recipe_digest": recipe["recipe_digest"],
                "objects": {
                    "cube": {
                        "source": {"vertices": 8, "edges": 18, "faces": 12, "triangles": 12, "modifiers": []},
                        "evaluated": {"vertices": 8, "edges": 18, "faces": 12, "triangles": 12},
                    }
                },
                "artifact": {
                    "filename": "geometry_output.blend",
                    "bytes": len(blend),
                    "sha256": hashlib.sha256(blend).hexdigest(),
                },
            }
            (cwd / "geometry_result.json").write_text(json.dumps(result), encoding="utf-8")
            return RunnerProcessResult(0, "KODEPOIA_R10_3_RESULT=pass\n", "", stdout_bytes=29)

    return GeometryRunner(FakeBlenderRunner(boundary, sandbox)), executable, work


def test_r10_3_fake_runner_emits_stable_manifest(tmp_path: Path) -> None:
    runner, executable, _work = _fake_runner(tmp_path)
    manifest = runner.run(executable, recipe_payload(), source_sha=SOURCE_SHA)
    assert manifest["status"] == "pass"
    assert manifest["blockers"] == []
    assert manifest["objects"]["cube"]["source"]["triangles"] == 12
    assert manifest["artifact"]["bytes"] == len(b"r10.3-derived-blend")
    schema = json.loads((ROOT / "schemas/r10-geometry-manifest-v1.schema.json").read_text())
    Draft202012Validator(schema).validate(manifest)


def test_r10_3_result_digest_tamper_blocks(tmp_path: Path) -> None:
    runner, executable, _work = _fake_runner(tmp_path)
    original = runner.blender_runner._run_process

    def tampered(argv: tuple[str, ...], cwd: Path) -> RunnerProcessResult:
        process = original(argv, cwd)
        payload = json.loads((cwd / "geometry_result.json").read_text())
        payload["recipe_digest"] = "0" * 64
        (cwd / "geometry_result.json").write_text(json.dumps(payload), encoding="utf-8")
        return process

    runner.blender_runner._run_process = tampered  # type: ignore[method-assign]
    manifest = runner.run(executable, recipe_payload(), source_sha=SOURCE_SHA)
    assert manifest["status"] == "fail"
    assert "recipe_digest_mismatch" in manifest["blockers"]


def test_r10_3_bootstrap_has_no_dynamic_code_or_network_surface() -> None:
    compile(GEOMETRY_BOOTSTRAP_SOURCE, "geometry_bootstrap.py", "exec")
    lowered = GEOMETRY_BOOTSTRAP_SOURCE.lower()
    assert "exec(" not in lowered
    assert "eval(" not in lowered
    assert "subprocess" not in lowered
    assert "socket" not in lowered
    assert "urllib" not in lowered
    assert "requests" not in lowered
    assert "bmesh.ops.triangulate" in GEOMETRY_BOOTSTRAP_SOURCE
    assert "bmesh.ops.recalc_face_normals" in GEOMETRY_BOOTSTRAP_SOURCE
