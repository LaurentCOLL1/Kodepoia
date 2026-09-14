# Kodepoia next actions

Last synchronized: 2026-09-14 04:50 CEST  
Companion state: `docs/continuity/STATE.md`  
Baseline to re-check before any mutation: `main` = `b9f801ef30177ee9b46eeb5bbb32d39e76a13a82`

## Goal

The updater-only PowerShell/AuthentiCode correction is qualified and merged through PR `#456`. The remaining objective is now strictly the release/validation sequence:

`rc7 corrective install -> rc8 validation-only updater E2E`

The historical `rc5 -> rc6` attempt remains failed/incomplete and must never be retroactively relabeled successful.

No unrelated feature work is authorized until the fresh installed-updater E2E path succeeds.

## Phase 1 — re-validate live authority before rc7

Before creating any rc7 mutation:

1. Re-fetch current `main` and confirm its exact SHA. The normalization baseline is `b9f801ef30177ee9b46eeb5bbb32d39e76a13a82`.
2. Re-fetch open PRs and reconcile any concurrent release/updater work before writing.
3. Re-fetch the latest public release/tag state. At this normalization checkpoint, rc6 remains:
   - tag/source: `fdd88dfd6cee8408bf33de1c4ee4f70103fda340`;
   - installer size: `37712720` bytes;
   - installer SHA-256: `4214f19eea690357ef5aff20b74f9a4733dc1940d8a4315df803e9264ea46e6f`.
4. Re-read live Root/Targets/Snapshot/Timestamp from `main`. At this checkpoint they are Root `2`, Targets `6`, Snapshot `8`, Timestamp `8`; these are observations, not permission to assume future version numbers if live state changes.
5. Confirm the corrective merge and current release identity before branching. The repository may still identify itself as rc6 until the dedicated rc7 release branch intentionally changes that identity.

## Phase 2 — prepare and qualify rc7, updater correction only

Create a dedicated rc7 release branch from the revalidated canonical `main`.

rc7 constraints:

- version: `1.1.0-rc7`;
- source must contain the already-merged updater correction and no unrelated feature work;
- update only release/version/evidence material required to produce rc7;
- do not change the corrected PowerShell/AuthentiCode security semantics unless a new failing acceptance proves a defect;
- do not mutate rc6 in place.

Before any public publication or trusted-metadata signing:

1. Change canonical release identity to rc7 on the dedicated branch.
2. Build the Windows installer from the exact rc7 source head.
3. Record exact source SHA, installer length and SHA-256.
4. Run repository guard, full Python Core on Windows/Ubuntu, KodeStudio/UI smoke and every release/updater acceptance triggered by current governance on the **exact rc7 head**.
5. Require R17 Windows Installer, R18.6/R18.7/R18.8/R18.10/R18.11 and R19.2/R19.3/R19.4/R19.5 to remain green wherever current workflow path filters trigger them.
6. Do not reuse green evidence from PR `#456` for a changed rc7 SHA.
7. Fix any real failure and re-qualify the resulting new exact head. Never skip, disable or weaken a failing verification to obtain a green result.

## Phase 3 — rc7 publication / TUF boundary

After the exact rc7 source and installer are fully qualified, stop at the first custody-sensitive/manual boundary required by the live release process.

For the rc7 target metadata:

- `authenticode_policy` must be explicit for the exact target if unsigned acceptance is intended;
- use `allow-unsigned` only when the qualified exact installer is genuinely `NotSigned` and TUF still binds its exact length and SHA-256;
- use `require-valid` when the qualified installer has a valid Authenticode signature;
- never infer authorization from legacy free-text `signing_status`;
- unknown/malformed policy remains forbidden;
- Root/Targets/Snapshot/Timestamp next versions and expiries must be calculated from **live** metadata at ceremony time;
- no private signing key, passphrase, seed or custody path may be exposed in Git, Actions logs, release assets, docs or chat.

If offline Targets signing, public release publication or another custody-sensitive action requires user intervention, **stop there** and provide the exact commands/UI actions and exact hashes/SHA identities to verify. Do not proceed to rc8 until rc7 publication/authorization is confirmed from live state.

## Phase 4 — real Windows rc7 confirmation

Once rc7 is published/authorized as intended:

1. Install rc7 on the real Windows machine using the qualified installer.
2. Confirm the installed application reports `1.1.0-rc7`.
3. Open the updater UI and confirm it starts and searches without the PowerShell path failure that occurred during rc5 -> rc6.
4. Confirm the installation path actually used by the real machine; custom drive/directory support must remain intact.
5. Record any exact error text and do not continue to rc8 if rc7 itself is unhealthy.

This is a manual Windows gate. rc8 work is unauthorized until the rc7 installation/health result is reported and verified.

## Phase 5 — rc8 validation-only candidate

Only after the real installed rc7 gate succeeds:

1. Create a dedicated rc8 branch from the then-current normalized authority.
2. Set version to `1.1.0-rc8`.
3. Add **no unrelated feature or corrective work**. rc8 exists only to provide a strictly newer target for updater E2E validation.
4. Build and qualify its Windows installer on the exact source head.
5. Publish/authorize it through the same fail-closed release/TUF process, with an explicit target-scoped `authenticode_policy` matching the exact artifact state.
6. Stop again at any manual publication/offline-signing/custody boundary rather than bypassing it.

## Phase 6 — fresh real-machine updater E2E

Exercise exactly:

`installed rc7 -> search -> detect rc8 -> download -> verified TUF metadata -> exact length -> exact SHA-256 -> target-scoped Authenticode policy -> installer identity/version -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> search again`

Required verdicts:

- rc8 is discovered as strictly newer;
- staged `.KodepoiaSetup.exe.partial` path works on the real machine, including the actual installation/cache path;
- TUF target authorization, length and SHA-256 pass;
- Authenticode outcome is accepted only under the exact trusted target policy;
- installer identity is rc8 before launch;
- explicit user consent remains required;
- upgrade succeeds without changing the chosen installation directory unexpectedly;
- restarted application reports rc8;
- a subsequent update search does not incorrectly offer rc8 again as newer.

Only after the entire path succeeds may the updater E2E incident be marked closed.

## Phase 7 — normalize each completed milestone

After each merged rc7/rc8 milestone:

- update `docs/continuity/STATE.md` with canonical `main`, exact technical source, PR/merge identity, artifact identity and acceptance verdict;
- update `docs/continuity/NEXT.md` so it contains only still-pending actions;
- update the relevant rc7/rc8 release evidence document;
- update any long-form continuity authority still designated canonical by the repository;
- re-read live state before authorizing the next milestone.

## Ready-to-use next-chat prompt

`@Recherche sur le Web Continue la séquence updater après le correctif fusionné #456. Lis docs/continuity/STATE.md et docs/continuity/NEXT.md, revalide main, les PR ouvertes, rc6 et les métadonnées TUF live, puis prépare et qualifie uniquement Kodepoia 1.1.0-rc7. Ne contourne aucun échec et arrête-toi exactement à toute frontière manuelle Windows, publication ou signature TUF offline.`
