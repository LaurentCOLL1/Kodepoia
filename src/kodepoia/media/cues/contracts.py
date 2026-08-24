from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from kodepoia.media.contracts import MediaState, sha256_hex, stable_id
from kodepoia.media.serialization import canonical_sha256


class CueCategory(StrEnum):
    MUSIC = "music"
    AMBIENCE = "ambience"
    SFX = "sfx"
    FOLEY = "foley"
    UI = "ui"
    DIALOGUE_SUPPORT = "dialogue_support"


class CuePlayback(StrEnum):
    ONE_SHOT = "one_shot"
    LOOP = "loop"
    PLAYLIST = "playlist"
    WEIGHTED = "weighted"


class AttenuationProfile(StrEnum):
    NONE = "none"
    LINEAR = "linear"
    INVERSE = "inverse"


@dataclass(frozen=True, slots=True)
class CueVariant:
    asset_revision_id: str
    asset_sha256: str
    weight: int = 1
    qa_state: MediaState = MediaState.PASS
    rights_state: MediaState = MediaState.AVAILABLE

    def __post_init__(self) -> None:
        stable_id(self.asset_revision_id, field="asset_revision_id")
        sha256_hex(self.asset_sha256, field="asset_sha256")
        if isinstance(self.weight, bool) or not isinstance(self.weight, int) or not 1 <= self.weight <= 10000:
            raise ValueError("weight must be between 1 and 10000")
        if self.qa_state not in {MediaState.PASS, MediaState.WARN}:
            raise ValueError("variant QA state is not promotable")
        if self.rights_state != MediaState.AVAILABLE:
            raise ValueError("variant rights state is not promotable")

    def canonical(self) -> dict[str, Any]:
        return {"asset_revision_id": self.asset_revision_id, "asset_sha256": self.asset_sha256, "weight": self.weight, "qa_state": self.qa_state.value, "rights_state": self.rights_state.value}


@dataclass(frozen=True, slots=True)
class LoopPolicy:
    enabled: bool = False
    start_seconds: float | None = None
    end_seconds: float | None = None
    pre_roll_seconds: float = 0.0
    tail_seconds: float = 0.0
    crossfade_seconds: float = 0.0

    def __post_init__(self) -> None:
        for name in ("pre_roll_seconds", "tail_seconds", "crossfade_seconds"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0 or value > 30:
                raise ValueError(f"{name} is outside accepted bounds")
        for name in ("start_seconds", "end_seconds"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0):
                raise ValueError(f"{name} is invalid")
        if self.enabled:
            if self.start_seconds is None or self.end_seconds is None or self.end_seconds <= self.start_seconds:
                raise ValueError("enabled loop requires an ordered loop region")
            if self.crossfade_seconds * 2 > self.end_seconds - self.start_seconds:
                raise ValueError("loop crossfade exceeds half the loop region")
        elif any(value not in {None, 0, 0.0} for value in (self.start_seconds, self.end_seconds, self.crossfade_seconds)):
            raise ValueError("disabled loop cannot carry active loop fields")

    def canonical(self) -> dict[str, Any]:
        return {"enabled": self.enabled, "start_seconds": self.start_seconds, "end_seconds": self.end_seconds, "pre_roll_seconds": self.pre_roll_seconds, "tail_seconds": self.tail_seconds, "crossfade_seconds": self.crossfade_seconds}


@dataclass(frozen=True, slots=True)
class SpatializationIntent:
    positional: bool = False
    profile: AttenuationProfile = AttenuationProfile.NONE
    min_distance: float = 1.0
    max_distance: float = 50.0

    def __post_init__(self) -> None:
        for name in ("min_distance", "max_distance"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if self.max_distance < self.min_distance or self.max_distance > 100000:
            raise ValueError("spatial distance range is invalid")
        if not self.positional and self.profile != AttenuationProfile.NONE:
            raise ValueError("non-positional cue cannot request attenuation")

    def canonical(self) -> dict[str, Any]:
        return {"positional": self.positional, "profile": self.profile.value, "min_distance": self.min_distance, "max_distance": self.max_distance}


@dataclass(frozen=True, slots=True)
class AudioCueDefinition:
    cue_id: str
    category: CueCategory
    playback: CuePlayback
    variants: tuple[CueVariant, ...]
    bus_id: str
    priority: int = 50
    max_polyphony: int = 1
    cooldown_seconds: float = 0.0
    duck_bus_id: str | None = None
    loop: LoopPolicy = LoopPolicy()
    spatialization: SpatializationIntent = SpatializationIntent()
    allow_runtime_nondeterminism: bool = False
    schema_version: int = 1

    def __post_init__(self) -> None:
        stable_id(self.cue_id, field="cue_id")
        stable_id(self.bus_id, field="bus_id")
        if self.duck_bus_id is not None:
            stable_id(self.duck_bus_id, field="duck_bus_id")
            if self.duck_bus_id == self.bus_id:
                raise ValueError("cue cannot duck its own bus")
        if self.schema_version != 1:
            raise ValueError("R11.3 supports schema version 1 only")
        if not self.variants or len(self.variants) > 64:
            raise ValueError("cue must contain between 1 and 64 variants")
        identities = [(v.asset_revision_id, v.asset_sha256) for v in self.variants]
        if len(set(identities)) != len(identities):
            raise ValueError("cue contains duplicate asset variants")
        if isinstance(self.priority, bool) or not isinstance(self.priority, int) or not 0 <= self.priority <= 100:
            raise ValueError("priority must be in [0,100]")
        if isinstance(self.max_polyphony, bool) or not isinstance(self.max_polyphony, int) or not 1 <= self.max_polyphony <= 128:
            raise ValueError("max_polyphony must be in [1,128]")
        if isinstance(self.cooldown_seconds, bool) or not isinstance(self.cooldown_seconds, (int, float)) or not math.isfinite(float(self.cooldown_seconds)) or not 0 <= self.cooldown_seconds <= 3600:
            raise ValueError("cooldown_seconds is outside accepted bounds")
        if self.playback == CuePlayback.LOOP and not self.loop.enabled:
            raise ValueError("loop playback requires enabled loop policy")
        if self.playback != CuePlayback.LOOP and self.loop.enabled:
            raise ValueError("only loop playback may enable loop policy")

    def canonical(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "cue_id": self.cue_id,
            "category": self.category.value,
            "playback": self.playback.value,
            "variants": [variant.canonical() for variant in self.variants],
            "bus_id": self.bus_id,
            "priority": self.priority,
            "max_polyphony": self.max_polyphony,
            "cooldown_seconds": self.cooldown_seconds,
            "duck_bus_id": self.duck_bus_id,
            "loop": self.loop.canonical(),
            "spatialization": self.spatialization.canonical(),
            "allow_runtime_nondeterminism": self.allow_runtime_nondeterminism,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.canonical())
