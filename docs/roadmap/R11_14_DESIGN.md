# R11.14 — Adversarial hardening + R11 integrated acceptance design

## Authority and scope

This design implements only the frozen R11.14 section of `R11_PLAN.md` from normalized `main` `72d17eeda7b72b480b7a2268bec5c57187bc64e9`. It adds no R12 feature and changes no accepted R1–R10 foundation. R11.1–R11.13 remain authoritative for their domain/runtime semantics.

R11.14 attacks the seams between the accepted audio, voice, alignment, facial, cinematic, continuity, Canon and SaveBridge subsystems, then binds their immutable evidence into one deterministic integrated report. It never rewrites an earlier acceptance record or local collector output to manufacture a PASS.

## Threat model exercised

The dedicated suite covers high-value cross-boundary failures while the full Python Core re-runs every accepted lower-level R11 suite:

- environment, executable, path and output-root injection at the R11 media runtime boundary;
- Unicode bidi/control-character confusion and raw XML/SSML-like voice markup;
- NaN/Inf entering canonical semantic data, timing or pause values;
- R11 envelope/schema-version substitution;
- unauthorized research-to-Canon promotion and cyclic Canon supersession/deprecation graphs;
- SaveBridge checksum substitution and migration-cycle attacks;
- acceptance-document and normalized-continuity substitution after evidence binding;
- required R11.5/R11.9 local-evidence substitution or semantic digest drift;
- prior R7/R8/R9/R10 integrated-report substitution/non-PASS state;
- R11 integrated-report digest tampering.

Previously accepted R11.1–R11.13 tests remain the authority for the exhaustive malformed audio/ffprobe, TTS timeout/cancel/cache, alignment timing, viseme/facial target, cinematic timeline/capture, Continuity Bridge, Canon conflict and durable SaveBridge rollback matrices. R11.14 does not duplicate those suites merely to increase test count; it adds cross-seam attacks and requires the full suite on every exact head.

## Integrated evidence model

`src/kodepoia/media/acceptance.py` defines a versioned deterministic report with four evidence classes:

1. fourteen ordered R11 acceptance documents (`R11.1` through `R11.14`), each bound by repository SHA-256, byte length, immutable accepted implementation head and satisfied frozen manual state;
2. normalized `docs/continuity/KODEPOIA_CONTINUITY.md`, bound by repository SHA-256/byte length and used as additional immutable exact-head authority;
3. the two REQUIRED local runtime artifacts, `R11_5_LOCAL_ACCEPTANCE.json` and `R11_9_LOCAL_ACCEPTANCE.json`, bound by repository identity, exact source SHA and their collector-defined semantic `evidence_digest`;
4. canonical R7/R8/R9/R10 integrated reports, bound by repository identity and their own semantic `evidence_sha256`.

The verifier re-reads repository bytes. Required local evidence must remain `status=pass`, `blockers=[]`, internally digest-consistent and bound to the accepted R11.5/R11.9 source heads. R11.5 additionally reasserts offline capability, clean process completion, non-argv text transport, ephemeral input deletion, PASS QA, explicit license review and privacy invariants. R11.9 reasserts Godot 4.7 compatibility, repository-synthetic fixture identity, complete expected frame count and bounded A/V drift.

The dedicated repository test also freezes the already accepted local semantic digests:

- R11.5: `12223e911a76087a4eea23ce9e371fdc401990d127cb9f306237d67550725ffe`;
- R11.9: `6afe45e3c9047cfa58b7c617ff671e34e166bd9189a32ea62f1350243955b6f5`.

It likewise freezes the accepted prior integrated semantic digests for R7, R8, R9 and R10 so a substituted pre-report artifact cannot silently become the new baseline.

## Semantic digest and anti-circularity

`generated_at` is metadata only and is intentionally excluded from `evidence_sha256`. The semantic digest covers the schema version, immutable R11.14 source SHA, continuity binding, all subdivision bindings, required local evidence, prior integrated evidence, status and blockers. This makes repeated generation at a different timestamp semantically identical while any evidence/runtime/manual/source change alters the digest.

The canonical `docs/roadmap/R11_INTEGRATED_ACCEPTANCE.json` is intentionally absent from the initial implementation candidate.

1. Freeze one implementation head containing verifier, schema, adversarial tests, design and acceptance contract.
2. Require exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke.
3. Only after those gates succeed, bind that immutable implementation SHA as R11.14 `source_sha`/`accepted_head` and record the implementation run IDs in the acceptance document.
4. Generate `R11_INTEGRATED_ACCEPTANCE.json` from repository evidence on that immutable source SHA.
5. Require fresh R0/Python/UI on the exact final documentation/evidence head.
6. Merge only if the canonical report verifies `status=pass`, `blockers=[]` and no required/triggered manual gate is unsatisfied.
7. Perform exactly one final continuity-only normalization, gate that exact head with the same three workflows, then merge it. Only that merge makes R11 COMPLETE + NORMALIZED and authorizes R12 planning.

No report claims the SHA of its own future Git blob or a future final-documentation commit.

## Final continuity verification

Before final normalization the report binds the exact normalized R11.13 continuity bytes. After the implementation/evidence PR merges, the single authorized continuity-only normalization necessarily changes that file. The verifier permits that one post-report continuity identity change only when the normalized continuity explicitly states R11.14 `COMPLETE + NORMALIZED` and contains the exact R11 integrated semantic digest. Any other continuity substitution remains rejected.

## Manual-state evaluation

Frozen state: **CONDITIONAL**.

Current implementation introduces no new authoritative Piper, FFmpeg or Godot runtime behavior. It adversarially validates accepted contracts and re-verifies the preserved REQUIRED R11.5 and R11.9 local evidence. Therefore the condition is evaluated as **NOT TRIGGERED** unless the exact-head gates reveal a new runtime-specific seam that cannot be proven by hosted CI plus the already accepted evidence.

If such a seam appears, finalization stops before a PASS report is generated. One bounded collector, exact candidate SHA, prerequisites, expected output, recovery and privacy instructions must then be frozen and reviewed; no hosted or synthetic PASS may substitute for missing real-runtime evidence.

## Rollback and recovery

A failed implementation candidate is fixed or rejected on the R11.14 branch; historical accepted evidence is not rewritten. A failed integrated verifier blocks report generation/merge. If the post-merge normalization fails, R11 remains merged-but-not-normalized and R12 stays forbidden until a corrected continuity-only normalization passes.
