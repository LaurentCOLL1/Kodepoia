from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.blender3d import BlenderExecutableBoundary, MeshQAProfile, MeshQARunner, MeshRepairRecipe, evaluate_mesh_qa
from kodepoia.blender3d.errors import BlenderBoundaryError
from kodepoia.blender3d.qa_bootstrap import MESH_QA_BOOTSTRAP_SOURCE
from kodepoia.blender3d.runner import BlenderRunner, RunnerProcessResult
from kodepoia.core.sandbox import ProcessSandbox

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "d" * 40


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def profile(blend_sha: str, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "version": 1, "profile_id": "qa.fixture", "asset_class": "closed_static", "input_blend_sha256": blend_sha,
        "object_ids": ["cube"],
        "budgets": {"max_objects": 4, "max_triangles": 1000, "max_materials": 8, "max_textures": 16, "max_shape_keys": 8, "max_uv_layers": 4, "max_loose_vertices": 0, "max_loose_edges": 0, "max_non_manifold_edges": 0, "max_duplicate_vertex_indicators": 0, "max_zero_area_uv_triangles": 0, "max_scale_ratio": 10.0},
        "boundary_policy": "block", "overlap_policy": "ignore", "require_uv": True, "require_consistent_winding": True,
        "minimum_face_area": 1e-12, "duplicate_tolerance": 1e-7, "uv_zero_area_epsilon": 1e-12,
    }
    payload.update(overrides)
    return payload


def measurements(parsed: MeshQAProfile, **source_overrides: object) -> dict[str, object]:
    source: dict[str, object] = {
        "vertices": 8, "edges": 12, "faces": 6, "triangles": 12, "finite_coordinates": True, "degenerate_faces": 0,
        "loose_vertices": 0, "loose_edges": 0, "boundary_edges": 0, "non_manifold_edges": 0, "inconsistent_winding_edges": 0,
        "duplicate_vertex_indicators": 0, "uv_layer_count": 1,
        "uv_layers": {"UVMap": {"loops": 24, "zero_area_triangles": 0, "triangle_area_sum": 1.0, "bounds": [0.0, 0.0, 1.0, 1.0]}},
        "zero_area_uv_triangles": 0, "materials": 1, "textures": 1, "shape_keys": 0,
    }
    source.update(source_overrides)
    evaluated = dict(source)
    return {
        "schema": "kodepoia.blender.mesh_qa_measurements", "version": 1, "status": "pass", "blockers": [],
        "profile_digest": parsed.digest, "input_blend_sha256": parsed.input_blend_sha256, "input_file_sha256": parsed.input_blend_sha256,
        "objects": {"cube": {"source": source, "evaluated": evaluated, "transform": {"finite": True, "scale": [1.0, 1.0, 1.0], "scale_ratio": 1.0}, "normal_maps": [{"material_id": "fixture.mat", "uv_map": "UVMap", "tangent_status": "pass", "reason": "tangent_basis_valid"}], "uv_overlap": {"status": "not_measured", "reason": "bounded_runtime_policy"}}},
    }


def test_r10_5_profile_digest_schemas_and_repair_allowlist() -> None:
    parsed = MeshQAProfile.from_dict(profile("a" * 64))
    assert parsed.digest == MeshQAProfile.from_dict(json.loads(json.dumps(parsed.to_dict()))).digest
    Draft202012Validator(json.loads((ROOT / "schemas/r10-mesh-qa-profile-v1.schema.json").read_text())).validate(parsed.to_dict())
    repair = MeshRepairRecipe.from_dict({"version": 1, "recipe_id": "repair.normals", "input_blend_sha256": "a" * 64, "object_ids": ["cube"], "operation": "recalculate_normals"})
    Draft202012Validator(json.loads((ROOT / "schemas/r10-mesh-repair-recipe-v1.schema.json").read_text())).validate(repair.to_dict())
    bad = repair.to_dict(); bad["operation"] = "delete_faces"
    with pytest.raises(BlenderBoundaryError, match="Unsupported"):
        MeshRepairRecipe.from_dict(bad)


def test_r10_5_rejects_unknown_fields_and_unbounded_profile() -> None:
    payload = profile("a" * 64); payload["arbitrary_python"] = "pass"
    with pytest.raises(BlenderBoundaryError, match="missing or unknown"):
        MeshQAProfile.from_dict(payload)
    payload = profile("a" * 64); payload["budgets"]["max_triangles"] = 100_000_000  # type: ignore[index]
    with pytest.raises(BlenderBoundaryError, match="max_triangles"):
        MeshQAProfile.from_dict(payload)


def test_r10_5_engine_passes_clean_fixture_and_schema() -> None:
    parsed = MeshQAProfile.from_dict(profile("a" * 64))
    report = evaluate_mesh_qa(parsed, measurements(parsed))
    assert report["status"] == "pass" and report["summary"]["block"] == 0
    Draft202012Validator(json.loads((ROOT / "schemas/r10-mesh-qa-report-v1.schema.json").read_text())).validate(report)


def test_r10_5_boundary_policy_is_profile_aware() -> None:
    closed = MeshQAProfile.from_dict(profile("a" * 64))
    closed_report = evaluate_mesh_qa(closed, measurements(closed, boundary_edges=4))
    assert "boundary_edges" in {item["rule_id"] for item in closed_report["rules"] if item["state"] == "BLOCK"}
    opened = MeshQAProfile.from_dict(profile("a" * 64, asset_class="character", boundary_policy="allow"))
    open_report = evaluate_mesh_qa(opened, measurements(opened, boundary_edges=4))
    assert next(item for item in open_report["rules"] if item["rule_id"] == "boundary_edges")["state"] == "PASS"


def test_r10_5_malformed_geometry_budget_and_tangent_fail_closed() -> None:
    parsed = MeshQAProfile.from_dict(profile("a" * 64))
    payload = measurements(parsed, finite_coordinates=False, degenerate_faces=1, loose_vertices=2, triangles=5000)
    payload["objects"]["cube"]["normal_maps"][0]["tangent_status"] = "fail"  # type: ignore[index]
    report = evaluate_mesh_qa(parsed, payload)
    blocked = {item["rule_id"] for item in report["rules"] if item["state"] == "BLOCK"}
    assert {"finite_coordinates_source", "degenerate_faces", "loose_vertices", "triangle_budget", "normal_map_tangents"} <= blocked
    assert report["status"] == "block"


def test_r10_5_requested_overlap_never_manufactures_pass() -> None:
    parsed = MeshQAProfile.from_dict(profile("a" * 64, overlap_policy="block"))
    report = evaluate_mesh_qa(parsed, measurements(parsed))
    overlap = next(item for item in report["rules"] if item["rule_id"] == "uv_overlap")
    assert overlap["state"] == "BLOCK" and overlap["value"]["measured"] is False


def _make_runner(tmp_path: Path, *, tamper: str | None = None) -> tuple[MeshQARunner, Path, Path]:
    install, input_root, work = tmp_path / "install", tmp_path / "inputs", tmp_path / "work"
    for item in (install, input_root, work): item.mkdir(parents=True, exist_ok=False)
    executable = install / ("blender.exe" if os.name == "nt" else "blender"); executable.write_bytes(b"fake-blender-r10.5")
    input_blend = input_root / "source.blend"; input_blend.write_bytes(b"immutable-r10.5-blend")
    boundary = BlenderExecutableBoundary(allowed_roots=(install,), staging_root=work)
    sandbox = ProcessSandbox(work, allowed_executables={"blender", "blender.exe"})
    class FakeBlenderRunner(BlenderRunner):
        def _run_process(self, argv: tuple[str, ...], cwd: Path) -> RunnerProcessResult:
            job = json.loads((cwd / "mesh_qa_job.json").read_text()); parsed = MeshQAProfile.from_dict(job["profile"]); result = measurements(parsed)
            if tamper == "profile": result["profile_digest"] = "0" * 64
            elif tamper == "input": result["input_file_sha256"] = "0" * 64
            (cwd / "mesh_qa_result.json").write_text(json.dumps(result), encoding="utf-8")
            return RunnerProcessResult(0, "KODEPOIA_R10_5_RESULT=pass\n", "")
    return MeshQARunner(FakeBlenderRunner(boundary, sandbox), input_root=input_root), executable, input_blend


def test_r10_5_runner_is_read_only_and_lineage_bound(tmp_path: Path) -> None:
    runner, executable, input_blend = _make_runner(tmp_path); before = _digest(input_blend.read_bytes())
    manifest = runner.run(executable, profile(before), source_sha=SOURCE_SHA, input_blend=input_blend)
    assert manifest["status"] == "pass" and manifest["read_only"] is True and manifest["blockers"] == []
    assert _digest(input_blend.read_bytes()) == before
    assert list((tmp_path / "work").glob("*.blend")) == [tmp_path / "work" / "input.blend"]


@pytest.mark.parametrize("tamper, blocker", [("profile", "profile_digest_mismatch"), ("input", "staged_input_digest_mismatch")])
def test_r10_5_runner_rejects_tampered_measurement_lineage(tmp_path: Path, tamper: str, blocker: str) -> None:
    runner, executable, input_blend = _make_runner(tmp_path, tamper=tamper)
    manifest = runner.run(executable, profile(_digest(input_blend.read_bytes())), source_sha=SOURCE_SHA, input_blend=input_blend)
    assert manifest["status"] == "block" and blocker in manifest["blockers"]


def test_r10_5_bootstrap_is_static_read_only_and_offline() -> None:
    compile(MESH_QA_BOOTSTRAP_SOURCE, "mesh_qa_bootstrap.py", "exec")
    tree = ast.parse(MESH_QA_BOOTSTRAP_SOURCE); forbidden_roots = {"socket", "http", "urllib", "requests", "ftplib", "subprocess"}; imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module: imports.add(node.module.split(".")[0])
    assert not (imports & forbidden_roots)
    lowered = MESH_QA_BOOTSTRAP_SOURCE.lower()
    for forbidden in ("exec(", "eval(", "bpy.ops.wm.save", "bpy.ops.object.delete", "bpy.ops.mesh.", "bpy.ops.wm.url_open"):
        assert forbidden not in lowered
    assert "calc_loop_triangles" in lowered and "calc_tangents" in lowered and "is_manifold" in lowered and "is_contiguous" in lowered
