from __future__ import annotations

MESH_QA_BOOTSTRAP_SOURCE = r'''from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import bmesh
import bpy

ROOT = Path.cwd().resolve()
JOB = ROOT / "mesh_qa_job.json"
RESULT = ROOT / "mesh_qa_result.json"
RESULT_TMP = ROOT / "mesh_qa_result.tmp"
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


def finite_vector(values) -> bool:
    return all(math.isfinite(float(value)) for value in values)


def duplicate_indicators(mesh: bpy.types.Mesh, tolerance: float) -> int:
    buckets: dict[tuple[int, int, int], int] = {}
    duplicates = 0
    for vertex in mesh.vertices:
        if not finite_vector(vertex.co):
            continue
        key = tuple(round(float(value) / tolerance) for value in vertex.co)
        prior = buckets.get(key, 0)
        if prior:
            duplicates += 1
        buckets[key] = prior + 1
    return duplicates


def uv_measurements(mesh: bpy.types.Mesh, epsilon: float) -> tuple[dict[str, object], int]:
    mesh.calc_loop_triangles()
    layers: dict[str, object] = {}
    total_zero = 0
    for layer in mesh.uv_layers:
        zero = 0
        total_area = 0.0
        coords = [(float(item.uv.x), float(item.uv.y)) for item in layer.data]
        for triangle in mesh.loop_triangles:
            uv = [layer.data[index].uv for index in triangle.loops]
            ax, ay = float(uv[0].x), float(uv[0].y)
            bx, by = float(uv[1].x), float(uv[1].y)
            cx, cy = float(uv[2].x), float(uv[2].y)
            area = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax)) * 0.5
            total_area += area
            if area <= epsilon:
                zero += 1
        total_zero += zero
        if coords:
            xs = [item[0] for item in coords]
            ys = [item[1] for item in coords]
            bounds = [min(xs), min(ys), max(xs), max(ys)]
        else:
            bounds = None
        layers[layer.name] = {"loops": len(coords), "zero_area_triangles": zero, "triangle_area_sum": total_area, "bounds": bounds}
    return layers, total_zero


def topology_measurements(mesh: bpy.types.Mesh, profile: dict[str, object]) -> dict[str, object]:
    mesh.calc_loop_triangles()
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        minimum_area = float(profile["minimum_face_area"])
        degenerate = sum(1 for face in bm.faces if face.calc_area() <= minimum_area)
        loose_vertices = sum(1 for vertex in bm.verts if len(vertex.link_edges) == 0)
        loose_edges = sum(1 for edge in bm.edges if edge.is_wire)
        boundary_edges = sum(1 for edge in bm.edges if edge.is_boundary)
        non_manifold = sum(1 for edge in bm.edges if not edge.is_manifold and not edge.is_boundary and not edge.is_wire)
        inconsistent = sum(1 for edge in bm.edges if edge.is_manifold and not edge.is_contiguous)
    finally:
        bm.free()
    uv_layers, zero_uv = uv_measurements(mesh, float(profile["uv_zero_area_epsilon"]))
    material_slots = [material for material in mesh.materials if material is not None]
    texture_ids: set[int] = set()
    for material in material_slots:
        if not material.use_nodes or material.node_tree is None:
            continue
        for node in material.node_tree.nodes:
            if node.bl_idname == "ShaderNodeTexImage" and node.image is not None:
                texture_ids.add(int(node.image.as_pointer()))
    shape_keys = len(mesh.shape_keys.key_blocks) if mesh.shape_keys is not None else 0
    return {
        "vertices": len(mesh.vertices), "edges": len(mesh.edges), "faces": len(mesh.polygons), "triangles": len(mesh.loop_triangles),
        "finite_coordinates": all(finite_vector(vertex.co) for vertex in mesh.vertices), "degenerate_faces": degenerate,
        "loose_vertices": loose_vertices, "loose_edges": loose_edges, "boundary_edges": boundary_edges,
        "non_manifold_edges": non_manifold, "inconsistent_winding_edges": inconsistent,
        "duplicate_vertex_indicators": duplicate_indicators(mesh, float(profile["duplicate_tolerance"])),
        "uv_layer_count": len(mesh.uv_layers), "uv_layers": uv_layers, "zero_area_uv_triangles": zero_uv,
        "materials": len(material_slots), "textures": len(texture_ids), "shape_keys": shape_keys,
    }


def normal_map_requirements(obj: bpy.types.Object) -> list[dict[str, object]]:
    requirements: list[dict[str, object]] = []
    mesh = obj.data
    for material in mesh.materials:
        if material is None or not material.use_nodes or material.node_tree is None:
            continue
        material_id = material.get("kodepoia_material_id")
        for node in material.node_tree.nodes:
            if node.bl_idname != "ShaderNodeNormalMap":
                continue
            uv_map = str(getattr(node, "uv_map", "") or "")
            if not uv_map and mesh.uv_layers.active is not None:
                uv_map = mesh.uv_layers.active.name
            status = "fail"
            reason = "tangent_calculation_failed"
            if uv_map and mesh.uv_layers.get(uv_map) is not None:
                temp = mesh.copy()
                try:
                    temp.calc_tangents(uvmap=uv_map)
                    tangent_values = [loop.tangent for loop in temp.loops]
                    if tangent_values and all(finite_vector(value) and float(value.length) > 1e-12 for value in tangent_values):
                        status = "pass"
                        reason = "tangent_basis_valid"
                    else:
                        reason = "tangent_basis_nonfinite_or_zero"
                except Exception:
                    reason = "tangent_calculation_failed"
                finally:
                    bpy.data.meshes.remove(temp)
            else:
                reason = "normal_map_uv_missing"
            requirements.append({"material_id": str(material_id) if isinstance(material_id, str) else material.name, "uv_map": uv_map, "tangent_status": status, "reason": reason})
    return sorted(requirements, key=lambda item: (str(item["material_id"]), str(item["uv_map"])))


def transform_measurements(obj: bpy.types.Object) -> dict[str, object]:
    matrix_values = [float(value) for row in obj.matrix_world for value in row]
    scale = [abs(float(value)) for value in obj.scale]
    finite = all(math.isfinite(value) for value in matrix_values + scale)
    minimum = min(scale, default=0.0)
    maximum = max(scale, default=0.0)
    ratio = maximum / minimum if finite and minimum > 1e-12 else 1e308
    return {"finite": finite, "scale": scale, "scale_ratio": ratio}


payload: dict[str, object]
try:
    job = json.loads(JOB.read_text(encoding="utf-8"))
    profile = dict(job["profile"])
    bpy.ops.wm.open_mainfile(filepath=str(INPUT_BLEND), load_ui=False, use_scripts=False)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    objects: dict[str, object] = {}
    for object_id in profile["object_ids"]:
        matches = [item for item in bpy.data.objects if item.type == "MESH" and item.get("kodepoia_id") == object_id]
        if len(matches) != 1:
            continue
        obj = matches[0]
        evaluated_obj = obj.evaluated_get(depsgraph)
        evaluated_mesh = evaluated_obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
        try:
            objects[str(object_id)] = {
                "source": topology_measurements(obj.data, profile),
                "evaluated": topology_measurements(evaluated_mesh, profile),
                "transform": transform_measurements(obj),
                "normal_maps": normal_map_requirements(obj),
                "uv_overlap": {"status": "not_measured", "reason": "bounded_runtime_policy"},
            }
        finally:
            evaluated_obj.to_mesh_clear()
    payload = {
        "schema": "kodepoia.blender.mesh_qa_measurements", "version": 1, "status": "pass", "blockers": [],
        "profile_digest": str(job["profile_digest"]), "input_blend_sha256": str(job["input_blend_sha256"]),
        "input_file_sha256": sha256_file(INPUT_BLEND), "objects": objects,
    }
except Exception as exc:
    payload = {
        "schema": "kodepoia.blender.mesh_qa_measurements", "version": 1, "status": "fail",
        "blockers": ["mesh_qa_measurement_exception"], "profile_digest": None, "input_blend_sha256": None,
        "input_file_sha256": None, "objects": {}, "error_type": type(exc).__name__,
        "error_message": str(exc).replace(str(ROOT), "<WORKSPACE>")[:512],
    }
write_result(payload)
print("KODEPOIA_R10_5_RESULT=" + str(payload["status"]))
raise SystemExit(0 if payload["status"] == "pass" else 17)
'''
