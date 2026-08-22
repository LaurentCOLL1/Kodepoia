# R6.2 — KodeBudget foundation — Acceptance

**Status:** PENDING CI / PR MERGE

## Acceptance gates

R6.2 is accepted only when all of the following pass on the final PR head:

1. Python compilation passes on Windows and Ubuntu.
2. Existing full pytest suite remains green.
3. KodeStudio smoke remains green on Windows.
4. `tests/test_r6_2_budget.py` passes.
5. Only target platforms from Project DNA receive derived budget specs.
6. Existing Project DNA FPS, RAM, VRAM and build-size values are preserved as deterministic constraints.
7. Frame-time limits are deterministically derived from FPS values.
8. Target misses warn while hard-limit violations fail.
9. Configured-but-unmeasured constraints remain explicit `unknown` and reduce coverage.
10. Duplicate or unconfigured observations are rejected.
11. Blocking hard-limit failures are separately enumerable.
12. Serialized reports round-trip with derived-field consistency validation.
13. Persistence is confined to `.kodepoia/budgets/` through `WorkspaceBoundary`.
14. `budget-report-v1` JSON schema is present.
15. No R1–R6.1 governance boundary is bypassed or weakened.

## Pre-CI isolated evidence

An isolated core smoke exercised Project DNA derivation, full PASS evaluation, blocking FAIL evaluation and persistent round-trip successfully.

This evidence is not sufficient to mark R6.2 COMPLETE. Authoritative GitHub CI and merge evidence are still required.
