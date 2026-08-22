# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1/R2/R3/R4/R5 sont COMPLETE. R6 est IN PROGRESS. R6.1 KodeHealth, R6.2 KodeBudget, R6.3 KodeTests + KodeRegression et R6.4 KodeVisualQA sont COMPLETE. Le plan exhaustif `docs/roadmap/R6_PLAN.md` est ACCEPTED et fige R6.1–R6.12. R6.5 — KodeAccessibility foundation est IN PROGRESS sur `feature/r6-5-accessibility`, PR #41, depuis le main normalisé `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`.** R6.5 implémente le modèle de preuve accessibilité, le schéma/report anti-tamper, la persistance WorkspaceBoundary, le hook R6.3, les contrôles Qt `QAccessible`, les métadonnées accessibles KodeStudio/Project Wizard, l'audit clavier et un gate manuel Windows clavier/focus/Narrator de 13 contrôles. La PR #41 NE DOIT PAS être fusionnée et R6.6 NE DOIT PAS commencer avant CI verte sur le head final ET acceptation interactive Windows réelle sur ce même SHA. Lire `R6_PLAN.md`, `R6_STATUS.md`, `R6_5_DESIGN.md`, `R6_5_ACCEPTANCE.md`, `R6_4_ACCEPTANCE.md`, l'architecture gelée et ce fichier avant reprise. Ne pas rouvrir R1–R6.4 sans régression démontrée/ADR, ne pas renuméroter R6 sans mise à jour gouvernée, et ne pas passer à R7 avant R6 COMPLETE.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
- Source de vérité fusionnée au démarrage R6.5 : normalized `main` `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`.
- Branche active R6.5 : `feature/r6-5-accessibility`.
- PR active R6.5 : #41 — DO NOT MERGE until final-head CI + REQUIRED local acceptance.
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
- R6.5 : IN PROGRESS — PR #41 — manual `REQUIRED`, final implementation head not yet frozen.
- R6.6–R6.12 : PLANNED in `docs/roadmap/R6_PLAN.md`.
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
- R0 Repository Guard run `32563057993` / #639 — SUCCESS Windows + Ubuntu;
- Python Core run `32563057956` / #613 — SUCCESS Windows + Ubuntu, PowerShell validation + integrated KodeStudio smoke;
- KodeStudio UI Smoke run `32563057903` / #580 — SUCCESS Windows;
- PR #37 merge `0a91064608507966a47921df8fb36e5f25477141`;
- post-plan normalization PR #38 merge `e96e7c3b168975869c911f880044b7ef8e322157`.

The plan freezes this structure:

1. R6.1 — KodeHealth foundation — COMPLETE — manual `NONE`.
2. R6.2 — KodeBudget foundation — COMPLETE — manual `NONE`.
3. R6.3 — KodeTests + KodeRegression foundation — COMPLETE — manual `NONE`.
4. R6.4 — KodeVisualQA foundation — COMPLETE — manual `REQUIRED` SATISFIED.
5. R6.5 — KodeAccessibility foundation — IN PROGRESS — manual `REQUIRED`.
6. R6.6 — KodeLocalization + pseudo-localization — PLANNED — manual `NONE`.
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

- base normalized `main`: `e96e7c3b168975869c911f880044b7ef8e322157`;
- branch: `feature/r6-4-visualqa`;
- PR: #39;
- accepted final implementation head: `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`;
- merge: `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`;
- post-merge normalization: PR #40 merge `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`;
- manual classification: `REQUIRED` — SATISFIED.

Accepted hosted evidence on the exact final head:

- R0 Repository Guard run `32564304755` / #666 — SUCCESS Windows + Ubuntu;
- Python Core run `32564304757` / #640 — SUCCESS Windows + Ubuntu, PowerShell validation, pytest and integrated KodeStudio smoke;
- KodeStudio UI Smoke run `32564304798` / #607 — SUCCESS Windows.

Accepted hardware-local evidence on that same head:

- Windows `Windows-11-10.0.26220-SP0`;
- Python `3.12.4`;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- rendering method `gl_compatibility`;
- rendering driver `opengl3`;
- video adapter `AMD Radeon RX 6750 XT`;
- baseline/current SHA-256 `98dca538d872e8f883b4de4e9b92b741091365f15d193bac1127801277ca567a`;
- changed ratio `0.0`;
- perceptual distance ratio `0.0`;
- policy SHA-256 `a2dbb4532c50e522639a1b1a264420d2f491d17e7b2350d500ddf415bd70014e`;
- evidence SHA-256 `4c0375391d8f0e1b54c8c949b264ec70d6c9a18f10798a52a72d79ac18daab56`;
- VisualQA PASS;
- R6.3 hook `visual:godot-real-render` PASS;
- AuditLog PASS;
- `8 PASS / 0 FAIL / 8`, `acceptance_completed=true`.

Accepted implementation scope:

- deterministic engine-neutral `KodeVisualQA`;
- immutable content-addressed baseline approval and SHA-256 provenance;
- exact-file identity, pixel statistics, normalized mean error and deterministic dHash perceptual evidence;
- masks declared by policy and included in canonical policy hashing;
- explicit UNKNOWN for missing evidence and FAIL for incompatible format/mode/resolution;
- PNG diff artifacts and validated anti-tamper `visual-report-v1` evidence;
- stable R6.3 `visual:<case-id>` adapter;
- `.kodepoia/visual_tests/{baselines,runs,diffs}` confinement through `WorkspaceBoundary`;
- Pillow `>=12.3,<12.4` dependency control;
- separate governed `kodegodot_capture_png_sequence` real-render path with fixed output root and no arbitrary executable/argv/command/cwd/host/output-path input;
- accepted R5 `kodegodot_capture_movie` AVI behavior preserved;
- real-render acceptance rejects empty/dummy/headless renderer evidence.

R6.4 must not be reopened without a demonstrated regression or architecture-changing ADR.

## R6.5 — KodeAccessibility — IN PROGRESS

Implementation identity/state:

- base normalized `main`: `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`;
- branch: `feature/r6-5-accessibility`;
- PR: #41;
- final implementation head: **NOT YET FROZEN**;
- manual classification: `REQUIRED` — PENDING after final-head CI.

Current implementation scope:

- `src/kodepoia/quality/accessibility.py`: stable result/report model with `unknown/pass/warn/fail/not_applicable`, severity, applicability reason, blockers, deterministic aggregate state, canonical evidence SHA-256, anti-tamper round-trip and R6.3 adapter;
- `schemas/accessibility-report-v1.schema.json`;
- `AccessibilityStore` confined to `.kodepoia/diagnostics/accessibility/` through `WorkspaceBoundary`;
- explicit sRGB contrast helper and explicit direct-rectangle target-size helper, without inventing rendered values or ignoring standards exceptions;
- `src/kodepoia/kodestudio/accessibility.py`: stable KodeStudio control registry/audit with explicit Qt accessible names/descriptions, tab-focus rules and `QAccessibleInterface` name/role/state evidence;
- KodeStudio main and Project Wizard accessibility metadata, including dynamic performance-budget and requirement-priority controls;
- hidden/disabled adaptive controls are `not_applicable` for keyboard focus with a reason, never a false PASS;
- named application-owned interactive controls that bypass registration create blocking failures;
- identified Qt-owned `QTabBar` internal scroll buttons are excluded narrowly from application-control discovery;
- `tests/test_r6_5_accessibility.py` core evidence/schema/confinement tests;
- `tests/test_r6_5_accessibility_ui.py` Windows Qt/QAccessible/keyboard-focus tests;
- `src/kodepoia/quality/accessibility_acceptance.py` + `scripts/r6_5_accept_local.ps1`: source-head-bound real Windows acceptance with two automated surface reports plus 13 manual keyboard/focus/Narrator checks;
- manual manifest/responses/final summary confined under `.kodepoia/diagnostics/accessibility/`;
- `.github/workflows/python-core.yml` and `.github/workflows/ui-smoke.yml` include R6.5 UI tests; Windows PowerShell parser also covers R6.4/R6.5 acceptance scripts;
- `docs/roadmap/R6_5_DESIGN.md` and `R6_5_ACCEPTANCE.md` define architecture boundary, manual gate, failure recovery and completion criteria.

External accessibility interpretation for R6.5:

- WCAG 2.2 remains the source criteria baseline where applicable;
- W3C WCAG2ICT 2.2 is the preferred interpretation guidance for non-Web desktop software;
- Qt `QAccessibleInterface`/widget accessibility metadata is the structural implementation mechanism;
- Windows Narrator is the required real screen-reader acceptance environment;
- this is not a universal WCAG certification claim.

Initial CI findings/corrections that must be remembered:

1. Ubuntu showed that symlink escape correctly raises existing `WorkspaceViolation`; the initial R6.5 test incorrectly expected `ValueError`. The test was corrected. Do not weaken `WorkspaceBoundary`.
2. Windows UI CI showed Qt creates internal tab-scroll controls `ScrollLeftButton` and `ScrollRightButton`; the discovery rule now excludes only those known Qt-owned implementation children. Do not broaden this to arbitrary controls.
3. PySide focus-policy conversion was hardened to avoid eager `int()` evaluation of enum wrappers.

Required manual acceptance, after exact final-head hosted CI is green:

- five keyboard checks;
- two focus checks (`visible`, `not_obscured`);
- six Narrator checks;
- all 13 manual checks blocking;
- two automated KodeStudio/Project Wizard reports must also PASS with zero blockers;
- successful integrated local result must be `15 PASS / 0 FAIL / 15` and `metadata.acceptance_completed=true`.

Narrator commands recorded by the runner:

- `Win+Ctrl+Enter` toggles Narrator;
- `Narrator+Alt+X` opens Speech Recap/live transcription.

Safety rule: the Narrator test may focus `STOP ALL PROTECTED PROCESSES` but must **not activate the KillSwitch**.

R6.5 must not merge or become COMPLETE before final-head hosted CI + required local evidence are both reviewed on the same final SHA. Do not start R6.6 earlier.

## Manual-intervention forecast — remaining R6

The user must receive exact commands/actions, expected output, recovery, evidence and do-not-do-yet instructions when each gate is reached.

- **R6.4 REQUIRED:** SATISFIED; no further action unless a regression is demonstrated.
- **R6.5 REQUIRED:** real interactive Windows keyboard-only + visible/unobscured focus + Narrator accessibility checklist after final-head CI. Expected successful integrated local result: 15/15 PASS.
- **R6.8 CONDITIONAL:** local Windows build evidence only if hosted CI cannot authoritatively meet the build/reproducibility DoD.
- **R6.11 CONDITIONAL:** provenance/license evidence only if an acceptance-critical component remains unresolved after trusted metadata/source inspection.
- **R6.12 CONDITIONAL:** local integration/user approval only if final selected gates require hardware-local execution or explicit approval.
- R6.6, R6.7, R6.9 and R6.10 currently require no user-side acceptance execution.

The exact planned procedures are in `R6_PLAN.md`. Before requesting manual execution, replace user-facing placeholders with the exact final implementation head and verify the implementation-specific script/commands exist.

## Current external baselines used by the R6 plan

- accessibility: W3C WCAG 2.2 source criteria, with WCAG2ICT 2.2 guidance for non-Web software where applicable;
- application security: OWASP ASVS 5.0.0 current stable baseline, only for applicable surfaces;
- BOM: SPDX 3.0 current stable baseline; SPDX 3.1 RC1 is not an authoritative stable R6 baseline.

## Permanent phase-start planning rule

Adopted via PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9`. For every newly started major phase from R7 onward:

1. create `docs/roadmap/RX_PLAN.md` from `PHASE_PLAN_TEMPLATE.md` before `RX.1`;
2. enumerate every planned `RX.N` with detailed objective/scope/dependencies/implementation/deliverables/acceptance/evidence/rollback/risks;
3. classify each `NONE`, `REQUIRED` or `CONDITIONAL` for manual intervention;
4. for REQUIRED/CONDITIONAL, pre-document reason, prerequisites, exact commands/actions, expected output, recovery, evidence, do-not-do-yet and privacy/security requirements;
5. planning PR final-head checks must pass and plan must merge before implementation starts;
6. keep plan + continuity synchronized on scope/status/prerequisites/manual gates/important defects;
7. scope renumber/add/remove/merge/split requires explicit rationale and ADR if architecture changes;
8. major phase COMPLETE only when every planned subdivision is COMPLETE or explicitly removed by governed decision.

## Next action

Continue only **R6.5 PR #41** until its exact final implementation head is CI-green. Then give the user the exact final SHA and commands from `R6_5_ACCEPTANCE.md` for the REQUIRED Windows keyboard/focus/Narrator acceptance. Do not merge PR #41 before that local evidence is reviewed. Do not start R6.6 and do not start R7.

## Permanent process rules

- Update the active phase plan, status and continuity in the same work cycle whenever subdivision/phase status, PR state, hardware acceptance, prerequisites, manual requirements or important defects change.
- Never mark phase/subdivision COMPLETE from partial CI or unsupported claims.
- Use exact accepted head/PR/run/merge evidence.
- Preserve frozen architecture unless ADR authorizes a foundation change.
- No manual acceptance by inference from silence, partial logs/screenshots or wrong-environment evidence.
- Never ask for passwords, tokens, private keys or unrelated personal data; require redaction where logs can contain secrets.
