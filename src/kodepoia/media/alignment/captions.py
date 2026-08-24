from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from kodepoia.media.contracts import bounded_text, sha256_hex, stable_id
from kodepoia.media.serialization import canonical_sha256

from .contracts import SpeechAlignmentTimeline


@dataclass(frozen=True, slots=True)
class CaptionCue:
    text: str
    start_seconds: float
    end_seconds: float

    def __post_init__(self) -> None:
        bounded_text(self.text, field="caption.text", maximum=1024)
        values = (self.start_seconds, self.end_seconds)
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in values):
            raise ValueError("caption cue times must be finite numeric values")
        if self.start_seconds < 0 or self.end_seconds <= self.start_seconds:
            raise ValueError("caption cue timing is invalid")

    def canonical(self) -> dict[str, Any]:
        return {"text": self.text, "start_seconds": float(self.start_seconds), "end_seconds": float(self.end_seconds)}


@dataclass(frozen=True, slots=True)
class CaptionTimingBridge:
    bridge_id: str
    alignment_digest: str
    audio_sha256: str
    locale: str
    cues: tuple[CaptionCue, ...]
    phoneme_authority: bool = False

    def __post_init__(self) -> None:
        stable_id(self.bridge_id, field="bridge_id")
        sha256_hex(self.alignment_digest, field="alignment_digest")
        sha256_hex(self.audio_sha256, field="audio_sha256")
        bounded_text(self.locale, field="locale", maximum=64)
        if self.phoneme_authority:
            raise ValueError("captions must never be phoneme authority")
        previous = -1.0
        for cue in self.cues:
            if cue.start_seconds < previous:
                raise ValueError("caption cues must be monotonic")
            previous = cue.start_seconds

    def canonical(self) -> dict[str, Any]:
        return {"bridge_id": self.bridge_id, "alignment_digest": self.alignment_digest, "audio_sha256": self.audio_sha256, "locale": self.locale, "phoneme_authority": False, "cues": [cue.canonical() for cue in self.cues]}

    def digest(self) -> str:
        return canonical_sha256({"schema": "kodepoia.r11.caption_timing_bridge", "version": 1, "payload": self.canonical()})


def captions_from_alignment(alignment: SpeechAlignmentTimeline, *, bridge_id: str) -> CaptionTimingBridge:
    cues = tuple(CaptionCue(word.text, word.start_seconds, word.end_seconds) for word in alignment.words)
    return CaptionTimingBridge(bridge_id, alignment.digest(), alignment.audio_sha256, alignment.locale, cues)
