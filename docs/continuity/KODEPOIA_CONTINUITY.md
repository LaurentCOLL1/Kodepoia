# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.7 COMPLETE + NORMALIZED. R12.8 accepted implementation candidate `7d59d1e1320f18f0173d4df0374b174075b8d3fa`: R0 #1519 / `32791617782`, Python #1493 / `32791617851`, UI #1460 / `32791617772`, Qt #5 / `32791617789`, Avalonia #10 / `32791617798`, WPF #24 / `32791617714`, WinUI #14 / `32791617839`, tous SUCCESS. Real Qt evidence: macOS ARM64, Qt 6.11.1, CMake 4.4.0, Ninja, AppleClang 21, configure/build/runtime PASS, manual CONDITIONAL NOT TRIGGERED. Documentation now records that candidate; the resulting final R12.8 documentation head must be freshly re-gated before PR #201 merge. R12.9 remains forbidden until R12.8 merge + single normalization.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` after each accepted merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.7 : **COMPLETE + NORMALIZED**.
- R12.8 : **IMPLEMENTATION ACCEPTED / FINAL DOCUMENTATION RE-GATE PENDING**.
- R12.9–R12.16 : **PLANNED / NOT STARTED**.

## Recent closure authority

### R12.7
- Final documentation head `59e273e04cb8b947173e5f58861cbf034c247877`: R0 #1511 / `32787385521`, Python #1485 / `32787385588`, UI #1452 / `32787385577`, Avalonia #4 / `32787385526`, WPF #18 / `32787385528`, WinUI #8 / `32787385520` — SUCCESS; PR #199 merge `c0e5cd90e8b04501096694bbcb12a9075292e1e1`.
- Single continuity normalization `5b36cd60e3e25ddb1028faf385e28b5d81ba6e45`: R0 #1513 / `32790355026`, Python #1487 / `32790354991`, UI #1454 / `32790355072`, Avalonia #5 / `32790355019`, WPF #19 / `32790354989`, WinUI #9 / `32790354979` — SUCCESS; PR #200 merge `306d0b6fafb6d8c9c069936799e0c82bf94be1c7`.
- Manual CONDITIONAL NOT TRIGGERED. **R12.7 COMPLETE + NORMALIZED.**

## R12.8 acceptance in progress

- Base normalized `main`: `306d0b6fafb6d8c9c069936799e0c82bf94be1c7`.
- Branch `r12/8-qt6-cmake-adapter`; PR #201; Manual **CONDITIONAL / NOT TRIGGERED**.
- Delivered deterministic Qt/CMake mapping, schema-backed Qt/CMake/compiler kit identity, fixed configure/build argv, embedded model resource, compiler hashing, Core/Widgets dependency declarations, explicit `REVIEW_REQUIRED` license state and adversarial injection tests.
- Rejected CI bootstrap attempts before Kodepoia execution: aqt metadata/mirror route could not locate Qt 6.11.2; official Windows Online Installer required Qt Account/license credentials. Neither is accepted evidence.
- Accepted CI route: Qt-documented account-free package-manager path on hosted macOS ARM64 using Homebrew `qtbase` + CMake + Ninja.
- Accepted implementation candidate `7d59d1e1320f18f0173d4df0374b174075b8d3fa`.
- R0 #1519 / `32791617782` — **SUCCESS**.
- Python Core #1493 / `32791617851` — **SUCCESS**.
- KodeStudio UI Smoke #1460 / `32791617772` — **SUCCESS**.
- R12 Qt6 Acceptance #5 / `32791617789` — **SUCCESS**.
- Avalonia #10 / `32791617798`, WPF #24 / `32791617714`, WinUI #14 / `32791617839` — **SUCCESS** regressions.
- Qt evidence reports Qt `6.11.1`, macOS ARM64, CMake `4.4.0`, Ninja, AppleClang `21.0.0.21000101`, kit digest `9b8fafd5af74d5c41381ebe7df9f31627e24882fc809f982532fe4859839b272`, and configure/build/runtime return codes `0`.
- Runtime sentinel: `KODEPOIA_QT6_RUNTIME_PASS:3feb7493c8fa969e638bb9c4454161edea8d1f36f49f2f93a72a99c3b4ca0da0:6.11.1`.
- Core/Widgets remain `REVIEW_REQUIRED`; redistribution rights are never inferred.
- Evidence recording changes repository bytes. Freeze the resulting final documentation head and require fresh R0 + Python + UI + Qt acceptance before merging PR #201 with `expected_head_sha`.

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

**R12.8 final documentation re-gate only.** Require fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R12 Qt6 Acceptance on the resulting exact head. If all succeed, merge PR #201 with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization and gate/merge it. **Only that normalization merge authorizes R12.9.**
