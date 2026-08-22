# R6.2 — KodeBudget foundation — Design

**Phase:** R6.2  
**Status:** IMPLEMENTED / ACCEPTANCE PENDING  
**Architecture:** v1.0 frozen; additive quality module, no ADR required.

## Purpose

R6.2 establishes the per-platform budget contract defined by the frozen architecture before later collectors and CI gates consume real measurements.

The architecture names FPS/frame time, CPU/GPU, RAM/VRAM, storage, draw calls, polygons, textures, audio memory/voices, build size, mobile battery/thermal and online network budgets.

## Delivered contract

- `BudgetMetric` enumerates the frozen budget families with explicit units in constraints/results.
- `BudgetDirection` supports `at_least` and `at_most` limits.
- `BudgetConstraint` separates a desired target from a hard limit; crossing the target can warn while crossing the hard limit fails.
- `PlatformBudgetSpec` is platform-scoped and rejects duplicate metrics.
- `KodeBudget.from_project_dna()` derives only budgets for Project DNA target platforms.
- Existing `PerformanceBudget` values become FPS, frame-time, RAM, VRAM and build-size constraints when configured.
- `KodeBudget.evaluate()` rejects duplicate and unconfigured observations; configured-but-unmeasured constraints remain explicit `unknown` results.
- Coverage measures only configured constraints, so missing observations cannot silently pass.
- Hard-limit failures can be blocking.
- `BudgetReport` validates timestamps, coverage, aggregate status and serialized derived evidence.
- `BudgetStore` persists only under `.kodepoia/budgets/` through the existing `WorkspaceBoundary`, with atomic latest reports and timestamped snapshots.
- `schemas/budget-report-v1.schema.json` defines the serialized v1 report contract.

## Scope boundary

R6.2 does not invent platform budgets that are absent from Project DNA and does not execute profilers or external commands. It evaluates structured observations only. CPU/GPU, asset, audio, mobile and network collectors are later R6 work and remain unconfigured until an explicit platform budget exists.

## Rollback

The change is additive. Revert the R6.2 commits; existing Project DNA and `.kodepoia/budgets/` directories remain valid because no existing schema is migrated.
