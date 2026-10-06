# Kodepoia 1.1.1 — terminal V2 consolidation maintenance release

Status: **PREPARATION / EXACT-SOURCE CANDIDATE AUTHORIZED — NO PUBLIC EFFECT YET**

Authority date: 2026-10-06  
Repository: `LaurentCOLL1/Kodepoia`  
Terminal V2 main base: `913aef2cf4673a2c8b8b7874204fe1b11edcf225`

## Purpose

Kodepoia 1.1.1 is a **post-V2 maintenance consolidation release** whose purpose is to ship
the terminal post-normalization V2 tree rather than the earlier 1.1.0 candidate snapshot.

It does **not** create V2.7, reopen R20, or authorize any new product capability.

The target release identity is:

- product: `Kodepoia`;
- public / installer / PEP 440 version: `1.1.1`;
- channel: `stable`;
- build type: `release`;
- tag: `v1.1.1`;
- source binding: `exact-head`.

## Accepted public baseline

The currently published stable baseline remains Kodepoia 1.1.0 until 1.1.1 is fully closed:

- tag: `v1.1.0`;
- exact source: `46ed800888b4f19da9e984232dd1ad6cdb639cc1`;
- installer: `KodepoiaSetup.exe`;
- installer bytes: `38834833`;
- installer SHA-256: `8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef`;
- production TUF: Root v2 / Targets v9 / Snapshot v11 / Timestamp v11;
- Authenticode: unsigned, no production trust claim;
- WinGet: OUT.

## Consolidation boundary

The 1.1.1 release-preparation source must descend from terminal V2 main
`913aef2cf4673a2c8b8b7874204fe1b11edcf225`.

The preparation diff is restricted to canonical version identity, compatibility of historical
V2.6 acceptance with a newer current release, the 1.1.1 release workflow/tests, and
continuity/release documentation. No unrelated `src/kodepoia/**` product implementation
change is authorized.

The V2.6.1 terminal freeze remains historical truth for 1.1.0 and must not be rewritten to
pretend that V2.6 originally targeted 1.1.1.

## Candidate definition of done

The exact-source Windows candidate must:

1. check out and prove one exact SHA descending from terminal V2 main;
2. enforce the release-only diff allowlist;
3. prove canonical release identity and package version are both 1.1.1;
4. verify that `v1.1.1` tag and Release are absent before candidate staging;
5. build `KodepoiaSetup.exe` twice from the same exact SHA;
6. generate SPDX SBOM and provenance for that SHA;
7. build evidence-bound release bundles and pass the existing R18 semantic two-build comparison;
8. record truthful unsigned Authenticode state with `production_signed=false`;
9. stage a draft-only immutable `v1.1.1` release description without publishing;
10. perform clean custom-directory install, packaged smoke and uninstall;
11. emit `V1_1_1_CONSOLIDATION_CANDIDATE.json` with fail-closed checks and an evidence digest;
12. perform no public tag/release/asset, production TUF, signing-secret or WinGet effect.

## Production sequence after candidate acceptance

After the candidate is frozen, production publication must remain sequential and exact-source:

1. preserve Root v2 and all existing targets;
2. add one exact stable 1.1.1 target, expected as the next monotonic Targets generation;
3. obtain the Targets signature through the existing **offline Targets custody** boundary;
4. create fresh signed Snapshot/Timestamp metadata around that exact Targets file;
5. revalidate the candidate source/hash/length against the signed target;
6. publish exactly one `v1.1.1` Release and one `KodepoiaSetup.exe`;
7. prove real public updater discovery and installed upgrade `1.1.0 -> 1.1.1`;
8. prove a fresh stable query reports `up-to-date`;
9. normalize authorities only after all live evidence passes.

No private Targets key, Snapshot/Timestamp seed or passphrase may be pasted into ChatGPT.
