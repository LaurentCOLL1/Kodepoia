# R14.5 — PostgreSQL authoritative persistence acceptance

## Acceptance authority

This ledger records R14.5 only. It must not claim managed-cloud provisioning, production credentials, production backup/DR or PostgreSQL 19 readiness.

## Stable external baseline

- PostgreSQL major authority: 18.x stable.
- Current patch release researched for this work cycle: PostgreSQL 18.6, released 2026-08-13.
- PostgreSQL 19 is pre-release and is not production authority for this subdivision.

## Implemented surface

- `src/kodepoia/backend/postgres.py`
  - secret-reference-only connection policy;
  - PostgreSQL version/capability snapshot;
  - migration identities, SQL checksums, prefix-stable schema digests and drift checks;
  - transactional apply / rollback ledger;
  - explicit isolation and bounded retry policy;
  - optimistic concurrency and row-lock helpers;
  - digest-bound idempotency claims;
  - deterministic semantic snapshot/restore evidence.
- `scripts/r14_5_postgres_acceptance.py`
  - real PostgreSQL 18 integration acceptance.
- `.github/workflows/r14-postgresql-acceptance.yml`
  - exact-head PostgreSQL 18 CI service gate.
- strict R14 JSON Schemas for migration-plan and acceptance evidence.
- focused unit/adversarial regression tests.

## Required technical acceptance

The immutable technical candidate must pass, on the exact same source SHA:

1. R0 Repository Guard — Ubuntu + Windows;
2. full Python Core — Ubuntu + Windows, package builds and internal UI smoke;
3. KodeStudio UI Smoke — Windows;
4. R14 PostgreSQL Acceptance — real PostgreSQL 18 service, exact-head evidence.

The PostgreSQL gate must report all checks true:

- `fresh_apply`;
- `rollback_reapply`;
- `atomicity`;
- `optimistic_conflict`;
- `row_lock`;
- `idempotency`;
- `bounded_retry` (real `40P01` deadlock observed plus bounded retry helper proof);
- `backup_restore`.

Evidence must validate against `schemas/r14/backend-postgres-evidence.schema.json`, bind the exact source SHA, report server major 18 and `secrets_exposed=false`.

## Security / regression assertions

- No DSN appears in canonical models or persisted evidence.
- SQL identifiers accepted by generic helpers are repository-governed stable identifiers, not free-form project/model SQL.
- Migration checksum/identity drift blocks forward and rollback paths.
- Failed migration/transaction state is rolled back.
- Only `40P01` and `40001` are retryable in the generic transaction helper.
- Retry count and backoff are bounded.
- A stale optimistic writer cannot overwrite a newer revision.
- An idempotency key cannot be rebound to a different request digest.
- PostgreSQL 19 pre-release cannot satisfy the stable R14.5 capability claim.

## Technical evidence

- Immutable source SHA: `3273ac50b43b64f6f365522f170765f44f45eedf`.
- R0 Repository Guard #1787 / `33190672723`: SUCCESS on Ubuntu and Windows.
- Python Core #1761 / `33190672676`: SUCCESS; Ubuntu full suite 1509 passed / 13 skipped / 46 warnings; Windows Core, both package builds and internal UI smoke also SUCCESS.
- KodeStudio UI Smoke #1728 / `33190672761`: SUCCESS.
- R14 PostgreSQL Acceptance #1 / `33190672769`: SUCCESS against PostgreSQL 18.6 (`server_version_num=180006`, `stable_supported=true`).
- Focused PostgreSQL gate: 44 tests passed.
- Functional checks: `fresh_apply=true`, `rollback_reapply=true`, `atomicity=true`, `optimistic_conflict=true`, `row_lock=true`, `idempotency=true`, `bounded_retry=true`, `backup_restore=true`.
- PostgreSQL server logs confirm a real `40P01` deadlock was generated and detected during acceptance.
- Migration-plan digest: `b96484ae6d56fe54b013b975572310d8daf44cf43116c5c43edc73845856b71b`.
- Restore digest: `bcc5ae8b707231568263e0f52c8426dd956a67e4e131bcf97becb4b45ccb9f6e`.
- Evidence is bound to the immutable source SHA, validates against the Draft 2020-12 evidence schema and reports `secrets_exposed=false`.
- Manual intervention: NONE.

## END synchronization

After technical acceptance, only `docs/roadmap/R14_PLAN.md`, this ledger and `docs/continuity/KODEPOIA_CONTINUITY.md` may change before the final re-gates. The implementation/evidence PR then merges with expected-head protection, followed by exactly one continuity-only post-merge normalization before R14.6 starts.

## Manual intervention

**NONE.** Hosted CI PostgreSQL 18 is sufficient for core acceptance.
