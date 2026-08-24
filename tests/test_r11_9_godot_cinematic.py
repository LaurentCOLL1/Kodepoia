from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.core.sandbox import SandboxResult
from kodepoia.kodegodot.runtime import GodotRuntime
from kodepoia.media.cinematic.contracts import (
    CinematicRef,
    CinematicTrackKind,
    SequenceEntry,
    SequenceTimeline,
    ShotDefinition,
    TimelineEvent,
)
from kodepoia.media.cinematic.godot_capture import (
    CapturePolicy,
    build_ffprobe_movie_argv,
    build_godot_assembly_intent,
    synthetic_capture_fixture_intent,
    verify_capture_probe,
    write_trusted_capture_fixture,
)
from kodepoia.media.cinematic.timebase import Timebase


ROOT = Path(__file__).resolve().parents[1]


def _digest(char: str = "a") -> str:
    return char * 64


def _shot(*, timebase: Timebase | None = None, digest_char: str = "a") -> ShotDefinition:
    tb = timebase or Timebase(30)
    ref = CinematicRef("camera.main", "camera", _digest(digest_char))
    return ShotDefinition(
        "shot.one",
        tb,
        90,
        (ref,),
        (
            TimelineEvent("camera.move", CinematicTrackKind.CAMERA, 0, 90, ref.ref_id, {"camera_id": "camera.main", "fov_deg": 50.0}),
            TimelineEvent("marker.end", CinematicTrackKind.EVENT, 89, 1, None, {"marker_id": "end", "event_kind": "marker"}),
        ),
    )


def _sequence(shot: ShotDefinition) -> SequenceTimeline:
    return SequenceTimeline(
        "sequence.one",
        shot.timebase,
        (SequenceEntry("entry.one", shot.shot_id, shot.digest(), 0, shot.duration_frames),),
    )


def _probe(*, video_duration: str = "3.0", audio_duration: str = "3.0", fps: str = "30/1", width: int = 640, height: int = 360, frames: str = "90") -> dict[str, object]:
    return {
        "streams": [
            {
                "index": 0,
                "codec_type": "video",
                "width": width,
                "height": height,
                "r_frame_rate": fps,
                "avg_frame_rate": fps,
                "nb_frames": frames,
                "duration": video_duration,
            },
            {
                "index": 1,
                "codec_type": "audio",
                "sample_rate": "48000",
                "channels": 2,
                "duration": audio_duration,
            },
        ],
        "format": {"duration": "3.0", "size": "4096"},
    }


def test_build_godot_assembly_intent_is_digest_bound_and_typed() -> None:
    shot = _shot()
    intent = build_godot_assembly_intent(_sequence(shot), {shot.shot_id: shot})
    assert intent.fps == 30
    assert intent.frames == 90
    assert [track.kind for track in intent.tracks] == [CinematicTrackKind.CAMERA, CinematicTrackKind.EVENT]
    canonical = intent.canonical()
    assert set(canonical) == {"sequence_id", "sequence_digest", "fps", "frames", "tracks", "command_policy_id"}
    assert "script" not in json.dumps(canonical).lower()
    assert "path" not in json.dumps(canonical).lower()
    assert canonical["command_policy_id"] == "r11.9.godot.capture.v1"


def test_build_godot_assembly_intent_rejects_non_integer_timebase() -> None:
    shot = _shot(timebase=Timebase(30000, 1001))
    with pytest.raises(ValueError, match="integer fixed FPS"):
        build_godot_assembly_intent(_sequence(shot), {shot.shot_id: shot})


def test_build_godot_assembly_intent_rejects_missing_or_spoofed_shot() -> None:
    shot = _shot()
    sequence = _sequence(shot)
    with pytest.raises(ValueError, match="missing shot"):
        build_godot_assembly_intent(sequence, {})
    spoof = _shot(digest_char="b")
    with pytest.raises(ValueError, match="digest mismatch"):
        build_godot_assembly_intent(sequence, {shot.shot_id: spoof})


def test_capture_policy_is_bounded() -> None:
    CapturePolicy(width=640, height=360, fps=30, frames=90)
    with pytest.raises(ValueError):
        CapturePolicy(width=641)
    with pytest.raises(ValueError):
        CapturePolicy(fps=121)
    with pytest.raises(ValueError):
        CapturePolicy(frames=3601)
    with pytest.raises(ValueError):
        CapturePolicy(max_output_bytes=513 * 1024 * 1024)


def test_trusted_fixture_is_fixed_and_contains_no_process_escape(tmp_path: Path) -> None:
    policy = CapturePolicy(width=640, height=360, fps=30, frames=90)
    intent = synthetic_capture_fixture_intent(fps=policy.fps, frames=policy.frames)
    digests = write_trusted_capture_fixture(tmp_path, policy, intent)
    assert set(digests) == {"project.godot", "capture.gd", "capture.tscn", "tone.wav", "assembly.json"}
    assert {item.name for item in tmp_path.iterdir()} == set(digests)
    script = (tmp_path / "capture.gd").read_text(encoding="utf-8")
    lowered = script.lower()
    assert "os.execute" not in lowered
    assert "subprocess" not in lowered
    assert "shell" not in lowered
    assert "http" not in lowered
    assembly = json.loads((tmp_path / "assembly.json").read_text(encoding="utf-8"))
    assert assembly["command_policy_id"] == "r11.9.godot.capture.v1"


def test_ffprobe_movie_argv_is_fixed_and_rejects_wrong_suffix(tmp_path: Path) -> None:
    ffprobe = tmp_path / "ffprobe.exe"
    ffprobe.write_bytes(b"fixture")
    movie = tmp_path / "capture.avi"
    movie.write_bytes(b"RIFFfixture")
    argv = build_ffprobe_movie_argv(ffprobe, movie)
    assert argv[0] == str(ffprobe.resolve())
    assert argv[-1] == str(movie.resolve())
    assert "-of" in argv and "json" in argv
    bad = tmp_path / "capture.mp4"
    bad.write_bytes(b"fixture")
    with pytest.raises(ValueError, match="AVI"):
        build_ffprobe_movie_argv(ffprobe, bad)


def test_capture_probe_accepts_exact_synthetic_av() -> None:
    policy = CapturePolicy(width=640, height=360, fps=30, frames=90)
    report = verify_capture_probe(_probe(), policy=policy, output_bytes=4096, output_sha256=_digest("c"))
    assert report["status"] == "pass"
    assert report["reported_frames"] == 90
    assert report["av_sync_error_seconds"] == 0.0


@pytest.mark.parametrize(
    "document,bytes_count,match",
    [
        (_probe(width=1280), 4096, "resolution"),
        (_probe(fps="60/1"), 4096, "frame rate"),
        (_probe(audio_duration="2.8"), 4096, "sync"),
        ({"streams": [_probe()["streams"][0]], "format": {"duration": "3.0"}}, 4096, "one video and one audio"),
        (_probe(), 65 * 1024 * 1024, "byte budget"),
    ],
)
def test_capture_probe_fails_closed(document: dict[str, object], bytes_count: int, match: str) -> None:
    policy = CapturePolicy(width=640, height=360, fps=30, frames=90, max_output_bytes=64 * 1024 * 1024)
    with pytest.raises(ValueError, match=match):
        verify_capture_probe(document, policy=policy, output_bytes=bytes_count, output_sha256=_digest("d"))


class FakeRunner:
    def __init__(self, capture_result: SandboxResult | None = None) -> None:
        self.calls: list[list[str]] = []
        self.capture_result = capture_result or SandboxResult(0, "", "")

    def run(self, argv: list[str], *, cwd: Path | None = None, timeout: float = 60.0, env: dict[str, str] | None = None) -> SandboxResult:
        self.calls.append(list(argv))
        if "--version" in argv:
            return SandboxResult(0, "4.7.0.stable.official\n", "")
        return self.capture_result


def _fake_runtime(tmp_path: Path, result: SandboxResult | None = None) -> tuple[GodotRuntime, FakeRunner]:
    (tmp_path / "project.godot").write_text("[application]\n", encoding="utf-8")
    (tmp_path / "capture.tscn").write_text("[gd_scene format=3]\n[node name=\"Root\" type=\"Node\"]\n", encoding="utf-8")
    runner = FakeRunner(result)
    return GodotRuntime(tmp_path, executable="godot.exe", runner=runner), runner


def test_existing_r5_runtime_compiles_exact_movie_command(tmp_path: Path) -> None:
    runtime, runner = _fake_runtime(tmp_path)
    invocation = runtime.capture_movie(scene="capture.tscn", output_name="r11_9_capture.avi", frames=90, fps=30, timeout=60.0)
    assert invocation.ok
    argv = runner.calls[-1]
    assert argv == [
        "godot.exe",
        "--path", ".",
        "--write-movie", ".kodepoia/captures/r11_9_capture.avi",
        "--fixed-fps", "30",
        "--quit-after", "90",
        "--scene", "res://capture.tscn",
    ]
    assert "--headless" not in argv


@pytest.mark.parametrize(
    "result",
    [
        SandboxResult(1, "", "capture failed"),
        SandboxResult(-1, "", "", timed_out=True),
        SandboxResult(-1, "", "", cancelled=True),
    ],
)
def test_existing_r5_runtime_surfaces_failure_timeout_and_cancel(tmp_path: Path, result: SandboxResult) -> None:
    runtime, _runner = _fake_runtime(tmp_path, result)
    invocation = runtime.capture_movie(scene="capture.tscn", output_name="r11_9_capture.avi", frames=90, fps=30, timeout=60.0)
    assert not invocation.ok


def test_r11_9_schemas_accept_canonical_examples() -> None:
    intent = synthetic_capture_fixture_intent()
    intent_schema = json.loads((ROOT / "schemas/r11/godot-cinematic-assembly-intent.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(intent_schema).validate(intent.canonical())

    evidence = {
        "schema": "kodepoia.r11_9_local_acceptance",
        "version": 1,
        "source_sha": "e" * 40,
        "status": "pass",
        "blockers": [],
        "error_type": None,
        "runtime": {"platform": "Windows", "godot_compatible_47": True},
        "fixture": {"kind": "repository_synthetic", "file_sha256": {"capture.gd": _digest("a")}},
        "assembly": {"sequence_id": "r11.9.synthetic.sequence", "digest": intent.digest(), "command_policy_id": "r11.9.godot.capture.v1"},
        "capture": {"status": "pass"},
        "evidence_digest": _digest("f"),
    }
    evidence_schema = json.loads((ROOT / "schemas/r11/r11-9-local-acceptance.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(evidence_schema).validate(evidence)
