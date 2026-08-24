# R11.6 — Acceptance

Status: **IMPLEMENTATION ACCEPTED — FINAL DOCUMENTATION GATES PENDING**  
Manual intervention: **CONDITIONAL — NOT TRIGGERED**

## Branch point and scope

- Base normalized `main`: `e12a575314afd511bb752f263c9e5b7e60c75d51`.
- Branch: `r11/6-speech-alignment-viseme-qa`.
- PR: #167.
- Exact accepted implementation candidate: `ea86762ecaa5ab16f6637701638c3461eea9d5ce`.
- R11.6 scope only: speech alignment normalization, phoneme/viseme timeline, coarticulation, lip-sync QA and caption timing bridge.
- R11.7 facial target mapping and R11.9 Godot cinematic runtime work remain out of scope.

## Hosted exact-head evidence — implementation candidate

All required gates succeeded on `ea86762ecaa5ab16f6637701638c3461eea9d5ce`:

- R0 Repository Guard #1403 / `32745871626`: **SUCCESS**.
- Python Core #1377 / `32745871312`: **SUCCESS**.
  - Ubuntu: **981 passed / 8 skipped / 46 warnings**.
  - R7/R8/R9 integrated acceptance: **PASS**.
  - Windows Python: **SUCCESS**.
  - Ubuntu + Windows package builds: **SUCCESS**.
  - internal KodeStudio smoke: **SUCCESS**.
- KodeStudio UI Smoke #1344 / `32745871357`: **SUCCESS**.

## Accepted behavior

Focused R11.6 coverage proves:

- deterministic backend timing normalization and synthetic fixture identity;
- negative/non-finite/non-monotonic/out-of-duration timing rejection;
- strict backend document shape and event budgets;
- versioned viseme mapping with explicit unknown-phoneme fallback;
- bounded deterministic attack/release coarticulation;
- identity-bound lip-sync QA for density, overlap, drift, fallback and confidence;
- captions remain separate and can never become phoneme authority;
- alignment, viseme, QA and caption artifacts validate against versioned JSON schemas;
- no facial rig target or Godot runtime resource is produced by R11.6.

## Manual checkpoint decision

The frozen R11 plan says R11.6 manual intervention is **CONDITIONAL** and triggers only when accepted production behavior relies on backend/native phoneme timing or an external aligner that hosted CI cannot reproduce.

This implementation makes no such production-runtime accuracy claim. It normalizes already-provided timing and tests deterministic Kodepoia semantics using synthetic/fake data only. It installs/runs no aligner, downloads no acoustic/dictionary model and uses no private recording. Therefore manual intervention is **NOT TRIGGERED**.

Montreal Forced Aligner remains only a possible future governed backend compatibility target; it is not an R11.6 dependency or acceptance authority.

## Final acceptance ordering

- The implementation head above is immutable and accepted.
- This document update creates a documentation-only final head; run fresh R0 + full Python Core + UI Smoke on that exact head.
- Merge PR #167 only if all three final-documentation gates are SUCCESS and the PR head is unchanged.
- Perform exactly one continuity-only post-merge normalization, re-gate it with all three workflows, and merge it.
- Only that normalization merge makes R11.6 **COMPLETE + NORMALIZED** and authorizes R11.7.
