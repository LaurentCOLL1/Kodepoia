# R6.3 — KodeTests + KodeRegression foundation — Design

**Phase:** R6.3  
**Status:** IMPLEMENTED / ACCEPTANCE PENDING  
**Architecture:** v1.0 frozen; additive quality modules, no ADR required.

## Purpose

R6.3 establishes deterministic test-run evidence and baseline regression comparison for later R6 validation gates.

## KodeTests contract

- `TestCaseStatus`: `pass`, `fail`, `error`, `skip`.
- `TestRunStatus`: `unknown`, `pass`, `warn`, `fail`.
- `TestCaseResult` carries stable case ID, status, duration, message, source and structured details.
- `KodeTests.evaluate()` normalizes immutable reports: failures/errors fail the run; skipped cases warn; empty runs are unknown.
- Duplicate test IDs and negative durations are rejected.
- `TestRunReport` derives and validates counts plus total duration; serialized derived fields must match case evidence.
- `TestRunStore` writes atomically under `.kodepoia/tests/runs/` through `WorkspaceBoundary`, with latest and timestamped snapshots.
- `schemas/test-run-report-v1.schema.json` defines the serialized contract.

## KodeRegression contract

- Baseline and current reports must have the same suite identity.
- Cases are compared by stable test ID, not aggregate totals.
- Changes are `unchanged`, `regressed`, `fixed`, `added`, or `removed`.
- PASS→FAIL/ERROR, PASS→SKIP, FAIL→ERROR, removed cases, and newly added failing/error cases are regressions.
- FAIL/ERROR→PASS is a fix; ERROR→FAIL is an improvement/fix rather than a new regression.
- FAIL/ERROR→SKIP is still a regression because skipping must not hide an existing failure.
- A comparison containing regressions fails; an initial comparison containing only new passing/skipped cases warns because no comparable baseline exists.
- `RegressionReport` validates timestamps, unique IDs, aggregate status and serialized derived lists (`regressions`, `fixed`, `added`, `removed`).
- `RegressionStore` writes atomically under `.kodepoia/tests/regression/` through `WorkspaceBoundary`, with latest and timestamped snapshots.
- `schemas/regression-report-v1.schema.json` defines the serialized contract.

## Scope boundary

R6.3 does not execute pytest, Godot or arbitrary commands itself. Existing governed executors and later CI/Build work produce raw test observations; R6.3 converts those observations into durable, comparable evidence. This preserves the Sandbox/Guardian boundary instead of introducing a second command-execution path.

## Rollback

The change is additive. Revert R6.3 commits; existing `.kodepoia/tests/` content remains structurally valid and no prior schema is migrated.
