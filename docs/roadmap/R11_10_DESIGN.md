# R11.10 — Continuity Bridge design

## Scope

R11.10 implements typed continuity snapshots and deterministic cross-scene/project comparison without creating a second save system or silently promoting free-form content to canon.

## Contracts

- `ContinuitySnapshot` carries scope (`shot|sequence|scene|project|franchise`), project/content version, typed facts and namespaced extensions.
- Every `ContinuityFact` carries a stable fact ID, namespace/key, JSON-compatible value, source authority/ref, content version and explicit state (`ACTIVE|STALE|MISSING|DELETED|CONFLICTED`).
- Snapshot identity is canonical JSON SHA-256 and independent of input fact ordering.
- `compare_snapshots()` emits stable finding IDs for additions, removals, value/source/state changes; missing/deleted/conflicted transitions are fail-closed errors.
- `ContinuityBridgePackage` binds a source project, target project, R8 artifact revision ID and exact snapshot digest.
- Import is validation-only and requires `promotion_policy=compare_only_no_canon_mutation`.

## Governance boundaries

R8 remains authoritative for artifact transport/lineage; R11.10 carries only the R8 revision identity. R2 Project DNA remains project intent authority. R11.11 owns Canon/Franchise promotion. R11.10 performs no durable canon mutation and no automatic conflict resolution.

No shell/runtime/network dependency is introduced. Cross-project fixtures are synthetic and path-free.

## Budgets

Snapshots are limited to 10,000 facts. IDs, namespaces and extension keys are bounded. Values must be finite JSON-compatible data. Duplicate fact IDs and unscoped extensions fail closed.

## Schemas

- `schemas/r11/continuity-snapshot.schema.json`
- `schemas/r11/continuity-diff.schema.json`
- `schemas/r11/continuity-bridge-package.schema.json`

## Manual state

**NONE.** Synthetic multi-project fixtures are authoritative for R11.10 acceptance.
