# KODEPOIA CONTINUITY — R19

**Status:** R19.1 MERGED; UNIQUE R19.1 CONTINUITY NORMALIZATION IN PROGRESS

This file remains the active continuation authority for R19. The branch `r19/01-continuity-normalization` is the single authorized post-R19.1 continuity-only normalization. R19.2 is authorized only after this normalization passes fresh exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke and merges into `main` with exact expected-head protection.

## Frozen inherited authority

- Repository: `LaurentCOLL1/Kodepoia`.
- R18 remains **COMPLETE + NORMALIZED** and frozen at R18.11. No `R18.12` is authorized.
- Public prerelease remains `v1.1.0-rc1`, accepted source `c64bac012ef3afa332526a539901b11428fd966f`, installer SHA-256 `3d11af229392a6756a2bbc161af0150aca92168d843a42a3944ab5c01660b8e0`, `production_signed=false`.
- Published `v1.1.0-rc1` assets must not be replaced in place as a normal update mechanism.

## R19 planning authority

Formal phase: **R19 — Installed Experience & Trusted Self-Update Hardening**.

Roadmap authority: `docs/roadmap/R19_PLAN.md`.

Planning PR #408 merged as `main` `c1e8dd2848c0a57a6a4f6c59082cdc111f155df1` after exact-head R0, Python Core and KodeStudio UI acceptance.

Unique planning-normalization PR #409 merged as normalized planning `main` `c586e7f6cfd175c5c6fd81574b3a1b3dd43cee6d` after fresh exact-head R0 Repository Guard, Python Core and KodeStudio UI Smoke. That normalization authorized R19.1.

## Authorized subdivision sequence

1. R19.1 — Language Switching Hardening
2. R19.2 — Production/Beta Update Repository Bootstrap
3. R19.3 — Network UpdateTransport & Packaged Startup Wiring
4. R19.4 — Seamless Windows In-App Update
5. R19.5 — Corrective RC Release Automation & Integrated Acceptance

No subdivision may be silently inserted, removed, merged, split or renumbered.

## R19.1 accepted authority

R19.1 implementation branch: `r19/01-language-switching-hardening`.

Accepted exact implementation HEAD: `f8bb810f459d0af35673e3bb80789e1109dfbb80`.

R19.1 PR #410 merged with `expected_head_sha=f8bb810f459d0af35673e3bb80789e1109dfbb80` as `main` `717b2cc0efd4c59100c5145dd8916c21787137c7`.

Exact accepted-head evidence:

- R0 Repository Guard #2576: **SUCCESS** on Ubuntu and Windows.
- Python Core #2548: **SUCCESS** on Ubuntu and Windows; package-build and KodeStudio smoke evidence jobs also passed.
- KodeStudio UI Smoke #2513: **SUCCESS**.
- R18.7 Update Discovery Channel UX #77: **SUCCESS** on Ubuntu and Windows, including compile, Ruff, focused tests and exact-source evidence.
- R15.15 CLI KodeStudio UX #250: **SUCCESS**.
- Additional R17 Windows Installer validation confirmed the corrected French navigation acceptance (`Discussion` rather than the stale mixed-language `Chat`) before installer packaging continued.

Accepted R19.1 behavior includes:

- merge-safe atomic application preferences rather than locale-only settings replacement;
- persisted user locale precedence over normal OS detection and accidental packaging environment forcing;
- explicit controlled apply/restart behavior for language changes;
- strict English/French v1.1 catalogs with no silent French fallback to English;
- completed French runtime coverage across the KodeStudio shell and assembled Project Wizard surfaces touched by the v1.1 product;
- regression coverage for French/English key parity and placeholders, preference preservation, corrupt-settings fallback, locale precedence, main-window French UI, full French Project Wizard and selector persistence;
- historical R13/R15/R17 assertions aligned with the now-complete French labels instead of preserving mixed-language expectations.

Manual intervention for R19.1: **NONE**.

## R19.1 post-merge continuity normalization

Base `main`: `717b2cc0efd4c59100c5145dd8916c21787137c7`.

Normalization branch: `r19/01-continuity-normalization`.

This branch changes continuity only. It must pass fresh exact-head:

- R0 Repository Guard Ubuntu + Windows;
- full Python Core;
- KodeStudio UI Smoke.

It must then merge with exact expected-head protection. No second R19.1 continuity normalization is authorized.

R19.2 START-sync is authorized **only after** that exact normalization merge enters `main`.

## Defects carried forward after R19.1

The language-selection defect is closed by R19.1. The remaining carried defect is the installed update path: the packaged application still needs a production/beta trusted update repository and later packaged startup wiring so update discovery no longer reports that no structured update repository is configured.

## R19.2 authority and manual boundary

R19.2 — **Production/Beta Update Repository Bootstrap** — may begin only from normalized post-R19.1 `main`.

R19.2 may implement repository layout, schemas, expiry/rotation policy and clearly synthetic local fixtures without manual action. The moment real beta/production TUF private keys must be generated, stored, imported into a secret store or used outside repository-safe synthetic fixtures, stop and provide the user exact manual actions before any later subdivision.

No R19.3 work is authorized before R19.2 is either fully accepted and normalized or explicitly stopped at that genuine manual boundary.

## Security invariants

- Never embed private TUF/AuthentiCode keys, tokens, passwords or certificate private material in source, packages, logs, artifacts or continuity.
- Never silently promote `trusted_root.synthetic.json` into production trust.
- Network update checks never gate normal application startup.
- No update installation occurs without explicit user confirmation after verification.
- GitHub Release assets may carry payloads, but TUF metadata remains the update authorization source.
- RC/beta discovery must not rely only on GitHub `/releases/latest`, which excludes prereleases.

## Resume rule

On a new conversation, verify current `main`, releases, open PRs, exact R19 subdivision status and whether this record has a later normalization. Continue subdivision-by-subdivision with dedicated branch, implementation, exact-head acceptance, expected-head merge and one continuity normalization before the next subdivision. Stop later subdivisions only at a genuine manual intervention boundary and provide exact user actions.
