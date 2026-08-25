# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.10 COMPLETE + NORMALIZED. R12.10 implementation/final-documentation PR #205 merged as `8fbec86c3137bbcc48871e7d273a71e7d86db779`; its single continuity-only normalization PR #206 exact head `15cc38b26aa23f0deda8fdfc4e6e8996d1cc7613` passed all exact-head gates and merged as `25b3e94b58d6ac08511b2510a98148354f5144f2`. This normalized merge is the sole authorized base for R12.11. R12.11 branch `r12/11-async-concurrency` is implementing bounded async/concurrency, cancellation, progress, UI-thread affinity and owner lifecycle safety. Manual R12.11 state is NONE. R12.12 remains forbidden until R12.11 implementation and its single post-merge normalization are accepted and merged.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.10 : **COMPLETE + NORMALIZED**.
- R12.11 : **IMPLEMENTATION IN PROGRESS**.
- R12.12–R12.16 : **PLANNED / NOT STARTED**.

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
- Final normalization head `b16501c9362f5865d0b49d95139e207f196b66e4`: R0 #1541 / run `32817426235`, Python #1515 / `32817426223`, UI #1482 / `32817426134`, Tauri #15 / `32817426144`, Qt #24 / `32817426178`, WPF #43 / `32817426138`, WinUI #33 / `32817426145`, Avalonia #29 / `32817426180` — all SUCCESS.
- PR #204 merged with expected head `b16501c9362f5865d0b49d95139e207f196b66e4` as merge commit `136967485e063254904269578f9ab4be23e5d599`.
- **R12.9 COMPLETE + NORMALIZED**. Manual R12.9 CONDITIONAL was **NOT TRIGGERED**.

## R12.10 closure authority

- Base normalized `main`: `136967485e063254904269578f9ab4be23e5d599`.
- Implementation branch `r12/10-sqlite-persistence`; PR #205; Manual **NONE**.
- Scope: deterministic SQLite schema digests; typed/parameterized data intents; bounded migration graph; transaction, foreign-key, busy-timeout and integrity policy; online backup/recovery; exact-schema import validation; SafeChange/Backup/Recovery/Audit integration.
- Accepted implementation candidate `464be11dd9c889336cac20208fc3fb9728ccac5f`.
- Exact-head gates on candidate: R0 #1544 / run `32818839673`; Python #1518 / `32818839682`; UI #1485 / `32818839667`; WPF #45 / `32818839654`; WinUI #35 / `32818839609`; Avalonia #31 / `32818839711`; Qt #26 / `32818839626`; Tauri #17 / `32818839625` — all SUCCESS.
- Accepted final-documentation head `29b86046d881c87fe77a70e7ce6a952ec13d46e6`: R0 #1546 / run `32821661433`; Python #1520 / `32821661437`; UI #1487 / `32821661426`; WPF #47 / `32821661420`; WinUI #37 / `32821661480`; Avalonia #33 / `32821661427`; Qt #28 / `32821661412`; Tauri #19 / `32821661394` — all SUCCESS.
- PR #205 merged with expected head `29b86046d881c87fe77a70e7ce6a952ec13d46e6` as merge commit `8fbec86c3137bbcc48871e7d273a71e7d86db779`.
- Single post-merge normalization branch `r12/10-postmerge-continuity-normalization`; PR #206; continuity-only.
- Normalization head `15cc38b26aa23f0deda8fdfc4e6e8996d1cc7613`: R0 #1548 / run `32822110376`; Python #1522 / `32822110412`; UI #1489 / `32822110410`; WPF #48 / `32822110443`; WinUI #38 / `32822110487`; Avalonia #34 / `32822110395`; Qt #29 / `32822110737`; Tauri #20 / `32822110393` — all SUCCESS.
- PR #206 merged with expected head `15cc38b26aa23f0deda8fdfc4e6e8996d1cc7613` as merge commit `25b3e94b58d6ac08511b2510a98148354f5144f2`.
- **R12.10 COMPLETE + NORMALIZED**. Its merge head is the sole authorized base for R12.11.

## R12.11 execution authority

- Base normalized `main`: `25b3e94b58d6ac08511b2510a98148354f5144f2`.
- Dedicated branch: `r12/11-async-concurrency`.
- Manual state: **NONE**.
- Frozen scope: framework-neutral async descriptors; cancellation propagation; KillSwitch bridge for governed external operations; UI dispatcher/thread-affinity intent; bounded concurrency/queue/progress; owner/disposal lifecycle; deterministic timeout/deadlock/starvation safety tests.
- Implementation candidate and exact-head evidence: **PENDING** until branch freeze and hosted gates.

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

**R12.11 only:** finish implementation and focused tests on `r12/11-async-concurrency`, freeze one exact candidate HEAD, require R0 Repository Guard + full Python Core + KodeStudio UI Smoke plus desktop adapter regressions, record evidence, re-gate final documentation bytes, merge with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization. R12.12 is authorized only after that normalization merge. R12.11 manual state is **NONE**.
