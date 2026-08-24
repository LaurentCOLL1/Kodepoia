from __future__ import annotations

import io
import math
import struct
import wave
from dataclasses import dataclass


class AudioFormatError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class WavFacts:
    channels: int
    sample_rate_hz: int
    sample_width_bytes: int
    frame_count: int
    duration_seconds: float
    pcm_sha256_source_bytes: int
    peak: float | None
    clipped_samples: int | None
    silent_fraction: float | None
    first_sample: int | None
    last_sample: int | None

    def canonical(self) -> dict[str, object]:
        return {
            "channels": self.channels,
            "sample_rate_hz": self.sample_rate_hz,
            "sample_width_bytes": self.sample_width_bytes,
            "frame_count": self.frame_count,
            "duration_seconds": self.duration_seconds,
            "pcm_sha256_source_bytes": self.pcm_sha256_source_bytes,
            "peak": self.peak,
            "clipped_samples": self.clipped_samples,
            "silent_fraction": self.silent_fraction,
            "first_sample": self.first_sample,
            "last_sample": self.last_sample,
        }


def inspect_wav_bytes(data: bytes, *, max_bytes: int = 64 * 1024 * 1024, max_duration_seconds: float = 3600.0) -> WavFacts:
    if not isinstance(data, bytes):
        raise TypeError("WAV input must be bytes")
    if len(data) < 44 or len(data) > max_bytes:
        raise AudioFormatError("WAV byte size is outside accepted bounds")
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise AudioFormatError("WAV must be RIFF/WAVE")
    declared = struct.unpack_from("<I", data, 4)[0] + 8
    if declared > len(data) or declared < 44:
        raise AudioFormatError("WAV RIFF size is truncated or malformed")
    try:
        with wave.open(io.BytesIO(data), "rb") as handle:
            channels = handle.getnchannels()
            sample_rate = handle.getframerate()
            sample_width = handle.getsampwidth()
            frames = handle.getnframes()
            compression = handle.getcomptype()
            if compression != "NONE":
                raise AudioFormatError("R11.2 pure-Python WAV acceptance supports PCM only")
            if channels < 1 or channels > 8:
                raise AudioFormatError("WAV channel count is outside accepted bounds")
            if sample_rate < 8000 or sample_rate > 192000:
                raise AudioFormatError("WAV sample rate is outside accepted bounds")
            if sample_width not in {1, 2, 3, 4}:
                raise AudioFormatError("WAV sample width is unsupported")
            duration = frames / sample_rate
            if not math.isfinite(duration) or duration > max_duration_seconds:
                raise AudioFormatError("WAV duration exceeds accepted budget")
            pcm = handle.readframes(frames)
            expected = frames * channels * sample_width
            if len(pcm) != expected:
                raise AudioFormatError("WAV PCM payload is truncated")
    except (wave.Error, EOFError) as exc:
        raise AudioFormatError("WAV cannot be parsed") from exc

    peak: float | None = None
    clipped: int | None = None
    silent_fraction: float | None = None
    first_sample: int | None = None
    last_sample: int | None = None
    if sample_width == 2 and pcm:
        count = len(pcm) // 2
        samples = struct.unpack("<" + "h" * count, pcm)
        abs_values = [abs(value) for value in samples]
        peak = max(abs_values) / 32768.0
        clipped = sum(1 for value in abs_values if value >= 32767)
        silent_fraction = sum(1 for value in abs_values if value <= 32) / count
        first_sample = samples[0]
        last_sample = samples[-1]

    return WavFacts(channels, sample_rate, sample_width, frames, duration, len(pcm), peak, clipped, silent_fraction, first_sample, last_sample)
