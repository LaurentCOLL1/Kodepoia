# V2.6.5 — Installed Windows release rehearsal and pre-publication go/no-go

Status: **IMPLEMENTATION / QUALIFICATION — PRE-PUBLICATION ONLY — NO LIVE RELEASE AUTHORITY**

V2.6.5 performs the final installed-Windows rehearsal for the frozen Kodepoia 1.1.0
candidate. It reuses the accepted V2.6.3 candidate bytes and the accepted V2.6.4 transition
intent. It does not create the public release, mutate live TUF metadata, activate the live updater,
or authorize V2.6.6 before post-merge normalization.

## Frozen inputs

Public installed baseline:

- version: `1.1.0-rc8`;
- exact source/tag target: `fa787ab7ef76f2556b56ac1f058916a1425455af`;
- installer: `KodepoiaSetup.exe`;
- length: `37,730,750` bytes;
- SHA-256: `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`;
- target-scoped Authenticode policy: `allow-unsigned`.

Frozen terminal candidate:

- version/channel/build: `1.1.0` / stable / release;
- source SHA: `46ed800888b4f19da9e984232dd1ad6cdb639cc1`;
- installer length: `38,834,833` bytes;
- installer SHA-256: `8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef`;
- V2.6.3 acceptance evidence SHA-256:
  `80192b517ebd6a607536f52892e5b23d05448138e63d7d222c30c7f4444dc3d8`;
- accepted V2.6.3 artifact run: `37151521725`;
- accepted artifact ID: `11284279492`.

Accepted V2.6.4 transition request:

- accepted V2.6.4 head: `addbaf43b286f825ce42a11176c6647d15748845`;
- request SHA-256: `a44914e80fb2fafb6b03f2a9847a78805b1ccb2a87fafedae9199f66c88bacea`;
- stable target:
  `channels/stable/windows-x86_64/1.1.0/46ed800888b4f19da9e984232dd1ad6cdb639cc1/KodepoiaSetup.exe`;
- requested role generations: Root v2 / Targets v9 / Snapshot v11 / Timestamp v11;
- exact-target Authenticode policy: `allow-unsigned`.

The production repository itself remains at Root v2 / Targets v8 / Snapshot v10 / Timestamp v10.
Snapshot/Timestamp are still expired and must continue to fail closed. V2.6.5 does not repair,
refresh, sign, or mutate those live metadata files.

## Exact candidate artifact reuse

V2.6.5 does not rebuild the terminal candidate and then pretend the new bytes are the frozen
candidate. The Windows acceptance downloads the still-retained V2.6.3 accepted Actions artifact by
its exact run/name and verifies its source binding, candidate acceptance evidence, installer length,
and SHA-256 before use.

This preserves the exact candidate bytes that V2.6.3 qualified even though the existing R18
two-build evidence correctly established only semantic equivalence rather than byte-for-byte
determinism.

## Installed Windows rehearsal

The dedicated Windows gate performs this sequence:

1. fetch and verify the public rc8 release/tag/installer read-only;
2. install the exact public rc8 installer into a non-default custom directory;
3. confirm rc8 ProductVersion and execute packaged smoke with developer Python/pip hidden;
4. create independent project, user-data and QSettings sentinels;
5. reconstruct and verify the exact accepted V2.6.4 transition request;
6. use an isolated synthetic TUF repository to discover the exact stable target from the rc8
   installed identity;
7. stage the exact frozen candidate through the existing TUF/hash/length/installer-identity and
   target-scoped `allow-unsigned` verification path;
8. launch only those staged verified bytes with the existing fixed Inno update arguments;
9. require installer-driven KodeStudio relaunch;
10. verify installed ProductVersion `1.1.0` in the original custom directory and verify that the
    default installation directory was not silently used;
11. run packaged smoke again;
12. verify project/settings/user-data preservation after upgrade;
13. verify a subsequent isolated staged check reports `up-to-date` for installed `1.1.0`;
14. uninstall the upgraded installation and verify the installed executable is removed;
15. verify project/settings/user-data sentinels remain after uninstall;
16. clean-install the same exact staged candidate bytes into a second custom directory;
17. confirm ProductVersion `1.1.0`, run packaged smoke, uninstall and confirm clean removal;
18. run the existing R18.10 incident/recovery drill and require the last-known-good recovery
    scenario to remain `RECOVER`;
19. aggregate all results into the final V2.6.5 critical-veto report.

The synthetic TUF repository is deliberately labeled `fixture_only` and
`production_proof=false`. Its purpose is to exercise the updater against the exact frozen
candidate bytes without touching production metadata. It cannot be substituted for the later
production signing/publication evidence required in V2.6.6.

## Critical veto / go-no-go

V2.6.5 reports `GO` only when every frozen binding and every installed-Windows check succeeds.
Any mismatch or failure is a critical veto, including:

- rc8 public asset/tag/source/hash/length drift;
- V2.6.3 candidate source/evidence/hash/length drift;
- V2.6.4 request digest or target-policy drift;
- failure to discover or stage the exact candidate;
- candidate verification failure;
- clean rc8 installation or packaged smoke failure;
- exact-candidate clean installation, smoke or clean-uninstall failure;
- custom-directory loss;
- missing installer-driven relaunch;
- wrong installed version after upgrade;
- project/settings/user-data loss;
- post-upgrade staged check not reporting current/up-to-date;
- uninstall failure;
- incident/recovery drill failure;
- any public release, tag, asset, live TUF, live updater, signing-secret or WinGet effect.

No averaging or partial success can override a veto.

## Publication-input freeze

A passing report freezes the inputs that a later V2.6.6 may consume:

- public version/tag: `1.1.0` / `v1.1.0`;
- exact candidate source SHA;
- exact installer byte length and SHA-256;
- exact stable TUF target path;
- exact-target `allow-unsigned` policy;
- `production_signed=false` truth;
- WinGet decision `out`;
- V2.6.3 evidence SHA-256;
- V2.6.4 transition-request SHA-256.

This freeze is evidence only. It does not itself authorize or perform publication.

## Effect boundary

V2.6.5 performs **no public GitHub Release**, no public tag creation/repointing, no public asset
upload, **no live production TUF mutation**, no production signing ceremony, no live updater
activation, no production signing-secret provisioning and no WinGet submission.

V2.6.6 remains unauthorized until V2.6.5:

1. passes all exact-head required workflows on one unchanged SHA;
2. merges with `expected_head_sha` protection; and
3. completes post-merge normalization that explicitly authorizes V2.6.6.

A real manual operator step is therefore not required by V2.6.5. Any later protected production
signing/publication or real-machine live-updater step belongs only to V2.6.6.
