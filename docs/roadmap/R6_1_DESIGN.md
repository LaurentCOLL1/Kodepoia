# R6.1 — KodeHealth foundation — Design

**Phase:** R6.1  
**Status:** IMPLEMENTED / ACCEPTANCE PENDING  
**Architecture:** v1.0 frozen; no foundation change and no ADR required.

## Purpose

R6.1 establishes the project-health contract required by the frozen architecture before later R6 collectors and gates are added.

The frozen architecture defines KodeHealth across these dimensions: build, tests, warnings, security, dependencies, performance, memory, assets, audio, accessibility, localization, technical debt, licences, and privacy.

## Delivered contract

- `HealthDimension` contains exactly the 14 architecture health dimensions.
- `HealthStatus` is `unknown`, `pass`, `warn`, or `fail`.
- `HealthMetric` records one dimension, status, optional evidence summary/source/details, numeric score, and whether a failure blocks progression.
- `HealthPolicy` provides deterministic initial thresholds: FAIL below 60, PASS at or above 85, and complete dimension coverage required for overall PASS.
- `KodeHealth.evaluate()` rejects duplicate dimensions and normalizes absent dimensions to explicit `unknown` metrics.
- Overall score is the arithmetic mean of measured dimensions only; coverage separately records the measured fraction so unknown dimensions cannot silently improve confidence.
- Any explicit dimension FAIL makes the overall report FAIL. WARN dimensions, incomplete coverage, or a score below the PASS threshold make the overall report WARN.
- `HealthReport` validates schema version, timezone-aware timestamps, score ranges, unique/exhaustive dimensions, and coverage consistency.
- `HealthStore` persists only under the initialized project's fixed `.kodepoia/health/` location.
- `latest.json` is written atomically and an optional timestamped snapshot preserves point-in-time evidence.
- `schemas/health-report-v1.schema.json` defines the serialized v1 contract.

## Architectural boundary

R6.1 does not execute arbitrary commands, inspect arbitrary host paths, or bypass Guardian/Sandbox/SafeChange. It only evaluates supplied structured observations and writes health metadata to the fixed project health directory.

Real collectors for build/tests/regression/security/performance and later major-patch validation gates are subsequent R6 work. Unknown domains therefore remain visible instead of being guessed or treated as healthy.

## Rollback

R6.1 is additive. Rollback consists of reverting the R6.1 commits; existing projects remain valid because `.kodepoia/health/` already exists in the project layout and no existing schema or project file is migrated.
