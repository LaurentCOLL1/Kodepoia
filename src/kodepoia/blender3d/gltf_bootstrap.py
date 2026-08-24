from __future__ import annotations

GLTF_EXPORT_BOOTSTRAP_SOURCE = r'''from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import bpy

ROOT = Path.cwd().resolve()
JOB = ROOT / "gltf_job.json"
INPUT = ROOT / "input.blend"
OUTPUT_ROOT = ROOT / "export"
RESULT = ROOT / "gltf_result.json"
RESULT_TMP = ROOT / "gltf_result.tmp"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_result(payload: dict[str, object]) -> None:
    RESULT_TMP.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    os.replace(RESULT_TMP, RESULT)


def facts(objects: list[bpy.types.Object] | None = None) -> dict[str, object]:
    chosen = list(objects) if objects is not None else list(bpy.context.scene.objects)
    meshes = [item for item in chosen if item.type == "MESH"]
    armatures = [item for item in chosen if item.type == "ARMATURE"]
    materials: set[str] = set()
    uv_layers: set[str] = set()
    shape_keys: set[str] = set()
    bones: set[str] = set()
    for obj in meshes:
        for slot in obj.material_slots:
            if slot.material is not None:
                materials.add(slot.material.name)
        for layer in obj.data.uv_layers:
            uv_layers.add(layer.name)
        if obj.data.shape_keys is not None:
            for block in obj.data.shape_keys.key_blocks:
                if block.name != "Basis":
                    shape_keys.add(block.name)
    for armature in armatures:
        for bone in armature.data.bones:
            bones.add(bone.name)
    animation_names = sorted(action.name for action in bpy.data.actions)
    return {
        "object_count": len(chosen),
        "mesh_count": len(meshes),
        "armature_count": len(armatures),
        "material_names": sorted(materials),
        "uv_layer_names": sorted(uv_layers),
        "shape_key_names": sorted(shape_keys),
        "bone_names": sorted(bones),
        "animation_names": animation_names,
    }


def governed_objects(profile: dict[str, object]) -> list[bpy.types.Object]:
    if str(profile["scope"]) == "scene":
        return list(bpy.context.scene.objects)
    expected = [str(item) for item in profile["source_object_ids"]]
    resolved: list[bpy.types.Object] = []
    for object_id in expected:
        matches = [item for item in bpy.context.scene.objects if item.get("kodepoia_id") == object_id]
        if len(matches) != 1:
            raise RuntimeError("object_identity_resolution_failed:" + object_id)
        resolved.append(matches[0])
    return resolved


def select_only(objects: list[bpy.types.Object]) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    if objects:
        bpy.context.view_layer.objects.active = objects[0]


def export(profile: dict[str, object], objects: list[bpy.types.Object]) -> Path:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    container = str(profile["container"])
    output = OUTPUT_ROOT / ("asset.glb" if container == "GLB" else "asset.gltf")
    select_only(objects)
    kwargs = {
        "filepath": str(output),
        "check_existing": False,
        "export_format": container,
        "export_texcoords": bool(profile["export_uvs"]),
        "export_normals": bool(profile["export_normals"]),
        "export_tangents": bool(profile["export_tangents"]),
        "export_materials": "EXPORT" if bool(profile["export_materials"]) else "NONE",
        "use_selection": str(profile["scope"]) == "selected",
        "export_yup": True,
        "export_apply": False,
        "export_animations": bool(profile["export_animations"]),
        "export_animation_mode": "ACTIONS",
        "export_skins": bool(profile["export_skins"]),
        "export_influence_nb": int(profile["max_influences"]),
        "export_all_influences": False,
        "export_def_bones": bool(profile["deform_bones_only"]),
        "export_morph": bool(profile["export_morphs"]),
        "export_morph_normal": bool(profile["export_normals"] and profile["export_morphs"]),
        "export_morph_tangent": False,
        "export_morph_animation": bool(profile["export_animations"] and profile["export_morphs"]),
        "export_cameras": False,
        "export_lights": False,
        "export_extras": False,
        "export_draco_mesh_compression_enable": False,
        "export_meshopt_compression_enable": False,
        "export_use_gltfpack": False,
        "will_save_settings": False,
    }
    if container == "GLTF_SEPARATE":
        kwargs["export_texture_dir"] = "textures"
    result = bpy.ops.export_scene.gltf(**kwargs)
    if "FINISHED" not in result:
        raise RuntimeError("gltf_export_operator_failed")
    if not output.is_file():
        raise RuntimeError("gltf_primary_output_missing")
    return output


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.actions):
        for item in list(collection):
            try:
                collection.remove(item)
            except RuntimeError:
                pass


def artifact_records() -> list[dict[str, object]]:
    allowed = {".glb", ".gltf", ".bin", ".png", ".jpg", ".jpeg", ".webp"}
    records: list[dict[str, object]] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_symlink():
            raise RuntimeError("output_symlink_forbidden")
        if not path.is_file():
            continue
        rel = path.relative_to(OUTPUT_ROOT).as_posix()
        if path.suffix.lower() not in allowed or len(records) >= 128:
            raise RuntimeError("output_inventory_forbidden_or_oversized")
        records.append({"path": rel, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    if not records:
        raise RuntimeError("no_export_artifacts")
    return records


def main() -> None:
    job = json.loads(JOB.read_text(encoding="utf-8"))
    profile = dict(job["profile"])
    if not INPUT.is_file():
        raise RuntimeError("input_blend_missing")
    bpy.ops.wm.open_mainfile(filepath=str(INPUT), load_ui=False, use_scripts=False, display_file_selector=False)
    objects = governed_objects(profile)
    source = facts(objects)
    output = export(profile, objects)
    clear_scene()
    imported = bpy.ops.import_scene.gltf(filepath=str(output))
    if "FINISHED" not in imported:
        raise RuntimeError("gltf_roundtrip_import_failed")
    roundtrip = facts()
    payload = {
        "schema": "kodepoia.blender.gltf_result",
        "version": 1,
        "status": "pass",
        "blockers": [],
        "profile_digest": str(job["profile_digest"]),
        "input_blend_sha256": sha256_file(INPUT),
        "runtime": {
            "blender_version": bpy.app.version_string,
            "background": bool(bpy.app.background),
            "online_access": bool(getattr(bpy.app, "online_access", False)),
        },
        "source": source,
        "roundtrip": roundtrip,
        "primary": output.relative_to(OUTPUT_ROOT).as_posix(),
        "artifacts": artifact_records(),
    }
    write_result(payload)


try:
    main()
except Exception as exc:
    message = str(exc).replace(str(ROOT), "<WORK>")[:500]
    write_result({
        "schema": "kodepoia.blender.gltf_result",
        "version": 1,
        "status": "fail",
        "blockers": ["gltf_bootstrap_exception"],
        "profile_digest": None,
        "input_blend_sha256": sha256_file(INPUT) if INPUT.is_file() else None,
        "runtime": {
            "blender_version": bpy.app.version_string,
            "background": bool(bpy.app.background),
            "online_access": bool(getattr(bpy.app, "online_access", False)),
        },
        "source": {},
        "roundtrip": {},
        "primary": None,
        "artifacts": [],
        "error": {"type": type(exc).__name__, "message": message},
    })
    raise
'''


GLTF_ACCEPTANCE_BOOTSTRAP_SOURCE = r'''from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import bpy

ROOT = Path.cwd().resolve()
RESULT = ROOT / "gltf_acceptance_result.json"
RESULT_TMP = ROOT / "gltf_acceptance_result.tmp"
STATIC_GLB = ROOT / "static.glb"
RIGGED_GLB = ROOT / "rigged.glb"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_result(payload: dict[str, object]) -> None:
    RESULT_TMP.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    os.replace(RESULT_TMP, RESULT)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.actions):
        for item in list(collection):
            try:
                collection.remove(item)
            except RuntimeError:
                pass


def add_uv_and_material(obj: bpy.types.Object, material_name: str) -> None:
    material = bpy.data.materials.new(material_name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF") if material.node_tree is not None else None
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (0.25, 0.55, 0.8, 1.0)
        bsdf.inputs["Metallic IOR Level"].default_value = 0.1
        bsdf.inputs["Roughness"].default_value = 0.45
    obj.data.materials.append(material)
    uv = obj.data.uv_layers.new(name="UVMap")
    for loop in obj.data.loops:
        u = 1.0 if loop.vertex_index % 2 else 0.0
        v = 1.0 if (loop.vertex_index // 2) % 2 else 0.0
        uv.data[loop.index].uv = (u, v)


def facts() -> dict[str, object]:
    meshes = [item for item in bpy.context.scene.objects if item.type == "MESH"]
    armatures = [item for item in bpy.context.scene.objects if item.type == "ARMATURE"]
    materials: set[str] = set()
    uv_layers: set[str] = set()
    shape_keys: set[str] = set()
    bones: set[str] = set()
    for obj in meshes:
        for slot in obj.material_slots:
            if slot.material is not None:
                materials.add(slot.material.name)
        for layer in obj.data.uv_layers:
            uv_layers.add(layer.name)
        if obj.data.shape_keys is not None:
            for block in obj.data.shape_keys.key_blocks:
                if block.name != "Basis":
                    shape_keys.add(block.name)
    for armature in armatures:
        for bone in armature.data.bones:
            bones.add(bone.name)
    return {
        "mesh_count": len(meshes),
        "armature_count": len(armatures),
        "material_names": sorted(materials),
        "uv_layer_names": sorted(uv_layers),
        "shape_key_names": sorted(shape_keys),
        "bone_names": sorted(bones),
        "animation_names": sorted(action.name for action in bpy.data.actions),
    }


def export_selected(path: Path, *, skins: bool, morphs: bool, animations: bool) -> None:
    result = bpy.ops.export_scene.gltf(
        filepath=str(path), check_existing=False, export_format="GLB",
        export_texcoords=True, export_normals=True, export_tangents=True,
        export_materials="EXPORT", use_selection=True, export_yup=True, export_apply=False,
        export_animations=animations, export_animation_mode="ACTIONS",
        export_skins=skins, export_influence_nb=4, export_all_influences=False,
        export_def_bones=skins, export_morph=morphs, export_morph_normal=morphs,
        export_morph_tangent=False, export_morph_animation=animations and morphs,
        export_cameras=False, export_lights=False, export_extras=False,
        export_draco_mesh_compression_enable=False, export_meshopt_compression_enable=False,
        export_use_gltfpack=False, will_save_settings=False,
    )
    if "FINISHED" not in result or not path.is_file():
        raise RuntimeError("fixture_export_failed")


def build_static() -> dict[str, object]:
    clear_scene()
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 0.0))
    obj = bpy.context.active_object
    obj.name = "KDP_StaticMesh"
    obj["kodepoia_id"] = "static.mesh"
    add_uv_and_material(obj, "KDP_StaticMaterial")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    source = facts()
    export_selected(STATIC_GLB, skins=False, morphs=False, animations=False)
    clear_scene()
    if "FINISHED" not in bpy.ops.import_scene.gltf(filepath=str(STATIC_GLB)):
        raise RuntimeError("static_roundtrip_import_failed")
    return {"source": source, "roundtrip": facts()}


def build_rigged() -> dict[str, object]:
    clear_scene()
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 0.0))
    mesh = bpy.context.active_object
    mesh.name = "KDP_RiggedMesh"
    mesh["kodepoia_id"] = "rigged.mesh"
    add_uv_and_material(mesh, "KDP_RiggedMaterial")
    mesh.shape_key_add(name="Basis")
    smile = mesh.shape_key_add(name="Smile")
    if len(smile.data) > 0:
        smile.data[0].co.z += 0.2

    arm_data = bpy.data.armatures.new("KDP_RigData")
    arm = bpy.data.objects.new("KDP_Rig", arm_data)
    arm["kodepoia_id"] = "rigged.armature"
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    root = arm_data.edit_bones.new("Root")
    root.head = (0.0, 0.0, -1.0)
    root.tail = (0.0, 0.0, 0.0)
    child = arm_data.edit_bones.new("Child")
    child.head = (0.0, 0.0, 0.0)
    child.tail = (0.0, 0.0, 1.0)
    child.parent = root
    child.use_connect = True
    bpy.ops.object.mode_set(mode="OBJECT")
    arm_data.bones["Root"].use_deform = True
    arm_data.bones["Child"].use_deform = True

    root_group = mesh.vertex_groups.new(name="Root")
    child_group = mesh.vertex_groups.new(name="Child")
    indices = [vertex.index for vertex in mesh.data.vertices]
    split = max(1, len(indices) // 2)
    root_group.add(indices[:split], 1.0, "REPLACE")
    child_group.add(indices[split:], 1.0, "REPLACE")
    modifier = mesh.modifiers.new(name="KDP_Armature", type="ARMATURE")
    modifier.object = arm
    modifier.use_vertex_groups = True
    modifier.use_bone_envelopes = False

    pose = arm.pose.bones["Child"]
    pose.rotation_mode = "XYZ"
    bpy.context.scene.frame_set(1)
    pose.rotation_euler = (0.0, 0.0, 0.0)
    pose.keyframe_insert(data_path="rotation_euler", frame=1, group="Child")
    bpy.context.scene.frame_set(20)
    pose.rotation_euler = (0.0, 0.0, 0.4)
    pose.keyframe_insert(data_path="rotation_euler", frame=20, group="Child")
    if arm.animation_data is None or arm.animation_data.action is None:
        raise RuntimeError("fixture_action_missing")
    arm.animation_data.action.name = "Wave"
    bpy.context.scene.frame_set(1)

    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    source = facts()
    export_selected(RIGGED_GLB, skins=True, morphs=True, animations=True)
    clear_scene()
    if "FINISHED" not in bpy.ops.import_scene.gltf(filepath=str(RIGGED_GLB)):
        raise RuntimeError("rigged_roundtrip_import_failed")
    return {"source": source, "roundtrip": facts()}


def main() -> None:
    static = build_static()
    rigged = build_rigged()
    static_ok = (
        static["roundtrip"]["mesh_count"] >= 1
        and "KDP_StaticMaterial" in static["roundtrip"]["material_names"]
        and "UVMap" in static["roundtrip"]["uv_layer_names"]
    )
    rigged_ok = (
        rigged["roundtrip"]["mesh_count"] >= 1
        and rigged["roundtrip"]["armature_count"] >= 1
        and {"Root", "Child"}.issubset(set(rigged["roundtrip"]["bone_names"]))
        and "Smile" in rigged["roundtrip"]["shape_key_names"]
        and len(rigged["roundtrip"]["animation_names"]) >= 1
    )
    blockers = []
    if not static_ok:
        blockers.append("static_roundtrip_semantics")
    if not rigged_ok:
        blockers.append("rigged_roundtrip_semantics")
    if not bpy.app.background:
        blockers.append("background_false")
    if bool(getattr(bpy.app, "online_access", False)):
        blockers.append("offline_mode_not_confirmed")
    write_result({
        "schema": "kodepoia.blender.gltf_acceptance_result",
        "version": 1,
        "status": "pass" if not blockers else "fail",
        "blockers": blockers,
        "runtime": {
            "blender_version": bpy.app.version_string,
            "background": bool(bpy.app.background),
            "online_access": bool(getattr(bpy.app, "online_access", False)),
        },
        "fixtures": {"static": static, "rigged": rigged},
        "artifacts": {
            "static": {"filename": "static.glb", "sha256": sha256_file(STATIC_GLB), "bytes": STATIC_GLB.stat().st_size},
            "rigged": {"filename": "rigged.glb", "sha256": sha256_file(RIGGED_GLB), "bytes": RIGGED_GLB.stat().st_size},
        },
    })


try:
    main()
except Exception as exc:
    message = str(exc).replace(str(ROOT), "<WORK>")[:500]
    write_result({
        "schema": "kodepoia.blender.gltf_acceptance_result",
        "version": 1,
        "status": "fail",
        "blockers": ["acceptance_bootstrap_exception"],
        "runtime": {
            "blender_version": bpy.app.version_string,
            "background": bool(bpy.app.background),
            "online_access": bool(getattr(bpy.app, "online_access", False)),
        },
        "fixtures": {},
        "artifacts": {},
        "error": {"type": type(exc).__name__, "message": message},
    })
    raise
'''
