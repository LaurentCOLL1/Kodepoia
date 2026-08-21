# R1 — KodeStudio minimal + Protected Core — Status

**Phase:** R1  
**Status:** IN PROGRESS  
**Started:** 2026-08-21

## Steps

- [x] R1.1 — KodeGuardian decision gate + global kill switch
- [x] R1.2 — KodePermissions default-deny capability policy
- [x] R1.3 — KodeAudit append-only JSONL journal
- [x] R1.4 — KodeSafeChange atomic changes + pre-image snapshots
- [x] R1.5 — KodeSandbox allowlist/cwd/env/timeout boundary behind Guardian
- [x] R1.6 — KodeSecrets broker + Windows Credential Manager backend + redaction
- [x] R1.7 — KodeSchema versioned validation + deterministic migration chain
- [x] R1.8 — KodeDataGovernance classification and movement policy
- [x] R1.9 — KodeBackup local snapshots + SHA-256 integrity + guarded restore
- [x] R1.10 — KodeRecovery atomic task checkpoints + pending-task discovery
- [x] R1.11 — KodeResearchGuard untrusted envelopes + injection indicators
- [ ] R1.12 — KodeStudio minimal

## Security invariant for research

Web/GitHub/YouTube/document content can be useful evidence but has `instruction_authority = none` permanently. Pattern flags are diagnostics only; even unflagged external content remains untrusted data and cannot directly authorize an action.

## Sandbox note

R1 provides a real capability/process boundary (argv-only, `shell=False`, executable allowlist, cwd roots, stripped environment, timeout and kill support). It does not falsely claim OS/VM network isolation; stronger Windows isolation backends can replace this backend later through the same interface.

## Acceptance targets

- forbidden action is actually denied;
- risky action requires explicit confirmation;
- secrets are never exposed to KodeBrain;
- generated/downloaded process execution crosses Guardian + Sandbox;
- destructive file change uses recoverable pre-image protection;
- interrupted tasks have atomic checkpoints;
- external research is permanently marked non-authoritative;
- minimal KodeStudio exposes Projects, Chat, Security, Audit and Settings plus a kill switch;
- R1 unit tests pass on Windows and Ubuntu;
- KodeStudio offscreen smoke test passes on Windows.
