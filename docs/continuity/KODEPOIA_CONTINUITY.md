# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.7 COMPLETE + NORMALIZED. R12.7 normalization head `5b36cd60e3e25ddb1028faf385e28b5d81ba6e45`: R0 #1513 / `32790355026`, Python #1487 / `32790354991`, UI #1454 / `32790355072`, Avalonia #5 / `32790355019`, WPF #19 / `32790354989`, WinUI #9 / `32790354979`, tous SUCCESS; PR #200 merged as `306d0b6fafb6d8c9c069936799e0c82bf94be1c7`. R12.8 is now the only active subdivision on branch `r12/8-qt6-cmake-adapter`, based on that normalized main. Manual R12.8 is CONDITIONAL and NOT YET TRIGGERED. R12.9 remains forbidden until R12.8 implementation/evidence merge + single normalization.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` after each accepted merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.7 : **COMPLETE + NORMALIZED**.
- R12.8 : **IMPLEMENTATION IN PROGRESS**.
- R12.9–R12.16 : **PLANNED / NOT STARTED**.

## Recent closure authority

### R12.7
- Base normalized `main`: `47ca9463015d652ead0b21a2e9a7030377a0c695`.
- Implementation branch `r12/7-avalonia-cross-platform`; PR #199; Manual **CONDITIONAL / NOT TRIGGERED**.
- Accepted implementation head `57432a90c439abbbbcc6a8b2de76dcd7d917b8a2`: R0 #1509 / `32787159628`, Python #1483 / `32787159636`, UI #1450 / `32787159647`, Avalonia #2 / `32787159696`, WPF #16 / `32787159633`, WinUI #6 / `32787159622` — SUCCESS.
- Final documentation head `59e273e04cb8b947173e5f58861cbf034c247877`: R0 #1511 / `32787385521`, Python #1485 / `32787385588`, UI #1452 / `32787385577`, Avalonia #4 / `32787385526`, WPF #18 / `32787385528`, WinUI #8 / `32787385520` — SUCCESS.
- Avalonia independently proved restore/build/runtime-probe/evidence on Windows, Ubuntu and macOS ARM64; no OS PASS was inferred from another OS.
- PR #199 merge `c0e5cd90e8b04501096694bbcb12a9075292e1e1`.
- Single continuity normalization `5b36cd60e3e25ddb1028faf385e28b5d81ba6e45`: R0 #1513 / `32790355026`, Python #1487 / `32790354991`, UI #1454 / `32790355072`, Avalonia #5 / `32790355019`, WPF #19 / `32790354989`, WinUI #9 / `32790354979` — SUCCESS; PR #200 merge `306d0b6fafb6d8c9c069936799e0c82bf94be1c7`.
- Manual CONDITIONAL NOT TRIGGERED. **R12.7 COMPLETE + NORMALIZED.**

## R12.8 implementation in progress

- Base normalized `main`: `306d0b6fafb6d8c9c069936799e0c82bf94be1c7`.
- Branch `r12/8-qt6-cmake-adapter`; Manual **CONDITIONAL / NOT YET TRIGGERED**.
- Scope: Qt 6/CMake adapter, explicit Qt/CMake/compiler kit identity, fixed CMake argv, deterministic resource/project manifest, exact component/BOM declarations and license state `REVIEW_REQUIRED`.
- Current acceptance baseline: hosted Windows, Qt `6.11.2` MSVC 2022 x64, CMake 3.22+, C++17. CI may provision the exact Qt SDK before Kodepoia runs; Kodepoia runtime never installs Qt/CMake/Visual Studio workloads.
- Generated fixture uses only Qt Core + Widgets, embeds the shared logical-model digest as a Qt resource and runtime-verifies it without claiming interactive rendering.
- No accepted implementation SHA exists yet. Freeze only after R0 + full Python Core + KodeStudio UI Smoke + real `R12 Qt6 Acceptance` succeed on one exact head.

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

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → implementation + focused tests → exact-head standard + adapter-specific gates → satisfy triggered manual state → evidence/re-gate if bytes change → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**R12.8 implementation/evidence only.** Finish the Qt 6 adapter, tests and real hosted Windows Qt/CMake/MSVC acceptance, freeze one exact implementation head, record evidence, re-gate final documentation head, merge with `expected_head_sha`, then perform exactly one continuity-only normalization. **R12.9 remains forbidden until that normalization merges.**
