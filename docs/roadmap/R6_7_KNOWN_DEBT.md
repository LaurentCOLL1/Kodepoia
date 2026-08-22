# R6.7 — Known technical-debt observations

This file records observations already seen during accepted Kodepoia work. It is **not** an assertion that a new scanner was run. Each entry must retain its real provenance and must be rechecked before being promoted into a project-local `.kodepoia/diagnostics/technical_debt/` register.

## Candidate TD-OBS-001 — Pillow `Image.getdata()` deprecation

- category: dependencies / code quality
- observed source: hosted Python Core pytest warning output during R6 work
- affected area: VisualQA image processing
- current interpretation: open candidate; Pillow warnings indicated `Image.getdata()` deprecation with future removal timeline
- recommended R6.7 representation if reproduced: medium severity, nonblocking, file/symbol reference to the VisualQA call site, source/provenance equal to the exact workflow run/log
- do not resolve merely by suppressing the warning; replace the deprecated API and preserve VisualQA deterministic behavior.

## Candidate TD-OBS-002 — pytest collection warnings from imported `Test*` symbols

- category: tests
- observed source: hosted pytest output during R6 work
- affected area: tests that import classes whose names begin with `Test`
- current interpretation: low-severity collection-noise candidate
- recommended representation if reproduced: nonblocking, with exact test-file/symbol references and exact workflow provenance
- do not rename public quality classes solely to silence pytest without checking compatibility; local aliasing or collection controls may be safer.

## Candidate TD-OBS-003 — Qt font-directory / `propagateSizeHints()` notices

- category: accessibility / build environment
- observed source: required R6.5 Windows local acceptance
- messages included a missing PySide6 bundled-font directory notice and `This plugin does not support propagateSizeHints()`
- structured R6.5 accessibility reports nevertheless had zero warnings, zero unknowns and zero blockers, so these notices did not fail R6.5
- current interpretation: environment-specific candidate debt only; recheck in an ordinary interactive KodeStudio run before promoting it
- do not reopen R6.5 from these notices alone.

## Promotion rule

A candidate becomes authoritative technical-debt evidence only when it is represented as a valid `TechnicalDebtItem` with:

- stable debt ID;
- category/severity;
- impact/probability/effort;
- explicit scope/source/provenance;
- stable references;
- first/last seen timestamps;
- lifecycle state;
- rationale when accepted;
- blocking status when justified.

Do not fabricate workflow IDs, scan results or resolution evidence.
