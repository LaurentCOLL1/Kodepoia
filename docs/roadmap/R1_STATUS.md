# R1 — KodeStudio minimal + Protected Core — Status

**Phase:** R1  
**Status:** IMPLEMENTED — awaiting PR validation/merge  
**Date:** 2026-08-21

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

The R1 `ProcessSandbox` is intentionally documented as a restricted subprocess launcher, not as a claim of full OS/container isolation. It already enforces the application-layer controls required by R1. Stronger OS isolation remains an adapter behind KodeSandbox and can be hardened without changing the frozen architecture.

## Acceptance

The phase is complete when the R1 PR passes `Python Core` and the existing `R0 Repository Guard` on both Windows and Ubuntu, then merges into `main`.
