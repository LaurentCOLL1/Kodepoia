"""R11.6 speech alignment, viseme timelines and lip-sync QA."""

from .adapters import AlignmentProtocolError, make_synthetic_alignment, normalize_backend_timing
from .captions import CaptionCue, CaptionTimingBridge, captions_from_alignment
from .contracts import AlignmentSource, SpeechAlignmentTimeline, TimedPhoneme, TimedWord
from .qa import LipSyncQAProfile, LipSyncQAReport, evaluate_lipsync
from .visemes import PhonemeVisemeEntry, VisemeEvent, VisemeSet, VisemeTimeline, build_viseme_timeline, default_viseme_set

__all__ = [
    "AlignmentProtocolError",
    "AlignmentSource",
    "CaptionCue",
    "CaptionTimingBridge",
    "LipSyncQAProfile",
    "LipSyncQAReport",
    "PhonemeVisemeEntry",
    "SpeechAlignmentTimeline",
    "TimedPhoneme",
    "TimedWord",
    "VisemeEvent",
    "VisemeSet",
    "VisemeTimeline",
    "build_viseme_timeline",
    "captions_from_alignment",
    "default_viseme_set",
    "evaluate_lipsync",
    "make_synthetic_alignment",
    "normalize_backend_timing",
]
