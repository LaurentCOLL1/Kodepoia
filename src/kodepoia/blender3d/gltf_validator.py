from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import BlenderProtocolError
from .gltf_contracts import GltfExportProfile
from .serialization import canonical_sha256

_GLB_MAGIC = b"glTF"
_GLB_VERSION = 2
_JSON_CHUNK = 0x4E4F534A
_BIN_CHUNK = 0x004E4942
_MAX_JSON_BYTES = 64 * 1024 * 1024
_MAX_ARRAY_ITEMS = 1_000_000


@dataclass(frozen=True, slots=True)
class GltfDocumentFacts:
    asset_version: str
    generator: str | None
    scene_count: int
    node_count: int
    mesh_count: int
    material_count: int
    skin_count: int
    animation_count: int
    accessor_count: int
    buffer_count: int
    image_count: int
    texture_count: int
    morph_target_count: int
    extensions_used: tuple[str, ...]
    json_bytes: int
    binary_bytes: int
    total_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_version": self.asset_version,
            "generator": self.generator,
            "scene_count": self.scene_count,
            "node_count": self.node_count,
            "mesh_count": self.mesh_count,
            "material_count": self.material_count,
            "skin_count": self.skin_count,
            "animation_count": self.animation_count,
            "accessor_count": self.accessor_count,
            "buffer_count": self.buffer_count,
            "image_count": self.image_count,
            "texture_count": self.texture_count,
            "morph_target_count": self.morph_target_count,
            "extensions_used": list(self.extensions_used),
            "json_bytes": self.json_bytes,
            "binary_bytes": self.binary_bytes,
            "total_bytes": self.total_bytes,
        }


def _array(document: dict[str, Any], key: str, maximum: int = _MAX_ARRAY_ITEMS) -> list[Any]:
    value = document.get(key, [])
    if not isinstance(value, list) or len(value) > maximum:
        raise BlenderProtocolError(f"glTF {key} must be a bounded array")
    return value


def _index(value: Any, size: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < size:
        raise BlenderProtocolError(f"glTF {field} index is invalid")
    return value


def _safe_uri(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 4096:
        raise BlenderProtocolError("glTF external URI is invalid")
    normalized = value.replace("\\", "/")
    if "://" in normalized or normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
        raise BlenderProtocolError("glTF external URI escapes or uses a remote scheme")
    return normalized


def validate_gltf_document(document: dict[str, Any], *, json_bytes: int, binary_bytes: int, total_bytes: int) -> GltfDocumentFacts:
    if not isinstance(document, dict):
        raise BlenderProtocolError("glTF root must be an object")
    asset = document.get("asset")
    if not isinstance(asset, dict) or asset.get("version") != "2.0":
        raise BlenderProtocolError("glTF asset.version must be exactly 2.0")
    generator = asset.get("generator")
    if generator is not None and (not isinstance(generator, str) or len(generator) > 512):
        raise BlenderProtocolError("glTF asset.generator is invalid")

    scenes = _array(document, "scenes", 1024)
    nodes = _array(document, "nodes", 100_000)
    meshes = _array(document, "meshes", 100_000)
    materials = _array(document, "materials", 100_000)
    skins = _array(document, "skins", 100_000)
    animations = _array(document, "animations", 100_000)
    accessors = _array(document, "accessors")
    buffers = _array(document, "buffers", 1024)
    images = _array(document, "images", 100_000)
    textures = _array(document, "textures", 100_000)

    if scenes and "scene" in document:
        _index(document["scene"], len(scenes), "scene")
    for scene in scenes:
        if not isinstance(scene, dict):
            raise BlenderProtocolError("glTF scene entry must be an object")
        for item in scene.get("nodes", []):
            _index(item, len(nodes), "scene.nodes")
    for node in nodes:
        if not isinstance(node, dict):
            raise BlenderProtocolError("glTF node entry must be an object")
        for child in node.get("children", []):
            _index(child, len(nodes), "node.children")
        if "mesh" in node:
            _index(node["mesh"], len(meshes), "node.mesh")
        if "skin" in node:
            _index(node["skin"], len(skins), "node.skin")

    morph_targets = 0
    for mesh in meshes:
        if not isinstance(mesh, dict):
            raise BlenderProtocolError("glTF mesh entry must be an object")
        primitives = mesh.get("primitives")
        if not isinstance(primitives, list) or not primitives or len(primitives) > 100_000:
            raise BlenderProtocolError("glTF mesh.primitives must be a bounded non-empty array")
        for primitive in primitives:
            if not isinstance(primitive, dict):
                raise BlenderProtocolError("glTF primitive must be an object")
            attributes = primitive.get("attributes")
            if not isinstance(attributes, dict) or "POSITION" not in attributes:
                raise BlenderProtocolError("glTF primitive must contain POSITION")
            for accessor_index in attributes.values():
                _index(accessor_index, len(accessors), "primitive.attributes")
            if "indices" in primitive:
                _index(primitive["indices"], len(accessors), "primitive.indices")
            if "material" in primitive:
                _index(primitive["material"], len(materials), "primitive.material")
            targets = primitive.get("targets", [])
            if not isinstance(targets, list) or len(targets) > 1024:
                raise BlenderProtocolError("glTF primitive.targets is invalid")
            morph_targets += len(targets)
            for target in targets:
                if not isinstance(target, dict):
                    raise BlenderProtocolError("glTF morph target must be an object")
                for accessor_index in target.values():
                    _index(accessor_index, len(accessors), "primitive.targets")

    for skin in skins:
        if not isinstance(skin, dict):
            raise BlenderProtocolError("glTF skin entry must be an object")
        joints = skin.get("joints")
        if not isinstance(joints, list) or not joints:
            raise BlenderProtocolError("glTF skin.joints must be non-empty")
        for joint in joints:
            _index(joint, len(nodes), "skin.joints")
        if "inverseBindMatrices" in skin:
            _index(skin["inverseBindMatrices"], len(accessors), "skin.inverseBindMatrices")

    for animation in animations:
        if not isinstance(animation, dict):
            raise BlenderProtocolError("glTF animation entry must be an object")
        samplers = animation.get("samplers")
        channels = animation.get("channels")
        if not isinstance(samplers, list) or not isinstance(channels, list) or not samplers or not channels:
            raise BlenderProtocolError("glTF animations require samplers and channels")
        for sampler in samplers:
            if not isinstance(sampler, dict):
                raise BlenderProtocolError("glTF animation sampler must be an object")
            _index(sampler.get("input"), len(accessors), "animation.sampler.input")
            _index(sampler.get("output"), len(accessors), "animation.sampler.output")
        for channel in channels:
            if not isinstance(channel, dict):
                raise BlenderProtocolError("glTF animation channel must be an object")
            _index(channel.get("sampler"), len(samplers), "animation.channel.sampler")
            target = channel.get("target")
            if not isinstance(target, dict) or target.get("path") not in {"translation", "rotation", "scale", "weights"}:
                raise BlenderProtocolError("glTF animation channel target is invalid")
            if "node" in target:
                _index(target["node"], len(nodes), "animation.channel.target.node")

    for collection_name, collection in (("buffers", buffers), ("images", images)):
        for item in collection:
            if not isinstance(item, dict):
                raise BlenderProtocolError(f"glTF {collection_name} entry must be an object")
            uri = item.get("uri")
            if uri is not None and not str(uri).startswith("data:"):
                _safe_uri(uri)

    extensions = document.get("extensionsUsed", [])
    if not isinstance(extensions, list) or len(extensions) > 128 or not all(isinstance(item, str) for item in extensions):
        raise BlenderProtocolError("glTF extensionsUsed must be a bounded string array")
    if len(set(extensions)) != len(extensions):
        raise BlenderProtocolError("glTF extensionsUsed must be unique")

    return GltfDocumentFacts(
        asset_version="2.0",
        generator=generator,
        scene_count=len(scenes),
        node_count=len(nodes),
        mesh_count=len(meshes),
        material_count=len(materials),
        skin_count=len(skins),
        animation_count=len(animations),
        accessor_count=len(accessors),
        buffer_count=len(buffers),
        image_count=len(images),
        texture_count=len(textures),
        morph_target_count=morph_targets,
        extensions_used=tuple(extensions),
        json_bytes=json_bytes,
        binary_bytes=binary_bytes,
        total_bytes=total_bytes,
    )


def parse_glb_bytes(data: bytes, *, max_bytes: int) -> tuple[dict[str, Any], GltfDocumentFacts]:
    if not isinstance(data, bytes) or not 12 <= len(data) <= max_bytes:
        raise BlenderProtocolError("GLB size is outside the declared budget")
    magic, version, declared_length = struct.unpack_from("<4sII", data, 0)
    if magic != _GLB_MAGIC or version != _GLB_VERSION or declared_length != len(data):
        raise BlenderProtocolError("invalid GLB header/version/declared length")
    offset = 12
    chunks: list[tuple[int, bytes]] = []
    while offset < len(data):
        if offset + 8 > len(data):
            raise BlenderProtocolError("truncated GLB chunk header")
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        end = offset + chunk_length
        if chunk_length < 0 or end > len(data):
            raise BlenderProtocolError("GLB chunk escapes declared length")
        chunks.append((chunk_type, data[offset:end]))
        offset = end
    if offset != len(data) or not chunks or chunks[0][0] != _JSON_CHUNK:
        raise BlenderProtocolError("GLB requires JSON as its first bounded chunk")
    if sum(1 for item in chunks if item[0] == _JSON_CHUNK) != 1:
        raise BlenderProtocolError("GLB must contain exactly one JSON chunk")
    if any(item[0] not in {_JSON_CHUNK, _BIN_CHUNK} for item in chunks):
        raise BlenderProtocolError("GLB contains an unsupported chunk type")
    json_payload = chunks[0][1].rstrip(b" \t\r\n\x00")
    if not json_payload or len(json_payload) > _MAX_JSON_BYTES:
        raise BlenderProtocolError("GLB JSON chunk is empty or oversized")
    try:
        document = json.loads(json_payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BlenderProtocolError("GLB JSON chunk is invalid UTF-8 JSON") from exc
    binary_bytes = sum(len(chunk) for kind, chunk in chunks if kind == _BIN_CHUNK)
    facts = validate_gltf_document(document, json_bytes=len(json_payload), binary_bytes=binary_bytes, total_bytes=len(data))
    return document, facts


def parse_gltf_json_bytes(data: bytes, *, max_bytes: int) -> tuple[dict[str, Any], GltfDocumentFacts]:
    if not isinstance(data, bytes) or not 2 <= len(data) <= min(max_bytes, _MAX_JSON_BYTES):
        raise BlenderProtocolError("glTF JSON size is outside the declared budget")
    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BlenderProtocolError("glTF file is invalid UTF-8 JSON") from exc
    facts = validate_gltf_document(document, json_bytes=len(data), binary_bytes=0, total_bytes=len(data))
    return document, facts


def validate_gltf_file(path: Path, *, max_bytes: int) -> tuple[dict[str, Any], GltfDocumentFacts]:
    candidate = path.resolve(strict=True)
    if not candidate.is_file():
        raise BlenderProtocolError("glTF artifact must be a regular file")
    data = candidate.read_bytes()
    if candidate.suffix.lower() == ".glb":
        return parse_glb_bytes(data, max_bytes=max_bytes)
    if candidate.suffix.lower() == ".gltf":
        return parse_gltf_json_bytes(data, max_bytes=max_bytes)
    raise BlenderProtocolError("unsupported glTF artifact extension")


def evaluate_roundtrip(profile: GltfExportProfile, source: dict[str, Any], imported: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
    rules: list[dict[str, str]] = []

    def rule(rule_id: str, passed: bool, detail: str) -> None:
        rules.append({"rule_id": rule_id, "state": "PASS" if passed else "BLOCK", "detail": detail})

    def names(facts: dict[str, Any], key: str) -> set[str]:
        value = facts.get(key, [])
        return {str(item) for item in value} if isinstance(value, list) else set()

    source_meshes = int(source.get("mesh_count", 0)) if isinstance(source.get("mesh_count", 0), int) else 0
    imported_meshes = int(imported.get("mesh_count", 0)) if isinstance(imported.get("mesh_count", 0), int) else 0
    rule("mesh_presence", source_meshes > 0 and imported_meshes > 0, f"source={source_meshes} imported={imported_meshes}")

    if profile.export_materials:
        required = set(profile.required_materials)
        rule("materials", required.issubset(names(imported, "material_names")), f"required={sorted(required)}")
    if profile.export_uvs:
        required_uvs = set(profile.required_uv_sets)
        rule("uv_sets", required_uvs.issubset(names(imported, "uv_layer_names")), f"required={sorted(required_uvs)}")
    if profile.export_skins:
        required_bones = set(profile.required_bones)
        rule("skin_bones", required_bones.issubset(names(imported, "bone_names")), f"required={sorted(required_bones)}")
        rule("gltf_skin", isinstance(document.get("skins"), list) and len(document["skins"]) > 0, "skins must survive export")
    if profile.export_morphs:
        required_shapes = set(profile.required_shape_keys)
        rule("shape_keys", required_shapes.issubset(names(imported, "shape_key_names")), f"required={sorted(required_shapes)}")
    if profile.export_animations:
        required_animations = set(profile.required_animations)
        imported_animation_names = names(imported, "animation_names")
        rule("animations", required_animations.issubset(imported_animation_names), f"required={sorted(required_animations)} imported={sorted(imported_animation_names)}")
        rule("gltf_animation", isinstance(document.get("animations"), list) and len(document["animations"]) >= len(required_animations), "animation channels must survive export")

    used = document.get("extensionsUsed", [])
    used_extensions = set(used) if isinstance(used, list) else set()
    allowed = set(profile.allowed_extensions)
    rule("extensions", used_extensions.issubset(allowed), f"used={sorted(used_extensions)} allowed={sorted(allowed)}")
    blockers = sorted(item["rule_id"] for item in rules if item["state"] == "BLOCK")
    payload = {"status": "pass" if not blockers else "block", "blockers": blockers, "rules": rules}
    return {**payload, "report_digest": canonical_sha256(payload)}
