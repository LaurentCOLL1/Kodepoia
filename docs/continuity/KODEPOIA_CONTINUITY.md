# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.13 COMPLETE + NORMALIZED. R12.14 dedicated branch `r12/14-packaging-update` starts from normalized main `63d6548d024fb511ca6172b121c05c9c7f02cf9c`; PR #213 accepted implementation candidate `4d1377d74d9a6b5f7d47256288511908957d0adb`. R0 #1568, Python #1542, UI #1509, WPF #61, WinUI #51, Avalonia #47, Qt #42 and Tauri #33 are all SUCCESS; full Python Core passed the R12.14 focused suite on hosted Linux and Windows. Manual R12.14 CONDITIONAL is NOT TRIGGERED because the accepted scope proves semantic package/update integrity and bounded local-fixture rollback only, not an unproven real installer/signing claim. Mandatory end-of-subdivision plan/continuity synchronization has set R12.14 COMPLETE and leaves R12.15/R12.16 PLANNED. The resulting documentation HEAD must now receive fresh exact-head gates before PR #213 can merge. R12.15 remains forbidden until the single R12.14 post-merge normalization passes and merges.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.13 : **COMPLETE + NORMALIZED**.
- R12.14 : **IMPLEMENTED / CANDIDATE ACCEPTED / FINAL DOCUMENTATION RE-GATE PENDING**.
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

- Implementation PR #211 final-documentation head `84f75090759e6a54da5b69c8b9b6970ac7c572ae` passed all exact-head gates and merged as `2c0f5c5c1b64747a44e5fd2b41532e469a3ae8b2`.
- Manual R12.13: **CONDITIONAL / NOT TRIGGERED**.
- Single normalization PR #212 exact head `7b00ecce39112a3f2158993d9923bfaead864957` passed R0 #1566, Python #1540, UI #1507, WPF #60, WinUI #50, Avalonia #46, Qt #41 and Tauri #32 and merged as `63d6548d024fb511ca6172b121c05c9c7f02cf9c`.
- **R12.13 COMPLETE + NORMALIZED**. This merge is the sole authorized base for R12.14.

## R12.14 execution authority

- Base normalized `main`: `63d6548d024fb511ca6172b121c05c9c7f02cf9c`.
- Dedicated branch: `r12/14-packaging-update`.
- PR: #213.
- Manual state: **CONDITIONAL / NOT TRIGGERED**.
- Manual trigger remains restricted to a required real installer/install/update/signing semantic that hosted CI cannot prove. No such semantic is part of the accepted R12.14 claim. No production certificate, Store submission, OS trust-store mutation or production update server is asserted.
- Implemented scope: common `PackageDefinition`/`ArtifactManifest`; semantic file-set/size/SHA-256 integrity; framework package capability states; explicit `UNSIGNED`/`TEST_SIGNED`/`SIGNED`/`SIGNING_UNAVAILABLE` identity without private key material; version/channel/compatibility `UpdateManifest`/`UpdatePolicy`; default downgrade rejection; signing-state/signer substitution rejection; bounded local-fixture staging/promotion; verified rollback after injected failure; workspace/path/symlink/tamper defenses; versioned packaging schema.
- Accepted implementation candidate: `4d1377d74d9a6b5f7d47256288511908957d0adb`.
- Candidate gates: R0 #1568 / `32831015949`; Python #1542 / `32831015974`; UI #1509 / `32831016023`; WPF #61 / `32831016002`; WinUI #51 / `32831016057`; Avalonia #47 / `32831016116`; Qt #42 / `32831016129`; Tauri #33 / `32831015985` — all SUCCESS.
- Full Python Core passed `tests/test_desktop_r12_14.py` on hosted Linux and Windows; package build evidence also succeeded on both OSes.
- Start status synchronization was completed before implementation: R12.1–R12.13 `COMPLETE`, R12.14 `IN_PROGRESS`, R12.15–R12.16 `PLANNED`.
- End status synchronization is now completed before final documentation gates: `R12_PLAN.md` marks R12.14 `COMPLETE`; R12.15–R12.16 remain `PLANNED`. Continuity matches that state.
- Candidate evidence and status synchronization changed documentation bytes after the accepted implementation candidate. The resulting final documentation HEAD must receive a fresh exact-head R0/Python/UI + desktop-adapter gate set before expected-SHA merge.

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

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**R12.14 only:** freeze the current final documentation HEAD after candidate evidence + end-of-subdivision plan/continuity synchronization. Require fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke + WPF/WinUI/Avalonia/Qt/Tauri regressions on that exact SHA. If all are SUCCESS, merge PR #213 with `expected_head_sha`, then create exactly one continuity-only R12.14 post-merge normalization, gate and merge it. R12.15 is authorized only after that normalization merge.
