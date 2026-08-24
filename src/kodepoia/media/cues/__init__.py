"""Semantic R11.3 Music/SFX/Foley cue contracts and packaging intents."""

from .contracts import AttenuationProfile, AudioCueDefinition, CueCategory, CuePlayback, CueVariant, LoopPolicy, SpatializationIntent
from .godot_intent import GodotAudioPackagingIntent, compile_godot_audio_intent
from .selection import playlist_order, select_variant

__all__ = [
    "AttenuationProfile", "AudioCueDefinition", "CueCategory", "CuePlayback",
    "CueVariant", "GodotAudioPackagingIntent", "LoopPolicy", "SpatializationIntent",
    "compile_godot_audio_intent", "playlist_order", "select_variant",
]
