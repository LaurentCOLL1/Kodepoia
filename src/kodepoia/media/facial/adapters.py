from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, Sequence

from kodepoia.media.contracts import bounded_text, sha256_hex, stable_id
from kodepoia.media.serialization import canonical_sha256

from .contracts import FacialTarget, FacialTargetCatalog, FacialTargetKind
from .curves import FacialCurveSet


class R5FacialTrackKind(StrEnum):
    BLEND_SHAPE = "blend_shape"
    BONE_PROPERTY = "bone_property"


class R10FacialTargetAdapter:
    """Strict bridge from already-accepted R10 metadata into R11 target identities."""

    @staticmethod
    def from_metadata(document: Mapping[str, Any]) -> FacialTargetCatalog:
        if set(document) != {"catalog_id", "rig_digest", "targets"}:
            raise ValueError("R10 facial metadata shape is invalid")
        targets_raw = document["targets"]
        if not isinstance(targets_raw, Sequence) or isinstance(targets_raw, (str, bytes)) or not 1 <= len(targets_raw) <= 512:
            raise ValueError("R10 facial metadata targets must contain 1..512 items")
        targets: list[FacialTarget] = []
        for raw in targets_raw:
            if not isinstance(raw, Mapping) or set(raw) != {"target_id", "semantic", "kind", "minimum", "maximum", "source_digest"}:
                raise ValueError("R10 facial target metadata shape is invalid")
            try:
                kind = FacialTargetKind(str(raw["kind"]))
            except ValueError as exc:
                raise ValueError("unsupported R10 facial target kind") from exc
            targets.append(
                FacialTarget(
                    target_id=str(raw["target_id"]),
                    semantic=str(raw["semantic"]),
                    kind=kind,
                    minimum=raw["minimum"],
                    maximum=raw["maximum"],
                    source_digest=str(raw["source_digest"]),
                )
            )
        return FacialTargetCatalog(str(document["catalog_id"]), str(document["rig_digest"]), tuple(targets))


@dataclass(frozen=True, slots=True)
class GodotFacialAnimationIntent:
    intent_id: str
    curve_set_digest: str
    target_id: str
    target_kind: FacialTargetKind
    track_kind: R5FacialTrackKind
    key_count: int
    duration_seconds: float

    def __post_init__(self) -> None:
        stable_id(self.intent_id, field="intent_id")
        sha256_hex(self.curve_set_digest, field="curve_set_digest")
        stable_id(self.target_id, field="target_id")
        if not isinstance(self.target_kind, FacialTargetKind):
            raise TypeError("target_kind must be FacialTargetKind")
        if not isinstance(self.track_kind, R5FacialTrackKind):
            raise TypeError("track_kind must be R5FacialTrackKind")
        if isinstance(self.key_count, bool) or not isinstance(self.key_count, int) or self.key_count <= 0:
            raise ValueError("key_count must be positive integer")
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
        expected = R5FacialTrackKind.BLEND_SHAPE if self.target_kind is FacialTargetKind.BLEND_SHAPE else R5FacialTrackKind.BONE_PROPERTY
        if self.track_kind is not expected:
            raise ValueError("track kind does not match target kind")

    def canonical(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "curve_set_digest": self.curve_set_digest,
            "target_id": self.target_id,
            "target_kind": self.target_kind.value,
            "track_kind": self.track_kind.value,
            "key_count": self.key_count,
            "duration_seconds": float(self.duration_seconds),
        }

    def digest(self) -> str:
        return canonical_sha256({"schema": "kodepoia.r11.godot_facial_animation_intent", "version": 1, "payload": self.canonical()})


def build_godot_facial_intents(curves: FacialCurveSet, catalog: FacialTargetCatalog) -> tuple[GodotFacialAnimationIntent, ...]:
    if curves.target_catalog_digest != catalog.digest():
        raise ValueError("curve set target catalog digest mismatch")
    intents: list[GodotFacialAnimationIntent] = []
    for curve in curves.curves:
        target = catalog.target(curve.target_id)
        track_kind = R5FacialTrackKind.BLEND_SHAPE if target.kind is FacialTargetKind.BLEND_SHAPE else R5FacialTrackKind.BONE_PROPERTY
        intents.append(
            GodotFacialAnimationIntent(
                intent_id=f"facial.intent.{curve.target_id}",
                curve_set_digest=curves.digest(),
                target_id=curve.target_id,
                target_kind=target.kind,
                track_kind=track_kind,
                key_count=len(curve.keys),
                duration_seconds=curves.duration_seconds,
            )
        )
    return tuple(intents)
