from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validate

from kodepoia.media.alignment import (
    AlignmentProtocolError,
    CaptionTimingBridge,
    LipSyncQAProfile,
    PhonemeVisemeEntry,
    SpeechAlignmentTimeline,
    TimedPhoneme,
    TimedWord,
    VisemeSet,
    build_viseme_timeline,
    captions_from_alignment,
    default_viseme_set,
    evaluate_lipsync,
    make_synthetic_alignment,
    normalize_backend_timing,
)
from kodepoia.media.contracts import MediaState


AUDIO_SHA = "a" * 64


def _alignment() -> SpeechAlignmentTimeline:
    document = {
        "words": [
            {"text": "Kodepoia", "start": 0.0, "end": 0.8, "confidence": 0.97},
            {"text": "parle", "start": 0.8, "end": 1.6, "confidence": 0.95},
        ],
        "phonemes": [
            {"phoneme": "k", "start": 0.0, "end": 0.25, "confidence": 0.9, "word_index": 0},
            {"phoneme": "o", "start": 0.25, "end": 0.55, "confidence": 0.9, "word_index": 0},
            {"phoneme": "d", "start": 0.55, "end": 0.8, "confidence": 0.9, "word_index": 0},
            {"phoneme": "p", "start": 0.8, "end": 1.0, "confidence": 0.9, "word_index": 1},
            {"phoneme": "a", "start": 1.0, "end": 1.3, "confidence": 0.9, "word_index": 1},
            {"phoneme": "l", "start": 1.3, "end": 1.6, "confidence": 0.9, "word_index": 1},
        ],
    }
    return normalize_backend_timing(
        document,
        timeline_id="alignment.fixture.v1",
        audio_sha256=AUDIO_SHA,
        locale="fr-FR",
        duration_seconds=1.6,
        source_id="backend.fixture.v1",
    )


def test_backend_normalization_is_deterministic_and_strict() -> None:
    first = _alignment()
    second = _alignment()
    assert first.digest() == second.digest()
    assert first.words[0].text == "Kodepoia"
    bad = {"words": [], "phonemes": [], "extra": []}
    with pytest.raises(AlignmentProtocolError):
        normalize_backend_timing(bad, timeline_id="x", audio_sha256=AUDIO_SHA, locale="fr-FR", duration_seconds=1.0, source_id="backend.x")


def test_negative_non_monotonic_and_out_of_duration_timings_fail_closed() -> None:
    with pytest.raises(ValueError):
        TimedPhoneme("a", -0.1, 0.2)
    with pytest.raises(ValueError, match="monotonic"):
        SpeechAlignmentTimeline(
            "alignment.bad",
            AUDIO_SHA,
            "fr-FR",
            1.0,
            __import__("kodepoia.media.alignment", fromlist=["AlignmentSource"]).AlignmentSource.IMPORTED,
            "import.bad",
            phonemes=(TimedPhoneme("a", 0.5, 0.8), TimedPhoneme("b", 0.2, 0.9)),
        )
    with pytest.raises(ValueError, match="exceeds"):
        SpeechAlignmentTimeline(
            "alignment.long",
            AUDIO_SHA,
            "fr-FR",
            1.0,
            __import__("kodepoia.media.alignment", fromlist=["AlignmentSource"]).AlignmentSource.IMPORTED,
            "import.long",
            phonemes=(TimedPhoneme("a", 0.8, 1.1),),
        )


def test_synthetic_fixture_is_explicit_and_deterministic() -> None:
    one = make_synthetic_alignment(timeline_id="alignment.synthetic", audio_sha256=AUDIO_SHA, locale="fr-FR", duration_seconds=1.0, phonemes=("m", "a", "p"))
    two = make_synthetic_alignment(timeline_id="alignment.synthetic", audio_sha256=AUDIO_SHA, locale="fr-FR", duration_seconds=1.0, phonemes=("m", "a", "p"))
    assert one.source.value == "synthetic"
    assert one.digest() == two.digest()
    assert one.phonemes[-1].end_seconds == pytest.approx(1.0)


def test_versioned_viseme_mapping_and_explicit_fallback() -> None:
    mapping = default_viseme_set()
    assert mapping.lookup("P") == ("viseme.mbp", False)
    assert mapping.lookup("not-known") == ("viseme.fallback", True)
    with pytest.raises(ValueError, match="duplicate"):
        VisemeSet("viseme.bad", (PhonemeVisemeEntry("a", "viseme.a"), PhonemeVisemeEntry("A", "viseme.e")), "viseme.fallback", "viseme.rest")


def test_viseme_timeline_is_identity_bound_and_coarticulation_bounded() -> None:
    alignment = _alignment()
    mapping = default_viseme_set()
    timeline = build_viseme_timeline(alignment, mapping, timeline_id="viseme.fixture.v1")
    assert timeline.alignment_digest == alignment.digest()
    assert timeline.viseme_set_digest == mapping.digest()
    assert timeline.events[0].influence_start_seconds == 0.0
    assert timeline.events[-1].influence_end_seconds <= alignment.duration_seconds
    with pytest.raises(ValueError):
        build_viseme_timeline(alignment, mapping, timeline_id="viseme.bad", attack_seconds=0.5)


def test_lipsync_qa_passes_good_timeline_and_reports_metrics() -> None:
    alignment = _alignment()
    timeline = build_viseme_timeline(alignment, default_viseme_set(), timeline_id="viseme.fixture.qa")
    report = evaluate_lipsync(alignment, timeline, accepted_audio_duration_seconds=1.6)
    assert report.state is MediaState.PASS
    assert report.blockers == ()
    assert report.metrics["event_count"] == 6
    assert report.metrics["duration_drift_seconds"] == pytest.approx(0.0)


def test_lipsync_qa_blocks_duration_drift_density_and_excess_fallback() -> None:
    alignment = _alignment()
    timeline = build_viseme_timeline(alignment, default_viseme_set(), timeline_id="viseme.fixture.block")
    drift = evaluate_lipsync(alignment, timeline, accepted_audio_duration_seconds=1.0)
    assert "duration_drift" in drift.blockers
    dense = evaluate_lipsync(alignment, timeline, accepted_audio_duration_seconds=1.6, profile=LipSyncQAProfile(max_events_per_second=1.0))
    assert dense.state is MediaState.BUDGET_EXCEEDED
    unknown = make_synthetic_alignment(timeline_id="alignment.unknown", audio_sha256=AUDIO_SHA, locale="fr-FR", duration_seconds=1.0, phonemes=("x-unknown", "y-unknown"))
    unknown_timeline = build_viseme_timeline(unknown, default_viseme_set(), timeline_id="viseme.unknown")
    report = evaluate_lipsync(unknown, unknown_timeline, accepted_audio_duration_seconds=1.0)
    assert "phoneme_fallback_ratio" in report.blockers


def test_low_reported_confidence_is_warning_not_silent_rejection() -> None:
    alignment = SpeechAlignmentTimeline(
        "alignment.low-confidence",
        AUDIO_SHA,
        "fr-FR",
        0.5,
        __import__("kodepoia.media.alignment", fromlist=["AlignmentSource"]).AlignmentSource.BACKEND,
        "backend.low",
        phonemes=(TimedPhoneme("a", 0.0, 0.5, confidence=0.1),),
    )
    timeline = build_viseme_timeline(alignment, default_viseme_set(), timeline_id="viseme.low-confidence")
    report = evaluate_lipsync(alignment, timeline, accepted_audio_duration_seconds=0.5)
    assert report.state is MediaState.WARN
    assert "low_alignment_confidence" in report.warnings


def test_caption_bridge_is_separate_and_never_phoneme_authority() -> None:
    alignment = _alignment()
    bridge = captions_from_alignment(alignment, bridge_id="captions.fixture")
    assert bridge.phoneme_authority is False
    assert [cue.text for cue in bridge.cues] == ["Kodepoia", "parle"]
    with pytest.raises(ValueError, match="never"):
        CaptionTimingBridge("captions.bad", alignment.digest(), AUDIO_SHA, "fr-FR", (), phoneme_authority=True)


def test_alignment_viseme_qa_and_caption_schemas_accept_canonical_objects() -> None:
    alignment = _alignment()
    visemes = build_viseme_timeline(alignment, default_viseme_set(), timeline_id="viseme.schema")
    qa = evaluate_lipsync(alignment, visemes, accepted_audio_duration_seconds=1.6)
    captions = captions_from_alignment(alignment, bridge_id="captions.schema")
    fixtures = (
        ("schemas/r11/speech-alignment.schema.json", alignment.canonical()),
        ("schemas/r11/viseme-timeline.schema.json", visemes.canonical()),
        ("schemas/r11/lipsync-qa.schema.json", qa.canonical()),
        ("schemas/r11/caption-timing-bridge.schema.json", captions.canonical()),
    )
    for schema_path, payload in fixtures:
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
        validate(instance=payload, schema=schema)
