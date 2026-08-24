# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.3 COMPLETE + NORMALIZED. R12.4 implementation/evidence ACCEPTED + MERGED via PR #193, merge `a98d985c3200f977f8fdbc38483d4aaf81e870af`; exactement une continuity-only normalization est en cours. Final R12.4 head `b9c926d94d8ad52de8471287a6b34f9950e24c96`: R0 #1486 / `32779563916`, Python Core #1460 / `32779563963`, UI Smoke #1427 / `32779563925`, tous SUCCESS. Manual NONE. R12.5 reste interdit jusqu’au succès et merge de cette normalisation.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` après chaque merge accepté est source de vérité.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.3 : **COMPLETE + NORMALIZED**.
- R12.4 : **ACCEPTED + MERGED / CONTINUITY NORMALIZATION PENDING**.
- R12.5–R12.16 : **PLANNED / NOT STARTED**.

## Recent closure authority

### R12.3
- Final docs `be9217edf96518556c37f7e1ae3b1cdcb093cdb7`: R0 #1480 / `32778510158`, Python #1454 / `32778510179`, UI #1421 / `32778510136` — SUCCESS; PR #191 merge `dab35e11a354b4a8d90c6d8bf5695a3e8f9c6937`.
- Normalization `34a5becb45603c1cf0ddc7b1679111dc44708397`: R0 #1482 / `32778771303`, Python #1456 / `32778771366`, UI #1423 / `32778771306` — SUCCESS; PR #192 merge `1f52adffedb69384904a4b35bb32e45e06b05e33`.
- Manual NONE. **R12.3 COMPLETE + NORMALIZED.**

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

## R12.4 closure

- Base normalized `main`: `1f52adffedb69384904a4b35bb32e45e06b05e33`.
- Implementation branch `r12/4-desktop-app-contracts`; PR #193; Manual **NONE**.
- Delivered framework-neutral `DesktopAppModel`, durable schema and canonical shared adapter fixture.
- First accepted candidate `d55b55feedcfc638e1e11d194d12f80b8f7b6f9c`: R0 #1484 / `32779332770`, Python #1458 / `32779332780`, UI #1425 / `32779332799` — SUCCESS.
- Final documentation head `b9c926d94d8ad52de8471287a6b34f9950e24c96`: R0 #1486 / `32779563916`, Python #1460 / `32779563963`, UI #1427 / `32779563925` — SUCCESS.
- PR #193 merge `a98d985c3200f977f8fdbc38483d4aaf81e870af`.
- Current branch `r12/4-postmerge-continuity-normalization` is the **single** authorized R12.4 continuity normalization and MUST change only this file.
- Accepted normalization triplet + merge makes **R12.4 COMPLETE + NORMALIZED** and authorizes R12.5.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → implementation + focused tests → exact-head R0/full Python/UI → satisfy REQUIRED/triggered CONDITIONAL manual state → final docs/evidence and re-gate if head changes → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + same exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**R12.4 continuity normalization only.** Gate its exact head with R0 + full Python Core + KodeStudio UI Smoke and merge with `expected_head_sha`. **Only that merge authorizes R12.5.**
