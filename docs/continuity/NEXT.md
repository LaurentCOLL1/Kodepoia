# Kodepoia next actions

Last synchronized: 2026-09-14 15:20 CEST  
Companion state: `docs/continuity/STATE.md`  
Baseline to re-check before any mutation: `main` = `3721c1e5aec7ded023bf158bb9c2cce0900fa7ad`

## Goal

The updater-only correction is merged and the exact rc7 source/installer are fully qualified. The remaining sequence is now strictly:

`rc7 draft -> verify draft asset -> TUF ceremony -> publish rc7 -> real Windows rc7 health -> rc8 validation-only -> real updater E2E`

The historical `rc5 -> rc6` attempt remains failed/incomplete and must never be retroactively relabeled successful.

No unrelated feature work is authorized until the fresh installed-updater E2E path succeeds.

## Completed — rc7 source and installer qualification

- rc7 PR: `#458`;
- exact qualified technical source: `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- merge on `main`: `3721c1e5aec7ded023bf158bb9c2cce0900fa7ad`;
- all 40 PR-triggered workflows on the exact source head: `completed/success`;
- authoritative R17 run: `34802824212`;
- authoritative Actions artifact ID: `10331939170`;
- installer length: `37734287` bytes;
- installer SHA-256: `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0`;
- exact installer is unsigned; future target policy must be `authenticode_policy = "allow-unsigned"`.

At the synchronization checkpoint there is no rc7 release yet, no open PR, and live TUF remains Root `2`, Targets `6`, Snapshot `8`, Timestamp `8`.

## Next authorized action — manual GitHub draft only

This is the current manual publication boundary. Do **not** run the TUF ceremony yet and do **not** publish the release yet.

In GitHub:

1. Open the Kodepoia repository -> **Releases** -> **Draft a new release**.
2. In **Choose a tag**, enter `v1.1.0-rc7` and choose to create that new tag **on publish**. Do not create a separate tag manually.
3. Set **Target** to `release/1.1.0-rc7-updater-corrective`. This branch currently resolves exactly to `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`.
4. Release title: `Kodepoia 1.1.0-rc7`.
5. Mark **Set as a pre-release**.
6. Attach exactly the `KodepoiaSetup.exe` extracted from R17 Actions artifact `KodepoiaSetup-Windows` / artifact ID `10331939170`.
7. Before saving the draft, locally verify the file is exactly:
   - size `37734287` bytes;
   - SHA-256 `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0`.
8. Save as **Draft**. Do **not** click Publish release.

Suggested draft body:

```text
Kodepoia 1.1.0-rc7 — updater corrective beta release candidate.

Qualified exact source:
fafe96ce45c4ca98ef5c40f50c596036071eb6f9

Windows installer SHA-256:
c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0

Windows installer size:
37734287 bytes

This candidate contains the already-qualified updater PowerShell/AuthentiCode correction and no unrelated feature work.
```

After the draft exists, stop and return to ChatGPT. The next step is a read-only re-fetch of the draft, tag target and uploaded asset identity. TUF signing remains unauthorized until those live identities match exactly.

## After draft verification — not yet authorized

Only after the draft has been independently re-fetched and verified may the local TUF ceremony be staged.

The ceremony must:

- re-read live Root/Targets/Snapshot/Timestamp at execution time;
- preserve Root unless a separately governed Root ceremony is required;
- add exactly the rc7 target bound to source `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`, length `37734287`, SHA-256 `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0`;
- declare `authenticode_policy = "allow-unsigned"` for that exact target;
- preserve all still-authorized prior targets;
- increment metadata versions monotonically from the live generation;
- sign Targets only with the already-authorized offline Targets authority and Snapshot/Timestamp only with their already-authorized signers;
- expose no private key, seed, passphrase or custody path.

The approved launcher is `scripts/Run-TufReleaseCeremony.ps1`. Even its STAGE mode accesses private custody material, so it is a separate manual/custody-sensitive boundary and must not be run until the draft is verified.

## Later manual gates — not yet authorized

After a successful staged and verified TUF transition, the exact apply/publish ordering must be revalidated against live state before execution. `main` must never intentionally advertise a target whose final release payload cannot be retrieved and verified.

After rc7 is public and TUF-authorized:

1. install the qualified rc7 installer on the real Windows machine;
2. confirm Kodepoia reports `1.1.0-rc7`;
3. confirm updater search works without the previous PowerShell staging-path failure;
4. confirm the actual chosen installation path remains valid;
5. stop on any error and do not start rc8.

Only after this real-machine rc7 health gate succeeds may rc8 be created. rc8 must be validation-only and exists solely to exercise the repaired updater path from installed rc7.

## Resume prompt

`@Recherche sur le Web Continue rc7 depuis docs/continuity/STATE.md et docs/continuity/NEXT.md. Vérifie d'abord main, le draft v1.1.0-rc7, son tag/target et son KodepoiaSetup.exe exact. Ne lance aucune cérémonie TUF tant que le draft n'est pas vérifié, ne publie rien et ne contourne aucun échec.`
