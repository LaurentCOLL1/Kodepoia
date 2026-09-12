# Kodepoia — Current Authority

**Current state:** R1–R20 COMPLETE + NORMALIZED; R20 terminal; no R20.7 authorized.

This compact file is the current-state entry point after the completion of R20. It does not replace immutable historical phase evidence. It exists to prevent old current-state wording inside the large legacy continuity archive from being mistaken for the present release/update state.

## Current repository and release

- Repository: `LaurentCOLL1/Kodepoia`.
- Current public beta prerelease: **`v1.1.0-rc4`**.
- Exact rc4 source/tag target: `42e58b6b9c00d53c27e005020d6e99688958ee3a`.
- Accepted Windows installer: `KodepoiaSetup.exe`.
- Installer size: `37,713,467` bytes.
- Installer SHA-256: `54f751593b86d62eec50ea6852cc8683f0154d8645f9d98b84ccc6319ba058ee`.
- Installer claim: `production_signed=false`; rc4 is a prerelease/beta, not a production-signed stable release.
- Fresh Root bootstrap correction: PR #438, accepted head `841fa729f9743a47e26ea489affda0ef418aea09`, merge `aeea4a3fd2da2bca25f4c8126d496e241b8823d6`.
- rc4 identity/rebuild: PR #439, exact source `42e58b6b9c00d53c27e005020d6e99688958ee3a`, merge `5757cf28981fa70a89e39c3456302f90cc06e031`.
- Atomic rc4 TUF transition: PR #440, exact transition head `d61240bbca6b7a85b2fdfdb9442b6beac0a8ce7f`, merge/current pre-doc-normalization main `575aa74d3f3109989d39322dbc12cab8cb912ca7`.

## Current TUF generation

- Root: **v2**, SHA-256 `c92b2165bcbf39f74599fbdf8cc30e203f8c93cc2f24c5c74012821646850ee7`, threshold 2-of-3, expiry `2027-09-08T14:59:19Z`.
- Targets: **v4**, SHA-256 `9db8604cd2e9fc3de052ad01c0f25727650b2b4c410ed2383cd911de183282ba`, length `1677`, expiry `2027-09-12T06:08:24Z`, offline keyid `70e86d478a769ffbefbf6febc37435a2a4563197df03d6dcda6627282fa5cf00`.
- Snapshot: **v6**, SHA-256 `5d636b3d9ad81f5bb533a13b790e18873736f70cdf38e43f939c8740731e5fb9`, length `469`, expiry `2026-09-15T06:22:35Z`, online keyid `fac1c790b4d6dbeb04ca4a803bd80e6fde19127fc7ada34003cef5d6b50506d8`.
- Timestamp: **v6**, SHA-256 `03fb5f4c31c48ab5bc43d89178e5c805b54b1f519df193d03cf01ee75bed2463`, length `470`, expiry `2026-09-14T06:22:35Z`, distinct online keyid `8d81006fd9de63660d74c43b6926ed664b2e9f1bdf81a9556367232533d5a2ad`.
- Targets v4 preserves rc3 and authorizes rc4. Snapshot v6 binds exact Targets v4 bytes/version/hash/length. Timestamp v6 binds exact signed Snapshot v6 bytes/version/hash/length.
- Root/Targets private custody remains outside Git/repository/CI. Snapshot/Timestamp are low-authority distinct online signing roles.

## Continuity hierarchy

Use the following documents in this order when interpreting current state:

1. this file for the latest cross-phase/public-release state;
2. `docs/continuity/KODEPOIA_CONTINUITY_R20.md` for terminal R20 authority and post-R20 release operations;
3. `docs/continuity/KODEPOIA_CONTINUITY_R19.md` for frozen R19 authority;
4. `docs/continuity/KODEPOIA_CONTINUITY.md` for the large historical R1–R18 continuity archive;
5. phase plans and Git history for immutable phase-specific evidence.

The large legacy continuity archive intentionally remains historical; stale “current” wording inside older sections is superseded by this file and the phase-specific latest-state sections, not rewritten retroactively.

## Terminal boundary

R20 is **COMPLETE + NORMALIZED**. Post-R20 rc3/rc4 publication, bootstrap correction and TUF-generation changes are release operations built on the completed R20 machinery. They do **not** create R20.7, reopen R20, or authorize a second R20 phase normalization.
