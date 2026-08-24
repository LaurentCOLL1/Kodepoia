from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

from kodepoia.media.contracts import bounded_text, sha256_hex, stable_id
from kodepoia.media.serialization import canonical_sha256

from .timebase import Timebase


class CinematicTrackKind(StrEnum):
    CAMERA = "camera"
    BODY = "body"
    FACIAL = "facial"
    DIALOGUE = "dialogue"
    MUSIC = "music"
    SFX = "sfx"
    FOLEY = "foley"
    SUBTITLE = "subtitle"
    EVENT = "event"


_ALLOWED_PAYLOAD_KEYS: dict[CinematicTrackKind, frozenset[str]] = {
    CinematicTrackKind.CAMERA: frozenset({"camera_id", "fov_deg"}),
    CinematicTrackKind.BODY: frozenset({"animation_id", "blend"}),
    CinematicTrackKind.FACIAL: frozenset({"curve_set_id", "weight"}),
    CinematicTrackKind.DIALOGUE: frozenset({"voice_run_id", "speaker_id"}),
    CinematicTrackKind.MUSIC: frozenset({"cue_id", "gain_db"}),
    CinematicTrackKind.SFX: frozenset({"cue_id", "gain_db"}),
    CinematicTrackKind.FOLEY: frozenset({"cue_id", "gain_db"}),
    CinematicTrackKind.SUBTITLE: frozenset({"caption_bridge_id", "locale"}),
    CinematicTrackKind.EVENT: frozenset({"marker_id", "event_kind"}),
}


def _payload_value(value: object) -> str | int | float | bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if abs(value) > 1_000_000_000:
            raise ValueError("integer payload is outside bounded range")
        return value
    if isinstance(value, float):
        if not math.isfinite(value) or abs(value) > 1_000_000_000:
            raise ValueError("float payload must be finite and bounded")
        return value
    if isinstance(value, str):
        return bounded_text(value, field="event payload string", maximum=256)
    raise TypeError("event payload values must be bounded primitives")


@dataclass(frozen=True, slots=True)
class CinematicRef:
    ref_id: str
    ref_kind: str
    digest: str

    def __post_init__(self) -> None:
        stable_id(self.ref_id, field="ref_id")
        stable_id(self.ref_kind, field="ref_kind")
        sha256_hex(self.digest, field="digest")

    def canonical(self) -> dict[str, str]:
        return {"ref_id": self.ref_id, "ref_kind": self.ref_kind, "digest": self.digest}


@dataclass(frozen=True, slots=True)
class TimelineEvent:
    event_id: str
    track_kind: CinematicTrackKind
    start_frame: int
    duration_frames: int
    ref_id: str | None
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        stable_id(self.event_id, field="event_id")
        if not isinstance(self.track_kind, CinematicTrackKind):
            raise TypeError("track_kind must be CinematicTrackKind")
        for name, value, allow_zero in (("start_frame", self.start_frame, True), ("duration_frames", self.duration_frames, False)):
            if isinstance(value, bool) or not isinstance(value, int) or value < (0 if allow_zero else 1):
                raise ValueError(f"{name} is invalid")
        if self.ref_id is not None:
            stable_id(self.ref_id, field="ref_id")
        if not isinstance(self.payload, Mapping) or len(self.payload) > 8:
            raise ValueError("event payload must be a bounded mapping")
        keys = set(self.payload)
        if not keys <= _ALLOWED_PAYLOAD_KEYS[self.track_kind]:
            raise ValueError("event payload contains non-allowlisted keys")
        for key, value in self.payload.items():
            bounded_text(key, field="payload key", maximum=64)
            _payload_value(value)
        if self.track_kind is CinematicTrackKind.EVENT:
            kind = self.payload.get("event_kind")
            if kind not in {"marker", "state_tag", None}:
                raise ValueError("event_kind is not allowlisted")

    @property
    def end_frame(self) -> int:
        return self.start_frame + self.duration_frames

    def canonical(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "track_kind": self.track_kind.value,
            "start_frame": self.start_frame,
            "duration_frames": self.duration_frames,
            "ref_id": self.ref_id,
            "payload": {key: _payload_value(self.payload[key]) for key in sorted(self.payload)},
        }


@dataclass(frozen=True, slots=True)
class ShotDefinition:
    shot_id: str
    timebase: Timebase
    duration_frames: int
    refs: tuple[CinematicRef, ...]
    events: tuple[TimelineEvent, ...]

    def __post_init__(self) -> None:
        stable_id(self.shot_id, field="shot_id")
        if not isinstance(self.timebase, Timebase):
            raise TypeError("timebase must be Timebase")
        if isinstance(self.duration_frames, bool) or not isinstance(self.duration_frames, int) or self.duration_frames <= 0:
            raise ValueError("duration_frames must be positive")
        if len(self.refs) > 2048 or len(self.events) > 8192:
            raise ValueError("shot reference/event budget exceeded")
        ref_ids = [ref.ref_id for ref in self.refs]
        if len(ref_ids) != len(set(ref_ids)):
            raise ValueError("duplicate shot ref_id")
        event_ids = [event.event_id for event in self.events]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("duplicate shot event_id")
        known = set(ref_ids)
        previous_start = -1
        for event in self.events:
            if event.start_frame < previous_start:
                raise ValueError("shot events must be globally monotonic")
            if event.end_frame > self.duration_frames:
                raise ValueError("shot event exceeds shot duration")
            if event.ref_id is not None and event.ref_id not in known:
                raise ValueError("shot event references unknown identity")
            previous_start = event.start_frame

    def canonical(self) -> dict[str, Any]:
        return {
            "shot_id": self.shot_id,
            "timebase": self.timebase.canonical(),
            "duration_frames": self.duration_frames,
            "refs": [ref.canonical() for ref in sorted(self.refs, key=lambda item: item.ref_id)],
            "events": [event.canonical() for event in self.events],
        }

    def digest(self) -> str:
        return canonical_sha256({"schema": "kodepoia.r11.shot_definition", "version": 1, "payload": self.canonical()})


@dataclass(frozen=True, slots=True)
class SequenceEntry:
    entry_id: str
    shot_id: str
    shot_digest: str
    start_frame: int
    duration_frames: int

    def __post_init__(self) -> None:
        stable_id(self.entry_id, field="entry_id")
        stable_id(self.shot_id, field="shot_id")
        sha256_hex(self.shot_digest, field="shot_digest")
        if isinstance(self.start_frame, bool) or not isinstance(self.start_frame, int) or self.start_frame < 0:
            raise ValueError("start_frame must be non-negative")
        if isinstance(self.duration_frames, bool) or not isinstance(self.duration_frames, int) or self.duration_frames <= 0:
            raise ValueError("duration_frames must be positive")

    @property
    def end_frame(self) -> int:
        return self.start_frame + self.duration_frames

    def canonical(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "shot_id": self.shot_id,
            "shot_digest": self.shot_digest,
            "start_frame": self.start_frame,
            "duration_frames": self.duration_frames,
        }


@dataclass(frozen=True, slots=True)
class SequenceTimeline:
    sequence_id: str
    timebase: Timebase
    entries: tuple[SequenceEntry, ...]
    nested_sequence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        stable_id(self.sequence_id, field="sequence_id")
        if not isinstance(self.timebase, Timebase):
            raise TypeError("timebase must be Timebase")
        if not self.entries or len(self.entries) > 4096:
            raise ValueError("sequence entries must contain 1..4096 items")
        ids = [entry.entry_id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate sequence entry ids")
        for nested in self.nested_sequence_ids:
            stable_id(nested, field="nested_sequence_id")
        if self.sequence_id in self.nested_sequence_ids:
            raise ValueError("sequence cannot directly nest itself")

    @property
    def duration_frames(self) -> int:
        return max(entry.end_frame for entry in self.entries)

    def canonical(self) -> dict[str, Any]:
        return {
            "sequence_id": self.sequence_id,
            "timebase": self.timebase.canonical(),
            "entries": [entry.canonical() for entry in sorted(self.entries, key=lambda item: (item.start_frame, item.entry_id))],
            "nested_sequence_ids": sorted(self.nested_sequence_ids),
        }

    def digest(self) -> str:
        return canonical_sha256({"schema": "kodepoia.r11.sequence_timeline", "version": 1, "payload": self.canonical()})
