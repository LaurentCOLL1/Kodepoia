from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

from .wav import AudioFormatError


@dataclass(frozen=True, slots=True)
class ProbeFacts:
    codec: str
    sample_rate_hz: int
    channels: int
    duration_seconds: float
    bit_rate: int | None
    container: str | None

    def canonical(self) -> dict[str, object]:
        return {"codec": self.codec, "sample_rate_hz": self.sample_rate_hz, "channels": self.channels, "duration_seconds": self.duration_seconds, "bit_rate": self.bit_rate, "container": self.container}


def parse_ffprobe_json(data: bytes, *, max_bytes: int = 1024 * 1024) -> ProbeFacts:
    if not isinstance(data, bytes) or len(data) > max_bytes:
        raise AudioFormatError("ffprobe output exceeds accepted bounds")
    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AudioFormatError("ffprobe output must be valid UTF-8 JSON") from exc
    if not isinstance(document, dict) or set(document) - {"streams", "format"}:
        raise AudioFormatError("ffprobe root contains unexpected fields")
    streams = document.get("streams")
    if not isinstance(streams, list) or len(streams) != 1 or not isinstance(streams[0], dict):
        raise AudioFormatError("ffprobe must describe exactly one expected audio stream")
    stream: dict[str, Any] = streams[0]
    if stream.get("codec_type") not in {None, "audio"}:
        raise AudioFormatError("ffprobe stream is not audio")
    codec = stream.get("codec_name")
    if not isinstance(codec, str) or not codec or len(codec) > 64:
        raise AudioFormatError("ffprobe codec is invalid")
    try:
        rate = int(stream["sample_rate"])
        channels = int(stream["channels"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AudioFormatError("ffprobe sample facts are invalid") from exc
    if not 8000 <= rate <= 384000 or not 1 <= channels <= 32:
        raise AudioFormatError("ffprobe sample facts exceed accepted bounds")
    fmt = document.get("format", {})
    if not isinstance(fmt, dict):
        raise AudioFormatError("ffprobe format must be an object")
    raw_duration = stream.get("duration", fmt.get("duration"))
    try:
        duration = float(raw_duration)
    except (TypeError, ValueError) as exc:
        raise AudioFormatError("ffprobe duration is invalid") from exc
    if not math.isfinite(duration) or duration < 0 or duration > 24 * 3600:
        raise AudioFormatError("ffprobe duration is outside accepted bounds")
    raw_rate = stream.get("bit_rate", fmt.get("bit_rate"))
    bit_rate = None
    if raw_rate not in {None, "N/A"}:
        try:
            bit_rate = int(raw_rate)
        except (TypeError, ValueError) as exc:
            raise AudioFormatError("ffprobe bit rate is invalid") from exc
        if bit_rate < 0 or bit_rate > 100_000_000:
            raise AudioFormatError("ffprobe bit rate exceeds accepted bounds")
    container = fmt.get("format_name")
    if container is not None and (not isinstance(container, str) or len(container) > 128):
        raise AudioFormatError("ffprobe container is invalid")
    return ProbeFacts(codec, rate, channels, duration, bit_rate, container)
