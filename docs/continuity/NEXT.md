# Kodepoia next actions

Last synchronized: 2026-09-14 after exact-head rc8 qualification, source merge and R17 artifact binding  
Companion state: `docs/continuity/STATE.md`

## Goal

The remaining updater-incident sequence is now strictly:

`manual unpublished rc8 draft -> re-fetch/verify exact draft asset -> prepare and qualify rc8 TUF transition while draft remains unpublished -> explicit rc8 publication -> re-fetch/verify public tag and asset -> merge/apply qualified TUF authorization -> real Windows updater E2E rc7 -> rc8`

The historical `rc5 -> rc6` attempt remains failed/incomplete and must never be relabeled successful. No unrelated feature work is authorized until the fresh installed-updater E2E succeeds.

## Completed — rc8 source qualification

- exact qualified source: `fa787ab7ef76f2556b56ac1f058916a1425455af`;
- PR `#462` qualified with exactly 40 PR-triggered workflows;
- terminal re-fetch: all 40 `completed/success` on that exact source SHA;
- final long gates R18.2, R17 and R18.11 all succeeded;
- #462 merged with exact-head guard;
- post-merge `main`: `9554dbf3968360a61c2b6392398502572bf8f198`;
- the release/tag authority remains the exact source `fa787ab7...`, not the merge commit.

No failed, skipped, neutral, cancelled or otherwise non-success workflow was treated as green.

## Completed — exact rc8 installer authority

Authoritative R17 evidence:

- R17 run ID: `34871154670`;
- artifact name: `KodepoiaSetup-Windows`;
- artifact ID: `10360685910`;
- file: `KodepoiaSetup.exe`;
- public version: `1.1.0-rc8`;
- source SHA: `fa787ab7ef76f2556b56ac1f058916a1425455af`;
- length: `37730750` bytes;
- SHA-256: `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`;
- exact artifact is genuinely unsigned (`production_signed=false`; PE certificate table absent);
- derived target-scoped policy: `authenticode_policy = "allow-unsigned"`.

The updater contract was revalidated: exact TUF length/SHA checks occur before Authenticode, `allow-unsigned` accepts only exact `NotSigned`, installer identity is verified afterward, and launch requires explicit user consent.

## Current release state

Latest live checks show:

- `v1.1.0-rc8` GitHub release: absent;
- `refs/tags/v1.1.0-rc8`: absent.

This is expected and leaves a clean draft-first boundary.

## NEXT AUTHORIZED ACTION — manual draft creation

This is a manual publication boundary. Create an **unpublished draft**, do not publish it yet.

Required draft identity:

- tag: `v1.1.0-rc8`;
- target exact source: `fa787ab7ef76f2556b56ac1f058916a1425455af`;
- title: `Kodepoia 1.1.0-rc8`;
- draft: yes;
- prerelease: yes;
- exactly one installer asset: `KodepoiaSetup.exe`;
- expected length: `37730750` bytes;
- expected SHA-256: `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`.

Recommended release notes:

```text
Kodepoia 1.1.0-rc8 — validation-only updater E2E release candidate.

Qualified exact source:
fa787ab7ef76f2556b56ac1f058916a1425455af

Windows installer SHA-256:
6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422
```

Do not publish the draft after upload. Stop with it unpublished.

## Immediately after the draft exists

Re-fetch the draft release and require all of these before any TUF mutation:

1. tag exactly `v1.1.0-rc8`;
2. target/source exactly `fa787ab7ef76f2556b56ac1f058916a1425455af`;
3. `draft=true` and `prerelease=true`;
4. exactly one intended installer asset named `KodepoiaSetup.exe`;
5. asset size exactly `37730750`;
6. GitHub asset digest exactly `sha256:6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`;
7. no unexpected tag/source/release or asset drift.

Any mismatch is a hard stop; do not replace a public asset or weaken the gate.

## TUF transition to prepare after exact draft verification

Live pre-rc8 metadata authority remains Root 2 / Targets 7 / Snapshot 9 / Timestamp 9.

The new target must be exactly:

`channels/beta/windows-x86_64/1.1.0-rc8/fa787ab7ef76f2556b56ac1f058916a1425455af/KodepoiaSetup.exe`

with:

```text
channel = beta
public_version = 1.1.0-rc8
source_sha = fa787ab7ef76f2556b56ac1f058916a1425455af
payload_url = https://github.com/LaurentCOLL1/Kodepoia/releases/download/v1.1.0-rc8/KodepoiaSetup.exe
length = 37730750
sha256 = 6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422
withdrawn = false
signing_status = unsigned; production trust is not claimed
authenticode_policy = allow-unsigned
```

Preserve every rc3-rc7 target. Expected monotonic versions are Targets `8`, Snapshot `10`, Timestamp `10`; exact expiry values and signatures must come from the authorized metadata tooling, never be invented.

Stage and cryptographically verify the complete transition before apply. If Targets signing requires an offline/private key, passphrase, custody path or other secret-bearing action, stop and give the user the exact local command/action. Do not request or expose signing material in chat.

## Publication ordering

Follow the same fail-closed ordering proven for rc7:

1. keep the rc8 GitHub release as an unpublished draft while the TUF transition PR is prepared and exact-head qualified;
2. do not merge the TUF transition while the release is still only a draft;
3. at the separate authorized publication boundary, explicitly publish the already-verified rc8 prerelease;
4. re-fetch the public release, tag and asset;
5. require exact source, asset name, size and SHA-256 again;
6. only then merge/apply the already-qualified TUF authorization.

Never mutate or replace the asset after public publication.

## Final real-machine E2E

Once rc8 is both public and TUF-authorized, use the already-installed healthy rc7 and test exactly:

`installed rc7 -> discover rc8 -> download -> staged .KodepoiaSetup.exe.partial -> verified TUF metadata -> exact length -> exact SHA-256 -> target-scoped Authenticode policy -> installer identity -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> Check for updates again`

Required evidence:

- rc7 discovers rc8 rather than itself;
- repaired PowerShell literal-path/data transport successfully handles the staged partial path;
- exact length and SHA checks occur before Authenticode acceptance;
- target-scoped `allow-unsigned` accepts only the exact unsigned state and no broken/untrusted state;
- installer identity is `1.1.0-rc8`;
- no automatic launch occurs without explicit consent;
- upgrade/restart succeeds and reports `1.1.0-rc8`;
- subsequent update check is healthy.

Only this successful path closes the updater incident.

## Resume prompt

`@Recherche sur le Web Continue rc8 depuis docs/continuity/STATE.md et docs/continuity/NEXT.md. #462 est qualifiée 40/40 et fusionnée; source rc8 exacte fa787ab7ef76f2556b56ac1f058916a1425455af; main après merge 9554dbf3968360a61c2b6392398502572bf8f198; R17 run 34871154670 / artifact 10360685910; KodepoiaSetup.exe = 37730750 octets / SHA-256 6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422 / réellement non signé / policy allow-unsigned. La prochaine frontière est la création manuelle du draft GitHub v1.1.0-rc8 ciblant fa787ab7..., prerelease et non publié, avec cet EXE exact. Re-fetch et vérifie le draft avant tout TUF; ne contourne aucun échec.`
