# R6.1 — KodeHealth foundation — Acceptance

**Status:** COMPLETE  
**Accepted:** 2026-08-22  
**Accepted implementation head:** `802de4ba3110ace657c4e16306a0ca29850ce2bd`  
**Merged by:** PR #30  
**Merge commit:** `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`

## Acceptance gates

R6.1 required all of the following:

1. Python compilation passes on Windows and Ubuntu.
2. Existing full pytest suite remains green.
3. KodeStudio smoke remains green on Windows.
4. `tests/test_r6_1_health.py` passes.
5. All 14 frozen-architecture KodeHealth dimensions are represented exactly once in a normalized report.
6. Missing measurements become explicit `unknown` dimensions and reduce coverage.
7. Duplicate dimensions and invalid scores/status combinations are rejected.
8. A dimension FAIL forces overall FAIL; blocking failures remain separately enumerable.
9. Overall PASS requires complete dimension coverage under the default R6.1 policy.
10. Serialized reports round-trip through `HealthReport.load()` with validation, and serialized derived fields must match metric evidence.
11. Persistence is confined to an initialized project's `.kodepoia/health/` directory through the existing `WorkspaceBoundary`, including rejection of symlink escape.
12. `latest.json` and timestamped evidence snapshots are produced without changing any frozen architecture file.
13. The JSON schema for health report v1 is present.
14. No R1–R5 governance boundary is bypassed or weakened.

## Local implementation evidence

After workspace-boundary and serialized-evidence hardening:

```text
9 passed
```

## Authoritative GitHub CI evidence

Final accepted PR #30 head: `802de4ba3110ace657c4e16306a0ca29850ce2bd`.

- R0 Repository Guard — run `32561211168` — **SUCCESS** (Windows + Ubuntu).
- Python Core — run `32561211156` — **SUCCESS**:
  - `python-core-ubuntu-latest` — SUCCESS;
  - `python-core-windows-latest` — SUCCESS, including PowerShell acceptance-runner syntax validation;
  - integrated `kodestudio-ui-windows` job — SUCCESS.
- KodeStudio UI Smoke — run `32561211167` — **SUCCESS** (Windows).

## Merge evidence

PR #30 was merged to `main` as `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1` only after all final-head gates above were successful.

## Acceptance result

| Gate | Result |
| --- | --- |
| 14 architecture health dimensions | PASS |
| Explicit unknown coverage | PASS |
| Deterministic aggregate status | PASS |
| Blocking failure reporting | PASS |
| Report validation / JSON round-trip | PASS |
| Derived-field tamper detection | PASS |
| WorkspaceBoundary persistence confinement | PASS |
| Symlink escape rejection | PASS |
| Local focused tests | PASS — 9 |
| R0 Windows + Ubuntu | PASS |
| Python Core Windows + Ubuntu | PASS |
| KodeStudio smoke | PASS |
| PR #30 merged | PASS |

**R6.1 = COMPLETE.**
