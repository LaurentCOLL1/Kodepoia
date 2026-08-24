from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.media import AudioQAReport, AudioSourceIdentity, MediaBoundaryError, MediaProcessLimits, MediaRuntimeBoundary, MediaState, RootReference, VoiceModelIdentity, canonical_sha256, make_envelope, parse_envelope, validate_environment_overrides

SHA = "a" * 64


def test_contracts_canonical_and_digest_stable() -> None:
    source = AudioSourceIdentity("asset:r8:voice", SHA, 44, "wav", "pcm_s16le", 48000, 1, 1.25)
    report = AudioQAReport("dialogue.v1", SHA, MediaState.PASS)
    payload = {"source": source.canonical(), "qa": report.canonical()}
    assert canonical_sha256(payload) == canonical_sha256(json.loads(json.dumps(payload)))
    envelope = make_envelope(schema="kodepoia.r11.media_root", version=1, payload=payload)
    assert parse_envelope(envelope, expected_schema="kodepoia.r11.media_root") == payload


def test_nonfinite_and_bad_hash_rejected() -> None:
    with pytest.raises(ValueError):
        AudioSourceIdentity("asset:r8:x", SHA, 1, "wav", "pcm", 48000, 1, float("nan"))
    with pytest.raises(ValueError):
        VoiceModelIdentity("bad", SHA, "fr_FR", "prov:1", "license:ok")


def test_voice_model_rights_state_explicit() -> None:
    model = VoiceModelIdentity(SHA, "b" * 64, "fr_FR", "prov:synthetic", "license:cc0", MediaState.RIGHTS_BLOCKED)
    assert model.canonical()["state"] == "RIGHTS_BLOCKED"
    assert model.canonical()["locale"] == "fr-FR"


def test_root_reference_never_uses_display_filename_identity() -> None:
    ref = RootReference("voice_profile", "character:alex", SHA)
    assert ref.canonical()["identity"] == "character:alex"


def test_limits_reject_invalid_values() -> None:
    with pytest.raises(ValueError):
        MediaProcessLimits(wall_time_seconds=0)
    with pytest.raises(ValueError):
        MediaProcessLimits(max_result_bytes=True)


def test_boundary_builds_fixed_ffprobe_argv(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    input_dir = tmp_path / "inputs"
    stage = tmp_path / "stage"
    bin_dir.mkdir(); input_dir.mkdir(); stage.mkdir()
    exe = bin_dir / ("ffprobe.exe" if __import__("os").name == "nt" else "ffprobe")
    exe.write_bytes(b"x")
    src = input_dir / "voice.wav"
    src.write_bytes(b"RIFF")
    boundary = MediaRuntimeBoundary(allowed_roots=(bin_dir,), staging_root=stage)
    argv = boundary.build_ffprobe_argv(exe, src, input_root=input_dir)
    assert argv[1:] == ("-v", "error", "-show_format", "-show_streams", "-of", "json", "--", str(src.resolve()))


def test_boundary_rejects_escape_and_raw_environment(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"; bin_dir.mkdir()
    stage = tmp_path / "stage"; stage.mkdir()
    boundary = MediaRuntimeBoundary(allowed_roots=(bin_dir,), staging_root=stage)
    outside = tmp_path / "outside.wav"; outside.write_bytes(b"x")
    with pytest.raises(MediaBoundaryError):
        boundary.validate_input(outside, root=stage, suffixes=frozenset({".wav"}))
    with pytest.raises(MediaBoundaryError):
        validate_environment_overrides({"PYTHONPATH": "evil"})
    assert validate_environment_overrides({"KODEPOIA_RUN_ID": "r11"}) == {"KODEPOIA_RUN_ID": "r11"}


def test_no_generic_process_escape_surface() -> None:
    names = set(dir(MediaRuntimeBoundary))
    assert "run_shell" not in names
    assert "run_ffmpeg" not in names
    assert "run_tts" not in names
    assert "run_godot_script" not in names
