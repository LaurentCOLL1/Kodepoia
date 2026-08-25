# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.12 COMPLETE + NORMALIZED. R12.12 normalization PR #210 merged as `34c21c8ba6f12f6cd746dd9aea8c9b3cd7e32c41`, sole normalized base for R12.13. R12.13 branch `r12/13-accessibility-localization-qa`, PR #211, accepted implementation candidate `646b4ad079113e27bb8d091c4153b125b6673f8c`; R0 #1562, Python #1536, UI #1503, WPF #57, WinUI #47, Avalonia #43, Qt #38 and Tauri #29 are all SUCCESS. Full Python Core passed the R12.13 structural accessibility/localization/theming/keyboard-focus/DPI suite on Linux and Windows. No required unproven interactive assistive-technology semantic was discovered, therefore manual R12.13 CONDITIONAL is NOT TRIGGERED. Evidence-recording documentation bytes now require a fresh exact-head re-gate before expected-SHA merge. R12.14 remains forbidden until the single R12.13 post-merge normalization is accepted and merged.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.12 : **COMPLETE + NORMALIZED**.
- R12.13 : **IMPLEMENTED / CANDIDATE ACCEPTED / FINAL DOCUMENTATION RE-GATE PENDING**.
- R12.14–R12.16 : **PLANNED / NOT STARTED**.

## R12.12 closure authority

- Implementation PR #209 final-documentation head `227a0c9ac87b464ee08889dd3f60d54faee47907` passed all required exact-head gates and merged as `e86021ff9080552dcfed5cbb3da2d4405f1cc1a2`.
- Manual R12.12: **CONDITIONAL / NOT TRIGGERED**; hosted Windows/Linux Python Core proved real `AF_PIPE`/`AF_UNIX` roundtrips.
- Single normalization branch `r12/12-postmerge-continuity-normalization`; PR #210; head `62874c7db6854c6ef81c9a0eb85e53cbab1da30f`.
- Normalization gates: R0 #1560 / `32826712135`; Python #1534 / `32826712144`; UI #1501 / `32826712166`; WPF #56 / `32826712141`; WinUI #46 / `32826712139`; Avalonia #42 / `32826712108`; Qt #37 / `32826712099`; Tauri #28 / `32826712136` — all SUCCESS.
- PR #210 merged with expected head as `34c21c8ba6f12f6cd746dd9aea8c9b3cd7e32c41`.
- **R12.12 COMPLETE + NORMALIZED**.

## R12.13 execution authority

- Base normalized `main`: `34c21c8ba6f12f6cd746dd9aea8c9b3cd7e32c41`.
- Dedicated branch: `r12/13-accessibility-localization-qa`.
- PR: #211.
- Manual state: **CONDITIONAL / NOT TRIGGERED**.
- Trigger is restricted to a required interactive accessibility/DPI runtime semantic that hosted CI cannot verify. No such required unproven semantic was discovered. R12.13 makes structural accessibility/localization/theming/keyboard/focus/DPI claims only and does not manufacture an interactive screen-reader PASS.
- Frozen implemented scope: digest-stable `DesktopAccessibilityProfile`; mappings for WPF/WinUI3/Avalonia/Qt6/Tauri2 accessible-name/description/role/focus/localization/theme/DPI concepts; deterministic keyboard tab order and focus restoration; localization catalogs/fallback/pseudo-localization; RTL intent; light/dark/high-contrast semantics; contrast gates; Windows scale probes 100–400%; clipping/overlap/hidden-focus failures; canonical/negative fixtures.
- Accepted implementation candidate: `646b4ad079113e27bb8d091c4153b125b6673f8c`.
- Exact-head candidate evidence: R0 #1562 / run `32827475621`; Python #1536 / `32827475643`; UI #1503 / `32827475650`; WPF #57 / `32827475625`; WinUI #47 / `32827475686`; Avalonia #43 / `32827475711`; Qt #38 / `32827475698`; Tauri #29 / `32827475658` — all SUCCESS.
- Full Python Core passed `tests/test_desktop_r12_13.py` on hosted Linux and Windows.
- Evidence-recording docs changed after the accepted candidate. The final documentation HEAD must receive the same fresh exact-head gate set before PR #211 can merge with `expected_head_sha`.
- After PR #211 merge, create exactly one continuity-only `r12/13-postmerge-continuity-normalization` PR, gate its exact HEAD and merge it. Only that normalized merge authorizes R12.14.

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

**R12.13 only:** re-gate the final documentation HEAD of PR #211 exactly. If all required gates remain SUCCESS, merge PR #211 with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization with fresh exact-head gates. R12.14 is authorized only after that normalization merge. Manual R12.13 is **CONDITIONAL / NOT TRIGGERED**.
