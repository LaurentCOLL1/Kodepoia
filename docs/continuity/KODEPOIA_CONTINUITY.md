# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.11 COMPLETE + NORMALIZED. R12.11 implementation PR #207 merged as `86e1663eb4f68f74cdba23687161c8d38849f11e`; its single continuity-only normalization PR #208 head `ea3244b5b031d37d7e2d4e3557c75e369aeff24b` passed all exact-head gates and merged as `1f2d18b01e79845473fefbda98f722485310d92a`. This normalized merge is the sole authorized base for R12.12. R12.12 branch `r12/12-local-ipc` implements bounded local IPC framing/authentication/authorization/replay/lifecycle with real hosted `AF_PIPE` Windows and `AF_UNIX` Linux acceptance. Manual R12.12 is CONDITIONAL and triggers only if the required hosted OS transport semantic cannot be proved. R12.13 remains forbidden until R12.12 and its single post-merge normalization are accepted and merged.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.11 : **COMPLETE + NORMALIZED**.
- R12.12 : **IMPLEMENTATION IN PROGRESS / MANUAL CONDITIONAL PENDING HOSTED EVIDENCE**.
- R12.13–R12.16 : **PLANNED / NOT STARTED**.

## R12.11 closure authority

- Base normalized `main`: `25b3e94b58d6ac08511b2510a98148354f5144f2`.
- Implementation branch `r12/11-async-concurrency`; PR #207; Manual **NONE**.
- Accepted implementation candidate `39461205919b4fbb01354ea39af9a58638cfcd8c`.
- Candidate gates: R0 #1550 / `32823338030`; Python #1524 / `32823338014`; UI #1491 / `32823337990`; WPF #49 / `32823337991`; WinUI #39 / `32823338016`; Avalonia #35 / `32823338024`; Qt #30 / `32823337983`; Tauri #21 / `32823338040` — all SUCCESS.
- Accepted final-documentation head `4e0aaa34b1c45dd35741e7930bdbdaa06740c5e7`: R0 #1552 / `32823953135`; Python #1526 / `32823953175`; UI #1493 / `32823953119`; WPF #51 / `32823953171`; WinUI #41 / `32823953181`; Avalonia #37 / `32823953148`; Qt #32 / `32823953109`; Tauri #23 / `32823953137` — all SUCCESS.
- PR #207 merged with expected head as `86e1663eb4f68f74cdba23687161c8d38849f11e`.
- Single normalization PR #208 exact head `ea3244b5b031d37d7e2d4e3557c75e369aeff24b`: R0 #1554 / `32824419942`; Python #1528 / `32824419923`; UI #1495 / `32824419856`; WPF #52 / `32824419832`; WinUI #42 / `32824419895`; Avalonia #38 / `32824419932`; Qt #33 / `32824419854`; Tauri #24 / `32824419859` — all SUCCESS.
- PR #208 merged with expected head as `1f2d18b01e79845473fefbda98f722485310d92a`.
- **R12.11 COMPLETE + NORMALIZED**. This merge head is the sole authorized base for R12.12.

## R12.12 execution authority

- Base normalized `main`: `1f2d18b01e79845473fefbda98f722485310d92a`.
- Dedicated branch: `r12/12-local-ipc`.
- Manual state: **CONDITIONAL / PENDING**.
- Manual trigger: only if an OS-specific Windows named-pipe or Unix-domain-socket semantic required by acceptance cannot be proven by hosted exact-head CI.
- Frozen scope: versioned local IPC envelope and endpoint identity; bounded length framing; HMAC authentication; peer session/role/method authorization; replay rejection; stale/malformed/oversized/truncated failure; `AF_PIPE` Windows and `AF_UNIX` Linux local transports; no network fallback; owned endpoint cleanup.
- Hosted Python Core on Windows and Linux is the required real transport evidence. Success on both platforms means manual **NOT TRIGGERED**; missing/failing authoritative transport evidence triggers STOP before R12.13.
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

**R12.12 only:** finish implementation and focused tests on `r12/12-local-ipc`, freeze one exact candidate HEAD, require R0 Repository Guard + full Python Core + KodeStudio UI Smoke plus desktop regressions. Hosted Windows `AF_PIPE` and Linux `AF_UNIX` focused tests determine the conditional manual state. If either required transport semantic is not proven, STOP before R12.13; otherwise record manual NOT TRIGGERED, re-gate final documentation bytes, merge with `expected_head_sha`, and perform exactly one continuity-only post-merge normalization.
