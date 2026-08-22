# R6 — Quality / Health / Budget / CI — Status

**Phase:** R6  
**Status:** IN PROGRESS  
**Started:** 2026-08-22

R1–R5 remain COMPLETE. R6 is active under the frozen architecture v1.0.

## Accepted subdivisions

1. **R6.1 — KodeHealth foundation** — COMPLETE — PR #30 merged as `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.
2. **R6.2 — KodeBudget foundation** — COMPLETE — PR #32 merged as `65510a9b116d9c48b185a0edb51d99e5b951200a`.
3. **R6.3 — KodeTests + KodeRegression foundation** — COMPLETE — PR #34 merged as `6657b258f2396b3d6a3850153b1ffaae1951104d`.

## R6.1 accepted scope

R6.1 established KodeHealth with the 14 frozen health dimensions, explicit unknown coverage, blocking failures, validated reports, atomic `.kodepoia/health/` persistence, WorkspaceBoundary confinement and schema v1.

Accepted head `802de4ba3110ace657c4e16306a0ca29850ce2bd`; R0 `32561211168`, Python Core `32561211156` and UI Smoke `32561211167` all SUCCESS.

## R6.2 accepted scope

R6.2 established per-platform KodeBudget with 16 architecture-aligned metrics, target/hard-limit semantics, Project DNA derivation for FPS/frame time/RAM/VRAM/build size, explicit observation coverage, blocking failures, validated reports and WorkspaceBoundary persistence under `.kodepoia/budgets/`.

Accepted head `8ac3772e98c70260c320519a214bb25b6cedbb38`; R0 `32561719921`, Python Core `32561719925` and UI Smoke `32561720008` all SUCCESS. PR #32 merged as `65510a9b116d9c48b185a0edb51d99e5b951200a`.

## R6.3 accepted scope

R6.3 implements the adjacent roadmap pair Tests + Regression:

- stable test case IDs and `pass/fail/error/skip` observations;
- deterministic test-run `unknown/pass/warn/fail` aggregation;
- validated derived counts and total duration;
- atomic test-run evidence under `.kodepoia/tests/runs/` through `WorkspaceBoundary`;
- baseline/current comparison by stable test ID;
- explicit `unchanged/regressed/fixed/added/removed` changes;
- regression detection for failures/errors, skipped formerly-passing/failing tests, removed cases and added failing/error tests;
- explicit protection against hiding an existing failure by converting it to `skip`;
- validated derived regression lists and serialized tamper detection;
- atomic regression evidence under `.kodepoia/tests/regression/` through `WorkspaceBoundary`;
- `test-run-report-v1` and `regression-report-v1` schemas;
- focused R6.3 acceptance tests and documented rollback;
- no new arbitrary command execution path.

Accepted implementation head: `7150237c263dd3ac96af4662d74909e05f3cf991`.

Final R6.3 GitHub CI:

- R0 Repository Guard `32562032986` / #622 — SUCCESS Windows + Ubuntu;
- Python Core `32562032998` / #596 — SUCCESS Windows + Ubuntu, PowerShell validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32562032982` / #563 — SUCCESS Windows.

PR #34 merged as `6657b258f2396b3d6a3850153b1ffaae1951104d`.

**R6.1 = COMPLETE. R6.2 = COMPLETE. R6.3 = COMPLETE.**

## Remaining R6 scope

The frozen roadmap still requires VisualQA, Accessibility, Localization, TechnicalDebt, CI/Build, AppSecurity baseline, Privacy baseline, License/BOM, and the rule that every major patch has validation and rollback.

R6 itself remains **IN PROGRESS**. Do not mark R6 COMPLETE and do not skip directly to R7 before the remaining R6 scope is accepted.
