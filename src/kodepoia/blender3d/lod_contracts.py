from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from kodepoia.assets.contracts import AssetId, AssetKind, AssetRevision, AssetRevisionId, AssetRole, AssetStatus, LineageRef, PreservationPolicy, ProvenanceRef, ReuseScope
from .errors import BlenderBoundaryError
from .serialization import canonical_sha256

_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class LODAssetMode(StrEnum):
    STATIC = "static"
    SKINNED = "skinned"


class ShapeKeyLODPolicy(StrEnum):
    BLOCK_IF_PRESENT = "block_if_present"
    DROP_EXPLICIT = "drop_explicit"


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


def _integer(value: Any, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise BlenderBoundaryError(f"{field} must be an integer between {minimum} and {maximum}")
    return value


def _string_array(value: Any, field: str, maximum: int = 512) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > maximum or not all(isinstance(item, str) for item in value):
        raise BlenderBoundaryError(f"{field} must be an array of at most {maximum} strings")
    result = tuple(value)
    if len(set(result)) != len(result):
        raise BlenderBoundaryError(f"{field} must contain unique strings")
    if any(not item or len(item) > 128 or any(ord(ch) < 32 for ch in item) for item in result):
        raise BlenderBoundaryError(f"{field} contains an invalid name")
    return result


@dataclass(frozen=True, slots=True)
class LODTier:
    tier_id: str
    output_asset_id: str
    ratio: float
    min_triangles: int
    max_triangles: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LODTier":
        if set(payload) != {"tier_id", "output_asset_id", "ratio", "min_triangles", "max_triangles"}:
            raise BlenderBoundaryError("LODTier has missing or unknown fields")
        try:
            output_asset = AssetId(str(payload["output_asset_id"]))
        except (TypeError, ValueError) as exc:
            raise BlenderBoundaryError("output_asset_id must be an R8 AssetId") from exc
        ratio = _number(payload["ratio"], "ratio", 0.01, 0.99)
        minimum = _integer(payload["min_triangles"], "min_triangles", 1, 50_000_000)
        maximum = _integer(payload["max_triangles"], "max_triangles", 1, 50_000_000)
        if minimum > maximum:
            raise BlenderBoundaryError("min_triangles cannot exceed max_triangles")
        return cls(_id(payload["tier_id"], "tier_id"), str(output_asset), ratio, minimum, maximum)

    def to_dict(self) -> dict[str, Any]:
        return {"tier_id": self.tier_id, "output_asset_id": self.output_asset_id, "ratio": self.ratio, "min_triangles": self.min_triangles, "max_triangles": self.max_triangles}


@dataclass(frozen=True, slots=True)
class LODPreservationPolicy:
    preserve_material_slots: bool
    preserve_uv_layers: bool
    preserve_normals: bool
    shape_keys: ShapeKeyLODPolicy
    required_vertex_groups: tuple[str, ...]
    max_extent_relative_error: float
    max_surface_area_relative_error: float
    max_weight_sum_error: float
    max_influences: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LODPreservationPolicy":
        required = {"preserve_material_slots", "preserve_uv_layers", "preserve_normals", "shape_keys", "required_vertex_groups", "max_extent_relative_error", "max_surface_area_relative_error", "max_weight_sum_error", "max_influences"}
        if set(payload) != required:
            raise BlenderBoundaryError("LODPreservationPolicy has missing or unknown fields")
        for field in ("preserve_material_slots", "preserve_uv_layers", "preserve_normals"):
            if not isinstance(payload[field], bool):
                raise BlenderBoundaryError(f"{field} must be boolean")
        try:
            shape_keys = ShapeKeyLODPolicy(payload["shape_keys"])
        except (TypeError, ValueError) as exc:
            raise BlenderBoundaryError("unsupported shape-key LOD policy") from exc
        return cls(payload["preserve_material_slots"], payload["preserve_uv_layers"], payload["preserve_normals"], shape_keys, _string_array(payload["required_vertex_groups"], "required_vertex_groups"), _number(payload["max_extent_relative_error"], "max_extent_relative_error", 0.0, 1.0), _number(payload["max_surface_area_relative_error"], "max_surface_area_relative_error", 0.0, 1.0), _number(payload["max_weight_sum_error"], "max_weight_sum_error", 0.0, 1.0), _integer(payload["max_influences"], "max_influences", 1, 16))

    def to_dict(self) -> dict[str, Any]:
        return {"preserve_material_slots": self.preserve_material_slots, "preserve_uv_layers": self.preserve_uv_layers, "preserve_normals": self.preserve_normals, "shape_keys": self.shape_keys.value, "required_vertex_groups": list(self.required_vertex_groups), "max_extent_relative_error": self.max_extent_relative_error, "max_surface_area_relative_error": self.max_surface_area_relative_error, "max_weight_sum_error": self.max_weight_sum_error, "max_influences": self.max_influences}


@dataclass(frozen=True, slots=True)
class LODProfile:
    version: int
    profile_id: str
    input_blend_sha256: str
    source_asset_id: str
    source_revision_id: str
    source_content_sha256: str
    source_object_id: str
    asset_mode: LODAssetMode
    mesh_qa_profile_digest: str
    rig_profile_digest: str | None
    ratio_tolerance: float
    tiers: tuple[LODTier, ...]
    preservation: LODPreservationPolicy

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LODProfile":
        required = {"version", "profile_id", "input_blend_sha256", "source_asset_id", "source_revision_id", "source_content_sha256", "source_object_id", "asset_mode", "mesh_qa_profile_digest", "rig_profile_digest", "ratio_tolerance", "tiers", "preservation"}
        if set(payload) != required:
            raise BlenderBoundaryError("LODProfile has missing or unknown fields")
        if payload["version"] != 1:
            raise BlenderBoundaryError("only LODProfile version 1 is supported")
        try:
            source_asset = AssetId(str(payload["source_asset_id"]))
            source_revision = AssetRevisionId(str(payload["source_revision_id"]))
            mode = LODAssetMode(payload["asset_mode"])
        except (TypeError, ValueError) as exc:
            raise BlenderBoundaryError("invalid R8 asset identity or LOD mode") from exc
        input_sha = _sha(payload["input_blend_sha256"], "input_blend_sha256")
        source_sha = _sha(payload["source_content_sha256"], "source_content_sha256")
        if input_sha != source_sha:
            raise BlenderBoundaryError("input_blend_sha256 must equal source_content_sha256")
        rig_digest = payload["rig_profile_digest"]
        if rig_digest is not None:
            rig_digest = _sha(rig_digest, "rig_profile_digest")
        if mode is LODAssetMode.SKINNED and rig_digest is None:
            raise BlenderBoundaryError("skinned LOD profiles require rig_profile_digest")
        if mode is LODAssetMode.STATIC and rig_digest is not None:
            raise BlenderBoundaryError("static LOD profiles require rig_profile_digest=null")
        raw_tiers = payload["tiers"]
        if not isinstance(raw_tiers, list) or not 1 <= len(raw_tiers) <= 8 or not all(isinstance(item, dict) for item in raw_tiers):
            raise BlenderBoundaryError("tiers must contain 1-8 objects")
        tiers = tuple(LODTier.from_dict(item) for item in raw_tiers)
        if len({item.tier_id for item in tiers}) != len(tiers):
            raise BlenderBoundaryError("LOD tier IDs must be unique")
        if len({item.output_asset_id for item in tiers}) != len(tiers):
            raise BlenderBoundaryError("LOD output asset IDs must be unique")
        if str(source_asset) in {item.output_asset_id for item in tiers}:
            raise BlenderBoundaryError("LOD tiers may not overwrite the source asset identity")
        ratios = [item.ratio for item in tiers]
        if ratios != sorted(ratios, reverse=True) or len(set(ratios)) != len(ratios):
            raise BlenderBoundaryError("LOD ratios must be strictly descending")
        preservation_payload = payload["preservation"]
        if not isinstance(preservation_payload, dict):
            raise BlenderBoundaryError("preservation must be an object")
        preservation = LODPreservationPolicy.from_dict(preservation_payload)
        if mode is LODAssetMode.SKINNED and not preservation.required_vertex_groups:
            raise BlenderBoundaryError("skinned LOD profiles require governed vertex groups")
        return cls(1, _id(payload["profile_id"], "profile_id"), input_sha, str(source_asset), str(source_revision), source_sha, _id(payload["source_object_id"], "source_object_id"), mode, _sha(payload["mesh_qa_profile_digest"], "mesh_qa_profile_digest"), rig_digest, _number(payload["ratio_tolerance"], "ratio_tolerance", 0.0, 0.25), tiers, preservation)

    def to_dict(self) -> dict[str, Any]:
        return {"version": 1, "profile_id": self.profile_id, "input_blend_sha256": self.input_blend_sha256, "source_asset_id": self.source_asset_id, "source_revision_id": self.source_revision_id, "source_content_sha256": self.source_content_sha256, "source_object_id": self.source_object_id, "asset_mode": self.asset_mode.value, "mesh_qa_profile_digest": self.mesh_qa_profile_digest, "rig_profile_digest": self.rig_profile_digest, "ratio_tolerance": self.ratio_tolerance, "tiers": [item.to_dict() for item in self.tiers], "preservation": self.preservation.to_dict()}

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


def validate_lod_source_revision(profile: LODProfile, revision: AssetRevision) -> None:
    if str(revision.asset_id) != profile.source_asset_id or str(revision.revision_id) != profile.source_revision_id:
        raise BlenderBoundaryError("R8 source asset/revision identity mismatch")
    if revision.kind is not AssetKind.MODEL_3D or revision.status is not AssetStatus.READY:
        raise BlenderBoundaryError("R10.9 requires a READY R8 model_3d source revision")
    if revision.content_sha256 != profile.source_content_sha256:
        raise BlenderBoundaryError("R8 source content digest mismatch")
    if not revision.provenance:
        raise BlenderBoundaryError("R10.9 source revision requires retained R8 provenance")


def make_lod_variant_revision(profile: LODProfile, tier: LODTier, *, output_sha256: str, output_length: int, source_revision: AssetRevision) -> AssetRevision:
    validate_lod_source_revision(profile, source_revision)
    digest = _sha(output_sha256, "output_sha256")
    if isinstance(output_length, bool) or not isinstance(output_length, int) or output_length < 1:
        raise BlenderBoundaryError("output_length must be a positive integer")
    if tier not in profile.tiers:
        raise BlenderBoundaryError("tier does not belong to LOD profile")
    transform_id = f"blender.lod.v1.{profile.profile_id}.{tier.tier_id}"
    return AssetRevision.create(asset_id=AssetId(tier.output_asset_id), role=AssetRole.DERIVED, kind=AssetKind.MODEL_3D, content_sha256=digest, content_length=output_length, reuse_scope=ReuseScope.VAULT_LOCAL, preservation=PreservationPolicy.EVICTABLE_DERIVED, provenance=(ProvenanceRef("transform", transform_id),), lineage=(LineageRef(AssetRevisionId(profile.source_revision_id), relation="lod_variant", transform_id=transform_id),), status=AssetStatus.READY)
