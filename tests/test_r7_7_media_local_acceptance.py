from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.intelligence.research.media import (
    EXPECTED_FIXTURE_SHA256,
    _fixture_transcript_matches_expected,
)


_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA64 = re.compile(r"^[0-9a-f]{64}$")


def _git_head(root: Path) -> str:
    git_dir = root / ".git"
    raw = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    if _SHA40.fullmatch(raw):
        return raw
    assert raw.startswith("ref: ")
    ref_name = raw[5:].strip()
    ref_path = git_dir / ref_name
    if ref_path.exists():
        value = ref_path.read_text(encoding="utf-8").strip()
        if _SHA40.fullmatch(value):
            return value
    packed = git_dir / "packed-refs"
    if packed.exists():
        for line in packed.read_text(encoding="utf-8").splitlines():
            if line.endswith(f" {ref_name}"):
                value = line.split(" ", 1)[0]
                if _SHA40.fullmatch(value):
                    return value
    raise AssertionError("cannot resolve exact current Git head")


def test_r7_7_authoritative_local_acceptance_evidence() -> None:
    root = Path(__file__).resolve().parents[1]
    doctor_path = root / ".kodepoia" / "research" / "r7_7_media_doctor.json"
    acceptance_path = root / ".kodepoia" / "research" / "r7_7_local_acceptance.json"
    if not doctor_path.exists() or not acceptance_path.exists():
        pytest.skip("R7.7 REQUIRED local evidence has not been generated on this checkout")

    doctor = json.loads(doctor_path.read_text(encoding="utf-8"))
    acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
    doctor_schema = json.loads(
        (root / "schemas" / "research-media-doctor-v1.schema.json").read_text(encoding="utf-8")
    )
    acceptance_schema = json.loads(
        (root / "schemas" / "research-media-acceptance-v1.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(doctor_schema).validate(doctor)
    Draft202012Validator(acceptance_schema).validate(acceptance)

    exact_head = _git_head(root)
    assert doctor["ready"] is True
    assert doctor["source_sha"] == exact_head
    assert acceptance["source_sha"] == exact_head
    assert acceptance["status"] == "PASS"
    assert acceptance["fixture_sha256"] == EXPECTED_FIXTURE_SHA256
    assert acceptance["cleanup_passed"] is True
    assert acceptance["vision_status"] in {"ready", "unavailable"}

    for tool_key in ("ffmpeg", "stt"):
        assert doctor[tool_key]["status"] == "ready"
        assert _SHA64.fullmatch(doctor[tool_key]["executable_sha256"])
        assert doctor[tool_key]["version"]
    assert doctor["stt_model"]["status"] == "ready"
    assert _SHA64.fullmatch(doctor["stt_model"]["sha256"])

    transcript_text = " ".join(
        segment["text"] for segment in acceptance["transcript_segments"]
    )
    assert _fixture_transcript_matches_expected(transcript_text)
    assert acceptance["transcript_segments"]
    assert len(acceptance["frames"]) == 3
    assert len({frame["sha256"] for frame in acceptance["frames"]}) == 3
    assert all(check["passed"] is True for check in acceptance["checks"])
    assert acceptance["resources"]["input_bytes"] > 0
    assert acceptance["resources"]["temporary_peak_bytes"] > 0
