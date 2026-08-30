# R15.6 — Acceptance record

**Acceptance state:** COMPLETE — TECHNICAL ACCEPTANCE RECORDED; FINAL END GATES REQUIRED  
**Clean START:** `097e99db28508cd1c53eadfe00b2b33576a445af`  
**Immutable technical source:** `ae856396faa964fee19ee39e461bc7de4e775cd9`  
**Manual:** NONE

## Acceptance contract

R15.6 is merge-eligible only when the final documented END-head proves on Ubuntu and Windows that KodeBench v2 preserves R3 compatibility, deterministic identities, domain/critical scoring, failure isolation, resource evidence, protected-holdout binding and report-schema validity, and that same exact head passes R0 Repository Guard, full Python Core and KodeStudio UI Smoke.

## Required coverage

- deterministic suite/task/scorer/config identities and task-order-independent suite digest;
- all built-in scorer classes plus code-owned custom scorer failure isolation;
- repeated seeds, domain/critical summaries and variance;
- distinct wrong-answer/model/capability/scorer failure categories;
- resource metrics when available;
- strict model/runtime identity and report comparability with critical-regression detection;
- fail-closed R15.4 protected-holdout registry binding and no protected raw prompt/response in saved reports;
- Draft 2020-12 schema validation;
- R3 `BaselineBench` regression tests, Ruff/import checks, compileall and CLI comparison smoke.

## Technical evidence

Technical source `ae856396faa964fee19ee39e461bc7de4e775cd9` passed:

- R15.6 KodeBench v2 Acceptance #2 / `33295649414`: SUCCESS Ubuntu + Windows; 17 combined R3/R15.6 tests per OS plus schema/Ruff/import/compile/CLI checks;
- R0 Repository Guard #2124 / `33295649494`: SUCCESS Ubuntu + Windows;
- Python Core #2099 / `33295649527`: SUCCESS 5/5;
- KodeStudio UI Smoke #2064 / `33295649458`: SUCCESS.

These prove the technical tree only. This END-sync repairs the stale `R15_PLAN.md` START status; therefore those runs are not final-END proof. Fresh R15.6/R0/Python/UI success is required on the final documented PR head before expected-head merge.

## Rollback / recovery

KodeBench v2 adds derived benchmark contracts/reports and a compatibility layer. Rollback removes the v2 module/schema/CLI comparison surface while preserving the accepted R3 baseline and historical immutable benchmark evidence.
