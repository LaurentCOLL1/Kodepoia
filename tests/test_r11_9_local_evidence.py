from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/roadmap/R11_9_LOCAL_ACCEPTANCE.json"
SCHEMA = ROOT / "schemas/r11/r11-9-local-acceptance.schema.json"
EXPECTED_SOURCE_SHA = "087eae19ea03dd544d75a08c1eb348fe187624c5"
EXPECTED_EVIDENCE_DIGEST = "6afe45e3c9047cfa58b7c617ff671e34e166bd9189a32ea62f1350243955b6f5"


def _semantic_digest(document: dict[str, object]) -> str:
    payload = dict(document)
    payload.pop("evidence_digest", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def test_r11_9_accepted_local_evidence_is_schema_valid_and_digest_bound() -> None:
    document = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(document)

    assert document["source_sha"] == EXPECTED_SOURCE_SHA
    assert document["status"] == "pass"
    assert document["blockers"] == []
    assert document["error_type"] is None
    assert document["evidence_digest"] == EXPECTED_EVIDENCE_DIGEST
    assert _semantic_digest(document) == EXPECTED_EVIDENCE_DIGEST

    runtime = document["runtime"]
    assert runtime["platform"] == "Windows"
    assert runtime["godot_compatible_47"] is True
    assert str(runtime["godot_version"]).startswith("4.7.2")
    assert len(runtime["godot_sha256"]) == 64
    assert len(runtime["ffprobe"]["sha256"]) == 64

    capture = document["capture"]
    assert capture["status"] == "pass"
    assert capture["width"] == 640
    assert capture["height"] == 360
    assert capture["fps"] == 30
    assert capture["expected_frames"] == 90
    assert capture["reported_frames"] == 90
    assert capture["video_duration_seconds"] == 3.0
    assert capture["audio_duration_seconds"] == 3.0
    assert capture["av_sync_error_seconds"] == 0.0
    assert capture["av_sync_error_seconds"] <= capture["av_sync_limit_seconds"]
    assert capture["output_bytes"] > 0
    assert len(capture["output_sha256"]) == 64

    assert document["assembly"]["command_policy_id"] == "r11.9.godot.capture.v1"
    assert document["fixture"]["kind"] == "repository_synthetic"
    assert set(document["fixture"]["file_sha256"]) == {
        "assembly.json",
        "capture.gd",
        "capture.tscn",
        "project.godot",
        "tone.wav",
    }
