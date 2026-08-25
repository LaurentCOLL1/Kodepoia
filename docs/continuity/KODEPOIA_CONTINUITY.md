# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.13 COMPLETE + NORMALIZED. R12.14 implementation PR #213 final documentation head `a1481e5b23e14b029bcf076d0433e866c6d93895` passed all required exact-head gates and merged with expected SHA as `d1a0d3831f3767d713f3288b5269fcc722bab1eb`. Manual R12.14 CONDITIONAL was NOT TRIGGERED. The single continuity-only post-merge normalization branch `r12/14-postmerge-continuity-normalization` is now the only authorized action. The R-phase plan status rule is permanent: every phase plan must be synchronized at both subdivision start and end, especially `Complete subdivision index` and `Status`; post-merge normalization remains continuity-only and must not change plan status. R12.15 remains forbidden until this normalization exact head passes the complete exact-head gate set and merges.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.13 : **COMPLETE + NORMALIZED**.
- R12.14 : **IMPLEMENTATION MERGED / POST-MERGE NORMALIZATION IN_PROGRESS**.
- R12.15–R12.16 : **PLANNED / NOT STARTED**.

## Permanent R-phase plan status synchronization rule

For every R phase, the phase plan (for example `docs/roadmap/R12_PLAN.md`) is live execution authority and MUST be updated both **at the beginning** and **at the end** of every subdivision.

- **Subdivision start, before implementation:** update phase-level `Status`, `Complete subdivision index`, and execution checkpoint so all prior normalized subdivisions are `COMPLETE`, the active subdivision is `IN_PROGRESS`, and later subdivisions remain `PLANNED`/`NOT STARTED`; synchronize continuity in the same work cycle.
- **Subdivision end, before final documentation re-gates:** update the same plan fields so the accepted active subdivision is `COMPLETE`; the next subdivision remains `PLANNED` until its own dedicated branch starts; synchronize continuity in the same work cycle.
- A triggered conditional manual gate must set a truthful `BLOCKED`/`MANUAL_REQUIRED` state rather than `COMPLETE`.
- Post-merge normalization is continuity-only and MUST NOT rewrite phase-plan status. The implementation branch carries the end-of-subdivision plan update before merge.
- A stale `Complete subdivision index` or stale phase `Status` is a governance defect and blocks acceptance until corrected.

This rule applies to R12.14–R12.16 and all future R-phase execution/recovery unless a later accepted governance ADR explicitly changes it.

## R12.14 closure authority

- Base normalized `main`: `63d6548d024fb511ca6172b121c05c9c7f02cf9c`.
- Dedicated implementation branch: `r12/14-packaging-update`.
- PR: #213.
- Manual state: **CONDITIONAL / NOT TRIGGERED**.
- Accepted implementation candidate: `4d1377d74d9a6b5f7d47256288511908957d0adb`.
- Candidate gates: R0 #1568 / `32831015949`; Python #1542 / `32831015974`; UI #1509 / `32831016023`; WPF #61 / `32831016002`; WinUI #51 / `32831016057`; Avalonia #47 / `32831016116`; Qt #42 / `32831016129`; Tauri #33 / `32831015985` — all SUCCESS.
- Full Python Core passed `tests/test_desktop_r12_14.py` on hosted Linux and Windows; package-build evidence also succeeded on both OSes.
- Start status synchronization: R12.1–R12.13 `COMPLETE`, R12.14 `IN_PROGRESS`, R12.15–R12.16 `PLANNED`.
- End status synchronization before final documentation gates: `R12_PLAN.md` marks R12.14 `COMPLETE`; R12.15–R12.16 remain `PLANNED`; continuity matched that state.
- Accepted final-documentation head: `a1481e5b23e14b029bcf076d0433e866c6d93895`.
- Final-documentation exact-head gates: R0 #1571 / `32831671974`; Python #1545 / `32831671907`; UI #1512 / `32831671875`; WPF #64 / `32831671788`; WinUI #54 / `32831671805`; Avalonia #50 / `32831671949`; Qt #45 / `32831671906`; Tauri #36 / `32831671838` — all SUCCESS.
- PR #213 merged with `expected_head_sha=a1481e5b23e14b029bcf076d0433e866c6d93895` as merge commit `d1a0d3831f3767d713f3288b5269fcc722bab1eb`.
- Implemented scope remains bounded: semantic `PackageDefinition`/`ArtifactManifest`, framework packaging capability truthfulness, explicit signing states without secret material, version/channel/compatibility update contracts, digest verification, downgrade/signing substitution rejection, bounded local-fixture promotion and verified rollback. No real OS installer, Store submission, trust-store mutation, production signing or production update-server claim was manufactured.
- Single authorized normalization branch: `r12/14-postmerge-continuity-normalization`; continuity-only. Its exact head must pass R0/full Python/UI plus the five desktop adapter regressions before merge.
- After that normalization merges, **R12.14 becomes COMPLETE + NORMALIZED** and its normalization merge SHA becomes the sole authorized base for R12.15.

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
| R12.14 | Packaging/install/update/signing-state + rollback model | COMPLETE | CONDITIONAL |
| R12.15 | CLI + KodeStudio Desktop workspace and governed Wizard workflow | PLANNED | NONE |
| R12.16 | Adversarial hardening + Wizard-to-Windows integrated acceptance | PLANNED | CONDITIONAL |

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → **start-of-subdivision plan + continuity status synchronization** → implementation + focused tests → exact-head standard + subdivision-specific gates → satisfy triggered manual state → **end-of-subdivision plan + continuity status synchronization** → evidence/re-gate if bytes change → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands, prerequisites, expected evidence path and recovery/privacy instructions.

## Next authorized action

**R12.14 normalization only:** open the single continuity-only PR from `r12/14-postmerge-continuity-normalization`, gate its exact head with R0/full Python/UI plus WPF/WinUI/Avalonia/Qt/Tauri regressions, and merge with `expected_head_sha`. Then and only then create R12.15 from that normalized merge SHA and immediately perform the mandatory R12.15 start-of-subdivision plan + continuity status synchronization before implementation.
