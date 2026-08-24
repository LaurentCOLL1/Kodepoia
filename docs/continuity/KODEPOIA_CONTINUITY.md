# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.3 COMPLETE + NORMALIZED. R12.4 first implementation candidate `d55b55feedcfc638e1e11d194d12f80b8f7b6f9c` est accepté : R0 #1484 / `32779332770`, Python Core #1458 / `32779332780`, UI Smoke #1425 / `32779332799`, tous SUCCESS. Cette documentation crée le final R12.4 head à re-gater avant merge de PR #193. Manual NONE. R12.5 reste interdit jusqu’au merge R12.4 puis à son unique normalisation post-merge.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` après chaque merge accepté est source de vérité.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.3 : **COMPLETE + NORMALIZED**.
- R12.4 : **FIRST CANDIDATE ACCEPTED / FINAL DOCUMENTATION HEAD RE-GATE PENDING**.
- R12.5–R12.16 : **PLANNED / NOT STARTED**.

## Recent closure authority

### R12.2
- Final docs `030d35ecd2d712bb9465760854a54ddc96c1c652`: R0 #1474 / `32775260396`, Python #1448 / `32775260347`, UI #1415 / `32775260363` — SUCCESS; PR #189 merge `919508b6aad977ee7c4242b51509d108b1bdf1f6`.
- Normalization `611c8768bb11ad25ca275eb50cb4cc325abe1db3`: R0 #1476 / `32776007461`, Python #1450 / `32776007559`, UI #1417 / `32776007449` — SUCCESS; PR #190 merge `6a58719522b46b0f89b9514dbeff6cb5ca0bdb6c`.
- Manual NONE. **R12.2 COMPLETE + NORMALIZED.**

### R12.3
- First candidate `bf4c5b095bc7b91ecf7c27100c3da81c0a13ce31`: R0 #1478 / `32778299021`, Python #1452 / `32778298974`, UI #1419 / `32778299000` — SUCCESS.
- Final docs `be9217edf96518556c37f7e1ae3b1cdcb093cdb7`: R0 #1480 / `32778510158`, Python #1454 / `32778510179`, UI #1421 / `32778510136` — SUCCESS; PR #191 merge `dab35e11a354b4a8d90c6d8bf5695a3e8f9c6937`.
- Normalization `34a5becb45603c1cf0ddc7b1679111dc44708397`: R0 #1482 / `32778771303`, Python #1456 / `32778771366`, UI #1423 / `32778771306` — SUCCESS; PR #192 merge `1f52adffedb69384904a4b35bb32e45e06b05e33`.
- Manual NONE. **R12.3 COMPLETE + NORMALIZED.**

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

## R12.4 acceptance in progress

- Base normalized `main`: `1f52adffedb69384904a4b35bb32e45e06b05e33`.
- Branch `r12/4-desktop-app-contracts`; PR #193; Manual **NONE**.
- Delivered framework-neutral `DesktopAppModel`: typed state/validation, bounded commands/can-execute, view-model bindings, views, routes/dialogs, service dependencies/lifetimes and deterministic disposal.
- Durable schema `schemas/r12/desktop-app-model.schema.json` and canonical shared adapter fixture `canonical_sample_app()`.
- Tests reject dangling refs, duplicate/cyclic routes, raw/invalid operations, service cycles/lifetime capture and type-invalid validation; all five frozen adapters must preserve the same logical signature.
- First accepted candidate `d55b55feedcfc638e1e11d194d12f80b8f7b6f9c`.
- R0 #1484 / `32779332770` — **SUCCESS**.
- Python Core #1458 / `32779332780` — **SUCCESS** including Ubuntu/Windows pytest, package builds and internal UI smoke.
- KodeStudio UI Smoke #1425 / `32779332799` — **SUCCESS**.
- Evidence recording changed bytes; final documentation head requires a fresh exact-head triplet before merge.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → implementation + focused tests → exact-head R0/full Python/UI → satisfy REQUIRED/triggered CONDITIONAL manual state → final docs/evidence and re-gate if head changes → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + same exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**R12.4 final documentation re-gate only.** Merge PR #193 only after fresh R0 + full Python Core + UI succeed, then perform exactly one continuity normalization. **R12.5 remains forbidden until that normalization merges.**
