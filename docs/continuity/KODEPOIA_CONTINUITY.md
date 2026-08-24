# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 24 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning est ACCEPTED + MERGED via PR #185; exactement une planning continuity normalization est maintenant en cours. R12.1 reste interdit jusqu’au succès exact-head R0 + full Python Core + KodeStudio UI Smoke de cette normalisation et à son merge.** Plan final head `661c09e57639190a60630411127d49870a959cc9`: R0 #1464 / `32772400955`, Python Core #1438 / `32772400921`, UI Smoke #1405 / `32772400996`, tous SUCCESS. PR #185 merge `6ad0e6045ac70a82f367b4eacb18d927ffd1bddf`. `docs/roadmap/R12_PLAN.md` fige R12.1–R12.16. Aucun R12.x n’est encore implémenté.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; `main` est la source de vérité après chaque merge accepté.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + MERGED; CONTINUITY NORMALIZATION PENDING**.
- R12.1–R12.16 : **PLANNED / NOT STARTED**.
- R13–R16 : **PENDING / NOT STARTED**.

## R11 closure authority

- R11 canonical integrated report : `docs/roadmap/R11_INTEGRATED_ACCEPTANCE.json` — `status=pass`, `blockers=[]`, semantic digest `ed956be1aa19592b654382a209e5ca99d44d3cbcd67dd3981bdae3d865563170`.
- R11.14 accepted implementation head `f2693c8cfd4a7aaa5c73fc0a318ebaeef4ff0bb1`: R0 #1455 / `32769325414`, Python #1429 / `32769325329`, UI #1396 / `32769325281` SUCCESS.
- R11.14 final docs/evidence head `081fe88009aeb0cc89c6f91bd01184646d4aacdd`: R0 #1459 / `32769936597`, Python #1433 / `32769936407`, UI #1400 / `32769936452` SUCCESS.
- R11.14 implementation/evidence PR #183 merge `03dad4366ff5332b0728f548497f2051b7051138`.
- R11.14 continuity normalization head `b406ea16538843bbce8c75b0633c151e3bab2eb4`: R0 #1461 / `32771013589`, Python #1435 / `32771013516`, UI #1402 / `32771013711` SUCCESS.
- R11.14 normalization PR #184 merge `6d3c7eb557d940641977d18384e4f6d2bad42f3c`.
- R11.14 manual **CONDITIONAL NOT TRIGGERED**.

## R12 planning closure in progress

Roadmap title : **R12 — Desktop applications**. Roadmap DoD : **créer, compiler et tester une application Windows moderne depuis le Project Wizard**.

- Plan : `docs/roadmap/R12_PLAN.md`.
- Planning branch : `r12/00-phase-plan`, base normalized `main` `6d3c7eb557d940641977d18384e4f6d2bad42f3c`.
- Planning PR : #185.
- Premier planning candidate `b085fbdb03d62bd06dbdd045eccded3a0de667ab`: R0 #1463 / `32771732655`, Python #1437 / `32771732751`, UI #1404 / `32771732640` SUCCESS.
- Final planning documentation head `661c09e57639190a60630411127d49870a959cc9`: R0 #1464 / `32772400955`, Python #1438 / `32772400921`, UI #1405 / `32772400996` SUCCESS.
- Python #1438 includes Python Ubuntu/Windows, package builds Ubuntu/Windows and KodeStudio UI smoke internal, all SUCCESS.
- PR #185 merge : `6ad0e6045ac70a82f367b4eacb18d927ffd1bddf`.
- Current branch `r12/00-postmerge-continuity-normalization` is the single authorized planning continuity normalization and MUST change only this file.
- Its accepted merge makes R12 planning **ACCEPTED + NORMALIZED** and authorizes R12.1.

### Frozen R12 subdivision index

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

## R12 frozen technical boundaries

- Existing R2 Project DNA/Project Wizard/KodeProduct remain authoritative; R12 extends them and creates no parallel Wizard.
- Windows-first phase DoD; one Windows PASS never manufactures Linux/macOS PASS.
- WinUI 3/Windows App SDK, WPF, Avalonia, Qt 6/CMake and Tauri v2 are the five frozen adapter families.
- SQLite is the embedded persistence baseline.
- Toolchains are capability-probed. Kodepoia does not silently install SDKs, workloads, Qt, Rust, WebView2 or signing credentials.
- ProcessSandbox + KillSwitch, Guardian/PermissionSet, SafeChange/Backup/Recovery/Audit, KodeSecrets, R6 governance, R7 ResearchGuard and R8 lineage remain mandatory.
- No shell command strings or model/project raw argv/MSBuild/CMake/Cargo/package scripts/SQL/signing commands are execution surfaces.
- Dependencies are pinned/locked; network off by default. Signing state is explicit and no production certificate is required for phase acceptance.
- CONDITIONAL manual intervention triggers only when an authoritative OS/toolchain/runtime semantic required by a claim cannot be proven by accepted CI. Missing evidence never manufactures PASS.

## Execution rule after planning normalization

Each R12 subdivision : dedicated branch from normalized `main` → focused implementation/tests → exact-head R0/full Python/UI → satisfy triggered CONDITIONAL manual gate if any → final docs/evidence and re-gate if head changes → expected-SHA merge → exactly one continuity-only normalization + same gates + merge → only then next subdivision.

R12.16 uses anti-circular integrated acceptance and only its final normalized closure authorizes R13 planning.

## Next authorized action

Cycle = **R12 planning continuity normalization only**. Gate exact head of `r12/00-postmerge-continuity-normalization`; merge it with `expected_head_sha`. **Only that merge authorizes R12.1.**
