# R14.5 — PostgreSQL authoritative persistence design

## Status

Implementation design for R14.5. Core acceptance requires a real hosted CI PostgreSQL **18.x stable** instance and no manual provider account.

## Authority boundary

PostgreSQL is the multi-writer transactional authority for R14 services that require durable server state. SQLite remains valid for R12 local desktop persistence, but it is not promoted as the production authority for concurrent backend writers.

The database connection value is resolved at runtime from `PostgresSecretRef`. The DSN is never stored in Project DNA, generated evidence, canonical payloads, logs or `repr` output.

## Connection policy

`PostgresConnectionPolicy` binds:

- environment identity;
- secret reference only;
- bounded connect/statement/lock/idle-transaction timeouts;
- bounded connection budget;
- explicit application identity;
- optional TLS requirement.

Session timeout settings are supplied as libpq connection options so transaction isolation can be selected before application statements execute.

## Stable version policy

The accepted current production family is PostgreSQL 18.x. Capability probing records `server_version_num` and the server version string. Major 18 is `AVAILABLE`; older majors are `UNSUPPORTED` for the R14.5 authority claim; a newer pre-release major is not silently promoted and remains non-authoritative until a later accepted compatibility update.

Current external baseline on 2026-08-28: PostgreSQL 18.6 was released 2026-08-13; PostgreSQL 19 remains pre-release.

## Migration lineage

Every `PostgresMigration` owns:

- stable migration ID and contiguous sequence;
- human description;
- forward SQL SHA-256;
- rollback SQL SHA-256.

SQL bodies are repository source, not evidence payloads. The migration ledger stores identity, sequence, forward checksum and a **prefix schema digest**. Prefix digests remain stable when a later migration is appended. Drift in ID, order, checksum or prefix digest blocks apply/rollback.

A failed migration transaction is rolled back and must never be recorded as applied.

## Transactions and concurrency

`PostgresTransactionPolicy` exposes explicit isolation and bounded retry count/backoff. Only PostgreSQL deadlock (`40P01`) and serialization (`40001`) states are retryable by the generic transaction helper. Other failures propagate immediately.

Optimistic updates require an expected version and atomically increment the version only when it matches. A stale writer receives `PostgresConcurrencyError`. Pessimistic access uses `SELECT ... FOR UPDATE` through validated repository-owned identifiers.

## Idempotency

Idempotency keys are scoped and request-digest-bound. First claim wins. Repeating the same key with the same request digest is a duplicate-safe no-op; reusing the key for a different digest is rejected.

## Backup / restore fixture

R14.5 does not claim that a test JSON snapshot replaces production PostgreSQL physical/logical backup tooling. The deterministic fixture snapshot proves the Kodepoia **semantic restore contract**: ordered authoritative rows + schema digest are exported to a canonical hash-bound payload, restored, and re-read to an identical semantic digest.

Production backup/DR orchestration remains in R14.15.

## Acceptance topology

`.github/workflows/r14-postgresql-acceptance.yml` provisions the official `postgres:18` service container on Ubuntu, checks out the exact PR head SHA, installs the optional `postgres` capability, and proves:

1. PostgreSQL 18 capability probe;
2. fresh migration apply;
3. rollback and reapply;
4. transaction atomicity;
5. optimistic conflict rejection;
6. row lock semantics;
7. idempotency duplicate/conflict semantics;
8. an actual PostgreSQL deadlock with SQLSTATE `40P01`;
9. bounded adapter retry for a retryable transaction state;
10. semantic backup/restore digest equivalence;
11. strict JSON Schema evidence validation with no exposed secret.

R0, full Python Core and KodeStudio UI Smoke remain separate required exact-head gates.

## Out of scope

- managed PostgreSQL provisioning;
- production DSNs/passwords/certificates;
- cloud-provider backup products;
- product-specific gameplay/application tables;
- PostgreSQL 19 pre-release production claims;
- silent destructive migration or automatic production promotion.

## Manual intervention

**NONE** for core R14.5 acceptance. The CI PostgreSQL service is sufficient and authoritative for the claimed capability.
