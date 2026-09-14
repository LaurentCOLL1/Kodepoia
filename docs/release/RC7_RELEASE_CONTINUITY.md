# Kodepoia 1.1.0-rc7 release continuity

Status: **PUBLISHED AND TUF-AUTHORIZED — AWAITING REAL WINDOWS HEALTH GATE**  
Synchronized: 2026-09-14 after TUF merge  
Canonical `main`: `bbcb4313108732a0be2e4828bf2be5cca747904d`

## Purpose

`1.1.0-rc7` is the corrective release candidate carrying the already-qualified updater PowerShell path transport and target-scoped TUF Authenticode-policy correction. It introduces no unrelated feature work.

Its purpose is to establish a healthy installed rc7 baseline before a later validation-only rc8 is used for the real updater E2E exercise.

## Exact source and installer authority

- rc7 qualification PR: `#458`;
- exact qualified source head: `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- release branch: `release/1.1.0-rc7-updater-corrective`;
- all 40 PR-triggered workflows on the exact source head completed successfully before merge;
- authoritative R17 installer length: `37734287` bytes;
- authoritative SHA-256: `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0`;
- qualified installer is genuinely unsigned (`production_signed: false`, no PE certificate table).

## Public release authority

GitHub release `v1.1.0-rc7` is public:

- release ID: `388454717`;
- draft: `false`;
- prerelease: `true`;
- tag/source: `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- asset: `KodepoiaSetup.exe`;
- asset ID: `563538713`;
- size: `37734287` bytes;
- digest: `sha256:c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0`.

The tag resolves directly to the exact qualified source.

## TUF authorization authority

TUF transition PR `#460` was qualified on exact head:

`4976ded7956e20e64e3abd3dffdd7b8fb58cc04d`

All 30 PR-triggered workflows on that exact head completed `success` before merge. The transition merged as:

`bbcb4313108732a0be2e4828bf2be5cca747904d`

Live generation:

- Root v2;
- Targets v7, expiry `2027-09-12T20:49:31Z`;
- Snapshot v9, expiry `2026-09-17T14:53:24Z`;
- Timestamp v9, expiry `2026-09-16T14:53:24Z`.

Targets v7 preserves rc3 through rc6 and adds exactly the rc7 target for source `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`, length `37734287`, SHA-256 `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0`, `withdrawn=false`, and:

```json
"authenticode_policy": "allow-unsigned"
```

This policy is target-scoped. Invalid, broken, untrusted, unknown or malformed signature states remain rejected.

## Current stop boundary

The next required action is the real Windows rc7 health gate. rc8 is not authorized yet.

Required checks:

1. install the exact public rc7 installer;
2. confirm the intended installation directory;
3. launch and confirm running version `1.1.0-rc7`;
4. invoke **Check for updates**;
5. confirm the previous PowerShell staging-path failure is absent;
6. confirm no TUF/AuthentiCode-policy/installer-identity error occurs;
7. stop and capture exact evidence if anything fails.

Do not begin rc8 until this gate succeeds.

## Later validation objective

After a healthy installed rc7 baseline is confirmed, rc8 may be created as a validation-only candidate. No new updater feature is permitted.

The incident closes only after the complete real-machine path succeeds:

`installed rc7 -> discover rc8 -> download -> verified TUF metadata -> exact length -> exact SHA-256 -> target-scoped Authenticode policy -> installer identity -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> search again`

The historical `rc5 -> rc6` attempt remains failed/incomplete and must not be retroactively marked successful.
