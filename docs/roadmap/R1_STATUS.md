# R1 — KodeStudio minimal + Protected Core — Status

**Phase:** R1  
**Status:** COMPLETE ON R1–R3 HARDENING BRANCH  
**Accepted:** 2026-08-21

## Validation evidence

Original implementation:
- PR #3 — `R1: implement Protected Core and minimal KodeStudio`.
- Merge commit: `df324b1ad2a9b08fdc116eec0ff761c791e0c546`.

Acceptance hardening:
- PR #8 — `R1-R3 Acceptance Hardening` (still open while R3 hardware-local acceptance is pending).
- Validated hardening commit: `e2cc5cb624e14c459b92fd9128343c8e2b4a1d1f`.
- `R0 Repository Guard` run `32456258458`: SUCCESS on Windows and Ubuntu.
- `Python Core` run `32456258437`: SUCCESS on Windows and Ubuntu; Windows KodeStudio smoke job SUCCESS.
- `KodeStudio UI Smoke` run `32456258443`: SUCCESS on Windows.

## Implemented and accepted

- [x] R1.1 KodeGuardian deterministic policy engine and risk decisions.
- [x] R1.2 KodePermissions capability/path/executable scopes.
- [x] R1.3 KodeAudit append-only JSONL hash chain.
- [x] R1.4 KodeSafeChange project-boundary checks and snapshots.
- [x] R1.5 KodeSandbox restricted and interruptible subprocess launcher.
- [x] R1.6 KodeSecrets OS-keyring adapter + test backend + redaction.
- [x] R1.7 KodeSchema version registry and migrations.
- [x] R1.8 KodeDataGovernance project/global/training/confidential controls.
- [x] R1.9 KodeBackup SHA-256 manifest, archive verification and verified restore.
- [x] R1.10 KodeRecovery atomic durable checkpoint journal + simulated restart/resume test.
- [x] R1.11 KodeResearchGuard indirect-prompt-injection indicators and untrusted-data wrapper.
- [x] R1.12 KodeStudio minimal optional PySide6 desktop shell.
- [x] Global KillSwitch shared by KodeStudio and ProcessSandbox.
- [x] Active protected subprocesses can be terminated and new execution is refused until reset.
- [x] KodeStudio emergency STOP is covered by an offscreen Windows UI smoke test.
- [x] Cross-platform Python 3.12 CI on Windows and Ubuntu.

## Security boundary note

The R1 `ProcessSandbox` is intentionally a restricted subprocess launcher, not a claim of full OS/container isolation. Stronger OS isolation remains an adapter behind the KodeSandbox boundary and can be hardened without changing the frozen architecture.

## Merge note

R1 is accepted on `agent/r1-r3-acceptance-hardening`, but the PR is intentionally not merged yet because the same PR contains R3 hardening and R3 still requires hardware-local model acceptance on the target workstation.
