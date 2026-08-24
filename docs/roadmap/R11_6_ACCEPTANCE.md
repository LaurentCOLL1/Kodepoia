# R11.6 — Acceptance

Status: **IMPLEMENTATION CANDIDATE — HOSTED GATES PENDING**  
Manual intervention: **CONDITIONAL — NOT TRIGGERED**

## Branch point and scope

- Base normalized `main`: `e12a575314afd511bb752f263c9e5b7e60c75d51`.
- Branch: `r11/6-speech-alignment-viseme-qa`.
- R11.6 scope only: speech alignment normalization, phoneme/viseme timeline, coarticulation, lip-sync QA and caption timing bridge.
- R11.7 facial target mapping and R11.9 Godot cinematic runtime work remain out of scope.

## Required hosted acceptance

The exact implementation candidate must pass all of the following on one immutable head:

1. R0 Repository Guard — SUCCESS.
2. Full Python Core — SUCCESS on Ubuntu and Windows, including R7/R8/R9 integrated checks and package builds.
3. KodeStudio UI Smoke — SUCCESS.
4. Focused R11.6 tests demonstrate:
   - deterministic backend timing normalization and synthetic fixture identity;
   - negative/non-finite/non-monotonic/out-of-duration timing rejection;
   - strict backend document shape/event budgets;
   - versioned viseme mapping and explicit unknown fallback;
   - bounded deterministic attack/release coarticulation;
   - identity-bound lip-sync QA for density/overlap/drift/fallback/confidence;
   - captions remain separate and never phoneme authority;
   - canonical artifacts validate against versioned JSON schemas.

## Manual checkpoint decision

The frozen R11 plan says R11.6 manual intervention is **CONDITIONAL** and triggers only when accepted production behavior relies on backend/native phoneme timing or an external aligner that hosted CI cannot reproduce.

This candidate makes no such production-runtime accuracy claim. It normalizes already-provided timing and tests deterministic Kodepoia semantics using synthetic/fake data only. It installs/runs no aligner, downloads no acoustic/dictionary model and uses no private recording. Therefore manual intervention is **NOT TRIGGERED**.

If later implementation in this subdivision adds a real external/native alignment claim before merge, this decision becomes invalid and the exact candidate/manual command/evidence requirements must be frozen before any local run.

## Completion ordering

- Freeze implementation head and run R0 + Python Core + UI Smoke.
- If the acceptance document changes to record immutable head/run IDs, re-run all three gates on that final documentation head.
- Merge the exact accepted PR head with expected-SHA protection.
- Perform exactly one continuity-only post-merge normalization, re-gate it with all three workflows, and merge it.
- Only that normalization merge makes R11.6 COMPLETE + NORMALIZED and authorizes R11.7.
