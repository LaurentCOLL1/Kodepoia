# R11.5 — Acceptance

Status: **CANDIDATE — HOSTED GATES PENDING / MANUAL REQUIRED**

Manual intervention: **REQUIRED**.

## Hosted acceptance requirements

- focused `tests/test_r11_5_tts.py` and `tests/test_r11_5_tts_adapters.py` PASS;
- backend registry returns `UNAVAILABLE` for absent adapters rather than failing the phase;
- Godot/system TTS remains accessibility/runtime-only and non-canonical for production assets;
- Piper capability probe is bounded and requires fixed CLI markers;
- synthesis text is supplied only via an ephemeral staging `--input-file`, never directly in argv;
- exact `<model>.onnx.json` sibling/config identity is hash-bound to the R11.4 binding;
- no network/model download/cloud/voice-cloning/training/arbitrary-engine-flag surface exists;
- timeout/cancel/non-zero/stale-output/malformed-WAV cases fail closed;
- output passes R11.2 WAV/PCM QA before accepted manifest status;
- cache records resolve only for exact request/runtime/model/config identities and reference R8 revision identity rather than owning physical bytes;
- synthesis manifest/cache/local-evidence JSON schemas validate;
- full Python Core PASS Ubuntu/Windows;
- R0 Repository Guard PASS;
- KodeStudio UI Smoke PASS.

## Required real local acceptance

The real-runtime checkpoint must run only after one implementation candidate SHA has passed the hosted gates above. The exact SHA and copy-paste command will then be frozen in this document/PR before the user executes it.

Prerequisites:

1. existing local `piper` or `piper.exe`; the collector never downloads or installs it;
2. one user-reviewed/licensed voice `.onnx` and its exact `<model>.onnx.json` sibling;
3. explicit locale, stable provenance id and reviewed license id;
4. no private reference recording and no voice cloning;
5. network is not required by the collector.

The collector is `scripts/r11_5_accept_local.py`. It synthesizes only neutral repository-owned acceptance text, uses temporary staging, deletes the temporary text/WAV, and emits a privacy-minimized JSON evidence file.

Expected PASS evidence:

- `schema = kodepoia.r11_5_local_acceptance`;
- `source_sha` exactly matches the frozen implementation candidate;
- `status = pass` and `blockers = []`;
- capability status PASS;
- synthesis status PASS;
- R11.2 audio QA state PASS;
- duration greater than 0.05 seconds;
- runtime/model/config/input/output identities are SHA-bound;
- `private_recording_used = false`;
- `voice_clone_used = false`;
- `network_download_performed_by_collector = false`;
- `audio_retained = false`.

If Piper/model/config is missing, the voice license is unclear, a network request is required, the config is not the exact sibling, synthesis fails, or evidence has blockers, **STOP** and return the error/evidence instead of improvising.

## Completion rule

R11.5 cannot merge from hosted CI alone. After the required local JSON is returned and validated against the frozen candidate, acceptance documentation/evidence is updated, that final documentation head is re-gated with R0 + full Python Core + UI Smoke, and only then may the exact accepted PR head merge. A continuity-only normalization must then pass and merge before R11.6 is authorized.
