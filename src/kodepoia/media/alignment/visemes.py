from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from kodepoia.media.contracts import bounded_text, sha256_hex, stable_id
from kodepoia.media.serialization import canonical_sha256

from .contracts import SpeechAlignmentTimeline


@dataclass(frozen=True, slots=True)
class PhonemeVisemeEntry:
    phoneme: str
    viseme: str

    def __post_init__(self) -> None:
        bounded_text(self.phoneme, field="phoneme", maximum=64)
        stable_id(self.viseme, field="viseme")

    def canonical(self) -> dict[str, str]:
        return {"phoneme": self.phoneme, "viseme": self.viseme}


@dataclass(frozen=True, slots=True)
class VisemeSet:
    set_id: str
    entries: tuple[PhonemeVisemeEntry, ...]
    fallback_viseme: str
    rest_viseme: str

    def __post_init__(self) -> None:
        stable_id(self.set_id, field="set_id")
        stable_id(self.fallback_viseme, field="fallback_viseme")
        stable_id(self.rest_viseme, field="rest_viseme")
        if not self.entries or len(self.entries) > 1024:
            raise ValueError("viseme set must contain 1..1024 entries")
        keys = [entry.phoneme.casefold() for entry in self.entries]
        if len(keys) != len(set(keys)):
            raise ValueError("viseme set contains duplicate phoneme mappings")

    def lookup(self, phoneme: str) -> tuple[str, bool]:
        key = phoneme.casefold()
        for entry in self.entries:
            if entry.phoneme.casefold() == key:
                return entry.viseme, False
        return self.fallback_viseme, True

    def canonical(self) -> dict[str, Any]:
        ordered = sorted(self.entries, key=lambda item: item.phoneme.casefold())
        return {
            "set_id": self.set_id,
            "entries": [entry.canonical() for entry in ordered],
            "fallback_viseme": self.fallback_viseme,
            "rest_viseme": self.rest_viseme,
        }

    def digest(self) -> str:
        return canonical_sha256({"schema": "kodepoia.r11.viseme_set", "version": 1, "payload": self.canonical()})


@dataclass(frozen=True, slots=True)
class VisemeEvent:
    source_phoneme: str
    viseme: str
    influence_start_seconds: float
    peak_start_seconds: float
    peak_end_seconds: float
    influence_end_seconds: float
    fallback_used: bool

    def __post_init__(self) -> None:
        bounded_text(self.source_phoneme, field="source_phoneme", maximum=64)
        stable_id(self.viseme, field="viseme")
        values = (
            self.influence_start_seconds,
            self.peak_start_seconds,
            self.peak_end_seconds,
            self.influence_end_seconds,
        )
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in values):
            raise ValueError("viseme event times must be finite numeric values")
        start, peak_start, peak_end, end = (float(value) for value in values)
        if start < 0 or not start <= peak_start < peak_end <= end:
            raise ValueError("viseme event timing order is invalid")

    def canonical(self) -> dict[str, Any]:
        return {
            "source_phoneme": self.source_phoneme,
            "viseme": self.viseme,
            "influence_start_seconds": float(self.influence_start_seconds),
            "peak_start_seconds": float(self.peak_start_seconds),
            "peak_end_seconds": float(self.peak_end_seconds),
            "influence_end_seconds": float(self.influence_end_seconds),
            "fallback_used": self.fallback_used,
        }


@dataclass(frozen=True, slots=True)
class VisemeTimeline:
    timeline_id: str
    audio_sha256: str
    alignment_digest: str
    viseme_set_id: str
    viseme_set_digest: str
    duration_seconds: float
    attack_seconds: float
    release_seconds: float
    events: tuple[VisemeEvent, ...]

    def __post_init__(self) -> None:
        stable_id(self.timeline_id, field="timeline_id")
        sha256_hex(self.audio_sha256, field="audio_sha256")
        sha256_hex(self.alignment_digest, field="alignment_digest")
        stable_id(self.viseme_set_id, field="viseme_set_id")
        sha256_hex(self.viseme_set_digest, field="viseme_set_digest")
        for name, value in (("duration_seconds", self.duration_seconds), ("attack_seconds", self.attack_seconds), ("release_seconds", self.release_seconds)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0:
                raise ValueError(f"{name} must be finite and non-negative")
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
        if self.attack_seconds > 0.25 or self.release_seconds > 0.25:
            raise ValueError("coarticulation windows exceed bounded policy")
        previous_peak = -1.0
        for event in self.events:
            if event.peak_start_seconds < previous_peak:
                raise ValueError("viseme peaks must be monotonic")
            if event.influence_end_seconds > self.duration_seconds + 1e-9:
                raise ValueError("viseme event exceeds audio duration")
            previous_peak = event.peak_start_seconds

    def canonical(self) -> dict[str, Any]:
        return {
            "timeline_id": self.timeline_id,
            "audio_sha256": self.audio_sha256,
            "alignment_digest": self.alignment_digest,
            "viseme_set_id": self.viseme_set_id,
            "viseme_set_digest": self.viseme_set_digest,
            "duration_seconds": float(self.duration_seconds),
            "attack_seconds": float(self.attack_seconds),
            "release_seconds": float(self.release_seconds),
            "events": [event.canonical() for event in self.events],
        }

    def digest(self) -> str:
        return canonical_sha256({"schema": "kodepoia.r11.viseme_timeline", "version": 1, "payload": self.canonical()})


def default_viseme_set() -> VisemeSet:
    groups = {
        "viseme.rest": ("<sil>", "sil", "sp", "pau"),
        "viseme.a": ("a", "aa", "ah", "ae"),
        "viseme.e": ("e", "eh", "ey"),
        "viseme.i": ("i", "ih", "iy", "y"),
        "viseme.o": ("o", "ao", "ow", "oy"),
        "viseme.u": ("u", "uh", "uw", "w"),
        "viseme.mbp": ("m", "b", "p"),
        "viseme.fv": ("f", "v"),
        "viseme.tdn": ("t", "d", "n", "th", "dh"),
        "viseme.kg": ("k", "g", "ng"),
        "viseme.sz": ("s", "z", "sh", "zh", "ch", "jh"),
        "viseme.rl": ("r", "l"),
    }
    entries = tuple(PhonemeVisemeEntry(phoneme, viseme) for viseme, phonemes in groups.items() for phoneme in phonemes)
    return VisemeSet("viseme.kdp.v1", entries, fallback_viseme="viseme.fallback", rest_viseme="viseme.rest")


def build_viseme_timeline(
    alignment: SpeechAlignmentTimeline,
    viseme_set: VisemeSet,
    *,
    timeline_id: str,
    attack_seconds: float = 0.025,
    release_seconds: float = 0.035,
) -> VisemeTimeline:
    if attack_seconds < 0 or release_seconds < 0 or attack_seconds > 0.25 or release_seconds > 0.25:
        raise ValueError("coarticulation windows are outside bounded policy")
    events: list[VisemeEvent] = []
    for phoneme in alignment.phonemes:
        viseme, fallback = viseme_set.lookup(phoneme.phoneme)
        events.append(
            VisemeEvent(
                source_phoneme=phoneme.phoneme,
                viseme=viseme,
                influence_start_seconds=max(0.0, float(phoneme.start_seconds) - attack_seconds),
                peak_start_seconds=float(phoneme.start_seconds),
                peak_end_seconds=float(phoneme.end_seconds),
                influence_end_seconds=min(alignment.duration_seconds, float(phoneme.end_seconds) + release_seconds),
                fallback_used=fallback,
            )
        )
    return VisemeTimeline(
        timeline_id=timeline_id,
        audio_sha256=alignment.audio_sha256,
        alignment_digest=alignment.digest(),
        viseme_set_id=viseme_set.set_id,
        viseme_set_digest=viseme_set.digest(),
        duration_seconds=alignment.duration_seconds,
        attack_seconds=attack_seconds,
        release_seconds=release_seconds,
        events=tuple(events),
    )
