# Kodepoia 1.1.1 — V2 terminal consolidation release

Status: **PREPARATION CURRENT — NO PUBLICATION OR TUF MUTATION YET**

## Authority

The user explicitly authorized a Kodepoia **1.1.1 consolidation release** after V2.6.6 reached
COMPLETE + NORMALIZED. This release does not reopen V2 and does not authorize V2.7, R20.7, or any
new product capability.

The source baseline is terminal V2 main:

`913aef2cf4673a2c8b8b7874204fe1b11edcf225`

The release branch is created directly from that exact commit. Only release-version, release
evidence, compatibility-test, updater/TUF staging and publication work needed to distribute the
already-complete V2 state is authorized.

## Version and compatibility

- current public baseline until publication: **1.1.0** / `v1.1.0`;
- consolidation target: **1.1.1** / `v1.1.1`;
- channel: `stable`;
- build type: `release`;
- source binding: `exact-head`;
- Windows installer identity and AppId remain unchanged;
- custom installation directory preservation remains mandatory;
- production Authenticode truth remains observed, never fabricated;
- WinGet remains OUT unless separately authorized.

The historical V2.6.1/V2.6.3 freeze remains bound to 1.1.0. Advancing CURRENT_RELEASE to 1.1.1
must not rewrite or reinterpret historical V2 evidence.

## Candidate gate

Before any public effect, the exact-source Windows candidate must:

1. bind canonical release identity and `pyproject.toml` to 1.1.1;
2. build `KodepoiaSetup.exe` twice from the same exact SHA;
3. run the accepted R18 semantic two-build comparison;
4. emit SPDX SBOM and provenance for the exact SHA;
5. record the observed Authenticode state truthfully;
6. clean-install, packaged-smoke and uninstall successfully;
7. revalidate the public 1.1.0 baseline tag/Release/asset;
8. prove `v1.1.1` tag and Release are absent;
9. emit `V1_1_1_CONSOLIDATION_CANDIDATE.json`;
10. perform no public tag, Release, asset, TUF, updater or WinGet mutation.

## Post-candidate sequence

Only after a candidate is qualified from an unchanged merged `main`:

1. freeze its exact source SHA, installer byte length and SHA-256;
2. prepare a new stable TUF target for 1.1.1 while preserving all historical targets;
3. perform the existing offline Targets custody ceremony locally with the already-authorized key;
4. refresh/sign Snapshot and Timestamp only through the approved production signing environment;
5. commit/revalidate the coherent production metadata generation;
6. publish a new immutable `v1.1.1` GitHub Release with exactly the qualified installer;
7. run a live installed updater closure proving **1.1.0 -> 1.1.1** and post-upgrade `up-to-date`;
8. normalize continuity authority only after all exact-source evidence passes.

Never paste Targets private keys, passphrases, Snapshot/Timestamp secret seeds or other production
secrets into ChatGPT, Git, logs or artifacts.
