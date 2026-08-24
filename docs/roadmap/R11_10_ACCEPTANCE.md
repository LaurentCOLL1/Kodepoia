# R11.10 — Acceptance

Status: **IMPLEMENTED — HOSTED EXACT-HEAD GATES PENDING**  
Manual intervention: **NONE**

## Base and scope

- Base normalized `main`: `470d8c63eda6bbc3e1a8151c6e050df334a94dba`.
- Branch: `r11/10-continuity-bridge`.
- Scope follows frozen `R11_PLAN.md`: typed continuity snapshots, structural deterministic diff/findings, explicit stale/missing/conflict states, R8 revision-bound bridge package and no automatic canon promotion.

## Acceptance criteria

- Snapshot digest is deterministic and independent of fact input order.
- Duplicate IDs, non-finite values, invalid extension namespaces and budget overflow fail closed.
- Structural differences produce stable finding IDs and explicit severity.
- Missing/deleted/conflicted reference states remain explicit.
- Cross-project bridge package is target-bound and snapshot-digest-bound.
- Tampering, wrong target or same-project package fails closed.
- `promotion_policy` is fixed to `compare_only_no_canon_mutation`; R11.10 cannot modify Canon.
- Snapshot/diff/bridge schemas validate canonical examples.
- Full R0 Repository Guard, Python Core and KodeStudio UI Smoke must be SUCCESS on one exact implementation head.
- After run IDs are recorded, the documentation head is re-gated before merge.

## Manual state

**NONE.** No real project/runtime is required; synthetic project fixtures are authoritative.

## Completion ordering

Accepted exact head → merge with expected SHA → exactly one continuity-only normalization + exact-head gates → merge normalization → only then R11.11 is authorized.
