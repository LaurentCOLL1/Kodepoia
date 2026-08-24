# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.4 COMPLETE + NORMALIZED. R12.5 first accepted implementation candidate `bd2ac96b4ac2a1b366ab52aae2ea50f7d49fce33`: R0 #1496 / `32782170580`, Python #1470 / `32782170531`, UI #1437 / `32782170529`, R12 WPF Acceptance #7 / `32782170577`, tous SUCCESS. Hosted Windows a réellement restauré/compilé/testé WPF; manual CONDITIONAL NOT TRIGGERED. Cette documentation crée le final R12.5 head à re-gater avec les quatre workflows. R12.6 reste interdit jusqu’au merge R12.5 puis à son unique normalisation.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` après chaque merge accepté est source de vérité.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.4 : **COMPLETE + NORMALIZED**.
- R12.5 : **FIRST CANDIDATE ACCEPTED / FINAL DOCUMENTATION RE-GATE PENDING**.
- R12.6–R12.16 : **PLANNED / NOT STARTED**.

## R12.4 closure authority

- Final docs `b9c926d94d8ad52de8471287a6b34f9950e24c96`: R0 #1486 / `32779563916`, Python #1460 / `32779563963`, UI #1427 / `32779563925` — SUCCESS; PR #193 merge `a98d985c3200f977f8fdbc38483d4aaf81e870af`.
- Single normalization `b280bf60cddf7b3a9b079d6845d9a991e009487e`: R0 #1488 / `32779785160`, Python #1462 / `32779785121`, UI #1429 / `32779785040` — SUCCESS; PR #194 merge `180a507a81c979ec797f3bafe3de29ba38b72c94`.
- Manual NONE. **R12.4 COMPLETE + NORMALIZED.**

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

## R12.5 acceptance in progress

- Base normalized `main`: `180a507a81c979ec797f3bafe3de29ba38b72c94`.
- Branch `r12/5-wpf-dotnet-adapter`; PR #195; Manual **CONDITIONAL / NOT TRIGGERED**.
- Delivered deterministic WPF adapter, bounded .NET identity, repository-owned `net10.0-windows` app + STA harness, fixed sandboxed restore/build/runtime flow, SHA-256 artifact evidence, adversarial tests and dedicated WPF workflow.
- Initial rejected heads exposed a sandbox environment defect: NuGet machine config requires `%ProgramFiles(x86)%`; accepted candidate inherits only fixed OS machine paths (`ProgramFiles*`, `ProgramData`) while project/user env injection remains rejected.
- Accepted implementation head `bd2ac96b4ac2a1b366ab52aae2ea50f7d49fce33`.
- R0 #1496 / `32782170580` — **SUCCESS**.
- Python Core #1470 / `32782170531` — **SUCCESS**.
- KodeStudio UI Smoke #1437 / `32782170529` — **SUCCESS**.
- R12 WPF Acceptance #7 / `32782170577` — **SUCCESS**, .NET 10.0.400 real restore/build/STA runtime/evidence.
- Evidence recording changes bytes; resulting final documentation head requires fresh exact-head R0 + Python + UI + WPF quartet before merge.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → implementation + focused tests → exact-head standard + adapter-specific gates → satisfy triggered manual state → evidence/re-gate if bytes change → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**R12.5 final documentation re-gate only.** Require fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R12 WPF Acceptance on the resulting head, then merge PR #195 with expected SHA and perform exactly one continuity-only normalization. **R12.6 remains forbidden until that normalization merges.**
