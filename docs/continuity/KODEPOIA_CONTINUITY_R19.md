# KODEPOIA CONTINUITY — R19

**Status:** R19 PLANNING CANDIDATE — supersedes `KODEPOIA_CONTINUITY_V2_POST_R18.md` only after the planning PR and unique planning normalization are merged.

## Frozen inherited authority

- Repository: `LaurentCOLL1/Kodepoia`.
- Planning branch point: canonical `main` `d0ba02f9d8101890602c5e1a412292cb27aa08c3`.
- R18 remains **COMPLETE + NORMALIZED** and frozen at R18.11. No `R18.12` is authorized.
- Public prerelease remains `v1.1.0-rc1`, accepted source `c64bac012ef3afa332526a539901b11428fd966f`, installer SHA-256 `3d11af229392a6756a2bbc161af0150aca92168d843a42a3944ab5c01660b8e0`, `production_signed=false`.
- Published `v1.1.0-rc1` assets must not be replaced in place as a normal update mechanism.

## R19 phase authority

Formal phase: **R19 — Installed Experience & Trusted Self-Update Hardening**.

Roadmap authority: `docs/roadmap/R19_PLAN.md`.

Authorized subdivision sequence after planning is COMPLETE + NORMALIZED:

1. R19.1 — Language Switching Hardening
2. R19.2 — Production/Beta Update Repository Bootstrap
3. R19.3 — Network UpdateTransport & Packaged Startup Wiring
4. R19.4 — Seamless Windows In-App Update
5. R19.5 — Corrective RC Release Automation & Integrated Acceptance

No subdivision may be silently inserted, removed, merged, split or renumbered.

## Defects carried into R19

1. Installed French Windows application does not visibly switch the current UI when English is selected. Existing code only persists the selection for a later start, rewrites the settings file with a locale-only object, and currently places `KODEPOIA_LOCALE` ahead of the saved preference.
2. Installed update check reports `no structured update repository is configured` because packaged startup does not construct/inject the production discovery and install services.

## Security and manual-intervention boundaries

- Never embed private TUF/AuthentiCode keys, tokens, passwords or certificate private material in source, packages, logs, artifacts or continuity.
- Never silently promote `trusted_root.synthetic.json` into production trust.
- Network update checks never gate normal application startup.
- No update installation occurs without explicit user confirmation after verification.
- R19.2 may proceed through repository layout/schema/synthetic fixtures without manual intervention, but must stop exactly when real TUF private-key creation/custody or external secret configuration becomes necessary.
- R19.5 similarly stops at any unavailable external signing/credential/publication boundary.

## Planning work cycle

Dedicated branch: `r19/plan-installed-experience-self-update`.

Planning candidate currently contains only roadmap/continuity documentation and therefore has no runtime product effect.

Before merge, exact candidate HEAD must pass:

- R0 Repository Guard Ubuntu + Windows;
- full Python Core acceptance;
- KodeStudio UI Smoke Windows.

Planning PR must merge with exact expected-head protection. Then one and only one continuity-only planning-normalization branch/PR must record the actual merge SHA and fresh exact-head gates. R19.1 starts only from that normalized `main`.

## Web-verified planning constraints

- Official TUF documentation continues to define Root, Targets, Snapshot and Timestamp as the four required top-level roles. Targets bind hashes/sizes, Snapshot provides consistency, and Timestamp limits stale/frozen metadata exposure.
- GitHub documents `GET /releases/latest` as returning the latest non-prerelease, non-draft release, so RC/beta discovery cannot rely on that endpoint alone.

## Resume rule

On a new conversation, verify current `main`, current releases, open PRs, exact planning/R19 subdivision status and whether this file has been superseded by a later R19 continuity normalization. Continue subdivision-by-subdivision with branch, implementation, exact-head acceptance, expected-head merge and continuity normalization. Stop later subdivisions only at a genuine manual intervention boundary and provide exact user actions.
