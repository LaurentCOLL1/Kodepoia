from __future__ import annotations

RIG_BOOTSTRAP_SOURCE = r'''from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path.cwd().resolve()
JOB = ROOT / "rig_job.json"
RESULT = ROOT / "rig_result.json"
RESULT_TMP = ROOT / "rig_result.tmp"
INPUT_BLEND = ROOT / "input.blend"
OUTPUT_BLEND = ROOT / "rig_output.blend"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_result(payload: dict[str, object]) -> None:
    RESULT_TMP.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    os.replace(RESULT_TMP, RESULT)


def get_mesh(mesh_id: str) -> bpy.types.Object:
    matches = [item for item in bpy.data.objects if item.type == "MESH" and item.get("kodepoia_id") == mesh_id]
    if len(matches) != 1:
        raise RuntimeError("mesh_identity_resolution_failed:" + mesh_id)
    return matches[0]


def get_armature(armature_id: str) -> bpy.types.Object:
    matches = [item for item in bpy.data.objects if item.type == "ARMATURE" and item.get("kodepoia_id") == armature_id]
    if len(matches) != 1:
        raise RuntimeError("armature_identity_resolution_failed:" + armature_id)
    return matches[0]


def create_armature(profile: dict[str, object]) -> bpy.types.Object:
    armature_id = str(profile["armature_id"])
    if any(item.get("kodepoia_id") == armature_id for item in bpy.data.objects):
        raise RuntimeError("armature_id_collision")
    data = bpy.data.armatures.new("kdp_armature_data_" + str(profile["rig_id"]))
    obj = bpy.data.objects.new("kdp_armature_" + str(profile["rig_id"]), data)
    obj["kodepoia_id"] = armature_id
    obj["kodepoia_rig_id"] = str(profile["rig_id"])
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    created = {}
    try:
        for spec in profile["bones"]:
            spec = dict(spec)
            bone_id = str(spec["bone_id"])
            bone = data.edit_bones.new(bone_id)
            bone.head = tuple(float(v) for v in spec["head"])
            bone.tail = tuple(float(v) for v in spec["tail"])
            parent_id = spec["parent_id"]
            if parent_id is not None:
                bone.parent = created[str(parent_id)]
                bone.use_connect = bool(spec["connected"])
            created[bone_id] = bone
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
    by_id = {str(spec["bone_id"]): dict(spec) for spec in profile["bones"]}
    for bone in data.bones:
        spec = by_id[bone.name]
        bone["kodepoia_bone_id"] = bone.name
        bone["kodepoia_display_name"] = str(spec["display_name"])
        bone.use_deform = bool(spec["deform"])
    return obj


def point_segment_distance(point: Vector, head: Vector, tail: Vector) -> float:
    delta = tail - head
    denom = delta.length_squared
    if denom <= 1e-20:
        return (point - head).length
    t = max(0.0, min(1.0, (point - head).dot(delta) / denom))
    return (point - (head + delta * t)).length


def ensure_group(mesh: bpy.types.Object, name: str):
    if mesh.vertex_groups.get(name) is not None:
        raise RuntimeError("vertex_group_collision:" + name)
    return mesh.vertex_groups.new(name=name)


def bind_created_mesh(mesh: bpy.types.Object, armature: bpy.types.Object, spec: dict[str, object], profile: dict[str, object], normalized: dict[str, object]) -> None:
    if mesh.modifiers.get("kdp_armature_" + str(profile["rig_id"])) is not None:
        raise RuntimeError("armature_modifier_collision")
    deform_specs = [dict(item) for item in profile["bones"] if bool(dict(item)["deform"])]
    groups = {str(item["bone_id"]): ensure_group(mesh, str(item["bone_id"])) for item in deform_specs}
    strategy = str(spec["strategy"])
    if strategy == "explicit":
        for row in normalized.get(str(spec["mesh_id"]), []):
            row = dict(row)
            vertex = int(row["vertex"])
            if vertex < 0 or vertex >= len(mesh.data.vertices):
                raise RuntimeError("explicit_vertex_out_of_range")
            for influence in row["influences"]:
                influence = dict(influence)
                groups[str(influence["bone_id"])].add([vertex], float(influence["weight"]), "REPLACE")
    elif strategy == "nearest_deform_bone":
        transform = armature.matrix_world.inverted() @ mesh.matrix_world
        segments = [(str(item["bone_id"]), Vector(item["head"]), Vector(item["tail"])) for item in deform_specs]
        for vertex in mesh.data.vertices:
            point = transform @ vertex.co
            nearest = min(segments, key=lambda item: (point_segment_distance(point, item[1], item[2]), item[0]))
            groups[nearest[0]].add([vertex.index], 1.0, "REPLACE")
    else:
        raise RuntimeError("unexpected_create_weight_strategy")
    modifier = mesh.modifiers.new(name="kdp_armature_" + str(profile["rig_id"]), type="ARMATURE")
    modifier.object = armature
    modifier.use_vertex_groups = True
    modifier.use_bone_envelopes = False
    world = mesh.matrix_world.copy()
    mesh.parent = armature
    mesh.matrix_world = world


def bone_mapping(armature: bpy.types.Object) -> tuple[dict[str, str], dict[str, bool]]:
    actual_to_semantic: dict[str, str] = {}
    deform: dict[str, bool] = {}
    for bone in armature.data.bones:
        semantic = bone.get("kodepoia_bone_id")
        if isinstance(semantic, str):
            actual_to_semantic[bone.name] = semantic
            deform[semantic] = bool(bone.use_deform)
    return actual_to_semantic, deform


def deformation_probe(mesh: bpy.types.Object, armature: bpy.types.Object, actual_to_semantic: dict[str, str], deform: dict[str, bool]) -> dict[str, object]:
    group_by_index = {group.index: group.name for group in mesh.vertex_groups}
    weight_by_actual: dict[str, float] = {}
    for vertex in mesh.data.vertices:
        for ref in vertex.groups:
            name = group_by_index.get(ref.group)
            if name in actual_to_semantic and deform.get(actual_to_semantic[name], False):
                weight_by_actual[name] = weight_by_actual.get(name, 0.0) + float(ref.weight)
    candidates = sorted(name for name, total in weight_by_actual.items() if total > 0.0 and armature.pose.bones.get(name) is not None)
    if not candidates:
        return {"status": "fail", "moved_vertices": 0, "reason": "no_weighted_deform_bone"}
    pose = armature.pose.bones[candidates[0]]
    old_mode = pose.rotation_mode
    pose.rotation_mode = "XYZ"
    old_rotation = tuple(float(value) for value in pose.rotation_euler)
    original = [mesh.matrix_world @ vertex.co for vertex in mesh.data.vertices]
    try:
        pose.rotation_euler.z += 0.17320508075688773
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = mesh.evaluated_get(depsgraph)
        evaluated_mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
        try:
            moved = sum(1 for index, vertex in enumerate(evaluated_mesh.vertices) if index < len(original) and ((mesh.matrix_world @ vertex.co) - original[index]).length > 1e-7)
        finally:
            evaluated.to_mesh_clear()
    finally:
        pose.rotation_euler = old_rotation
        pose.rotation_mode = old_mode
        bpy.context.view_layer.update()
    return {"status": "pass" if moved > 0 else "fail", "moved_vertices": moved, "reason": "weighted_geometry_moved" if moved > 0 else "no_geometry_movement"}


def measure_armature(armature: bpy.types.Object) -> dict[str, object]:
    bones = []
    for bone in armature.data.bones:
        semantic = bone.get("kodepoia_bone_id")
        if not isinstance(semantic, str):
            continue
        parent_semantic = bone.parent.get("kodepoia_bone_id") if bone.parent is not None else None
        bones.append({"bone_id": semantic, "actual_name": bone.name, "parent_id": parent_semantic if isinstance(parent_semantic, str) else None, "deform": bool(bone.use_deform), "connected": bool(bone.use_connect)})
    return {"object_id": armature.get("kodepoia_id"), "rig_id": armature.get("kodepoia_rig_id"), "bones": sorted(bones, key=lambda item: str(item["bone_id"]))}


def measure_mesh(mesh: bpy.types.Object, armature: bpy.types.Object, profile: dict[str, object]) -> dict[str, object]:
    actual_to_semantic, deform = bone_mapping(armature)
    expected = {str(item["bone_id"]) for item in profile["bones"]}
    group_by_index = {group.index: group.name for group in mesh.vertex_groups}
    orphan_names = {name for name in group_by_index.values() if name not in actual_to_semantic}
    tolerance = float(dict(profile["influence"])["normalization_tolerance"])
    threshold = float(dict(profile["influence"])["tiny_weight_threshold"])
    max_allowed = int(dict(profile["influence"])["max_influences"])
    zero = invalid = control = bad_sum = over = tiny = 0
    max_observed = 0
    weighted_vertices = 0
    for vertex in mesh.data.vertices:
        weights = []
        for ref in vertex.groups:
            name = group_by_index.get(ref.group)
            if name not in actual_to_semantic:
                continue
            semantic = actual_to_semantic[name]
            value = float(ref.weight)
            if semantic not in expected:
                invalid += 1
                continue
            if not deform.get(semantic, False) and value > 0.0:
                control += 1
                continue
            if value > 0.0:
                weights.append(value)
                if value < threshold:
                    tiny += 1
        count = len(weights)
        max_observed = max(max_observed, count)
        if count == 0:
            zero += 1
        else:
            weighted_vertices += 1
            if abs(sum(weights) - 1.0) > tolerance:
                bad_sum += 1
            if count > max_allowed:
                over += 1
    modifier_bound = any(mod.type == "ARMATURE" and mod.object is armature and bool(mod.use_vertex_groups) for mod in mesh.modifiers)
    parent_bound = mesh.parent is armature
    probe = deformation_probe(mesh, armature, actual_to_semantic, deform) if bool(dict(profile["influence"])["require_deformation_probe"]) else {"status": "not_required", "moved_vertices": 0, "reason": "profile_disabled"}
    return {"vertex_count": len(mesh.data.vertices), "weighted_vertices": weighted_vertices, "zero_weight_vertices": zero, "invalid_bone_references": invalid, "control_bone_references": control, "sum_outside_tolerance": bad_sum, "influence_over_budget": over, "max_influences": max_observed, "tiny_weight_count": tiny, "orphan_vertex_groups": len(orphan_names), "orphan_group_names": sorted(orphan_names), "armature_modifier_bound": modifier_bound, "parent_bound": parent_bound, "deformation_probe": probe}


payload: dict[str, object]
try:
    job = json.loads(JOB.read_text(encoding="utf-8"))
    profile = dict(job["profile"])
    bpy.ops.wm.open_mainfile(filepath=str(INPUT_BLEND), load_ui=False, use_scripts=False)
    if str(profile["mode"]) == "create":
        armature = create_armature(profile)
        by_mesh = {str(item["mesh_id"]): dict(item) for item in profile["meshes"]}
        normalized = dict(job.get("normalized_explicit_weights", {}))
        for mesh_id, spec in by_mesh.items():
            bind_created_mesh(get_mesh(mesh_id), armature, spec, profile, normalized)
    else:
        armature = get_armature(str(profile["armature_id"]))
    mesh_records = {str(spec["mesh_id"]): measure_mesh(get_mesh(str(spec["mesh_id"])), armature, profile) for spec in profile["meshes"]}
    armature_record = measure_armature(armature)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
    payload = {"schema": "kodepoia.blender.rig_measurements", "version": 1, "status": "pass", "blockers": [], "profile_digest": str(job["profile_digest"]), "input_blend_sha256": str(job["input_blend_sha256"]), "input_file_sha256": sha256_file(INPUT_BLEND), "armature": armature_record, "meshes": mesh_records, "artifact": {"filename": OUTPUT_BLEND.name, "bytes": OUTPUT_BLEND.stat().st_size, "sha256": sha256_file(OUTPUT_BLEND)}}
except Exception as exc:
    payload = {"schema": "kodepoia.blender.rig_measurements", "version": 1, "status": "fail", "blockers": ["rig_exception"], "profile_digest": None, "input_blend_sha256": None, "input_file_sha256": None, "armature": {}, "meshes": {}, "artifact": None, "error_type": type(exc).__name__, "error_message": str(exc).replace(str(ROOT), "<WORKSPACE>")[:512]}
write_result(payload)
print("KODEPOIA_R10_6_RESULT=" + str(payload["status"]))
raise SystemExit(0 if payload["status"] == "pass" else 17)
'''
