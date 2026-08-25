# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.13 COMPLETE + NORMALIZED. R12.13 implementation PR #211 final head `84f75090759e6a54da5b69c8b9b6970ac7c572ae` passed all exact-head gates and merged as `2c0f5c5c1b64747a44e5fd2b41532e469a3ae8b2`; its single continuity-only normalization PR #212 exact head `7b00ecce39112a3f2158993d9923bfaead864957` passed R0/Python/UI plus all desktop-adapter regressions and merged as `63d6548d024fb511ca6172b121c05c9c7f02cf9c`. Manual R12.13 CONDITIONAL was NOT TRIGGERED. R12.14 is now the only active subdivision, on dedicated branch `r12/14-packaging-update` from exact normalized base `63d6548d024fb511ca6172b121c05c9c7f02cf9c`. The R-phase plan status MUST be synchronized at the beginning and end of every subdivision.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.13 : **COMPLETE + NORMALIZED**.
- R12.14 : **IN_PROGRESS**.
- R12.15–R12.16 : **PLANNED / NOT STARTED**.

## Permanent R-phase plan status synchronization rule

For every R phase, the phase plan (for example `docs/roadmap/R12_PLAN.md`) is live execution authority and MUST be updated both **at the beginning** and **at the end** of every subdivision.

- **Subdivision start, before implementation:** update the plan-level `Status`, `Complete subdivision index`, and execution checkpoint so all prior normalized subdivisions are `COMPLETE`, the active subdivision is `IN_PROGRESS`, and later subdivisions remain `PLANNED`/`NOT STARTED`. Synchronize this state in continuity in the same work cycle.
- **Subdivision end, before final documentation re-gates:** update those plan fields again so the accepted active subdivision is `COMPLETE`; the next subdivision remains `PLANNED` until its own dedicated branch starts. Synchronize continuity in the same work cycle.
- A triggered conditional manual gate must set a truthful blocked/manual-required state rather than `COMPLETE`.
- Post-merge continuity normalization is continuity-only and must not be used to hide stale plan status. The implementation branch must carry the end-of-subdivision plan update before merge.
- A stale `Complete subdivision index` is a governance defect and blocks acceptance until corrected.

This rule applies to R12.14, R12.15, R12.16 and all future R-phase execution/recovery unless a later accepted governance ADR explicitly changes it.

## R12.13 closure authority

- Base normalized `main`: `34c21c8ba6f12f6cd746dd9aea8c9b3cd7e32c41`.
- Implementation branch `r12/13-accessibility-localization-qa`; PR #211.
- Manual state: **CONDITIONAL / NOT TRIGGERED**.
- Accepted implementation candidate `646b4ad079113e27bb8d091c4153b125b6673f8c`.
- Candidate gates: R0 #1562 / `32827475621`; Python #1536 / `32827475643`; UI #1503 / `32827475650`; WPF #57 / `32827475625`; WinUI #47 / `32827475686`; Avalonia #43 / `32827475711`; Qt #38 / `32827475698`; Tauri #29 / `32827475658` — all SUCCESS.
- Accepted final-documentation head `84f75090759e6a54da5b69c8b9b6970ac7c572ae`.
- Final-documentation gates: R0 #1564 / `32827958711`; Python #1538 / `32827958647`; UI #1505 / `32827958665`; WPF #59 / `32827958616`; WinUI #49 / `32827958581`; Avalonia #45 / `32827958608`; Qt #40 / `32827958615`; Tauri #31 / `32827958693` — all SUCCESS.
- PR #211 merged with expected head as `2c0f5c5c1b64747a44e5fd2b41532e469a3ae8b2`.
- Single normalization branch `r12/13-postmerge-continuity-normalization`; PR #212; exact head `7b00ecce39112a3f2158993d9923bfaead864957`.
- Normalization gates: R0 #1566 / `32828448962`; Python #1540 / `32828448955`; UI #1507 / `32828448935`; WPF #60 / `32828448918`; WinUI #50 / `32828448844`; Avalonia #46 / `32828448978`; Qt #41 / `32828449033`; Tauri #32 / `32828448947` — all SUCCESS.
- PR #212 merged with expected head as `63d6548d024fb511ca6172b121c05c9c7f02cf9c`.
- **R12.13 COMPLETE + NORMALIZED**. This merge is the sole authorized base for R12.14.

## R12.14 execution authority

- Base normalized `main`: `63d6548d024fb511ca6172b121c05c9c7f02cf9c`.
- Dedicated branch: `r12/14-packaging-update`.
- Manual state: **CONDITIONAL**.
- Manual trigger: only if R12.14 makes a real installer/install/update/signing claim that hosted CI cannot prove. No production certificate is required for acceptance; truthful `UNSIGNED`, `TEST_SIGNED`, `SIGNED`, and `SIGNING_UNAVAILABLE` states remain distinct.
- Frozen scope: common PackageDefinition/ArtifactManifest; framework package capability states; deterministic semantic package manifest verification; local-fixture update source; version/channel/compatibility checks; digest verification before promotion; downgrade/signing-state substitution rejection; rollback/backup/recovery/audit model; no production update server or store submission.
- Phase-plan synchronization at R12.14 start has been performed: R12.1–R12.13 = `COMPLETE`, R12.14 = `IN_PROGRESS`, R12.15–R12.16 = `PLANNED`.

## Frozen R12 subdivision index

| ID | Titre | Status | Manuel |
| --- | --- | --- | --- |
| R12.1 | Desktop contracts, identities, capability model + secure toolchain boundaries | COMPLETE | NONE |
| R12.2 | Project DNA/KodeProduct desktop profiles + Project Wizard target selection | COMPLETE | NONE |
| R12.3 | Deterministic desktop scaffold/template/workspace manifest engine | COMPLETE | NONE |
| R12.4 | Framework-neutral MVVM/state/navigation/command/service contracts | COMPLETE | NONE |
| R12.5 | WPF/.NET desktop adapter + build/test bridge | COMPLETE | CONDITIONAL |
| R12.6 | WinUI 3/Windows App SDK adapter + Windows identity/deployment bridge | COMPLETE | CONDITIONAL |
| R12.7 | Avalonia cross-platform desktop adapter | COMPLETE | CONDITIONAL |
| R12.8 | Qt 6/CMake desktop adapter | COMPLETE | CONDITIONAL |
| R12.9 | Tauri v2/Rust/WebView2 desktop adapter | COMPLETE | CONDITIONAL |
| R12.10 | SQLite persistence, schema migrations, transactions + backup/recovery | COMPLETE | NONE |
| R12.11 | Async/concurrency, cancellation, progress + UI-thread lifecycle safety | COMPLETE | NONE |
| R12.12 | Local IPC contracts, framing, authorization + lifecycle isolation | COMPLETE | CONDITIONAL |
| R12.13 | Accessibility, localization, theming, keyboard/focus + DPI/scaling QA | COMPLETE | CONDITIONAL |
| R12.14 | Packaging/install/update/signing-state + rollback model | IN_PROGRESS | CONDITIONAL |
| R12.15 | CLI + KodeStudio Desktop workspace and governed Wizard workflow | PLANNED | NONE |
| R12.16 | Adversarial hardening + Wizard-to-Windows integrated acceptance | PLANNED | CONDITIONAL |

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → **start-of-subdivision plan + continuity status synchronization** → implementation + focused tests → exact-head standard + subdivision-specific gates → satisfy triggered manual state → **end-of-subdivision plan + continuity status synchronization** → evidence/re-gate if bytes change → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**R12.14 only:** implement packaging/install/update/signing-state and rollback contracts on `r12/14-packaging-update`, add focused tests/design/acceptance/schema, freeze one candidate, run exact-head gates and adapter regressions, determine manual state truthfully, then perform the mandatory end-of-subdivision R12 plan + continuity update before final documentation re-gates. R12.15 remains forbidden until R12.14 implementation merge and its single continuity-only normalization merge.
