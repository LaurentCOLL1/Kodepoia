from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

from kodepoia.media.serialization import canonical_sha256

from .contracts import SequenceTimeline, ShotDefinition


class CinematicValidationStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class CinematicBudget:
    max_shot_frames: int = 216_000
    max_sequence_frames: int = 432_000
    max_events_per_shot: int = 8192
    max_refs_per_shot: int = 2048

    def __post_init__(self) -> None:
        for name in ("max_shot_frames", "max_sequence_frames", "max_events_per_shot", "max_refs_per_shot"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class CinematicValidationReport:
    status: CinematicValidationStatus
    subject_digest: str
    blockers: tuple[str, ...]
    facts: Mapping[str, int]

    def canonical(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "subject_digest": self.subject_digest,
            "blockers": list(self.blockers),
            "facts": {key: int(self.facts[key]) for key in sorted(self.facts)},
        }

    def digest(self) -> str:
        return canonical_sha256({"schema": "kodepoia.r11.cinematic_validation", "version": 1, "payload": self.canonical()})


def validate_shot(shot: ShotDefinition, *, budget: CinematicBudget = CinematicBudget()) -> CinematicValidationReport:
    blockers: list[str] = []
    if shot.duration_frames > budget.max_shot_frames:
        blockers.append("shot_duration_budget_exceeded")
    if len(shot.events) > budget.max_events_per_shot:
        blockers.append("event_budget_exceeded")
    if len(shot.refs) > budget.max_refs_per_shot:
        blockers.append("ref_budget_exceeded")
    return CinematicValidationReport(
        status=CinematicValidationStatus.FAIL if blockers else CinematicValidationStatus.PASS,
        subject_digest=shot.digest(),
        blockers=tuple(sorted(set(blockers))),
        facts={"duration_frames": shot.duration_frames, "event_count": len(shot.events), "ref_count": len(shot.refs)},
    )


def validate_sequence(
    sequence: SequenceTimeline,
    *,
    known_shots: Mapping[str, ShotDefinition],
    known_sequences: Mapping[str, SequenceTimeline] | None = None,
    allow_gaps: bool = False,
    budget: CinematicBudget = CinematicBudget(),
) -> CinematicValidationReport:
    blockers: list[str] = []
    previous_end = 0
    for entry in sorted(sequence.entries, key=lambda item: (item.start_frame, item.entry_id)):
        shot = known_shots.get(entry.shot_id)
        if shot is None:
            blockers.append("missing_shot_ref")
        else:
            if entry.shot_digest != shot.digest():
                blockers.append("shot_digest_mismatch")
            if entry.duration_frames != shot.duration_frames:
                blockers.append("shot_duration_mismatch")
            if shot.timebase != sequence.timebase:
                blockers.append("timebase_mismatch")
        if entry.start_frame < previous_end:
            blockers.append("sequence_overlap")
        elif entry.start_frame > previous_end and not allow_gaps:
            blockers.append("sequence_gap")
        previous_end = max(previous_end, entry.end_frame)
    if sequence.duration_frames > budget.max_sequence_frames:
        blockers.append("sequence_duration_budget_exceeded")
    nested = known_sequences or {}
    visited: set[str] = set()
    active: set[str] = set()

    def visit(sequence_id: str) -> None:
        if sequence_id in active:
            blockers.append("nested_sequence_cycle")
            return
        if sequence_id in visited:
            return
        item = nested.get(sequence_id)
        if item is None:
            blockers.append("missing_nested_sequence")
            return
        active.add(sequence_id)
        for child in item.nested_sequence_ids:
            visit(child)
        active.remove(sequence_id)
        visited.add(sequence_id)

    for child in sequence.nested_sequence_ids:
        visit(child)
    return CinematicValidationReport(
        status=CinematicValidationStatus.FAIL if blockers else CinematicValidationStatus.PASS,
        subject_digest=sequence.digest(),
        blockers=tuple(sorted(set(blockers))),
        facts={"duration_frames": sequence.duration_frames, "entry_count": len(sequence.entries), "nested_count": len(sequence.nested_sequence_ids)},
    )
