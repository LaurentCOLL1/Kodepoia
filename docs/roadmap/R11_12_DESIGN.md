# R11.12 — Persistence / SaveBridge design

## Scope

R11.12 adds a local-only, typed SaveBridge contract between runtime state and evolving schema/content versions. It does not implement cloud saves, account sync, DRM, anti-cheat authority or a new Canon authority.

## Save document

A SaveBridge document carries schema/project/franchise/content versions, an immutable Canon snapshot digest reference, runtime `state`, namespaced extensions and a SHA-256 checksum over every field except the checksum itself. Tampering, truncation, unknown top-level fields, non-finite JSON and oversized state fail closed.

Runtime save state remains distinct from Canon: migration functions can transform only the runtime state. Project/franchise identity and Canon snapshot digest are copied from the source document and cannot be rewritten by a migration step.

## Migration registry

Migrations are registered as trusted typed Python callables identified by stable step IDs and explicit source/target versions. No model-supplied code or string migration surface exists. The version graph rejects cycles; path search is deterministic and bounded to 16 steps. A newer unsupported schema returns `UNSUPPORTED_NEWER` and is never downgraded destructively by default.

## Durable migration transaction

`SaveBridgeStore` performs:

1. parse/checksum verification;
2. in-memory deterministic migration and dry-run digest report;
3. Guardian write authorization;
4. SafeChange snapshot of the exact save file;
5. verified `BackupManager` archive of the save directory;
6. RecoveryJournal `prepared` checkpoint;
7. atomic temporary-file replacement;
8. reparse/checksum/digest verification plus trusted post-write verifier;
9. Audit success and recovery clear.

Any exception after the write restores the exact prior bytes, records a `rolled_back` recovery checkpoint and appends a rollback audit event.

## Compatibility states

`COMPATIBLE`, `MIGRATION_REQUIRED`, `UNSUPPORTED_NEWER`, and `CORRUPT` are explicit. Missing migration paths never manufacture compatibility.

## Manual state

`CONDITIONAL NOT TRIGGERED` for this implementation. Acceptance is limited to synthetic SaveBridge/R5-compatible fixtures; no claim is made about a concrete existing user Godot save format, so no disposable-project local run is required.
