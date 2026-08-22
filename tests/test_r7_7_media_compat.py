from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PIL import Image

from kodepoia.core.sandbox import SandboxResult
from kodepoia.intelligence.research.media import (
    AcceptanceStatus,
    LocalMediaAcceptance,
    MediaDoctor,
    _fixture_transcript_matches_expected,
)


class LegacyCompatibleFakeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def run(self, argv: Sequence[str], *, cwd: Path, timeout: float) -> SandboxResult:
        del cwd, timeout
        args = tuple(str(item) for item in argv)
        self.calls.append(args)
        executable = Path(args[0]).name.lower()
        if "ffmpeg" in executable and "-version" in args:
            return SandboxResult(0, "ffmpeg version 4.2.3 test\n", "")
        if "whisper-cli" in executable and "--version" in args:
            return SandboxResult(0, "whisper.cpp version: 1.9.1\n", "")
        if "whisper-cli" in executable and "-h" in args:
            return SandboxResult(0, "--output-json --output-json-full --output-file --no-gpu\n", "")
        if "whisper-cli" in executable:
            output_base = Path(args[args.index("-of") + 1])
            output_base.with_suffix(".json").write_text(
                '{"transcription":[{"text":"1, 2, 3, 4.","offsets":{"from":0,"to":1000}}]}',
                encoding="utf-8",
            )
            return SandboxResult(0, "", "")
        if "ffmpeg" in executable:
            output = Path(args[-1])
            if output.suffix == ".wav":
                output.write_bytes(b"RIFF" + (b"0" * 256))
                return SandboxResult(0, "", "")
            if output.suffix == ".png":
                if "-fps_mode" in args:
                    return SandboxResult(1, "", "Unrecognized option 'fps_mode'.")
                value = int(float(args[args.index("-ss") + 1]) * 50) % 255
                Image.new("RGB", (320, 180), (value, 1, 2)).save(output)
                return SandboxResult(0, "", "")
        return SandboxResult(1, "", "unexpected fake invocation")


def _project(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "project"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_text("b" * 40 + "\n", encoding="utf-8")
    fixture = root / "tests" / "fixtures" / "research" / "r7_7_media_fixture.mp4"
    fixture.parent.mkdir(parents=True)
    fixture.write_bytes(b"fixture")
    ffmpeg = root / "ffmpeg.exe"
    whisper = root / "whisper-cli.exe"
    ffmpeg.write_bytes(b"legacy-ffmpeg")
    whisper.write_bytes(b"whisper")
    model = root / ".kodepoia" / "models" / "stt" / "ggml-base.en.bin"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"model")
    return root, ffmpeg, whisper


def test_fixture_transcript_accepts_words_digits_and_mixed_forms() -> None:
    assert _fixture_transcript_matches_expected("one two three four")
    assert _fixture_transcript_matches_expected("1, 2, 3, 4.")
    assert _fixture_transcript_matches_expected("one, 2, three, 4")


def test_fixture_transcript_rejects_wrong_order_or_missing_number() -> None:
    assert not _fixture_transcript_matches_expected("1 3 2 4")
    assert not _fixture_transcript_matches_expected("one two three")
    assert not _fixture_transcript_matches_expected("four three two one")


def test_frame_command_avoids_post_2022_fps_mode_option(tmp_path: Path, monkeypatch) -> None:
    root, ffmpeg, whisper = _project(tmp_path)
    runner = LegacyCompatibleFakeRunner()
    doctor = MediaDoctor(root, runner, ffmpeg_executable=ffmpeg, whisper_executable=whisper)

    import kodepoia.intelligence.research.media as media

    monkeypatch.setattr(media, "EXPECTED_FIXTURE_SHA256", media._sha256_file(root / "tests" / "fixtures" / "research" / "r7_7_media_fixture.mp4"))
    report = LocalMediaAcceptance(root, runner, doctor).run("tests/fixtures/research/r7_7_media_fixture.mp4")

    assert report.status is AcceptanceStatus.PASS
    frame_calls = [call for call in runner.calls if "ffmpeg" in Path(call[0]).name.lower() and "-frames:v" in call]
    assert len(frame_calls) == 3
    assert all("-fps_mode" not in call for call in frame_calls)
    assert all("-frames:v" in call and call[call.index("-frames:v") + 1] == "1" for call in frame_calls)
