# R11.14 — Acceptance record

Status: **FINAL EVIDENCE CANDIDATE — EXACT-HEAD FINAL GATES PENDING**  
Frozen manual intervention: **CONDITIONAL — NOT TRIGGERED**

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

Prior canonical semantic digests remain frozen to their currently accepted values on normalized `main`:

- R7 `2d6fc8e95d22891228a462d2731059683ed03ae51bb5fff6e2755b194198f437`;
- R8 `6ea9c82dedbc2adb97849344f94386838235050bc598f0f8a8d0cfb3676dea89`;
- R9 `19291d79bd800fdb76d96656f9f150ee3114dbcde08d2e82415aff7ff747816a`;
- R10 `48c18aacc916fb064810b36ada5a179f1d3b149912bea8a19a3295da1826a3c8`.

## Manual-state evaluation

Final implementation-candidate evaluation: **CONDITIONAL NOT TRIGGERED**.

R11.14 introduces deterministic adversarial validation and evidence binding only. It does not change authoritative Piper/TTS synthesis behavior, Godot capture behavior, FFmpeg/ffprobe execution semantics, or add a new external runtime. The reviewed REQUIRED R11.5 and R11.9 local evidence is revalidated rather than replaced. Exact-head hosted gates exposed no new runtime-specific seam requiring an additional collector.

## Implementation-candidate history

Rejected candidate:

- SHA `1bd7d671e0b708e3d75ec0de013453eec4a6a43e`.
- R0 Repository Guard #1452 / `32768634250` — **SUCCESS**.
- KodeStudio UI Smoke #1393 / `32768637839` — **SUCCESS**.
- Python Core #1426 / `32768635381` — **FAILURE**: four R11.14 test failures (three Python 3.12 dataclass/slots inheritance failures and one stale R7 semantic-digest expectation). No canonical R11 report was generated from this rejected SHA.

Accepted immutable implementation candidate:

- SHA `f2693c8cfd4a7aaa5c73fc0a318ebaeef4ff0bb1`.
- R0 Repository Guard #1455 / `32769325414` — **SUCCESS**.
- Python Core #1429 / `32769325329` — **SUCCESS**.
- KodeStudio UI Smoke #1396 / `32769325281` — **SUCCESS**.
- Python Core Ubuntu and Windows: **SUCCESS**.
- Package build Ubuntu and Windows: **SUCCESS**.
- Python-Core-internal KodeStudio smoke: **SUCCESS**.
- Prior R7/R8/R9 integrated validation remained PASS where authoritatively re-executed.

This accepted implementation SHA is immutable for R11.14 integrated evidence. Documentation/report commits after it MUST NOT replace the R11.14 `source_sha`/`accepted_head`.

## Canonical integrated report state

`docs/roadmap/R11_INTEGRATED_ACCEPTANCE.json` is now present only because the immutable implementation candidate above passed all three required gates. The report binds this final acceptance-document state, normalized R11.13 continuity, the two preserved REQUIRED local runtime artifacts and the canonical R7–R10 integrated reports. Its exact semantic digest is authoritative in the report itself and will be copied into the single post-merge continuity normalization; it is deliberately not embedded in this acceptance document, avoiding a circular digest dependency.

The final documentation/evidence head containing the regenerated canonical report MUST now pass fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke before PR #183 may merge.

## Completion ordering

Accepted implementation head -> frozen exact run IDs -> canonical integrated report -> fresh exact-head R0/Python/UI on final documentation/evidence head -> merge implementation/evidence PR with expected SHA -> exactly one continuity-only normalization containing the report digest -> exact-head R0/Python/UI -> merge normalization -> R11 COMPLETE + NORMALIZED -> R12 planning authorized.
