# Kodepoia continuity state

Last synchronized: 2026-09-14 after exact-head rc8 qualification and source merge  
Repository: `LaurentCOLL1/Kodepoia`  
Canonical branch: `main`  
Canonical `main` SHA at this checkpoint: `9554dbf3968360a61c2b6392398502572bf8f198`

## Immediate authority

Read this file together with `docs/continuity/NEXT.md` before any updater/release/TUF mutation and re-fetch live GitHub state before acting.

The updater corrective path, rc7 publication/TUF authorization, rc7 discovery health gate, rc8 exact-head qualification, rc8 source merge, and exact rc8 R17 installer binding are complete. The active stop boundary is now **manual creation of the unpublished rc8 GitHub draft release**.

No new updater feature or unrelated product work is authorized in rc8. The historical `rc5 -> rc6` attempt remains failed/incomplete and must never be relabeled successful.

## Completed rc7 authority

- updater corrective PR `#456` qualified and merged;
- rc7 exact qualified source: `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- public prerelease: `v1.1.0-rc7`, release ID `388454717`;
- rc7 installer asset ID `563538713`;
- rc7 installer length: `37734287` bytes;
- rc7 installer SHA-256: `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0`;
- rc7 installer is genuinely unsigned;
- rc7 target-scoped policy: `authenticode_policy = "allow-unsigned"`;
- rc7 TUF transition PR `#460` merged as `bbcb4313108732a0be2e4828bf2be5cca747904d` after qualification and public asset re-verification;
- real Windows rc7 UI evidence confirms healthy Beta discovery from `tuf-verified-metadata` with no PowerShell/AuthentiCode/TUF/installer-identity error.

The full repaired staged-download path remains unproven until the real installed rc7 -> rc8 E2E succeeds.

## Live TUF authority before rc8

Last revalidated live generation:

- Root v2;
- Targets v7, expiry `2027-09-12T20:49:31Z`;
- Snapshot v9, expiry `2026-09-17T14:53:24Z`;
- Timestamp v9, expiry `2026-09-16T14:53:24Z`.

Targets v7 preserves rc3 through rc6 and authorizes rc7 at:

`channels/beta/windows-x86_64/1.1.0-rc7/fafe96ce45c4ca98ef5c40f50c596036071eb6f9/KodepoiaSetup.exe`

`allow-unsigned` is target-scoped and accepts only the exact PowerShell Authenticode state `NotSigned` for an otherwise exact TUF-authorized target. Invalid, broken, untrusted, unknown or malformed states remain fail-closed. Exact TUF length/SHA and installer identity are still mandatory.

## rc8 exact-source qualification — COMPLETE

Qualified source authority:

- PR `#462`: `Release 1.1.0-rc8 — validation-only candidate`;
- exact qualified source: `fa787ab7ef76f2556b56ac1f058916a1425455af`;
- creation base: `c61347993af70f9167d08f2ff5e46f33f7686b4e`;
- source diff was exactly two release-identity edits: `1.1.0rc7 -> 1.1.0rc8` and serial `7 -> 8`;
- exactly 40 PR-triggered workflows were re-fetched for this exact SHA;
- all 40 were `completed` with conclusion exactly `success`;
- the final long gates `R18.2 Deterministic Release Bundle Acceptance`, `R17 Windows Installer`, and `R18.11 Integrated Adversarial Release Update Acceptance` all completed `success`;
- R18.11 completed its isolated R17 fixture, clean install/update/packaged smoke/uninstall, final verdict and evidence upload successfully;
- no failed, skipped, neutral, cancelled or otherwise non-success run was accepted as green.

PR #462 was merged only after that terminal 40/40 revalidation and with `expected_head_sha` pinned to the exact qualified source.

Source merge:

- `main`: `9554dbf3968360a61c2b6392398502572bf8f198`;
- merge parents: previous `main` `c61347993af70f9167d08f2ff5e46f33f7686b4e` and exact qualified source `fa787ab7ef76f2556b56ac1f058916a1425455af`.

The release/tag must bind to the exact qualified **source** `fa787ab7...`, not to the later merge commit.

## rc8 exact R17 installer authority — COMPLETE

Authoritative exact-source build:

- workflow: `R17 Windows Installer`;
- run ID: `34871154670`;
- Actions artifact: `KodepoiaSetup-Windows`;
- artifact ID: `10360685910`;
- file: `KodepoiaSetup.exe`;
- public version: `1.1.0-rc8`;
- source SHA: `fa787ab7ef76f2556b56ac1f058916a1425455af`;
- exact length: `37730750` bytes;
- exact SHA-256: `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`;
- manifest: `production_signed = false`;
- PE Security Directory: absent, so the exact installer is genuinely unsigned.

Derived exact target-scoped policy for this artifact:

```json
"authenticode_policy": "allow-unsigned"
```

The corrective updater contract was re-checked: `allow-unsigned` accepts only exact `NotSigned`; length and SHA are checked before Authenticode, then installer identity is checked, and installer launch still requires explicit user consent.

## rc8 GitHub release state — NOT YET CREATED

At the latest live check:

- release `v1.1.0-rc8`: absent (`404`);
- Git ref `refs/tags/v1.1.0-rc8`: absent (`404`).

Therefore no rc8 public effect has occurred and the next boundary is clean.

## ACTIVE STOP BOUNDARY — manual unpublished rc8 draft

The repository release discipline and the previous rc7 flow require draft-first publication. Draft creation/upload is a manual publication boundary; do not simulate or bypass it.

The draft must be created with exactly:

- tag: `v1.1.0-rc8`;
- target: exact qualified source `fa787ab7ef76f2556b56ac1f058916a1425455af`;
- title: `Kodepoia 1.1.0-rc8`;
- draft: `true`;
- prerelease: `true`;
- exactly one installer asset: `KodepoiaSetup.exe`;
- expected asset length: `37730750` bytes;
- expected asset SHA-256: `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`.

Do **not** publish the draft yet.

After the user creates the draft and uploads the exact installer, re-fetch the draft and require exact tag/source, draft/prerelease flags, asset name, size and GitHub digest before preparing any TUF authorization.

## Required TUF sequence after exact draft verification

While the rc8 release remains unpublished draft:

1. prepare the rc8 target at:
   `channels/beta/windows-x86_64/1.1.0-rc8/fa787ab7ef76f2556b56ac1f058916a1425455af/KodepoiaSetup.exe`;
2. bind payload URL, exact source, length `37730750`, SHA-256 `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`, `withdrawn=false`, unsigned signing status and `authenticode_policy="allow-unsigned"`;
3. preserve every existing rc3-rc7 target;
4. advance metadata monotonically, expected generation Targets `7 -> 8`, Snapshot `9 -> 10`, Timestamp `9 -> 10`;
5. stage and cryptographically verify the complete transition before applying it;
6. stop at any offline Targets-signing/private-key/passphrase/custody boundary and give the user exact local actions; never expose signing material;
7. qualify the exact TUF transition head without weakening any gate;
8. keep the GitHub rc8 release unpublished while that TUF PR is qualified;
9. explicitly publish the already-verified rc8 draft only at the authorized publication boundary;
10. re-fetch the now-public tag/release/asset and verify exact source, length and SHA again;
11. only then merge/apply the qualified TUF authorization.

## Final real-machine E2E

After rc8 is public and TUF-authorized, test exactly:

`installed rc7 -> discover rc8 -> download -> staged .KodepoiaSetup.exe.partial -> verified TUF metadata -> exact length -> exact SHA-256 -> target-scoped Authenticode policy -> installer identity -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> Check for updates again`

Required evidence must show rc7 really discovers rc8, the repaired literal-path/data transport handles the staged partial path, verification happens in the required order, no broken signature state is accepted, no installer launches without explicit consent, the restart reports `1.1.0-rc8`, and the subsequent update check is healthy.

Only that successful real-machine path closes the updater incident.

## Security and process invariants

- no unrelated feature work in rc8;
- do not mutate rc6, rc7 or published assets in place;
- no weakening of TUF signature, threshold, rollback, expiry, version, length or hash verification;
- no unconditional unsigned acceptance;
- no shell interpolation of staged paths;
- no private TUF key, seed, passphrase, custody path or signing material in Git, GitHub logs, release assets, documentation or chat;
- never reuse green CI evidence from another source SHA;
- re-fetch live release and metadata state at every publication/signing boundary;
- stop at every manual Windows, publication or custody-sensitive step rather than bypassing it.

## Resume rule

Before the next mutation:

1. re-fetch live `main`, PR #463/continuity state, `v1.1.0-rc8` release and tag;
2. expect canonical source authority `fa787ab7ef76f2556b56ac1f058916a1425455af` and post-source-merge `main` `9554dbf3968360a61c2b6392398502572bf8f198` unless later continuity explicitly supersedes it;
3. if the rc8 draft now exists, verify all exact draft fields and installer bytes before TUF work;
4. if it does not exist, remain at the manual draft-creation boundary;
5. if any live state contradicts this checkpoint, stop and resolve the discrepancy rather than guessing.
