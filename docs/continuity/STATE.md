# Kodepoia continuity state

Last synchronized: 2026-09-14 during rc8 validation-only qualification  
Repository: `LaurentCOLL1/Kodepoia`  
Canonical branch: `main`  
Canonical `main` SHA at this checkpoint: `c61347993af70f9167d08f2ff5e46f33f7686b4e`

## Immediate authority

Read this file together with `docs/continuity/NEXT.md` before any updater/release/TUF mutation. Re-fetch live GitHub state before acting: this checkpoint was written while rc8 CI was still running.

The updater corrective path and rc7 publication/TUF authorization are complete. The real Windows rc7 health gate has now also succeeded sufficiently to authorize creation of rc8.

## Completed corrective and rc7 authority

- updater corrective PR `#456` qualified and merged;
- rc7 qualification PR `#458` exact qualified source: `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- rc7 source merge on `main`: `3721c1e5aec7ded023bf158bb9c2cce0900fa7ad`;
- public prerelease `v1.1.0-rc7`, release ID `388454717`;
- rc7 installer asset ID `563538713`;
- rc7 installer length `37734287` bytes;
- rc7 installer SHA-256 `c2e6da8e18d55c9e0397385ec5de9feb5a71b8d283db1d8322a7dff7d9a233c0`;
- rc7 exact tag/source `fafe96ce45c4ca98ef5c40f50c596036071eb6f9`;
- qualified rc7 installer is intentionally unsigned (`production_signed: false`, PE certificate table absent);
- rc7 TUF transition PR `#460` exact qualified head `4976ded7956e20e64e3abd3dffdd7b8fb58cc04d`;
- all 30 PR-triggered workflows on that TUF head completed `success` before merge;
- TUF transition merge `bbcb4313108732a0be2e4828bf2be5cca747904d`;
- no failed verification was skipped, disabled or weakened.

## Live TUF authority before rc8

The last revalidated live generation remains:

- Root v2;
- Targets v7, expiry `2027-09-12T20:49:31Z`;
- Snapshot v9, expiry `2026-09-17T14:53:24Z`;
- Timestamp v9, expiry `2026-09-16T14:53:24Z`.

Targets v7 preserves rc3 through rc6 and authorizes rc7 at:

`channels/beta/windows-x86_64/1.1.0-rc7/fafe96ce45c4ca98ef5c40f50c596036071eb6f9/KodepoiaSetup.exe`

with exact length/SHA above, `withdrawn=false` and:

```json
"authenticode_policy": "allow-unsigned"
```

`allow-unsigned` is target-scoped. It permits only the exact `NotSigned` state for that exact TUF-authorized target. Invalid, broken, untrusted, unknown or malformed signature states remain fail-closed. TUF authorization, exact length, exact SHA-256 and installer identity/version remain mandatory.

## Real Windows rc7 health gate — SUCCEEDED

User-provided real Windows UI evidence on 2026-09-14 shows:

- KodeStudio running `1.1.0-rc7`;
- update channel `Beta`;
- **Check for updates** completes normally;
- installed version is reported current for the selected channel;
- candidate `1.1.0-rc7 (beta)` is read from `tuf-verified-metadata`;
- no PowerShell/AuthentiCode/TUF/installer-identity error is shown.

This health gate proves the installed rc7 updater can perform discovery normally and removes the prior pre-rc8 stop boundary. It does **not** by itself exercise download/staging of `.KodepoiaSetup.exe.partial`, because no newer target existed yet. The full repaired path must therefore be proven by the rc7 -> rc8 E2E.

## rc8 validation-only qualification — ACTIVE

rc8 is authorized solely as a validation candidate. No new updater feature or unrelated change is permitted.

Active PR:

- PR `#462`: `Release 1.1.0-rc8 — validation-only candidate`;
- branch: `release/1.1.0-rc8-validation`;
- base at creation: `main` = `c61347993af70f9167d08f2ff5e46f33f7686b4e`;
- exact rc8 head: `fa787ab7ef76f2556b56ac1f058916a1425455af`;
- diff: exactly 2 files, `+2/-2`;
- `pyproject.toml`: `1.1.0rc7` -> `1.1.0rc8`;
- `src/kodepoia/release/release_identity.json`: serial `7` -> `8`;
- no updater code, dependency, TUF metadata, release asset or unrelated refactor changed.

CI checkpoint on exact head `fa787ab7ef76f2556b56ac1f058916a1425455af`:

- 40 pull-request workflows were triggered;
- 37 had completed with conclusion exactly `success`;
- 3 were still `in_progress` at the checkpoint:
  - `R18.2 Deterministic Release Bundle Acceptance`;
  - `R17 Windows Installer`;
  - `R18.11 Integrated Adversarial Release Update Acceptance`;
- there was no observed failed workflow at the checkpoint;
- notable already-green gates included `R18.1 Release Identity Acceptance`, `R0 Repository Guard`, `Python Core`, `R19.4 Seamless Windows In-App Update Acceptance`, `R19.5 Corrective RC Release Integrated Acceptance`, and `R18.4 Windows Authenticode Signing Acceptance`.

**Do not treat the 37/40 snapshot as final evidence. Re-fetch all workflow runs for the exact rc8 head. PR #462 must not be merged unless every triggered workflow on that exact head is completed with conclusion `success`.**

## Required sequence after rc8 source qualification

If and only if all 40 workflows on the exact rc8 head complete `success`:

1. re-fetch `main`, PR #462 and its exact head; resolve any drift without reusing evidence from another SHA;
2. merge PR #462 only if the qualified exact head is still the intended source;
3. obtain the exact R17 Windows installer produced for the qualified rc8 source and bind its authoritative byte length and SHA-256;
4. determine Authenticode state from the exact artifact, not assumption;
5. follow draft-first release discipline for `v1.1.0-rc8`;
6. prepare the rc8 TUF target with exact source SHA, asset URL, length, SHA-256, `withdrawn=false`, and target-scoped `authenticode_policy` derived from the exact artifact;
7. stage and verify the complete Root/Targets/Snapshot/Timestamp transition before apply;
8. stop for any required offline/custody-sensitive Targets signing or other manual secret-bearing step;
9. publish/authorize rc8 only after all release and TUF gates pass;
10. perform the real Windows E2E from installed rc7 to rc8.

The required E2E is:

`installed rc7 -> discover rc8 -> download -> verified TUF metadata -> exact length -> exact SHA-256 -> target-scoped Authenticode policy -> installer identity -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> search again`

Only that successful path closes the updater incident.

The historical `rc5 -> rc6` attempt remains failed/incomplete and must never be retroactively relabeled successful.

## Security and process invariants

- no unrelated feature work in rc8;
- do not mutate rc6 or rc7 assets in place;
- no weakening of TUF signature, threshold, rollback, expiry, version, length or hash verification;
- no unconditional unsigned acceptance;
- no shell interpolation of staged paths;
- no private TUF key, seed, passphrase, custody path or signing material in Git, GitHub logs, release assets, documentation or chat;
- never reuse green CI evidence from a different source SHA;
- for rc8 qualification require conclusion exactly `success` for every triggered workflow; do not interpret `skipped`/`neutral` as equivalent for this release gate;
- re-fetch live release and metadata state at every publication/signing boundary;
- stop at each manual Windows, publication or custody-sensitive step rather than bypassing it.

## Resume rule

Before the next mutation:

1. read this file and `docs/continuity/NEXT.md`;
2. re-fetch live `main`, open PRs and PR #462;
3. verify PR #462 head is still `fa787ab7ef76f2556b56ac1f058916a1425455af` before using the recorded CI evidence;
4. re-fetch all PR-triggered workflow runs for that exact SHA and require all 40 to be `completed/success` before merge;
5. if any workflow failed, stop and diagnose it; do not bypass, reroute or weaken the gate;
6. if the head SHA changed, discard the old qualification result and qualify the new exact head from scratch;
7. if conversation context is lost, live GitHub state wins over this snapshot and any discrepancy must be resolved first.
