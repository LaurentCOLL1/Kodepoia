from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from kodepoia.media.contracts import bounded_text, sha256_hex, stable_id
from kodepoia.media.serialization import canonical_sha256


class AlignmentSource(StrEnum):
    BACKEND = "backend"
    SYNTHETIC = "synthetic"
    IMPORTED = "imported"


def _time(value: float, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{field} must be finite and non-negative")
    return result


def _confidence(value: float | None) -> float | None:
    if value is None:
        return None
    result = _time(value, field="confidence")
    if result > 1:
        raise ValueError("confidence must be in [0,1]")
    return result


@dataclass(frozen=True, slots=True)
class TimedWord:
    text: str
    start_seconds: float
    end_seconds: float
    confidence: float | None = None

    def __post_init__(self) -> None:
        bounded_text(self.text, field="word.text", maximum=256)
        start = _time(self.start_seconds, field="word.start_seconds")
        end = _time(self.end_seconds, field="word.end_seconds")
        if end <= start:
            raise ValueError("word timing must have positive duration")
        _confidence(self.confidence)

    def canonical(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "start_seconds": float(self.start_seconds),
            "end_seconds": float(self.end_seconds),
            "confidence": self.confidence,
        }


@dataclass(frozen=True, slots=True)
class TimedPhoneme:
    phoneme: str
    start_seconds: float
    end_seconds: float
    confidence: float | None = None
    word_index: int | None = None

    def __post_init__(self) -> None:
        bounded_text(self.phoneme, field="phoneme", maximum=64)
        start = _time(self.start_seconds, field="phoneme.start_seconds")
        end = _time(self.end_seconds, field="phoneme.end_seconds")
        if end <= start:
            raise ValueError("phoneme timing must have positive duration")
        _confidence(self.confidence)
        if self.word_index is not None and (
            isinstance(self.word_index, bool) or not isinstance(self.word_index, int) or self.word_index < 0
        ):
            raise ValueError("word_index must be a non-negative integer")

    def canonical(self) -> dict[str, Any]:
        return {
            "phoneme": self.phoneme,
            "start_seconds": float(self.start_seconds),
            "end_seconds": float(self.end_seconds),
            "confidence": self.confidence,
            "word_index": self.word_index,
        }


def _validate_monotonic(items: tuple[TimedWord | TimedPhoneme, ...], *, duration_seconds: float, label: str) -> None:
    previous_start = -1.0
    previous_end = -1.0
    for item in items:
        start = float(item.start_seconds)
        end = float(item.end_seconds)
        if start < previous_start or end < previous_end:
            raise ValueError(f"{label} timings must be monotonic")
        if end > duration_seconds + 1e-9:
            raise ValueError(f"{label} timing exceeds accepted audio duration")
        previous_start = start
        previous_end = end


@dataclass(frozen=True, slots=True)
class SpeechAlignmentTimeline:
    timeline_id: str
    audio_sha256: str
    locale: str
    duration_seconds: float
    source: AlignmentSource
    source_id: str
    words: tuple[TimedWord, ...] = ()
    phonemes: tuple[TimedPhoneme, ...] = ()

    def __post_init__(self) -> None:
        stable_id(self.timeline_id, field="timeline_id")
        sha256_hex(self.audio_sha256, field="audio_sha256")
        bounded_text(self.locale, field="locale", maximum=64)
        duration = _time(self.duration_seconds, field="duration_seconds")
        if duration <= 0:
            raise ValueError("duration_seconds must be positive")
        if not isinstance(self.source, AlignmentSource):
            raise TypeError("source must be AlignmentSource")
        stable_id(self.source_id, field="source_id")
        _validate_monotonic(self.words, duration_seconds=duration, label="word")
        _validate_monotonic(self.phonemes, duration_seconds=duration, label="phoneme")
        for phoneme in self.phonemes:
            if phoneme.word_index is not None and phoneme.word_index >= len(self.words):
                raise ValueError("phoneme word_index is out of range")

    def canonical(self) -> dict[str, Any]:
        return {
            "timeline_id": self.timeline_id,
            "audio_sha256": self.audio_sha256,
            "locale": self.locale,
            "duration_seconds": float(self.duration_seconds),
            "source": self.source.value,
            "source_id": self.source_id,
            "words": [item.canonical() for item in self.words],
            "phonemes": [item.canonical() for item in self.phonemes],
        }

    def digest(self) -> str:
        return canonical_sha256({"schema": "kodepoia.r11.speech_alignment", "version": 1, "payload": self.canonical()})
