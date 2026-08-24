from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .profiles import normalize_voice_text


class SpeechSegmentKind(StrEnum):
    TEXT = "text"
    PAUSE = "pause"
    EMPHASIS = "emphasis"


@dataclass(frozen=True, slots=True)
class SpeechSegment:
    kind: SpeechSegmentKind
    text: str | None = None
    pause_seconds: float | None = None
    emphasis: str | None = None

    def __post_init__(self) -> None:
        if self.kind is SpeechSegmentKind.TEXT:
            if self.text is None or self.pause_seconds is not None or self.emphasis is not None:
                raise ValueError("text segment requires only text")
            object.__setattr__(self, "text", normalize_voice_text(self.text, maximum=4096))
            return
        if self.kind is SpeechSegmentKind.PAUSE:
            if self.text is not None or self.emphasis is not None or self.pause_seconds is None:
                raise ValueError("pause segment requires only pause_seconds")
            value = self.pause_seconds
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or not 0.0 <= float(value) <= 5.0:
                raise ValueError("pause_seconds must be finite and between 0 and 5")
            return
        if self.kind is SpeechSegmentKind.EMPHASIS:
            if self.text is None or self.pause_seconds is not None or self.emphasis not in {"reduced", "moderate", "strong"}:
                raise ValueError("emphasis segment requires text and an allowlisted emphasis")
            object.__setattr__(self, "text", normalize_voice_text(self.text, maximum=4096))
            return
        raise ValueError("unsupported speech segment kind")

    def canonical(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "text": self.text,
            "pause_seconds": None if self.pause_seconds is None else float(self.pause_seconds),
            "emphasis": self.emphasis,
        }
