# R11.2 — Audio ingest/transcode/analysis + deterministic QA

## Design

R11.2 adds deterministic audio inspection and QA without expanding the process trust surface.

- WAV acceptance uses Python's standard RIFF/WAVE parser with explicit byte, duration, channel, sample-rate, compression and PCM-payload bounds.
- Optional ffprobe integration is represented by a strict parser for one expected audio stream. The external compatibility contract is JSON output only; this subdivision does not require a real FFmpeg invocation for acceptance.
- Transform intent is represented by `AudioTransformRecipe` with allowlisted operations and bounded typed fields. Arbitrary FFmpeg filter graphs, argv fragments, URLs and shell strings are not part of the API.
- QA evaluates deterministic source facts and reports explicit PASS/WARN/BLOCKED/BUDGET_EXCEEDED states for budgets, clipping, silence and loop seams.
- Source identity remains the R8 revision + SHA-256; transformed bytes are not promoted merely because a recipe exists.

Manual state: **CONDITIONAL**. The condition is not triggered when acceptance claims are limited to deterministic WAV parsing, transform compilation contracts, fake/bounded ffprobe JSON parsing and QA semantics. A real local FFmpeg run would be required only if this subdivision attempted to assert runtime-specific codec/transcode behavior.
