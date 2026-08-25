# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.8 COMPLETE + NORMALIZED. R12.8 normalization head `a926f0a3bfd713c668554b14d673582db981b7bf`: R0 #1524 / `32811363092`, Python #1498 / `32811363187`, UI #1465 / `32811363114`, Qt #9 / `32811363119`, Avalonia #14 / `32811363132`, WPF #28 / `32811363162`, WinUI #18 / `32811363023`, tous SUCCESS; PR #202 merged as `1cd32eb0cf78dbf468a9921955bbc8695cedab89`. R12.9 is now the only active subdivision on branch `r12/9-tauri2-rust-webview2-adapter`, based exactly on that normalized main. Manual R12.9 is CONDITIONAL and NOT YET TRIGGERED. R12.10 remains forbidden until R12.9 implementation/evidence merge + single normalization.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` after each accepted merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.8 : **COMPLETE + NORMALIZED**.
- R12.9 : **IMPLEMENTATION IN PROGRESS**.
- R12.10–R12.16 : **PLANNED / NOT STARTED**.

## Recent closure authority

### R12.8
- Base normalized `main`: `306d0b6fafb6d8c9c069936799e0c82bf94be1c7`.
- Implementation branch `r12/8-qt6-cmake-adapter`; PR #201; Manual **CONDITIONAL / NOT TRIGGERED**.
- Accepted implementation candidate `7d59d1e1320f18f0173d4df0374b174075b8d3fa`: R0 #1519 / `32791617782`, Python #1493 / `32791617851`, UI #1460 / `32791617772`, Qt #5 / `32791617789`, Avalonia #10 / `32791617798`, WPF #24 / `32791617714`, WinUI #14 / `32791617839` — SUCCESS.
- Accepted Qt route: hosted macOS ARM64, Homebrew `qtbase`, Qt `6.11.1`, CMake `4.4.0`, Ninja, AppleClang `21.0.0.21000101`; configure/build/runtime return codes `0`.
- Final documentation head `091a356b42328b169b37ca1601d922e1720ef3e1`: R0 #1522 / `32791843505`, Python #1496 / `32791843496`, UI #1463 / `32791843461`, Qt #8 / `32791843472`, Avalonia #13 / `32791843614`, WPF #27 / `32791843555`, WinUI #17 / `32791843482` — SUCCESS; PR #201 merge `8d18f95740c33820ae79362f388471cd587629da`.
- Single continuity normalization `a926f0a3bfd713c668554b14d673582db981b7bf`: R0 #1524 / `32811363092`, Python #1498 / `32811363187`, UI #1465 / `32811363114`, Qt #9 / `32811363119`, Avalonia #14 / `32811363132`, WPF #28 / `32811363162`, WinUI #18 / `32811363023` — SUCCESS; PR #202 merge `1cd32eb0cf78dbf468a9921955bbc8695cedab89`.
- Manual CONDITIONAL NOT TRIGGERED. **R12.8 COMPLETE + NORMALIZED.**

## R12.9 implementation in progress

- Base normalized `main`: `1cd32eb0cf78dbf468a9921955bbc8695cedab89`.
- Branch `r12/9-tauri2-rust-webview2-adapter`; Manual **CONDITIONAL / NOT YET TRIGGERED**.
- Scope: Tauri v2/Rust MSVC/WebView2 adapter, exact Cargo lock, deterministic static frontend/config manifest, default-deny frontend IPC policy, offline locked Cargo build and real WebView2 runtime-version evidence.
- Acceptance pins Tauri `2.11.5` and `tauri-build` `2.6.3`. CI may preload the Cargo dependency graph before Kodepoia runs; the authoritative Kodepoia build remains `cargo build --locked --offline`.
- Canonical fixture has no Node package manager, no plugins, no custom Tauri command, empty capability set, `withGlobalTauri=false`, restrictive CSP, no remote/dev URL and no bundle/installer target.
- Hosted acceptance target: Windows x64 + Rust MSVC + system WebView2. MSI/VBSCRIPT is intentionally outside R12.9 and remains R12.14 scope.
- No accepted implementation SHA exists yet. Freeze only after R0 + full Python Core + KodeStudio UI Smoke + real `R12 Tauri2 Acceptance` succeed on one exact head.

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

**R12.9 implementation/evidence only.** Finish the Tauri v2 adapter, tests and real hosted Windows Rust/MSVC/WebView2 acceptance, freeze one exact implementation head, record evidence, re-gate final documentation head, merge with `expected_head_sha`, then perform exactly one continuity-only normalization. **R12.10 remains forbidden until that normalization merges.**
