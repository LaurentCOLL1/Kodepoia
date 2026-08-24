# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.6 COMPLETE + NORMALIZED. R12.6 final head `c5b98d71cc279018745c83c8edc81a23e8df4b22`: R0 #1504 / `32786268565`, Python #1478 / `32786268605`, UI #1445 / `32786268585`, WPF #13 / `32786268628`, WinUI #3 / `32786268572`, tous SUCCESS; PR #197 merge `62edf1540c4da7689e86d6a391087a9bc50ae1c3`. Single normalization `fabd6c86ca9f1302576db7cd5e794faab1042bc0`: R0 #1506 / `32786517826`, Python #1480 / `32786517750`, UI #1447 / `32786517737`, WPF #14 / `32786517811`, WinUI #4 / `32786517785`, tous SUCCESS; PR #198 merge `47ca9463015d652ead0b21a2e9a7030377a0c695`. Manual R12.6 CONDITIONAL NOT TRIGGERED. R12.7 Avalonia est en implémentation sur branche dédiée depuis ce normalized main; R12.8 reste interdit avant R12.7 COMPLETE + NORMALIZED.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` après chaque merge accepté est source de vérité.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.6 : **COMPLETE + NORMALIZED**.
- R12.7 : **IMPLEMENTATION / ACCEPTANCE PENDING**.
- R12.8–R12.16 : **PLANNED / NOT STARTED**.

## Recent closure authority

### R12.6
- Accepted implementation candidate `b990a613d6becbc80e637ea0184f87b502573b74`: R0 #1502 / `32786054869`, Python #1476 / `32786054919`, UI #1443 / `32786054865`, WPF #11 / `32786054841`, WinUI #1 / `32786054895` — SUCCESS.
- Final documentation head `c5b98d71cc279018745c83c8edc81a23e8df4b22`: R0 #1504 / `32786268565`, Python #1478 / `32786268605`, UI #1445 / `32786268585`, WPF #13 / `32786268628`, WinUI #3 / `32786268572` — SUCCESS; PR #197 merge `62edf1540c4da7689e86d6a391087a9bc50ae1c3`.
- Single continuity normalization `fabd6c86ca9f1302576db7cd5e794faab1042bc0`: R0 #1506 / `32786517826`, Python #1480 / `32786517750`, UI #1447 / `32786517737`, WPF #14 / `32786517811`, WinUI #4 / `32786517785` — SUCCESS; PR #198 merge `47ca9463015d652ead0b21a2e9a7030377a0c695`.
- Manual CONDITIONAL NOT TRIGGERED. **R12.6 COMPLETE + NORMALIZED.**

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

## R12.7 acceptance in progress

- Base normalized `main`: `47ca9463015d652ead0b21a2e9a7030377a0c695`.
- Branch `r12/7-avalonia-cross-platform`; Manual **CONDITIONAL**, triggered only if a platform claim selected by frozen acceptance cannot be proven in hosted CI.
- Delivered schema-backed desktop-only `AvaloniaTargetMatrix`, deterministic common-model adapter, exact Avalonia `12.1.1` dependency pin, `net10.0` accepted target, repository-owned Avalonia XAML app, platform-specific runtime probe and Windows/Linux/macOS evidence partitioning.
- Dedicated matrix workflow builds/probes the exact candidate independently on Windows, Ubuntu and macOS. Assembly/runtime evidence does not manufacture an interactive native-window-rendering claim.
- Exact implementation candidate/run IDs: **PENDING** until branch freeze and exact-head gates.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → implementation + focused tests → exact-head standard + adapter-specific gates → satisfy triggered manual state → evidence/re-gate if bytes change → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**Freeze and gate R12.7 only.** Require exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + complete Windows/Linux/macOS `R12 Avalonia Acceptance`. If accepted, record evidence, re-gate final docs, merge, then perform exactly one post-merge continuity normalization. **R12.8 remains forbidden until that normalization merges.**
