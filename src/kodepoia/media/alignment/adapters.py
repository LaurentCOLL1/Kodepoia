from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .contracts import AlignmentSource, SpeechAlignmentTimeline, TimedPhoneme, TimedWord


class AlignmentProtocolError(ValueError):
    pass


def _number(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AlignmentProtocolError(f"{field} must be numeric")
    return float(value)


def _confidence(value: object, *, field: str) -> float | None:
    if value is None:
        return None
    return _number(value, field=field)


def normalize_backend_timing(
    document: Mapping[str, Any],
    *,
    timeline_id: str,
    audio_sha256: str,
    locale: str,
    duration_seconds: float,
    source_id: str,
) -> SpeechAlignmentTimeline:
    """Normalize one trusted-adapter timing document into durable R11 semantics.

    This parser deliberately accepts only a tiny Kodepoia-owned interchange shape. It
    does not execute or trust backend-specific command/token streams.
    """

    if set(document) != {"words", "phonemes"}:
        raise AlignmentProtocolError("backend timing document must contain exactly words and phonemes")
    raw_words = document["words"]
    raw_phonemes = document["phonemes"]
    if not isinstance(raw_words, list) or not isinstance(raw_phonemes, list):
        raise AlignmentProtocolError("words and phonemes must be arrays")
    if len(raw_words) > 4096 or len(raw_phonemes) > 16384:
        raise AlignmentProtocolError("backend timing event budget exceeded")

    words: list[TimedWord] = []
    for index, raw in enumerate(raw_words):
        if not isinstance(raw, dict) or set(raw) != {"text", "start", "end", "confidence"}:
            raise AlignmentProtocolError(f"word {index} has unexpected shape")
        words.append(
            TimedWord(
                text=raw["text"],
                start_seconds=_number(raw["start"], field=f"word[{index}].start"),
                end_seconds=_number(raw["end"], field=f"word[{index}].end"),
                confidence=_confidence(raw["confidence"], field=f"word[{index}].confidence"),
            )
        )

    phonemes: list[TimedPhoneme] = []
    for index, raw in enumerate(raw_phonemes):
        if not isinstance(raw, dict) or set(raw) != {"phoneme", "start", "end", "confidence", "word_index"}:
            raise AlignmentProtocolError(f"phoneme {index} has unexpected shape")
        word_index = raw["word_index"]
        if word_index is not None and (isinstance(word_index, bool) or not isinstance(word_index, int)):
            raise AlignmentProtocolError(f"phoneme[{index}].word_index must be integer or null")
        phonemes.append(
            TimedPhoneme(
                phoneme=raw["phoneme"],
                start_seconds=_number(raw["start"], field=f"phoneme[{index}].start"),
                end_seconds=_number(raw["end"], field=f"phoneme[{index}].end"),
                confidence=_confidence(raw["confidence"], field=f"phoneme[{index}].confidence"),
                word_index=word_index,
            )
        )

    return SpeechAlignmentTimeline(
        timeline_id=timeline_id,
        audio_sha256=audio_sha256,
        locale=locale,
        duration_seconds=duration_seconds,
        source=AlignmentSource.BACKEND,
        source_id=source_id,
        words=tuple(words),
        phonemes=tuple(phonemes),
    )


def make_synthetic_alignment(
    *,
    timeline_id: str,
    audio_sha256: str,
    locale: str,
    duration_seconds: float,
    phonemes: Sequence[str],
    source_id: str = "synthetic.fixture.v1",
) -> SpeechAlignmentTimeline:
    """Deterministic CI/preview fixture; never presented as measured speech alignment."""

    if not phonemes or len(phonemes) > 4096:
        raise ValueError("synthetic phoneme sequence must contain 1..4096 entries")
    step = duration_seconds / len(phonemes)
    events = tuple(
        TimedPhoneme(
            phoneme=phoneme,
            start_seconds=index * step,
            end_seconds=(index + 1) * step,
            confidence=None,
            word_index=None,
        )
        for index, phoneme in enumerate(phonemes)
    )
    return SpeechAlignmentTimeline(
        timeline_id=timeline_id,
        audio_sha256=audio_sha256,
        locale=locale,
        duration_seconds=duration_seconds,
        source=AlignmentSource.SYNTHETIC,
        source_id=source_id,
        phonemes=events,
    )
