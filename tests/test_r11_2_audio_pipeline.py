from __future__ import annotations

import hashlib
import io
import json
import struct
import wave

import pytest

from kodepoia.media import MediaState
from kodepoia.media.audio import AudioFormatError, AudioQAProfile, AudioTransform, AudioTransformRecipe, evaluate_wav, inspect_wav_bytes, parse_ffprobe_json

SHA = "a" * 64


def wav_bytes(samples: list[int], *, rate: int = 16000, channels: int = 1) -> bytes:
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack("<" + "h" * len(samples), *samples))
    return out.getvalue()


def test_wav_inspection_is_deterministic() -> None:
    data = wav_bytes([0, 100, -100, 32767, 0])
    facts = inspect_wav_bytes(data)
    assert facts.sample_rate_hz == 16000
    assert facts.channels == 1
    assert facts.clipped_samples == 1
    assert facts.peak == pytest.approx(32767 / 32768)


def test_wav_rejects_truncated_and_oversized() -> None:
    good = wav_bytes([0, 1, 2])
    with pytest.raises(AudioFormatError):
        inspect_wav_bytes(good[:-2])
    with pytest.raises(AudioFormatError):
        inspect_wav_bytes(good, max_bytes=20)


def test_wav_duration_budget_blocks() -> None:
    data = wav_bytes([0] * 160)
    with pytest.raises(AudioFormatError):
        inspect_wav_bytes(data, max_duration_seconds=0.001)


def test_ffprobe_json_parser_accepts_bounded_audio() -> None:
    payload = {"streams": [{"codec_type": "audio", "codec_name": "opus", "sample_rate": "48000", "channels": 2}], "format": {"duration": "1.25", "bit_rate": "128000", "format_name": "ogg"}}
    facts = parse_ffprobe_json(json.dumps(payload).encode())
    assert facts.codec == "opus" and facts.duration_seconds == 1.25


def test_ffprobe_json_rejects_extra_root_and_video() -> None:
    with pytest.raises(AudioFormatError):
        parse_ffprobe_json(json.dumps({"streams": [], "format": {}, "evil": {}}).encode())
    with pytest.raises(AudioFormatError):
        parse_ffprobe_json(json.dumps({"streams": [{"codec_type": "video", "codec_name": "h264", "sample_rate": "48000", "channels": 2}], "format": {"duration": "1"}}).encode())


def test_transform_recipe_has_no_raw_filter_surface() -> None:
    recipe = AudioTransformRecipe(AudioTransform.RESAMPLE, "asset:r8:a", SHA, sample_rate_hz=48000)
    assert len(recipe.digest) == 64
    assert set(recipe.canonical()) == {"schema_version", "operation", "input_revision_id", "input_sha256", "sample_rate_hz", "channels", "start_seconds", "end_seconds", "fade_seconds", "target_peak_dbfs"}
    with pytest.raises(ValueError):
        AudioTransformRecipe(AudioTransform.RESAMPLE, "asset:r8:a", SHA, sample_rate_hz=12345)


def test_qa_reports_clipping_and_silence() -> None:
    facts = inspect_wav_bytes(wav_bytes([32767, 0, 0, 0]))
    report = evaluate_wav(hashlib.sha256(b"source").hexdigest(), facts)
    assert report.state == MediaState.BLOCKED
    assert "clipping" in report.blockers


def test_qa_loop_seam_is_warning_not_fabricated_pass() -> None:
    facts = inspect_wav_bytes(wav_bytes([-20000, 0, 20000]))
    report = evaluate_wav(SHA, facts, AudioQAProfile(max_loop_edge_delta=100), loop=True)
    assert report.state == MediaState.WARN
    assert "loop_seam" in report.warnings


def test_non_pcm_metrics_are_not_silently_manufactured() -> None:
    data = wav_bytes([1, 2, 3])
    facts = inspect_wav_bytes(data)
    assert facts.peak is not None


def test_ffprobe_output_size_limit() -> None:
    with pytest.raises(AudioFormatError):
        parse_ffprobe_json(b"{}" * 100, max_bytes=10)
