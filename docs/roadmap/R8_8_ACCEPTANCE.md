# R8.8 — Git LFS tracking, pointer/object integrity + diagnostics — Candidate acceptance

**Status:** CANDIDATE / PENDING EXACT-HEAD CI  
**Manual intervention:** CONDITIONAL — candidate expects NOT TRIGGERED

## Implemented scope

- Independent strict Git LFS v1 pointer parser with canonical `version`, SHA-256 OID, exact size and ordered extension evidence; malformed/non-canonical pointers fail closed.
- Fixed local-only `git lfs version`, `git lfs ls-files --name-only` and `git lfs fsck --objects --dry-run` diagnostics through `ProcessSandbox`; no fetch/pull/push or hidden network operation is exposed.
- `.gitattributes` tracking inspection and frozen heavy-asset policy diagnostics; path-level effective attributes are checked with fixed `git check-attr`.
- Safe tracking-rule proposal/update is restricted to the accepted heavy-asset pattern set, requires explicit confirmation, snapshots `.gitattributes` through `SafeChangeManager`, writes atomically and audits the mutation.
- Index pointers are bounded before content read; valid pointer, malformed pointer, missing local object, local object mismatch, hydrated match/mismatch and pointer-only working states remain distinct.
- Default local object verification is confined to the authorized repository's Git common directory; a storage location outside the workspace is surfaced as `UNAVAILABLE` rather than escaped.
- Current Kodepoia `.gitattributes` heavy-asset policy is regression-tested.

## Manual gate expectation

The R8.8 manual gate remains CONDITIONAL. It is expected to be **NOT TRIGGERED** because Git LFS availability is already an authoritative R0 requirement on hosted Ubuntu and Windows, and R8.8 acceptance needs no real remote LFS upload/fetch. If exact-head CI cannot prove the local LFS capability/integrity path, stop before R8.9 and require only the documented disposable-repository local acceptance evidence; never request credentials, remote URLs or model files.

## Acceptance gates

R0 Repository Guard, full Python Core and KodeStudio UI Smoke must all succeed on one exact implementation head before merge. Post-merge normalization must complete before R8.9 begins.
