# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.2 COMPLETE + NORMALIZED. R12.3 first implementation candidate `bf4c5b095bc7b91ecf7c27100c3da81c0a13ce31` est accepté : R0 #1478 / `32778299021`, Python Core #1452 / `32778298974`, UI Smoke #1419 / `32778299000`, tous SUCCESS. Cette documentation crée le final R12.3 head à re-gater avant merge de PR #191. Manual NONE. R12.4 reste interdit jusqu’au merge R12.3 puis à son unique normalisation post-merge.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` après chaque merge accepté est source de vérité.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.2 : **COMPLETE + NORMALIZED**.
- R12.3 : **FIRST CANDIDATE ACCEPTED / FINAL DOCUMENTATION HEAD RE-GATE PENDING**.
- R12.4–R12.16 : **PLANNED / NOT STARTED**.

## R12.1 closure authority

- PR #187 final head `5d541ea9b71fead8c048a8933dccbfdfe357bf7e`: R0 #1469 / `32773951265`, Python #1443 / `32773951408`, UI #1410 / `32773951307` — SUCCESS; merge `8f8dc143b0d3788184577f55cf9f8503783898d3`.
- Single normalization head `4d2a90593844b69bc26dba5ee9d7e68e04de3b82`: R0 #1471 / `32774326113`, Python #1445 / `32774326078`, UI #1412 / `32774326154` — SUCCESS; PR #188 merge `d0c97b89a49a0bb3a49761a0ccf46ac755c3a1e8`.
- Manual NONE. **R12.1 COMPLETE + NORMALIZED.**

## R12.2 closure authority

- Base normalized `main`: `d0c97b89a49a0bb3a49761a0ccf46ac755c3a1e8`.
- Implementation branch `r12/2-desktop-project-wizard`; PR #189; Manual **NONE**.
- First candidate `7d26027c8eed997fc1c8c2bdedf4c9a3bd47bb21`: R0 #1473 / `32775050033`, Python #1447 / `32775049955`, UI #1414 / `32775049980` — SUCCESS.
- Final documentation head `030d35ecd2d712bb9465760854a54ddc96c1c652`: R0 #1474 / `32775260396`, Python #1448 / `32775260347`, UI #1415 / `32775260363` — SUCCESS.
- PR #189 merge: `919508b6aad977ee7c4242b51509d108b1bdf1f6`.
- Single continuity normalization head `611c8768bb11ad25ca275eb50cb4cc325abe1db3`: R0 #1476 / `32776007461`, Python Core #1450 / `32776007559`, UI Smoke #1417 / `32776007449` — SUCCESS.
- Normalization PR #190 merge: `6a58719522b46b0f89b9514dbeff6cb5ca0bdb6c`.
- Manual NONE. **R12.2 COMPLETE + NORMALIZED.**

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

## R12.3 acceptance in progress

- Base normalized `main`: `6a58719522b46b0f89b9514dbeff6cb5ca0bdb6c`.
- Branch: `r12/3-desktop-scaffold-engine`; PR #191; Manual **NONE**.
- Delivered deterministic typed scaffold engine, strict durable template/workspace schemas, repository-owned canonical template, read-only preview, whole-file ownership, prior-SHA guard, SafeChange + Backup + Audit destructive-regeneration path and R8-style DNA/Product/template/file lineage.
- Focused tests cover deterministic bytes/digests, schema load, traversal/reserved/symlink/directive/type attacks, preservation/conflict policy, prior-SHA anti-overwrite and governed backup/audit regeneration.
- First accepted implementation candidate: `bf4c5b095bc7b91ecf7c27100c3da81c0a13ce31`.
- R0 Repository Guard #1478 / `32778299021` — **SUCCESS**.
- Python Core #1452 / `32778298974` — **SUCCESS**, Ubuntu/Windows pytest + package builds + internal KodeStudio smoke.
- KodeStudio UI Smoke #1419 / `32778299000` — **SUCCESS**.
- Evidence recording changes bytes after that candidate; the resulting final documentation head requires a fresh exact-head R0 + full Python + UI triplet before expected-SHA merge of #191.

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → implementation + focused tests → exact-head R0/full Python/UI → satisfy REQUIRED/triggered CONDITIONAL manual state → final docs/evidence and re-gate if head changes → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + same exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands/prerequisites/evidence path.

## Next authorized action

**R12.3 final documentation re-gate only.** Merge PR #191 only after fresh R0 + full Python Core + UI succeed, then perform exactly one continuity normalization. **R12.4 remains forbidden until that normalization merges.**
