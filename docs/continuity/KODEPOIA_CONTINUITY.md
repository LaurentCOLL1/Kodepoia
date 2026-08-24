# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1 first implementation/documentation candidate `3d567314221479aad5760e12e99bf49aa52f68a7` est accepté par R0 #1468 / `32773782636`, Python Core #1442 / `32773782642`, UI Smoke #1409 / `32773782630`, tous SUCCESS. Cette continuité enregistre ces preuves et crée le final documentation head qui doit être re-gaté avant merge de PR #187. R12.2 reste interdit jusqu’au merge R12.1 puis à son unique normalisation post-merge.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` après chaque merge accepté est source de vérité.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1 : **FIRST CANDIDATE ACCEPTED / FINAL DOCUMENTATION HEAD RE-GATE PENDING**.
- R12.2–R12.16 : **PLANNED / NOT STARTED**.
- R13–R16 : **PENDING / NOT STARTED**.

## R12 planning authority

- Plan : `docs/roadmap/R12_PLAN.md`.
- Final planning documentation head `661c09e57639190a60630411127d49870a959cc9`: R0 #1464 / `32772400955`, Python Core #1438 / `32772400921`, UI Smoke #1405 / `32772400996` — SUCCESS.
- Planning PR #185 merge : `6ad0e6045ac70a82f367b4eacb18d927ffd1bddf`.
- Planning continuity-normalization head `95aa2fd2120ee7d8de48ad12517942619ae1d1fb`: R0 #1466 / `32772691975`, Python Core #1440 / `32772691982`, UI Smoke #1407 / `32772691853` — SUCCESS.
- Planning normalization PR #186 merge : `f82444fa4c7018409bb0bdf83456b2cebd683e7e`.
- Therefore **R12 planning = ACCEPTED + NORMALIZED**.

## Frozen R12 subdivision index

| ID | Titre | Manuel |
| --- | --- | --- |
| R12.1 | Desktop contracts, identities, capability model + secure toolchain boundaries | NONE |
| R12.2 | Project DNA/KodeProduct desktop profiles + Project Wizard target selection | NONE |
| R12.3 | Deterministic desktop scaffold/template/workspace manifest engine | NONE |
| R12.4 | Framework-neutral MVVM/state/navigation/command/service contracts | NONE |
| R12.5 | WPF/.NET desktop adapter + build/test bridge | CONDITIONAL |
| R12.6 | WinUI 3/Windows App SDK adapter + Windows identity/deployment bridge | CONDITIONAL |
| R12.7 | Avalonia cross-platform desktop adapter | CONDITIONAL |
| R12.8 | Qt 6/CMake desktop adapter | CONDITIONAL |
| R12.9 | Tauri v2/Rust/WebView2 desktop adapter | CONDITIONAL |
| R12.10 | SQLite persistence, schema migrations, transactions + backup/recovery | NONE |
| R12.11 | Async/concurrency, cancellation, progress + UI-thread lifecycle safety | NONE |
| R12.12 | Local IPC contracts, framing, authorization + lifecycle isolation | CONDITIONAL |
| R12.13 | Accessibility, localization, theming, keyboard/focus + DPI/scaling QA | CONDITIONAL |
| R12.14 | Packaging/install/update/signing-state + rollback model | CONDITIONAL |
| R12.15 | CLI + KodeStudio Desktop workspace and governed Wizard workflow | NONE |
| R12.16 | Adversarial hardening + Wizard-to-Windows integrated acceptance | CONDITIONAL |

## R12.1 acceptance in progress

- Base normalized `main`: `f82444fa4c7018409bb0bdf83456b2cebd683e7e`.
- Branch: `r12/1-desktop-contracts-boundaries`.
- PR: #187.
- Manual: **NONE**.
- Delivered source: `src/kodepoia/desktop/contracts.py`, `boundary.py`, package exports.
- Delivered schemas: `schemas/r12/desktop-target-profile.schema.json`, `desktop-capability-report.schema.json`.
- Delivered tests: `tests/test_r12_1_desktop_contracts.py`.
- Design/acceptance: `docs/roadmap/R12_1_DESIGN.md`, `R12_1_ACCEPTANCE.md`.
- First accepted candidate: `3d567314221479aad5760e12e99bf49aa52f68a7`.
- R0 Repository Guard #1468 / `32773782636` — **SUCCESS**.
- Python Core #1442 / `32773782642` — **SUCCESS** including Ubuntu/Windows pytest, package builds and internal KodeStudio smoke.
- KodeStudio UI Smoke #1409 / `32773782630` — **SUCCESS**.
- This continuity update changes bytes after the accepted candidate; the resulting final documentation head must pass a fresh exact-head R0 + full Python + UI triplet before expected-SHA merge of #187.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → implementation + focused tests → exact-head R0/full Python/UI → satisfy REQUIRED/triggered CONDITIONAL manual state → final docs/evidence and re-gate if head changes → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + same exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**R12.1 final documentation re-gate only.** Merge PR #187 only after the fresh triplet succeeds, then perform exactly one post-merge continuity normalization. **R12.2 remains forbidden until that normalization merges.**
