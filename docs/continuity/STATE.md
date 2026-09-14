# Kodepoia continuity state

Last synchronized: 2026-09-14 04:50 CEST  
Repository: `LaurentCOLL1/Kodepoia`  
Canonical branch: `main`  
Canonical `main` SHA: `b9f801ef30177ee9b46eeb5bbb32d39e76a13a82`

## Immediate authority

This file is the current short-form authority for the updater incident discovered during the real Windows `1.1.0-rc5 -> 1.1.0-rc6` exercise. Read it together with `docs/continuity/NEXT.md` before any release mutation.

The updater-only corrective implementation is now **qualified and merged**:

- corrective PR: `#456` — `Fix updater PowerShell paths and TUF Authenticode policy`;
- exact qualified corrective head: `7d1a23c6f8c6be9a0564ad60f411a8c39e39979b`;
- merge commit on `main`: `b9f801ef30177ee9b46eeb5bbb32d39e76a13a82`;
- every pull-request-triggered workflow returned `completed/success` on the exact qualified head before merge;
- Python Core Windows executed the complete suite on that exact head: `2417 passed, 26 skipped, 0 failed`;
- R17 Windows Installer passed build, exact-source provenance, custom-directory silent install, packaged updater smoke and uninstall;
- R18.11 Integrated Adversarial Release Update passed fresh R18.1-R18.10 regressions, exact-source candidate build, immutable R17 fixture rebuild, clean install, upgrade, packaged smoke, uninstall and final integrated verdict;
- R0, R18.6, R18.7, R18.8, R18.10, R19.2, R19.3, R19.4 and R19.5 all passed on the same exact corrective head, along with the repository-wide platform/build workflows triggered by the PR.

No failing check was bypassed. Earlier Windows and Apple transient/failing attempts were corrected or re-run on later exact heads; only the final exact qualified head above was used for merge authority.

## Corrective behavior now in `main`

The merged updater correction preserves fail-closed trust semantics:

1. Both PowerShell verifier paths use fixed executable PowerShell code. The staged installer path is transported as process data via `KODEPOIA_UPDATER_LITERAL_PATH`; the path is never concatenated into `-Command` text.
2. Path dereference uses `-LiteralPath`, covering normal Windows paths with spaces and the updater staging form `.KodepoiaSetup.exe.partial`.
3. Authenticode verification of the staged partial file evaluates its bytes as executable content while retaining literal path dereference.
4. Trusted TUF target metadata may carry exactly one structured key: `authenticode_policy`.
5. Accepted policy values are exactly:
   - `require-valid`;
   - `allow-unsigned`.
6. Missing policy defaults to `require-valid`.
7. Unknown, malformed or contradictory policy fails closed.
8. `allow-unsigned` permits only the exact Authenticode `NotSigned` state for that exact TUF-authorized target; invalid, broken, untrusted or unknown signature states remain rejected.
9. Legacy `signing_status` remains informational and never authorizes an unsigned installer.
10. Verified TUF metadata provenance, non-withdrawn state, exact target length, exact SHA-256 and installer identity/version remain mandatory before installation can proceed.

## Current public release / trusted repository state

The already-published rc6 release was not mutated by the corrective work:

- public prerelease: `v1.1.0-rc6`;
- tag/source: `fdd88dfd6cee8408bf33de1c4ee4f70103fda340`;
- asset: `KodepoiaSetup.exe`;
- size: `37712720` bytes;
- SHA-256: `4214f19eea690357ef5aff20b74f9a4733dc1940d8a4315df803e9264ea46e6f`;
- release ID: `387864235`;
- installer asset ID: `561016551`.

Trusted update metadata remained unchanged through the corrective merge:

- Root version `2`;
- Targets version `6`;
- Snapshot version `8`;
- Timestamp version `8`.

The rc6 target has no structured `authenticode_policy`, therefore the corrected client treats rc6 as `require-valid`. The historical free-text `signing_status` for rc6 does not become an authorization bypass.

The older `docs/release/RC6_VALIDATION_CONTINUITY.md` retains historical pre-build wording and is not the live authority for rc6 identity or current corrective status.

## Incident status

The **client-side updater defect is corrected and merged**, but the installed-updater E2E incident is **not yet closed**.

Do not claim the historical `rc5 -> rc6` attempt succeeded retroactively. A fresh transition must validate the repaired updater using the already accepted sequence:

`installed rc7 -> discover rc8 -> download -> TUF length/SHA -> Authenticode policy -> installer identity -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> search again`

Only a complete successful real-machine `rc7 -> rc8` path closes the updater E2E incident.

## Security invariants for the remaining release sequence

- no unrelated feature work in rc7 or rc8;
- never mutate the already-published rc6 asset or rewrite its history;
- no weakening of TUF signature, threshold, rollback, expiry, version, length or hash verification;
- no unconditional unsigned acceptance;
- no shell interpolation of staged paths;
- no private TUF key, seed, passphrase, custody path or signing material in Git, GitHub logs, release assets, documentation or chat;
- use current live metadata when selecting future TUF versions; never infer next versions solely from stale continuity prose;
- stop at any manual Windows, offline Targets-signing, public-release publication or other custody-sensitive boundary and record the exact required intervention before proceeding further.

## Resume rule

A new ChatGPT conversation must first:

1. read `docs/continuity/STATE.md`;
2. read `docs/continuity/NEXT.md`;
3. re-fetch live `main`, open PRs, current public release/tag state and current Root/Targets/Snapshot/Timestamp;
4. compare live state with the identities recorded here before creating an rc7 release branch or changing metadata.

If live GitHub state differs, live repository/release state wins and the difference must be recorded before proceeding.
