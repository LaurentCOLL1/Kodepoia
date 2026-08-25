# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.12 COMPLETE + NORMALIZED. R12.13 implementation/final-documentation PR #211 accepted candidate `646b4ad079113e27bb8d091c4153b125b6673f8c`; final documentation head `84f75090759e6a54da5b69c8b9b6970ac7c572ae` passed all exact-head gates and merged as `2c0f5c5c1b64747a44e5fd2b41532e469a3ae8b2`. Manual R12.13 CONDITIONAL was NOT TRIGGERED because no required unproven interactive accessibility/DPI semantic was discovered. The single continuity-only branch `r12/13-postmerge-continuity-normalization` is now the only authorized action. R12.14 remains forbidden until its exact normalization head passes all required gates and merges.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.12 : **COMPLETE + NORMALIZED**.
- R12.13 : **IMPLEMENTATION MERGED / POST-MERGE NORMALIZATION IN PROGRESS**.
- R12.14–R12.16 : **PLANNED / NOT STARTED**.

## R12.12 closure authority

- Implementation PR #209 merged as `e86021ff9080552dcfed5cbb3da2d4405f1cc1a2`; manual **CONDITIONAL / NOT TRIGGERED** with hosted real `AF_PIPE`/`AF_UNIX` roundtrips.
- Single normalization PR #210 exact head `62874c7db6854c6ef81c9a0eb85e53cbab1da30f` passed R0 #1560, Python #1534, UI #1501, WPF #56, WinUI #46, Avalonia #42, Qt #37 and Tauri #28 and merged as `34c21c8ba6f12f6cd746dd9aea8c9b3cd7e32c41`.
- **R12.12 COMPLETE + NORMALIZED**.

## R12.13 closure authority

- Base normalized `main`: `34c21c8ba6f12f6cd746dd9aea8c9b3cd7e32c41`.
- Implementation branch `r12/13-accessibility-localization-qa`; PR #211.
- Manual state: **CONDITIONAL / NOT TRIGGERED**.
- Scope: digest-stable accessibility profile; WPF/WinUI3/Avalonia/Qt6/Tauri2 accessibility/focus/localization/theme/DPI mappings; keyboard tab order and focus restoration; localization fallback and pseudo-localization; RTL intent; light/dark/high-contrast semantics; contrast gates; scale profiles 100–400%; clipping/overlap/hidden-focus negative cases.
- Accepted implementation candidate `646b4ad079113e27bb8d091c4153b125b6673f8c`.
- Candidate gates: R0 #1562 / `32827475621`; Python #1536 / `32827475643`; UI #1503 / `32827475650`; WPF #57 / `32827475625`; WinUI #47 / `32827475686`; Avalonia #43 / `32827475711`; Qt #38 / `32827475698`; Tauri #29 / `32827475658` — all SUCCESS.
- Full Python Core passed the focused R12.13 suite on hosted Linux and Windows. No acceptance claim requires an unexecuted interactive screen-reader result; manual evidence did not trigger.
- Accepted final-documentation head `84f75090759e6a54da5b69c8b9b6970ac7c572ae`.
- Final-documentation gates: R0 #1564 / `32827958711`; Python #1538 / `32827958647`; UI #1505 / `32827958665`; WPF #59 / `32827958616`; WinUI #49 / `32827958581`; Avalonia #45 / `32827958608`; Qt #40 / `32827958615`; Tauri #31 / `32827958693` — all SUCCESS.
- PR #211 merged with expected head `84f75090759e6a54da5b69c8b9b6970ac7c572ae` as merge commit `2c0f5c5c1b64747a44e5fd2b41532e469a3ae8b2`.
- Single post-merge normalization branch `r12/13-postmerge-continuity-normalization`; continuity-only. Its exact head must pass the standard exact-head gate set plus desktop adapter regressions before merge.
- After normalization merge, **R12.13 becomes COMPLETE + NORMALIZED** and the normalization merge SHA becomes the sole authorized base for R12.14.

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

**R12.13 normalization only:** open the single continuity-only normalization PR from `r12/13-postmerge-continuity-normalization`, gate its exact head and merge it with `expected_head_sha`. Then and only then create the dedicated R12.14 branch from that normalized merge SHA. R12.14 manual state is **CONDITIONAL**.
