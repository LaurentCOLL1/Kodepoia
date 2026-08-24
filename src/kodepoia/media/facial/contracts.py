from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from kodepoia.media.contracts import bounded_text, sha256_hex, stable_id
from kodepoia.media.serialization import canonical_sha256


class FacialTargetKind(StrEnum):
    BLEND_SHAPE = "blend_shape"
    BONE = "bone"


def _finite(value: float, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


@dataclass(frozen=True, slots=True)
class FacialTarget:
    target_id: str
    semantic: str
    kind: FacialTargetKind
    minimum: float
    maximum: float
    source_digest: str

    def __post_init__(self) -> None:
        stable_id(self.target_id, field="target_id")
        stable_id(self.semantic, field="semantic")
        if not isinstance(self.kind, FacialTargetKind):
            raise TypeError("kind must be FacialTargetKind")
        minimum = _finite(self.minimum, field="minimum")
        maximum = _finite(self.maximum, field="maximum")
        if maximum <= minimum:
            raise ValueError("target maximum must exceed minimum")
        sha256_hex(self.source_digest, field="source_digest")

    def canonical(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "semantic": self.semantic,
            "kind": self.kind.value,
            "minimum": float(self.minimum),
            "maximum": float(self.maximum),
            "source_digest": self.source_digest,
        }


@dataclass(frozen=True, slots=True)
class FacialTargetCatalog:
    catalog_id: str
    rig_digest: str
    targets: tuple[FacialTarget, ...]

    def __post_init__(self) -> None:
        stable_id(self.catalog_id, field="catalog_id")
        sha256_hex(self.rig_digest, field="rig_digest")
        if not self.targets or len(self.targets) > 512:
            raise ValueError("facial target catalog must contain 1..512 targets")
        ids = [target.target_id for target in self.targets]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate facial target_id")

    def target(self, target_id: str) -> FacialTarget:
        for target in self.targets:
            if target.target_id == target_id:
                return target
        raise KeyError(target_id)

    def canonical(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "rig_digest": self.rig_digest,
            "targets": [target.canonical() for target in sorted(self.targets, key=lambda item: item.target_id)],
        }

    def digest(self) -> str:
        return canonical_sha256({"schema": "kodepoia.r11.facial_target_catalog", "version": 1, "payload": self.canonical()})


@dataclass(frozen=True, slots=True)
class FacialMapping:
    source_semantic: str
    target_id: str
    weight: float

    def __post_init__(self) -> None:
        stable_id(self.source_semantic, field="source_semantic")
        stable_id(self.target_id, field="target_id")
        _finite(self.weight, field="weight")

    def canonical(self) -> dict[str, Any]:
        return {"source_semantic": self.source_semantic, "target_id": self.target_id, "weight": float(self.weight)}


@dataclass(frozen=True, slots=True)
class FacialLODLevel:
    lod_id: str
    included_target_ids: tuple[str, ...]
    max_keys_per_second: int
    required_semantics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        stable_id(self.lod_id, field="lod_id")
        if not self.included_target_ids or len(self.included_target_ids) > 512:
            raise ValueError("LOD must include 1..512 targets")
        for target_id in self.included_target_ids:
            stable_id(target_id, field="included_target_id")
        if len(set(self.included_target_ids)) != len(self.included_target_ids):
            raise ValueError("LOD contains duplicate target ids")
        if isinstance(self.max_keys_per_second, bool) or not isinstance(self.max_keys_per_second, int) or not 1 <= self.max_keys_per_second <= 240:
            raise ValueError("max_keys_per_second must be 1..240")
        for semantic in self.required_semantics:
            stable_id(semantic, field="required_semantic")

    def canonical(self) -> dict[str, Any]:
        return {
            "lod_id": self.lod_id,
            "included_target_ids": sorted(self.included_target_ids),
            "max_keys_per_second": self.max_keys_per_second,
            "required_semantics": sorted(self.required_semantics),
        }


@dataclass(frozen=True, slots=True)
class FacialPerformanceProfile:
    profile_id: str
    target_catalog_digest: str
    viseme_set_digest: str
    mappings: tuple[FacialMapping, ...]
    lod_levels: tuple[FacialLODLevel, ...]
    clamp_out_of_range: bool = False

    def __post_init__(self) -> None:
        stable_id(self.profile_id, field="profile_id")
        sha256_hex(self.target_catalog_digest, field="target_catalog_digest")
        sha256_hex(self.viseme_set_digest, field="viseme_set_digest")
        if not self.mappings or len(self.mappings) > 2048:
            raise ValueError("profile mappings must contain 1..2048 entries")
        if not self.lod_levels or len(self.lod_levels) > 16:
            raise ValueError("profile must define 1..16 LOD levels")
        keys = [(mapping.source_semantic, mapping.target_id) for mapping in self.mappings]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate source_semantic/target mapping")
        lod_ids = [lod.lod_id for lod in self.lod_levels]
        if len(lod_ids) != len(set(lod_ids)):
            raise ValueError("duplicate LOD ids")

    def mappings_for(self, semantic: str) -> tuple[FacialMapping, ...]:
        return tuple(mapping for mapping in self.mappings if mapping.source_semantic == semantic)

    def lod(self, lod_id: str) -> FacialLODLevel:
        for lod in self.lod_levels:
            if lod.lod_id == lod_id:
                return lod
        raise KeyError(lod_id)

    def canonical(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "target_catalog_digest": self.target_catalog_digest,
            "viseme_set_digest": self.viseme_set_digest,
            "mappings": [item.canonical() for item in sorted(self.mappings, key=lambda item: (item.source_semantic, item.target_id))],
            "lod_levels": [item.canonical() for item in sorted(self.lod_levels, key=lambda item: item.lod_id)],
            "clamp_out_of_range": self.clamp_out_of_range,
        }

    def digest(self) -> str:
        return canonical_sha256({"schema": "kodepoia.r11.facial_performance_profile", "version": 1, "payload": self.canonical()})


def validate_profile_against_catalog(profile: FacialPerformanceProfile, catalog: FacialTargetCatalog) -> None:
    if profile.target_catalog_digest != catalog.digest():
        raise ValueError("profile target catalog digest does not match R10 metadata")
    for mapping in profile.mappings:
        target = catalog.target(mapping.target_id)
        if not profile.clamp_out_of_range and not target.minimum <= mapping.weight <= target.maximum:
            raise ValueError("mapping weight exceeds target range")
    by_semantic = {target.semantic: target.target_id for target in catalog.targets}
    for lod in profile.lod_levels:
        for target_id in lod.included_target_ids:
            catalog.target(target_id)
        for semantic in lod.required_semantics:
            target_id = by_semantic.get(semantic)
            if target_id is None or target_id not in lod.included_target_ids:
                raise ValueError(f"LOD {lod.lod_id} does not preserve required semantic {semantic}")
