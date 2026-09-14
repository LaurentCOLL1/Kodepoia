# Kodepoia next actions

Last synchronized: 2026-09-14 during rc8 validation-only qualification  
Companion state: `docs/continuity/STATE.md`  
Baseline to re-check before any mutation: live `main` was `c61347993af70f9167d08f2ff5e46f33f7686b4e` at this checkpoint.

## Goal

The updater-only correction, rc7 publication/TUF authorization and the real Windows rc7 discovery health gate are complete. The remaining sequence is now strictly:

`finish exact-head rc8 qualification -> merge exact qualified rc8 source -> obtain/bind exact rc8 installer -> draft/publication gates -> TUF authorize rc8 -> real updater E2E rc7 -> rc8`

The historical `rc5 -> rc6` attempt remains failed/incomplete and must never be relabeled successful.

No unrelated feature work is authorized until the fresh installed-updater E2E path succeeds.

## Completed — rc7 baseline

- rc7 exact qualified source: `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- public prerelease: `v1.1.0-rc7`;
- installer length: `37734287` bytes;
- installer SHA-256: `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0`;
- live pre-rc8 metadata generation: Root `2`, Targets `7`, Snapshot `9`, Timestamp `9`;
- rc7 target policy: `authenticode_policy = "allow-unsigned"`;
- real Windows rc7 UI evidence confirms running `1.1.0-rc7` and successful **Check for updates** with candidate sourced from `tuf-verified-metadata` and no PowerShell/AuthentiCode/TUF/installer-identity error.

The rc7 health gate authorized rc8 creation. The full staged download path is still unproven until rc7 discovers and downloads a newer rc8 target.

## ACTIVE — rc8 validation-only PR #462

Exact active authority at this checkpoint:

- PR: `#462` — `Release 1.1.0-rc8 — validation-only candidate`;
- branch: `release/1.1.0-rc8-validation`;
- exact head: `fa787ab7ef76f2556b56ac1f058916a1425455af`;
- creation base: `c61347993af70f9167d08f2ff5e46f33f7686b4e`;
- scope: exactly 2 files, `+2/-2`;
- `pyproject.toml`: `1.1.0rc7 -> 1.1.0rc8`;
- `src/kodepoia/release/release_identity.json`: serial `7 -> 8`;
- no updater code, dependency, TUF metadata or unrelated feature change.

CI checkpoint for exact head `fa787ab7ef76f2556b56ac1f058916a1425455af`:

- 40 PR-triggered workflows total;
- 37 completed `success`;
- 3 still running:
  - `R18.2 Deterministic Release Bundle Acceptance`;
  - `R17 Windows Installer`;
  - `R18.11 Integrated Adversarial Release Update Acceptance`.

This is a snapshot only. Re-fetch live workflow state before acting.

## Next authorized action — finish exact-head qualification

1. Re-fetch live `main` and PR #462.
2. Confirm PR #462 head is still exactly `fa787ab7ef76f2556b56ac1f058916a1425455af`.
3. Re-fetch **all** PR-triggered workflow runs for that SHA.
4. Require all 40 to be `completed` with conclusion exactly `success`.
5. If any is `failure`, `cancelled`, `timed_out`, `action_required`, `startup_failure`, `stale`, `skipped`, `neutral`, or otherwise not exactly `success`, do not merge; inspect and resolve the real cause without weakening verification.
6. If the head SHA changed, old green evidence is invalid for release qualification; qualify the new exact SHA from scratch.
7. Only when all 40 exact-head runs are green may PR #462 be merged.

## After PR #462 merges — rc8 artifact authority

Do not assume the rc8 installer identity, size, hash or signature state.

For the exact qualified rc8 source:

1. identify the authoritative `R17 Windows Installer` run/artifact for the exact qualified source;
2. obtain `KodepoiaSetup.exe` from that exact run;
3. establish authoritative byte length and SHA-256;
4. inspect the exact artifact's Authenticode state;
5. derive target-scoped TUF `authenticode_policy` from the artifact result:
   - genuinely unsigned exact artifact -> `allow-unsigned` may be used for that exact target;
   - signed artifact -> signed-required policy as defined by the updater contract;
   - malformed/unknown/contradictory evidence -> stop fail-closed;
6. preserve source SHA, artifact length/SHA and evidence in release continuity.

## rc8 publication/TUF sequence

After exact source and installer qualification:

1. prepare rc8 release using draft-first discipline;
2. never replace/mutate an already-published asset in place;
3. verify tag/source binds to the exact qualified rc8 source;
4. verify release asset bytes match the qualified installer exactly;
5. prepare the rc8 TUF target with exact:
   - channel/platform/version path;
   - source SHA;
   - public version;
   - release asset URL;
   - byte length;
   - SHA-256;
   - `withdrawn=false`;
   - target-scoped `authenticode_policy`;
6. advance Targets/Snapshot/Timestamp monotonically and maintain all existing rc3-rc7 targets unless a separately authorized withdrawal exists;
7. stage and cryptographically verify the complete TUF transition before apply;
8. if offline Targets signing, private key custody, passphrase entry, Windows-only manual publication, or another secret-bearing/manual boundary is required, **stop** and give the user exact commands/actions; do not improvise or bypass it;
9. only merge/publish TUF authorization when all exact-head checks pass.

## Final real-machine E2E objective

With rc7 installed and healthy, test exactly:

`installed rc7 -> discover rc8 -> download -> staged .KodepoiaSetup.exe.partial -> verified TUF metadata -> exact length -> exact SHA-256 -> target-scoped Authenticode policy -> installer identity -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> Check for updates again`

Required evidence includes:

- rc7 actually discovers rc8, not itself;
- download succeeds through the repaired PowerShell literal-path/data transport with normal Windows path characters/spaces;
- `.KodepoiaSetup.exe.partial` verification succeeds;
- TUF length/SHA checks occur before Authenticode policy acceptance;
- the exact target-scoped policy is honored without accepting broken/untrusted signature states;
- installer identity matches rc8;
- no automatic installer launch without explicit consent;
- restart reports `1.1.0-rc8`;
- a subsequent update check is healthy.

Only this successful E2E closes the updater incident.

## Continuity protection

A dedicated continuity branch was created while PR #462 qualification was in progress:

`docs/continuity-rc8-qualification-20260914`

If the current conversation ends before these updates reach `main`, locate that branch/its continuity PR and use it as the latest written handoff, while still re-fetching live GitHub state. Do not modify the rc8 head merely to carry documentation because that would invalidate exact-head qualification evidence.

## Resume prompt

`@Recherche sur le Web Reprends rc8 depuis docs/continuity/STATE.md et docs/continuity/NEXT.md (ou la branche docs/continuity-rc8-qualification-20260914 si elle n'est pas encore fusionnée). Revalide d'abord main et la PR #462. Le head rc8 attendu au checkpoint est fa787ab7ef76f2556b56ac1f058916a1425455af. Re-fetch les 40 workflows et ne fusionne que s'ils sont tous completed/success sur ce SHA exact. Ensuite poursuis l'artefact R17, publication/TUF et l'E2E rc7 -> rc8 sans contourner aucun échec.`
