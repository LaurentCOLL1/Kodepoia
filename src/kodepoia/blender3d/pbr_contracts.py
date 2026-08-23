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


class UVMethod(StrEnum):
    KEEP = "keep"
    SMART = "smart"
    ANGLE_BASED = "angle_based"
    CONFORMAL = "conformal"


class TextureRole(StrEnum):
    BASE_COLOR = "base_color"
    METALLIC = "metallic"
    ROUGHNESS = "roughness"
    NORMAL = "normal"
    EMISSIVE = "emissive"


_COLOR_ROLES = frozenset({TextureRole.BASE_COLOR, TextureRole.EMISSIVE})
_DATA_ROLES = frozenset({TextureRole.METALLIC, TextureRole.ROUGHNESS, TextureRole.NORMAL})


def _id(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise BlenderBoundaryError(f"{field} must match ^[a-z][a-z0-9_.-]{{0,63}}$")
    return value


def _sha(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise BlenderBoundaryError(f"{field} must be a lowercase SHA-256")
    return value


def _number(value: Any, *, field: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BlenderBoundaryError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise BlenderBoundaryError(f"{field} must be between {minimum} and {maximum}")
    return result


def _rgba(value: Any, *, field: str) -> tuple[float, float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise BlenderBoundaryError(f"{field} must contain four values")
    return tuple(_number(item, field=field, minimum=0.0, maximum=1.0) for item in value)  # type: ignore[return-value]


def _rgb(value: Any, *, field: str) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise BlenderBoundaryError(f"{field} must contain three values")
    return tuple(_number(item, field=field, minimum=0.0, maximum=64.0) for item in value)  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class UVSpec:
    object_id: str
    map_name: str
    method: UVMethod
    margin: float
    angle_limit: float

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "UVSpec":
        allowed = {"object_id", "map_name", "method", "margin", "angle_limit"}
        if set(payload) - allowed:
            raise BlenderBoundaryError("UV spec contains unknown fields")
        object_id = _id(payload.get("object_id"), field="object_id")
        map_name = payload.get("map_name", "UVMap")
        if not isinstance(map_name, str) or not map_name or len(map_name) > 48 or "/" in map_name or "\\" in map_name:
            raise BlenderBoundaryError("UV map_name must be a bounded plain name")
        try:
            method = UVMethod(payload.get("method", "smart"))
        except (ValueError, TypeError) as exc:
            raise BlenderBoundaryError("Unsupported UV method") from exc
        margin = _number(payload.get("margin", 0.001), field="margin", minimum=0.0, maximum=0.1)
        angle_limit = _number(payload.get("angle_limit", 1.15192), field="angle_limit", minimum=0.01, maximum=1.5708)
        return cls(object_id, map_name, method, margin, angle_limit)

    def to_dict(self) -> dict[str, Any]:
        return {"object_id": self.object_id, "map_name": self.map_name, "method": self.method.value, "margin": self.margin, "angle_limit": self.angle_limit}


@dataclass(frozen=True, slots=True)
class TextureRef:
    source_id: str
    role: TextureRole
    sha256: str
    uv_map: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TextureRef":
        if set(payload) != {"source_id", "role", "sha256", "uv_map"}:
            raise BlenderBoundaryError("Texture refs require source_id/role/sha256/uv_map")
        source_id = _id(payload["source_id"], field="source_id")
        try:
            role = TextureRole(payload["role"])
        except (ValueError, TypeError) as exc:
            raise BlenderBoundaryError("Unsupported texture role") from exc
        sha256 = _sha(payload["sha256"], field="texture sha256")
        uv_map = payload["uv_map"]
        if not isinstance(uv_map, str) or not uv_map or len(uv_map) > 48 or "/" in uv_map or "\\" in uv_map:
            raise BlenderBoundaryError("Texture uv_map must be a bounded plain name")
        return cls(source_id, role, sha256, uv_map)

    @property
    def color_semantics(self) -> str:
        return "COLOR" if self.role in _COLOR_ROLES else "DATA"

    def to_dict(self) -> dict[str, str]:
        return {"source_id": self.source_id, "role": self.role.value, "sha256": self.sha256, "uv_map": self.uv_map}


@dataclass(frozen=True, slots=True)
class MaterialSpec:
    material_id: str
    object_ids: tuple[str, ...]
    base_color: tuple[float, float, float, float]
    metallic: float
    roughness: float
    emission_color: tuple[float, float, float]
    emission_strength: float
    alpha: float
    normal_strength: float
    textures: tuple[TextureRef, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MaterialSpec":
        allowed = {"material_id", "object_ids", "base_color", "metallic", "roughness", "emission_color", "emission_strength", "alpha", "normal_strength", "textures"}
        if set(payload) - allowed:
            raise BlenderBoundaryError("Material spec contains unknown fields")
        material_id = _id(payload.get("material_id"), field="material_id")
        object_ids_raw = payload.get("object_ids")
        if not isinstance(object_ids_raw, list) or not object_ids_raw or len(object_ids_raw) > 64:
            raise BlenderBoundaryError("Material object_ids must contain 1-64 IDs")
        object_ids = tuple(_id(item, field="object_id") for item in object_ids_raw)
        if len(set(object_ids)) != len(object_ids):
            raise BlenderBoundaryError("Material object_ids must be unique")
        raw_textures = payload.get("textures", [])
        if not isinstance(raw_textures, list) or len(raw_textures) > len(TextureRole):
            raise BlenderBoundaryError("Material textures exceed the role budget")
        textures = tuple(TextureRef.from_dict(item) for item in raw_textures if isinstance(item, dict))
        if len(textures) != len(raw_textures):
            raise BlenderBoundaryError("Every texture ref must be an object")
        roles = [item.role for item in textures]
        sources = [item.source_id for item in textures]
        if len(set(roles)) != len(roles):
            raise BlenderBoundaryError("A material may bind each texture role only once")
        if len(set(sources)) != len(sources):
            raise BlenderBoundaryError("A material may bind a source_id only once")
        return cls(
            material_id=material_id,
            object_ids=object_ids,
            base_color=_rgba(payload.get("base_color", [0.8, 0.8, 0.8, 1.0]), field="base_color"),
            metallic=_number(payload.get("metallic", 0.0), field="metallic", minimum=0.0, maximum=1.0),
            roughness=_number(payload.get("roughness", 0.5), field="roughness", minimum=0.0, maximum=1.0),
            emission_color=_rgb(payload.get("emission_color", [0.0, 0.0, 0.0]), field="emission_color"),
            emission_strength=_number(payload.get("emission_strength", 0.0), field="emission_strength", minimum=0.0, maximum=64.0),
            alpha=_number(payload.get("alpha", 1.0), field="alpha", minimum=0.0, maximum=1.0),
            normal_strength=_number(payload.get("normal_strength", 1.0), field="normal_strength", minimum=0.0, maximum=8.0),
            textures=textures,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "material_id": self.material_id,
            "object_ids": list(self.object_ids),
            "base_color": list(self.base_color),
            "metallic": self.metallic,
            "roughness": self.roughness,
            "emission_color": list(self.emission_color),
            "emission_strength": self.emission_strength,
            "alpha": self.alpha,
            "normal_strength": self.normal_strength,
            "textures": [item.to_dict() for item in self.textures],
        }


@dataclass(frozen=True, slots=True)
class PBRRecipe:
    version: int
    recipe_id: str
    input_blend_sha256: str
    uv: tuple[UVSpec, ...]
    materials: tuple[MaterialSpec, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PBRRecipe":
        if set(payload) != {"version", "recipe_id", "input_blend_sha256", "uv", "materials"}:
            raise BlenderBoundaryError("PBR recipe requires exactly version/recipe_id/input_blend_sha256/uv/materials")
        if payload["version"] != 1:
            raise BlenderBoundaryError("Only PBR recipe version 1 is supported")
        uv_raw = payload["uv"]
        materials_raw = payload["materials"]
        if not isinstance(uv_raw, list) or len(uv_raw) > 128:
            raise BlenderBoundaryError("PBR recipe uv must be a bounded array")
        if not isinstance(materials_raw, list) or not materials_raw or len(materials_raw) > 128:
            raise BlenderBoundaryError("PBR recipe requires 1-128 materials")
        uv = tuple(UVSpec.from_dict(item) for item in uv_raw if isinstance(item, dict))
        materials = tuple(MaterialSpec.from_dict(item) for item in materials_raw if isinstance(item, dict))
        if len(uv) != len(uv_raw) or len(materials) != len(materials_raw):
            raise BlenderBoundaryError("PBR recipe entries must be objects")
        if len({item.object_id for item in uv}) != len(uv):
            raise BlenderBoundaryError("Only one UV policy is allowed per object")
        if len({item.material_id for item in materials}) != len(materials):
            raise BlenderBoundaryError("Material IDs must be unique")
        all_sources = [texture.source_id for material in materials for texture in material.textures]
        source_hashes: dict[str, str] = {}
        for material in materials:
            for texture in material.textures:
                prior = source_hashes.setdefault(texture.source_id, texture.sha256)
                if prior != texture.sha256:
                    raise BlenderBoundaryError("A texture source_id cannot claim multiple digests")
        if len(all_sources) > 256:
            raise BlenderBoundaryError("PBR recipe exceeds texture reference budget")
        return cls(1, _id(payload["recipe_id"], field="recipe_id"), _sha(payload["input_blend_sha256"], field="input blend sha256"), uv, materials)

    def to_dict(self) -> dict[str, Any]:
        return {"version": 1, "recipe_id": self.recipe_id, "input_blend_sha256": self.input_blend_sha256, "uv": [item.to_dict() for item in self.uv], "materials": [item.to_dict() for item in self.materials]}

    @property
    def digest(self) -> str:
        return canonical_sha256(self.to_dict())

    @property
    def texture_sources(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for material in self.materials:
            for texture in material.textures:
                result[texture.source_id] = texture.sha256
        return result
