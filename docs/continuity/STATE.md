# Kodepoia continuity state

Last synchronized: 2026-09-13 22:59 CEST  
Repository: `LaurentCOLL1/Kodepoia`  
Canonical branch: `main`  
Canonical `main` SHA at handoff: `f8e7857da0605f76ae7009181a7e4b9839e9ae41`

## Immediate authority

This file is the current short-form handoff for the updater validation incident discovered during the real Windows `1.1.0-rc5 -> 1.1.0-rc6` exercise. It supplements the long continuity history and must be read together with `docs/continuity/NEXT.md` before any new mutation.

The older `docs/release/RC6_VALIDATION_CONTINUITY.md` still contains its pre-build wording (`PLANNED — NOT YET BUILT OR PUBLISHED`). That historical file is no longer a reliable statement of the live rc6 state. Re-read GitHub live state before using any identity from it.

## Current public release / repository state

- `main` is at `f8e7857da0605f76ae7009181a7e4b9839e9ae41`, merge of PR `#454` (`release/1.1.0-rc6-tuf-transition`).
- No pull request is open at the time of this handoff.
- Public prerelease `v1.1.0-rc6` exists and is published.
- `v1.1.0-rc6` tag resolves to exact source commit `fdd88dfd6cee8408bf33de1c4ee4f70103fda340`.
- Public rc6 asset: `KodepoiaSetup.exe`.
- Public rc6 asset size: `37712720` bytes.
- Public rc6 asset SHA-256: `4214f19eea690357ef5aff20b74f9a4733dc1940d8a4315df803e9264ea46e6f`.
- rc6 release ID: `387864235`; installer asset ID: `561016551`.
- The rc6 TUF transition has already been merged into `main`; do not recreate or replace it merely to repair the client-side updater defect described below.

## Real-machine finding that blocks declaring the updater E2E validated

The real Windows rc5 -> rc6 path progressed far enough to expose an updater verification defect. The correction scope was explicitly accepted and is intentionally narrow: **updater only**.

The defect family to repair is:

1. PowerShell invocation/path handling must safely support the updater's staged installer path, including the hidden partial filename form such as `.KodepoiaSetup.exe.partial` and installation/cache paths containing spaces or other normal Windows path characters.
2. Both PowerShell-based verifier paths must use fixed code and `-LiteralPath`; user/model-controlled shell text must never be evaluated.
3. Authenticode acceptance must be governed by an explicit policy carried by trusted TUF target metadata. Default behavior remains fail-closed: require `Valid`. `NotSigned` may be accepted **only** when the target metadata explicitly declares that policy for that exact authorized installer.
4. TUF authorization, exact target length, and SHA-256 verification remain mandatory regardless of Authenticode policy. The corrective work must not turn any verification failure into a blanket bypass.
5. Windows-focused regression tests must cover the exact staged `.partial` path and the Authenticode policy matrix.

## Security invariants

The following constraints are non-negotiable for the corrective branch:

- no feature work;
- no unrelated refactor or dependency upgrade;
- no weakening of TUF signature/threshold/version/hash/length verification;
- no unconditional acceptance of unsigned installers;
- no shell interpolation of the staged installer path;
- no private TUF key, seed, passphrase, custody path or signing material in Git, GitHub logs, release assets, documentation, or chat;
- fail closed on missing/unknown Authenticode policy.

## Release sequencing decision already accepted

Do **not** mutate the already-published rc6 asset as a shortcut. The next release work is to qualify the updater-only correction in a later prerelease, then perform a fresh real-machine E2E transition with a still-newer validation candidate. The detailed sequence and acceptance gates are in `docs/continuity/NEXT.md`.

## Resume rule

A new ChatGPT conversation must first:

1. read `docs/continuity/STATE.md`;
2. read `docs/continuity/NEXT.md`;
3. re-fetch live `main`, open PRs, the rc6 release/tag, and current trusted TUF metadata;
4. compare live state with the SHA and identities above before writing code.

If live GitHub state differs, the live repository/release state wins and the difference must be recorded before proceeding.
