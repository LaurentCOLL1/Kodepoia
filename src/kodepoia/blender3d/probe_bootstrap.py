from __future__ import annotations

PROBE_BOOTSTRAP_SOURCE = r'''from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path.cwd().resolve()
RESULT = ROOT / "probe_result.json"
RESULT_TMP = ROOT / "probe_result.tmp"
BLEND = ROOT / "probe.blend"
GLB = ROOT / "probe.glb"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {"filename": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size}


def write_result(payload: dict[str, object]) -> None:
    RESULT_TMP.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False),
        encoding="utf-8",
    )
    os.replace(RESULT_TMP, RESULT)


payload: dict[str, object]
try:
    version = ".".join(str(part) for part in bpy.app.version)
    python_version = ".".join(str(part) for part in sys.version_info[:3])
    background = bool(bpy.app.background)
    online_access = bool(getattr(bpy.app, "online_access", False))
    exporter_available = hasattr(bpy.ops.export_scene, "gltf")

    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    mesh = bpy.data.meshes.new("KodepoiaProbeMesh")
    vertices = [
        (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
        (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5),
    ]
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
        (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7),
    ]
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("KodepoiaProbeCube", mesh)
    bpy.context.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh_vertex_count = len(bm.verts)
    bm.free()

    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    if not exporter_available:
        raise RuntimeError("gltf_exporter_unavailable")
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB")

    payload = {
        "schema": "kodepoia.blender.probe_result",
        "version": 1,
        "status": "pass",
        "blockers": [],
        "facts": {
            "blender_version": version,
            "python_version": python_version,
            "background": background,
            "online_access": online_access,
            "gltf_exporter_available": exporter_available,
            "bmesh_available": True,
            "object_count": len(bpy.data.objects),
            "mesh_count": len(bpy.data.meshes),
            "vertex_count": len(mesh.vertices),
            "face_count": len(mesh.polygons),
            "bmesh_vertex_count": bmesh_vertex_count,
        },
        "artifacts": {"blend": artifact(BLEND), "glb": artifact(GLB)},
    }
except Exception as exc:
    message = str(exc).replace(str(ROOT), "<WORKSPACE>")[:512]
    payload = {
        "schema": "kodepoia.blender.probe_result",
        "version": 1,
        "status": "fail",
        "blockers": ["probe_exception"],
        "facts": {"error_type": type(exc).__name__, "error_message": message},
        "artifacts": {},
    }

write_result(payload)
print("KODEPOIA_R10_2_RESULT=" + str(payload["status"]))
raise SystemExit(0 if payload["status"] == "pass" else 17)
'''
