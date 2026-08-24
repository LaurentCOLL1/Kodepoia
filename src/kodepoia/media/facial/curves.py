from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from kodepoia.media.contracts import sha256_hex, stable_id
from kodepoia.media.serialization import canonical_sha256
from kodepoia.media.alignment.visemes import VisemeTimeline

from .contracts import FacialPerformanceProfile, FacialTargetCatalog, validate_profile_against_catalog


@dataclass(frozen=True, slots=True)
class FacialCurveKey:
    time_seconds: float
    value: float

    def __post_init__(self) -> None:
        for field, value in (("time_seconds", self.time_seconds), ("value", self.value)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError(f"{field} must be finite numeric")
        if self.time_seconds < 0:
            raise ValueError("time_seconds must be non-negative")

    def canonical(self) -> dict[str, float]:
        return {"time_seconds": float(self.time_seconds), "value": float(self.value)}


@dataclass(frozen=True, slots=True)
class FacialTargetCurve:
    target_id: str
    keys: tuple[FacialCurveKey, ...]

    def __post_init__(self) -> None:
        stable_id(self.target_id, field="target_id")
        if not self.keys:
            raise ValueError("facial curve must contain at least one key")
        previous = -1.0
        for key in self.keys:
            if key.time_seconds < previous:
                raise ValueError("facial curve keys must be monotonic")
            previous = key.time_seconds

    def canonical(self) -> dict[str, Any]:
        return {"target_id": self.target_id, "keys": [key.canonical() for key in self.keys]}


@dataclass(frozen=True, slots=True)
class FacialCurveSet:
    curve_set_id: str
    profile_digest: str
    viseme_timeline_digest: str
    target_catalog_digest: str
    lod_id: str
    duration_seconds: float
    curves: tuple[FacialTargetCurve, ...]
    clipped_key_count: int

    def __post_init__(self) -> None:
        stable_id(self.curve_set_id, field="curve_set_id")
        sha256_hex(self.profile_digest, field="profile_digest")
        sha256_hex(self.viseme_timeline_digest, field="viseme_timeline_digest")
        sha256_hex(self.target_catalog_digest, field="target_catalog_digest")
        stable_id(self.lod_id, field="lod_id")
        if not math.isfinite(float(self.duration_seconds)) or self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be finite and positive")
        if isinstance(self.clipped_key_count, bool) or not isinstance(self.clipped_key_count, int) or self.clipped_key_count < 0:
            raise ValueError("clipped_key_count must be non-negative integer")
        ids = [curve.target_id for curve in self.curves]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate target curves")
        for curve in self.curves:
            if curve.keys[-1].time_seconds > self.duration_seconds + 1e-9:
                raise ValueError("curve exceeds duration")

    def canonical(self) -> dict[str, Any]:
        return {
            "curve_set_id": self.curve_set_id,
            "profile_digest": self.profile_digest,
            "viseme_timeline_digest": self.viseme_timeline_digest,
            "target_catalog_digest": self.target_catalog_digest,
            "lod_id": self.lod_id,
            "duration_seconds": float(self.duration_seconds),
            "clipped_key_count": self.clipped_key_count,
            "curves": [curve.canonical() for curve in sorted(self.curves, key=lambda item: item.target_id)],
        }

    def digest(self) -> str:
        return canonical_sha256({"schema": "kodepoia.r11.facial_curve_set", "version": 1, "payload": self.canonical()})


def _merge_key(points: dict[float, float], time_seconds: float, value: float) -> None:
    key = round(float(time_seconds), 9)
    current = points.get(key)
    points[key] = value if current is None else max(current, value)


def _decimate(keys: list[FacialCurveKey], *, duration: float, max_keys_per_second: int) -> list[FacialCurveKey]:
    max_keys = max(2, int(math.ceil(duration * max_keys_per_second)) + 1)
    if len(keys) <= max_keys:
        return keys
    keep = {0, len(keys) - 1}
    span = len(keys) - 1
    for slot in range(1, max_keys - 1):
        keep.add(round(slot * span / (max_keys - 1)))
    return [key for index, key in enumerate(keys) if index in keep]


def build_facial_curves(
    timeline: VisemeTimeline,
    profile: FacialPerformanceProfile,
    catalog: FacialTargetCatalog,
    *,
    curve_set_id: str,
    lod_id: str,
) -> FacialCurveSet:
    validate_profile_against_catalog(profile, catalog)
    if profile.viseme_set_digest != timeline.viseme_set_digest:
        raise ValueError("profile viseme set digest does not match timeline")
    lod = profile.lod(lod_id)
    included = set(lod.included_target_ids)
    points_by_target: dict[str, dict[float, float]] = {}
    clipped = 0
    for event in timeline.events:
        for mapping in profile.mappings_for(event.viseme):
            if mapping.target_id not in included:
                continue
            target = catalog.target(mapping.target_id)
            value = float(mapping.weight)
            if value < target.minimum or value > target.maximum:
                if not profile.clamp_out_of_range:
                    raise ValueError("curve weight exceeds R10 target range")
                value = min(target.maximum, max(target.minimum, value))
                clipped += 2
            points = points_by_target.setdefault(mapping.target_id, {})
            neutral = min(target.maximum, max(target.minimum, 0.0))
            _merge_key(points, event.influence_start_seconds, neutral)
            _merge_key(points, event.peak_start_seconds, value)
            _merge_key(points, event.peak_end_seconds, value)
            _merge_key(points, event.influence_end_seconds, neutral)
    curves: list[FacialTargetCurve] = []
    for target_id in sorted(points_by_target):
        raw_keys = [FacialCurveKey(time, value) for time, value in sorted(points_by_target[target_id].items())]
        keys = _decimate(raw_keys, duration=timeline.duration_seconds, max_keys_per_second=lod.max_keys_per_second)
        curves.append(FacialTargetCurve(target_id, tuple(keys)))
    return FacialCurveSet(
        curve_set_id=curve_set_id,
        profile_digest=profile.digest(),
        viseme_timeline_digest=timeline.digest(),
        target_catalog_digest=catalog.digest(),
        lod_id=lod_id,
        duration_seconds=timeline.duration_seconds,
        curves=tuple(curves),
        clipped_key_count=clipped,
    )
