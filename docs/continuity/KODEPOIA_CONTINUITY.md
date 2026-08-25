# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.15 COMPLETE + NORMALIZED. R12.15 final recorded-evidence head `095c8f5eafd67e7c23f7a38700b053ae634b6bc5` passed R0 #1583 / `32837368878`, Python #1557 / `32837368733`, KodeStudio UI #1524 / `32837368999`, WPF #74 / `32837368788`, WinUI #64 / `32837368932`, Avalonia #60 / `32837368735`, Qt #55 / `32837368921`, Tauri #46 / `32837368783`, then PR #215 merged with expected SHA as `bfd957a1f9de5493c927ab50f6875a54ee3f4ed9`. Its single continuity-only normalization head `965d21235171a260f9d97002c585142c5cafd094` passed R0 #1585 / `32837907058`, Python #1559 / `32837906972`, KodeStudio UI #1526 / `32837907051`, WPF #75 / `32837906956`, WinUI #65 / `32837906989`, Avalonia #61 / `32837907001`, Qt #56 / `32837906941`, Tauri #47 / `32837906926`, and PR #216 merged as normalized `main` `30095003ab5fa61328319be320122ff647ce351a`. R12.16 is now the sole active subdivision on `r12/16-adversarial-integrated-acceptance`, created exactly from that normalized base. Start-of-subdivision plan/continuity synchronization sets R12.16 IN_PROGRESS before implementation. Manual state is CONDITIONAL / NOT TRIGGERED at subdivision start; trigger only if a real interactive/runtime/install Windows semantic required by the frozen DoD cannot be established by accepted hosted CI.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.15 : **COMPLETE + NORMALIZED**.
- R12.16 : **IN_PROGRESS**.
- R13 planning : **FORBIDDEN until R12.16 implementation/evidence merge + its single accepted continuity-only normalization merge**.

## Permanent R-phase plan status synchronization rule

For every R phase, the phase plan (for example `docs/roadmap/R12_PLAN.md`) is live execution authority and MUST be updated both **at the beginning** and **at the end** of every subdivision.

- **Subdivision start, before implementation:** update phase-level `Status`, `Complete subdivision index`, and execution checkpoint so all prior normalized subdivisions are `COMPLETE`, the active subdivision is `IN_PROGRESS`, and later subdivisions remain `PLANNED`/`NOT STARTED`; synchronize continuity in the same work cycle.
- **Subdivision end, before final documentation re-gates:** update the same plan fields so the accepted active subdivision is `COMPLETE`; the next subdivision remains `PLANNED` until its own dedicated branch starts; synchronize continuity in the same work cycle.
- A triggered conditional manual gate must set a truthful `BLOCKED`/`MANUAL_REQUIRED` state rather than `COMPLETE`.
- Post-merge normalization is continuity-only and MUST NOT rewrite phase-plan status. The implementation branch carries the end-of-subdivision plan update before merge.
- A stale `Complete subdivision index` or stale phase `Status` is a governance defect and blocks acceptance until corrected.

This rule applies to all future R-phase execution/recovery unless a later accepted governance ADR explicitly changes it.

## R12.14 closure authority

- Base normalized `main`: `63d6548d024fb511ca6172b121c05c9c7f02cf9c`.
- Dedicated implementation branch: `r12/14-packaging-update`; PR #213.
- Manual state: **CONDITIONAL / NOT TRIGGERED**.
- Accepted implementation candidate: `4d1377d74d9a6b5f7d47256288511908957d0adb`.
- Candidate gates: R0 #1568 / `32831015949`; Python #1542 / `32831015974`; UI #1509 / `32831016023`; WPF #61 / `32831016002`; WinUI #51 / `32831016057`; Avalonia #47 / `32831016116`; Qt #42 / `32831016129`; Tauri #33 / `32831015985` — all SUCCESS.
- Final-documentation head: `a1481e5b23e14b029bcf076d0433e866c6d93895`; gates R0 #1571 / `32831671974`; Python #1545 / `32831671907`; UI #1512 / `32831671875`; WPF #64 / `32831671788`; WinUI #54 / `32831671805`; Avalonia #50 / `32831671949`; Qt #45 / `32831671906`; Tauri #36 / `32831671838` — all SUCCESS.
- PR #213 merged as `d1a0d3831f3767d713f3288b5269fcc722bab1eb`.
- Single normalization head `598cd5d257c366609e084b5968c576cbde5cdd86`; gates R0 #1573 / `32832951142`; Python #1547 / `32832950972`; UI #1514 / `32832951226`; WPF #65 / `32832951024`; WinUI #55 / `32832951587`; Avalonia #51 / `32832951938`; Qt #46 / `32832951124`; Tauri #37 / `32832951182` — all SUCCESS.
- PR #214 merged as `089e54cdbd1ac344ce71fc92eef213ad2e9589d3`.
- **R12.14 COMPLETE + NORMALIZED**.

## R12.15 closure authority

- Base normalized `main`: `089e54cdbd1ac344ce71fc92eef213ad2e9589d3`.
- Dedicated implementation branch: `r12/15-cli-kodestudio-desktop`; PR #215.
- Manual state: **NONE**.
- Frozen scope: structured `kodepoia r12` desktop status/scaffold/validate/build/test/package intents; stable JSON/exit semantics; no raw executable/argv/flags/scripts/SQL/signing-key surface; KodeStudio Desktop workspace bound to Project Wizard output and read-only evidence; passive refresh performs no external process; execute actions remain explicit and governed; global KillSwitch cancellation; accessibility/localization/pseudo-localization for new controls.
- Rejected candidate: `696ab04eda402fd77b826ef80c9cc8a98706ad75`; UI Smoke #1516 exposed an accessibility registration defect and stale pseudo-localization navigation cardinality. No failed evidence reused.
- Accepted candidate: `79cda1733bc470f897a5153dcd0c4d059b948900`.
- Candidate gates: R0 #1577 / `32834583380`; Python #1551 / `32834583390`; UI #1518 / `32834583399`; WPF #68 / `32834583424`; WinUI #58 / `32834583419`; Avalonia #54 / `32834583411`; Qt #49 / `32834583377`; Tauri #40 / `32834583375` — all SUCCESS.
- End status synchronization marked R12.15 `COMPLETE` and R12.16 `PLANNED` before documentation re-gates.
- Synchronized documentation head `881ac7e6baee67f594f62377f3a7d1b9aee2ce72`; gates R0 #1580 / `32836806493`; Python #1554 / `32836806644`; UI #1521 / `32836806507`; WPF #71 / `32836806242`; WinUI #61 / `32836806760`; Avalonia #57 / `32836806320`; Qt #52 / `32836806429`; Tauri #43 / `32836806371` — all SUCCESS.
- Final recorded-evidence head `095c8f5eafd67e7c23f7a38700b053ae634b6bc5`; gates R0 #1583 / `32837368878`; Python #1557 / `32837368733`; UI #1524 / `32837368999`; WPF #74 / `32837368788`; WinUI #64 / `32837368932`; Avalonia #60 / `32837368735`; Qt #55 / `32837368921`; Tauri #46 / `32837368783` — all SUCCESS.
- PR #215 merged with expected head as `bfd957a1f9de5493c927ab50f6875a54ee3f4ed9`.
- Single continuity-only normalization head `965d21235171a260f9d97002c585142c5cafd094`; gates R0 #1585 / `32837907058`; Python #1559 / `32837906972`; UI #1526 / `32837907051`; WPF #75 / `32837906956`; WinUI #65 / `32837906989`; Avalonia #61 / `32837907001`; Qt #56 / `32837906941`; Tauri #47 / `32837906926` — all SUCCESS.
- PR #216 merged with expected head as **normalized `main` `30095003ab5fa61328319be320122ff647ce351a`**.
- **R12.15 COMPLETE + NORMALIZED**. This merge is the sole authorized base for R12.16.

## R12.16 execution authority

- Base normalized `main`: `30095003ab5fa61328319be320122ff647ce351a`.
- Dedicated branch: `r12/16-adversarial-integrated-acceptance`, created exactly from that SHA.
- Manual state: **CONDITIONAL / NOT TRIGGERED at subdivision start**.
- Trigger: only if the final frozen Wizard-to-Windows DoD requires an interactive/runtime/install Windows semantic not established by accepted hosted Windows CI. If triggered, freeze one exact candidate SHA and stop before any next phase; provide one bounded local collector with prerequisites, exact commands, expected evidence path, privacy/recovery instructions, and review the evidence before proceeding.
- Start status synchronization: **DONE in this work cycle** — R12.1–R12.15 `COMPLETE`, R12.15 `COMPLETE + NORMALIZED`, R12.16 `IN_PROGRESS` in both `R12_PLAN.md` and continuity before implementation.
- Frozen deliverables: adversarial suite across Project DNA → template → adapter → build/test → SQLite/async/IPC → package/update; canonical `R12_INTEGRATED_ACCEPTANCE.json` schema/model/verifier; anti-circular report creation only after the implementation head independently passes gates; evidence binding R12.1–R12.16 plus prior canonical integrated evidence; canonical Project Wizard Windows desktop fixture scaffolded, compiled and tested with a modern Windows adapter; package artifact validation.
- Runtime launch/install smoke is not automatically part of the claim. It remains conditional; do not manufacture PASS if later required and not CI-provable.
- Required acceptance ordering remains: immutable implementation head with canonical report absent → exact-head R0/full Python/UI (plus relevant desktop adapter regressions) → triggered manual gate if any → freeze implementation SHA/run IDs → generate canonical integrated report → end-of-subdivision plan/continuity update to R12.16 `COMPLETE` → fresh exact-head final documentation/evidence gates → merge with expected head → exactly one continuity-only R12.16 normalization + exact-head gates + merge → only then R12 COMPLETE + NORMALIZED.

## Frozen R12 subdivision index

| ID | Titre | Status | Manuel |
| --- | --- | --- | --- |
| R12.1 | Desktop contracts, identities, capability model + secure toolchain boundaries | COMPLETE | NONE |
| R12.2 | Project DNA/KodeProduct desktop profiles + Project Wizard target selection | COMPLETE | NONE |
| R12.3 | Deterministic desktop scaffold/template/workspace manifest engine | COMPLETE | NONE |
| R12.4 | Framework-neutral MVVM/state/navigation/command/service contracts | COMPLETE | NONE |
| R12.5 | WPF/.NET desktop adapter + build/test bridge | COMPLETE | CONDITIONAL |
| R12.6 | WinUI 3/Windows App SDK adapter + Windows identity/deployment bridge | COMPLETE | CONDITIONAL |
| R12.7 | Avalonia cross-platform desktop adapter | COMPLETE | CONDITIONAL |
| R12.8 | Qt 6/CMake desktop adapter | COMPLETE | CONDITIONAL |
| R12.9 | Tauri v2/Rust/WebView2 desktop adapter | COMPLETE | CONDITIONAL |
| R12.10 | SQLite persistence, schema migrations, transactions + backup/recovery | COMPLETE | NONE |
| R12.11 | Async/concurrency, cancellation, progress + UI-thread lifecycle safety | COMPLETE | NONE |
| R12.12 | Local IPC contracts, framing, authorization + lifecycle isolation | COMPLETE | CONDITIONAL |
| R12.13 | Accessibility, localization, theming, keyboard/focus + DPI/scaling QA | COMPLETE | CONDITIONAL |
| R12.14 | Packaging/install/update/signing-state + rollback model | COMPLETE | CONDITIONAL |
| R12.15 | CLI + KodeStudio Desktop workspace and governed Wizard workflow | COMPLETE | NONE |
| R12.16 | Adversarial hardening + Wizard-to-Windows integrated acceptance | IN_PROGRESS | CONDITIONAL |

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → **start-of-subdivision plan + continuity status synchronization** → implementation + focused tests → exact-head standard + subdivision-specific gates → satisfy triggered manual state → **end-of-subdivision plan + continuity status synchronization** → evidence/re-gate if bytes change → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + exact-head gates + merge → only then next subdivision/phase.

If any CONDITIONAL manual gate triggers, stop before R13 planning and provide exact bounded user commands, prerequisites, expected evidence path and recovery/privacy instructions.

## Next authorized action

**R12.16 implementation only:** inspect and reuse the accepted R11 anti-circular integrated-acceptance pattern; implement R12.16 adversarial verifier/schema/tests and canonical Wizard-to-Windows CI acceptance while keeping `R12_INTEGRATED_ACCEPTANCE.json` absent from the first immutable implementation candidate. Freeze that candidate and require exact-head gates before any canonical PASS report is created. R13 planning remains forbidden.
