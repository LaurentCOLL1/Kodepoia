# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.12 COMPLETE + NORMALIZED. R12.12 implementation PR #209 merged as `e86021ff9080552dcfed5cbb3da2d4405f1cc1a2`; its single continuity-only normalization PR #210 exact head `62874c7db6854c6ef81c9a0eb85e53cbab1da30f` passed all exact-head gates and merged as `34c21c8ba6f12f6cd746dd9aea8c9b3cd7e32c41`. This normalized merge is the sole authorized base for R12.13. R12.13 branch `r12/13-accessibility-localization-qa` is implementing accessibility/localization/theming/keyboard-focus/DPI QA. Manual R12.13 is CONDITIONAL and is not triggered unless a required interactive accessibility/DPI runtime semantic cannot be proven by hosted evidence. R12.14 remains forbidden until R12.13 implementation and its single post-merge normalization are accepted and merged.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.12 : **COMPLETE + NORMALIZED**.
- R12.13 : **IMPLEMENTATION IN PROGRESS**.
- R12.14–R12.16 : **PLANNED / NOT STARTED**.

## R12.12 closure authority

- Base normalized `main`: `1f2d18b01e79845473fefbda98f722485310d92a`.
- Implementation branch `r12/12-local-ipc`; PR #209; Manual **CONDITIONAL / NOT TRIGGERED**.
- Accepted implementation candidate `2ba561745f59b2701e5578df0915e58dab2345e0`.
- Candidate gates: R0 #1556 / `32825111226`; Python #1530 / `32825111135`; UI #1497 / `32825111255`; WPF #53 / `32825111230`; WinUI #43 / `32825111274`; Avalonia #39 / `32825111277`; Qt #34 / `32825111137`; Tauri #25 / `32825111146` — all SUCCESS.
- Hosted Windows and Ubuntu Python Core jobs proved real `AF_PIPE` and `AF_UNIX` request/response roundtrips; manual evidence was not triggered.
- Accepted final-documentation head `227a0c9ac87b464ee08889dd3f60d54faee47907`: R0 #1558 / `32825553323`; Python #1532 / `32825553371`; UI #1499 / `32825553431`; WPF #55 / `32825553296`; WinUI #45 / `32825553308`; Avalonia #41 / `32825553365`; Qt #36 / `32825553292`; Tauri #27 / `32825553336` — all SUCCESS.
- PR #209 merged with expected head as `e86021ff9080552dcfed5cbb3da2d4405f1cc1a2`.
- Single normalization branch `r12/12-postmerge-continuity-normalization`; PR #210; exact head `62874c7db6854c6ef81c9a0eb85e53cbab1da30f`.
- Normalization gates: R0 #1560 / `32826712135`; Python #1534 / `32826712144`; UI #1501 / `32826712166`; WPF #56 / `32826712141`; WinUI #46 / `32826712139`; Avalonia #42 / `32826712108`; Qt #37 / `32826712099`; Tauri #28 / `32826712136` — all SUCCESS.
- PR #210 merged with expected head as `34c21c8ba6f12f6cd746dd9aea8c9b3cd7e32c41`.
- **R12.12 COMPLETE + NORMALIZED**. Its normalization merge is the sole authorized base for R12.13.

## R12.13 execution authority

- Base normalized `main`: `34c21c8ba6f12f6cd746dd9aea8c9b3cd7e32c41`.
- Dedicated branch: `r12/13-accessibility-localization-qa`.
- Manual state: **CONDITIONAL**.
- Trigger only if a required interactive accessibility/DPI runtime semantic is discovered that hosted CI cannot verify. Structural accessibility metadata, deterministic focus/tab ordering, localization/fallback/pseudo-localization, RTL intent, theme/contrast and layout probes are machine-verifiable scope and do not manufacture an interactive screen-reader claim.
- Frozen scope: framework bindings for accessible names/descriptions/roles/focus/localization/theme/DPI; keyboard-only navigation and focus restoration; deterministic locale fallback and pseudo-localization; RTL intent; light/dark/high-contrast semantics; contrast thresholds; Windows scale profiles 100–400%; clipping/overlap/hidden-focus failure; R6 quality-governance integration intent.
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

**R12.13 only:** finish implementation and focused tests on `r12/13-accessibility-localization-qa`, freeze one exact candidate HEAD, require R0 Repository Guard + full Python Core + KodeStudio UI Smoke plus desktop adapter regressions, determine whether the conditional manual trigger actually fires, record evidence, re-gate final documentation bytes, merge with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization. R12.14 is authorized only after that normalization merge.
