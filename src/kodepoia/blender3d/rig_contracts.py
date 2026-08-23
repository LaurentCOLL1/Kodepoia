from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .errors import BlenderBoundaryError
from .serialization import canonical_sha256

_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class RigMode(StrEnum):
    CREATE = "create"
    VALIDATE_EXISTING = "validate_existing"


class WeightStrategy(StrEnum):
    EXPLICIT = "explicit"
    NEAREST_DEFORM_BONE = "nearest_deform_bone"
    EXISTING = "existing"


def _id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise BlenderBoundaryError(f"{field} must match ^[a-z][a-z0-9_.-]{{0,63}}$")
    return value


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise BlenderBoundaryError(f"{field} must be a lowercase SHA-256")
    return value


def _number(value: Any, field: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BlenderBoundaryError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise BlenderBoundaryError(f"{field} must be finite and between {minimum} and {maximum}")
    return result


def _vec3(value: Any, field: str) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise BlenderBoundaryError(f"{field} must be a 3-vector")
    return tuple(_number(item, field, -1_000_000.0, 1_000_000.0) for item in value)  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class BoneSpec:
    bone_id: str
    display_name: str
    parent_id: str | None
    head: tuple[float, float, float]
    tail: tuple[float, float, float]
    deform: bool
    connected: bool

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BoneSpec":
        required = {"bone_id", "display_name", "parent_id", "head", "tail", "deform", "connected"}
        if set(payload) != required:
            raise BlenderBoundaryError("BoneSpec has missing or unknown fields")
        display = payload["display_name"]
        if not isinstance(display, str) or not 1 <= len(display) <= 128 or any(ord(ch) < 32 for ch in display):
            raise BlenderBoundaryError("display_name must be printable and 1-128 characters")
        parent = payload["parent_id"]
        if parent is not None:
            parent = _id(parent, "parent_id")
        for flag in ("deform", "connected"):
            if not isinstance(payload[flag], bool):
                raise BlenderBoundaryError(f"{flag} must be boolean")
        head = _vec3(payload["head"], "head")
        tail = _vec3(payload["tail"], "tail")
        if math.dist(head, tail) <= 1e-8:
            raise BlenderBoundaryError("Bone head/tail must define a non-zero rest segment")
        if payload["connected"] and parent is None:
            raise BlenderBoundaryError("A root bone cannot be connected")
        return cls(_id(payload["bone_id"], "bone_id"), display, parent, head, tail, payload["deform"], payload["connected"])

    def to_dict(self) -> dict[str, Any]:
        return {"bone_id": self.bone_id, "display_name": self.display_name, "parent_id": self.parent_id, "head": list(self.head), "tail": list(self.tail), "deform": self.deform, "connected": self.connected}


@dataclass(frozen=True, slots=True)
class BoneWeight:
    bone_id: str
    weight: float

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BoneWeight":
        if set(payload) != {"bone_id", "weight"}:
            raise BlenderBoundaryError("BoneWeight requires exactly bone_id/weight")
        return cls(_id(payload["bone_id"], "bone_id"), _number(payload["weight"], "weight", 0.0, 1.0))

    def to_dict(self) -> dict[str, Any]:
        return {"bone_id": self.bone_id, "weight": self.weight}


@dataclass(frozen=True, slots=True)
class VertexWeight:
    vertex: int
    influences: tuple[BoneWeight, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VertexWeight":
        if set(payload) != {"vertex", "influences"}:
            raise BlenderBoundaryError("VertexWeight requires exactly vertex/influences")
        vertex = payload["vertex"]
        if isinstance(vertex, bool) or not isinstance(vertex, int) or not 0 <= vertex <= 50_000_000:
            raise BlenderBoundaryError("vertex must be an integer in [0, 50000000]")
        raw = payload["influences"]
        if not isinstance(raw, list) or not 1 <= len(raw) <= 16 or not all(isinstance(item, dict) for item in raw):
            raise BlenderBoundaryError("influences must contain 1-16 entries")
        values = tuple(BoneWeight.from_dict(item) for item in raw)
        if len({item.bone_id for item in values}) != len(values):
            raise BlenderBoundaryError("Per-vertex bone influences must be unique")
        return cls(vertex, values)

    def to_dict(self) -> dict[str, Any]:
        return {"vertex": self.vertex, "influences": [item.to_dict() for item in self.influences]}


@dataclass(frozen=True, slots=True)
class MeshSkinSpec:
    mesh_id: str
    strategy: WeightStrategy
    weights: tuple[VertexWeight, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MeshSkinSpec":
        if set(payload) != {"mesh_id", "strategy", "weights"}:
            raise BlenderBoundaryError("MeshSkinSpec requires exactly mesh_id/strategy/weights")
        try:
            strategy = WeightStrategy(payload["strategy"])
        except (TypeError, ValueError) as exc:
            raise BlenderBoundaryError("Unsupported weight strategy") from exc
        raw = payload["weights"]
        if not isinstance(raw, list) or len(raw) > 250_000 or not all(isinstance(item, dict) for item in raw):
            raise BlenderBoundaryError("weights must be an array with at most 250000 entries")
        weights = tuple(VertexWeight.from_dict(item) for item in raw)
        if len({item.vertex for item in weights}) != len(weights):
            raise BlenderBoundaryError("Explicit vertex records must be unique")
        if strategy is WeightStrategy.EXPLICIT and not weights:
            raise BlenderBoundaryError("Explicit strategy requires vertex weights")
        if strategy is not WeightStrategy.EXPLICIT and weights:
            raise BlenderBoundaryError("Only explicit strategy accepts embedded vertex weights")
        return cls(_id(payload["mesh_id"], "mesh_id"), strategy, weights)

    def to_dict(self) -> dict[str, Any]:
        return {"mesh_id": self.mesh_id, "strategy": self.strategy.value, "weights": [item.to_dict() for item in self.weights]}


@dataclass(frozen=True, slots=True)
class InfluenceProfile:
    max_influences: int = 4
    allow_extended_influences: bool = False
    normalization_tolerance: float = 1e-4
    tiny_weight_threshold: float = 1e-5
    require_deformation_probe: bool = True

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InfluenceProfile":
        required = {"max_influences", "allow_extended_influences", "normalization_tolerance", "tiny_weight_threshold", "require_deformation_probe"}
        if set(payload) != required:
            raise BlenderBoundaryError("InfluenceProfile has missing or unknown fields")
        count = payload["max_influences"]
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 8:
            raise BlenderBoundaryError("max_influences must be an integer in [1, 8]")
        for flag in ("allow_extended_influences", "require_deformation_probe"):
            if not isinstance(payload[flag], bool):
                raise BlenderBoundaryError(f"{flag} must be boolean")
        if count > 4 and not payload["allow_extended_influences"]:
            raise BlenderBoundaryError("More than four influences requires explicit opt-in")
        return cls(
            max_influences=count,
            allow_extended_influences=payload["allow_extended_influences"],
            normalization_tolerance=_number(payload["normalization_tolerance"], "normalization_tolerance", 1e-8, 0.05),
            tiny_weight_threshold=_number(payload["tiny_weight_threshold"], "tiny_weight_threshold", 0.0, 0.05),
            require_deformation_probe=payload["require_deformation_probe"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {"max_influences": self.max_influences, "allow_extended_influences": self.allow_extended_influences, "normalization_tolerance": self.normalization_tolerance, "tiny_weight_threshold": self.tiny_weight_threshold, "require_deformation_probe": self.require_deformation_probe}


@dataclass(frozen=True, slots=True)
class RigProfile:
    version: int
    rig_id: str
    armature_id: str
    mode: RigMode
    input_blend_sha256: str
    bones: tuple[BoneSpec, ...]
    meshes: tuple[MeshSkinSpec, ...]
    influence: InfluenceProfile

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RigProfile":
        required = {"version", "rig_id", "armature_id", "mode", "input_blend_sha256", "bones", "meshes", "influence"}
        if set(payload) != required:
            raise BlenderBoundaryError("RigProfile has missing or unknown fields")
        if payload["version"] != 1:
            raise BlenderBoundaryError("Only RigProfile version 1 is supported")
        try:
            mode = RigMode(payload["mode"])
        except (TypeError, ValueError) as exc:
            raise BlenderBoundaryError("Unsupported rig mode") from exc
        raw_bones = payload["bones"]
        raw_meshes = payload["meshes"]
        if not isinstance(raw_bones, list) or not 1 <= len(raw_bones) <= 256 or not all(isinstance(item, dict) for item in raw_bones):
            raise BlenderBoundaryError("bones must contain 1-256 entries")
        if not isinstance(raw_meshes, list) or not 1 <= len(raw_meshes) <= 64 or not all(isinstance(item, dict) for item in raw_meshes):
            raise BlenderBoundaryError("meshes must contain 1-64 entries")
        bones = tuple(BoneSpec.from_dict(item) for item in raw_bones)
        meshes = tuple(MeshSkinSpec.from_dict(item) for item in raw_meshes)
        influence_payload = payload["influence"]
        if not isinstance(influence_payload, dict):
            raise BlenderBoundaryError("influence must be an object")
        influence = InfluenceProfile.from_dict(influence_payload)
        if len({bone.bone_id for bone in bones}) != len(bones):
            raise BlenderBoundaryError("bone_id values must be unique")
        if len({mesh.mesh_id for mesh in meshes}) != len(meshes):
            raise BlenderBoundaryError("mesh_id values must be unique")
        by_id = {bone.bone_id: bone for bone in bones}
        index = {bone.bone_id: pos for pos, bone in enumerate(bones)}
        roots = [bone for bone in bones if bone.parent_id is None]
        if len(roots) != 1:
            raise BlenderBoundaryError("RigProfile requires exactly one root bone")
        for pos, bone in enumerate(bones):
            if bone.parent_id is not None:
                parent = by_id.get(bone.parent_id)
                if parent is None:
                    raise BlenderBoundaryError(f"Unknown parent bone: {bone.parent_id}")
                if index[bone.parent_id] >= pos:
                    raise BlenderBoundaryError("Parent bones must appear before children")
                if bone.connected and math.dist(bone.head, parent.tail) > 1e-6:
                    raise BlenderBoundaryError("Connected child head must match parent tail")
        deform_ids = {bone.bone_id for bone in bones if bone.deform}
        if not deform_ids:
            raise BlenderBoundaryError("RigProfile requires at least one deform bone")
        for mesh in meshes:
            if mode is RigMode.CREATE and mesh.strategy is WeightStrategy.EXISTING:
                raise BlenderBoundaryError("Create mode cannot use existing weights")
            if mode is RigMode.VALIDATE_EXISTING and mesh.strategy is not WeightStrategy.EXISTING:
                raise BlenderBoundaryError("validate_existing mode requires existing weight strategy")
            for vertex in mesh.weights:
                for item in vertex.influences:
                    if item.bone_id not in by_id:
                        raise BlenderBoundaryError(f"Explicit weight references unknown bone: {item.bone_id}")
                    if item.bone_id not in deform_ids and item.weight > 0.0:
                        raise BlenderBoundaryError(f"Explicit weight references control-only bone: {item.bone_id}")
        return cls(1, _id(payload["rig_id"], "rig_id"), _id(payload["armature_id"], "armature_id"), mode, _sha(payload["input_blend_sha256"], "input_blend_sha256"), bones, meshes, influence)

    def to_dict(self) -> dict[str, Any]:
        return {"version": 1, "rig_id": self.rig_id, "armature_id": self.armature_id, "mode": self.mode.value, "input_blend_sha256": self.input_blend_sha256, "bones": [bone.to_dict() for bone in self.bones], "meshes": [mesh.to_dict() for mesh in self.meshes], "influence": self.influence.to_dict()}

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())

    @property
    def deform_bone_ids(self) -> tuple[str, ...]:
        return tuple(bone.bone_id for bone in self.bones if bone.deform)

    def normalized_explicit_weights(self) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = {}
        threshold = self.influence.tiny_weight_threshold
        for mesh in self.meshes:
            if mesh.strategy is not WeightStrategy.EXPLICIT:
                continue
            rows: list[dict[str, Any]] = []
            for vertex in mesh.weights:
                kept = [item for item in vertex.influences if item.weight >= threshold and item.weight > 0.0]
                total = sum(item.weight for item in kept)
                influences = [] if total <= 0.0 else [{"bone_id": item.bone_id, "weight": item.weight / total} for item in kept]
                rows.append({"vertex": vertex.vertex, "influences": influences})
            result[mesh.mesh_id] = rows
        return result
