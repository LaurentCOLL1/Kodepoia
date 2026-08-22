# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1/R2/R3/R4/R5 sont COMPLETE. R6 est IN PROGRESS. R6.1 KodeHealth, R6.2 KodeBudget, R6.3 KodeTests + KodeRegression, R6.4 KodeVisualQA et R6.5 KodeAccessibility sont COMPLETE. Le plan exhaustif `docs/roadmap/R6_PLAN.md` est ACCEPTED et fige R6.1–R6.12. R6.6 — KodeLocalization + pseudo-localization foundation est NEXT / NOT STARTED.** R6.5 a été accepté sur le head exact `06fd66af4b3a85da24b98ea2a5fbb2685358c540` après R0 #710, Python Core #684, UI Smoke #651 et le gate Windows réel clavier/focus/Narrator `15 PASS / 0 FAIL / 15`, puis PR #41 a été fusionnée en `db1a1ab78eb2ac7d90f75ab294074dec0238268c`. Lire `R6_PLAN.md`, `R6_STATUS.md`, `R6_5_ACCEPTANCE.md`, `R6_5_DESIGN.md`, `R6_4_ACCEPTANCE.md`, l'architecture gelée et ce fichier avant reprise. Ne pas rouvrir R1–R6.5 sans régression démontrée/ADR, ne pas renuméroter R6 sans mise à jour gouvernée, ne pas commencer R7 avant R6 COMPLETE.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
- Source de vérité fusionnée après implémentation R6.5 : `main` `db1a1ab78eb2ac7d90f75ab294074dec0238268c` avant normalisation post-merge R6.5.
- Branche de normalisation R6.5 : `feature/r6-5-post-merge-normalization`.
- R1 : COMPLETE.
- R2 : COMPLETE.
- R3 : COMPLETE — hardware-local model acceptance passed.
- R4 : COMPLETE — governed KodeCode acceptance passed.
- R5 : COMPLETE — KodeGodot 4.7.x hardware-local acceptance passed.
- R6 : IN PROGRESS.
- R6.1 : COMPLETE — PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.
- R6.2 : COMPLETE — PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`.
- R6.3 : COMPLETE — PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`.
- R6 detailed plan : ACCEPTED — PR #37 merge `0a91064608507966a47921df8fb36e5f25477141`.
- R6 plan post-merge normalization : PR #38 merge `e96e7c3b168975869c911f880044b7ef8e322157`.
- R6.4 : COMPLETE — PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f` — manual `REQUIRED` SATISFIED.
- R6.4 post-merge normalization : PR #40 merge `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`.
- R6.5 : COMPLETE — PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c` — manual `REQUIRED` SATISFIED.
- R6.6 : NEXT / NOT STARTED — manual `NONE`.
- R6.7–R6.12 : PLANNED in `docs/roadmap/R6_PLAN.md`.
- R7–R16 : PENDING.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.
- Nontrivial Git/repository/software-engineering must not route to Granite.

## Permanent architecture/security boundaries

All later work must preserve:

- `WorkspaceBoundary` path confinement and symlink-escape rejection;
- `ProcessSandbox` + global KillSwitch;
- Guardian + `PermissionSet`;
- structured Tool APIs, never arbitrary model-supplied commands;
- SafeChange snapshots before sensitive mutations;
- AuditLog hash-chain evidence;
- secrets redaction and exclusion from LLM context/persistent memory;
- Schema/DataGovernance discipline;
- structured Health/Budget/Test/Regression/VisualQA/Accessibility evidence;
- platform-aware behavior: non-target platforms must not impose requirements/dependencies/inputs/budgets/tests;
- architecture-foundation changes require ADR.

## R5 hardware-local accepted baseline

- Python `3.12.4`;
- Windows 11 build `26220`;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- LSP 6005, DAP 6006, debug 6007;
- AMD Radeon RX 6750 XT observed during real Movie Maker acceptance;
- final hardware-local acceptance: 19 PASS / 0 FAIL / 19, `acceptance_completed=true`;
- benchmark ~101 effective FPS on disposable fixture;
- AVI capture 64,612 bytes;
- governed scene edit with SafeChange snapshot;
- loopback LSP/DAP, DAP thread `Main`;
- Windows release export 109,127,680 bytes;
- valid AuditLog chain.

### R5 anti-regression rules

1. `ProcessSandbox.run()` drains stdout/stderr with `communicate(timeout=...)`; never poll exit before draining PIPEs.
2. Long-lived socket services use the sandboxed background path when stdio is not protocol; no unread PIPEs.
3. Real Godot Movie Maker capture must not be substituted with headless/dummy rendering.
4. TCP connect timeout must not remain protocol-read timeout after connection.
5. DAP launch supports deferred response sequencing through `configurationDone`.
6. Godot services remain loopback-only; model input must not expose arbitrary host/argv/command/program/cwd.

## R6 detailed plan — ACCEPTED

`docs/roadmap/R6_PLAN.md` is the authoritative exhaustive R6 plan. It was reconstructed retroactively by explicit user request because R6.1–R6.3 predated the permanent phase-plan rule.

Planning acceptance evidence:

- accepted planning head `8fbad7c13dd65f9dcd49a03b33a3174fcf28d18a`;
- R0 Repository Guard `32563057993` / #639 — SUCCESS Windows + Ubuntu;
- Python Core `32563057956` / #613 — SUCCESS Windows + Ubuntu, PowerShell validation + integrated KodeStudio smoke;
- KodeStudio UI Smoke `32563057903` / #580 — SUCCESS Windows;
- PR #37 merge `0a91064608507966a47921df8fb36e5f25477141`;
- post-plan normalization PR #38 merge `e96e7c3b168975869c911f880044b7ef8e322157`.

Frozen structure:

1. R6.1 — KodeHealth foundation — COMPLETE — manual `NONE`.
2. R6.2 — KodeBudget foundation — COMPLETE — manual `NONE`.
3. R6.3 — KodeTests + KodeRegression foundation — COMPLETE — manual `NONE`.
4. R6.4 — KodeVisualQA foundation — COMPLETE — manual `REQUIRED` SATISFIED.
5. R6.5 — KodeAccessibility foundation — COMPLETE — manual `REQUIRED` SATISFIED.
6. R6.6 — KodeLocalization + pseudo-localization — NEXT / NOT STARTED — manual `NONE`.
7. R6.7 — KodeTechnicalDebt — PLANNED — manual `NONE`.
8. R6.8 — KodeCI + KodeBuild — PLANNED — manual `CONDITIONAL`.
9. R6.9 — KodeAppSecurity baseline — PLANNED — manual `NONE`.
10. R6.10 — KodePrivacy baseline — PLANNED — manual `NONE`.
11. R6.11 — KodeLicense + KodeBOM — PLANNED — manual `CONDITIONAL`.
12. R6.12 — Major-patch validation + rollback gate and R6 integration acceptance — PLANNED — manual `CONDITIONAL`.

Do not silently add/remove/merge/split/renumber any R6.N. Update plan + continuity in the same work cycle; architecture changes need ADR.

## Accepted R6.1 evidence

- head `802de4ba3110ace657c4e16306a0ca29850ce2bd`;
- PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`;
- 9 focused tests PASS;
- R0 `32561211168`, Python Core `32561211156`, UI Smoke `32561211167` — SUCCESS.

## Accepted R6.2 evidence

- head `8ac3772e98c70260c320519a214bb25b6cedbb38`;
- PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`;
- derivation/evaluation/persistence smoke PASS;
- R0 `32561719921`/#603, Python Core `32561719925`/#577, UI Smoke `32561720008`/#544 — SUCCESS.

## Accepted R6.3 evidence

- head `7150237c263dd3ac96af4662d74909e05f3cf991`;
- PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`;
- baseline/current comparison + persistence smoke PASS;
- R0 `32562032986`/#622, Python Core `32562032998`/#596, UI Smoke `32562032982`/#563 — SUCCESS.

## R6.4 — KodeVisualQA — COMPLETE

Accepted implementation identity:

- base normalized main `e96e7c3b168975869c911f880044b7ef8e322157`;
- accepted head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`;
- PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`;
- post-merge normalization PR #40 merge `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`;
- manual `REQUIRED` SATISFIED.

Hosted evidence:

- R0 #666, Python Core #640, UI Smoke #607 — SUCCESS.

Hardware-local evidence:

- Windows `Windows-11-10.0.26220-SP0`, Python `3.12.4`;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- AMD Radeon RX 6750 XT;
- baseline/current SHA-256 `98dca538d872e8f883b4de4e9b92b741091365f15d193bac1127801277ca567a`;
- VisualQA evidence SHA-256 `4c0375391d8f0e1b54c8c949b264ec70d6c9a18f10798a52a72d79ac18daab56`;
- VisualQA PASS, R6.3 hook PASS, AuditLog PASS;
- `8 PASS / 0 FAIL / 8`, `acceptance_completed=true`.

R6.4 must not be reopened without demonstrated regression or architecture-changing ADR.

## R6.5 — KodeAccessibility — COMPLETE

Accepted implementation identity:

- base normalized main `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`;
- branch `feature/r6-5-accessibility`;
- accepted final head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`;
- PR #41;
- merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`;
- manual `REQUIRED` SATISFIED.

Accepted implementation scope:

- structured accessibility result/report model with `unknown/pass/warn/fail/not_applicable`, severity, applicability reasons, blockers and canonical SHA-256 evidence;
- anti-tamper round-trip/derived-field validation;
- `accessibility-report-v1` schema;
- `.kodepoia/diagnostics/accessibility/` confinement through `WorkspaceBoundary`;
- stable R6.3 accessibility hooks;
- explicit contrast and target-size helpers when source data exists;
- KodeStudio/Project Wizard explicit accessible names/descriptions;
- stable required-control manifests including dynamic budget/requirement controls;
- QAccessible interface/name/role/state audit;
- tab-focus audit for visible enabled registered controls;
- explicit N/A for hidden/disabled adaptive controls;
- blocking detection of named application-owned controls bypassing registration;
- narrow exclusion of Qt-owned `QTabBar` `ScrollLeftButton`/`ScrollRightButton` internals;
- Windows accessibility UI CI;
- source-head/hash-bound 13-item Windows keyboard/focus/Narrator acceptance contract;
- wrong-SHA/incomplete/failing/tampered/out-of-workspace manual evidence cannot produce `acceptance_completed=true`.

Hosted final-head evidence:

- R0 Repository Guard `32567824374` / #710 — SUCCESS Windows + Ubuntu;
- Python Core `32567824373` / #684 — SUCCESS Windows + Ubuntu, PowerShell syntax, full pytest and integrated accessibility UI smoke;
- KodeStudio UI Smoke `32567824370` / #651 — SUCCESS Windows.

Required Windows interactive evidence on the exact same head:

- Windows `Windows-11-10.0.26220-SP0`;
- Python `3.12.4`;
- KodeStudio automated report: 343 applicable PASS, zero failed/warnings/unknown/blockers, SHA-256 `9244424a8addb921822bae80de2d7c1a95733a10f04775dc7ec8b55194041920`;
- Project Wizard automated report: 318 applicable PASS, zero failed/warnings/unknown/blockers, SHA-256 `e824358a8068d871f59fdbcc55092b300b572d34548d76b0c379973002ea2d91`;
- keyboard 5/5 PASS;
- visible/unobscured focus 2/2 PASS;
- Narrator 6/6 PASS;
- manual 13/13 PASS, zero blocking failures;
- integrated `15 PASS / 0 FAIL / 15`;
- `metadata.acceptance_completed=true`;
- evidence `.kodepoia/diagnostics/accessibility/r6-5-local-acceptance.json`.

Initial CI findings/corrections to remember:

1. Symlink escape correctly raises existing `WorkspaceViolation`; the initial R6.5 test expected the wrong exception. Do not weaken `WorkspaceBoundary`.
2. Qt creates internal `QTabBar` controls `ScrollLeftButton` and `ScrollRightButton`; only those identified framework-owned children are excluded. Do not broaden this to arbitrary controls.
3. PySide focus-policy conversion was hardened to avoid eager enum conversion.

The local run emitted `QFontDatabase` missing-font-directory and `propagateSizeHints()` notices; both structured accessibility reports still had zero warnings, zero unknowns and zero blockers. Do not reopen R6.5 from those notices alone. They may become R6.7 technical-debt items if still relevant.

External interpretation:

- WCAG 2.2 source criteria where applicable;
- W3C WCAG2ICT 2.2 guidance for non-Web desktop software;
- Qt QAccessible metadata as structural mechanism;
- Windows Narrator as real assistive-technology acceptance environment;
- no universal WCAG certification claim.

R6.5 must not be reopened without demonstrated regression or architecture-changing ADR.

## Manual-intervention forecast — remaining R6

The user must receive exact commands/actions, expected output, recovery, evidence and do-not-do-yet instructions when each gate is reached.

- **R6.4 REQUIRED:** SATISFIED; no further action unless regression.
- **R6.5 REQUIRED:** SATISFIED; no further action unless regression.
- **R6.8 CONDITIONAL:** local Windows build evidence only if hosted CI cannot authoritatively meet build/reproducibility DoD.
- **R6.11 CONDITIONAL:** provenance/license evidence only if an acceptance-critical component remains unresolved after trusted metadata/source inspection.
- **R6.12 CONDITIONAL:** local integration/user approval only if final selected gates require hardware-local execution or explicit approval.
- R6.6, R6.7, R6.9 and R6.10 currently require no user-side acceptance execution.

## Current external baselines used by R6

- accessibility: WCAG 2.2 source criteria with WCAG2ICT 2.2 guidance for non-Web software where applicable;
- application security: OWASP ASVS 5.0.0 stable baseline for applicable surfaces;
- BOM: SPDX 3.0 stable baseline.

## Permanent phase-start planning rule

Adopted via PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9`. For every newly started major phase from R7 onward:

1. create `docs/roadmap/RX_PLAN.md` before `RX.1`;
2. enumerate every planned `RX.N` with objective/scope/dependencies/implementation/deliverables/acceptance/evidence/rollback/risks;
3. classify each `NONE`, `REQUIRED` or `CONDITIONAL` for manual intervention;
4. pre-document manual reason/prerequisites/commands/actions/expected output/recovery/evidence/do-not-do/privacy/security;
5. planning PR final-head checks must pass and plan merge before implementation;
6. keep plan + continuity synchronized on scope/status/prerequisites/manual gates/important defects;
7. scope renumber/add/remove/merge/split requires rationale and ADR if architecture changes;
8. major phase COMPLETE only when every planned subdivision is COMPLETE or explicitly removed by governed decision.

## Next action

After this R6.5 post-merge normalization branch passes final-head CI and merges, **R6.6 — KodeLocalization + pseudo-localization foundation is the next authorized implementation subdivision, but remains NOT STARTED until explicitly begun.** Follow `R6_PLAN.md`. R6.6 manual classification is `NONE`.

Do not start R7.

## Permanent process rules

- Update active phase plan, status and continuity in the same work cycle whenever subdivision/phase status, PR state, hardware acceptance, prerequisites, manual requirements or important defects change.
- Never mark a phase/subdivision COMPLETE from partial CI or unsupported claims.
- Use exact accepted head/PR/run/merge evidence.
- Preserve frozen architecture unless ADR authorizes a foundation change.
- No manual acceptance by inference from silence, partial logs/screenshots or wrong-environment evidence.
- Never ask for passwords, tokens, private keys or unrelated personal data; require redaction where logs can contain secrets.
