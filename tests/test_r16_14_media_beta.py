from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from kodepoia.media.r16_14_acceptance import (
    FIXTURE_RELATIVE,
    MediaBetaGovernanceError,
    build_media_beta_report,
    qualify_human_listening,
    validate_fixture_payload,
)
from kodepoia.media.serialization import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]


def _fixture() -> dict[str, object]:
    return json.loads((ROOT / FIXTURE_RELATIVE).read_text(encoding="utf-8"))


def test_r16_14_fixture_digest_is_line_ending_independent() -> None:
    raw = (ROOT / FIXTURE_RELATIVE).read_bytes()
    payload_lf = json.loads(raw.decode("utf-8"))
    payload_crlf = json.loads(raw.replace(b"\n", b"\r\n").decode("utf-8"))
    assert canonical_sha256(payload_lf) == canonical_sha256(payload_crlf)


def test_r16_14_fixture_is_deterministic_and_bounded() -> None:
    payload = _fixture()
    validated = validate_fixture_payload(payload)
    assert validated["name"] == "r16.14-representative-audio-voice-cinematic-beta"
    assert validated["audio"]["sample_rate_hz"] == 16000
    assert validated["audio"]["duration_ms"] == 1000
    assert validated["budgets"]["max_output_bytes"] == 1024 * 1024


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("output_relative", "../../escape.wav", "must not escape"),
        ("external_reference", "https://example.invalid/model", "external media references"),
    ],
)
def test_r16_14_fixture_rejects_path_and_external_reference(field: str, value: str, match: str) -> None:
    payload = copy.deepcopy(_fixture())
    payload[field] = value
    with pytest.raises(MediaBetaGovernanceError, match=match):
        validate_fixture_payload(payload)


def test_r16_14_human_listening_is_never_inferred() -> None:
    core = qualify_human_listening(requested=False)
    requested = qualify_human_listening(requested=True)
    assert core["state"] == "NOT_EXERCISED"
    assert core["claim_satisfied"] is False
    assert requested["state"] == "MANUAL_REQUIRED"
    assert requested["manual_required"] is True
    assert requested["claim_satisfied"] is False


def test_r16_14_full_representative_media_report() -> None:
    report = build_media_beta_report(ROOT, source_sha="1" * 40, platform="synthetic-test")
    failed = [item for item in report["cases"] if not item["pass"]]
    assert report["security_claim"] is True, failed
    assert report["critical_veto"] is False
    assert report["manual_state"] == "CONDITIONAL_NOT_TRIGGERED"
    assert report["core_manual_required"] is False
    assert report["external_network_calls"] == 0
    assert report["fixture_is_synthetic_audio"] is True
    assert report["fixture_is_real_tts_runtime"] is False
    assert report["fixture_is_human_listened"] is False
    assert report["human_listening_qualification"]["state"] == "NOT_EXERCISED"
    assert report["summary"] == {"total": 16, "passed": 16, "failed": 0}
    assert report["secret_free"] is True
    assert report["audio_facts"]["channels"] == 1
    assert report["audio_facts"]["sample_rate_hz"] == 16000
    assert report["audio_qa"]["state"] == "PASS"
    for key in (
        "fixture_sha256",
        "text_sha256",
        "profile_sha256",
        "voice_binding_sha256",
        "tts_request_sha256",
        "audio_sha256",
        "alignment_sha256",
        "viseme_sha256",
        "cinematic_sha256",
        "binding_sha256",
        "semantic_sha256",
        "evidence_sha256",
    ):
        assert len(report[key]) == 64
