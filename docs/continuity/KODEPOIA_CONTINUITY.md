# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.8 COMPLETE + NORMALIZED. R12.8 normalization PR #202 merged as `1cd32eb0cf78dbf468a9921955bbc8695cedab89`. R12.9 is the only active subdivision on branch `r12/9-tauri2-rust-webview2-adapter`, PR #203, based exactly on that normalized main. Accepted implementation candidate `2664b65903e3f9dc1399bbbfad10cac772ce5b75`: R0 #1537, Python #1511, UI #1478, Tauri #12 / run `32814261183`, Qt #21, WPF #40, WinUI #30, Avalonia #26 — all SUCCESS. Hosted Tauri evidence proves Rust/Cargo 1.97.1 MSVC, Tauri 2.11.5 and WebView2 131.0.2903.86 with build/runtime return codes 0. Manual R12.9 CONDITIONAL was NOT TRIGGERED. Acceptance evidence is now recorded; re-gate the resulting final documentation head, merge #203 with expected SHA, then perform exactly one continuity-only post-merge normalization. R12.10 remains forbidden until that normalization merges.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.8 : **COMPLETE + NORMALIZED**.
- R12.9 : **IMPLEMENTATION ACCEPTED / FINAL-DOC REGATE REQUIRED**.
- R12.10–R12.16 : **PLANNED / NOT STARTED**.

## Recent closure authority

### R12.8
- Base normalized `main`: `306d0b6fafb6d8c9c069936799e0c82bf94be1c7`.
- Implementation branch `r12/8-qt6-cmake-adapter`; PR #201; Manual **CONDITIONAL / NOT TRIGGERED**.
- Accepted implementation candidate `7d59d1e1320f18f0173d4df0374b174075b8d3fa`: R0 #1519 / `32791617782`, Python #1493 / `32791617851`, UI #1460 / `32791617772`, Qt #5 / `32791617789`, Avalonia #10 / `32791617798`, WPF #24 / `32791617714`, WinUI #14 / `32791617839` — SUCCESS.
- Accepted Qt route: hosted macOS ARM64, Homebrew `qtbase`, Qt `6.11.1`, CMake `4.4.0`, Ninja, AppleClang `21.0.0.21000101`; configure/build/runtime return codes `0`.
- Final documentation head `091a356b42328b169b37ca1601d922e1720ef3e1`: R0 #1522 / `32791843505`, Python #1496 / `32791843496`, UI #1463 / `32791843461`, Qt #8 / `32791843472`, Avalonia #13 / `32791843614`, WPF #27 / `32791843555`, WinUI #17 / `32791843482` — SUCCESS; PR #201 merge `8d18f95740c33820ae79362f388471cd587629da`.
- Single continuity normalization `a926f0a3bfd713c668554b14d673582db981b7bf`: R0 #1524 / `32811363092`, Python #1498 / `32811363187`, UI #1465 / `32811363114`, Qt #9 / `32811363119`, Avalonia #14 / `32811363132`, WPF #28 / `32811363023`, WinUI #18 / `32811363023` — SUCCESS; PR #202 merge `1cd32eb0cf78dbf468a9921955bbc8695cedab89`.
- Manual CONDITIONAL NOT TRIGGERED. **R12.8 COMPLETE + NORMALIZED.**

## R12.9 accepted implementation / final-doc regate

- Base normalized `main`: `1cd32eb0cf78dbf468a9921955bbc8695cedab89`.
- Branch `r12/9-tauri2-rust-webview2-adapter`; PR #203; Manual **CONDITIONAL / NOT TRIGGERED**.
- Accepted implementation SHA `2664b65903e3f9dc1399bbbfad10cac772ce5b75`.
- Exact-head gates on that SHA: R0 Repository Guard #1537 SUCCESS; Python Core #1511 SUCCESS on Linux+Windows; KodeStudio UI Smoke #1478 SUCCESS; R12 Tauri2 Acceptance #12 / run `32814261183` SUCCESS; Qt #21 SUCCESS; WPF #40 SUCCESS; WinUI #30 SUCCESS; Avalonia #26 SUCCESS.
- Hosted artifact `r12-9-tauri2-windows-2664b65903e3f9dc1399bbbfad10cac772ce5b75`, id `9551033181`, ZIP digest `sha256:67e49aba4a1bb99d9f93e0ad2a13beb3d636a63bf2f6a29287e345974169d407`.
- Proven runtime/toolchain: Windows x64, host `x86_64-pc-windows-msvc`, Cargo `1.97.1`, rustc `1.97.1`, Tauri `2.11.5`, WebView2 `131.0.2903.86`; authoritative build and runtime return codes `0`.
- Runtime sentinel: `KODEPOIA_TAURI2_RUNTIME_PASS:3feb7493c8fa969e638bb9c4454161edea8d1f36f49f2f93a72a99c3b4ca0da0:2.11.5:131.0.2903.86`.
- Security boundaries proved by candidate: no Node/dev server, empty Tauri capability set, no custom IPC commands/plugins, `withGlobalTauri=false`, restrictive CSP, no installer target, governed Cargo build remains `--locked --offline` after CI preload, MSVC environment is narrowed to build-system variables.
- Tauri and tauri-build license state remains `REVIEW_REQUIRED`; Kodepoia infers no redistribution rights.
- Evidence recording changes bytes: final documentation head must pass exact-head R0 + Python + UI + Tauri and all triggered R12 regression workflows before expected-SHA merge of #203.

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

Each R12 subdivision: dedicated branch from normalized `main` → implementation + focused tests → exact-head standard + subdivision-specific gates → satisfy triggered manual state → evidence/re-gate if bytes change → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**R12.9 final-documentation re-gate only.** Re-gate the evidence-recording head, merge PR #203 with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization and exact-head gate/merge it. **R12.10 remains forbidden until that normalization merges.**
