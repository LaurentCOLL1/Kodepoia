from __future__ import annotations

PBR_BOOTSTRAP_SOURCE = r'''from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import bpy

ROOT = Path.cwd().resolve()
JOB = ROOT / "pbr_job.json"
RESULT = ROOT / "pbr_result.json"
RESULT_TMP = ROOT / "pbr_result.tmp"
INPUT_BLEND = ROOT / "input.blend"
OUTPUT_BLEND = ROOT / "pbr_output.blend"
TEXTURES = ROOT / "textures"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_result(payload: dict[str, object]) -> None:
    RESULT_TMP.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    os.replace(RESULT_TMP, RESULT)


def get_object(object_id: str) -> bpy.types.Object:
    matches = [item for item in bpy.data.objects if item.type == "MESH" and item.get("kodepoia_id") == object_id]
    if len(matches) != 1:
        raise RuntimeError("object_resolution_failed:" + object_id)
    return matches[0]


def activate(target: bpy.types.Object) -> None:
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    target.select_set(True)
    bpy.context.view_layer.objects.active = target


def ensure_uv(target: bpy.types.Object, spec: dict[str, object]) -> None:
    name = str(spec["map_name"])
    method = str(spec["method"])
    layer = target.data.uv_layers.get(name)
    if method == "keep":
        if layer is None:
            raise RuntimeError("required_uv_missing:" + name)
        target.data.uv_layers.active = layer
        return
    if layer is None:
        layer = target.data.uv_layers.new(name=name, do_init=False)
    target.data.uv_layers.active = layer
    activate(target)
    bpy.ops.object.mode_set(mode="EDIT")
    try:
        bpy.ops.mesh.select_all(action="SELECT")
        margin = float(spec["margin"])
        if method == "smart":
            bpy.ops.uv.smart_project(
                angle_limit=float(spec["angle_limit"]),
                margin_method="ADD",
                rotate_method="AXIS_ALIGNED_Y",
                island_margin=margin,
                area_weight=0.0,
                correct_aspect=True,
                scale_to_bounds=True,
            )
        elif method in {"angle_based", "conformal"}:
            bpy.ops.uv.unwrap(
                method="ANGLE_BASED" if method == "angle_based" else "CONFORMAL",
                fill_holes=True,
                correct_aspect=True,
                margin_method="ADD",
                margin=margin,
                no_flip=True,
            )
        else:
            raise RuntimeError("uv_method_unsupported")
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")


def image_for(source_id: str, role: str) -> bpy.types.Image:
    entries = list(TEXTURES.glob(source_id + ".*"))
    if len(entries) != 1:
        raise RuntimeError("texture_binding_missing:" + source_id)
    image = bpy.data.images.load(str(entries[0]), check_existing=False)
    if role in {"metallic", "roughness", "normal"}:
        image.colorspace_settings.is_data = True
    else:
        image.colorspace_settings.is_data = False
    image["kodepoia_source_id"] = source_id
    image["kodepoia_role"] = role
    return image


def input_socket(node: bpy.types.Node, *names: str):
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            return socket
    raise RuntimeError("principled_socket_missing:" + names[0])


def make_material(spec: dict[str, object]) -> bpy.types.Material:
    material_id = str(spec["material_id"])
    material = bpy.data.materials.new("KDP_MAT_" + material_id)
    material["kodepoia_material_id"] = material_id
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    material.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    input_socket(principled, "Base Color").default_value = tuple(float(v) for v in spec["base_color"])
    input_socket(principled, "Metallic").default_value = float(spec["metallic"])
    input_socket(principled, "Roughness").default_value = float(spec["roughness"])
    input_socket(principled, "Alpha").default_value = float(spec["alpha"])
    input_socket(principled, "Emission Color", "Emission").default_value = (*tuple(float(v) for v in spec["emission_color"]), 1.0)
    input_socket(principled, "Emission Strength").default_value = float(spec["emission_strength"])

    for texture in spec["textures"]:
        texture = dict(texture)
        role = str(texture["role"])
        uv = nodes.new("ShaderNodeUVMap")
        uv.uv_map = str(texture["uv_map"])
        image_node = nodes.new("ShaderNodeTexImage")
        image_node.image = image_for(str(texture["source_id"]), role)
        image_node.interpolation = "Linear"
        material.node_tree.links.new(uv.outputs["UV"], image_node.inputs["Vector"])
        if role == "base_color":
            material.node_tree.links.new(image_node.outputs["Color"], input_socket(principled, "Base Color"))
            material.node_tree.links.new(image_node.outputs["Alpha"], input_socket(principled, "Alpha"))
        elif role == "metallic":
            material.node_tree.links.new(image_node.outputs["Color"], input_socket(principled, "Metallic"))
        elif role == "roughness":
            material.node_tree.links.new(image_node.outputs["Color"], input_socket(principled, "Roughness"))
        elif role == "emissive":
            material.node_tree.links.new(image_node.outputs["Color"], input_socket(principled, "Emission Color", "Emission"))
        elif role == "normal":
            normal = nodes.new("ShaderNodeNormalMap")
            normal.space = "TANGENT"
            normal.inputs["Strength"].default_value = float(spec["normal_strength"])
            normal.uv_map = str(texture["uv_map"])
            material.node_tree.links.new(image_node.outputs["Color"], normal.inputs["Color"])
            material.node_tree.links.new(normal.outputs["Normal"], input_socket(principled, "Normal"))
        else:
            raise RuntimeError("texture_role_unsupported")
    return material


def uv_stats(target: bpy.types.Object) -> dict[str, object]:
    result: dict[str, object] = {}
    for layer in target.data.uv_layers:
        coords = [(float(item.uv.x), float(item.uv.y)) for item in layer.data]
        if coords:
            xs = [item[0] for item in coords]
            ys = [item[1] for item in coords]
            bounds = [min(xs), min(ys), max(xs), max(ys)]
        else:
            bounds = None
        result[layer.name] = {"loops": len(coords), "bounds": bounds}
    return result


def material_stats(material: bpy.types.Material) -> dict[str, object]:
    nodes = list(material.node_tree.nodes) if material.use_nodes and material.node_tree else []
    images = []
    for node in nodes:
        if node.bl_idname == "ShaderNodeTexImage" and node.image is not None:
            images.append({
                "source_id": node.image.get("kodepoia_source_id"),
                "role": node.image.get("kodepoia_role"),
                "is_data": bool(node.image.colorspace_settings.is_data),
            })
    return {"node_types": sorted(node.bl_idname for node in nodes), "textures": sorted(images, key=lambda item: str(item["role"]))}


payload: dict[str, object]
try:
    job = json.loads(JOB.read_text(encoding="utf-8"))
    bpy.ops.wm.open_mainfile(filepath=str(INPUT_BLEND), load_ui=False, use_scripts=False)
    recipe = dict(job["recipe"])
    for spec in recipe["uv"]:
        ensure_uv(get_object(str(spec["object_id"])), dict(spec))
    material_manifest: dict[str, object] = {}
    for spec in recipe["materials"]:
        spec = dict(spec)
        material = make_material(spec)
        for object_id in spec["object_ids"]:
            target = get_object(str(object_id))
            target.data.materials.clear()
            target.data.materials.append(material)
        material_manifest[str(spec["material_id"])] = material_stats(material)
    object_manifest = {
        str(item.get("kodepoia_id")): {"uv": uv_stats(item), "materials": [mat.get("kodepoia_material_id") for mat in item.data.materials]}
        for item in bpy.data.objects if item.type == "MESH" and isinstance(item.get("kodepoia_id"), str)
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
    payload = {
        "schema": "kodepoia.blender.pbr_result",
        "version": 1,
        "status": "pass",
        "blockers": [],
        "recipe_digest": str(job["recipe_digest"]),
        "input_blend_sha256": str(job["input_blend_sha256"]),
        "objects": object_manifest,
        "materials": material_manifest,
        "artifact": {"filename": OUTPUT_BLEND.name, "bytes": OUTPUT_BLEND.stat().st_size, "sha256": sha256_file(OUTPUT_BLEND)},
    }
except Exception as exc:
    payload = {
        "schema": "kodepoia.blender.pbr_result",
        "version": 1,
        "status": "fail",
        "blockers": ["pbr_exception"],
        "recipe_digest": None,
        "input_blend_sha256": None,
        "objects": {},
        "materials": {},
        "artifact": None,
        "error_type": type(exc).__name__,
        "error_message": str(exc).replace(str(ROOT), "<WORKSPACE>")[:512],
    }

write_result(payload)
print("KODEPOIA_R10_4_RESULT=" + str(payload["status"]))
raise SystemExit(0 if payload["status"] == "pass" else 17)
'''
