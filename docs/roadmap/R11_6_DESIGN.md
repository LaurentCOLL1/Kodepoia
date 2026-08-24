# R11.6 — Speech alignment, phoneme/viseme timeline + lip-sync QA

## Status

Implementation candidate. Manual intervention is **CONDITIONAL** and is currently **NOT TRIGGERED**.

## Scope

R11.6 turns already synthesized/approved speech timing into deterministic engine-neutral alignment and viseme artifacts without claiming backend-specific alignment accuracy.

Delivered semantics:

- `SpeechAlignmentTimeline` with audio SHA-256, locale, duration, source/source-id, timed words and timed phonemes;
- strict bounded adapter for Kodepoia-owned backend timing interchange;
- deterministic synthetic alignment fixtures explicitly marked `synthetic` for CI/preview only;
- versioned `VisemeSet` with explicit unknown-phoneme fallback;
- deterministic `VisemeTimeline` with attack/release coarticulation windows;
- lip-sync QA for event budget/density, influence overlap, duration drift, fallback ratio and reported confidence;
- `CaptionTimingBridge` linked to alignment/audio identity while explicitly forbidden from becoming phoneme authority;
- versioned JSON schemas and adversarial tests.

## Timing authority and trust boundary

R11.6 never executes a forced aligner and never treats provider-specific token streams as durable semantics. External/native alignment may be added later through a governed adapter, but durable state is always normalized into the R11 contracts first.

The bounded backend interchange accepts exactly `words` and `phonemes` arrays. Negative, non-finite, non-monotonic, out-of-duration, over-budget or malformed events fail closed. Confidence is optional but, when present, is constrained to `[0,1]`.

`source=synthetic` is an explicit evidence semantic. Synthetic timing is useful for deterministic tests and previews but cannot be represented as measured backend timing.

## Viseme semantics

`VisemeSet` is versioned and digest-bound. Phoneme keys are exact normalized symbols under a given mapping set; unknown symbols map to an explicit fallback viseme and set `fallback_used=true` rather than being silently guessed.

R11.6 provides `viseme.kdp.v1` as a small neutral default grouping suitable for deterministic pipeline tests. It is not a facial rig mapping and does not name R10 blend shapes/bones. R11.7 remains authoritative for mapping semantic visemes to validated R10 targets.

Coarticulation is deterministic. Each phoneme peak interval may receive bounded attack/release influence windows, clamped to the accepted audio duration. Attack/release are capped at 250 ms and the default is 25/35 ms.

## Lip-sync QA

`lipsync.default.v1` checks:

- event count and events/second budgets;
- maximum adjacent influence overlap;
- viseme duration drift versus accepted audio duration;
- fraction/count of explicit unknown-phoneme fallbacks;
- low reported alignment confidence as a warning;
- missing phoneme timing as a blocker.

Budget excess produces `BUDGET_EXCEEDED`; semantic invalidity produces `BLOCKED`; non-fatal findings produce `WARN`. QA is identity-bound to both alignment and viseme timeline digests.

## Accessibility/localization bridge

Caption/subtitle timing remains a separate R6-facing text artifact. `CaptionTimingBridge.phoneme_authority` is permanently false. Word timing can seed caption cues, but captions cannot silently redefine pronunciation or phoneme identity.

## External compatibility note

Montreal Forced Aligner 3.x remains a possible future external alignment backend because it supports multilingual forced alignment from audio, orthographic transcription and pronunciation dictionaries. R11.6 does not install, download, execute or require MFA, and therefore makes no real-runtime MFA accuracy claim.

## Manual checkpoint

Frozen R11 plan rule: **CONDITIONAL** — trigger only when accepted production behavior relies on backend/native phoneme timing or an external aligner not reproducible in hosted CI.

This implementation does not make that claim. It tests only Kodepoia-owned normalization/mapping/QA semantics with deterministic fixtures, so manual state is **CONDITIONAL NOT TRIGGERED**.

## Out of scope

- external aligner installation/execution or accuracy benchmarking;
- voice cloning/reference recording;
- facial target/blend-shape/bone mapping (R11.7);
- Godot animation resource generation (R11.7/R11.9);
- free-form Blender/Godot edits;
- subtitles as phoneme authority.
