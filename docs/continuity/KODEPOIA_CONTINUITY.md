# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.5 COMPLETE + NORMALIZED. R12.5 final head `07181f30c9326dcb05bafc93da86e0fdb67de8a0`: R0 #1498 / `32782373299`, Python #1472 / `32782373210`, UI #1439 / `32782373424`, WPF #9 / `32782373004`, tous SUCCESS; PR #195 merge `9b9e0060520fec664e90b4c833245dade2c86287`. Single normalization `676edfec7d028f06ecb5d4ef490555b70e5254ea`: R0 #1500 / `32785594679`, Python #1474 / `32785594639`, UI #1441 / `32785594705`, WPF #10 / `32785594643`, tous SUCCESS; PR #196 merge `f84762085282eccc2e2c26ee1c0ccf62fbdfcf49`. Manual R12.5 CONDITIONAL NOT TRIGGERED. R12.6 WinUI 3 est en implémentation sur branche dédiée depuis ce normalized main; R12.7 reste interdit avant R12.6 COMPLETE + NORMALIZED.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` après chaque merge accepté est source de vérité.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.5 : **COMPLETE + NORMALIZED**.
- R12.6 : **IMPLEMENTATION / ACCEPTANCE PENDING**.
- R12.7–R12.16 : **PLANNED / NOT STARTED**.

## Recent closure authority

### R12.4
- Final docs `b9c926d94d8ad52de8471287a6b34f9950e24c96`: R0 #1486 / `32779563916`, Python #1460 / `32779563963`, UI #1427 / `32779563925` — SUCCESS; PR #193 merge `a98d985c3200f977f8fdbc38483d4aaf81e870af`.
- Single normalization `b280bf60cddf7b3a9b079d6845d9a991e009487e`: R0 #1488 / `32779785160`, Python #1462 / `32779785121`, UI #1429 / `32779785040` — SUCCESS; PR #194 merge `180a507a81c979ec797f3bafe3de29ba38b72c94`.
- Manual NONE. **R12.4 COMPLETE + NORMALIZED.**

### R12.5
- Base normalized `main`: `180a507a81c979ec797f3bafe3de29ba38b72c94`.
- Implementation branch `r12/5-wpf-dotnet-adapter`; PR #195; Manual **CONDITIONAL / NOT TRIGGERED**.
- Accepted implementation candidate `bd2ac96b4ac2a1b366ab52aae2ea50f7d49fce33`: R0 #1496 / `32782170580`, Python #1470 / `32782170531`, UI #1437 / `32782170529`, WPF #7 / `32782170577` — SUCCESS.
- Final documentation head `07181f30c9326dcb05bafc93da86e0fdb67de8a0`: R0 #1498 / `32782373299`, Python #1472 / `32782373210`, UI #1439 / `32782373424`, WPF #9 / `32782373004` — SUCCESS.
- PR #195 merge `9b9e0060520fec664e90b4c833245dade2c86287`.
- Single continuity normalization `676edfec7d028f06ecb5d4ef490555b70e5254ea`: R0 #1500 / `32785594679`, Python #1474 / `32785594639`, UI #1441 / `32785594705`, WPF #10 / `32785594643` — SUCCESS.
- PR #196 merge `f84762085282eccc2e2c26ee1c0ccf62fbdfcf49`.
- Hosted Windows proved real .NET 10 WPF restore/build/STA runtime; no manual intervention required. **R12.5 COMPLETE + NORMALIZED.**

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
- Branch `r12/6-winui3-windows-app-sdk`; Manual **CONDITIONAL**, triggered only if hosted Windows cannot prove the required WinUI/Windows App SDK build/runtime/deployment semantic.
- Delivered `WinUiDeploymentContract` + durable schema, deterministic WinUI 3 adapter mapping from `canonical_sample_app()`, bounded .NET 10 + `dotnet new winui` capability probe, Windows App SDK exact package pin, unpackaged self-contained CI fixture, deterministic package manifest identity and separate runtime probe.
- Hosted workflow may provision the documented WinUI dotnet-new template package as CI infrastructure; Kodepoia runtime never installs templates/workloads, enables Developer Mode or requests production certificates.
- Exact implementation candidate/run IDs: **PENDING** until branch freeze and exact-head gates.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → implementation + focused tests → exact-head standard + adapter-specific gates → satisfy triggered manual state → evidence/re-gate if bytes change → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**Freeze and gate R12.6 only.** Require exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + real Windows `R12 WinUI3 Acceptance`. If accepted, record evidence, re-gate final docs, merge, then perform exactly one post-merge continuity normalization. **R12.7 remains forbidden until that normalization merges.**
