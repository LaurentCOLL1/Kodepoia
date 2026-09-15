# Kodepoia next actions

Last synchronized: 2026-09-15 after successful real Windows rc7 -> rc8 updater E2E, closure-time CI normalization and rc8 public-documentation alignment  
Companion state: `docs/continuity/STATE.md`

## Goal

The updater corrective/validation sequence is complete:

`rc7 corrective release -> healthy installed rc7 -> validation-only rc8 -> exact-source qualification -> draft-first publication -> qualified TUF authorization -> real Windows updater E2E rc7 -> rc8`

The real-machine E2E succeeded and the updater incident is **CLOSED**.

The historical `rc5 -> rc6` attempt remains failed/incomplete and must never be relabeled successful.

The active user-facing/current-state documentation is aligned with this closure: `README.md`, `KODEPOIA_CURRENT_AUTHORITY.md`, `STATE.md`, this file and the explicitly current post-R20 section of `KODEPOIA_CONTINUITY_R20.md` all identify rc8 as the current validated beta authority. Older frozen continuity text remains historical evidence.

## Completed authority

- exact rc8 source: `fa787ab7ef76f2556b56ac1f058916a1425455af`;
- source PR `#462`: 40/40 exact-head workflows `completed/success` before merge;
- authoritative installer: `KodepoiaSetup.exe`;
- installer length: `37730750` bytes;
- installer SHA-256: `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`;
- public prerelease: `v1.1.0-rc8`, tag resolving directly to the exact source;
- target-scoped policy: `authenticode_policy = "allow-unsigned"` for this genuinely unsigned exact artifact;
- TUF PR `#464`, exact head `10804c629ca81de8b5e54ddfbfaf53370e88a201`;
- TUF exact-head qualification: 30/30 workflows `completed/success`;
- TUF merge: `1deb84e1b63581ed78ea90480fde2019623d01de`;
- live TUF generation after rc8: Root v2 / Targets v8 / Snapshot v10 / Timestamp v10;
- seven push-triggered workflows on the TUF merge completed successfully;
- real installed Windows rc7 -> rc8 updater E2E: PASS;
- closure-time CI normalization PR `#466`, exact head `ab86b7c5b504189c69c4317317a9b7e330a33239`: 25/25 PR-triggered workflows `completed/success` before merge;
- CI normalization merge: `6d53794aa71a7740ca7157e41f2ae37f60f33a80`;
- canonical E2E closure PR `#467`, exact head `a6e67e0ad052275e6b2bf069a50c127ec4043fdf`: 25/25 PR-triggered workflows `completed/success` before merge;
- closure merge: `e40477699d98bda2f804c269339929de719556b5`, followed by seven successful push-triggered workflows;
- current README/current-authority documentation is aligned to rc8 and does not change product/release/TUF semantics.

See `docs/release/RC8_WINDOWS_E2E_ACCEPTANCE.md` for the terminal acceptance evidence.

## Current boundary

There is **no remaining rc8 corrective action** required by this incident.

Do not create another release candidate merely to repeat the already-successful rc7 -> rc8 validation. Do not reopen R20 or invent `R20.7`; R20 remains complete/normalized unless a separately approved roadmap change explicitly says otherwise.

Do not create a follow-up release/TUF mutation merely to make documentation mention its own normalization commit. Documentation normalization is complete once its exact-head checks pass and it is merged; future sessions should re-fetch live `main` rather than recursively writing every documentation merge SHA back into current-state files.

The next work should come from the normal project roadmap or an explicit new user request, not from the now-closed updater incident.

## If future work touches the updater or releases

Before any new updater/release/TUF mutation:

1. re-fetch live `main`;
2. re-fetch the latest public release/tag/asset;
3. re-read live Root/Targets/Snapshot/Timestamp metadata;
4. treat rc8 as the last real-machine E2E-validated Windows baseline unless later continuity supersedes it;
5. preserve exact-source qualification and draft-first release discipline;
6. preserve TUF exact length/SHA binding, signature/threshold/rollback/version/expiry checks and installer identity verification;
7. keep Authenticode exceptions target-scoped only;
8. require explicit user consent before installer launch;
9. stop on any failed verification rather than bypassing it;
10. never expose private signing keys, seeds, passphrases or custody paths.

## If future work is unrelated to updater/release

Use the project roadmap and current repository state as authority. The rc8 sequence imposes no additional feature freeze now that its E2E validation has succeeded.

## Resume prompt

`@Recherche sur le Web Reprends Kodepoia depuis docs/continuity/STATE.md et docs/continuity/NEXT.md. Le correctif updater est clos : rc8 source fa787ab7ef76f2556b56ac1f058916a1425455af est public, TUF-autorisé et le vrai E2E Windows rc7 -> rc8 a réussi. README.md, KODEPOIA_CURRENT_AUTHORITY.md et l'autorité post-R20 sont alignés sur rc8. Revalide d'abord le main live, la release publique rc8 et les métadonnées TUF live, puis suis la roadmap ou ma prochaine demande sans rouvrir artificiellement l'incident updater ni inventer R20.7.`
