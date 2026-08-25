# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.10 COMPLETE + NORMALIZED. R12.11 implementation/final-documentation PR #207 final head `4e0aaa34b1c45dd35741e7930bdbdaa06740c5e7` passed all exact-head gates and merged as `86e1663eb4f68f74cdba23687161c8d38849f11e`. The single continuity-only R12.11 post-merge normalization is now the only authorized action. R12.11 manual state is NONE. R12.12 remains forbidden until that normalization exact head passes all required gates and merges.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.10 : **COMPLETE + NORMALIZED**.
- R12.11 : **IMPLEMENTATION MERGED / POST-MERGE NORMALIZATION IN PROGRESS**.
- R12.12–R12.16 : **PLANNED / NOT STARTED**.

## Recent closure authority

### R12.10

- Base normalized `main`: `136967485e063254904269578f9ab4be23e5d599`.
- PR #205 final-documentation head `29b86046d881c87fe77a70e7ce6a952ec13d46e6` passed R0 #1546, Python #1520, UI #1487, WPF #47, WinUI #37, Avalonia #33, Qt #28 and Tauri #19; merged as `8fbec86c3137bbcc48871e7d273a71e7d86db779`.
- Single normalization PR #206 head `15cc38b26aa23f0deda8fdfc4e6e8996d1cc7613` passed R0 #1548, Python #1522, UI #1489, WPF #48, WinUI #38, Avalonia #34, Qt #29 and Tauri #20; merged as `25b3e94b58d6ac08511b2510a98148354f5144f2`.
- **R12.10 COMPLETE + NORMALIZED**.

### R12.11

- Base normalized `main`: `25b3e94b58d6ac08511b2510a98148354f5144f2`.
- Implementation branch `r12/11-async-concurrency`; PR #207; Manual **NONE**.
- Scope: framework-neutral async operation/policy descriptors; bounded concurrency and queue wait; cancellation and timeout propagation; deterministic progress; owner-scoped lifecycle cleanup; KillSwitch bridge for governed BUILD/TEST/PACKAGE operations; WPF/WinUI/Avalonia/Qt/Tauri UI-thread dispatcher identities; stale callback and orphan-task prevention.
- Accepted implementation candidate `39461205919b4fbb01354ea39af9a58638cfcd8c`.
- Candidate exact-head gates: R0 #1550 / `32823338030`; Python #1524 / `32823338014`; UI #1491 / `32823337990`; WPF #49 / `32823337991`; WinUI #39 / `32823338016`; Avalonia #35 / `32823338024`; Qt #30 / `32823337983`; Tauri #21 / `32823338040` — all SUCCESS.
- Accepted final-documentation head `4e0aaa34b1c45dd35741e7930bdbdaa06740c5e7`: R0 #1552 / `32823953135`; Python #1526 / `32823953175`; UI #1493 / `32823953119`; WPF #51 / `32823953171`; WinUI #41 / `32823953181`; Avalonia #37 / `32823953148`; Qt #32 / `32823953109`; Tauri #23 / `32823953137` — all SUCCESS.
- PR #207 merged with expected head `4e0aaa34b1c45dd35741e7930bdbdaa06740c5e7` as merge commit `86e1663eb4f68f74cdba23687161c8d38849f11e`.
- Single post-merge normalization branch `r12/11-postmerge-continuity-normalization`; continuity-only. Its exact head must pass the standard exact-head gate set plus desktop adapter regressions before merge.
- After that normalization merge, **R12.11 becomes COMPLETE + NORMALIZED** and the normalization merge SHA becomes the sole authorized base for R12.12.

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

**R12.11 normalization only:** open the single continuity-only post-merge normalization PR from `r12/11-postmerge-continuity-normalization`, gate its exact head, and merge it with `expected_head_sha`. Then and only then create the dedicated R12.12 branch from that normalized `main` merge SHA. R12.12 manual state is **CONDITIONAL**.
