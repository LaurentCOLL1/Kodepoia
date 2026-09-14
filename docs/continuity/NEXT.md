# Kodepoia next actions

Last synchronized: 2026-09-14 after rc7 publication/TUF authorization  
Companion state: `docs/continuity/STATE.md`  
Baseline to re-check before any mutation: `main` = `bbcb4313108732a0be2e4828bf2be5cca747904d`

## Goal

The updater-only correction, rc7 publication and rc7 TUF authorization are complete. The remaining sequence is now strictly:

`real Windows rc7 health -> rc8 validation-only -> publish/TUF authorize rc8 -> real updater E2E rc7 -> rc8`

The historical `rc5 -> rc6` attempt remains failed/incomplete and must never be relabeled successful.

No unrelated feature work is authorized until the fresh installed-updater E2E path succeeds.

## Completed — rc7 public release and TUF authorization

- rc7 exact qualified source: `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- public prerelease: `v1.1.0-rc7`;
- release ID: `388454717`;
- installer asset ID: `563538713`;
- installer length: `37734287` bytes;
- installer SHA-256: `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0`;
- rc7 TUF PR: `#460`;
- exact qualified TUF head: `4976ded7956e20e64e3abd3dffdd7b8fb58cc04d`;
- all 30 PR-triggered workflows on that head: `completed/success`;
- TUF merge commit: `bbcb4313108732a0be2e4828bf2be5cca747904d`;
- live metadata: Root `2`, Targets `7`, Snapshot `9`, Timestamp `9`;
- rc7 target policy: `authenticode_policy = "allow-unsigned"`.

## Next authorized action — real Windows rc7 health gate

This is now the mandatory manual boundary. Do **not** start rc8 until it succeeds.

On the real Windows machine:

1. download/use the exact public `v1.1.0-rc7` `KodepoiaSetup.exe`;
2. verify size `37734287` and SHA-256 `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0` if using a fresh download;
3. install rc7 in the intended installation directory;
4. launch Kodepoia and confirm version `1.1.0-rc7`;
5. invoke **Check for updates** from the installed application;
6. confirm the previous PowerShell staged-path failure does not recur;
7. confirm there is no Authenticode-policy, TUF, installer-identity or installation-path error;
8. preserve the exact console/UI/log result if anything unexpected occurs.

If any step fails, stop and return with the exact error. Do not create rc8.

## After rc7 health succeeds — rc8 only

Only after the real-machine rc7 health gate is explicitly confirmed may rc8 start.

rc8 constraints:

- validation-only release candidate;
- no new updater functionality;
- no unrelated refactor or dependency update;
- minimum technical delta should be canonical release identity (`rc7 -> rc8`) plus strictly necessary release/TUF evidence;
- qualify the exact rc8 source head before publication;
- build and bind the exact installer to its own length/SHA;
- derive its Authenticode policy from the exact built artifact, never from assumption;
- draft-first release discipline;
- stage/verify TUF before apply;
- publish asset before merging TUF authorization into `main`;
- no failed check may be bypassed.

## Final E2E objective

With rc7 installed and healthy, the required real-machine E2E is:

`installed rc7 -> discover rc8 -> download -> verified TUF metadata -> exact length -> exact SHA-256 -> target-scoped Authenticode policy -> installer identity -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> search again`

Only that successful path closes the updater incident.

## Resume prompt

`@Recherche sur le Web Continue rc7 health / rc8 validation depuis docs/continuity/STATE.md et docs/continuity/NEXT.md. Revalide d'abord main, v1.1.0-rc7, son asset et les métadonnées TUF live. Ne commence rc8 que si le health gate Windows rc7 est explicitement réussi, et ne contourne aucun échec.`
