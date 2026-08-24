from __future__ import annotations

LOD_BOOTSTRAP_SOURCE = r'''from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import bpy

ROOT = Path.cwd().resolve()
JOB = ROOT / "lod_job.json"
RESULT = ROOT / "lod_result.json"
RESULT_TMP = ROOT / "lod_result.tmp"
INPUT_BLEND = ROOT / "input.blend"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_result(payload: dict[str, object]) -> None:
    RESULT_TMP.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    os.replace(RESULT_TMP, RESULT)


def governed_mesh(object_id: str):
    matches = [item for item in bpy.data.objects if item.type == "MESH" and item.get("kodepoia_id") == object_id]
    if len(matches) != 1:
        raise RuntimeError("lod_mesh_identity_resolution_failed:" + object_id)
    return matches[0]


def triangle_count(obj) -> int:
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def inventory(obj, required_groups: list[str]) -> dict[str, object]:
    mesh = obj.data
    triangles = triangle_count(obj)
    materials = [slot.material.name if slot.material is not None else "" for slot in obj.material_slots]
    uv_layers = [layer.name for layer in mesh.uv_layers]
    shapes = [] if mesh.shape_keys is None else [key.name for key in mesh.shape_keys.key_blocks]
    groups = [group.name for group in obj.vertex_groups]
    coords = [vertex.co for vertex in mesh.vertices]
    if coords:
        extent = [max(v[i] for v in coords) - min(v[i] for v in coords) for i in range(3)]
    else:
        extent = [0.0, 0.0, 0.0]
    surface_area = sum(float(poly.area) for poly in mesh.polygons)
    invalid_normals = 0
    for poly in mesh.polygons:
        normal = poly.normal
        if not all(math.isfinite(float(normal[i])) for i in range(3)) or float(normal.length) <= 1e-12:
            invalid_normals += 1
    required = set(required_groups)
    group_by_index = {group.index: group.name for group in obj.vertex_groups}
    zero_weight = 0
    max_influences = 0
    max_sum_error = 0.0
    if required:
        for vertex in mesh.vertices:
            weights = [float(ref.weight) for ref in vertex.groups if group_by_index.get(ref.group) in required and float(ref.weight) > 0.0]
            max_influences = max(max_influences, len(weights))
            if not weights:
                zero_weight += 1
            else:
                max_sum_error = max(max_sum_error, abs(sum(weights) - 1.0))
    return {"triangle_count": triangles, "material_slots": materials, "uv_layers": uv_layers, "shape_keys": shapes, "vertex_groups": groups, "bounds_extent": [float(value) for value in extent], "surface_area": surface_area, "invalid_normal_count": invalid_normals, "zero_weight_vertices": zero_weight, "max_influences": max_influences, "max_weight_sum_error": max_sum_error}


def open_source() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(INPUT_BLEND), load_ui=False, use_scripts=False)


def main() -> None:
    job = json.loads(JOB.read_text(encoding="utf-8"))
    profile = dict(job["profile"])
    object_id = str(profile["source_object_id"])
    preservation = dict(profile["preservation"])
    required_groups = [str(item) for item in preservation["required_vertex_groups"]]
    open_source()
    source_obj = governed_mesh(object_id)
    source_inventory = inventory(source_obj, required_groups)
    source_shapes = list(source_inventory["shape_keys"])
    if source_shapes and str(preservation["shape_keys"]) == "block_if_present":
        write_result({"schema": "kodepoia.blender.lod_measurements", "version": 1, "status": "fail", "blockers": ["source_shape_keys_block_decimation"], "profile_digest": str(job["profile_digest"]), "input_blend_sha256": str(job["input_blend_sha256"]), "input_file_sha256": sha256_file(INPUT_BLEND), "source": source_inventory, "tiers": {}, "artifacts": []})
        return

    tiers: dict[str, object] = {}
    artifacts: list[dict[str, object]] = []
    for tier_raw in profile["tiers"]:
        tier = dict(tier_raw)
        tier_id = str(tier["tier_id"])
        open_source()
        obj = governed_mesh(object_id)
        if obj.data.shape_keys is not None and str(preservation["shape_keys"]) == "drop_explicit":
            obj.shape_key_clear()
        modifier = obj.modifiers.new(name="kdp_lod_" + tier_id, type="DECIMATE")
        modifier.decimate_type = "COLLAPSE"
        modifier.ratio = float(tier["ratio"])
        modifier.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = obj
        for candidate in bpy.context.selected_objects:
            candidate.select_set(False)
        obj.select_set(True)
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.context.view_layer.update()
        tiers[tier_id] = inventory(obj, required_groups)
        output = ROOT / ("lod_" + tier_id + ".blend")
        bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
        artifacts.append({"tier_id": tier_id, "filename": output.name, "bytes": output.stat().st_size, "sha256": sha256_file(output)})

    write_result({"schema": "kodepoia.blender.lod_measurements", "version": 1, "status": "pass", "blockers": [], "profile_digest": str(job["profile_digest"]), "input_blend_sha256": str(job["input_blend_sha256"]), "input_file_sha256": sha256_file(INPUT_BLEND), "source": source_inventory, "tiers": tiers, "artifacts": artifacts})


try:
    main()
    print("KODEPOIA_R10_9_RESULT=pass")
except Exception as exc:
    write_result({"schema": "kodepoia.blender.lod_measurements", "version": 1, "status": "fail", "blockers": ["lod_runtime_exception:" + type(exc).__name__], "profile_digest": "", "input_blend_sha256": "", "input_file_sha256": sha256_file(INPUT_BLEND) if INPUT_BLEND.is_file() else "", "source": {}, "tiers": {}, "artifacts": []})
    raise
'''
