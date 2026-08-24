# R11.10 — Acceptance

Status: **IMPLEMENTATION ACCEPTED — FINAL DOCUMENTATION RE-GATE REQUIRED BEFORE MERGE**  
Manual intervention: **NONE**

## Base and scope

- Base normalized `main`: `470d8c63eda6bbc3e1a8151c6e050df334a94dba`.
- Branch: `r11/10-continuity-bridge`.
- PR: #175.
- Scope follows frozen `R11_PLAN.md`: typed continuity snapshots, deterministic structural diff/findings, explicit stale/missing/conflict states, R8 revision-bound bridge packages and no automatic Canon promotion.

## Rejected initial candidate

Initial head `089ab8bb5bedc74d1b2750ae201b5176ad51216b` compiled and kept R7/R8/R9 PASS but was rejected because one new schema test attempted network resolution of `https://kodepoia.local/...` through a cross-file `$ref`. Ubuntu result: **1 failed, 1023 passed, 8 skipped, 48 warnings**. The failure was in test/schema resolution, not continuity semantics.

The bridge schema was made self-contained with an internal `$defs` snapshot schema and the deprecated `RefResolver` test path was removed. No continuity behavior was weakened.

## Accepted implementation head

Exact implementation head: **`5fb1b80a212880bd510977d54a570859c532c206`**.

- R0 Repository Guard: #1432 / `32759111326` — **SUCCESS**.
- Full Python Core: #1406 / `32759111337` — **SUCCESS**.
  - Ubuntu Python: SUCCESS; R7/R8/R9 integrated checks PASS.
  - Windows Python: SUCCESS.
  - Ubuntu package build: SUCCESS.
  - Windows package build: SUCCESS.
  - internal KodeStudio smoke: SUCCESS.
- KodeStudio UI Smoke: #1373 / `32759111321` — **SUCCESS**.

## Accepted behavior

- Snapshot digest is deterministic and independent of fact input order.
- Duplicate IDs, non-finite values, invalid extension namespaces and budget overflow fail closed.
- Structural differences produce stable finding IDs and explicit severity.
- Missing/deleted/conflicted reference states remain explicit.
- Cross-project bridge package is target-bound and snapshot-digest-bound.
- Tampering, wrong target or same-project package fails closed.
- `promotion_policy` is fixed to `compare_only_no_canon_mutation`; R11.10 cannot modify Canon.
- Snapshot/diff/bridge schemas validate canonical examples entirely offline.
- No shell, runtime, network or real-project dependency was introduced.

## Manual state

**NONE.** Synthetic multi-project fixtures are authoritative for R11.10 acceptance.

## Completion ordering

The documentation-only head created by this record must itself pass R0 + full Python Core + KodeStudio UI Smoke. Then PR #175 may merge only with expected-head protection. Exactly one continuity-only normalization must then be gated and merged. **Only that normalization merge authorizes R11.11.**
