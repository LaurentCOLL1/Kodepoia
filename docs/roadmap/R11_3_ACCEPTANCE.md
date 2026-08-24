# R11.3 — Acceptance

Status: CANDIDATE

Manual intervention: **NONE**.

Acceptance requires:
- deterministic cue canonicalization/digest and variant test vectors;
- invalid QA/rights R8 references fail closed;
- loop/spatialization/bus/polyphony/cooldown/ducking bounds tested;
- Godot packaging output is semantic intent only, without raw `.tres`/script/path injection;
- focused `tests/test_r11_3_audio_cues.py` PASS;
- full Python Core PASS Ubuntu/Windows;
- R0 Repository Guard PASS;
- KodeStudio UI Smoke PASS;
- final documentation head re-gated before merge;
- continuity-only normalization after merge before R11.4.
