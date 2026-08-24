# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.3 COMPLETE + NORMALIZED. R12.4 est en implémentation sur branche dédiée depuis normalized main `1f52adffedb69384904a4b35bb32e45e06b05e33`. Manual R12.4 NONE. R12.5 reste interdit jusqu’à acceptance, merge et unique normalisation post-merge de R12.4.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` après chaque merge accepté est source de vérité.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.3 : **COMPLETE + NORMALIZED**.
- R12.4 : **IMPLEMENTATION / ACCEPTANCE PENDING**.
- R12.5–R12.16 : **PLANNED / NOT STARTED**.

## R12.2 closure authority

- Final documentation head `030d35ecd2d712bb9465760854a54ddc96c1c652`: R0 #1474 / `32775260396`, Python #1448 / `32775260347`, UI #1415 / `32775260363` — SUCCESS.
- PR #189 merge `919508b6aad977ee7c4242b51509d108b1bdf1f6`.
- Single normalization head `611c8768bb11ad25ca275eb50cb4cc325abe1db3`: R0 #1476 / `32776007461`, Python #1450 / `32776007559`, UI #1417 / `32776007449` — SUCCESS.
- PR #190 merge `6a58719522b46b0f89b9514dbeff6cb5ca0bdb6c`. Manual NONE. **R12.2 COMPLETE + NORMALIZED.**

## R12.3 closure authority

- Base normalized `main`: `6a58719522b46b0f89b9514dbeff6cb5ca0bdb6c`.
- Implementation branch `r12/3-desktop-scaffold-engine`; PR #191; Manual **NONE**.
- First accepted implementation candidate `bf4c5b095bc7b91ecf7c27100c3da81c0a13ce31`: R0 #1478 / `32778299021`, Python #1452 / `32778298974`, UI #1419 / `32778299000` — SUCCESS.
- Final documentation head `be9217edf96518556c37f7e1ae3b1cdcb093cdb7`: R0 #1480 / `32778510158`, Python #1454 / `32778510179`, UI #1421 / `32778510136` — SUCCESS.
- PR #191 merge `dab35e11a354b4a8d90c6d8bf5695a3e8f9c6937`.
- Single continuity normalization head `34a5becb45603c1cf0ddc7b1679111dc44708397`: R0 #1482 / `32778771303`, Python Core #1456 / `32778771366`, UI Smoke #1423 / `32778771306` — SUCCESS.
- Normalization PR #192 merge `1f52adffedb69384904a4b35bb32e45e06b05e33`.
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
- Branch: `r12/4-desktop-app-contracts`.
- Manual: **NONE**.
- Delivered source: `src/kodepoia/desktop/app_model.py` and package exports.
- Durable schema: `schemas/r12/desktop-app-model.schema.json`.
- Focused tests: `tests/test_r12_4_desktop_app_contracts.py`.
- Design/acceptance: `docs/roadmap/R12_4_DESIGN.md`, `R12_4_ACCEPTANCE.md`.
- Logical model: typed state/validation, commands, view-model bindings, views, routes/dialogs, services/lifetimes and deterministic disposal ordering; no concrete framework object is serialized.
- Canonical sample app is the shared adapter conformance fixture for WPF/WinUI/Avalonia/Qt/Tauri.
- Exact implementation candidate/run IDs: **PENDING** until branch freeze and exact-head gates.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → implementation + focused tests → exact-head R0/full Python/UI → satisfy REQUIRED/triggered CONDITIONAL manual state → final docs/evidence and re-gate if head changes → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + same exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**Freeze and gate R12.4 only.** Require exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke. If accepted, record evidence, re-gate the final documentation head, merge with expected SHA, then perform exactly one post-merge continuity normalization. **R12.5 remains forbidden until that normalization merges.**
