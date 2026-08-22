# R6.3 — KodeTests + KodeRegression foundation — Acceptance

**Status:** PENDING CI / PR MERGE

## Acceptance gates

R6.3 is accepted only when all of the following pass on the final PR head:

1. Python compilation passes on Windows and Ubuntu.
2. Existing full pytest suite remains green.
3. KodeStudio smoke remains green on Windows.
4. `tests/test_r6_3_tests_regression.py` passes.
5. Test runs use stable unique case IDs and reject negative durations.
6. Empty runs are `unknown`, skipped runs warn, and fail/error observations fail.
7. Serialized test counts and total duration must match underlying case evidence.
8. Test-run persistence is confined to `.kodepoia/tests/runs/` through `WorkspaceBoundary`.
9. Regression comparison requires matching suite identities.
10. PASS→FAIL/ERROR, PASS→SKIP, FAIL→ERROR and removed cases are regressions.
11. FAIL/ERROR→SKIP cannot be misclassified as a fix.
12. New failing/error cases fail regression comparison even without a baseline case.
13. Fixed, added, removed and regressed cases are separately enumerable.
14. Serialized regression derived lists must match entry evidence.
15. Regression persistence is confined to `.kodepoia/tests/regression/` through `WorkspaceBoundary`.
16. Test-run-report-v1 and regression-report-v1 schemas are present.
17. No arbitrary command execution path is introduced and no R1–R6.2 governance boundary is bypassed.

## Pre-CI isolated evidence

An isolated core smoke compiled the draft KodeTests/KodeRegression modules, compared a baseline/current pair with one regression, one fix and one added test, and persisted both test and regression evidence successfully.

This evidence is not sufficient to mark R6.3 COMPLETE. Authoritative GitHub CI and merge evidence are still required.
