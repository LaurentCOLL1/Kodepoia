from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Sequence

import pytest
from jsonschema import Draft202012Validator
from PIL import Image

from kodepoia.core.sandbox import SandboxResult
from kodepoia.intelligence.research.contracts import ResearchStatus
from kodepoia.intelligence.research.media import (
    EXPECTED_FIXTURE_SHA256,
    AcceptanceStatus,
    LocalMediaAcceptance,
    MediaDoctor,
    MediaExecutionPolicy,
    MediaProcessingError,
    UnavailableFrameAnalysisProvider,
    build_governed_media_runner,
    parse_whisper_json,
)
from kodepoia.exceptions import PermissionDenied


class FakeMediaRunner:
    def __init__(self, *, timeout_audio: bool = False) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.timeout_audio = timeout_audio

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        timeout: float,
    ) -> SandboxResult:
        del cwd, timeout
        args = tuple(str(item) for item in argv)
        self.calls.append(args)
        executable = Path(args[0]).name.lower()
        if "ffmpeg" in executable and "-version" in args:
            return SandboxResult(0, "ffmpeg version 7.1.5 test\n", "")
        if "whisper-cli" in executable and "--version" in args:
            return SandboxResult(0, "whisper.cpp version 1.9.1\n", "")
        if "whisper-cli" in executable and "-h" in args:
            return SandboxResult(
                0,
                "--output-json --output-json-full --output-file --no-gpu\n",
                "",
            )
        if "whisper-cli" in executable:
            output_base = Path(args[args.index("-of") + 1])
            payload = {
                "transcription": [
                    {
                        "text": " one two three four ",
                        "offsets": {"from": 100, "to": 1500},
                    }
                ]
            }
            output_base.with_suffix(".json").write_text(json.dumps(payload), encoding="utf-8")
            return SandboxResult(0, "", "")
        if "ffmpeg" in executable:
            output = Path(args[-1])
            if output.suffix == ".wav":
                if self.timeout_audio:
                    return SandboxResult(-1, "", "", timed_out=True)
                output.write_bytes(b"RIFF" + (b"0" * 256))
                return SandboxResult(0, "", "")
            if output.suffix == ".png":
                timestamp = args[args.index("-ss") + 1]
                value = int(float(timestamp) * 50) % 255
                Image.new("RGB", (320, 180), (value, 1, 2)).save(output)
                return SandboxResult(0, "", "")
        return SandboxResult(1, "", "unexpected fake invocation")


def _fixture_source() -> Path:
    return Path(__file__).parent / "fixtures" / "research" / "r7_7_media_fixture.mp4.b64"


def _project(tmp_path: Path, *, model: bool = True) -> tuple[Path, Path, Path]:
    root = tmp_path / "project"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_text("a" * 40 + "\n", encoding="utf-8")
    fixture_dir = root / "tests" / "fixtures" / "research"
    fixture_dir.mkdir(parents=True)
    fixture_text = _fixture_source().read_text(encoding="ascii")
    (fixture_dir / "r7_7_media_fixture.mp4.b64").write_text(fixture_text, encoding="ascii")
    ffmpeg = root / ("ffmpeg.exe" if __import__("os").name == "nt" else "ffmpeg")
    whisper = root / ("whisper-cli.exe" if __import__("os").name == "nt" else "whisper-cli")
    ffmpeg.write_bytes(b"fake-ffmpeg")
    whisper.write_bytes(b"fake-whisper")
    model_path = root / ".kodepoia" / "models" / "stt" / "ggml-base.en.bin"
    model_path.parent.mkdir(parents=True)
    if model:
        model_path.write_bytes(b"fake-model")
    return root, ffmpeg, whisper


def test_fixture_payload_is_canonical_and_small() -> None:
    raw = base64.b64decode(_fixture_source().read_text(encoding="ascii"), validate=True)
    assert len(raw) == 12112
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_FIXTURE_SHA256


def test_whisper_json_preserves_millisecond_offsets() -> None:
    segments = parse_whisper_json(
        {
            "transcription": [
                {"text": "hello", "offsets": {"from": 125, "to": 975}, "confidence": 0.8},
                {"text": "skip", "offsets": {"from": "bad", "to": 1200}},
            ]
        }
    )
    assert len(segments) == 1
    assert segments[0].start_ms == 125
    assert segments[0].end_ms == 975
    assert segments[0].confidence == 0.8


def test_whisper_json_rejects_missing_transcription() -> None:
    with pytest.raises(MediaProcessingError):
        parse_whisper_json({"result": []})


def test_doctor_reports_missing_model_as_unavailable(tmp_path: Path) -> None:
    root, ffmpeg, whisper = _project(tmp_path, model=False)
    report = MediaDoctor(
        root,
        FakeMediaRunner(),
        ffmpeg_executable=ffmpeg,
        whisper_executable=whisper,
    ).run()
    assert report.ready is False
    assert report.ffmpeg.status is ResearchStatus.READY
    assert report.stt.status is ResearchStatus.READY
    assert report.stt_model.status is ResearchStatus.UNAVAILABLE
    assert report.stt_model.reason == "model_not_found"


def test_full_fake_acceptance_uses_fixed_cpu_stt_and_cleans_temp(tmp_path: Path) -> None:
    root, ffmpeg, whisper = _project(tmp_path)
    runner = FakeMediaRunner()
    doctor = MediaDoctor(root, runner, ffmpeg_executable=ffmpeg, whisper_executable=whisper)
    report = LocalMediaAcceptance(
        root,
        runner,
        doctor,
        policy=MediaExecutionPolicy(frame_timestamps_ms=(500, 1500, 2500)),
        frame_analysis=UnavailableFrameAnalysisProvider(),
    ).run("tests/fixtures/research/r7_7_media_fixture.mp4")

    assert report.status is AcceptanceStatus.PASS
    assert report.source_sha == "a" * 40
    assert report.fixture_sha256 == EXPECTED_FIXTURE_SHA256
    assert report.cleanup_passed is True
    assert len(report.frames) == 3
    assert len({frame.sha256 for frame in report.frames}) == 3
    assert report.vision_status is ResearchStatus.UNAVAILABLE
    assert report.resources.cpu_measurement_status is ResearchStatus.UNKNOWN
    assert report.resources.ram_measurement_status is ResearchStatus.UNKNOWN
    whisper_calls = [call for call in runner.calls if "whisper-cli" in Path(call[0]).name.lower() and "-f" in call]
    assert len(whisper_calls) == 1
    whisper_call = whisper_calls[0]
    assert "-ng" in whisper_call
    assert "-ojf" in whisper_call
    assert "-of" in whisper_call
    assert "--model-download" not in whisper_call
    assert not any((root / ".kodepoia" / "research" / "tmp").glob("r7_7_*"))


def test_timeout_fails_closed_and_still_cleans_temp(tmp_path: Path) -> None:
    root, ffmpeg, whisper = _project(tmp_path)
    runner = FakeMediaRunner(timeout_audio=True)
    doctor = MediaDoctor(root, runner, ffmpeg_executable=ffmpeg, whisper_executable=whisper)
    report = LocalMediaAcceptance(root, runner, doctor).run(
        "tests/fixtures/research/r7_7_media_fixture.mp4"
    )
    assert report.status is AcceptanceStatus.FAIL
    assert report.cleanup_passed is True
    assert any(check.check_id == "processing" and not check.passed for check in report.checks)


def test_governed_runner_rejects_non_allowlisted_executable(tmp_path: Path) -> None:
    runner = build_governed_media_runner(tmp_path)
    with pytest.raises(PermissionDenied):
        runner.run(("python", "-V"), cwd=tmp_path, timeout=1.0)


def test_report_schemas_accept_deterministic_fake_evidence(tmp_path: Path) -> None:
    root, ffmpeg, whisper = _project(tmp_path)
    runner = FakeMediaRunner()
    doctor = MediaDoctor(root, runner, ffmpeg_executable=ffmpeg, whisper_executable=whisper)
    doctor_payload = doctor.run().to_dict()
    acceptance_payload = LocalMediaAcceptance(root, runner, doctor).run(
        "tests/fixtures/research/r7_7_media_fixture.mp4"
    ).to_dict()

    repository_root = Path(__file__).resolve().parents[1]
    doctor_schema = json.loads(
        (repository_root / "schemas" / "research-media-doctor-v1.schema.json").read_text(encoding="utf-8")
    )
    acceptance_schema = json.loads(
        (repository_root / "schemas" / "research-media-acceptance-v1.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(doctor_schema).validate(doctor_payload)
    Draft202012Validator(acceptance_schema).validate(acceptance_payload)
