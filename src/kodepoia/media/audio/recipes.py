from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from kodepoia.media.serialization import canonical_sha256


class AudioTransform(StrEnum):
    RESAMPLE = "resample"
    CHANNELS = "channels"
    TRIM = "trim"
    FADE = "fade"
    NORMALIZE = "normalize"
    TRANSCODE_PCM = "transcode_pcm"


@dataclass(frozen=True, slots=True)
class AudioTransformRecipe:
    operation: AudioTransform
    input_revision_id: str
    input_sha256: str
    sample_rate_hz: int | None = None
    channels: int | None = None
    start_seconds: float | None = None
    end_seconds: float | None = None
    fade_seconds: float | None = None
    target_peak_dbfs: float | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("R11.2 supports recipe schema 1 only")
        if not self.input_revision_id or len(self.input_revision_id) > 256 or any(ord(ch) < 32 for ch in self.input_revision_id):
            raise ValueError("input_revision_id is invalid")
        if len(self.input_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in self.input_sha256):
            raise ValueError("input_sha256 is invalid")
        if self.sample_rate_hz is not None and self.sample_rate_hz not in {16000, 22050, 24000, 44100, 48000}:
            raise ValueError("sample_rate_hz is not allowlisted")
        if self.channels is not None and self.channels not in {1, 2}:
            raise ValueError("channels must be 1 or 2")
        for name in ("start_seconds", "end_seconds", "fade_seconds", "target_peak_dbfs"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value))):
                raise ValueError(f"{name} must be finite")
        if self.start_seconds is not None and self.start_seconds < 0:
            raise ValueError("start_seconds must be non-negative")
        if self.end_seconds is not None and (self.end_seconds <= 0 or (self.start_seconds is not None and self.end_seconds <= self.start_seconds)):
            raise ValueError("end_seconds must exceed start_seconds")
        if self.fade_seconds is not None and not 0 <= self.fade_seconds <= 30:
            raise ValueError("fade_seconds is outside accepted bounds")
        if self.target_peak_dbfs is not None and not -30 <= self.target_peak_dbfs <= 0:
            raise ValueError("target_peak_dbfs is outside accepted bounds")

    def canonical(self) -> dict[str, Any]:
        return {"schema_version": 1, "operation": self.operation.value, "input_revision_id": self.input_revision_id, "input_sha256": self.input_sha256, "sample_rate_hz": self.sample_rate_hz, "channels": self.channels, "start_seconds": self.start_seconds, "end_seconds": self.end_seconds, "fade_seconds": self.fade_seconds, "target_peak_dbfs": self.target_peak_dbfs}

    @property
    def digest(self) -> str:
        return canonical_sha256(self.canonical())
