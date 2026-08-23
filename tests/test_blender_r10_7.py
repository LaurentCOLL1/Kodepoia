from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.blender3d import (
    AnimationRunner,
    BlenderExecutableBoundary,
    RetargetRecipe,
    RigSemanticProfile,
    evaluate_animation_measurements,
)
from kodepoia.blender3d.animation_bootstrap import ANIMATION_BOOTSTRAP_SOURCE
from kodepoia.blender3d.errors import BlenderBoundaryError
from kodepoia.blender3d.runner import BlenderRunner, RunnerProcessResult
from kodepoia.core.sandbox import ProcessSandbox

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "f" * 40


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def semantic_profile(input_sha: str, *, rig_id: str, armature_id: str) -> dict[str, object]:
    return {
        "rig_id": rig_id,
        "armature_id": armature_id,
        "input_blend_sha256": input_sha,
        "bones": [{"bone_id": "root", "actual_name": "root", "parent_id": None, "deform": True}],
    }


def recipe(input_sha: str, *, root_motion: str = "keep", max_keys: int = 16) -> dict[str, object]:
    return {
        "version": 1,
        "recipe_id": "fixture.retarget",
        "input_blend_sha256": input_sha,
        "source_rig": semantic_profile(input_sha, rig_id="fixture.source", armature_id="source_armature"),
        "target_rig": semantic_profile(input_sha, rig_id="fixture.target", armature_id="target_armature"),
        "clip": {
            "clip_id": "fixture.clip",
            "fps": 30.0,
            "frame_start": 1.0,
            "frame_end": 10.0,
            "loop": True,
            "root_motion": root_motion,
            "channels": [
                {"bone_id": "root", "path": "location", "keys": [{"frame": 1.0, "value": [0.0, 0.0, 0.0]}, {"frame": 10.0, "value": [0.5, 0.0, 0.0]}]},
                {"bone_id": "root", "path": "rotation_quaternion", "keys": [{"frame": 1.0, "value": [2.0, 0.0, 0.0, 0.0]}, {"frame": 10.0, "value": [1.0, 0.0, 0.0, 0.0]}]},
            ],
        },
        "mappings": [{"source_bone_id": "root", "target_bone_id": "root", "copy_translation": True, "copy_rotation": True, "copy_scale": False}],
        "required_target_bones": ["root"],
        "translation_scale": 1.0,
        "max_keys": max_keys,
    }


def measurements(parsed: RetargetRecipe, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "mapping": {"mapped_bones": 1, "missing_required": [], "ambiguous": [], "unmapped_source_deform": [], "unmapped_target_deform": []},
        "rest_pose": {"max_direction_angle_degrees": 0.0, "max_scaled_length_relative_error": 0.0},
        "sampling": {"policy": "explicit_keys_only", "constraint_count": 0, "driver_count": 0},
        "clip": {"key_count": parsed.clip.key_count, "frame_start": parsed.clip.frame_start, "frame_end": parsed.clip.frame_end, "fps": parsed.clip.fps, "duration_seconds": (parsed.clip.frame_end - parsed.clip.frame_start) / parsed.clip.fps, "loop": parsed.clip.loop},
        "nla": {"track_count": 1, "strip_count": 1, "action_identity_bound": True, "active_action_cleared": True},
        "root_motion": {"translation_delta": 0.0 if parsed.clip.root_motion.value == "zero" else 0.5},
    }
    payload.update(overrides)
    return payload


def test_r10_7_semantic_profile_identity_is_deterministic() -> None:
    raw = semantic_profile("a" * 64, rig_id="fixture.source", armature_id="source_armature")
    parsed = RigSemanticProfile.from_dict(raw)
    assert parsed.deform_ids == ("root",)
    assert parsed.digest == RigSemanticProfile.from_dict(json.loads(json.dumps(parsed.to_dict()))).digest


def test_r10_7_clip_normalizes_quaternion_and_rejects_bad_frames() -> None:
    parsed = RetargetRecipe.from_dict(recipe("a" * 64))
    quaternion = next(channel for channel in parsed.clip.channels if channel.path.value == "rotation_quaternion")
    assert quaternion.keys[0].value == (1.0, 0.0, 0.0, 0.0)
    bad = recipe("a" * 64)
    bad["clip"]["channels"][0]["keys"][1]["frame"] = 11.0  # type: ignore[index]
    with pytest.raises(BlenderBoundaryError, match="outside clip frame range"):
        RetargetRecipe.from_dict(bad)


def test_r10_7_mapping_is_explicit_injective_and_required() -> None:
    bad = recipe("a" * 64)
    bad["mappings"].append(dict(bad["mappings"][0]))  # type: ignore[union-attr,index]
    with pytest.raises(BlenderBoundaryError, match="source semantic bones may be mapped only once"):
        RetargetRecipe.from_dict(bad)
    bad = recipe("a" * 64)
    bad["mappings"] = []
    with pytest.raises(BlenderBoundaryError, match="mappings must contain"):
        RetargetRecipe.from_dict(bad)


def test_r10_7_key_budget_blocks_oversized_clip() -> None:
    with pytest.raises(BlenderBoundaryError, match="key count exceeds"):
        RetargetRecipe.from_dict(recipe("a" * 64, max_keys=3))


def test_r10_7_validator_passes_clean_fixture_and_schema() -> None:
    parsed = RetargetRecipe.from_dict(recipe("a" * 64))
    report = evaluate_animation_measurements(parsed, measurements(parsed))
    assert report["status"] == "pass"
    assert report["summary"]["block"] == 0
    Draft202012Validator(json.loads((ROOT / "schemas/r10-animation-report-v1.schema.json").read_text())).validate(report)
    Draft202012Validator(json.loads((ROOT / "schemas/r10-retarget-recipe-v1.schema.json").read_text())).validate(parsed.to_dict())


def test_r10_7_validator_blocks_rest_sampling_nla_and_root_failures() -> None:
    parsed = RetargetRecipe.from_dict(recipe("a" * 64, root_motion="zero"))
    report = evaluate_animation_measurements(
        parsed,
        measurements(
            parsed,
            rest_pose={"max_direction_angle_degrees": 80.0, "max_scaled_length_relative_error": 0.9},
            sampling={"policy": "explicit_keys_only", "constraint_count": 1, "driver_count": 1},
            nla={"track_count": 2, "strip_count": 0, "action_identity_bound": False, "active_action_cleared": False},
            root_motion={"translation_delta": 1.0},
        ),
    )
    blocked = {item["rule_id"] for item in report["rules"] if item["state"] == "BLOCK"}
    assert {"rest_direction_compatibility", "rest_length_compatibility", "constraint_free_target", "driver_free_target", "nla_track_count", "nla_strip_count", "export_readiness", "root_motion_policy"} <= blocked


def test_r10_7_unmapped_optional_deform_is_warn_not_guessed() -> None:
    parsed = RetargetRecipe.from_dict(recipe("a" * 64))
    report = evaluate_animation_measurements(parsed, measurements(parsed, mapping={"mapped_bones": 1, "missing_required": [], "ambiguous": [], "unmapped_source_deform": ["finger"], "unmapped_target_deform": []}))
    warning = next(item for item in report["rules"] if item["rule_id"] == "unmapped_source_deform")
    assert warning["state"] == "WARN"
    assert report["status"] == "warn"


def make_runner(tmp_path: Path, *, tamper: bool = False) -> tuple[AnimationRunner, Path, Path]:
    install, inputs, work = tmp_path / "install", tmp_path / "inputs", tmp_path / "work"
    for item in (install, inputs, work):
        item.mkdir(parents=True, exist_ok=False)
    executable = install / ("blender.exe" if os.name == "nt" else "blender")
    executable.write_bytes(b"fake-r10.7")
    source = inputs / "rigged.blend"
    source.write_bytes(b"immutable-r10.7-source")
    boundary = BlenderExecutableBoundary(allowed_roots=(install,), staging_root=work)
    sandbox = ProcessSandbox(work, allowed_executables={"blender", "blender.exe"})

    class Fake(BlenderRunner):
        def _run_process(self, argv: tuple[str, ...], cwd: Path) -> RunnerProcessResult:
            job = json.loads((cwd / "animation_job.json").read_text())
            parsed = RetargetRecipe.from_dict(job["recipe"])
            blend = b"derived-r10.7-animation"
            (cwd / "animation_output.blend").write_bytes(blend)
            result = {
                "schema": "kodepoia.blender.animation_measurements",
                "version": 1,
                "status": "pass",
                "blockers": [],
                "recipe_digest": "0" * 64 if tamper else parsed.digest,
                "input_blend_sha256": parsed.input_blend_sha256,
                "input_file_sha256": parsed.input_blend_sha256,
                **measurements(parsed),
                "artifact": {"filename": "animation_output.blend", "bytes": len(blend), "sha256": digest(blend)},
            }
            (cwd / "animation_result.json").write_text(json.dumps(result), encoding="utf-8")
            return RunnerProcessResult(0, "KODEPOIA_R10_7_RESULT=pass\n", "")

    return AnimationRunner(Fake(boundary, sandbox), input_root=inputs), executable, source


def test_r10_7_runner_preserves_input_and_lineage(tmp_path: Path) -> None:
    runner, executable, source = make_runner(tmp_path)
    input_sha = digest(source.read_bytes())
    manifest = runner.run(executable, recipe(input_sha), source_sha=SOURCE_SHA, input_blend=source)
    assert manifest["status"] == "pass"
    assert manifest["blockers"] == []
    assert manifest["lineage"]["parent_sha256"] == input_sha
    assert manifest["lineage"]["derived_sha256"] == manifest["artifact"]["sha256"]
    assert digest(source.read_bytes()) == input_sha


def test_r10_7_runner_blocks_result_tamper(tmp_path: Path) -> None:
    runner, executable, source = make_runner(tmp_path, tamper=True)
    manifest = runner.run(executable, recipe(digest(source.read_bytes())), source_sha=SOURCE_SHA, input_blend=source)
    assert manifest["status"] == "block"
    assert "recipe_digest_mismatch" in manifest["blockers"]


def test_r10_7_bootstrap_has_static_offline_animation_surface() -> None:
    compile(ANIMATION_BOOTSTRAP_SOURCE, "animation_bootstrap.py", "exec")
    tree = ast.parse(ANIMATION_BOOTSTRAP_SOURCE)
    forbidden = {"socket", "http", "urllib", "requests", "ftplib", "subprocess"}
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert not imports & forbidden
    lowered = ANIMATION_BOOTSTRAP_SOURCE.lower()
    for token in ("exec(", "eval(", "driver_add", "bpy.data.texts", "bpy.ops.script", "bpy.ops.wm.url_open"):
        assert token not in lowered
    assert "bpy.data.actions.new" in lowered
    assert "keyframe_insert" in lowered
    assert "nla_tracks.new" in lowered
    assert "strips.new" in lowered


def test_r10_7_local_acceptance_script_and_schema_are_bounded() -> None:
    source = (ROOT / "scripts/r10_7_local_acceptance.py").read_text()
    compile(source, "r10_7_local_acceptance.py", "exec")
    assert "GeometryRunner" in source and "RigRunner" in source and "AnimationRunner" in source
    assert "--source-sha" in source and "run_capability_probe" in source
    schema = json.loads((ROOT / "schemas/r10-animation-local-acceptance-v1.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
