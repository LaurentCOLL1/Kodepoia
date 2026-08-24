# R11.14 — Acceptance record

Status: **IMPLEMENTATION CANDIDATE — EXACT-HEAD GATES PENDING**  
Frozen manual intervention: **CONDITIONAL — NOT TRIGGERED unless a new authoritative runtime seam is exposed**

## Base and frozen scope

- Base normalized `main`: `72d17eeda7b72b480b7a2268bec5c57187bc64e9`.
- Branch: `r11/14-adversarial-integrated-acceptance`.
- Scope: adversarial cross-seam hardening plus anti-circular R11 integrated acceptance only.
- R12 remains forbidden throughout R11.14 until the final continuity-only normalization passes and merges.

## Definition of Done

R11.14 is accepted only after the anti-circular sequence frozen in `R11_PLAN.md` completes:

1. one immutable implementation head contains the adversarial suite, integrated acceptance model/verifier, JSON Schema, design and this acceptance contract, while the canonical R11 report is still absent;
2. that exact implementation head passes R0 Repository Guard + full Python Core + KodeStudio UI Smoke, with Ubuntu/Windows Python, package builds and prior integrated reports remaining PASS where authoritative;
3. the accepted implementation SHA is then bound as R11.14 `source_sha`/`accepted_head`, and its exact implementation run IDs are frozen in this document;
4. `docs/roadmap/R11_INTEGRATED_ACCEPTANCE.json` is generated only from that immutable implementation SHA plus immutable repository evidence;
5. the final documentation/evidence head passes fresh exact-head R0 + full Python Core + KodeStudio UI Smoke;
6. the canonical R11 report verifies `status=pass`, `blockers=[]` and the REQUIRED R11.5/R11.9 evidence remains valid;
7. the implementation/evidence PR merges with its exact expected head SHA;
8. exactly one final continuity-only normalization records R11 closure and the canonical semantic digest, passes the same exact-head gates and merges.

Only step 8 makes R11 **COMPLETE + NORMALIZED** and authorizes **R12 planning**.

## Required adversarial properties

The dedicated R11.14 suite must fail closed for representative cross-seam attacks including:

- forbidden environment/path/output-root injection;
- Unicode bidi/control-character confusion and raw XML/SSML-like markup;
- non-finite semantic/timing values and schema-version substitution;
- unauthorized research authority becoming canonical Canon state;
- cyclic Canon supersession/deprecation;
- SaveBridge checksum substitution and migration cycles;
- acceptance-document and normalized-continuity substitution after binding;
- prior integrated-report failure/substitution;
- R11 integrated semantic-digest tampering.

Full Python Core additionally re-runs every accepted R11.1–R11.13 test, including audio parsing/QA, runtime boundaries, TTS timeout/cancel/cache, alignment/viseme QA, facial target validation, cinematic timeline/capture, Continuity Bridge, Canon conflicts, SaveBridge rollback, CLI/KodeStudio safety and R7/R8/R9/R10 integrated checks.

## Integrated verifier requirements

The report verifier must independently re-read and bind:

- `docs/roadmap/R11_1_ACCEPTANCE.md` through `R11_14_ACCEPTANCE.md` in strict order;
- normalized `docs/continuity/KODEPOIA_CONTINUITY.md`;
- `docs/roadmap/R11_5_LOCAL_ACCEPTANCE.json` and `R11_9_LOCAL_ACCEPTANCE.json` by file identity, exact source SHA and collector semantic digest;
- canonical `R7_INTEGRATED_ACCEPTANCE.json`, `R8_INTEGRATED_ACCEPTANCE.json`, `R9_INTEGRATED_ACCEPTANCE.json` and `R10_INTEGRATED_ACCEPTANCE.json` by repository identity and semantic evidence digest.

Passing evidence cannot contain explicit or derived blockers. Unsatisfied REQUIRED/triggered CONDITIONAL manual state, stale/missing evidence, changed accepted bytes after binding, changed local semantic digest, failed local runtime/privacy/QA assertions or non-PASS prior integrated evidence must reject verification.

`generated_at` is excluded from the semantic evidence digest; changing only that timestamp must not alter `evidence_sha256`.

## Frozen preserved evidence

R11.5 REQUIRED local TTS evidence remains authoritative:

- source SHA `a9862b3bf475b259fe154d1e2486116ad04602f3`;
- semantic digest `12223e911a76087a4eea23ce9e371fdc401990d127cb9f306237d67550725ffe`;
- local/offline Piper-compatible synthesis, approved repository-local voice identity, privacy-safe transport and PASS QA.

R11.9 REQUIRED local cinematic evidence remains authoritative:

- source SHA `087eae19ea03dd544d75a08c1eb348fe187624c5`;
- semantic digest `6afe45e3c9047cfa58b7c617ff671e34e166bd9189a32ea62f1350243955b6f5`;
- Godot 4.7-compatible repository-synthetic capture, 90/90 frames and bounded A/V synchronization.

Prior canonical semantic digests remain frozen to their already accepted values:

- R7 `5b56bb94b6c5c0b8a11e0d1883d0123f0803418414509517e88204990647e2fc`;
- R8 `c73868d7f89453c65d3b633ccdded70d031766c1ce05b77c02e8e4a0d51ed8c5`;
- R9 `ad8ad9d16682f54dd942e76dccf333234065d27f320409301cbb8dd67036dcdc`;
- R10 `48c18aacc916fb064810b36ada5a179f1d3b149912bea8a19a3295da1826a3c8`.

## Manual-state evaluation

Current evaluation: **CONDITIONAL NOT TRIGGERED**.

R11.14 introduces deterministic adversarial validation and evidence binding only. It does not change authoritative Piper/TTS synthesis behavior, Godot capture behavior, FFmpeg/ffprobe execution semantics, or add a new external runtime. The reviewed REQUIRED R11.5 and R11.9 local evidence is revalidated rather than replaced.

If exact-head gates demonstrate that the implementation has created or newly depends on a runtime-specific semantic not covered by the preserved evidence, this state must change to triggered and work must stop before canonical PASS report generation until bounded local evidence is collected and reviewed.

## Implementation-candidate history

No implementation head is accepted yet. The canonical `docs/roadmap/R11_INTEGRATED_ACCEPTANCE.json` MUST remain absent until one exact implementation head passes all three authoritative gates.

## Completion ordering

Implementation head -> exact-head R0/Python/UI -> freeze accepted source SHA/run IDs here -> generate canonical integrated report -> fresh exact-head R0/Python/UI -> merge implementation/evidence PR -> exactly one continuity-only normalization -> exact-head R0/Python/UI -> merge normalization -> R11 COMPLETE + NORMALIZED -> R12 planning authorized.
