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


## Exact 1.1.1 candidate freeze — QUALIFIED

The post-merge `Kodepoia 1.1.1 Consolidation Candidate` workflow run `37536813744`
completed successfully on exact `main` source
`aa1c80389b10f5ef44737241bf192c04f847e4ec`.

Accepted candidate identity:

- artifact ID: `11448467632`;
- artifact: `v1-1-1-consolidation-aa1c80389b10f5ef44737241bf192c04f847e4ec`;
- terminal candidate report: **9/9 PASS**;
- candidate evidence SHA-256:
  `19a1fb1e73693f64cae7d1571c529b3f35625046ac4210375ad23ed2ac2b0d97`;
- installer: `KodepoiaSetup.exe`;
- installer byte length: **38,880,869**;
- installer SHA-256:
  `c8e7949ead2e1e14adece7cb9826f0b1be689b81ac814eef2f041760b9f738cd`;
- Authenticode: `NotSigned`, `production_signed=false`;
- target policy: `allow-unsigned`;
- clean install, packaged smoke, uninstall and two-build semantic comparison: PASS;
- public `v1.1.1` namespace remained absent;
- no public tag/Release, production TUF or WinGet mutation occurred.

The deterministic TUF transition request is
`docs/release/V1_1_1_TUF_TRANSITION_REQUEST.json`, request SHA-256
`03f9225ae1529b1816f3e745f7c6a4f2e84400c7570f4c3ff02172102e857abe`.

Current production TUF input remains Root v2 / Targets v9 / Snapshot v11 / Timestamp v11.
The next legitimate step is the existing **offline Targets custody ceremony**, signing only the
new stable 1.1.1 target as Targets v10 while preserving every prior target. Snapshot/Timestamp
v12 are a later online-signing step and must not be generated with synthetic or exposed secrets.


## Offline Targets v10 qualified — online Snapshot/Timestamp v12 next

The operator-held Targets custody ceremony completed successfully on 2026-10-07 using the
already-authorized Targets role. The accepted public-only outputs are frozen under
`docs/release/evidence/V1_1_1_TARGETS_V10.json`,
`V1_1_1_TARGETS_V10_CEREMONY_REPORT.json` and
`V1_1_1_TARGETS_V10_CEREMONY_SUMMARY.txt`.

Accepted offline transition truth:

- release source: `aa1c80389b10f5ef44737241bf192c04f847e4ec`;
- installer: 38,880,869 bytes;
- installer SHA-256: `c8e7949ead2e1e14adece7cb9826f0b1be689b81ac814eef2f041760b9f738cd`;
- Targets v9 -> v10;
- Targets v10 SHA-256: `94107eb8bba745603eb27dc04c2060796c15d3977bd1a68abb3cb1bf74c7148e`;
- Targets v10 length: `5902`;
- all historical targets preserved; exactly one stable 1.1.1 target added;
- Targets signature threshold satisfied by an already-authorized signer;
- Authenticode policy remains `allow-unsigned`;
- no private key path, private material, passphrase or secret value is recorded;
- `applied=false`, `offline_targets_only=true`, `online_metadata_generated=false`.

The next legitimate effect is the protected `Kodepoia 1.1.1 Online Metadata Transition`
workflow on an unchanged `main`. It may generate Snapshot v12 and Timestamp v12 around this
exact Targets v10 using the existing `tuf-production-signing` environment, but it remains
read-only and must not mutate production metadata or create the public 1.1.1 Release.
