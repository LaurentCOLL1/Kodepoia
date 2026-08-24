# R11.11 — Franchise DNA + versioned Canon design

## Scope

R11.11 implements the frozen Franchise DNA and Canon layer on top of normalized R11.10. It does not replace R2 Project DNA, R7 ResearchGuard, R8 provenance, or R1 Guardian/SafeChange/Audit.

## Contracts

- `FranchiseDNA` is a multi-project compatibility/invariant contract. It references compatible Project DNA identities but is not itself a Project DNA document.
- `CanonRecord` is immutable, source-referenced and versioned. Durable updates create new records/snapshots rather than silently rewriting historical facts.
- `CanonSnapshot` has deterministic canonical JSON/SHA-256 identity and an optional `previous_snapshot_digest` chain.
- Authority tiers are `RESEARCH < PROJECT < FRANCHISE`.
- Workflow is one-way: `PROPOSED -> REVIEWED -> CANONICAL -> DEPRECATED`.
- `RESEARCH` authority can be proposed/reviewed but can never transition to `CANONICAL` directly. This keeps R7 external research advisory.

## Conflict policy

Canonical records sharing subject/predicate and overlapping validity are compared structurally. Different values at equal highest authority are `CONFLICTED` and queries fail closed. A higher authority record may be selected deterministically over a lower-authority value, while a `SHADOWED_BY_HIGHER_AUTHORITY` finding remains visible. No arbitrary winner is selected when highest authority is ambiguous.

Supersession/deprecation relations are bounded, self-links and missing targets are rejected, and relation cycles are forbidden.

## Durable promotion boundary

`CanonRepository` uses existing foundations only:

1. `KodeGuardian` authorizes the write against `PermissionSet` roots.
2. `SafeChangeManager` snapshots the prior target before durable mutation.
3. Canon JSON is written atomically through a temporary sibling file.
4. `AuditLog` appends a tamper-evident event containing the snapshot digest and backup identity.

There is no second permission, backup or audit system.

## Schema baseline

Schemas use JSON Schema Draft 2020-12 and are self-contained/offline. Canonical JSON excludes timestamps and other volatile fields from identity.

## Manual state

`NONE`. Synthetic franchise/canon fixtures are authoritative for R11.11 acceptance.
