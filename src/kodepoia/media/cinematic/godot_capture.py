from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import struct
import wave
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Protocol

from kodepoia.core.sandbox import ProcessSandbox, SandboxResult
from kodepoia.kodegodot.runtime import GodotRuntime
from kodepoia.media.contracts import bounded_text, sha256_hex, stable_id
from kodepoia.media.serialization import canonical_sha256

from .contracts import CinematicTrackKind, SequenceTimeline, ShotDefinition

_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_COMMAND_POLICY_ID = "r11.9.godot.capture.v1"
_ALLOWED_FFPROBE_NAMES = frozenset({"ffprobe", "ffprobe.exe"})


class CaptureRunner(Protocol):
    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: dict[str, str] | None = None,
    ) -> SandboxResult: ...


@dataclass(frozen=True, slots=True)
class CapturePolicy:
    width: int = 640
    height: int = 360
    fps: int = 30
    frames: int = 90
    max_output_bytes: int = 64 * 1024 * 1024
    video_tolerance_frames: int = 1
    av_sync_tolerance_frames: int = 2

    def __post_init__(self) -> None:
        if self.width not in {320, 640, 960, 1280, 1920}:
            raise ValueError("capture width is not allowlisted")
        if self.height not in {180, 360, 540, 720, 1080}:
            raise ValueError("capture height is not allowlisted")
        if not 1 <= self.fps <= 120:
            raise ValueError("capture fps must be in [1,120]")
        if not 1 <= self.frames <= 3600:
            raise ValueError("capture frames must be in [1,3600]")
        if not 1024 <= self.max_output_bytes <= 512 * 1024 * 1024:
            raise ValueError("capture output byte budget is invalid")
        if not 0 <= self.video_tolerance_frames <= 3:
            raise ValueError("video tolerance must be 0..3 frames")
        if not 0 <= self.av_sync_tolerance_frames <= 5:
            raise ValueError("A/V sync tolerance must be 0..5 frames")

    @property
    def duration(self) -> Fraction:
        return Fraction(self.frames, self.fps)

    def canonical(self) -> dict[str, int]:
        return {
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "frames": self.frames,
            "max_output_bytes": self.max_output_bytes,
            "video_tolerance_frames": self.video_tolerance_frames,
            "av_sync_tolerance_frames": self.av_sync_tolerance_frames,
        }


@dataclass(frozen=True, slots=True)
class GodotTrackIntent:
    event_id: str
    kind: CinematicTrackKind
    start_frame: int
    duration_frames: int
    ref_id: str | None

    def __post_init__(self) -> None:
        stable_id(self.event_id, field="event_id")
        if not isinstance(self.kind, CinematicTrackKind):
            raise TypeError("kind must be CinematicTrackKind")
        if isinstance(self.start_frame, bool) or not isinstance(self.start_frame, int) or self.start_frame < 0:
            raise ValueError("start_frame must be a non-negative integer")
        if isinstance(self.duration_frames, bool) or not isinstance(self.duration_frames, int) or self.duration_frames <= 0:
            raise ValueError("duration_frames must be positive")
        if self.ref_id is not None:
            stable_id(self.ref_id, field="ref_id")

    def canonical(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "kind": self.kind.value,
            "start_frame": self.start_frame,
            "duration_frames": self.duration_frames,
            "ref_id": self.ref_id,
        }


@dataclass(frozen=True, slots=True)
class GodotCinematicAssemblyIntent:
    sequence_id: str
    sequence_digest: str
    fps: int
    frames: int
    tracks: tuple[GodotTrackIntent, ...]
    command_policy_id: str = _COMMAND_POLICY_ID

    def __post_init__(self) -> None:
        stable_id(self.sequence_id, field="sequence_id")
        sha256_hex(self.sequence_digest, field="sequence_digest")
        if not 1 <= self.fps <= 120:
            raise ValueError("Godot capture fps must be in [1,120]")
        if not 1 <= self.frames <= 3600:
            raise ValueError("Godot capture frame budget exceeded")
        if len(self.tracks) > 8192:
            raise ValueError("Godot track budget exceeded")
        bounded_text(self.command_policy_id, field="command_policy_id", maximum=128)
        if self.command_policy_id != _COMMAND_POLICY_ID:
            raise ValueError("unknown capture command policy")
        previous = -1
        ids: set[str] = set()
        for track in self.tracks:
            if track.event_id in ids:
                raise ValueError("duplicate Godot track event id")
            ids.add(track.event_id)
            if track.start_frame < previous:
                raise ValueError("Godot tracks must be globally monotonic")
            if track.start_frame + track.duration_frames > self.frames:
                raise ValueError("Godot track exceeds capture duration")
            previous = track.start_frame

    def canonical(self) -> dict[str, Any]:
        return {
            "sequence_id": self.sequence_id,
            "sequence_digest": self.sequence_digest,
            "fps": self.fps,
            "frames": self.frames,
            "tracks": [track.canonical() for track in self.tracks],
            "command_policy_id": self.command_policy_id,
        }

    def digest(self) -> str:
        return canonical_sha256({"schema": "kodepoia.r11.godot_cinematic_assembly_intent", "version": 1, "payload": self.canonical()})


def build_godot_assembly_intent(sequence: SequenceTimeline, shots: Mapping[str, ShotDefinition]) -> GodotCinematicAssemblyIntent:
    if sequence.timebase.fps_den != 1:
        raise ValueError("Godot movie capture requires an integer fixed FPS timebase")
    fps = sequence.timebase.fps_num
    tracks: list[GodotTrackIntent] = []
    for entry in sorted(sequence.entries, key=lambda item: (item.start_frame, item.entry_id)):
        shot = shots.get(entry.shot_id)
        if shot is None:
            raise ValueError(f"missing shot for sequence entry: {entry.shot_id}")
        if shot.digest() != entry.shot_digest:
            raise ValueError("sequence entry shot digest mismatch")
        if shot.timebase != sequence.timebase:
            raise ValueError("shot/sequence timebase mismatch")
        if entry.duration_frames != shot.duration_frames:
            raise ValueError("sequence entry duration must equal referenced shot duration for capture")
        for event in shot.events:
            tracks.append(
                GodotTrackIntent(
                    event_id=f"{entry.entry_id}.{event.event_id}",
                    kind=event.track_kind,
                    start_frame=entry.start_frame + event.start_frame,
                    duration_frames=event.duration_frames,
                    ref_id=event.ref_id,
                )
            )
    tracks.sort(key=lambda item: (item.start_frame, item.event_id))
    return GodotCinematicAssemblyIntent(
        sequence_id=sequence.sequence_id,
        sequence_digest=sequence.digest(),
        fps=fps,
        frames=sequence.duration_frames,
        tracks=tuple(tracks),
    )


def synthetic_capture_fixture_intent(*, fps: int = 30, frames: int = 90) -> GodotCinematicAssemblyIntent:
    zero = "0" * 64
    kinds = (
        CinematicTrackKind.CAMERA,
        CinematicTrackKind.BODY,
        CinematicTrackKind.FACIAL,
        CinematicTrackKind.DIALOGUE,
        CinematicTrackKind.MUSIC,
        CinematicTrackKind.SFX,
        CinematicTrackKind.FOLEY,
        CinematicTrackKind.SUBTITLE,
        CinematicTrackKind.EVENT,
    )
    tracks = tuple(
        GodotTrackIntent(f"fixture.{kind.value}", kind, 0, frames, None)
        for kind in kinds
    )
    return GodotCinematicAssemblyIntent("r11.9.synthetic.sequence", zero, fps, frames, tracks)


def _tone_bytes(*, sample_rate: int, duration: Fraction) -> bytes:
    import io

    count = int(round(float(duration) * sample_rate))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        for index in range(count):
            sample = int(6000.0 * math.sin(2.0 * math.pi * 440.0 * index / sample_rate))
            frame = struct.pack("<hh", sample, sample)
            handle.writeframesraw(frame)
    return buffer.getvalue()


def write_trusted_capture_fixture(root: Path, policy: CapturePolicy, intent: GodotCinematicAssemblyIntent) -> dict[str, str]:
    root = Path(root).resolve(strict=False)
    root.mkdir(parents=True, exist_ok=True)
    if policy.fps != intent.fps or policy.frames != intent.frames:
        raise ValueError("fixture policy and assembly intent disagree")

    project = f'''[application]\nconfig/name="Kodepoia R11.9 Synthetic Capture"\nrun/main_scene="res://capture.tscn"\n\n[display]\nwindow/size/viewport_width={policy.width}\nwindow/size/viewport_height={policy.height}\nwindow/size/window_width_override={policy.width}\nwindow/size/window_height_override={policy.height}\n\n[rendering]\nrenderer/rendering_method="gl_compatibility"\nrenderer/rendering_method.mobile="gl_compatibility"\n\n[audio]\ndriver/enable_input=false\n'''
    script = '''extends Node3D\n\n@onready var body: MeshInstance3D = $Body\n@onready var face: MeshInstance3D = $Face\nvar frame_index: int = 0\n\nfunc _process(_delta: float) -> void:\n    frame_index += 1\n    body.rotation.y = float(frame_index) * 0.025\n    face.scale.y = 0.9 + 0.1 * sin(float(frame_index) * 0.2)\n'''
    scene = '''[gd_scene load_steps=5 format=3]\n\n[ext_resource type="Script" path="res://capture.gd" id="1_script"]\n[ext_resource type="AudioStream" path="res://tone.wav" id="2_audio"]\n\n[sub_resource type="BoxMesh" id="BoxMesh_body"]\nsize = Vector3(1.4, 1.4, 1.4)\n\n[sub_resource type="SphereMesh" id="SphereMesh_face"]\nradius = 0.45\nheight = 0.9\n\n[node name="Capture" type="Node3D"]\nscript = ExtResource("1_script")\n\n[node name="Camera3D" type="Camera3D" parent="."]\ntransform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.4, 6)\ncurrent = true\n\n[node name="DirectionalLight3D" type="DirectionalLight3D" parent="."]\nrotation_degrees = Vector3(-35, -25, 0)\nshadow_enabled = true\n\n[node name="Body" type="MeshInstance3D" parent="."]\nposition = Vector3(-0.8, 0, 0)\nmesh = SubResource("BoxMesh_body")\n\n[node name="Face" type="MeshInstance3D" parent="."]\nposition = Vector3(0.9, 0.2, 0)\nmesh = SubResource("SphereMesh_face")\n\n[node name="Tone" type="AudioStreamPlayer" parent="."]\nstream = ExtResource("2_audio")\nautoplay = true\n'''
    tone = _tone_bytes(sample_rate=48000, duration=policy.duration)
    assembly = json.dumps(intent.canonical(), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"

    files: dict[str, bytes] = {
        "project.godot": project.encode("utf-8"),
        "capture.gd": script.encode("utf-8"),
        "capture.tscn": scene.encode("utf-8"),
        "tone.wav": tone,
        "assembly.json": assembly.encode("utf-8"),
    }
    digests: dict[str, str] = {}
    for name, payload in files.items():
        target = root / name
        target.write_bytes(payload)
        digests[name] = hashlib.sha256(payload).hexdigest()
    return digests


def resolve_executable(value: str, *, allowed_names: frozenset[str]) -> Path:
    raw = str(value).strip()
    candidate = Path(raw)
    if candidate.exists():
        resolved = candidate.resolve(strict=True)
    else:
        found = shutil.which(raw)
        if not found:
            raise FileNotFoundError(f"runtime executable not found: {value}")
        resolved = Path(found).resolve(strict=True)
    if not resolved.is_file() or resolved.name.lower() not in allowed_names:
        raise ValueError(f"runtime executable is not allowlisted: {resolved.name}")
    return resolved


def build_ffprobe_movie_argv(ffprobe: Path, movie: Path) -> tuple[str, ...]:
    ffprobe = Path(ffprobe).resolve(strict=True)
    movie = Path(movie).resolve(strict=True)
    if ffprobe.name.lower() not in _ALLOWED_FFPROBE_NAMES:
        raise ValueError("ffprobe executable name is not allowlisted")
    if movie.suffix.lower() != ".avi" or not movie.is_file():
        raise ValueError("R11.9 verifier requires an existing AVI capture")
    return (
        str(ffprobe),
        "-v", "error",
        "-show_entries", "format=duration,size:stream=index,codec_type,width,height,r_frame_rate,avg_frame_rate,nb_frames,duration,sample_rate,channels",
        "-of", "json",
        str(movie),
    )


def _finite_float(value: object, *, field: str) -> float:
    try:
        result = float(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} is not numeric") from exc
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{field} must be finite and non-negative")
    return result


def _fraction(value: object, *, field: str) -> Fraction:
    text = str(value)
    try:
        result = Fraction(text)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{field} is not a rational value") from exc
    if result <= 0:
        raise ValueError(f"{field} must be positive")
    return result


def verify_capture_probe(document: Mapping[str, Any], *, policy: CapturePolicy, output_bytes: int, output_sha256: str) -> dict[str, Any]:
    sha256_hex(output_sha256, field="output_sha256")
    if not 1 <= output_bytes <= policy.max_output_bytes:
        raise ValueError("capture output byte budget violated")
    streams = document.get("streams")
    fmt = document.get("format")
    if not isinstance(streams, list) or not isinstance(fmt, Mapping):
        raise ValueError("ffprobe document shape is invalid")
    videos = [item for item in streams if isinstance(item, Mapping) and item.get("codec_type") == "video"]
    audios = [item for item in streams if isinstance(item, Mapping) and item.get("codec_type") == "audio"]
    if len(videos) != 1 or len(audios) != 1:
        raise ValueError("capture must contain exactly one video and one audio stream")
    video = videos[0]
    audio = audios[0]
    if int(video.get("width", -1)) != policy.width or int(video.get("height", -1)) != policy.height:
        raise ValueError("capture resolution mismatch")
    rate_value = video.get("avg_frame_rate") or video.get("r_frame_rate")
    rate = _fraction(rate_value, field="video frame rate")
    if rate != Fraction(policy.fps, 1):
        raise ValueError("capture frame rate mismatch")
    format_duration = _finite_float(fmt.get("duration"), field="format duration")
    expected = float(policy.duration)
    frame_seconds = 1.0 / policy.fps
    if abs(format_duration - expected) > policy.video_tolerance_frames * frame_seconds + 0.01:
        raise ValueError("capture duration outside frozen video tolerance")
    nb_frames_raw = video.get("nb_frames")
    if nb_frames_raw not in (None, "", "N/A"):
        try:
            nb_frames = int(str(nb_frames_raw))
        except ValueError as exc:
            raise ValueError("video nb_frames is invalid") from exc
        if abs(nb_frames - policy.frames) > policy.video_tolerance_frames:
            raise ValueError("capture frame count outside frozen tolerance")
    video_duration = _finite_float(video.get("duration", format_duration), field="video duration")
    audio_duration = _finite_float(audio.get("duration", format_duration), field="audio duration")
    sync_error = abs(video_duration - audio_duration)
    sync_limit = policy.av_sync_tolerance_frames * frame_seconds + 0.01
    if sync_error > sync_limit:
        raise ValueError("A/V sync error exceeds frozen tolerance")
    sample_rate = int(str(audio.get("sample_rate", "0")))
    channels = int(audio.get("channels", 0))
    if sample_rate not in {44100, 48000} or channels not in {1, 2}:
        raise ValueError("unexpected audio stream facts")
    return {
        "status": "pass",
        "width": policy.width,
        "height": policy.height,
        "fps": policy.fps,
        "expected_frames": policy.frames,
        "reported_frames": int(str(nb_frames_raw)) if nb_frames_raw not in (None, "", "N/A") else None,
        "expected_duration_seconds": expected,
        "format_duration_seconds": format_duration,
        "video_duration_seconds": video_duration,
        "audio_duration_seconds": audio_duration,
        "av_sync_error_seconds": sync_error,
        "av_sync_limit_seconds": sync_limit,
        "audio_sample_rate_hz": sample_rate,
        "audio_channels": channels,
        "output_bytes": output_bytes,
        "output_sha256": output_sha256,
    }


def run_local_capture(
    *,
    project_root: Path,
    godot: Path,
    ffprobe: Path,
    policy: CapturePolicy,
    intent: GodotCinematicAssemblyIntent,
    timeout: float = 300.0,
) -> dict[str, Any]:
    project_root = Path(project_root).resolve(strict=True)
    godot = Path(godot).resolve(strict=True)
    ffprobe = Path(ffprobe).resolve(strict=True)
    godot_runtime = GodotRuntime(project_root, executable=str(godot))
    version = godot_runtime.require_47()
    invocation = godot_runtime.capture_movie(
        scene="capture.tscn",
        output_name="r11_9_capture.avi",
        frames=policy.frames,
        fps=policy.fps,
        timeout=timeout,
    )
    if not invocation.ok:
        raise RuntimeError(
            f"Godot capture failed: rc={invocation.returncode} timed_out={invocation.timed_out} cancelled={invocation.cancelled} stderr={invocation.stderr.strip()}"
        )
    movie = project_root / ".kodepoia" / "captures" / "r11_9_capture.avi"
    if not movie.is_file():
        raise RuntimeError("Godot reported success but capture output is missing")
    payload = movie.read_bytes()
    if not payload:
        raise RuntimeError("Godot produced an empty capture")
    movie_sha = hashlib.sha256(payload).hexdigest()
    ffprobe_runner = ProcessSandbox(project_root, allowed_executables={ffprobe.name.lower()})
    probe_result = ffprobe_runner.run(list(build_ffprobe_movie_argv(ffprobe, movie)), cwd=project_root, timeout=min(timeout, 120.0))
    if probe_result.returncode != 0 or probe_result.timed_out or probe_result.cancelled:
        raise RuntimeError("ffprobe validation failed")
    try:
        probe_document = json.loads(probe_result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("ffprobe returned malformed JSON") from exc
    if not isinstance(probe_document, Mapping):
        raise RuntimeError("ffprobe root must be an object")
    verification = verify_capture_probe(probe_document, policy=policy, output_bytes=len(payload), output_sha256=movie_sha)
    return {
        "godot": {
            "version": version.raw,
            "compatible_47": version.compatible_47,
            "returncode": invocation.returncode,
            "timed_out": invocation.timed_out,
            "cancelled": invocation.cancelled,
        },
        "capture": verification,
        "assembly_id": intent.sequence_id,
        "assembly_digest": intent.digest(),
        "command_policy_id": intent.command_policy_id,
    }


def validate_source_sha(value: str) -> str:
    if not _SOURCE_SHA_RE.fullmatch(value):
        raise ValueError("source SHA must be the exact lowercase 40-character candidate SHA")
    return value
