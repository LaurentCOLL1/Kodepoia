from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from kodepoia.assets.contracts import AssetId, AssetRevisionId

from .errors import BlenderBoundaryError
from .serialization import canonical_sha256

_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class OrganicProfileKind(StrEnum):
    HUMANOID_BIPED = "humanoid_biped"
    QUADRUPED = "quadruped"


class ProfilePieceType(StrEnum):
    MESH = "mesh"
    ARMATURE = "armature"


def _id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise BlenderBoundaryError(f"{field} must match ^[a-z][a-z0-9_.-]{{0,63}}$")
    return value


def _printable(value: Any, field: str, *, maximum: int = 128) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= maximum or any(ord(ch) < 32 for ch in value):
        raise BlenderBoundaryError(f"{field} must be printable and 1-{maximum} characters")
    return value


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise BlenderBoundaryError(f"{field} must be a lowercase SHA-256")
    return value


def _bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise BlenderBoundaryError(f"{field} must be boolean")
    return value


def _id_array(value: Any, field: str, *, minimum: int = 0, maximum: int = 256) -> tuple[str, ...]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum or not all(isinstance(item, str) for item in value):
        raise BlenderBoundaryError(f"{field} must contain {minimum}-{maximum} IDs")
    result = tuple(_id(item, field) for item in value)
    if len(set(result)) != len(result):
        raise BlenderBoundaryError(f"{field} must contain unique IDs")
    return result


@dataclass(frozen=True, slots=True)
class CoordinateProfile:
    unit_scale_meters: float
    forward_axis: str
    up_axis: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CoordinateProfile":
        if set(payload) != {"unit_scale_meters", "forward_axis", "up_axis"}:
            raise BlenderBoundaryError("CoordinateProfile has missing or unknown fields")
        value = payload["unit_scale_meters"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise BlenderBoundaryError("unit_scale_meters must be finite numeric")
        scale = float(value)
        if abs(scale - 1.0) > 1e-9:
            raise BlenderBoundaryError("R10 profiles require normalized meter units (unit_scale_meters=1.0)")
        if payload["forward_axis"] != "-Z" or payload["up_axis"] != "Y":
            raise BlenderBoundaryError("R10 profiles require the frozen -Z forward / Y up basis")
        return cls(scale, "-Z", "Y")

    def to_dict(self) -> dict[str, Any]:
        return {"unit_scale_meters": self.unit_scale_meters, "forward_axis": self.forward_axis, "up_axis": self.up_axis}


@dataclass(frozen=True, slots=True)
class AssetRevisionBinding:
    asset_id: str
    revision_id: str
    content_sha256: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AssetRevisionBinding":
        if set(payload) != {"asset_id", "revision_id", "content_sha256"}:
            raise BlenderBoundaryError("AssetRevisionBinding has missing or unknown fields")
        try:
            asset = AssetId(str(payload["asset_id"]))
            revision = AssetRevisionId(str(payload["revision_id"]))
        except (TypeError, ValueError) as exc:
            raise BlenderBoundaryError("asset/revision identity must use R8 canonical IDs") from exc
        return cls(str(asset), str(revision), _sha(payload["content_sha256"], "content_sha256"))

    def to_dict(self) -> dict[str, Any]:
        return {"asset_id": self.asset_id, "revision_id": self.revision_id, "content_sha256": self.content_sha256}


@dataclass(frozen=True, slots=True)
class ProfilePiece:
    piece_id: str
    piece_type: ProfilePieceType
    object_id: str
    mesh_id: str | None
    required: bool

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ProfilePiece":
        if set(payload) != {"piece_id", "piece_type", "object_id", "mesh_id", "required"}:
            raise BlenderBoundaryError("ProfilePiece has missing or unknown fields")
        try:
            piece_type = ProfilePieceType(payload["piece_type"])
        except (TypeError, ValueError) as exc:
            raise BlenderBoundaryError("unsupported profile piece type") from exc
        mesh_id = payload["mesh_id"]
        if piece_type is ProfilePieceType.MESH:
            mesh_id = _id(mesh_id, "mesh_id")
        elif mesh_id is not None:
            raise BlenderBoundaryError("armature pieces must have mesh_id=null")
        return cls(
            _id(payload["piece_id"], "piece_id"),
            piece_type,
            _id(payload["object_id"], "object_id"),
            mesh_id,
            _bool(payload["required"], "required"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"piece_id": self.piece_id, "piece_type": self.piece_type.value, "object_id": self.object_id, "mesh_id": self.mesh_id, "required": self.required}


@dataclass(frozen=True, slots=True)
class MaterialSlotBinding:
    piece_id: str
    slot_id: str
    actual_name: str
    required: bool

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MaterialSlotBinding":
        if set(payload) != {"piece_id", "slot_id", "actual_name", "required"}:
            raise BlenderBoundaryError("MaterialSlotBinding has missing or unknown fields")
        return cls(
            _id(payload["piece_id"], "piece_id"),
            _id(payload["slot_id"], "slot_id"),
            _printable(payload["actual_name"], "actual_name"),
            _bool(payload["required"], "required"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"piece_id": self.piece_id, "slot_id": self.slot_id, "actual_name": self.actual_name, "required": self.required}


@dataclass(frozen=True, slots=True)
class ShapeKeyBinding:
    piece_id: str
    key_id: str
    actual_name: str
    required: bool

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ShapeKeyBinding":
        if set(payload) != {"piece_id", "key_id", "actual_name", "required"}:
            raise BlenderBoundaryError("ShapeKeyBinding has missing or unknown fields")
        return cls(
            _id(payload["piece_id"], "piece_id"),
            _id(payload["key_id"], "key_id"),
            _printable(payload["actual_name"], "actual_name"),
            _bool(payload["required"], "required"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"piece_id": self.piece_id, "key_id": self.key_id, "actual_name": self.actual_name, "required": self.required}


@dataclass(frozen=True, slots=True)
class SemanticZone:
    zone_id: str
    bone_ids: tuple[str, ...]
    piece_ids: tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SemanticZone":
        if set(payload) != {"zone_id", "bone_ids", "piece_ids"}:
            raise BlenderBoundaryError("SemanticZone has missing or unknown fields")
        return cls(
            _id(payload["zone_id"], "zone_id"),
            _id_array(payload["bone_ids"], "bone_ids", minimum=1),
            _id_array(payload["piece_ids"], "piece_ids", minimum=1),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"zone_id": self.zone_id, "bone_ids": list(self.bone_ids), "piece_ids": list(self.piece_ids)}


@dataclass(frozen=True, slots=True)
class OrganicProfileQAPolicy:
    exact_piece_inventory: bool
    exact_material_slots: bool
    exact_shape_keys: bool
    max_unmapped_deform_bones: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "OrganicProfileQAPolicy":
        required = {"exact_piece_inventory", "exact_material_slots", "exact_shape_keys", "max_unmapped_deform_bones"}
        if set(payload) != required:
            raise BlenderBoundaryError("OrganicProfileQAPolicy has missing or unknown fields")
        raw_limit = payload["max_unmapped_deform_bones"]
        if isinstance(raw_limit, bool) or not isinstance(raw_limit, int) or not 0 <= raw_limit <= 256:
            raise BlenderBoundaryError("max_unmapped_deform_bones must be an integer in [0, 256]")
        return cls(
            _bool(payload["exact_piece_inventory"], "exact_piece_inventory"),
            _bool(payload["exact_material_slots"], "exact_material_slots"),
            _bool(payload["exact_shape_keys"], "exact_shape_keys"),
            raw_limit,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "exact_piece_inventory": self.exact_piece_inventory,
            "exact_material_slots": self.exact_material_slots,
            "exact_shape_keys": self.exact_shape_keys,
            "max_unmapped_deform_bones": self.max_unmapped_deform_bones,
        }


@dataclass(frozen=True, slots=True)
class OrganicAssetProfile:
    version: int
    profile_id: str
    kind: OrganicProfileKind
    asset: AssetRevisionBinding
    coordinates: CoordinateProfile
    rig_id: str
    armature_id: str
    rig_profile_digest: str
    rig_semantic_digest: str
    pieces: tuple[ProfilePiece, ...]
    material_slots: tuple[MaterialSlotBinding, ...]
    shape_keys: tuple[ShapeKeyBinding, ...]
    semantic_zones: tuple[SemanticZone, ...]
    required_deform_bones: tuple[str, ...]
    animation_bones: tuple[str, ...]
    qa: OrganicProfileQAPolicy

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "OrganicAssetProfile":
        required = {
            "version", "profile_id", "kind", "asset", "coordinates", "rig_id", "armature_id",
            "rig_profile_digest", "rig_semantic_digest", "pieces", "material_slots", "shape_keys",
            "semantic_zones", "required_deform_bones", "animation_bones", "qa",
        }
        if set(payload) != required:
            raise BlenderBoundaryError("OrganicAssetProfile has missing or unknown fields")
        if payload["version"] != 1:
            raise BlenderBoundaryError("only OrganicAssetProfile version 1 is supported")
        try:
            kind = OrganicProfileKind(payload["kind"])
        except (TypeError, ValueError) as exc:
            raise BlenderBoundaryError("unsupported organic profile kind") from exc
        if not isinstance(payload["asset"], dict) or not isinstance(payload["coordinates"], dict) or not isinstance(payload["qa"], dict):
            raise BlenderBoundaryError("asset/coordinates/qa must be objects")

        def objects(name: str, maximum: int, *, minimum: int = 0) -> list[dict[str, Any]]:
            raw = payload[name]
            if not isinstance(raw, list) or not minimum <= len(raw) <= maximum or not all(isinstance(item, dict) for item in raw):
                raise BlenderBoundaryError(f"{name} must contain {minimum}-{maximum} objects")
            return raw

        pieces = tuple(ProfilePiece.from_dict(item) for item in objects("pieces", 128, minimum=2))
        if len({item.piece_id for item in pieces}) != len(pieces):
            raise BlenderBoundaryError("piece IDs must be unique")
        if len({item.object_id for item in pieces}) != len(pieces):
            raise BlenderBoundaryError("piece object IDs must be unique")
        armatures = [item for item in pieces if item.piece_type is ProfilePieceType.ARMATURE]
        if len(armatures) != 1:
            raise BlenderBoundaryError("profile requires exactly one armature piece")
        armature_id = _id(payload["armature_id"], "armature_id")
        if armatures[0].object_id != armature_id:
            raise BlenderBoundaryError("armature piece object_id must match armature_id")
        mesh_pieces = {item.piece_id: item for item in pieces if item.piece_type is ProfilePieceType.MESH}
        if not mesh_pieces:
            raise BlenderBoundaryError("profile requires at least one mesh piece")
        mesh_ids = [item.mesh_id for item in mesh_pieces.values()]
        if len(set(mesh_ids)) != len(mesh_ids):
            raise BlenderBoundaryError("mesh IDs must be unique across profile pieces")

        slots = tuple(MaterialSlotBinding.from_dict(item) for item in objects("material_slots", 512))
        if len({(item.piece_id, item.slot_id) for item in slots}) != len(slots):
            raise BlenderBoundaryError("material slots must be unique per piece/slot")
        shapes = tuple(ShapeKeyBinding.from_dict(item) for item in objects("shape_keys", 2048))
        if len({(item.piece_id, item.key_id) for item in shapes}) != len(shapes):
            raise BlenderBoundaryError("shape keys must be unique per piece/key")
        if len({(item.piece_id, item.actual_name) for item in shapes}) != len(shapes):
            raise BlenderBoundaryError("shape-key actual names must be unique per piece")
        for item in (*slots, *shapes):
            if item.piece_id not in mesh_pieces:
                raise BlenderBoundaryError("material/shape-key binding references a non-mesh or unknown piece")

        zones = tuple(SemanticZone.from_dict(item) for item in objects("semantic_zones", 128, minimum=1))
        if len({item.zone_id for item in zones}) != len(zones):
            raise BlenderBoundaryError("semantic zone IDs must be unique")
        piece_ids = {item.piece_id for item in pieces}
        for zone in zones:
            if any(piece_id not in piece_ids for piece_id in zone.piece_ids):
                raise BlenderBoundaryError("semantic zone references an unknown piece")

        required_deform = _id_array(payload["required_deform_bones"], "required_deform_bones", minimum=1)
        animation = _id_array(payload["animation_bones"], "animation_bones", minimum=1)
        zone_bones = {bone_id for zone in zones for bone_id in zone.bone_ids}
        if any(item not in zone_bones for item in required_deform):
            raise BlenderBoundaryError("every required deform bone must belong to a semantic zone")

        return cls(
            1,
            _id(payload["profile_id"], "profile_id"),
            kind,
            AssetRevisionBinding.from_dict(payload["asset"]),
            CoordinateProfile.from_dict(payload["coordinates"]),
            _id(payload["rig_id"], "rig_id"),
            armature_id,
            _sha(payload["rig_profile_digest"], "rig_profile_digest"),
            _sha(payload["rig_semantic_digest"], "rig_semantic_digest"),
            pieces,
            slots,
            shapes,
            zones,
            required_deform,
            animation,
            OrganicProfileQAPolicy.from_dict(payload["qa"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "profile_id": self.profile_id,
            "kind": self.kind.value,
            "asset": self.asset.to_dict(),
            "coordinates": self.coordinates.to_dict(),
            "rig_id": self.rig_id,
            "armature_id": self.armature_id,
            "rig_profile_digest": self.rig_profile_digest,
            "rig_semantic_digest": self.rig_semantic_digest,
            "pieces": [item.to_dict() for item in self.pieces],
            "material_slots": [item.to_dict() for item in self.material_slots],
            "shape_keys": [item.to_dict() for item in self.shape_keys],
            "semantic_zones": [item.to_dict() for item in self.semantic_zones],
            "required_deform_bones": list(self.required_deform_bones),
            "animation_bones": list(self.animation_bones),
            "qa": self.qa.to_dict(),
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())

    @property
    def mesh_piece_ids(self) -> tuple[str, ...]:
        return tuple(item.piece_id for item in self.pieces if item.piece_type is ProfilePieceType.MESH)
