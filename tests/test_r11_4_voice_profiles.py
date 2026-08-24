from __future__ import annotations

import dataclasses

import pytest

from kodepoia.media.contracts import MediaState
from kodepoia.media.voice import (
    AllowedUse,
    PronunciationEntry,
    PronunciationLexicon,
    ProsodyIntent,
    RightsDeclaration,
    SpeechSegment,
    SpeechSegmentKind,
    VoiceModelBinding,
    VoiceProfile,
    normalize_locale,
    normalize_voice_text,
)

_SHA_A = "a" * 64
_SHA_B = "b" * 64


def test_locale_normalization_profile_digest_and_fallbacks_are_deterministic() -> None:
    assert normalize_locale("fr_fr") == "fr-FR"
    assert normalize_locale("en-latn-us") == "en-Latn-US"
    profile = VoiceProfile(
        profile_id="voice.hero",
        scope_id="character.hero",
        locale="fr_fr",
        fallback_locales=("en_us", "fr-FR", "en-US"),
        prosody=ProsodyIntent(pace=1.05, pitch_semitones=-1.5, energy=0.9, styles=("warm", "calm", "warm")),
        display_name="He\u0301roïne",
    )
    assert profile.locale_candidates() == ("fr-FR", "en-US")
    assert profile.canonical()["display_name"] == "Héroïne"
    assert len(profile.digest()) == 64
    assert profile.digest() == profile.digest()


def test_voice_text_uses_nfc_and_rejects_controls_and_bidi_overrides() -> None:
    assert normalize_voice_text("Cafe\u0301") == "Café"
    with pytest.raises(ValueError):
        normalize_voice_text("hello\x00world")
    with pytest.raises(ValueError):
        normalize_voice_text("safe\u202eevil")


def test_pronunciation_lexicon_is_locale_aware_and_uses_profile_fallback_order() -> None:
    lexicon = PronunciationLexicon(
        lexicon_id="lex.main",
        entries=(
            PronunciationEntry("entry.en", "en-US", "Kodepoia", "koʊdˈpoʊiə"),
            PronunciationEntry("entry.fr", "fr-FR", "Kodepoia", "kɔdepɔja"),
        ),
    )
    profile = VoiceProfile("voice.hero", "character.hero", "fr-FR", ("en-US",))
    hit = lexicon.resolve("Kodepoia", profile.locale_candidates())
    assert hit is not None
    assert hit.entry_id == "entry.fr"
    assert len(lexicon.digest()) == 64


def test_duplicate_pronunciation_key_fails_closed() -> None:
    with pytest.raises(ValueError):
        PronunciationLexicon(
            "lex.bad",
            (
                PronunciationEntry("entry.one", "fr-FR", "Test", "tɛst"),
                PronunciationEntry("entry.two", "fr_fr", "test", "test"),
            ),
        )


def test_rights_declaration_requires_metadata_authorization_and_explicit_use() -> None:
    with pytest.raises(ValueError):
        RightsDeclaration(
            provenance_id="prov.synthetic",
            license_id="cc-by-4.0",
            allowed_uses=(AllowedUse.COMMERCIAL,),
            requires_authorization=True,
        )
    rights = RightsDeclaration(
        provenance_id="prov.synthetic",
        license_id="cc-by-4.0",
        allowed_uses=(AllowedUse.INTERNAL, AllowedUse.COMMERCIAL),
        source_uri_id="source.model-card",
        authorization_ref="auth.voice-package",
        requires_authorization=True,
    )
    assert rights.permits(AllowedUse.COMMERCIAL)
    assert not rights.permits(AllowedUse.REDISTRIBUTION)


def test_rights_blocked_binding_cannot_be_promoted_for_synthesis_use() -> None:
    binding = VoiceModelBinding(
        binding_id="binding.fr.demo",
        backend_id="piper-compatible",
        model_sha256=_SHA_A,
        config_sha256=_SHA_B,
        locale="fr_FR",
        rights=RightsDeclaration(
            provenance_id="prov.demo",
            license_id="restricted",
            allowed_uses=(AllowedUse.INTERNAL,),
            state=MediaState.RIGHTS_BLOCKED,
        ),
    )
    assert binding.state is MediaState.RIGHTS_BLOCKED
    with pytest.raises(PermissionError):
        binding.require_use(AllowedUse.INTERNAL)


def test_model_binding_is_engine_neutral_and_contains_no_path_or_clone_surface() -> None:
    binding = VoiceModelBinding(
        binding_id="binding.fr.demo",
        backend_id="piper-compatible",
        model_sha256=_SHA_A,
        config_sha256=_SHA_B,
        locale="fr-FR",
        rights=RightsDeclaration(
            provenance_id="prov.demo",
            license_id="cc-by-4.0",
            allowed_uses=(AllowedUse.INTERNAL,),
        ),
        speaker_id="speaker.0",
    )
    fields = {field.name for field in dataclasses.fields(binding)}
    assert "path" not in fields
    assert "reference_audio" not in fields
    assert "clone" not in fields
    assert binding.canonical()["locale"] == "fr-FR"
    assert len(binding.digest()) == 64


def test_typed_markup_accepts_only_bounded_segments_and_rejects_raw_ssml() -> None:
    assert SpeechSegment(SpeechSegmentKind.PAUSE, pause_seconds=0.25).canonical()["pause_seconds"] == 0.25
    assert SpeechSegment(SpeechSegmentKind.EMPHASIS, text="Bonjour", emphasis="strong").text == "Bonjour"
    with pytest.raises(ValueError):
        SpeechSegment(SpeechSegmentKind.TEXT, text="<speak>Hello</speak>")
    with pytest.raises(ValueError):
        SpeechSegment(SpeechSegmentKind.PAUSE, pause_seconds=6.0)


def test_invalid_locale_and_nonfinite_prosody_fail_closed() -> None:
    with pytest.raises(ValueError):
        normalize_locale("x")
    with pytest.raises(ValueError):
        ProsodyIntent(pace=float("nan"))
