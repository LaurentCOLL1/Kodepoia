# V2.6.1 — Terminal V2 release identity and compatibility freeze

Status: **FROZEN FOR QUALIFICATION — NO PUBLICATION AUTHORITY**

This document is the human-readable view of the machine-readable contract in
`src/kodepoia/release/terminal_release_freeze.json`.

## Frozen terminal release identity

The terminal V2 public release target is:

- product: **Kodepoia**;
- package: `kodepoia`;
- public version: **`1.1.0`**;
- PEP 440 version: **`1.1.0`**;
- installer version: **`1.1.0`**;
- channel: **stable**;
- build type: **release**;
- canonical tag: **`v1.1.0`**;
- release source binding: **exact-head**.

The terminal scope baseline for V2.6.1 is
`6402041e6c86b21260c9b0fd7176141fff53a0ee`.

This is not the final release-candidate source SHA. V2.6.2 is still authorized to perform
hardening/regression corrections after V2.6.1. Therefore the exact candidate source SHA is
deliberately frozen only in V2.6.3, after V2.6.2 has completed and normalized.

## Transition from the installed/public baseline

The accepted public baseline remains `v1.1.0-rc8`:

- version: `1.1.0-rc8`;
- channel: beta;
- source: `fa787ab7ef76f2556b56ac1f058916a1425455af`;
- installer: `KodepoiaSetup.exe`;
- bytes: `37730750`;
- SHA-256: `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`;
- production signing: not claimed;
- target-scoped updater Authenticode policy: `allow-unsigned`.

The existing `ReleaseIdentity` precedence contract makes `1.1.0` stable/final newer than
`1.1.0-rc8` beta/prerelease. No version reset, downgrade or new major/minor identity is introduced.

Supported installed-upgrade baseline for the terminal release is exactly `1.1.0-rc8`.
Clean installation remains supported.

## Stable and beta channel behavior

The release target belongs to the **stable** channel.

The frozen channel behavior is intentionally explicit:

- stable is the feed for final stable releases;
- beta remains the prerelease feed;
- beta is not silently treated as stable and there is no implicit cross-channel promotion;
- the installed rc8 -> stable rehearsal therefore explicitly selects the stable channel before
  discovering the staged `1.1.0` target.

The frozen staged target identity is:

`channels/stable/windows-x86_64/1.1.0/{source_sha}/KodepoiaSetup.exe`

The exact `source_sha`, byte length and SHA-256 are not invented in V2.6.1. They are produced and
bound later from the exact V2.6.3 candidate.

## Windows installer identity

The terminal release preserves the accepted installer compatibility identity:

- filename: `KodepoiaSetup.exe`;
- application: `Kodepoia`;
- AppId: `{A67EEAB5-46C2-4B21-A169-7E17275DE2F0}`;
- installed executable: `KodepoiaStudio.exe`;
- per-user installation;
- default directory: `{localappdata}\Programs\Kodepoia`;
- custom installation directory remains selectable;
- `UsePreviousAppDir=yes` preserves the existing installation path during upgrades;
- updater handoff remains `/KODEPOIAUPDATE=1`.

Changing these compatibility identities after V2.6.1 invalidates downstream release evidence.

## Authenticode posture

No production Authenticode signing capability is currently verified.

V2.6.1 therefore freezes the following truth:

- production signing is **not claimed**;
- no signing secret/certificate provisioning is authorized here;
- V2.6.3 must report the exact observed signing state;
- if no trusted production signing path exists at V2.6.3, an unsigned terminal installer remains
  permitted only under the already accepted **exact-target** TUF policy
  `authenticode_policy="allow-unsigned"`;
- invalid, broken, malformed or untrusted signatures remain rejected and can never be treated as
  equivalent to unsigned;
- release notes and TUF metadata must state the actual signing posture.

This freeze does not perform signing.

## WinGet decision

**WinGet publication is OUT for Kodepoia 1.1.0.**

The accepted WinGet readiness contract requires verified production signing in addition to a
verified immutable public release and exact installer hash. Production signing is not currently
verified, so V2.6.1 does not make WinGet a blocker for the terminal GitHub/TUF release.

Generating non-publishable WinGet preview evidence remains allowed. Public submission is not.

## Release-note and known-limitation contract

The terminal release notes must retain the established sections for release identity, summary,
validation evidence, known limitations and distribution status.

At minimum the known limitations must state:

1. the exact Authenticode production-signing truth, including possible SmartScreen/reputation
   warnings if the terminal installer remains unsigned;
2. that the installed rc8 -> stable rehearsal explicitly selects the stable update channel;
3. that WinGet publication is out of scope for `v1.1.0`.

No evidence field may imply signing, publication or updater activation that has not actually occurred.

## Terminal feature freeze

After V2.6.1 completes and normalizes, V2 is under a no-new-feature freeze.

Authorized remaining changes are limited to:

- bug fixes;
- security hardening;
- regression fixes;
- release packaging;
- release evidence;
- release documentation.

New product capability is not authorized. V2.7 and R20.7 are not authorized.

## Effect boundary

V2.6.1 performs **no live release effect**. In particular it does not:

- publish a GitHub Release;
- create or repoint the public `v1.1.0` tag;
- upload public assets;
- mutate production TUF metadata;
- activate a live updater target;
- provision signing secrets;
- submit WinGet.

Those publication effects remain reserved to V2.6.6 after V2.6.1 through V2.6.5 complete and
normalize sequentially.
