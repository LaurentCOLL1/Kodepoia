# Kodepoia 1.1.0-rc7 release continuity

Status: **QUALIFIED AND MERGED — NOT YET PUBLISHED**  
Synchronized: 2026-09-14 15:20 CEST  
Canonical `main`: `3721c1e5aec7ded023bf158bb9c2cce0900fa7ad`

## Purpose

`1.1.0-rc7` is the corrective release candidate that carries the already-qualified updater PowerShell path transport and target-scoped TUF Authenticode policy fix. It introduces no unrelated feature work.

Its purpose is to establish a healthy installed rc7 baseline before a later validation-only rc8 is used for the real updater E2E exercise.

## Exact source authority

- PR: `#458` — `Release 1.1.0-rc7 — updater corrective candidate`;
- exact qualified source head: `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- merge commit: `3721c1e5aec7ded023bf158bb9c2cce0900fa7ad`;
- release branch: `release/1.1.0-rc7-updater-corrective` -> `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- product delta in PR #458: canonical release identity only (`rc6 -> rc7`), with no updater logic or dependency change.

All 40 pull-request-triggered workflows on the exact source head completed successfully before merge. This includes Repository Guard, Python Core, KodeStudio/UI smoke, R17 Windows Installer, R18.1, R18.2, R18.3, R18.4, R18.5, R18.6, R18.11, R19.3, R19.4 and R19.5. No failed gate was bypassed.

## Exact Windows installer authority

Authoritative build provenance:

- workflow: `R17 Windows Installer`;
- run ID: `34802824212`;
- Actions artifact: `KodepoiaSetup-Windows`;
- artifact ID: `10331939170`;
- workflow head: `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`.

Exact installer identity:

- filename: `KodepoiaSetup.exe`;
- length: `37734287` bytes;
- SHA-256: `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0`;
- public version: `1.1.0-rc7`;
- PEP 440 version: `1.1.0rc7`;
- installer version: `1.1.0-rc7`;
- source SHA in `installer-manifest.json`: `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- manifest `production_signed`: `false`.

Independent PE inspection of the exact artifact found Authenticode Security Directory / certificate table offset `0` and size `0`. The qualified installer is therefore genuinely unsigned.

## Authenticode policy for rc7

Because the exact qualified installer is unsigned, its TUF target must explicitly declare:

```json
"authenticode_policy": "allow-unsigned"
```

The authorization is target-scoped and does not weaken other signature states. `Invalid`, broken, untrusted or unknown signature results remain rejected. Legacy `signing_status` is informational only and must not grant authorization.

## Public/TUF state before rc7 publication

At this continuity checkpoint:

- no GitHub release tagged `v1.1.0-rc7` exists;
- latest public prerelease remains `v1.1.0-rc6`;
- rc6 source: `fdd88dfd6cee8408bf33de1c4ee4f70103fda340`;
- rc6 installer size: `37712720` bytes;
- rc6 installer SHA-256: `4214f19eea690357ef5aff20b74f9a4733dc1940d8a4315df803e9264ea46e6f`;
- Root: v2, expiry `2027-09-08T14:59:19Z`;
- Targets: v6, expiry `2027-09-12T20:49:31Z`;
- Snapshot: v8, expiry `2026-09-16T17:44:32Z`;
- Timestamp: v8, expiry `2026-09-15T17:44:32Z`.

Targets v6 contains rc3 through rc6 and does not yet contain rc7. Do not infer future metadata versions from this document; the ceremony must re-read the live generation immediately before signing.

## Required publication order

Preserve the established fail-closed draft-first discipline:

1. create `v1.1.0-rc7` as a **draft prerelease**, targeted to `release/1.1.0-rc7-updater-corrective` / exact source `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
2. upload only the exact qualified `KodepoiaSetup.exe`;
3. keep the release in Draft state;
4. re-fetch the draft and independently verify target/source, filename, size and digest;
5. only then authorize a staged TUF ceremony with target policy `allow-unsigned`;
6. revalidate the staged metadata and live release state before any apply/publish action;
7. never leave `main` intentionally advertising a target whose final release asset is unavailable or fails identity verification.

Do not manually create a conflicting Git tag before publication.

## Current stop boundary

The next action is manual GitHub draft creation. Do not run the TUF ceremony yet.

After the draft is created and the exact installer is attached, return to ChatGPT so the draft can be re-fetched read-only and verified before any custody-sensitive signing step.

No private TUF key, seed, passphrase or custody path may be shared in chat, GitHub, release assets or logs.

## Later validation objective

After rc7 is public and TUF-authorized, install it on the real Windows machine and establish that rc7 itself is healthy. Only then may validation-only rc8 be created.

The updater incident closes only after the full real-machine path succeeds:

`installed rc7 -> discover rc8 -> download -> verified TUF metadata -> exact length -> exact SHA-256 -> target-scoped Authenticode policy -> installer identity -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> search again`
