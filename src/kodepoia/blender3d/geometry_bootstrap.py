from __future__ import annotations

GEOMETRY_BOOTSTRAP_SOURCE = r'''from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import bmesh
import bpy

ROOT = Path.cwd().resolve()
JOB = ROOT / "geometry_job.json"
RESULT = ROOT / "geometry_result.json"
RESULT_TMP = ROOT / "geometry_result.tmp"
OUTPUT_BLEND = ROOT / "geometry_output.blend"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_result(payload: dict[str, object]) -> None:
    RESULT_TMP.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    os.replace(RESULT_TMP, RESULT)


def activate(target: bpy.types.Object) -> None:
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    target.select_set(True)
    bpy.context.view_layer.objects.active = target


def get_object(object_id: str) -> bpy.types.Object:
    matches = [item for item in bpy.data.objects if item.get("kodepoia_id") == object_id]
    if len(matches) != 1:
        raise RuntimeError("object_resolution_failed:" + object_id)
    return matches[0]


def create_mesh(object_id: str, primitive: str, display_name: str) -> bpy.types.Object:
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, ...]]
    if primitive == "cube":
        vertices = [(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)]
        faces = [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(4,0,3,7)]
    elif primitive == "plane":
        vertices = [(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)]
        faces = [(0,1,2,3)]
    elif primitive == "cylinder":
        segments = 16
        vertices = []
        for z in (-.5, .5):
            for index in range(segments):
                angle = 2.0 * math.pi * index / segments
                vertices.append((.5 * math.cos(angle), .5 * math.sin(angle), z))
        faces = [tuple(range(segments - 1, -1, -1)), tuple(range(segments, segments * 2))]
        for index in range(segments):
            nxt = (index + 1) % segments
            faces.append((index, nxt, segments + nxt, segments + index))
    else:
        raise RuntimeError("primitive_not_supported")
    mesh = bpy.data.meshes.new("KDP_MESH_" + object_id)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(display_name, mesh)
    obj["kodepoia_id"] = object_id
    bpy.context.scene.collection.objects.link(obj)
    return obj


def bmesh_edit(target: bpy.types.Object, operation: str, params: dict[str, object]) -> None:
    mesh = target.data
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        if operation == "triangulate":
            bmesh.ops.triangulate(
                bm,
                faces=list(bm.faces),
                quad_method=str(params.get("quad_method", "FIXED")),
                ngon_method=str(params.get("ngon_method", "EAR_CLIP")),
            )
        elif operation == "recalculate_normals":
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        else:
            raise RuntimeError("bmesh_operation_not_supported")
        bm.to_mesh(mesh)
        mesh.update()
        mesh.calc_loop_triangles()
    finally:
        bm.free()


def add_modifier(target: bpy.types.Object, params: dict[str, object]) -> None:
    name = str(params["name"])
    kind = str(params["modifier"])
    settings = dict(params["settings"])
    mapping = {"triangulate":"TRIANGULATE","mirror":"MIRROR","solidify":"SOLIDIFY","bevel":"BEVEL"}
    modifier = target.modifiers.new(name=name, type=mapping[kind])
    if kind == "triangulate":
        modifier.quad_method = str(settings.get("quad_method", "FIXED"))
        modifier.ngon_method = str(settings.get("ngon_method", "BEAUTY"))
        modifier.keep_custom_normals = bool(settings.get("keep_custom_normals", False))
        modifier.min_vertices = int(settings.get("min_vertices", 4))
    elif kind == "mirror":
        axis = str(settings.get("axis", "X"))
        modifier.use_axis = (axis == "X", axis == "Y", axis == "Z")
        modifier.use_clip = False
        modifier.use_mirror_merge = bool(settings.get("merge", True))
        modifier.merge_threshold = float(settings.get("merge_threshold", 0.001))
    elif kind == "solidify":
        modifier.thickness = float(settings.get("thickness", 0.01))
        modifier.offset = float(settings.get("offset", 0.0))
    elif kind == "bevel":
        modifier.width = float(settings.get("width", 0.01))
        modifier.segments = int(settings.get("segments", 1))


def mesh_stats(target: bpy.types.Object) -> dict[str, object]:
    mesh = target.data
    mesh.calc_loop_triangles()
    source = {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "faces": len(mesh.polygons),
        "triangles": len(mesh.loop_triangles),
        "modifiers": [item.type for item in target.modifiers],
    }
    evaluated_obj = target.evaluated_get(bpy.context.evaluated_depsgraph_get())
    evaluated_mesh = evaluated_obj.to_mesh()
    try:
        evaluated_mesh.calc_loop_triangles()
        evaluated = {
            "vertices": len(evaluated_mesh.vertices),
            "edges": len(evaluated_mesh.edges),
            "faces": len(evaluated_mesh.polygons),
            "triangles": len(evaluated_mesh.loop_triangles),
        }
    finally:
        evaluated_obj.to_mesh_clear()
    return {"source": source, "evaluated": evaluated}


def run_step(step: dict[str, object]) -> None:
    operation = str(step["operation"])
    params = dict(step["params"])
    if operation == "reset_scene":
        for item in list(bpy.data.objects):
            bpy.data.objects.remove(item, do_unlink=True)
        return
    if operation == "create_primitive":
        create_mesh(str(params["object_id"]), str(params["primitive"]), str(params.get("display_name", params["object_id"])))
        return
    target = get_object(str(params["object_id"]))
    if operation == "transform":
        if "location" in params: target.location = tuple(float(v) for v in params["location"])
        if "rotation" in params: target.rotation_euler = tuple(float(v) for v in params["rotation"])
        if "scale" in params: target.scale = tuple(float(v) for v in params["scale"])
    elif operation == "apply_transform":
        activate(target)
        bpy.ops.object.transform_apply(
            location=bool(params.get("location", False)),
            rotation=bool(params.get("rotation", False)),
            scale=bool(params.get("scale", False)),
        )
    elif operation in {"triangulate", "recalculate_normals"}:
        bmesh_edit(target, operation, params)
    elif operation == "add_modifier":
        add_modifier(target, params)
    elif operation == "apply_modifier":
        activate(target)
        bpy.ops.object.modifier_apply(modifier=str(params["name"]))
    elif operation == "join":
        activate(target)
        for source_id in params["sources"]:
            get_object(str(source_id)).select_set(True)
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.join()
    elif operation == "separate_loose":
        activate(target)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.separate(type="LOOSE")
        bpy.ops.object.mode_set(mode="OBJECT")
        selected = sorted([item for item in bpy.context.selected_objects if item.type == "MESH"], key=lambda item: (len(item.data.vertices), item.name))
        new_ids = list(params["new_object_ids"])
        if len(selected) != len(new_ids) + 1:
            raise RuntimeError("separate_loose_output_count_mismatch")
        target["kodepoia_id"] = str(params["object_id"])
        others = [item for item in selected if item != target]
        for item, object_id in zip(others, new_ids, strict=True):
            item["kodepoia_id"] = str(object_id)
    elif operation == "set_origin":
        activate(target)
        mode = str(params["mode"])
        if mode == "CURSOR_ZERO":
            bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
            bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        else:
            bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")
    else:
        raise RuntimeError("operation_not_supported")


payload: dict[str, object]
try:
    job = json.loads(JOB.read_text(encoding="utf-8"))
    recipe = dict(job["recipe"])
    for step in recipe["steps"]:
        run_step(dict(step))
    objects = sorted(
        [item for item in bpy.data.objects if item.type == "MESH" and isinstance(item.get("kodepoia_id"), str)],
        key=lambda item: str(item.get("kodepoia_id")),
    )
    stats = {str(item.get("kodepoia_id")): mesh_stats(item) for item in objects}
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
    payload = {
        "schema": "kodepoia.blender.geometry_result",
        "version": 1,
        "status": "pass",
        "blockers": [],
        "recipe_digest": str(job["recipe_digest"]),
        "objects": stats,
        "artifact": {"filename": OUTPUT_BLEND.name, "bytes": OUTPUT_BLEND.stat().st_size, "sha256": sha256_file(OUTPUT_BLEND)},
    }
except Exception as exc:
    payload = {
        "schema": "kodepoia.blender.geometry_result",
        "version": 1,
        "status": "fail",
        "blockers": ["geometry_exception"],
        "recipe_digest": None,
        "objects": {},
        "artifact": None,
        "error_type": type(exc).__name__,
        "error_message": str(exc).replace(str(ROOT), "<WORKSPACE>")[:512],
    }

write_result(payload)
print("KODEPOIA_R10_3_RESULT=" + str(payload["status"]))
raise SystemExit(0 if payload["status"] == "pass" else 17)
'''
