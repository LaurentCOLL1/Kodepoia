from __future__ import annotations

import pytest

from kodepoia.media import MediaState
from kodepoia.media.cues import AttenuationProfile, AudioCueDefinition, CueCategory, CuePlayback, CueVariant, LoopPolicy, SpatializationIntent, compile_godot_audio_intent, playlist_order, select_variant

A = "a" * 64
B = "b" * 64


def variant(revision: str, digest: str, weight: int = 1) -> CueVariant:
    return CueVariant(revision, digest, weight)


def test_cue_digest_and_selection_are_deterministic() -> None:
    cue = AudioCueDefinition("cue:sfx:step", CueCategory.FOLEY, CuePlayback.WEIGHTED, (variant("asset:r8:step1", A, 1), variant("asset:r8:step2", B, 3)), "sfx")
    assert cue.digest == cue.digest
    assert select_variant(cue, seed="preview", occurrence=7) == select_variant(cue, seed="preview", occurrence=7)


def test_different_occurrences_have_stable_vector() -> None:
    cue = AudioCueDefinition("cue:sfx:hit", CueCategory.SFX, CuePlayback.WEIGHTED, (variant("asset:r8:a", A), variant("asset:r8:b", B)), "sfx")
    vector = [select_variant(cue, seed="fixture", occurrence=i).asset_revision_id for i in range(8)]
    assert vector == [select_variant(cue, seed="fixture", occurrence=i).asset_revision_id for i in range(8)]
    assert set(vector) <= {"asset:r8:a", "asset:r8:b"}


def test_blocked_or_stale_variant_fails_closed() -> None:
    with pytest.raises(ValueError):
        CueVariant("asset:r8:blocked", A, qa_state=MediaState.BLOCKED)
    with pytest.raises(ValueError):
        CueVariant("asset:r8:stale", A, rights_state=MediaState.STALE)


def test_loop_region_and_crossfade_are_bounded() -> None:
    loop = LoopPolicy(True, 1.0, 5.0, crossfade_seconds=1.0)
    cue = AudioCueDefinition("cue:music:theme", CueCategory.MUSIC, CuePlayback.LOOP, (variant("asset:r8:theme", A),), "music", loop=loop)
    assert cue.loop.end_seconds == 5.0
    with pytest.raises(ValueError):
        LoopPolicy(True, 1.0, 2.0, crossfade_seconds=0.6)


def test_loop_playback_policy_must_match() -> None:
    with pytest.raises(ValueError):
        AudioCueDefinition("cue:music:bad", CueCategory.MUSIC, CuePlayback.LOOP, (variant("asset:r8:a", A),), "music")
    with pytest.raises(ValueError):
        AudioCueDefinition("cue:sfx:bad", CueCategory.SFX, CuePlayback.ONE_SHOT, (variant("asset:r8:a", A),), "sfx", loop=LoopPolicy(True, 0.0, 1.0))


def test_spatialization_and_polyphony_budgets() -> None:
    spatial = SpatializationIntent(True, AttenuationProfile.INVERSE, 1.0, 25.0)
    cue = AudioCueDefinition("cue:sfx:world", CueCategory.SFX, CuePlayback.ONE_SHOT, (variant("asset:r8:a", A),), "world_sfx", max_polyphony=16, spatialization=spatial)
    assert cue.spatialization.positional is True
    with pytest.raises(ValueError):
        SpatializationIntent(False, AttenuationProfile.LINEAR)
    with pytest.raises(ValueError):
        AudioCueDefinition("cue:sfx:poly", CueCategory.SFX, CuePlayback.ONE_SHOT, (variant("asset:r8:a", A),), "sfx", max_polyphony=129)


def test_ducking_cannot_target_same_bus() -> None:
    with pytest.raises(ValueError):
        AudioCueDefinition("cue:ui:click", CueCategory.UI, CuePlayback.ONE_SHOT, (variant("asset:r8:a", A),), "ui", duck_bus_id="ui")


def test_playlist_order_is_deterministic() -> None:
    cue = AudioCueDefinition("cue:music:list", CueCategory.MUSIC, CuePlayback.PLAYLIST, (variant("asset:r8:a", A), variant("asset:r8:b", B)), "music")
    first = playlist_order(cue, seed="session")
    assert first == playlist_order(cue, seed="session")
    assert set(first) == set(cue.variants)


def test_runtime_nondeterminism_is_explicit_and_not_previewed_as_deterministic() -> None:
    cue = AudioCueDefinition("cue:ambience:birds", CueCategory.AMBIENCE, CuePlayback.WEIGHTED, (variant("asset:r8:a", A),), "ambience", allow_runtime_nondeterminism=True)
    with pytest.raises(ValueError):
        select_variant(cue, seed="preview")


def test_godot_intent_contains_semantics_not_raw_resource_text() -> None:
    cue = AudioCueDefinition("cue:foley:cloth", CueCategory.FOLEY, CuePlayback.ONE_SHOT, (variant("asset:r8:a", A),), "foley", cooldown_seconds=0.1)
    intent = compile_godot_audio_intent(cue).canonical()
    assert intent["asset_revisions"] == ["asset:r8:a"]
    assert "path" not in intent and "tres" not in intent and "script" not in intent
