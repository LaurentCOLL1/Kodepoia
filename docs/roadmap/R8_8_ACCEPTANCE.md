# R8.8 — Git LFS tracking, pointer/object integrity + diagnostics — Acceptance

**Status:** COMPLETE / ACCEPTED  
**Manual intervention:** CONDITIONAL NOT TRIGGERED

## Accepted implementation

- Exact implementation head: `32e5ace263546d85ee662c5ba333caaaefaa8bcc`.
- PR: #95.
- Merge SHA: `8923f6aa75656033887dd93551fc7b2651d78f04`.
- Rejected precursor: `6b02a22fb4c526a53579a96e81ade3a3088a5e88` — fixture re-staged malformed pointer through active LFS filtering; not accepted.

## Authoritative CI on the exact head

- R0 Repository Guard #1066 / `32604356727`: SUCCESS Ubuntu + Windows, including authoritative `git lfs version` availability checks.
- Python Core #1040 / `32604356661`: SUCCESS 5/5.
- Ubuntu authoritative suite: `558 passed / 5 skipped / 46 warnings`.
- KodeStudio UI Smoke #1007 / `32604356692`: SUCCESS.

## Accepted scope

- Independent strict Git LFS v1 pointer parser with canonical `version`, SHA-256 OID, exact size and ordered extension evidence; malformed/non-canonical pointers fail closed.
- Fixed local-only `git lfs version`, `git lfs ls-files --name-only` and `git lfs fsck --objects --dry-run` diagnostics through `ProcessSandbox`; no fetch/pull/push or hidden network operation is exposed.
- `.gitattributes` tracking inspection and frozen heavy-asset policy diagnostics; path-level effective attributes are checked with fixed `git check-attr`.
- Safe tracking-rule proposal/update is restricted to the accepted heavy-asset pattern set, requires explicit confirmation, snapshots `.gitattributes` through `SafeChangeManager`, writes atomically and audits the mutation.
- Index pointers are bounded before content read; valid pointer, malformed pointer, missing local object, local object mismatch, hydrated match/mismatch and pointer-only working states remain distinct.
- Default local object verification is confined to the authorized repository's Git common directory; storage outside that workspace is explicit `UNAVAILABLE` rather than escaped.
- Current Kodepoia `.gitattributes` heavy-asset policy is regression-tested.

## Rejected precursor

The first candidate `6b02a22fb4c526a53579a96e81ade3a3088a5e88` produced `1 failed, 557 passed, 5 skipped, 46 warnings` because the malformed-pointer fixture re-staged its working file through the active LFS clean filter. The filter retained/canonicalized the prior valid pointer in the index. The accepted correction writes exact fixture blobs with `git hash-object` + `git update-index`; production diagnostics were not weakened.

## Manual gate outcome

The conditional manual gate was **NOT TRIGGERED**. R0 already verifies Git LFS availability on both hosted Ubuntu and Windows, all R8.8 integrity behavior is exercised without a remote transfer, and authoritative exact-head CI passed. No user-side command, credential, remote URL or LFS server operation was required.
