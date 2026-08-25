# R12.10 — Acceptance

## Scope

Framework-neutral governed SQLite persistence: versioned schema contracts, typed migration graph, parameterized data intents, transactions, integrity/busy policy, online backup, deterministic recovery and SafeChange/Backup/Recovery/Audit integration.

Manual intervention: **NONE**.

## Required acceptance

- schema/model version is explicit and canonical contract serialization yields a deterministic SHA-256 digest;
- identifiers are validated and SQL structure is generated only from typed contracts;
- application values use DB-API placeholders; raw model-supplied SQL is not an execution surface;
- `PRAGMA foreign_keys=ON`, bounded `busy_timeout`, explicit transaction commit/rollback and `quick_check` integrity state are enforced;
- migration graph is bounded and rejects duplicate edges, cycles, missing paths, source-digest mismatch and tampered step checksum;
- dry-run migration returns versions, ordered step checksums and destructive state without mutation;
- database states distinguish absent, ready, migration-required, corrupt, incompatible and newer-schema;
- SQLite online backup is integrity-checked and checksum-bound for migration/crash recovery;
- a failed migration restores the accepted pre-state and never advances its schema version;
- destructive migration/import integrates existing SafeChange, BackupManager, RecoveryJournal and AuditLog boundaries;
- import requires SQLite integrity plus exact target schema version/digest;
- focused R12.10 tests plus exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke succeed; adapter regression workflows triggered by the PR remain green.

## Web-researched implementation basis

- Python `sqlite3.Connection.backup()` is the canonical database backup primitive and is designed to operate with concurrent access;
- SQLite Online Backup API documents `SQLITE_BUSY`/`SQLITE_LOCKED` as retryable lock states and busy-timeout handling;
- Python DB-API placeholders are required for untrusted values rather than string-formatted SQL.

## Evidence state

Base normalized `main`: `136967485e063254904269578f9ab4be23e5d599`.
Branch: `r12/10-sqlite-persistence`.
PR: #205.
Manual state: **NONE**.

Accepted implementation candidate: `464be11dd9c889336cac20208fc3fb9728ccac5f`.

Exact-head workflow evidence on that candidate:

- R0 Repository Guard #1544 / run `32818839673` — SUCCESS;
- Python Core #1518 / run `32818839682` — SUCCESS;
- KodeStudio UI Smoke #1485 / run `32818839667` — SUCCESS;
- R12 WPF Acceptance #45 / run `32818839654` — SUCCESS;
- R12 WinUI3 Acceptance #35 / run `32818839609` — SUCCESS;
- R12 Avalonia Acceptance #31 / run `32818839711` — SUCCESS;
- R12 Qt6 Acceptance #26 / run `32818839626` — SUCCESS;
- R12 Tauri2 Acceptance #17 / run `32818839625` — SUCCESS.

The focused R12.10 suite is `tests/test_desktop_r12_10.py` and is exercised by Python Core. No separate R12.10 hosted runtime workflow is required because R12.10 is framework-neutral and its frozen manual state is NONE.

This evidence-recording change modifies documentation bytes. The resulting final documentation HEAD must therefore pass a fresh exact-head standard gate set plus the adapter regression workflows before PR #205 may merge with `expected_head_sha`.

## Merge / normalization rule

Freeze one immutable implementation head and require exact-head gates. Record accepted run IDs in this document and continuity, then re-gate the final documentation head because bytes changed. Merge with `expected_head_sha`, perform exactly one continuity-only post-merge normalization, gate that exact head and merge it. R12.11 remains forbidden until R12.10 normalization merges.
