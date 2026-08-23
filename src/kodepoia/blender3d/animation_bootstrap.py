from __future__ import annotations

ANIMATION_BOOTSTRAP_SOURCE = r'''from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import bpy

ROOT = Path.cwd().resolve()
JOB = ROOT / "animation_job.json"
RESULT = ROOT / "animation_result.json"
RESULT_TMP = ROOT / "animation_result.tmp"
INPUT_BLEND = ROOT / "input.blend"
OUTPUT_BLEND = ROOT / "animation_output.blend"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_result(payload: dict[str, object]) -> None:
    RESULT_TMP.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    os.replace(RESULT_TMP, RESULT)


def get_armature(armature_id: str) -> bpy.types.Object:
    matches = [item for item in bpy.data.objects if item.type == "ARMATURE" and item.get("kodepoia_id") == armature_id]
    if len(matches) != 1:
        raise RuntimeError("armature_identity_resolution_failed:" + armature_id)
    return matches[0]


def semantic_actual_names(armature: bpy.types.Object) -> dict[str, str]:
    result: dict[str, str] = {}
    for bone in armature.data.bones:
        semantic = bone.get("kodepoia_bone_id")
        if isinstance(semantic, str):
            if semantic in result:
                raise RuntimeError("duplicate_semantic_bone_id:" + semantic)
            result[semantic] = bone.name
    return result


def validate_profile(armature: bpy.types.Object, profile: dict[str, object]) -> dict[str, str]:
    actual = semantic_actual_names(armature)
    expected = {str(item["bone_id"]): str(item["actual_name"]) for item in profile["bones"]}
    if set(actual) != set(expected):
        raise RuntimeError("semantic_bone_set_mismatch")
    for semantic, expected_name in expected.items():
        if actual[semantic] != expected_name:
            raise RuntimeError("semantic_actual_name_mismatch:" + semantic)
    return actual


def quat_normalize(values: list[float]) -> tuple[float, float, float, float]:
    norm = math.sqrt(sum(float(item) * float(item) for item in values))
    if norm <= 1e-12:
        raise RuntimeError("zero_quaternion")
    return tuple(float(item) / norm for item in values)


def rest_compatibility(source_armature: bpy.types.Object, target_armature: bpy.types.Object, source_actual: dict[str, str], target_actual: dict[str, str], mappings: list[dict[str, object]], translation_scale: float) -> dict[str, float]:
    max_angle = 0.0
    max_length_error = 0.0
    for mapping in mappings:
        source_id = str(mapping["source_bone_id"])
        target_id = str(mapping["target_bone_id"])
        source_bone = source_armature.data.bones.get(source_actual[source_id])
        target_bone = target_armature.data.bones.get(target_actual[target_id])
        if source_bone is None or target_bone is None:
            raise RuntimeError("mapped_rest_bone_missing")
        source_vector = source_bone.tail_local - source_bone.head_local
        target_vector = target_bone.tail_local - target_bone.head_local
        source_length = float(source_vector.length)
        target_length = float(target_vector.length)
        if source_length <= 1e-12 or target_length <= 1e-12:
            raise RuntimeError("zero_length_rest_bone")
        dot = max(-1.0, min(1.0, float(source_vector.normalized().dot(target_vector.normalized()))))
        angle = math.degrees(math.acos(dot))
        expected_length = source_length * translation_scale
        length_error = abs(target_length - expected_length) / max(target_length, expected_length, 1e-12)
        max_angle = max(max_angle, angle)
        max_length_error = max(max_length_error, length_error)
    return {"max_direction_angle_degrees": max_angle, "max_scaled_length_relative_error": max_length_error}


def main() -> int:
    job = json.loads(JOB.read_text(encoding="utf-8"))
    recipe = dict(job["recipe"])
    if sha256_file(INPUT_BLEND) != str(recipe["input_blend_sha256"]):
        raise RuntimeError("input_digest_mismatch")
    bpy.ops.wm.open_mainfile(filepath=str(INPUT_BLEND))

    source_profile = dict(recipe["source_rig"])
    target_profile = dict(recipe["target_rig"])
    source_armature = get_armature(str(source_profile["armature_id"]))
    target_armature = get_armature(str(target_profile["armature_id"]))
    source_actual = validate_profile(source_armature, source_profile)
    target_actual = validate_profile(target_armature, target_profile)

    mapping_list = [dict(item) for item in recipe["mappings"]]
    mappings = {str(item["source_bone_id"]): item for item in mapping_list}
    mapped_sources = set(mappings)
    mapped_targets = {str(item["target_bone_id"]) for item in mapping_list}
    required = {str(item) for item in recipe["required_target_bones"]}
    missing_required = sorted(required - mapped_targets)
    ambiguous: list[str] = []
    source_deform = {str(item["bone_id"]) for item in source_profile["bones"] if bool(item["deform"])}
    target_deform = {str(item["bone_id"]) for item in target_profile["bones"] if bool(item["deform"])}
    unmapped_source_deform = sorted(source_deform - mapped_sources)
    unmapped_target_deform = sorted(target_deform - mapped_targets)
    translation_scale = float(recipe["translation_scale"])
    rest_pose = rest_compatibility(source_armature, target_armature, source_actual, target_actual, mapping_list, translation_scale)

    if target_armature.animation_data is None:
        target_armature.animation_data_create()
    animation_data = target_armature.animation_data
    if animation_data is None:
        raise RuntimeError("animation_data_creation_failed")
    constraint_count = sum(len(pose_bone.constraints) for pose_bone in target_armature.pose.bones)
    driver_count = len(animation_data.drivers)
    if constraint_count:
        raise RuntimeError("target_constraints_require_explicit_bake_policy")
    if driver_count:
        raise RuntimeError("target_drivers_not_allowed")
    if animation_data.action is not None or len(animation_data.nla_tracks) != 0:
        raise RuntimeError("target_animation_not_empty")

    clip = dict(recipe["clip"])
    requested_fps = float(clip["fps"])
    integer_fps = max(1, min(32767, int(round(requested_fps))))
    bpy.context.scene.render.fps = integer_fps
    bpy.context.scene.render.fps_base = integer_fps / requested_fps
    actual_fps = float(bpy.context.scene.render.fps) / float(bpy.context.scene.render.fps_base)

    action_name = "kdp_action_" + str(clip["clip_id"])
    if bpy.data.actions.get(action_name) is not None:
        raise RuntimeError("action_identity_collision")
    action = bpy.data.actions.new(action_name)
    action["kodepoia_clip_id"] = str(clip["clip_id"])
    action["kodepoia_recipe_id"] = str(recipe["recipe_id"])
    action.use_frame_range = True
    action.frame_start = float(clip["frame_start"])
    action.frame_end = float(clip["frame_end"])
    action.use_cyclic = bool(clip["loop"])
    animation_data.action = action

    target_by_semantic = {str(item["bone_id"]): dict(item) for item in target_profile["bones"]}
    target_root_ids = sorted(item for item, spec in target_by_semantic.items() if spec["parent_id"] is None)
    target_root = target_root_ids[0] if target_root_ids else None
    key_count = 0
    root_first: tuple[float, float, float] | None = None
    root_last: tuple[float, float, float] | None = None

    for raw_channel in clip["channels"]:
        channel = dict(raw_channel)
        source_id = str(channel["bone_id"])
        mapping = mappings.get(source_id)
        if mapping is None:
            continue
        target_id = str(mapping["target_bone_id"])
        actual_name = target_actual[target_id]
        pose_bone = target_armature.pose.bones.get(actual_name)
        if pose_bone is None:
            raise RuntimeError("target_pose_bone_missing:" + target_id)
        path = str(channel["path"])
        allowed = (path == "location" and bool(mapping["copy_translation"])) or (path == "rotation_quaternion" and bool(mapping["copy_rotation"])) or (path == "scale" and bool(mapping["copy_scale"]))
        if not allowed:
            continue
        if path == "rotation_quaternion":
            pose_bone.rotation_mode = "QUATERNION"
        for raw_key in channel["keys"]:
            key = dict(raw_key)
            frame = float(key["frame"])
            values = [float(item) for item in key["value"]]
            if path == "location":
                if str(clip["root_motion"]) == "zero" and target_id == target_root:
                    transformed = (0.0, 0.0, 0.0)
                else:
                    transformed = tuple(item * translation_scale for item in values)
                pose_bone.location = transformed
                if target_id == target_root:
                    if root_first is None:
                        root_first = transformed
                    root_last = transformed
            elif path == "rotation_quaternion":
                transformed = quat_normalize(values)
                pose_bone.rotation_quaternion = transformed
            elif path == "scale":
                transformed = tuple(values)
                pose_bone.scale = transformed
            else:
                raise RuntimeError("unsupported_channel_path")
            if not pose_bone.keyframe_insert(data_path=path, frame=frame, group=target_id):
                raise RuntimeError("keyframe_insert_failed")
            key_count += 1

    if key_count <= 0:
        raise RuntimeError("no_retargeted_keys")
    bpy.context.view_layer.update()

    track = animation_data.nla_tracks.new()
    track.name = "kdp_track_" + str(clip["clip_id"])
    strip = track.strips.new("kdp_strip_" + str(clip["clip_id"]), float(clip["frame_start"]), action)
    strip.action_frame_start = float(clip["frame_start"])
    strip.action_frame_end = float(clip["frame_end"])
    strip.repeat = 1.0
    strip.use_sync_length = True
    animation_data.action = None
    action_identity_bound = strip.action == action and action.get("kodepoia_clip_id") == str(clip["clip_id"])
    active_action_cleared = animation_data.action is None

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
    if not OUTPUT_BLEND.is_file():
        raise RuntimeError("animation_output_missing")

    if root_first is None or root_last is None:
        root_delta = 0.0
    else:
        root_delta = math.sqrt(sum((root_last[i] - root_first[i]) ** 2 for i in range(3)))
    duration_seconds = (float(clip["frame_end"]) - float(clip["frame_start"])) / actual_fps

    result = {
        "schema": "kodepoia.blender.animation_measurements",
        "version": 1,
        "status": "pass",
        "blockers": [],
        "recipe_digest": str(job["recipe_digest"]),
        "input_blend_sha256": str(recipe["input_blend_sha256"]),
        "input_file_sha256": sha256_file(INPUT_BLEND),
        "mapping": {
            "mapped_bones": len(mappings),
            "missing_required": missing_required,
            "ambiguous": ambiguous,
            "source_bone_count": len(source_actual),
            "target_bone_count": len(target_actual),
            "unmapped_source_deform": unmapped_source_deform,
            "unmapped_target_deform": unmapped_target_deform,
        },
        "rest_pose": rest_pose,
        "sampling": {"policy": "explicit_keys_only", "constraint_count": constraint_count, "driver_count": driver_count},
        "clip": {"clip_id": str(clip["clip_id"]), "fps": actual_fps, "frame_start": float(clip["frame_start"]), "frame_end": float(clip["frame_end"]), "duration_seconds": duration_seconds, "loop": bool(clip["loop"]), "key_count": key_count},
        "nla": {"track_count": len(animation_data.nla_tracks), "strip_count": sum(len(item.strips) for item in animation_data.nla_tracks), "action_identity_bound": action_identity_bound, "active_action_cleared": active_action_cleared},
        "root_motion": {"policy": str(clip["root_motion"]), "translation_delta": root_delta},
        "artifact": {"filename": "animation_output.blend", "bytes": OUTPUT_BLEND.stat().st_size, "sha256": sha256_file(OUTPUT_BLEND)},
    }
    write_result(result)
    print("KODEPOIA_R10_7_RESULT=pass")
    return 0


try:
    raise SystemExit(main())
except Exception as exc:
    payload = {"schema": "kodepoia.blender.animation_measurements", "version": 1, "status": "fail", "blockers": [str(exc)[:256]], "mapping": {}, "rest_pose": {}, "sampling": {}, "clip": {}, "nla": {}, "root_motion": {}, "artifact": {}}
    write_result(payload)
    print("KODEPOIA_R10_7_RESULT=fail")
    raise SystemExit(17)
'''
