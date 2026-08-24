# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.5 COMPLETE + NORMALIZED. R12.6 first accepted implementation candidate `b990a613d6becbc80e637ea0184f87b502573b74`: R0 #1502 / `32786054869`, Python #1476 / `32786054919`, UI #1443 / `32786054865`, WPF regression #11 / `32786054841`, R12 WinUI3 Acceptance #1 / `32786054895`, tous SUCCESS. Hosted Windows a réellement provisionné le template WinUI documenté, restauré Windows App SDK `1.8.260804001`, compilé le fixture et chargé le runtime; manual CONDITIONAL NOT TRIGGERED. Cette documentation crée le final R12.6 head à re-gater. R12.7 reste interdit jusqu’au merge R12.6 puis à son unique normalisation.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` après chaque merge accepté est source de vérité.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.5 : **COMPLETE + NORMALIZED**.
- R12.6 : **FIRST CANDIDATE ACCEPTED / FINAL DOCUMENTATION RE-GATE PENDING**.
- R12.7–R12.16 : **PLANNED / NOT STARTED**.

## Recent closure authority

### R12.5
- Final documentation head `07181f30c9326dcb05bafc93da86e0fdb67de8a0`: R0 #1498 / `32782373299`, Python #1472 / `32782373210`, UI #1439 / `32782373424`, WPF #9 / `32782373004` — SUCCESS; PR #195 merge `9b9e0060520fec664e90b4c833245dade2c86287`.
- Single continuity normalization `676edfec7d028f06ecb5d4ef490555b70e5254ea`: R0 #1500 / `32785594679`, Python #1474 / `32785594639`, UI #1441 / `32785594705`, WPF #10 / `32785594643` — SUCCESS; PR #196 merge `f84762085282eccc2e2c26ee1c0ccf62fbdfcf49`.
- Manual CONDITIONAL NOT TRIGGERED. **R12.5 COMPLETE + NORMALIZED.**

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

## R12.6 acceptance in progress

- Base normalized `main`: `f84762085282eccc2e2c26ee1c0ccf62fbdfcf49`.
- Branch `r12/6-winui3-windows-app-sdk`; PR #197; Manual **CONDITIONAL / NOT TRIGGERED**.
- Delivered schema-backed `WinUiDeploymentContract`, deterministic WinUI 3 mapping, bounded .NET 10 + template probe, exact Windows App SDK package pin, deterministic package manifest, unpackaged self-contained acceptance fixture and separate runtime probe.
- Accepted implementation head `b990a613d6becbc80e637ea0184f87b502573b74`.
- R0 #1502 / `32786054869` — **SUCCESS**.
- Python Core #1476 / `32786054919` — **SUCCESS**.
- KodeStudio UI Smoke #1443 / `32786054865` — **SUCCESS**.
- WPF regression #11 / `32786054841` — **SUCCESS**.
- R12 WinUI3 Acceptance #1 / `32786054895` — **SUCCESS**, real hosted Windows template/restore/build/runtime/evidence.
- Evidence recording changes bytes; the resulting final documentation head requires fresh exact-head R0 + Python + UI + WinUI before merge.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → implementation + focused tests → exact-head standard + adapter-specific gates → satisfy triggered manual state → evidence/re-gate if bytes change → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**R12.6 final documentation re-gate only.** Require fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R12 WinUI3 Acceptance on the resulting head, then merge PR #197 with `expected_head_sha` and perform exactly one post-merge continuity normalization. **R12.7 remains forbidden until that normalization merges.**
