# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.14 COMPLETE + NORMALIZED. R12.14 implementation PR #213 final documentation head `a1481e5b23e14b029bcf076d0433e866c6d93895` passed all required exact-head gates and merged with expected SHA as `d1a0d3831f3767d713f3288b5269fcc722bab1eb`; its single continuity-only normalization PR #214 exact head `598cd5d257c366609e084b5968c576cbde5cdd86` passed R0/Python/UI plus all five desktop adapter regressions and merged as `089e54cdbd1ac344ce71fc92eef213ad2e9589d3`. Manual R12.14 CONDITIONAL was NOT TRIGGERED. R12.15 implementation is accepted on candidate `79cda1733bc470f897a5153dcd0c4d059b948900`: R0 #1577, Python #1551, KodeStudio UI #1518, WPF #68, WinUI #58, Avalonia #54, Qt #49 and Tauri #40 all SUCCESS. The earlier candidate `696ab04eda402fd77b826ef80c9cc8a98706ad75` is rejected and its failed UI evidence is not reusable. End-of-subdivision plan/continuity synchronization marks R12.15 COMPLETE while R12.16 remains PLANNED. Synchronized documentation head `881ac7e6baee67f594f62377f3a7d1b9aee2ce72` passed R0 #1580, Python #1554, KodeStudio UI #1521, WPF #71, WinUI #61, Avalonia #57, Qt #52 and Tauri #43. Recording that evidence changed bytes, so one fresh exact-head cycle on the resulting recorded-evidence documentation head is mandatory before merge. R12.16 remains forbidden until PR #215 is merged and exactly one continuity-only R12.15 normalization is gated and merged.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.14 : **COMPLETE + NORMALIZED**.
- R12.15 : **COMPLETE / RECORDED-EVIDENCE FINAL GATES PENDING**.
- R12.16 : **PLANNED / NOT STARTED**.

## Permanent R-phase plan status synchronization rule

For every R phase, the phase plan (for example `docs/roadmap/R12_PLAN.md`) is live execution authority and MUST be updated both **at the beginning** and **at the end** of every subdivision.

- **Subdivision start, before implementation:** update phase-level `Status`, `Complete subdivision index`, and execution checkpoint so all prior normalized subdivisions are `COMPLETE`, the active subdivision is `IN_PROGRESS`, and later subdivisions remain `PLANNED`/`NOT STARTED`; synchronize continuity in the same work cycle.
- **Subdivision end, before final documentation re-gates:** update the same plan fields so the accepted active subdivision is `COMPLETE`; the next subdivision remains `PLANNED` until its own dedicated branch starts; synchronize continuity in the same work cycle.
- A triggered conditional manual gate must set a truthful `BLOCKED`/`MANUAL_REQUIRED` state rather than `COMPLETE`.
- Post-merge normalization is continuity-only and MUST NOT rewrite phase-plan status. The implementation branch carries the end-of-subdivision plan update before merge.
- A stale `Complete subdivision index` or stale phase `Status` is a governance defect and blocks acceptance until corrected.

This rule applies to R12.14–R12.16 and all future R-phase execution/recovery unless a later accepted governance ADR explicitly changes it.

## R12.14 closure authority

- Base normalized `main`: `63d6548d024fb511ca6172b121c05c9c7f02cf9c`.
- Dedicated implementation branch: `r12/14-packaging-update`; PR #213.
- Manual state: **CONDITIONAL / NOT TRIGGERED**.
- Accepted implementation candidate: `4d1377d74d9a6b5f7d47256288511908957d0adb`.
- Candidate gates: R0 #1568 / `32831015949`; Python #1542 / `32831015974`; UI #1509 / `32831016023`; WPF #61 / `32831016002`; WinUI #51 / `32831016057`; Avalonia #47 / `32831016116`; Qt #42 / `32831016129`; Tauri #33 / `32831015985` — all SUCCESS.
- Full Python Core passed `tests/test_desktop_r12_14.py` on hosted Linux and Windows; package-build evidence also succeeded on both OSes.
- Start status synchronization: R12.1–R12.13 `COMPLETE`, R12.14 `IN_PROGRESS`, R12.15–R12.16 `PLANNED`.
- End status synchronization before final documentation gates: `R12_PLAN.md` marks R12.14 `COMPLETE`; R12.15–R12.16 remain `PLANNED`; continuity matched that state.
- Accepted final-documentation head: `a1481e5b23e14b029bcf076d0433e866c6d93895`.
- Final-documentation exact-head gates: R0 #1571 / `32831671974`; Python #1545 / `32831671907`; UI #1512 / `32831671875`; WPF #64 / `32831671788`; WinUI #54 / `32831671805`; Avalonia #50 / `32831671949`; Qt #45 / `32831671906`; Tauri #36 / `32831671838` — all SUCCESS.
- PR #213 merged with `expected_head_sha=a1481e5b23e14b029bcf076d0433e866c6d93895` as merge commit `d1a0d3831f3767d713f3288b5269fcc722bab1eb`.
- Single continuity-only normalization branch `r12/14-postmerge-continuity-normalization`; PR #214; exact head `598cd5d257c366609e084b5968c576cbde5cdd86`.
- Normalization gates: R0 #1573 / `32832951142`; Python #1547 / `32832950972`; UI #1514 / `32832951226`; WPF #65 / `32832951024`; WinUI #55 / `32832951587`; Avalonia #51 / `32832951938`; Qt #46 / `32832951124`; Tauri #37 / `32832951182` — all SUCCESS.
- PR #214 merged with expected head as `089e54cdbd1ac344ce71fc92eef213ad2e9589d3`.
- **R12.14 COMPLETE + NORMALIZED**. This merge is the sole authorized base for R12.15.

## R12.15 execution authority

- Base normalized `main`: `089e54cdbd1ac344ce71fc92eef213ad2e9589d3`.
- Dedicated branch: `r12/15-cli-kodestudio-desktop`; PR #215.
- Manual state: **NONE**.
- Frozen scope: structured `kodepoia r12` desktop status/scaffold/validate/build/test/package intents; stable JSON/exit semantics; no raw executable/argv/flags/scripts/SQL/signing-key surface; KodeStudio Desktop workspace bound to Project Wizard output and read-only evidence; passive refresh performs no external process; execute actions remain explicit and governed; global KillSwitch cancellation; accessibility/localization/pseudo-localization for new controls.
- Start status synchronization was performed before implementation: R12.1–R12.14 `COMPLETE`, R12.15 `IN_PROGRESS`, R12.16 `PLANNED`.
- First implementation candidate `696ab04eda402fd77b826ef80c9cc8a98706ad75` was rejected: KodeStudio UI Smoke #1516 found `r12Evidence` not registered in the accessibility contract and the pseudo-localization navigation test still fixed the main section count at 10 instead of 11. The candidate is not accepted and none of its failed UI evidence may be reused.
- Accepted corrected implementation candidate: `79cda1733bc470f897a5153dcd0c4d059b948900`.
- Candidate exact-head gates: R0 #1577 / `32834583380`; Python #1551 / `32834583390`; KodeStudio UI #1518 / `32834583399`; WPF #68 / `32834583424`; WinUI #58 / `32834583419`; Avalonia #54 / `32834583411`; Qt #49 / `32834583377`; Tauri #40 / `32834583375` — all SUCCESS.
- Full Python candidate proof includes Linux and Windows tests, Linux and Windows package-build evidence, and the internal KodeStudio Windows smoke — all SUCCESS.
- End status synchronization was performed: `R12_PLAN.md` marks R12.15 `COMPLETE`; R12.16 remains `PLANNED`; continuity matches that state.
- Synchronized documentation head: `881ac7e6baee67f594f62377f3a7d1b9aee2ce72`.
- Synchronized-documentation exact-head gates: R0 #1580 / `32836806493`; Python #1554 / `32836806644`; KodeStudio UI #1521 / `32836806507`; WPF #71 / `32836806242`; WinUI #61 / `32836806760`; Avalonia #57 / `32836806320`; Qt #52 / `32836806429`; Tauri #43 / `32836806371` — all SUCCESS.
- Recording the synchronized-documentation evidence changed bytes; the resulting recorded-evidence documentation head must pass a fresh exact-head cycle before merge.
- Final recorded-evidence documentation gates: **PENDING**.
- Implementation merge: **PENDING**.
- Single continuity-only post-merge normalization: **PENDING**.
- R12.16 remains forbidden until the implementation merge and normalization merge are both accepted.

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
| R12.16 | Adversarial hardening + Wizard-to-Windows integrated acceptance | PLANNED | CONDITIONAL |

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R12 subdivision: dedicated branch from normalized `main` → **start-of-subdivision plan + continuity status synchronization** → implementation + focused tests → exact-head standard + subdivision-specific gates → satisfy triggered manual state → **end-of-subdivision plan + continuity status synchronization** → evidence/re-gate if bytes change → merge with `expected_head_sha` → exactly one continuity-only post-merge normalization + exact-head gates + merge → only then next subdivision.

If any CONDITIONAL manual gate triggers, stop before the next subdivision and provide exact bounded user commands, prerequisites, expected evidence path and recovery/privacy instructions.

## Next authorized action

**R12.15 recorded-evidence closure only:** freeze the current PR #215 head after acceptance/continuity evidence recording, require a fresh exact-head R0/full Python/KodeStudio UI plus WPF/WinUI/Avalonia/Qt/Tauri cycle, merge #215 with that exact expected head only if all eight are SUCCESS, then create exactly one continuity-only R12.15 normalization branch/PR from the merge, gate and merge it. R12.16 remains forbidden until that normalization merge is authoritative.
