# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 25 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R11 COMPLETE + NORMALIZED. R12 planning ACCEPTED + NORMALIZED. R12.1–R12.16 COMPLETE. R12.16 a pour implementation source accepté `1927d9ab673228101c932b1cb6b89243296ac957`, final evidence head `f12132b777569a6a03171e759dd1b36d3a1858b4`, rapport canonique R12 digest `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`, et PR #217 fusionnée avec expected head sous merge commit `2250d782a65c4aa0d849cc98f7d87e6f3d68c07e`. Le manuel R12.16 est CONDITIONAL / NOT TRIGGERED. Cette branche contient l'unique payload de normalisation continuity-only post-merge ; ce payload ne devient autorité `R12 COMPLETE + NORMALIZED` qu'une fois son exact HEAD validé et sa PR fusionnée dans `main`. Après cette fusion, R13 planning est autorisé.**

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 gelée; normalized `main` after each accepted normalization merge is source of truth.
- R1–R11 : **COMPLETE + NORMALIZED**.
- R12 planning : **ACCEPTED + NORMALIZED**.
- R12.1–R12.16 : **COMPLETE**.
- R12.16 implementation/evidence PR #217 : **MERGED** as `2250d782a65c4aa0d849cc98f7d87e6f3d68c07e`.
- This file is the **single continuity-only R12.16 normalization payload**. On this normalization branch, normalization remains candidate-only until exact-head gates + merge. Once merged to `main`, R12 is **COMPLETE + NORMALIZED**.
- R13 planning : **AUTHORIZED only after this exact normalization payload passes all required gates and merges to `main`**.

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
- PR #216 merged with expected head as normalized `main` `30095003ab5fa61328319be320122ff647ce351a`.
- **R12.15 COMPLETE + NORMALIZED**. This merge is the sole authorized base for R12.16.

## R12.16 closure authority

- Base normalized `main`: `30095003ab5fa61328319be320122ff647ce351a`.
- Dedicated implementation branch: `r12/16-adversarial-integrated-acceptance`; PR #217.
- Start-of-subdivision plan + continuity synchronization: **DONE before implementation**.
- Rejected candidate 1: `64035fc92757e275bdf13eda60d6a47596b22c2e` — Python Core exposed a mismatched expected error-message regex; no failed/stale evidence reused.
- Rejected candidate 2: `af2daa01d4c98c2a6ce7ba48830819f513d8e741` — Integrated Windows acceptance exposed package verification against mutable global staging rather than a dedicated application artifact tree; no failed/stale evidence reused.
- Accepted immutable implementation source: **`1927d9ab673228101c932b1cb6b89243296ac957`**.
- Implementation-source exact-head gates — all SUCCESS: R0 #1590 / `32842609351`; Python Core #1564 / `32842609414`; KodeStudio UI #1531 / `32842609362`; WPF #79 / `32842609356`; WinUI3 #69 / `32842609315`; Avalonia #65 / `32842609365`; Qt6 #60 / `32842609324`; Tauri2 #51 / `32842609391`; Integrated Windows #4 / `32842609416`.
- Manual state: **CONDITIONAL / NOT TRIGGERED** (`conditional_not_triggered`). Hosted Windows CI establishes the frozen Project Wizard -> persisted DNA/Product -> deterministic scaffold -> WPF compile/runtime-test -> isolated package-manifest verification claim. R12 does not claim interactive install, Store publication, production signing or Developer Mode launch semantics.
- Accepted Windows CI artifact: `r12-16-windows-ci-1927d9ab673228101c932b1cb6b89243296ac957`, artifact id `9561095185`, archive digest `sha256:1ca4e2f65f7fa9563598de93c6e0c90a984231554fa6d0d982ff4690baa6a21e`.
- Accepted Windows CI evidence: `source_sha=1927d9ab673228101c932b1cb6b89243296ac957`, `status=pass`, `blockers=[]`, semantic digest `0bbead835c2ee48f4d6a78f11f6aceaca60262eebe70c3944f6475ae82b70a24`, model digest `3feb7493c8fa969e638bb9c4454161edea8d1f36f49f2f93a72a99c3b4ca0da0`, package-manifest digest `4debf90eddd3dca3f3af05c6ab245b06246e6d6eb538bd3b769c575a8a1401e1`, 5 isolated application artifacts.
- End-of-subdivision evidence-input head: `d29ef495810f4470b360e8f1df9fe9184906b3d4`. Integrated Windows #5 / `32843666461` generated and schema-validated the canonical report artifact from the frozen end-sync bytes.
- Canonical integrated report: `docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json`, `status=pass`, `blockers=[]`, `source_sha=1927d9ab673228101c932b1cb6b89243296ac957`, `manual_state=conditional_not_triggered`, semantic digest **`daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`**. It binds R12.1–R12.16 acceptance bytes, end-synchronized continuity, exact Windows CI evidence and canonical R11 semantic digest `ed956be1aa19592b654382a209e5ca99d44d3cbcd67dd3981bdae3d865563170`, without self-binding.
- Final evidence/documentation head: **`f12132b777569a6a03171e759dd1b36d3a1858b4`**.
- Final exact-head gates — all SUCCESS: R0 #1592 / `32843947371`; Python Core #1566 / `32843947324`; KodeStudio UI #1533 / `32843947398`; WPF #81 / `32843947300`; WinUI3 #71 / `32843947275`; Avalonia #67 / `32843947435`; Qt6 #62 / `32843947299`; Tauri2 #53 / `32843947285`; Integrated Windows #6 / `32843947259`.
- Integrated Windows #6 regenerated the report from the final head with the same semantic digest `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`; only `generated_at` changed.
- PR #217 merged with `expected_head_sha=f12132b777569a6a03171e759dd1b36d3a1858b4` as **`2250d782a65c4aa0d849cc98f7d87e6f3d68c07e`**.
- `R12_PLAN.md` already says R12.16 COMPLETE and MUST NOT be changed by post-merge normalization.
- This branch `r12/16-continuity-normalization` is the one and only authorized post-merge continuity normalization. Its diff MUST contain only this file.
- Once this exact normalization head passes R0/full Python/UI + WPF/WinUI/Avalonia/Qt/Tauri/Integrated Windows and is merged with expected SHA, **R12 COMPLETE + NORMALIZED** becomes authoritative on `main` and R13 planning is authorized.

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
| R12.16 | Adversarial hardening + Wizard-to-Windows integrated acceptance | COMPLETE | CONDITIONAL |

## Permanent boundaries

Workspace/R8 Vault boundaries; ProcessSandbox + KillSwitch; Guardian/PermissionSet; SafeChange/Backup/Recovery/Audit; KodeSecrets/redaction; R6 governance/security/privacy/license/build/accessibility/localization; R7 ResearchGuard; R8 lineage/provenance/cache/export; R9 AI resource arbitration; R10 3D authority; R11 media/runtime/privacy/evidence boundaries remain in force. Structured APIs only. Network off by default. Exact-head evidence mandatory. Missing evidence never manufactures PASS.

## Execution rule

Each R phase/subdivision: dedicated branch from normalized `main` -> start status sync -> implementation + focused tests -> exact-head gates -> truthful manual state -> end status sync -> final evidence/re-gates -> merge with `expected_head_sha` -> exactly one continuity-only post-merge normalization + exact-head gates + merge -> only then next phase planning.

A post-merge normalization MUST NOT modify `R12_PLAN.md`, implementation, tests, schemas, workflows, acceptance files, or canonical evidence. It changes continuity only.

## Next authorized action

**This normalization only:** verify the diff from `2250d782a65c4aa0d849cc98f7d87e6f3d68c07e` contains exactly `docs/continuity/KODEPOIA_CONTINUITY.md`; freeze the normalization SHA; require exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + WPF + WinUI3 + Avalonia + Qt6 + Tauri2 + R12 Integrated Windows Acceptance; merge the normalization PR with `expected_head_sha`. After that merge, R12 is **COMPLETE + NORMALIZED** and R13 planning is the next authorized phase action.
