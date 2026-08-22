# R6.3 — KodeTests + KodeRegression foundation — Acceptance

**Status:** COMPLETE  
**Accepted:** 2026-08-22  
**Accepted implementation head:** `7150237c263dd3ac96af4662d74909e05f3cf991`  
**Merged by:** PR #34  
**Merge commit:** `6657b258f2396b3d6a3850153b1ffaae1951104d`

## Acceptance gates

R6.3 required all of the following:

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

## Isolated pre-CI evidence

An isolated core smoke compiled the KodeTests/KodeRegression design, compared a baseline/current pair with one regression, one fix and one added test, and persisted test and regression evidence successfully.

## Authoritative GitHub CI evidence

Final accepted PR #34 head: `7150237c263dd3ac96af4662d74909e05f3cf991`.

- R0 Repository Guard — run `32562032986` / #622 — **SUCCESS** Windows + Ubuntu.
- Python Core — run `32562032998` / #596 — **SUCCESS**:
  - `python-core-ubuntu-latest` — SUCCESS;
  - `python-core-windows-latest` — SUCCESS, including PowerShell acceptance-runner syntax validation;
  - integrated `kodestudio-ui-windows` — SUCCESS.
- KodeStudio UI Smoke — run `32562032982` / #563 — **SUCCESS** Windows.

## Merge evidence

PR #34 was merged to `main` as `6657b258f2396b3d6a3850153b1ffaae1951104d` only after all final-head gates were successful.

## Acceptance result

| Gate | Result |
| --- | --- |
| Stable unique test IDs | PASS |
| Test status aggregation | PASS |
| Count/duration evidence validation | PASS |
| Test evidence persistence | PASS |
| Baseline/current suite matching | PASS |
| Regression/fix/add/remove classification | PASS |
| Skip cannot hide regression | PASS |
| Removed cases detected | PASS |
| Added failing cases detected | PASS |
| Regression derived-field validation | PASS |
| Regression persistence | PASS |
| JSON schemas v1 | PASS |
| No new command-execution path | PASS |
| R0 Windows + Ubuntu | PASS |
| Python Core Windows + Ubuntu | PASS |
| KodeStudio smoke | PASS |
| PR #34 merged | PASS |

**R6.3 = COMPLETE.**
