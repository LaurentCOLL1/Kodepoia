# R11.4 — Acceptance

Status: CANDIDATE

Manual intervention: **NONE**.

Acceptance requires:
- VoiceProfile canonicalization/digest and locale fallback tests PASS;
- Unicode NFC equivalence and bidi/control-character adversarial tests PASS;
- locale-aware pronunciation lookup and duplicate-key fail-closed tests PASS;
- rights/provenance missing/blocked/unauthorized states cannot produce an accepted use;
- VoiceModelBinding remains separate from profile identity and exposes no path/reference-audio/clone field;
- typed speech markup rejects raw XML/SSML-like input and bounds pause/emphasis values;
- JSON schemas accept representative canonical profile/lexicon/binding payloads;
- focused `tests/test_r11_4_voice_profiles.py` PASS;
- full Python Core PASS Ubuntu/Windows;
- R0 Repository Guard PASS;
- KodeStudio UI Smoke PASS;
- final documentation head re-gated before merge;
- post-merge continuity-only normalization before R11.5.

No real TTS runtime, model, voice recording or personal data is required for R11.4 acceptance.
