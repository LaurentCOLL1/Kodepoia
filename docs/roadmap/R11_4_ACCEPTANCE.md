# R11.4 — Acceptance

Status: ACCEPTED CANDIDATE — FINAL DOCUMENTATION HEAD MUST RE-GATE

Manual intervention: **NONE**.

Accepted implementation head: `a662046c9fd38a198cc76c33b9012774f254407c`.

Authoritative hosted gates on that implementation head:
- R0 Repository Guard #1354 / `32729014444`: **SUCCESS**;
- Python Core #1328 / `32729014573`: **SUCCESS**;
- KodeStudio UI Smoke #1295 / `32729014540`: **SUCCESS**;
- Python Ubuntu: **944 passed / 8 skipped / 46 warnings**;
- Python Windows, internal KodeStudio smoke and package builds Ubuntu/Windows: **SUCCESS**;
- integrated R7/R8/R9 acceptance: **PASS**.

Accepted scope:
- VoiceProfile canonicalization/digest and locale fallback tests PASS;
- Unicode NFC equivalence and bidi/control-character adversarial tests PASS;
- locale-aware pronunciation lookup and duplicate-key fail-closed tests PASS;
- rights/provenance missing/blocked/unauthorized states cannot produce an accepted use;
- VoiceModelBinding remains separate from profile identity and exposes no path/reference-audio/clone field;
- typed speech markup rejects raw XML/SSML-like input and bounds pause/emphasis values;
- JSON schemas accept representative canonical profile/lexicon/binding payloads;
- focused `tests/test_r11_4_voice_profiles.py` is covered by the full green suite.

No real TTS runtime, model, voice recording or personal data is required for R11.4 acceptance. Manual state remains **NONE**.

The documentation update that records this evidence changes the head. The resulting final documentation head MUST pass R0 Repository Guard + full Python Core + KodeStudio UI Smoke before merge. Merge must use that exact accepted head SHA. After merge, exactly one continuity-only normalization is required before R11.5.
