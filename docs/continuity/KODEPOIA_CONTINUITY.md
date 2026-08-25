# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.10 COMPLETE + NORMALIZED. R12.10 normalization PR #206 merged as `25b3e94b58d6ac08511b2510a98148354f5144f2`, sole normalized base for R12.11. R12.11 implementation branch `r12/11-async-concurrency`, PR #207, accepted candidate `39461205919b4fbb01354ea39af9a58638cfcd8c`; exact-head candidate gates R0 #1550, Python #1524, UI #1491, WPF #49, WinUI #39, Avalonia #35, Qt #30 and Tauri #21 are all SUCCESS. Evidence-recording documentation bytes now require a fresh exact-head re-gate before expected-SHA merge. Manual R12.11 state is NONE. R12.12 remains forbidden until the single R12.11 post-merge normalization is accepted and merged.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.10 : **COMPLETE + NORMALIZED**.
- R12.11 : **IMPLEMENTED / CANDIDATE ACCEPTED / FINAL DOCUMENTATION RE-GATE PENDING**.
- R12.12–R12.16 : **PLANNED / NOT STARTED**.

## Recent closure authority

### R12.9

- Final implementation/documentation PR #203 merged as `12624167af41b48438ce6601983038a0ce8fbdc3`.
- Single post-merge normalization PR #204 final head `b16501c9362f5865d0b49d95139e207f196b66e4` passed all required exact-head gates and merged as `136967485e063254904269578f9ab4be23e5d599`.
- Manual R12.9 CONDITIONAL was **NOT TRIGGERED**.
- **R12.9 COMPLETE + NORMALIZED**.

### R12.10

- Base normalized `main`: `136967485e063254904269578f9ab4be23e5d599`.
- Implementation branch `r12/10-sqlite-persistence`; PR #205; Manual **NONE**.
- Accepted implementation candidate `464be11dd9c889336cac20208fc3fb9728ccac5f`.
- Candidate exact-head gates: R0 #1544 / `32818839673`; Python #1518 / `32818839682`; UI #1485 / `32818839667`; WPF #45 / `32818839654`; WinUI #35 / `32818839609`; Avalonia #31 / `32818839711`; Qt #26 / `32818839626`; Tauri #17 / `32818839625` — all SUCCESS.
- Accepted final-documentation head `29b86046d881c87fe77a70e7ce6a952ec13d46e6`: R0 #1546 / `32821661433`; Python #1520 / `32821661437`; UI #1487 / `32821661426`; WPF #47 / `32821661420`; WinUI #37 / `32821661480`; Avalonia #33 / `32821661427`; Qt #28 / `32821661412`; Tauri #19 / `32821661394` — all SUCCESS.
- PR #205 merged with expected head as `8fbec86c3137bbcc48871e7d273a71e7d86db779`.
- Single normalization PR #206 head `15cc38b26aa23f0deda8fdfc4e6e8996d1cc7613`: R0 #1548 / `32822110376`; Python #1522 / `32822110412`; UI #1489 / `32822110410`; WPF #48 / `32822110443`; WinUI #38 / `32822110487`; Avalonia #34 / `32822110395`; Qt #29 / `32822110737`; Tauri #20 / `32822110393` — all SUCCESS.
- PR #206 merged with expected head as `25b3e94b58d6ac08511b2510a98148354f5144f2`.
- **R12.10 COMPLETE + NORMALIZED**.

## R12.11 execution authority

- Base normalized `main`: `25b3e94b58d6ac08511b2510a98148354f5144f2`.
- Dedicated branch: `r12/11-async-concurrency`.
- PR: #207.
- Manual state: **NONE**.
- Frozen scope: framework-neutral async operation/policy descriptors; bounded concurrency and queue wait; cancellation and timeout propagation; deterministic progress; owner-scoped lifecycle cleanup; KillSwitch bridge for governed BUILD/TEST/PACKAGE operations; explicit WPF/WinUI/Avalonia/Qt/Tauri UI-thread dispatcher identities; stale callback and orphan-task prevention.
- Accepted implementation candidate: `39461205919b4fbb01354ea39af9a58638cfcd8c`.
- Exact-head candidate evidence: R0 Repository Guard #1550 / run `32823338030`; Python Core #1524 / `32823338014`; KodeStudio UI Smoke #1491 / `32823337990`; WPF #49 / `32823337991`; WinUI #39 / `32823338016`; Avalonia #35 / `32823338024`; Qt #30 / `32823337983`; Tauri #21 / `32823338040` — all SUCCESS.
- Focused suite `tests/test_desktop_r12_11.py` is exercised by Python Core on Linux and Windows.
- Manual R12.11: **NONE / no manual evidence required**.
- Evidence-recording docs changed after the accepted candidate; therefore the final PR #207 documentation HEAD must pass the same fresh exact-head standard and regression gates before merge with `expected_head_sha`.
- After PR #207 merge, create exactly one continuity-only `r12/11-postmerge-continuity-normalization` PR, gate its exact HEAD, merge it, and only then authorize R12.12.

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

**R12.11 only:** re-gate the final documentation HEAD of PR #207 exactly. If all required gates remain SUCCESS, merge PR #207 with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization with fresh exact-head gates. R12.12 is authorized only after that normalization merge. R12.11 manual state is **NONE**.
