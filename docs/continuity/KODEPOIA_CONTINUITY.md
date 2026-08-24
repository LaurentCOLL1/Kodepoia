# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.4 COMPLETE + NORMALIZED. R12.4 single normalization head `b280bf60cddf7b3a9b079d6845d9a991e009487e`: R0 #1488 / `32779785160`, Python #1462 / `32779785121`, UI #1429 / `32779785040`, tous SUCCESS; PR #194 merge `180a507a81c979ec797f3bafe3de29ba38b72c94`. R12.5 WPF est en implémentation sur branche dédiée depuis ce normalized main. Manual R12.5 CONDITIONAL; aucun manuel n'est déclenché tant que le hosted Windows gate peut prouver compile/runtime/test WPF. R12.6 reste interdit avant R12.5 COMPLETE + NORMALIZED.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` après chaque merge accepté est source de vérité.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.4 : **COMPLETE + NORMALIZED**.
- R12.5 : **IMPLEMENTATION / ACCEPTANCE PENDING**.
- R12.6–R12.16 : **PLANNED / NOT STARTED**.

## Recent closure authority

### R12.3
- Final docs `be9217edf96518556c37f7e1ae3b1cdcb093cdb7`: R0 #1480 / `32778510158`, Python #1454 / `32778510179`, UI #1421 / `32778510136` — SUCCESS; PR #191 merge `dab35e11a354b4a8d90c6d8bf5695a3e8f9c6937`.
- Normalization `34a5becb45603c1cf0ddc7b1679111dc44708397`: R0 #1482 / `32778771303`, Python #1456 / `32778771366`, UI #1423 / `32778771306` — SUCCESS; PR #192 merge `1f52adffedb69384904a4b35bb32e45e06b05e33`.
- Manual NONE. **R12.3 COMPLETE + NORMALIZED.**

### R12.4
- Final docs `b9c926d94d8ad52de8471287a6b34f9950e24c96`: R0 #1486 / `32779563916`, Python #1460 / `32779563963`, UI #1427 / `32779563925` — SUCCESS; PR #193 merge `a98d985c3200f977f8fdbc38483d4aaf81e870af`.
- Single normalization `b280bf60cddf7b3a9b079d6845d9a991e009487e`: R0 #1488 / `32779785160`, Python #1462 / `32779785121`, UI #1429 / `32779785040` — SUCCESS; PR #194 merge `180a507a81c979ec797f3bafe3de29ba38b72c94`.
- Manual NONE. **R12.4 COMPLETE + NORMALIZED.**

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

## R12.5 acceptance in progress

- Base normalized `main`: `180a507a81c979ec797f3bafe3de29ba38b72c94`.
- Branch: `r12/5-wpf-dotnet-adapter`.
- Manual: **CONDITIONAL**, only if hosted Windows cannot establish the required WPF runtime semantic.
- Delivered adapter source `src/kodepoia/desktop/wpf.py`, real-toolchain runner `scripts/r12_5_wpf_acceptance.py`, focused unit/adversarial tests and dedicated `R12 WPF Acceptance` workflow.
- Fixture maps `canonical_sample_app()` to deterministic `net10.0-windows` WPF source with `UseWPF=true`; hosted acceptance compiles the app and runs an STA WPF harness proving `PresentationFramework`, `Application`, `Dispatcher`, `Window` and exact logical-model binding.
- Missing/incompatible SDK is explicit UNAVAILABLE/UNSUPPORTED; AVAILABLE requires successful build + runtime harness. Staged artifacts are SHA-256 inventoried.
- Exact implementation candidate/run IDs: **PENDING** until branch freeze and exact-head gates.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → implementation + focused tests → exact-head R0/full Python/UI + any adapter-specific gate → satisfy REQUIRED/triggered CONDITIONAL manual state → record evidence/re-gate if bytes change → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**Freeze and gate R12.5 only.** Require exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + real Windows `R12 WPF Acceptance`. If accepted, record evidence, re-gate final docs, merge, then perform exactly one post-merge continuity normalization. **R12.6 remains forbidden until that normalization merges.**
