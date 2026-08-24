from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest
from jsonschema import validate

from kodepoia.media.cinematic.branching import BranchCondition, BranchOperator, evaluate_branch
from kodepoia.media.cinematic.contracts import (
    CinematicRef,
    CinematicTrackKind,
    SequenceEntry,
    SequenceTimeline,
    ShotDefinition,
    TimelineEvent,
)
from kodepoia.media.cinematic.timebase import FrameTime, Timebase
from kodepoia.media.cinematic.validation import CinematicBudget, CinematicValidationStatus, validate_sequence, validate_shot


def _shot(*, shot_id: str = "shot.one", frames: int = 72, timebase: Timebase | None = None) -> ShotDefinition:
    tb = timebase or Timebase(24)
    refs = (
        CinematicRef("camera.main", "camera", "a" * 64),
        CinematicRef("facial.main", "facial_curve_set", "b" * 64),
        CinematicRef("voice.main", "voice_run", "c" * 64),
    )
    events = (
        TimelineEvent("event.camera", CinematicTrackKind.CAMERA, 0, frames, "camera.main", {"camera_id": "camera.main", "fov_deg": 50.0}),
        TimelineEvent("event.face", CinematicTrackKind.FACIAL, 0, frames, "facial.main", {"curve_set_id": "facial.main", "weight": 1.0}),
        TimelineEvent("event.dialogue", CinematicTrackKind.DIALOGUE, 0, frames, "voice.main", {"voice_run_id": "voice.main", "speaker_id": "actor.one"}),
    )
    return ShotDefinition(shot_id, tb, frames, refs, events)


def test_rational_timebase_has_exact_vectors() -> None:
    assert FrameTime(48, Timebase(24)).seconds == Fraction(2, 1)
    assert FrameTime(60, Timebase(30)).seconds == Fraction(2, 1)
    ntsc = Timebase(24_000, 1001)
    assert FrameTime(24_000, ntsc).seconds == Fraction(1001, 1)
    assert Timebase(25).frame_for_seconds(2) == 50
    with pytest.raises(ValueError):
        Timebase(24).frame_for_seconds(1, 10)


def test_shot_is_canonical_and_references_are_digest_bound() -> None:
    a = _shot()
    b = _shot()
    assert a.digest() == b.digest()
    bad = CinematicRef("voice.main", "voice_run", "d" * 64)
    changed = ShotDefinition(a.shot_id, a.timebase, a.duration_frames, (a.refs[0], a.refs[1], bad), a.events)
    assert changed.digest() != a.digest()


def test_event_payload_is_allowlisted_and_code_smuggling_fails() -> None:
    with pytest.raises(ValueError, match="non-allowlisted"):
        TimelineEvent("evil", CinematicTrackKind.EVENT, 0, 1, None, {"script": "OS.execute('x')"})
    with pytest.raises(ValueError):
        TimelineEvent("evil2", CinematicTrackKind.EVENT, 0, 1, None, {"event_kind": "python"})
    with pytest.raises(TypeError):
        TimelineEvent("evil3", CinematicTrackKind.EVENT, 0, 1, None, {"marker_id": ["not", "scalar"]})


def test_missing_ref_and_out_of_duration_fail_at_contract_boundary() -> None:
    shot = _shot()
    with pytest.raises(ValueError, match="unknown identity"):
        ShotDefinition(
            "shot.badref",
            shot.timebase,
            shot.duration_frames,
            shot.refs,
            (TimelineEvent("bad", CinematicTrackKind.FACIAL, 0, 1, "missing.ref", {"curve_set_id": "missing.ref"}),),
        )
    with pytest.raises(ValueError, match="exceeds"):
        ShotDefinition(
            "shot.badtime",
            shot.timebase,
            10,
            shot.refs,
            (TimelineEvent("badtime", CinematicTrackKind.CAMERA, 9, 2, "camera.main", {"camera_id": "camera.main"}),),
        )


def test_sequence_gap_overlap_digest_and_timebase_validation() -> None:
    shot1 = _shot(shot_id="shot.one", frames=24)
    shot2 = _shot(shot_id="shot.two", frames=24)
    sequence = SequenceTimeline(
        "sequence.ok",
        Timebase(24),
        (
            SequenceEntry("entry.one", shot1.shot_id, shot1.digest(), 0, 24),
            SequenceEntry("entry.two", shot2.shot_id, shot2.digest(), 24, 24),
        ),
    )
    report = validate_sequence(sequence, known_shots={shot1.shot_id: shot1, shot2.shot_id: shot2})
    assert report.status is CinematicValidationStatus.PASS
    gap = SequenceTimeline("sequence.gap", Timebase(24), (SequenceEntry("gap", shot1.shot_id, shot1.digest(), 1, 24),))
    assert "sequence_gap" in validate_sequence(gap, known_shots={shot1.shot_id: shot1}).blockers
    overlap = SequenceTimeline(
        "sequence.overlap",
        Timebase(24),
        (
            SequenceEntry("ov1", shot1.shot_id, shot1.digest(), 0, 24),
            SequenceEntry("ov2", shot2.shot_id, shot2.digest(), 12, 24),
        ),
    )
    assert "sequence_overlap" in validate_sequence(overlap, known_shots={shot1.shot_id: shot1, shot2.shot_id: shot2}).blockers


def test_nested_cycle_and_missing_nested_sequence_are_explicit() -> None:
    shot = _shot(frames=24)
    a = SequenceTimeline("sequence.a", Timebase(24), (SequenceEntry("a.entry", shot.shot_id, shot.digest(), 0, 24),), ("sequence.b",))
    b = SequenceTimeline("sequence.b", Timebase(24), (SequenceEntry("b.entry", shot.shot_id, shot.digest(), 0, 24),), ("sequence.a",))
    report = validate_sequence(a, known_shots={shot.shot_id: shot}, known_sequences={"sequence.a": a, "sequence.b": b})
    assert "nested_sequence_cycle" in report.blockers
    missing = SequenceTimeline("sequence.missing", Timebase(24), (SequenceEntry("m.entry", shot.shot_id, shot.digest(), 0, 24),), ("sequence.unknown",))
    assert "missing_nested_sequence" in validate_sequence(missing, known_shots={shot.shot_id: shot}, known_sequences={}).blockers


def test_branch_evaluation_is_deterministic_and_minimal_context() -> None:
    condition = BranchCondition("branch.relationship", "affinity", BranchOperator.GTE, 50, "shot.warm", "shot.cold")
    assert evaluate_branch(condition, {"affinity": 50}) == "shot.warm"
    assert evaluate_branch(condition, {"affinity": 49}) == "shot.cold"
    with pytest.raises(ValueError):
        evaluate_branch(condition, {"affinity": 50, "hidden": True})
    text = BranchCondition("branch.state", "weather", BranchOperator.EQ, "rain", "shot.rain", "shot.clear")
    assert evaluate_branch(text, {"weather": "rain"}) == "shot.rain"


def test_budget_failures_are_explicit() -> None:
    shot = _shot(frames=100)
    report = validate_shot(shot, budget=CinematicBudget(max_shot_frames=50))
    assert report.status is CinematicValidationStatus.FAIL
    assert "shot_duration_budget_exceeded" in report.blockers


def test_schemas_accept_canonical_examples() -> None:
    shot = _shot(frames=24)
    sequence = SequenceTimeline("sequence.schema", Timebase(24), (SequenceEntry("entry.schema", shot.shot_id, shot.digest(), 0, 24),))
    report = validate_sequence(sequence, known_shots={shot.shot_id: shot})
    fixtures = (
        ("shot-definition.schema.json", shot.canonical()),
        ("sequence-timeline.schema.json", sequence.canonical()),
        ("cinematic-validation.schema.json", report.canonical()),
    )
    for filename, payload in fixtures:
        schema = json.loads(Path("schemas/r11", filename).read_text(encoding="utf-8"))
        validate(instance=payload, schema=schema)
