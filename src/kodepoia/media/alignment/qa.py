from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from kodepoia.media.contracts import MediaState, stable_id
from kodepoia.media.serialization import canonical_sha256

from .contracts import SpeechAlignmentTimeline
from .visemes import VisemeTimeline


@dataclass(frozen=True, slots=True)
class LipSyncQAProfile:
    profile_id: str = "lipsync.default.v1"
    max_events: int = 8192
    max_events_per_second: float = 45.0
    max_influence_overlap_seconds: float = 0.125
    max_duration_drift_seconds: float = 0.050
    max_fallback_fraction: float = 0.20
    min_reported_confidence: float = 0.20

    def __post_init__(self) -> None:
        stable_id(self.profile_id, field="profile_id")
        if isinstance(self.max_events, bool) or not isinstance(self.max_events, int) or self.max_events < 1:
            raise ValueError("max_events must be positive")
        for name in ("max_events_per_second", "max_influence_overlap_seconds", "max_duration_drift_seconds", "max_fallback_fraction", "min_reported_confidence"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0:
                raise ValueError(f"{name} must be finite and non-negative")
        if self.max_fallback_fraction > 1 or self.min_reported_confidence > 1:
            raise ValueError("fraction/confidence bounds must be <= 1")


@dataclass(frozen=True, slots=True)
class LipSyncQAReport:
    profile_id: str
    alignment_digest: str
    viseme_timeline_digest: str
    state: MediaState
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, float | int]

    def canonical(self) -> dict[str, Any]:
        return {"profile_id": self.profile_id, "alignment_digest": self.alignment_digest, "viseme_timeline_digest": self.viseme_timeline_digest, "state": self.state.value, "blockers": list(self.blockers), "warnings": list(self.warnings), "metrics": dict(sorted(self.metrics.items()))}

    def digest(self) -> str:
        return canonical_sha256({"schema": "kodepoia.r11.lipsync_qa", "version": 1, "payload": self.canonical()})


def evaluate_lipsync(alignment: SpeechAlignmentTimeline, visemes: VisemeTimeline, *, accepted_audio_duration_seconds: float, profile: LipSyncQAProfile | None = None) -> LipSyncQAReport:
    p = profile or LipSyncQAProfile()
    if isinstance(accepted_audio_duration_seconds, bool) or not isinstance(accepted_audio_duration_seconds, (int, float)):
        raise TypeError("accepted_audio_duration_seconds must be numeric")
    accepted_duration = float(accepted_audio_duration_seconds)
    if not math.isfinite(accepted_duration) or accepted_duration <= 0:
        raise ValueError("accepted_audio_duration_seconds must be finite and positive")
    if visemes.alignment_digest != alignment.digest() or visemes.audio_sha256 != alignment.audio_sha256:
        raise ValueError("viseme timeline is not bound to supplied alignment/audio identity")

    blockers: list[str] = []
    warnings: list[str] = []
    event_count = len(visemes.events)
    density = event_count / accepted_duration
    duration_drift = abs(float(visemes.duration_seconds) - accepted_duration)
    fallback_count = sum(1 for event in visemes.events if event.fallback_used)
    fallback_fraction = fallback_count / event_count if event_count else 0.0
    overlaps = [max(0.0, left.influence_end_seconds - right.influence_start_seconds) for left, right in zip(visemes.events, visemes.events[1:])]
    max_overlap = max(overlaps, default=0.0)
    confidences = [float(item.confidence) for item in alignment.phonemes if item.confidence is not None]
    min_confidence = min(confidences, default=1.0)

    if event_count > p.max_events:
        blockers.append("event_budget")
    if density > p.max_events_per_second:
        blockers.append("density_budget")
    if max_overlap > p.max_influence_overlap_seconds + 1e-9:
        blockers.append("coarticulation_overlap")
    if duration_drift > p.max_duration_drift_seconds + 1e-9:
        blockers.append("duration_drift")
    if fallback_fraction > p.max_fallback_fraction + 1e-12:
        blockers.append("phoneme_fallback_ratio")
    elif fallback_count:
        warnings.append("phoneme_fallback_used")
    if confidences and min_confidence < p.min_reported_confidence:
        warnings.append("low_alignment_confidence")
    if not alignment.phonemes:
        blockers.append("phonemes_missing")

    state = MediaState.BUDGET_EXCEEDED if any(code.endswith("budget") for code in blockers) else (MediaState.BLOCKED if blockers else (MediaState.WARN if warnings else MediaState.PASS))
    metrics: dict[str, float | int] = {"event_count": event_count, "events_per_second": density, "duration_drift_seconds": duration_drift, "max_influence_overlap_seconds": max_overlap, "fallback_count": fallback_count, "fallback_fraction": fallback_fraction, "min_reported_confidence": min_confidence}
    return LipSyncQAReport(p.profile_id, alignment.digest(), visemes.digest(), state, tuple(sorted(set(blockers))), tuple(sorted(set(warnings))), metrics)
