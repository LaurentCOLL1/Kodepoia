from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import AudioCueDefinition


@dataclass(frozen=True, slots=True)
class GodotAudioPackagingIntent:
    cue_digest: str
    cue_id: str
    bus_id: str
    positional: bool
    attenuation_profile: str
    min_distance: float
    max_distance: float
    max_polyphony: int
    priority: int
    cooldown_seconds: float
    duck_bus_id: str | None
    loop: dict[str, Any]
    asset_revisions: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "cue_digest": self.cue_digest,
            "cue_id": self.cue_id,
            "bus_id": self.bus_id,
            "positional": self.positional,
            "attenuation_profile": self.attenuation_profile,
            "min_distance": self.min_distance,
            "max_distance": self.max_distance,
            "max_polyphony": self.max_polyphony,
            "priority": self.priority,
            "cooldown_seconds": self.cooldown_seconds,
            "duck_bus_id": self.duck_bus_id,
            "loop": dict(self.loop),
            "asset_revisions": list(self.asset_revisions),
        }


def compile_godot_audio_intent(cue: AudioCueDefinition) -> GodotAudioPackagingIntent:
    """Compile semantic R11 intent only; R5 remains authoritative for resource materialization."""
    return GodotAudioPackagingIntent(
        cue_digest=cue.digest,
        cue_id=cue.cue_id,
        bus_id=cue.bus_id,
        positional=cue.spatialization.positional,
        attenuation_profile=cue.spatialization.profile.value,
        min_distance=cue.spatialization.min_distance,
        max_distance=cue.spatialization.max_distance,
        max_polyphony=cue.max_polyphony,
        priority=cue.priority,
        cooldown_seconds=cue.cooldown_seconds,
        duck_bus_id=cue.duck_bus_id,
        loop=cue.loop.canonical(),
        asset_revisions=tuple(variant.asset_revision_id for variant in cue.variants),
    )
