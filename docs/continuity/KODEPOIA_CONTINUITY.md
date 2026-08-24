# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.7 COMPLETE + NORMALIZED once this single continuity-only normalization is accepted and merged. R12.7 final documentation head `59e273e04cb8b947173e5f58861cbf034c247877`: R0 #1511 / `32787385521`, Python #1485 / `32787385588`, UI #1452 / `32787385577`, Avalonia #4 / `32787385526`, WPF #18 / `32787385528`, WinUI #8 / `32787385520`, tous SUCCESS. Avalonia #4 passed independently on Windows, Ubuntu and macOS ARM64. Manual CONDITIONAL NOT TRIGGERED. PR #199 merged as `c0e5cd90e8b04501096694bbcb12a9075292e1e1`. Current branch is the single authorized R12.7 continuity normalization; R12.8 remains forbidden until its exact-head standard + Avalonia gate succeeds and it merges.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` after each accepted merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.6 : **COMPLETE + NORMALIZED**.
- R12.7 : **ACCEPTED + MERGED / CONTINUITY NORMALIZATION IN PROGRESS**.
- R12.8–R12.16 : **PLANNED / NOT STARTED**.

## Recent closure authority

### R12.6
- Final documentation head `c5b98d71cc279018745c83c8edc81a23e8df4b22`: R0 #1504 / `32786268565`, Python #1478 / `32786268605`, UI #1445 / `32786268585`, WPF #13 / `32786268628`, WinUI #3 / `32786268572` — SUCCESS; PR #197 merge `62edf1540c4da7689e86d6a391087a9bc50ae1c3`.
- Single continuity normalization `fabd6c86ca9f1302576db7cd5e794faab1042bc0`: R0 #1506 / `32786517826`, Python #1480 / `32786517750`, UI #1447 / `32786517737`, WPF #14 / `32786517811`, WinUI #4 / `32786517785` — SUCCESS; PR #198 merge `47ca9463015d652ead0b21a2e9a7030377a0c695`.
- Manual CONDITIONAL NOT TRIGGERED. **R12.6 COMPLETE + NORMALIZED.**

### R12.7
- Base normalized `main`: `47ca9463015d652ead0b21a2e9a7030377a0c695`.
- Implementation branch `r12/7-avalonia-cross-platform`; PR #199; Manual **CONDITIONAL / NOT TRIGGERED**.
- Delivered desktop-only target matrix schema, deterministic common-model adapter, exact Avalonia `12.1.1`, `net10.0` target, XAML application, platform runtime probe and per-OS SHA-256 evidence.
- Rejected predecessor `abbfa7677014b26fb60ecee335dec4a3a2f34488` used an internal assembly-name assertion; accepted head validates public Avalonia type identities.
- Accepted implementation head `57432a90c439abbbbcc6a8b2de76dcd7d917b8a2`: R0 #1509 / `32787159628`, Python #1483 / `32787159636`, UI #1450 / `32787159647`, Avalonia #2 / `32787159696`, WPF #16 / `32787159633`, WinUI #6 / `32787159622` — SUCCESS.
- Final documentation head `59e273e04cb8b947173e5f58861cbf034c247877`: R0 #1511 / `32787385521`, Python #1485 / `32787385588`, UI #1452 / `32787385577`, Avalonia #4 / `32787385526`, WPF #18 / `32787385528`, WinUI #8 / `32787385520` — SUCCESS.
- Avalonia #4 independently proved restore/build/runtime-probe/evidence on Windows, Ubuntu and macOS ARM64; no OS PASS was inferred from another OS.
- PR #199 merge `c0e5cd90e8b04501096694bbcb12a9075292e1e1`.
- Current branch `r12/7-postmerge-continuity-normalization` is the **single authorized** R12.7 continuity-only normalization and MUST change only this file.
- Accepted exact-head R0 + Python + UI + complete Avalonia matrix and merge make **R12.7 COMPLETE + NORMALIZED** and authorize R12.8.

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

**R12.7 continuity normalization only.** Gate its exact head with R0 Repository Guard + full Python Core + KodeStudio UI Smoke + complete Windows/Linux/macOS Avalonia matrix, then merge with `expected_head_sha`. **Only that merge authorizes R12.8.**
