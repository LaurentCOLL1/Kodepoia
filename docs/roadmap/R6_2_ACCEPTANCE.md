# R6.2 — KodeBudget foundation — Acceptance

**Status:** COMPLETE  
**Accepted:** 2026-08-22  
**Accepted implementation head:** `8ac3772e98c70260c320519a214bb25b6cedbb38`  
**Merged by:** PR #32  
**Merge commit:** `65510a9b116d9c48b185a0edb51d99e5b951200a`

## Acceptance gates

R6.2 required all of the following:

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

## Isolated pre-CI evidence

Project DNA derivation, full PASS evaluation, blocking FAIL evaluation and persistence round-trip all passed in an isolated core smoke.

## Authoritative GitHub CI evidence

Final accepted PR #32 head: `8ac3772e98c70260c320519a214bb25b6cedbb38`.

- R0 Repository Guard — run `32561719921` / #603 — **SUCCESS** Windows + Ubuntu.
- Python Core — run `32561719925` / #577 — **SUCCESS**:
  - `python-core-ubuntu-latest` — SUCCESS;
  - `python-core-windows-latest` — SUCCESS, including PowerShell acceptance-runner syntax validation;
  - integrated `kodestudio-ui-windows` — SUCCESS.
- KodeStudio UI Smoke — run `32561720008` / #544 — **SUCCESS** Windows.

## Merge evidence

PR #32 was merged to `main` as `65510a9b116d9c48b185a0edb51d99e5b951200a` only after all final-head gates were successful.

## Acceptance result

| Gate | Result |
| --- | --- |
| Target-platform budget derivation | PASS |
| Target vs hard-limit semantics | PASS |
| Explicit unknown coverage | PASS |
| Blocking failures | PASS |
| Invalid observation rejection | PASS |
| Report validation / round-trip | PASS |
| WorkspaceBoundary persistence | PASS |
| Budget report schema v1 | PASS |
| R0 Windows + Ubuntu | PASS |
| Python Core Windows + Ubuntu | PASS |
| KodeStudio smoke | PASS |
| PR #32 merged | PASS |

**R6.2 = COMPLETE.**
