# KODEPOIA CONTINUITY — R19

**Status:** R19 PLANNING ACCEPTED; UNIQUE PLANNING NORMALIZATION IN PROGRESS

This file supersedes `KODEPOIA_CONTINUITY_V2_POST_R18.md` as the active continuation authority once the unique planning-normalization PR from `r19/plan-continuity-normalization` passes fresh exact-head gates and merges.

## Frozen inherited authority

- Repository: `LaurentCOLL1/Kodepoia`.
- R18 remains **COMPLETE + NORMALIZED** and frozen at R18.11. No `R18.12` is authorized.
- Public prerelease remains `v1.1.0-rc1`, accepted source `c64bac012ef3afa332526a539901b11428fd966f`, installer SHA-256 `3d11af229392a6756a2bbc161af0150aca92168d843a42a3944ab5c01660b8e0`, `production_signed=false`.
- Published `v1.1.0-rc1` assets must not be replaced in place as a normal update mechanism.

## R19 planning authority

Formal phase: **R19 — Installed Experience & Trusted Self-Update Hardening**.

Roadmap authority: `docs/roadmap/R19_PLAN.md`.

Planning base: `main` `d0ba02f9d8101890602c5e1a412292cb27aa08c3`.

Planning candidate head: `7feabbcd1d718458d248e03b1bb82e4b88d5f25a` on `r19/plan-installed-experience-self-update`.

Exact planning-head acceptance:

- R0 Repository Guard #2566 / run `34139219887`: **SUCCESS**.
- Python Core #2538 / run `34139219864`: **SUCCESS**; exact-source Ubuntu and Windows core jobs passed, alongside package/UI evidence jobs.
- KodeStudio UI Smoke #2503 / run `34139219905`: **SUCCESS**.

Planning PR #408 merged with `expected_head_sha=7feabbcd1d718458d248e03b1bb82e4b88d5f25a` as planning `main` `c1e8dd2848c0a57a6a4f6c59082cdc111f155df1`.

This branch `r19/plan-continuity-normalization` is the **single authorized planning-normalization branch**. It changes continuity only. It must pass fresh R0 Repository Guard Ubuntu+Windows, full Python Core and KodeStudio UI Smoke on its exact HEAD, then merge with exact expected-head protection. No second R19 planning normalization is authorized.

R19.1 START-sync is authorized **only after** that exact normalization merge enters `main`.

## Authorized subdivision sequence

1. R19.1 — Language Switching Hardening
2. R19.2 — Production/Beta Update Repository Bootstrap
3. R19.3 — Network UpdateTransport & Packaged Startup Wiring
4. R19.4 — Seamless Windows In-App Update
5. R19.5 — Corrective RC Release Automation & Integrated Acceptance

No subdivision may be silently inserted, removed, merged, split or renumbered.

## Defects carried into R19

1. Installed French Windows application does not visibly switch the current UI when English is selected. Existing code only persists the selection for a later start, rewrites the settings file with a locale-only object, and currently places `KODEPOIA_LOCALE` ahead of the saved preference.
2. Installed update check reports `no structured update repository is configured` because packaged startup does not construct/inject the production discovery and install services.

## R19.1 authority

R19.1 must introduce merge-safe application preferences, make the user's persisted locale defeat normal OS detection and accidental packaging environment forcing, and provide an immediate retranslation or explicit controlled apply/restart behavior. French → English → French persistence, unrelated-setting preservation, corrupt-settings fallback and packaged Windows restart behavior are mandatory acceptance cases.

Manual intervention for R19.1: **NONE**.

## R19.2 manual boundary

R19.2 may implement repository layout, schemas, expiry/rotation policy and clearly synthetic local fixtures without manual action. The moment real beta/production TUF private keys must be generated, stored, imported into a secret store or used outside repository-safe synthetic fixtures, stop and provide the user exact manual actions before any later subdivision.

## Security invariants

- Never embed private TUF/AuthentiCode keys, tokens, passwords or certificate private material in source, packages, logs, artifacts or continuity.
- Never silently promote `trusted_root.synthetic.json` into production trust.
- Network update checks never gate normal application startup.
- No update installation occurs without explicit user confirmation after verification.
- GitHub Release assets may carry payloads, but TUF metadata remains the update authorization source.
- RC/beta discovery must not rely only on GitHub `/releases/latest`, which excludes prereleases.

## Resume rule

On a new conversation, verify current `main`, releases, open PRs, exact R19 subdivision status and whether this record has a later normalization. Continue subdivision-by-subdivision with dedicated branch, implementation, exact-head acceptance, expected-head merge and one continuity normalization before the next subdivision. Stop later subdivisions only at a genuine manual intervention boundary and provide exact user actions.
