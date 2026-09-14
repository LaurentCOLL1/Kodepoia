# Kodepoia continuity state

Last synchronized: 2026-09-14 15:20 CEST  
Repository: `LaurentCOLL1/Kodepoia`  
Canonical branch: `main`  
Canonical `main` SHA: `3721c1e5aec7ded023bf158bb9c2cce0900fa7ad`

## Immediate authority

This file is the current short-form authority for the updater incident discovered during the real Windows `1.1.0-rc5 -> 1.1.0-rc6` exercise. Read it together with `docs/continuity/NEXT.md` before any release or TUF mutation.

The updater correction and rc7 source qualification are complete:

- updater corrective PR: `#456` — qualified head `7d1a23c6f8c6be9a0564ad60f411a8c39e39979b`, merged as `b9f801ef30177ee9b46eeb5bbb32d39e76a13a82`;
- post-corrective continuity PR: `#457`, merged as `35b64846323f80dabe3d349cd2113614e2e3797d`;
- rc7 qualification PR: `#458` — `Release 1.1.0-rc7 — updater corrective candidate`;
- exact qualified rc7 technical source: `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- rc7 merge commit on `main`: `3721c1e5aec7ded023bf158bb9c2cce0900fa7ad`;
- release branch `release/1.1.0-rc7-updater-corrective` still resolves to the exact qualified source `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- all 40 pull-request-triggered workflows on that exact rc7 head completed successfully before merge;
- no failing verification was skipped, disabled or weakened.

## Qualified rc7 installer identity

The authoritative Windows installer is the artifact uploaded by `R17 Windows Installer` run `34802824212` on the exact rc7 source head above:

- GitHub Actions artifact: `KodepoiaSetup-Windows`;
- artifact ID: `10331939170`;
- installer: `KodepoiaSetup.exe`;
- public version: `1.1.0-rc7`;
- source SHA: `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- exact installer length: `37734287` bytes;
- exact installer SHA-256: `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0`;
- `installer-manifest.json` records `production_signed: false`;
- independent inspection of the exact PE shows Authenticode certificate-table offset `0` and size `0`.

Therefore rc7 is genuinely unsigned. The only authorized target-scoped Authenticode policy for this exact artifact is:

`authenticode_policy = "allow-unsigned"`

This does **not** authorize any invalid, broken, untrusted or unknown signature state. TUF authorization, exact length, exact SHA-256 and installer identity/version remain mandatory.

## Current public release and live trusted-repository state

At this checkpoint there is **no** GitHub release tagged `v1.1.0-rc7` yet and there are no concurrent open pull requests.

The latest published prerelease remains rc6 and is unchanged:

- public prerelease: `v1.1.0-rc6`;
- tag/source: `fdd88dfd6cee8408bf33de1c4ee4f70103fda340`;
- asset: `KodepoiaSetup.exe`;
- size: `37712720` bytes;
- SHA-256: `4214f19eea690357ef5aff20b74f9a4733dc1940d8a4315df803e9264ea46e6f`;
- release ID: `387864235`;
- installer asset ID: `561016551`.

Live TUF metadata on `main` is still:

- Root version `2`, expiry `2027-09-08T14:59:19Z`;
- Targets version `6`, expiry `2027-09-12T20:49:31Z`;
- Snapshot version `8`, expiry `2026-09-16T17:44:32Z`;
- Timestamp version `8`, expiry `2026-09-15T17:44:32Z`.

Targets v6 authorizes rc3, rc4, rc5 and rc6 only. rc7 is not yet advertised. Future version numbers must be derived again from live metadata at ceremony time rather than hard-coded from this observation.

## Current boundary — manual draft release creation

The accepted release discipline remains draft-first. The first remaining manual/publication boundary is now the GitHub rc7 **draft prerelease**:

1. create a new draft release for tag `v1.1.0-rc7`;
2. target the existing branch `release/1.1.0-rc7-updater-corrective`, which is pinned to `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
3. mark it as a prerelease;
4. attach only the exact qualified `KodepoiaSetup.exe` above;
5. leave the release in **Draft** state — do not publish it yet;
6. do not create a conflicting Git tag manually;
7. do not run or apply the TUF ceremony until the draft/asset identity has been re-fetched and independently verified.

The TUF ceremony is the next custody-sensitive boundary after the draft is verified. `scripts/Run-TufReleaseCeremony.ps1` deliberately accesses Targets custody material outside the repository and Snapshot/Timestamp signing secrets; private keys, seeds, passphrases and custody paths must never be placed in Git, release assets, logs, documentation or chat.

## Incident status

The client-side updater defect is corrected and rc7 is technically qualified, but the installed-updater E2E incident is **not closed**.

After rc7 is eventually published and TUF-authorized, rc7 must be installed and checked on the real Windows machine. Only after that manual health gate may the validation-only rc8 candidate be created. The incident closes only after a successful real-machine:

`installed rc7 -> discover rc8 -> download -> TUF length/SHA -> target-scoped Authenticode policy -> installer identity -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> search again`

## Security invariants

- no unrelated feature work in rc7 or rc8;
- never mutate rc6 in place;
- no weakening of TUF signature, threshold, rollback, expiry, version, length or hash verification;
- no unconditional unsigned acceptance;
- no shell interpolation of staged paths;
- no private TUF key, seed, passphrase, custody path or signing material in Git, GitHub logs, release assets, documentation or chat;
- re-read live release and metadata state at every publication/signing boundary;
- stop at each manual Windows, publication or custody-sensitive step rather than bypassing it.

## Resume rule

Before the next mutation:

1. read this file and `docs/continuity/NEXT.md`;
2. re-fetch live `main`, open PRs, rc7 draft/public state and Root/Targets/Snapshot/Timestamp;
3. verify that the rc7 draft asset, when present, is exactly `37734287` bytes with SHA-256 `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0` and is bound to source `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
4. if live state differs, live state wins and the discrepancy must be resolved before TUF signing or publication.
