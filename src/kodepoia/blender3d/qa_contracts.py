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


class MeshAssetClass(StrEnum):
    CLOSED_STATIC = "closed_static"
    OPEN_STATIC = "open_static"
    CHARACTER = "character"
    ANIMAL = "animal"


class BoundaryPolicy(StrEnum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"


class UVOverlapPolicy(StrEnum):
    IGNORE = "ignore"
    WARN = "warn"
    BLOCK = "block"


class MeshRepairOperation(StrEnum):
    RECALCULATE_NORMALS = "recalculate_normals"


def _plain_id(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise BlenderBoundaryError(f"{field} must match ^[a-z][a-z0-9_.-]{{0,63}}$")
    return value


def _sha(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise BlenderBoundaryError(f"{field} must be a lowercase SHA-256")
    return value


def _int(value: Any, *, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise BlenderBoundaryError(f"{field} must be an integer between {minimum} and {maximum}")
    return value


def _number(value: Any, *, field: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BlenderBoundaryError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise BlenderBoundaryError(f"{field} must be finite and between {minimum} and {maximum}")
    return result


@dataclass(frozen=True, slots=True)
class MeshQABudgets:
    max_objects: int = 64
    max_triangles: int = 500_000
    max_materials: int = 64
    max_textures: int = 256
    max_shape_keys: int = 128
    max_uv_layers: int = 8
    max_loose_vertices: int = 0
    max_loose_edges: int = 0
    max_non_manifold_edges: int = 0
    max_duplicate_vertex_indicators: int = 0
    max_zero_area_uv_triangles: int = 0
    max_scale_ratio: float = 100.0

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MeshQABudgets":
        allowed = {
            "max_objects", "max_triangles", "max_materials", "max_textures", "max_shape_keys",
            "max_uv_layers", "max_loose_vertices", "max_loose_edges", "max_non_manifold_edges",
            "max_duplicate_vertex_indicators", "max_zero_area_uv_triangles", "max_scale_ratio",
        }
        if set(payload) - allowed:
            raise BlenderBoundaryError("Mesh QA budgets contain unknown fields")
        return cls(
            max_objects=_int(payload.get("max_objects", 64), field="max_objects", minimum=1, maximum=1024),
            max_triangles=_int(payload.get("max_triangles", 500_000), field="max_triangles", minimum=1, maximum=50_000_000),
            max_materials=_int(payload.get("max_materials", 64), field="max_materials", minimum=0, maximum=4096),
            max_textures=_int(payload.get("max_textures", 256), field="max_textures", minimum=0, maximum=16384),
            max_shape_keys=_int(payload.get("max_shape_keys", 128), field="max_shape_keys", minimum=0, maximum=4096),
            max_uv_layers=_int(payload.get("max_uv_layers", 8), field="max_uv_layers", minimum=0, maximum=64),
            max_loose_vertices=_int(payload.get("max_loose_vertices", 0), field="max_loose_vertices", minimum=0, maximum=10_000_000),
            max_loose_edges=_int(payload.get("max_loose_edges", 0), field="max_loose_edges", minimum=0, maximum=10_000_000),
            max_non_manifold_edges=_int(payload.get("max_non_manifold_edges", 0), field="max_non_manifold_edges", minimum=0, maximum=10_000_000),
            max_duplicate_vertex_indicators=_int(payload.get("max_duplicate_vertex_indicators", 0), field="max_duplicate_vertex_indicators", minimum=0, maximum=10_000_000),
            max_zero_area_uv_triangles=_int(payload.get("max_zero_area_uv_triangles", 0), field="max_zero_area_uv_triangles", minimum=0, maximum=10_000_000),
            max_scale_ratio=_number(payload.get("max_scale_ratio", 100.0), field="max_scale_ratio", minimum=1.0, maximum=1_000_000.0),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_objects": self.max_objects,
            "max_triangles": self.max_triangles,
            "max_materials": self.max_materials,
            "max_textures": self.max_textures,
            "max_shape_keys": self.max_shape_keys,
            "max_uv_layers": self.max_uv_layers,
            "max_loose_vertices": self.max_loose_vertices,
            "max_loose_edges": self.max_loose_edges,
            "max_non_manifold_edges": self.max_non_manifold_edges,
            "max_duplicate_vertex_indicators": self.max_duplicate_vertex_indicators,
            "max_zero_area_uv_triangles": self.max_zero_area_uv_triangles,
            "max_scale_ratio": self.max_scale_ratio,
        }


@dataclass(frozen=True, slots=True)
class MeshQAProfile:
    version: int
    profile_id: str
    asset_class: MeshAssetClass
    input_blend_sha256: str
    object_ids: tuple[str, ...]
    budgets: MeshQABudgets
    boundary_policy: BoundaryPolicy
    overlap_policy: UVOverlapPolicy
    require_uv: bool
    require_consistent_winding: bool
    minimum_face_area: float
    duplicate_tolerance: float
    uv_zero_area_epsilon: float

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MeshQAProfile":
        required = {"version", "profile_id", "asset_class", "input_blend_sha256", "object_ids", "budgets"}
        allowed = required | {
            "boundary_policy", "overlap_policy", "require_uv", "require_consistent_winding",
            "minimum_face_area", "duplicate_tolerance", "uv_zero_area_epsilon",
        }
        if set(payload) - allowed or not required.issubset(payload):
            raise BlenderBoundaryError("Mesh QA profile has missing or unknown fields")
        if payload["version"] != 1:
            raise BlenderBoundaryError("Only Mesh QA profile version 1 is supported")
        raw_ids = payload["object_ids"]
        if not isinstance(raw_ids, list) or not raw_ids or len(raw_ids) > 256:
            raise BlenderBoundaryError("object_ids must contain 1-256 governed object IDs")
        object_ids = tuple(_plain_id(item, field="object_id") for item in raw_ids)
        if len(set(object_ids)) != len(object_ids):
            raise BlenderBoundaryError("object_ids must be unique")
        try:
            asset_class = MeshAssetClass(payload["asset_class"])
            boundary_policy = BoundaryPolicy(payload.get("boundary_policy", "block"))
            overlap_policy = UVOverlapPolicy(payload.get("overlap_policy", "ignore"))
        except (ValueError, TypeError) as exc:
            raise BlenderBoundaryError("Unsupported Mesh QA policy value") from exc
        for field in ("require_uv", "require_consistent_winding"):
            if field in payload and not isinstance(payload[field], bool):
                raise BlenderBoundaryError(f"{field} must be boolean")
        budgets_payload = payload["budgets"]
        if not isinstance(budgets_payload, dict):
            raise BlenderBoundaryError("budgets must be an object")
        return cls(
            version=1,
            profile_id=_plain_id(payload["profile_id"], field="profile_id"),
            asset_class=asset_class,
            input_blend_sha256=_sha(payload["input_blend_sha256"], field="input_blend_sha256"),
            object_ids=object_ids,
            budgets=MeshQABudgets.from_dict(budgets_payload),
            boundary_policy=boundary_policy,
            overlap_policy=overlap_policy,
            require_uv=payload.get("require_uv", True),
            require_consistent_winding=payload.get("require_consistent_winding", True),
            minimum_face_area=_number(payload.get("minimum_face_area", 1e-12), field="minimum_face_area", minimum=0.0, maximum=1.0),
            duplicate_tolerance=_number(payload.get("duplicate_tolerance", 1e-7), field="duplicate_tolerance", minimum=1e-12, maximum=1e-2),
            uv_zero_area_epsilon=_number(payload.get("uv_zero_area_epsilon", 1e-12), field="uv_zero_area_epsilon", minimum=0.0, maximum=1e-3),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "profile_id": self.profile_id,
            "asset_class": self.asset_class.value,
            "input_blend_sha256": self.input_blend_sha256,
            "object_ids": list(self.object_ids),
            "budgets": self.budgets.to_dict(),
            "boundary_policy": self.boundary_policy.value,
            "overlap_policy": self.overlap_policy.value,
            "require_uv": self.require_uv,
            "require_consistent_winding": self.require_consistent_winding,
            "minimum_face_area": self.minimum_face_area,
            "duplicate_tolerance": self.duplicate_tolerance,
            "uv_zero_area_epsilon": self.uv_zero_area_epsilon,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())


@dataclass(frozen=True, slots=True)
class MeshRepairRecipe:
    version: int
    recipe_id: str
    input_blend_sha256: str
    object_ids: tuple[str, ...]
    operation: MeshRepairOperation

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MeshRepairRecipe":
        if set(payload) != {"version", "recipe_id", "input_blend_sha256", "object_ids", "operation"}:
            raise BlenderBoundaryError("Mesh repair recipe requires exactly version/recipe_id/input_blend_sha256/object_ids/operation")
        if payload["version"] != 1:
            raise BlenderBoundaryError("Only Mesh repair recipe version 1 is supported")
        raw_ids = payload["object_ids"]
        if not isinstance(raw_ids, list) or not raw_ids or len(raw_ids) > 256:
            raise BlenderBoundaryError("Repair object_ids must contain 1-256 IDs")
        object_ids = tuple(_plain_id(item, field="object_id") for item in raw_ids)
        if len(set(object_ids)) != len(object_ids):
            raise BlenderBoundaryError("Repair object_ids must be unique")
        try:
            operation = MeshRepairOperation(payload["operation"])
        except (ValueError, TypeError) as exc:
            raise BlenderBoundaryError("Unsupported Mesh repair operation") from exc
        return cls(1, _plain_id(payload["recipe_id"], field="recipe_id"), _sha(payload["input_blend_sha256"], field="input_blend_sha256"), object_ids, operation)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "recipe_id": self.recipe_id,
            "input_blend_sha256": self.input_blend_sha256,
            "object_ids": list(self.object_ids),
            "operation": self.operation.value,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())
