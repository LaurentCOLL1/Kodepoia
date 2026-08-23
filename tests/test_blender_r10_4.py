from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.blender3d import BlenderExecutableBoundary
from kodepoia.blender3d.errors import BlenderBoundaryError
from kodepoia.blender3d.pbr_bootstrap import PBR_BOOTSTRAP_SOURCE
from kodepoia.blender3d.pbr_contracts import PBRRecipe
from kodepoia.blender3d.pbr_runner import PBRRunner
from kodepoia.blender3d.runner import BlenderRunner, RunnerProcessResult
from kodepoia.core.sandbox import ProcessSandbox

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "c" * 40


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def recipe(blend_sha: str, texture_sha: str) -> dict[str, object]:
    return {
        "version": 1,
        "recipe_id": "pbr.fixture",
        "input_blend_sha256": blend_sha,
        "uv": [{"object_id": "cube", "map_name": "UVMap", "method": "smart", "margin": 0.002, "angle_limit": 1.15192}],
        "materials": [{
            "material_id": "fixture.mat",
            "object_ids": ["cube"],
            "base_color": [0.8, 0.7, 0.6, 1.0],
            "metallic": 0.2,
            "roughness": 0.6,
            "emission_color": [0.0, 0.0, 0.0],
            "emission_strength": 0.0,
            "alpha": 1.0,
            "normal_strength": 1.0,
            "textures": [{"source_id": "normal.fixture", "role": "normal", "sha256": texture_sha, "uv_map": "UVMap"}],
        }],
    }


def test_r10_4_contract_digest_schema_and_color_semantics() -> None:
    payload = recipe("a" * 64, "b" * 64)
    parsed = PBRRecipe.from_dict(payload)
    assert parsed.digest == PBRRecipe.from_dict(json.loads(json.dumps(payload))).digest
    normal = parsed.materials[0].textures[0]
    assert normal.color_semantics == "DATA"
    schema = json.loads((ROOT / "schemas/r10-pbr-recipe-v1.schema.json").read_text())
    Draft202012Validator(schema).validate(parsed.to_dict())


def test_r10_4_rejects_unknown_role_duplicate_role_and_bad_uv_budget() -> None:
    payload = recipe("a" * 64, "b" * 64)
    payload["materials"][0]["textures"][0]["role"] = "height"  # type: ignore[index]
    with pytest.raises(BlenderBoundaryError, match="role"):
        PBRRecipe.from_dict(payload)

    payload = recipe("a" * 64, "b" * 64)
    texture = dict(payload["materials"][0]["textures"][0])  # type: ignore[index]
    texture["source_id"] = "normal.two"
    payload["materials"][0]["textures"].append(texture)  # type: ignore[index]
    with pytest.raises(BlenderBoundaryError, match="role"):
        PBRRecipe.from_dict(payload)

    payload = recipe("a" * 64, "b" * 64)
    payload["uv"][0]["margin"] = 0.5  # type: ignore[index]
    with pytest.raises(BlenderBoundaryError, match="margin"):
        PBRRecipe.from_dict(payload)


def _make_runner(tmp_path: Path, *, tamper: bool = False) -> tuple[PBRRunner, Path, Path, Path]:
    install = tmp_path / "install"
    input_root = tmp_path / "inputs"
    texture_root = tmp_path / "textures"
    work = tmp_path / "work"
    for item in (install, input_root, texture_root, work): item.mkdir()
    executable = install / ("blender.exe" if os.name == "nt" else "blender")
    executable.write_bytes(b"fake-blender-r10.4")
    input_blend = input_root / "source.blend"
    input_blend.write_bytes(b"immutable-r10.3-blend")
    texture = texture_root / "normal.png"
    texture.write_bytes(b"fake-png-normal-data")
    boundary = BlenderExecutableBoundary(allowed_roots=(install,), staging_root=work)
    sandbox = ProcessSandbox(work, allowed_executables={"blender", "blender.exe"})

    class FakeBlenderRunner(BlenderRunner):
        def _run_process(self, argv: tuple[str, ...], cwd: Path) -> RunnerProcessResult:
            job = json.loads((cwd / "pbr_job.json").read_text())
            blend = b"derived-pbr-blend"
            (cwd / "pbr_output.blend").write_bytes(blend)
            result = {
                "schema": "kodepoia.blender.pbr_result", "version": 1, "status": "pass", "blockers": [],
                "recipe_digest": "0" * 64 if tamper else job["recipe_digest"],
                "input_blend_sha256": job["input_blend_sha256"],
                "objects": {"cube": {"uv": {"UVMap": {"loops": 24, "bounds": [0.0, 0.0, 1.0, 1.0]}}, "materials": ["fixture.mat"]}},
                "materials": {"fixture.mat": {"node_types": ["ShaderNodeBsdfPrincipled", "ShaderNodeNormalMap", "ShaderNodeOutputMaterial", "ShaderNodeTexImage", "ShaderNodeUVMap"], "textures": [{"source_id": "normal.fixture", "role": "normal", "is_data": True}]}},
                "artifact": {"filename": "pbr_output.blend", "bytes": len(blend), "sha256": _digest(blend)},
            }
            (cwd / "pbr_result.json").write_text(json.dumps(result), encoding="utf-8")
            return RunnerProcessResult(0, "KODEPOIA_R10_4_RESULT=pass\n", "")

    runner = PBRRunner(FakeBlenderRunner(boundary, sandbox), input_root=input_root, texture_root=texture_root)
    return runner, executable, input_blend, texture


def test_r10_4_fake_runner_preserves_lineage_and_data_colorspace(tmp_path: Path) -> None:
    runner, executable, input_blend, texture = _make_runner(tmp_path)
    payload = recipe(_digest(input_blend.read_bytes()), _digest(texture.read_bytes()))
    manifest = runner.run(executable, payload, source_sha=SOURCE_SHA, input_blend=input_blend, texture_bindings={"normal.fixture": texture})
    assert manifest["status"] == "pass"
    assert manifest["blockers"] == []
    assert manifest["materials"]["fixture.mat"]["textures"][0]["is_data"] is True
    assert manifest["bake"] == {"requested": False, "executed": False}
    schema = json.loads((ROOT / "schemas/r10-pbr-manifest-v1.schema.json").read_text())
    Draft202012Validator(schema).validate(manifest)


def test_r10_4_rejects_texture_escape_and_digest_mismatch(tmp_path: Path) -> None:
    runner, executable, input_blend, texture = _make_runner(tmp_path)
    payload = recipe(_digest(input_blend.read_bytes()), _digest(texture.read_bytes()))
    outside = tmp_path / "outside.png"
    outside.write_bytes(texture.read_bytes())
    with pytest.raises(BlenderBoundaryError, match="governed root"):
        runner.run(executable, payload, source_sha=SOURCE_SHA, input_blend=input_blend, texture_bindings={"normal.fixture": outside})

    runner2, executable2, input_blend2, texture2 = _make_runner(tmp_path / "second")
    payload2 = recipe(_digest(input_blend2.read_bytes()), "f" * 64)
    with pytest.raises(BlenderBoundaryError, match="digest"):
        runner2.run(executable2, payload2, source_sha=SOURCE_SHA, input_blend=input_blend2, texture_bindings={"normal.fixture": texture2})


def test_r10_4_recipe_result_tamper_blocks(tmp_path: Path) -> None:
    runner, executable, input_blend, texture = _make_runner(tmp_path, tamper=True)
    manifest = runner.run(executable, recipe(_digest(input_blend.read_bytes()), _digest(texture.read_bytes())), source_sha=SOURCE_SHA, input_blend=input_blend, texture_bindings={"normal.fixture": texture})
    assert manifest["status"] == "fail"
    assert "recipe_digest_mismatch" in manifest["blockers"]


def test_r10_4_bootstrap_has_fixed_no_bake_no_network_surface() -> None:
    compile(PBR_BOOTSTRAP_SOURCE, "pbr_bootstrap.py", "exec")
    lowered = PBR_BOOTSTRAP_SOURCE.lower()
    for forbidden in ("exec(", "eval(", "subprocess", "socket", "urllib", "requests", "bpy.ops.object.bake", "bpy.ops.wm.url_open"):
        assert forbidden not in lowered
    assert "shadernodebsdfprincipled" in lowered
    assert "shadernodenormalmap" in lowered
    assert "colorspace_settings.is_data" in lowered
