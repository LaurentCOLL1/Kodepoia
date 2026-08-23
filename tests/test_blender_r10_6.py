from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.blender3d import BlenderExecutableBoundary, RigProfile, RigRunner, evaluate_rig_measurements
from kodepoia.blender3d.errors import BlenderBoundaryError
from kodepoia.blender3d.rig_bootstrap import RIG_BOOTSTRAP_SOURCE
from kodepoia.blender3d.runner import BlenderRunner, RunnerProcessResult
from kodepoia.core.sandbox import ProcessSandbox

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "e" * 40


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def profile(input_sha: str, *, strategy: str = "explicit", max_influences: int = 4, extended: bool = False) -> dict[str, object]:
    weights = [] if strategy != "explicit" else [{"vertex":index,"influences":[{"bone_id":"root","weight":1.0}]} for index in range(8)]
    return {"version":1,"rig_id":"fixture.rig","armature_id":"fixture_armature","mode":"validate_existing" if strategy == "existing" else "create","input_blend_sha256":input_sha,"bones":[{"bone_id":"root","display_name":"Root","parent_id":None,"head":[0.0,-1.0,0.0],"tail":[0.0,1.0,0.0],"deform":True,"connected":False},{"bone_id":"control","display_name":"Control","parent_id":"root","head":[0.0,1.0,0.0],"tail":[0.0,2.0,0.0],"deform":False,"connected":True}],"meshes":[{"mesh_id":"body","strategy":strategy,"weights":weights}],"influence":{"max_influences":max_influences,"allow_extended_influences":extended,"normalization_tolerance":0.0001,"tiny_weight_threshold":0.00001,"require_deformation_probe":True}}


def measurements(parsed: RigProfile, **mesh_overrides: object) -> dict[str, object]:
    mesh = {"vertex_count":8,"weighted_vertices":8,"zero_weight_vertices":0,"invalid_bone_references":0,"control_bone_references":0,"sum_outside_tolerance":0,"influence_over_budget":0,"max_influences":1,"tiny_weight_count":0,"orphan_vertex_groups":0,"orphan_group_names":[],"armature_modifier_bound":True,"parent_bound":True,"deformation_probe":{"status":"pass","moved_vertices":8,"reason":"weighted_geometry_moved"}}
    mesh.update(mesh_overrides)
    return {"schema":"kodepoia.blender.rig_measurements","version":1,"status":"pass","blockers":[],"profile_digest":parsed.digest,"input_blend_sha256":parsed.input_blend_sha256,"input_file_sha256":parsed.input_blend_sha256,"armature":{"object_id":parsed.armature_id,"rig_id":parsed.rig_id,"bones":[{"bone_id":"control","actual_name":"control","parent_id":"root","deform":False,"connected":True},{"bone_id":"root","actual_name":"root","parent_id":None,"deform":True,"connected":False}]},"meshes":{"body":mesh},"artifact":{"filename":"rig_output.blend","bytes":1,"sha256":"f"*64}}


def test_r10_6_profile_schema_identity_and_default_four_influences() -> None:
    parsed = RigProfile.from_dict(profile("a"*64))
    assert parsed.influence.max_influences == 4
    assert parsed.deform_bone_ids == ("root",)
    assert parsed.digest == RigProfile.from_dict(json.loads(json.dumps(parsed.to_dict()))).digest
    Draft202012Validator(json.loads((ROOT/"schemas/r10-rig-profile-v1.schema.json").read_text())).validate(parsed.to_dict())


def test_r10_6_extended_influence_requires_explicit_opt_in() -> None:
    with pytest.raises(BlenderBoundaryError, match="explicit opt-in"):
        RigProfile.from_dict(profile("a"*64, max_influences=6, extended=False))
    parsed = RigProfile.from_dict(profile("a"*64, max_influences=6, extended=True))
    assert parsed.influence.max_influences == 6


def test_r10_6_hierarchy_and_control_weight_contracts_fail_closed() -> None:
    bad = profile("a"*64); bad["bones"][1]["head"] = [1.0,1.0,0.0]  # type: ignore[index]
    with pytest.raises(BlenderBoundaryError, match="Connected child"):
        RigProfile.from_dict(bad)
    bad = profile("a"*64); bad["meshes"][0]["weights"][0]["influences"] = [{"bone_id":"control","weight":1.0}]  # type: ignore[index]
    with pytest.raises(BlenderBoundaryError, match="control-only"):
        RigProfile.from_dict(bad)


def test_r10_6_tiny_explicit_weights_are_pruned_then_normalized() -> None:
    payload = profile("a"*64)
    payload["meshes"][0]["weights"][0]["influences"] = [{"bone_id":"root","weight":0.000001}]  # type: ignore[index]
    parsed = RigProfile.from_dict(payload)
    rows = parsed.normalized_explicit_weights()["body"]
    assert rows[0]["influences"] == []


def test_r10_6_validator_clean_and_schema_valid() -> None:
    parsed = RigProfile.from_dict(profile("a"*64))
    report = evaluate_rig_measurements(parsed, measurements(parsed))
    assert report["status"] == "pass" and report["summary"]["block"] == 0
    Draft202012Validator(json.loads((ROOT/"schemas/r10-rig-report-v1.schema.json").read_text())).validate(report)


def test_r10_6_validator_blocks_weights_binding_and_deformation_failures() -> None:
    parsed = RigProfile.from_dict(profile("a"*64))
    report = evaluate_rig_measurements(parsed, measurements(parsed, zero_weight_vertices=2, sum_outside_tolerance=1, influence_over_budget=1, max_influences=5, control_bone_references=1, armature_modifier_bound=False, parent_bound=False, deformation_probe={"status":"fail","moved_vertices":0,"reason":"no_geometry_movement"}))
    blocked = {item["rule_id"] for item in report["rules"] if item["state"] == "BLOCK"}
    assert {"zero_weight_vertices","weight_normalization","influence_budget","control_bone_weights","armature_modifier_binding","armature_parent_binding","deformation_probe"} <= blocked


def test_r10_6_validate_existing_requires_existing_strategy() -> None:
    parsed = RigProfile.from_dict(profile("a"*64, strategy="existing"))
    assert parsed.mode.value == "validate_existing"
    bad = profile("a"*64, strategy="existing"); bad["meshes"][0]["strategy"] = "nearest_deform_bone"  # type: ignore[index]
    with pytest.raises(BlenderBoundaryError, match="validate_existing"):
        RigProfile.from_dict(bad)


def make_runner(tmp_path: Path, *, tamper: bool=False) -> tuple[RigRunner, Path, Path]:
    install, inputs, work = tmp_path/"install", tmp_path/"inputs", tmp_path/"work"
    for item in (install, inputs, work): item.mkdir(parents=True, exist_ok=False)
    executable = install/("blender.exe" if os.name=="nt" else "blender"); executable.write_bytes(b"fake-r10.6")
    source = inputs/"source.blend"; source.write_bytes(b"immutable-rig-source")
    boundary = BlenderExecutableBoundary(allowed_roots=(install,), staging_root=work)
    sandbox = ProcessSandbox(work, allowed_executables={"blender","blender.exe"})
    class Fake(BlenderRunner):
        def _run_process(self, argv: tuple[str,...], cwd: Path) -> RunnerProcessResult:
            job=json.loads((cwd/"rig_job.json").read_text()); parsed=RigProfile.from_dict(job["profile"]); blend=b"derived-rig"; (cwd/"rig_output.blend").write_bytes(blend); result=measurements(parsed); result["artifact"]={"filename":"rig_output.blend","bytes":len(blend),"sha256":digest(blend)}
            if tamper: result["profile_digest"]="0"*64
            (cwd/"rig_result.json").write_text(json.dumps(result), encoding="utf-8")
            return RunnerProcessResult(0,"KODEPOIA_R10_6_RESULT=pass\n","")
    return RigRunner(Fake(boundary,sandbox), input_root=inputs), executable, source


def test_r10_6_runner_preserves_parent_lineage_and_derivative_identity(tmp_path: Path) -> None:
    runner, executable, source = make_runner(tmp_path); input_sha=digest(source.read_bytes())
    manifest=runner.run(executable, profile(input_sha), source_sha=SOURCE_SHA, input_blend=source)
    assert manifest["status"] == "pass" and manifest["blockers"] == []
    assert manifest["lineage"]["parent_sha256"] == input_sha
    assert manifest["lineage"]["derived_sha256"] == manifest["artifact"]["sha256"]
    assert digest(source.read_bytes()) == input_sha


def test_r10_6_runner_blocks_profile_tamper(tmp_path: Path) -> None:
    runner, executable, source = make_runner(tmp_path, tamper=True)
    manifest=runner.run(executable, profile(digest(source.read_bytes())), source_sha=SOURCE_SHA, input_blend=source)
    assert manifest["status"] == "block" and "profile_digest_mismatch" in manifest["blockers"]


def test_r10_6_bootstrap_has_fixed_offline_rig_surface() -> None:
    compile(RIG_BOOTSTRAP_SOURCE,"rig_bootstrap.py","exec"); tree=ast.parse(RIG_BOOTSTRAP_SOURCE); forbidden={"socket","http","urllib","requests","ftplib","subprocess"}; imports=set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module: imports.add(node.module.split(".")[0])
    assert not imports & forbidden
    lowered=RIG_BOOTSTRAP_SOURCE.lower()
    for token in ("exec(","eval(","bpy.ops.paint.","armature_auto","bpy.ops.object.parent_set","bpy.ops.wm.url_open"):
        assert token not in lowered
    assert "edit_bones.new" in lowered and "use_deform" in lowered and "vertex_groups.new" in lowered and "type=\"armature\"" in lowered


def test_r10_6_local_acceptance_script_is_bounded_and_schema_exists() -> None:
    source=(ROOT/"scripts/r10_6_local_acceptance.py").read_text(); compile(source,"r10_6_local_acceptance.py","exec")
    assert "run_capability_probe" in source and "GeometryRunner" in source and "RigRunner" in source and "--source-sha" in source
    Draft202012Validator.check_schema(json.loads((ROOT/"schemas/r10-rig-local-acceptance-v1.schema.json").read_text()))
