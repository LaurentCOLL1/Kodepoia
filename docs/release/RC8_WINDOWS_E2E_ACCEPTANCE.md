# Kodepoia 1.1.0-rc8 Windows updater E2E acceptance

Status: **PASS — REAL INSTALLED rc7 -> rc8 PATH COMPLETED**  
Date: 2026-09-14  
Purpose: record the terminal real-machine acceptance for the updater incident that rc8 was created to validate.

## Authority

Qualified rc8 source:

`fa787ab7ef76f2556b56ac1f058916a1425455af`

Public prerelease:

`v1.1.0-rc8`

Authoritative installer:

- file: `KodepoiaSetup.exe`;
- length: `37730750` bytes;
- SHA-256: `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`;
- genuinely unsigned;
- target-scoped TUF policy: `authenticode_policy = "allow-unsigned"`.

TUF authorization transition:

- PR `#464`;
- exact qualified TUF head: `10804c629ca81de8b5e54ddfbfaf53370e88a201`;
- 30/30 PR-triggered workflows completed with conclusion `success` on that exact head;
- merge commit: `1deb84e1b63581ed78ea90480fde2019623d01de`;
- live generation after merge: Root v2 / Targets v8 / Snapshot v10 / Timestamp v10.

The public release/tag/asset were re-fetched before the TUF merge and matched the exact qualified source, installer length and SHA-256 above.

## Real Windows acceptance performed

The operator confirmed that the complete installed updater path succeeded from the already-installed healthy public rc7 baseline to rc8, without manually substituting a separately downloaded rc8 installer.

Observed sequence:

1. KodeStudio `1.1.0-rc7` was running from the installed application.
2. Settings -> Updates was set to the Beta channel.
3. **Check for updates** discovered `1.1.0-rc8` from TUF-verified metadata.
4. **Download and verify installer** completed successfully.
5. The verified installer was launched through Kodepoia only after explicit operator consent.
6. The installer-driven upgrade completed successfully in the existing installation.
7. KodeStudio restarted as `1.1.0-rc8`.
8. A subsequent Beta-channel update check completed successfully and reported rc8 as current.

The operator explicitly reported that the whole sequence completed successfully.

## Step-8 visual evidence

The supplied post-upgrade screenshot shows all of the following simultaneously:

- application title/version: `Kodepoia — KodeStudio — 1.1.0-rc8`;
- installed version: `1.1.0-rc8 (beta)`;
- selected update channel: `Beta`;
- status: `installed version is current for the selected channel`;
- candidate version: `1.1.0-rc8 (beta)`;
- source verification: `tuf-verified-metadata`;
- declared size: `37730750 octets (35.98 MiB)`;
- release note summary: validation-only updater E2E release candidate;
- signature metadata reports unsigned / production trust not claimed;
- download and install buttons are disabled because installed version equals the selected-channel candidate.

This is the required terminal post-upgrade state.

## Acceptance conclusion

The validation objective is satisfied:

`installed rc7 -> discover rc8 -> download -> TUF-authorized verification -> exact target acceptance -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> healthy subsequent update check`

No verification failure was bypassed during the release, TUF authorization, CI qualification or real-machine acceptance sequence.

The historical `rc5 -> rc6` attempt remains failed/incomplete and is not retroactively reclassified.

## Closure-time CI normalization

The first documentation-only closure PR exposed an unrelated hosted Android SDK tooling drift before that PR could be normalized: `android-actions/setup-android@v3` requested the obsolete implicit `tools` package through its default package list.

PR `#466` fixed only that CI setup behavior by setting `packages: ''` in the four affected R13 Android setup steps, while preserving each workflow's explicit SDK package installation and all existing acceptance assertions. Exact head `ab86b7c5b504189c69c4317317a9b7e330a33239` completed 25/25 PR-triggered workflows successfully before merge as `6d53794aa71a7740ca7157e41f2ae37f60f33a80`.

This CI normalization did not change the rc8 product, updater, release artifact, TUF authorization or real-machine acceptance result.

## Incident status

The updater incident that motivated the corrective rc7 and validation-only rc8 sequence is **CLOSED**.

Future updater work may proceed from rc8 as the validated installed baseline, but any new release must still use the established fail-closed release/TUF process and must not weaken signature, hash, length, rollback, expiry, installer-identity or explicit-consent checks.
