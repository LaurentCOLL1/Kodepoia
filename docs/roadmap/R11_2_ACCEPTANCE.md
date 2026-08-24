# R11.2 — Acceptance

Status: CANDIDATE

Manual intervention: **CONDITIONAL — NOT TRIGGERED for the hosted acceptance scope**.

The accepted scope does not assert execution of a real FFmpeg/ffprobe binary. It validates deterministic WAV/PCM inspection, strict parsing of representative ffprobe JSON, typed transform recipes and deterministic QA. Therefore no user-side runtime execution is required unless a later candidate introduces a claim that depends on actual FFmpeg codec/transcode behavior.

Acceptance requires:
- focused `tests/test_r11_2_audio_pipeline.py` PASS;
- full Python Core PASS Ubuntu/Windows;
- R0 Repository Guard PASS;
- KodeStudio UI Smoke PASS;
- R11.1 remains complete/normalized and prior evidence retained;
- final documentation head re-gated before merge;
- post-merge continuity-only normalization before R11.3.
