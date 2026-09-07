# KODEPOIA CONTINUITY — R19

**Status:** R19.4 MERGED; UNIQUE R19.4 CONTINUITY NORMALIZATION IN PROGRESS

This file remains the active continuation authority for R19. R19.4 implementation is accepted and merged. The branch `r19/04-continuity-normalization` is the single authorized post-R19.4 continuity-only normalization. R19.5 is authorized only after this normalization passes fresh exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke and merges into `main` with exact expected-head protection.

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

R19.1 normalization branch: `r19/01-continuity-normalization`.

Accepted exact normalization HEAD: `eb2cb73e468819850289a3174afcb99bb5c0438d`.

PR #411 merged with exact-head protection as normalized `main` `fd7736adc565c3c3cb169d8223c5841e86bbbe9d`. That single normalization authorized R19.2. No second R19.1 continuity normalization is authorized.

## R19.2 accepted authority

R19.2 implementation branch: `r19/02-update-repository-bootstrap`.

Accepted exact implementation HEAD: `356d0b29521155ef06c03e3342336532ac1dd0f1`.

R19.2 PR #412 merged with `expected_head_sha=356d0b29521155ef06c03e3342336532ac1dd0f1` as `main` `59bb064127b16c1374493ad8f3e0e7b48d23aab5`.

Exact accepted-head evidence:

- R19.2 Production/Beta Update Repository Bootstrap Acceptance #29: **SUCCESS** on Ubuntu and Windows, including compile, Ruff, focused trust tests, 12/12 exact-source acceptance, public-key-only checks, wheel build and exact embedded production Root verification.
- R0 Repository Guard #2587: **SUCCESS** on Ubuntu and Windows.
- Python Core #2559: **SUCCESS** on Ubuntu and Windows; Ubuntu full suite reported 2296 passed / 24 skipped, and both platform package-build jobs plus the KodeStudio Windows evidence job passed.
- KodeStudio UI Smoke #2524: **SUCCESS**.
- R16.9 Supply Chain Provenance Acceptance #208: **SUCCESS** on Ubuntu and Windows after registering the R19.2 acceptance workflow as an immutable pinned authority workflow and synchronizing the integrity test.

Accepted R19.2 behavior includes:

- active production/beta TUF Root v1 packaged at `src/kodepoia/update/trusted_root.production.json`;
- production Root SHA-256 `a036c2aac78092f8d46893cc18954bb64f2b998375ff230f996dc4b85157e9ed`;
- Root threshold 2-of-3 with three independent Ed25519 Root keys;
- distinct Targets, Snapshot and Timestamp role keys;
- public signed `root.json`, `targets.json`, `snapshot.json` and `timestamp.json` published under `update-repository/metadata/`;
- packaged production Root bytes exactly equal published `root.json` bytes;
- initial Targets v1 intentionally authorizes no installer target before an exact corrective release artifact exists;
- canonical HTTPS metadata base `https://raw.githubusercontent.com/LaurentCOLL1/Kodepoia/main/update-repository/metadata/`;
- GitHub Release assets remain payload storage while TUF metadata is the authorization authority;
- R18 `trusted_root.synthetic.json` remains acceptance-only, explicit-opt-in and cryptographically distinct from production trust;
- no private TUF key material is persisted, packaged, logged, uploaded as CI evidence or used by repository acceptance automation;
- supply-chain authority remains least-privilege and external Actions remain pinned to full commit SHAs.

The supplied bootstrap satisfied the R19.2 manual boundary using **public signed material only**. Repository work never generated, imported, persisted or used production private keys.

Manual intervention for R19.2: **NONE required to finalize the repository subdivision**.

Operational expiry note: initial Snapshot v1 and Timestamp v1 expire at `2026-09-08T19:02:56Z`; they must be renewed before that instant with valid monotonically versioned signed metadata. Root and Targets expire at `2027-09-07T19:02:56Z`. This short Snapshot/Timestamp policy is deliberate freeze/staleness protection, not authorization to embed online private keys in the repository.

## R19.2 post-merge continuity normalization

R19.2 normalization branch: `r19/02-continuity-normalization`.

Accepted exact normalization HEAD: `07a867afe06604f1795cde7cafc7a08206321ef9`.

PR #413 merged with exact-head protection as normalized `main` `5790004ed4fd5ec9679adbf8a3c8e4d599744683`. That single normalization authorized R19.3. No second R19.2 continuity normalization is authorized.

## R19.3 accepted authority

R19.3 implementation branch: `r19/03-network-update-transport`.

Accepted exact implementation HEAD: `d3c1364b5d7f4015a7205f16f0158e301c5c2e81`.

R19.3 PR #414 merged with `expected_head_sha=d3c1364b5d7f4015a7205f16f0158e301c5c2e81` as `main` `e74426844d661c7a6c1debc8823a137a03a0ce69`.

Exact accepted-head evidence:

- R19.3 Network UpdateTransport Acceptance #7: **SUCCESS** on Ubuntu and Windows, including exact checkout provenance, compile, Ruff, focused transport/startup tests and exact-source acceptance evidence.
- R0 Repository Guard #2597: **SUCCESS** on Ubuntu and Windows.
- Python Core #2569: **SUCCESS** on Ubuntu and Windows; both platform package-build jobs and the integrated KodeStudio Windows evidence job also passed.
- KodeStudio UI Smoke #2534: **SUCCESS**.
- R16.9 Supply Chain Provenance Acceptance #215: **SUCCESS** on Ubuntu and Windows after registering the R19.3 acceptance workflow as the 35th immutable pinned authority workflow and synchronizing the integrity regression test.

Accepted R19.3 behavior includes:

- one bounded HTTPS-only transport for TUF metadata and authorized installer targets;
- explicit connect/read timeout policy and independent metadata/target byte ceilings;
- exact top-level metadata allowlisting and canonical Kodepoia TUF target-path validation;
- redirect handling that prevents metadata from escaping its approved HTTPS origin/path and permits GitHub Release payload redirects only to explicitly authorized delivery hosts/paths;
- deterministic offline/timeout/transport error mapping rather than startup failure;
- canonical GitHub Release asset URLs derived from the TUF-authorized target path instead of arbitrary model/user URLs;
- packaged startup loads the active R19.2 production Root locally and constructs `UpdateDiscoveryService` without performing any startup network request;
- discovery and verified installation services are injected into normal KodeStudio update settings at packaged startup;
- local trust/bootstrap failure remains a non-destructive update UI state and does not gate normal offline/local-first startup;
- Windows packaged startup constructs the verified downloader/install coordinator with PowerShell Authenticode and ProductVersion verification available without requiring SignTool SDK presence;
- explicit user confirmation before installer launch remains mandatory;
- R19.3 did not generate, import, store or use private TUF/AuthentiCode credentials.

Manual intervention for R19.3: **NONE**.

## R19.3 post-merge continuity normalization

R19.3 normalization branch: `r19/03-continuity-normalization`.

Accepted exact normalization HEAD: `e8c2c69f084d52590c4e0926b8c338e777abc09d`.

PR #415 merged with exact-head protection as normalized `main` `3f25b51f0c9f619b859cd588908d0ecb04a4875c`. That single normalization authorized R19.4. No second R19.3 continuity normalization is authorized.

## R19.4 accepted authority

R19.4 implementation branch: `r19/04-seamless-windows-in-app-update`.

Accepted exact implementation HEAD: `86384155aed8dd1e536669c94b2e5958b7096d22`.

R19.4 PR #416 merged with `expected_head_sha=86384155aed8dd1e536669c94b2e5958b7096d22` as `main` `d8f365cc1abd585cd5a603d7f50e53cbaeb8416f`.

Exact accepted-head evidence:

- R19.4 Seamless Windows In-App Update Acceptance #3: **SUCCESS** on Ubuntu and Windows, including exact checkout provenance, compile, Ruff, focused R19.4/R19.3 regression tests and exact-source acceptance evidence.
- R0 Repository Guard #2603: **SUCCESS** on Ubuntu and Windows.
- Python Core #2575: **SUCCESS** on Ubuntu and Windows; both platform package-build jobs and the integrated KodeStudio Windows evidence job also passed.
- KodeStudio UI Smoke #2540: **SUCCESS**.
- R16.9 Supply Chain Provenance Acceptance #217: **SUCCESS** on Ubuntu and Windows after registering the R19.4 acceptance workflow as the 36th immutable pinned authority workflow and synchronizing the integrity regression test.

Accepted R19.4 behavior includes:

- R18.8 verified staging and explicit user consent remain authoritative prerequisites;
- staged installer size and SHA-256 are revalidated immediately before handoff, rejecting missing or modified payloads;
- Windows self-update launches only the verified staged installer path with fixed Inno Setup arguments `/SP- /SILENT /NORESTART /CLOSEAPPLICATIONS /NORESTARTAPPLICATIONS /KODEPOIAUPDATE=1`;
- no model-provided URL, command or installer parameter enters the launcher contract;
- KodeStudio exits only after successful installer handoff; launch/UAC failure keeps the application available and records failure evidence;
- governed update installs relaunch Kodepoia only under the explicit update marker and use Inno Setup original-user execution rather than an uncontrolled elevated relaunch;
- packaged startup reconciles prior handoff state locally without any network dependency;
- relaunch on the authorized candidate version records `succeeded`; relaunch on the prior version records recoverable `recovery-needed` rather than false success;
- normal install behavior remains separate from governed update relaunch behavior;
- R19.4 did not generate, import, persist or use private TUF/AuthentiCode credentials and caused no public release effect.

Historical compatibility note: the frozen R16.17 **v1.0** release-readiness workflow still expects public version `1.0.0rc1`; on the R19.4 v1.1 source it therefore fails its historical version assertion (`expected '1.0.0rc1', got '1.1.0rc1'`). R16.18 propagates only those R16.17 failures while its R16.1–R16.16 exact-source cases pass. This is not an R19.4 product regression and does not replace the R19.5 v1.1 corrective release authority.

Manual intervention for R19.4: **NONE**.

## R19.4 post-merge continuity normalization

Base `main`: `d8f365cc1abd585cd5a603d7f50e53cbaeb8416f`.

Normalization branch: `r19/04-continuity-normalization`.

This branch changes continuity only. It must pass fresh exact-head:

- R0 Repository Guard Ubuntu + Windows;
- full Python Core;
- KodeStudio UI Smoke.

It must then merge with exact expected-head protection. No second R19.4 continuity normalization is authorized.

R19.5 START-sync is authorized **only after** that exact normalization merge enters `main`.

## Defects carried forward after R19.4

The language-selection defect remains closed by R19.1. R19.2 closes the production/beta trust-anchor and repository-bootstrap defect. R19.3 closes the installed network UpdateTransport/startup-wiring defect. R19.4 closes the seamless verified Windows installer handoff/shutdown/relaunch coordination defect.

The remaining authorized R19 product work is **R19.5 — Corrective RC Release Automation & Integrated Acceptance**: advance the canonical prerelease to the intended `1.1.0-rc2`, build/verify the corrective Windows release, authorize it through production TUF metadata and prove the installed `rc1 → rc2` upgrade path. External signing, private TUF key use, repository-secret configuration or public release publication remains a genuine conditional manual boundary and must not be crossed without authorized credentials/effects.

## Security invariants

- Never embed private TUF/AuthentiCode keys, tokens, passwords or certificate private material in source, packages, logs, artifacts or continuity.
- Never silently promote `trusted_root.synthetic.json` into production trust.
- Network update checks never gate normal application startup.
- No update installation occurs without explicit user confirmation after verification.
- GitHub Release assets may carry payloads, but TUF metadata remains the update authorization source.
- RC/beta discovery must not rely only on GitHub `/releases/latest`, which excludes prereleases.
- Root rotation remains sequential and threshold-protected; rollback/freeze protections remain mandatory.

## Resume rule

On a new conversation, verify current `main`, releases, open PRs, exact R19 subdivision status and whether this record has a later normalization. Continue subdivision-by-subdivision with dedicated branch, implementation, exact-head acceptance, expected-head merge and one continuity normalization before the next subdivision. Stop later subdivisions only at a genuine manual intervention boundary and provide exact user actions.
