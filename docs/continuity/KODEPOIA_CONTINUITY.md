# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.9 COMPLETE + NORMALIZED. R12.9 implementation/final documentation PR #203 merged as `12624167af41b48438ce6601983038a0ce8fbdc3`; its single continuity-only post-merge normalization PR #204 passed its first exact-head gate set on `346bc3c4fb8b6992d21e37920724926073b60f67`. This final continuity head is being re-gated before PR #204 merge. R12.10 becomes the next authorized subdivision only after that merge. Manual R12.9 CONDITIONAL was NOT TRIGGERED.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.9 : **COMPLETE + NORMALIZED** once PR #204 final exact-head re-gate and merge complete.
- R12.10–R12.16 : **PLANNED / NOT STARTED**.

## R12.9 closure authority

- Base normalized `main`: `1cd32eb0cf78dbf468a9921955bbc8695cedab89`.
- Implementation branch `r12/9-tauri2-rust-webview2-adapter`; PR #203; Manual **CONDITIONAL / NOT TRIGGERED**.
- Accepted implementation SHA `2664b65903e3f9dc1399bbbfad10cac772ce5b75`.
- Exact-head gates on implementation SHA: R0 Repository Guard #1537 SUCCESS; Python Core #1511 SUCCESS on Linux+Windows; KodeStudio UI Smoke #1478 SUCCESS; R12 Tauri2 Acceptance #12 / run `32814261183` SUCCESS; Qt #21 SUCCESS; WPF #40 SUCCESS; WinUI #30 SUCCESS; Avalonia #26 SUCCESS.
- Hosted artifact `r12-9-tauri2-windows-2664b65903e3f9dc1399bbbfad10cac772ce5b75`, id `9551033181`, ZIP digest `sha256:67e49aba4a1bb99d9f93e0ad2a13beb3d636a63bf2f6a29287e345974169d407`.
- Proven runtime/toolchain: Windows x64, host `x86_64-pc-windows-msvc`, Cargo `1.97.1`, rustc `1.97.1`, Tauri `2.11.5`, WebView2 `131.0.2903.86`; authoritative build and runtime return codes `0`.
- Runtime sentinel: `KODEPOIA_TAURI2_RUNTIME_PASS:3feb7493c8fa969e638bb9c4454161edea8d1f36f49f2f93a72a99c3b4ca0da0:2.11.5:131.0.2903.86`.
- Security boundaries proved by candidate: no Node/dev server, empty Tauri capability set, no custom IPC commands/plugins, `withGlobalTauri=false`, restrictive CSP, no installer target, governed Cargo build remains `--locked --offline` after CI preload, MSVC environment narrowed to build-system variables.
- Tauri and tauri-build license state remains `REVIEW_REQUIRED`; Kodepoia infers no redistribution rights.
- Accepted final-documentation head `802124c8dc769c9be8db82ab53b4a58838832884`: R0 #1538 / run `32815321882`, Python #1512 / `32815321898`, UI #1479 / `32815321892`, Tauri #13 / `32815321864`, Qt #22 / `32815321852`, WPF #41 / `32815321863`, WinUI #31 / `32815321866`, Avalonia #27 / `32815321908` — all SUCCESS.
- PR #203 merged with expected head `802124c8dc769c9be8db82ab53b4a58838832884` as merge commit `12624167af41b48438ce6601983038a0ce8fbdc3`.
- Single post-merge normalization branch `r12/9-postmerge-continuity-normalization`; PR #204; continuity-only.
- First normalization head `346bc3c4fb8b6992d21e37920724926073b60f67`: R0 #1540 / run `32817089231`, Python #1514 / `32817089300`, UI #1481 / `32817089228`, Tauri #14 / `32817089224`, Qt #23 / `32817089235`, WPF #42 / `32817089227`, WinUI #32 / `32817089185`, Avalonia #28 / `32817089196` — all SUCCESS.
- This final continuity update changes documentation bytes only; exact-head gates must succeed again before PR #204 merge. After that merge, **R12.9 is COMPLETE + NORMALIZED** and its merge head is the sole authorized base for R12.10.

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

**Finish PR #204 only:** gate this final continuity head exactly, merge PR #204 with `expected_head_sha`, and use that merge SHA as normalized `main`. Then and only then create the dedicated R12.10 branch for SQLite persistence/migrations/transactions/backup-recovery. R12.10 manual state is **NONE**.
