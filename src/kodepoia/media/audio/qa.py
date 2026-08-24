from __future__ import annotations

from dataclasses import dataclass

from kodepoia.media.contracts import AudioQAReport, MediaState

from .wav import WavFacts


@dataclass(frozen=True, slots=True)
class AudioQAProfile:
    profile_id: str = "audio.default.v1"
    max_duration_seconds: float = 600.0
    max_channels: int = 2
    allowed_sample_rates: tuple[int, ...] = (16000, 22050, 24000, 44100, 48000)
    max_clipped_samples: int = 0
    max_silent_fraction: float = 0.98
    max_loop_edge_delta: int = 8192

    def __post_init__(self) -> None:
        if self.max_duration_seconds <= 0 or self.max_channels <= 0 or self.max_clipped_samples < 0:
            raise ValueError("invalid audio QA budget")
        if not 0 <= self.max_silent_fraction <= 1:
            raise ValueError("max_silent_fraction must be in [0,1]")
        if self.max_loop_edge_delta < 0:
            raise ValueError("max_loop_edge_delta must be non-negative")


def evaluate_wav(source_sha256: str, facts: WavFacts, profile: AudioQAProfile | None = None, *, loop: bool = False) -> AudioQAReport:
    p = profile or AudioQAProfile()
    blockers: list[str] = []
    warnings: list[str] = []
    if facts.duration_seconds > p.max_duration_seconds:
        blockers.append("duration_budget")
    if facts.channels > p.max_channels:
        blockers.append("channel_budget")
    if facts.sample_rate_hz not in p.allowed_sample_rates:
        blockers.append("sample_rate_policy")
    if facts.clipped_samples is None:
        warnings.append("pcm_metrics_unavailable")
    elif facts.clipped_samples > p.max_clipped_samples:
        blockers.append("clipping")
    if facts.silent_fraction is not None and facts.silent_fraction > p.max_silent_fraction:
        warnings.append("mostly_silent")
    if loop and facts.first_sample is not None and facts.last_sample is not None and abs(facts.first_sample - facts.last_sample) > p.max_loop_edge_delta:
        warnings.append("loop_seam")
    state = MediaState.BUDGET_EXCEEDED if any(code.endswith("budget") for code in blockers) else (MediaState.BLOCKED if blockers else (MediaState.WARN if warnings else MediaState.PASS))
    return AudioQAReport(p.profile_id, source_sha256, state, tuple(blockers), tuple(warnings))
