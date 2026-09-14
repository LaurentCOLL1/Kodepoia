# Kodepoia continuity state

Last synchronized: 2026-09-14 after rc7 publication/TUF authorization  
Repository: `LaurentCOLL1/Kodepoia`  
Canonical branch: `main`  
Canonical `main` SHA: `bbcb4313108732a0be2e4828bf2be5cca747904d`

## Immediate authority

Read this file together with `docs/continuity/NEXT.md` before any updater/release/TUF mutation.

The updater corrective path and rc7 publication are complete:

- updater corrective PR `#456` qualified and merged;
- rc7 qualification PR `#458` exact qualified source: `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- rc7 source merge on `main`: `3721c1e5aec7ded023bf158bb9c2cce0900fa7ad`;
- rc7 TUF transition PR `#460` exact qualified head: `4976ded7956e20e64e3abd3dffdd7b8fb58cc04d`;
- all 30 PR-triggered workflows on that TUF head completed `success` before merge;
- TUF transition merge on `main`: `bbcb4313108732a0be2e4828bf2be5cca747904d`;
- no failing verification was skipped, disabled or weakened.

## Public rc7 authority

GitHub prerelease `v1.1.0-rc7` is published and public:

- release ID: `388454717`;
- prerelease: `true`;
- draft: `false`;
- exact tag/source: `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- asset: `KodepoiaSetup.exe`;
- asset ID: `563538713`;
- exact length: `37734287` bytes;
- exact SHA-256: `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0`;
- qualified installer is intentionally unsigned (`production_signed: false`, PE certificate table absent).

The tag `v1.1.0-rc7` resolves directly to the exact qualified source above.

## Live TUF authority

The live metadata on `main` is now:

- Root v2;
- Targets v7, expiry `2027-09-12T20:49:31Z`;
- Snapshot v9, expiry `2026-09-17T14:53:24Z`;
- Timestamp v9, expiry `2026-09-16T14:53:24Z`.

Targets v7 preserves rc3 through rc6 and adds exactly rc7:

`channels/beta/windows-x86_64/1.1.0-rc7/fafe96ce45c4ca98ef5c40f50c596036071eb6f9/KodepoiaSetup.exe`

The rc7 target is bound to:

- length `37734287`;
- SHA-256 `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0`;
- `public_version = "1.1.0-rc7"`;
- `source_sha = "fafe96ce45c4ca98ef5c40f50c596036071eb6f9"`;
- `withdrawn = false`;
- `authenticode_policy = "allow-unsigned"`.

`allow-unsigned` is target-scoped. It only permits the exact `NotSigned` state for this exact TUF-authorized target. Invalid, broken, untrusted, unknown or malformed signature states remain fail-closed. TUF authorization, exact length, exact SHA-256 and installer identity/version remain mandatory.

Snapshot v9 references Targets v7 by version, length and hash. Timestamp v9 references Snapshot v9 by version, length and hash.

## Current manual boundary — real Windows rc7 health gate

The updater incident is **not closed** yet. Do not create rc8 until rc7 itself is installed and healthy on the real Windows machine.

Required manual gate:

1. install the exact public rc7 `KodepoiaSetup.exe`;
2. use/confirm the intended installation directory;
3. launch Kodepoia and confirm the running version reports `1.1.0-rc7`;
4. run **Check for updates** from the installed rc7 application;
5. confirm the updater no longer fails on the staged hidden `.KodepoiaSetup.exe.partial` path / spaces in the installation path;
6. confirm there is no PowerShell/AuthentiCode transport error and no TUF verification error;
7. record the exact observed result before any rc8 mutation.

If any step fails, stop and diagnose rc7. Do not start rc8.

## Later validation objective

Only after the rc7 health gate succeeds may rc8 be created. rc8 must be validation-only, with no new updater feature, and exists solely to exercise the repaired updater path from installed rc7.

The incident closes only after the real-machine path succeeds:

`installed rc7 -> discover rc8 -> download -> verified TUF metadata -> exact length -> exact SHA-256 -> target-scoped Authenticode policy -> installer identity -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> search again`

The historical `rc5 -> rc6` attempt remains failed/incomplete and must never be retroactively relabeled successful.

## Security invariants

- no unrelated feature work in rc7 or rc8;
- never mutate rc6 or rc7 assets in place;
- no weakening of TUF signature, threshold, rollback, expiry, version, length or hash verification;
- no unconditional unsigned acceptance;
- no shell interpolation of staged paths;
- no private TUF key, seed, passphrase, custody path or signing material in Git, GitHub logs, release assets, documentation or chat;
- re-fetch live release and metadata state at every publication/signing boundary;
- stop at each manual Windows, publication or custody-sensitive step rather than bypassing it.

## Resume rule

Before the next mutation:

1. read this file and `docs/continuity/NEXT.md`;
2. re-fetch live `main`, open PRs, rc7 release/tag/asset and Root/Targets/Snapshot/Timestamp;
3. confirm rc7 remains exactly `37734287` bytes with SHA-256 `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0` and tag/source `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
4. require explicit evidence that the real Windows rc7 health gate succeeded before any rc8 branch/version/release/TUF work;
5. if live state differs, live state wins and the discrepancy must be resolved first.
