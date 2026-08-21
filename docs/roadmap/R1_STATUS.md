# R1 — KodeStudio minimal + Protected Core — Status

**Phase:** R1  
**Status:** COMPLETE  
**Completed:** 2026-08-21

## Validation evidence

- PR #3 — `R1: implement Protected Core and minimal KodeStudio`.
- Merge commit: `df324b1ad2a9b08fdc116eec0ff761c791e0c546`.
- `Python Core`: SUCCESS on Windows and Ubuntu.
- `R0 Repository Guard`: SUCCESS on Windows and Ubuntu.

## Implemented

- [x] R1.1 KodeGuardian deterministic policy engine and risk decisions.
- [x] R1.2 KodePermissions capability/path/executable scopes.
- [x] R1.3 KodeAudit append-only JSONL hash chain.
- [x] R1.4 KodeSafeChange project-boundary checks and snapshots.
- [x] R1.5 KodeSandbox restricted subprocess launcher (no shell, cwd boundary, executable allowlist, clean env, timeout).
- [x] R1.6 KodeSecrets OS-keyring adapter + test backend + redaction.
- [x] R1.7 KodeSchema version registry and migrations.
- [x] R1.8 KodeDataGovernance project/global/training/confidential controls.
- [x] R1.9 KodeBackup ZIP snapshots.
- [x] R1.10 KodeRecovery durable task checkpoint journal.
- [x] R1.11 KodeResearchGuard indirect-prompt-injection indicators and untrusted-data wrapper.
- [x] R1.12 KodeStudio minimal optional PySide6 desktop shell.
- [x] Cross-platform Python 3.12 CI on Windows and Ubuntu.

## Security boundary note

The R1 `ProcessSandbox` is intentionally a restricted subprocess launcher, not a claim of full OS/container isolation. Stronger OS isolation remains an adapter behind the KodeSandbox boundary and can be hardened without changing the frozen architecture.
