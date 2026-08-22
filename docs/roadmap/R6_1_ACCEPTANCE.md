# R6.1 — KodeHealth foundation — Acceptance

**Status:** PENDING CI / PR MERGE

## Acceptance gates

R6.1 is accepted only when all of the following pass on the branch and PR:

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

## Local implementation evidence before final CI

The isolated R6.1 unit suite was executed after workspace-boundary hardening and reported:

```text
9 passed
```

This local evidence is not sufficient to mark R6.1 COMPLETE. GitHub CI and merge evidence are still required.
