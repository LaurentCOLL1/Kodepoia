# Kodepoia — R6 detailed phase plan

**Phase:** R6  
**Roadmap title:** Quality / Health / Budget / CI  
**Status:** IN PROGRESS — PLAN ACCEPTED  
**Phase started:** 2026-08-22  
**Plan reconstructed:** 2026-08-22 by explicit user request, after R6.1–R6.3 had already been accepted  
**Plan accepted:** 2026-08-22  
**Accepted planning head:** `8fbad7c13dd65f9dcd49a03b33a3174fcf28d18a`  
**Planning PR:** #37  
**Planning merge:** `0a91064608507966a47921df8fb36e5f25477141`  
**Architecture:** v1.0 frozen  
**Source of truth:** normalized `main`

## Purpose and authority

This is the exhaustive recovery and execution plan for R6. It is a retroactive exception to the normal phase-start planning rule because R6.1–R6.3 were already complete when the permanent `RX_PLAN.md` rule was introduced. The user explicitly requested that R6 be brought under the same discipline before R6.4.

The plan is accepted and merged. It:

1. records completed R6 subdivisions without reopening or redefining them;
2. freezes the R6.1–R6.12 subdivision structure;
3. defines acceptance, rollback and manual-intervention contracts for every subdivision;
4. remains authoritative together with `R6_STATUS.md`, subdivision acceptance documents and `KODEPOIA_CONTINUITY.md`.

R6 may not be marked COMPLETE until every subdivision listed here is COMPLETE with required evidence, or a later recorded roadmap/architecture decision explicitly removes a subdivision from scope.

## Planning acceptance evidence

The plan itself passed the normal repository acceptance discipline before R6.4 was authorized:

- accepted planning head `8fbad7c13dd65f9dcd49a03b33a3174fcf28d18a`;
- R0 Repository Guard `32563057993` / #639 — SUCCESS Windows + Ubuntu;
- Python Core `32563057956` / #613 — SUCCESS Windows + Ubuntu, PowerShell syntax validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32563057903` / #580 — SUCCESS Windows;
- PR #37 merged as `0a91064608507966a47921df8fb36e5f25477141`;
- post-plan normalization PR #38 merged as `e96e7c3b168975869c911f880044b7ef8e322157`.

**Planning gate result: PASS. R6.1–R6.4 are COMPLETE. R6.5 is IN PROGRESS on PR #41; its REQUIRED Windows keyboard/focus/Narrator gate remains pending until final-head CI is green.**

## Frozen-roadmap objective

R6 must establish the quality, health, budget and CI foundations required by the frozen roadmap:

- Health;
- Budget;
- Tests;
- Regression;
- VisualQA;
- Accessibility;
- Localization;
- TechnicalDebt;
- CI/Build;
- AppSecurity baseline;
- Privacy baseline;
- License/BOM;
- validation and rollback for every major patch.

The frozen architecture requires the quality layer to remain connected to the protected execution cycle: request → plan/context → Guardian → snapshot when required → governed executor → Tests/Verifier → Health/Budget/Regression → commit or correction. R6 must never create a direct model-to-shell path, unrestricted host path, arbitrary process invocation or governance bypass.

## Explicitly out of scope for R6

The architecture contains additional quality components such as KodeAudioQA, KodeDeviceLab, KodeAssetDoctor, KodeTextureOptimizer, KodeLOD and KodeShaderProfiler. They are not named in the frozen R6 roadmap and are not silently imported into this phase. They remain for later roadmap phases or the subsystem phases that naturally own them.

Also out of R6: store publishing/signing, Android/iOS device certification, full desktop-app generation, ComfyUI, Blender, audio/voice production, backend/live-ops implementation, release channels and updater implementation beyond the rollback contract required by R6.12.

## Phase-wide architecture and governance boundaries

Every R6 subdivision must preserve:

- `WorkspaceBoundary` for project-path confinement and symlink-escape rejection;
- `ProcessSandbox` plus the global KillSwitch for process execution;
- Guardian and `PermissionSet` for authorization/risk control;
- structured Tool APIs rather than arbitrary model-supplied commands;
- SafeChange snapshots before sensitive mutation;
- AuditLog hash-chain evidence for governed sensitive operations;
- Secrets redaction and exclusion from LLM context/persistent memory;
- schema versioning and DataGovernance;
- platform-aware behavior: a non-target platform must not impose requirements, dependencies, inputs, budgets or tests;
- local-first/offline-capable operation for already configured projects;
- ADR requirement for any foundation-level architecture change;
- no completion from partial CI, missing evidence, silence or evidence from the wrong environment.

All persistent R6 evidence belongs under the initialized `.kodepoia/` tree and must be resolved through `WorkspaceBoundary`. Existing reserved roots include `health/`, `budgets/`, `tests/`, `visual_tests/`, `licenses/`, `bom/`, `workflows/`, `diagnostics/` and `releases/`.

## Current external-reference baselines

External references inform applicable checks but never override the frozen architecture or create requirements for irrelevant platforms:

- **Accessibility:** W3C WCAG 2.2 remains the source-criteria baseline. W3C WCAG2ICT 2.2 is the preferred guidance for applying applicable WCAG criteria to KodeStudio as non-Web desktop software. R6.5 must not claim universal WCAG certification.
- **Application security:** OWASP ASVS 5.0.0, current stable ASVS baseline, used only for applicable web/API/auth/session/security surfaces.
- **Software BOM:** SPDX 3.0, current stable SPDX baseline. SPDX 3.1 RC1 is pre-release/testing material and is not authoritative for stable R6 acceptance unless a later recorded decision updates the plan after a stable release.

If implementation occurs substantially later, any externally versioned requirement that materially affects acceptance must be rechecked before coding and the plan updated if necessary.

## Complete subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R6.1 | KodeHealth foundation | COMPLETE | NONE | R5 COMPLETE |
| R6.2 | KodeBudget foundation | COMPLETE | NONE | R6.1 |
| R6.3 | KodeTests + KodeRegression foundation | COMPLETE | NONE | R6.1–R6.2 |
| R6.4 | KodeVisualQA foundation | COMPLETE | REQUIRED — SATISFIED | R6.1–R6.3 + accepted R5 Godot automation |
| R6.5 | KodeAccessibility foundation | IN PROGRESS | REQUIRED | R6.3–R6.4 |
| R6.6 | KodeLocalization + pseudo-localization foundation | PLANNED | NONE | R6.3 + R6.5 |
| R6.7 | KodeTechnicalDebt foundation | PLANNED | NONE | R6.1–R6.6 |
| R6.8 | KodeCI + KodeBuild foundation | PLANNED | CONDITIONAL | R6.1–R6.7 |
| R6.9 | KodeAppSecurity baseline | PLANNED | NONE | R6.3 + R6.7–R6.8 |
| R6.10 | KodePrivacy baseline | PLANNED | NONE | R6.7–R6.9 |
| R6.11 | KodeLicense + KodeBOM foundation | PLANNED | CONDITIONAL | R6.7–R6.10 |
| R6.12 | Major-patch validation + rollback gate and R6 integration acceptance | PLANNED | CONDITIONAL | R6.1–R6.11 |

No subdivision may be silently added, removed, merged, split or renumbered. Any scope change updates this plan and continuity in the same work cycle; architecture-changing scope requires an ADR before implementation.

---

# R6.1 — KodeHealth foundation — COMPLETE

## Objective and accepted scope

R6.1 established the structured KodeHealth contract: all 14 architecture health dimensions, explicit `unknown/pass/warn/fail`, deterministic score and coverage, blocking failures, exhaustive report validation and project-confined persistence.

Accepted artifacts/behavior:

- `src/kodepoia/quality/health.py`;
- `schemas/health-report-v1.schema.json`;
- `tests/test_r6_1_health.py`;
- `.kodepoia/health/` through `WorkspaceBoundary`;
- atomic `latest.json` plus timestamped snapshots;
- rejection of `.kodepoia` symlink escape;
- consistency checks for serialized `blockers` and `unknown_dimensions`.

## Acceptance record

- accepted implementation head `802de4ba3110ace657c4e16306a0ca29850ce2bd`;
- PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`;
- isolated hardened focused tests: 9 PASS;
- R0 `32561211168` — SUCCESS Windows + Ubuntu;
- Python Core `32561211156` — SUCCESS Windows + Ubuntu;
- KodeStudio UI Smoke `32561211167` — SUCCESS Windows.

## Manual intervention

**NONE.** R6.1 was authoritatively accepted without user-side execution.

## Regression protection

Later integrations may produce Health observations but must not weaken the exhaustive dimensions, explicit unknown coverage, validation integrity or `WorkspaceBoundary` confinement.

---

# R6.2 — KodeBudget foundation — COMPLETE

## Objective and accepted scope

R6.2 established per-platform budget contracts without changing Project DNA. It covers FPS/frame time, CPU/GPU, RAM/VRAM, storage, draw calls, polygons, textures, audio memory/voices, build size, mobile battery/thermal and online network.

Accepted behavior:

- `at_least` / `at_most` constraints;
- target versus hard-limit semantics;
- deterministic `pass/warn/fail/unknown` evaluation;
- Project DNA derivation for FPS/frame time/RAM/VRAM/build size;
- explicit configured-but-unmeasured coverage;
- duplicate/unconfigured observation rejection;
- blocking hard-limit failures;
- report round-trip and derived-field tamper validation;
- `.kodepoia/budgets/` through `WorkspaceBoundary`;
- `budget-report-v1` schema.

## Acceptance record

- accepted implementation head `8ac3772e98c70260c320519a214bb25b6cedbb38`;
- PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`;
- isolated derivation/evaluation/persistence smoke: PASS;
- R0 `32561719921` / #603 — SUCCESS Windows + Ubuntu;
- Python Core `32561719925` / #577 — SUCCESS Windows + Ubuntu;
- KodeStudio UI Smoke `32561720008` / #544 — SUCCESS Windows.

## Manual intervention

**NONE.** Foundation acceptance evaluated structured observations and did not require hardware profiling.

## Regression protection

Performance collectors may feed R6.2 later but must not create requirements for non-target platforms or weaken target/hard-limit/unknown semantics.

---

# R6.3 — KodeTests + KodeRegression foundation — COMPLETE

## Objective and accepted scope

R6.3 established structured test-run evidence and baseline/current regression comparison.

KodeTests accepted behavior:

- stable unique IDs;
- `pass/fail/error/skip` observations;
- run `unknown/pass/warn/fail` aggregation;
- validated counts and total duration;
- `.kodepoia/tests/runs/` through `WorkspaceBoundary`;
- `test-run-report-v1` schema.

KodeRegression accepted behavior:

- matching-suite comparison by stable ID;
- `unchanged/regressed/fixed/added/removed` classification;
- PASS→FAIL/ERROR, PASS→SKIP, FAIL→ERROR and removed cases are regressions;
- FAIL/ERROR→SKIP cannot hide a known failure;
- newly added FAIL/ERROR cases fail regression comparison;
- derived-field tamper detection;
- `.kodepoia/tests/regression/` through `WorkspaceBoundary`;
- `regression-report-v1` schema;
- no new arbitrary command-execution path.

## Acceptance record

- accepted implementation head `7150237c263dd3ac96af4662d74909e05f3cf991`;
- PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`;
- isolated baseline/current persistence smoke: PASS;
- R0 `32562032986` / #622 — SUCCESS Windows + Ubuntu;
- Python Core `32562032998` / #596 — SUCCESS Windows + Ubuntu;
- KodeStudio UI Smoke `32562032982` / #563 — SUCCESS Windows.

## Manual intervention

**NONE.** R6.3 consumes structured evidence produced by governed executors/CI.

## Regression protection

Deleting or skipping a known case must never manufacture an apparent fix.

---

# R6.4 — KodeVisualQA foundation — COMPLETE

## Objective and rationale

R6.4 established a deterministic visual-regression contract comparing a current render/capture with a named approved baseline. It distinguishes exact identity, controlled tolerance and blocking visual regression, bridges accepted R5 capture automation with R6.3 regression evidence, and keeps the comparison layer engine-neutral.

## Accepted scope

- immutable baseline identity/metadata and approval provenance;
- current capture identity/metadata;
- image dimensions/format/channel validation;
- deterministic pixel-difference statistics;
- dependency-controlled perceptual dHash metric;
- structured ignore/mask regions declared by policy and hash-bound into evidence;
- explicit PASS/WARN/FAIL/UNKNOWN and reasons;
- visual diff PNG generation;
- missing baseline/current evidence handling;
- hash-bound policy/baseline/current/report evidence;
- persistence under `.kodepoia/visual_tests/` with separate baselines/runs/diffs;
- R6.3 stable `visual:<case-id>` integration;
- fixtures for exact match, encoding identity, changed pixels, threshold boundaries, resolution/mode/format mismatch, missing evidence and tamper detection;
- one real hardware-local Godot rendered comparison on the accepted workstation.

## Out of scope

AI aesthetic judgement, automatic baseline replacement, Blender/ComfyUI visual generation, DeviceLab matrix, shader/LOD/texture optimization, audio QA and store screenshot certification.

## Accepted implementation/deliverables

- `src/kodepoia/quality/visual.py`;
- `src/kodepoia/quality/__init__.py` exports;
- `src/kodepoia/quality/visual_acceptance.py`;
- `schemas/visual-report-v1.schema.json`;
- `tests/test_r6_4_visualqa.py`;
- `docs/roadmap/R6_4_DESIGN.md`;
- `docs/roadmap/R6_4_ACCEPTANCE.md`;
- `scripts/r6_4_accept_local.ps1`;
- `.kodepoia/visual_tests/baselines/`, `runs/`, `diffs/`;
- separate `kodegodot_capture_png_sequence` tool with explicit KodeGodotExecutor policy and fixed VisualQA output root;
- Pillow constrained to `>=12.3,<12.4` for deterministic image handling in this accepted foundation.

All project paths resolve through `WorkspaceBoundary`. The new evaluator/capture surface exposes no arbitrary model-supplied executable, argv, command, cwd, host or output-path fields. The accepted R5 AVI capture behavior remains unchanged.

## Acceptance record

### Accepted implementation identity

- starting normalized `main`: `e96e7c3b168975869c911f880044b7ef8e322157`;
- implementation branch: `feature/r6-4-visualqa`;
- implementation PR: #39;
- accepted final implementation head: `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`;
- implementation merge: `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`.

### Final-head hosted evidence

All hosted gates passed on the exact accepted implementation head:

- R0 Repository Guard `32564304755` / #666 — SUCCESS Windows + Ubuntu;
- Python Core `32564304757` / #640 — SUCCESS Windows + Ubuntu, PowerShell acceptance-runner validation, full pytest and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32564304798` / #607 — SUCCESS Windows.

### Required manual hardware-local evidence — SATISFIED

The user executed `scripts/r6_4_accept_local.ps1` on the exact same head. Accepted result:

- `metadata.acceptance_completed=true`;
- Windows `Windows-11-10.0.26220-SP0`;
- Python `3.12.4`;
- Godot `4.7.2.stable.steam.ed1daf0bf`, compatible 4.7.x;
- rendering method `gl_compatibility`;
- rendering driver `opengl3`;
- video adapter `AMD Radeon RX 6750 XT`;
- baseline/current Movie Maker PNG captures return code 0, no timeout or cancellation;
- baseline SHA-256 `98dca538d872e8f883b4de4e9b92b741091365f15d193bac1127801277ca567a`;
- current SHA-256 `98dca538d872e8f883b4de4e9b92b741091365f15d193bac1127801277ca567a`;
- changed ratio `0.0`;
- perceptual distance ratio `0.0`;
- policy SHA-256 `a2dbb4532c50e522639a1b1a264420d2f491d17e7b2350d500ddf415bd70014e`;
- evidence SHA-256 `4c0375391d8f0e1b54c8c949b264ec70d6c9a18f10798a52a72d79ac18daab56`;
- VisualQA status `pass`;
- R6.3 hook `visual:godot-real-render` PASS;
- AuditLog chain valid;
- summary `8 PASS / 0 FAIL / 8`.

The real-render requirement is satisfied because rendering method, driver and Radeon adapter evidence are explicit and non-headless/non-dummy.

## Acceptance gates / Definition of Done — RESULT

1. deterministic fixture comparison Windows + Ubuntu — PASS;
2. exact match = PASS — PASS;
3. tolerance boundaries deterministic — PASS;
4. change above blocking threshold = FAIL — PASS;
5. resolution/mode/format incompatibility explicit — PASS;
6. baseline/current hashes preserved — PASS;
7. derived/policy/evidence tampering rejected — PASS;
8. masks/ignore policy included in evidence hash — PASS;
9. persistence confined to `.kodepoia/visual_tests/` — PASS;
10. R0/Python Core/KodeStudio CI green — PASS;
11. required real Godot rendered baseline/current/diff/report chain — PASS;
12. implementation PR merged only after CI + required local evidence — PASS;
13. post-merge plan/status/continuity normalization — PASS via PR #40 merge `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`.

## Manual intervention

**REQUIRED — SATISFIED.** No further R6.4 user action is required unless a later regression is demonstrated.

The accepted manual gate used the exact final implementation head and the accepted Windows/Radeon/Godot environment. The historical command contract remains documented in `R6_4_ACCEPTANCE.md`; it must not be reused as evidence for a later changed implementation head without rerunning the gate.

## Rollback / regression protection

R6.4 is additive. A demonstrated regression may revert its implementation merge without mutating R6.1–R6.3 evidence. Later changes must not:

- auto-approve or replace a baseline to hide a failure;
- convert missing evidence into PASS;
- weaken baseline/report/policy tamper checks;
- remove mask policy hashing;
- substitute headless/dummy rendering where real-render evidence is required;
- regress the accepted R5 AVI capture path;
- introduce arbitrary model-supplied process arguments or host paths.

---

# R6.5 — KodeAccessibility foundation — IN PROGRESS

## Objective and rationale

Create structured accessibility evidence and automated baseline checks for supported UI surfaces, plus a real Windows interactive validation path for keyboard/focus/accessibility semantics that hosted CI cannot fully prove.

WCAG 2.2 is the source-criteria baseline where applicable. W3C WCAG2ICT 2.2 is the preferred interpretation guidance for applying applicable WCAG criteria to KodeStudio as non-Web desktop software. The implementation must not claim universal WCAG certification.

## In scope

- stable accessibility rule IDs and target IDs;
- severity/status/evidence/applicability;
- explicit `not_applicable` with reason rather than false PASS;
- deterministic report aggregation, blockers, counts and canonical evidence SHA-256;
- round-trip, derived-field and evidence tamper rejection;
- project-confined persistence under `.kodepoia/diagnostics/accessibility/`;
- R6.3 stable test/regression integration;
- keyboard reachability/focus eligibility where automatable;
- accessible name/description/role/state checks where Qt/PySide exposes them;
- deterministic contrast/target-size checks when explicit source data exists;
- stable KodeStudio and Project Wizard accessibility control registration;
- dynamic budget and requirement-priority controls;
- named application-owned interactive-control discovery;
- real Windows interactive keyboard-only, visible/unobscured focus and Narrator acceptance;
- source-head and automated-report-hash binding for manual evidence.

## Out of scope

Universal WCAG/legal certification, certification of future generated applications, TalkBack/VoiceOver/mobile testing, NVDA/JAWS/Orca certification, console certification, cognitive user research, OCR-based screen-reader checking, automatic aesthetic focus judgement and game-specific accessibility feature design beyond the foundation.

## Current implementation/deliverables

R6.5 started from normalized `main` `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1` on `feature/r6-5-accessibility`; implementation PR #41 is open. The final implementation head is not yet frozen.

Implemented/current artifacts:

- `src/kodepoia/quality/accessibility.py`;
- `src/kodepoia/quality/accessibility_acceptance.py`;
- `src/kodepoia/kodestudio/accessibility.py`;
- accessibility metadata changes in `src/kodepoia/kodestudio/app.py` and `project_wizard.py`;
- `schemas/accessibility-report-v1.schema.json`;
- `tests/test_r6_5_accessibility.py`;
- `tests/test_r6_5_accessibility_ui.py`;
- `scripts/r6_5_accept_local.ps1`;
- `docs/roadmap/R6_5_DESIGN.md`;
- `docs/roadmap/R6_5_ACCEPTANCE.md`;
- Windows UI workflow coverage and PowerShell syntax validation for R6.4/R6.5 acceptance runners.

Current automated rules include:

- `qt.control.present`;
- `qt.name.explicit`;
- `qt.description.required`;
- `qt.keyboard.tab_focus`;
- `qt.accessible.interface`;
- `qt.accessible.role`;
- `qt.accessible.state`.

Visible enabled registered controls must participate in keyboard Tab focus. Hidden/disabled adaptive controls are `NOT_APPLICABLE` for the focus rule with an explicit reason. Registration/name/interface/role contracts remain auditable. Named application-owned controls that bypass registration are blocking failures.

Qt-owned implementation children are not treated as Kodepoia controls. Initial Windows CI identified `QTabBar` internal `ScrollLeftButton` and `ScrollRightButton`; the audit excludes only these known Qt-owned controls, not arbitrary application widgets.

Initial Ubuntu CI also demonstrated that an accessibility evidence symlink escape is correctly rejected by existing `WorkspaceBoundary` with `WorkspaceViolation`. The first test expected the wrong exception type and was corrected; confinement was not weakened. PySide focus-policy conversion was hardened to avoid eager enum conversion.

## Acceptance gates

1. stable IDs and duplicate rejection;
2. deterministic PASS/WARN/FAIL/UNKNOWN/NOT_APPLICABLE semantics;
3. N/A requires reason and never manufactures PASS;
4. blocking only on actual FAIL evidence;
5. report counts/blockers/hash survive round-trip and tampering is rejected;
6. JSON Schema validation;
7. `.kodepoia/diagnostics/accessibility/` WorkspaceBoundary and symlink confinement;
8. R6.3 stable accessibility hook;
9. deterministic explicit contrast/target-size fixtures;
10. required KodeStudio and Project Wizard controls registered;
11. QAccessible interface/name/role/state evidence;
12. visible enabled registered controls tab-focusable;
13. adaptive hidden/disabled controls explicitly N/A;
14. future named application controls cannot silently bypass registration;
15. R0 final-head SUCCESS Windows + Ubuntu;
16. Python Core final-head SUCCESS Windows + Ubuntu including PowerShell parser, pytest and integrated accessibility UI smoke;
17. KodeStudio UI Smoke final-head SUCCESS Windows including accessibility UI tests;
18. required real Windows keyboard-only checklist PASS;
19. required real focus-visible/not-obscured checklist PASS;
20. required Windows Narrator checklist PASS;
21. manual evidence bound to exact final source head and unchanged automated report hashes;
22. local integrated result `15 PASS / 0 FAIL / 15`, `acceptance_completed=true`;
23. implementation PR merges only after hosted + manual evidence review;
24. post-merge plan/status/continuity normalization.

## Manual intervention

**REQUIRED — PENDING FINAL-HEAD CI.**

### Reason

Hosted CI can inspect Qt metadata and structural keyboard focus, but cannot authoritatively prove human-observable focus appearance/occlusion or what Windows Narrator actually speaks in a real desktop session.

### Planned commands

Do not execute until ChatGPT supplies `<R6_5_FINAL_HEAD>` after final-head CI is green.

```powershell
git fetch origin
git checkout <R6_5_FINAL_HEAD>
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,ui]"
powershell -ExecutionPolicy Bypass -File .\scripts\r6_5_accept_local.ps1
```

If an environment must be created:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,ui]"
```

### Manual checklist contract

The runner prepares two automated reports, then launches KodeStudio in a real Windows session and asks for 13 blocking observations:

- 5 keyboard checks;
- 2 focus checks;
- 6 Narrator checks.

Narrator commands:

- `Win+Ctrl+Enter` — start/stop Narrator;
- `Narrator+Alt+X` — Speech Recap/live transcription if useful for reviewing spoken output.

The Security check may focus the emergency-stop button for its accessible announcement but **must not activate the KillSwitch**.

### Expected evidence

Successful final JSON must include:

- exact `metadata.source_head`;
- `metadata.acceptance_completed=true`;
- two automated reports status PASS with zero blocking failures and evidence hashes;
- `manual.total=13`, `manual.passed=13`, `manual.failed=0`, `manual.blocking_failures=0`;
- `summary.total=15`, `summary.passed=15`, `summary.failed=0`;
- output under `.kodepoia/diagnostics/accessibility/r6-5-local-acceptance.json`.

### Failure recovery

If any automated or manual item fails, preserve the evidence and answer FAIL truthfully with the checklist note. Do not edit generated reports/responses to manufacture PASS, do not disable a rule, and do not reinterpret missing Narrator output as success. Send the exact failure/output back for correction.

### Do not do yet

Do not merge PR #41, mark R6.5 COMPLETE, start R6.6, activate the KillSwitch for testing, or delete local accessibility evidence before final review.

## Rollback / risks

R6.5 is additive to the quality layer and adds accessibility metadata to existing KodeStudio controls. Reverting the implementation must remove the R6.5 modules/schema/tests/runner/UI metadata changes together without touching accepted R6.1–R6.4 evidence. Local `.kodepoia/diagnostics/accessibility/` evidence should not be deleted unless explicitly requested.

Risks include false PASS from hidden controls, false FAIL from framework internals, screen-reader behavior diverging from structural Qt metadata, focus appearance not inferable offscreen, stale manual evidence from another source SHA and accidental activation of the KillSwitch. The current design addresses these with explicit N/A semantics, narrow Qt-internal exclusions, real Narrator/focus testing, source-head/hash binding and a no-activation safety rule.

---

# R6.6 — KodeLocalization + pseudo-localization foundation

## Objective

Establish deterministic localization contracts before later phases multiply UI surfaces: stable message IDs, catalogs, placeholder integrity, fallback and pseudo-localization. Human-quality translation certification is deliberately not part of this foundation.

## In scope / deliverables

- stable locale/message IDs and source locale;
- missing/extra/duplicate key detection;
- placeholder/token parity;
- plural/select validation where supported;
- pseudo-localization that expands text without corrupting placeholders/markup;
- hard-coded user-visible string detection on registered surfaces where feasible;
- explicit locale fallback;
- `src/kodepoia/quality/localization.py`;
- `schemas/localization-report-v1.schema.json`;
- `tests/test_r6_6_localization.py`;
- pseudo-locale fixtures/catalogs;
- KodeStudio long-string/truncation smoke;
- project-confined localization evidence and R6.3 integration.

## Out of scope

Professional translation, cultural certification, voice localization, universal font/script certification and store metadata translation.

## Acceptance gates

Stable IDs/serialization, missing placeholders FAIL, pseudo-localization preserves placeholders, fallback explicit, no platform pollution, report tamper validation, Windows + Ubuntu tests and KodeStudio smoke, merge + normalization.

## Manual intervention

**NONE.** Structural and pseudo-localized acceptance is objectively testable in CI.

## Rollback / risks

Do not destabilize existing strings without migration; pseudo-locale must never become production default.

---

# R6.7 — KodeTechnicalDebt foundation

## Objective

Create a persistent structured technical-debt register so debt is observable, prioritized and linked to code/requirements/tests instead of remaining informal comments.

## In scope / deliverables

- stable debt IDs;
- category/severity/impact/probability/effort;
- owner/scope/source/provenance;
- file/symbol/test/requirement references;
- first-seen/last-seen/resolved lifecycle;
- accepted-debt rationale with optional review/expiry;
- deterministic ranking;
- stable duplicate fingerprinting where applicable;
- project-confined persistence under diagnostics;
- structured report/schema;
- Health `technical_debt` adapter;
- regression semantics for newly introduced blocking debt;
- `src/kodepoia/quality/technical_debt.py`, schema, focused tests and docs.

## Out of scope

Automatic code rewriting, License/BOM, architecture changes without ADR and arbitrary static-analysis shell commands supplied by a model.

## Acceptance gates

Stable lifecycle, deterministic score, accepted debt distinct from resolved debt, confinement, Health integration, serialization tamper checks, CI green, merge + normalization.

## Manual intervention

**NONE.** Deterministic fixtures and repository evidence suffice.

## Risks

Never treat accepted debt as resolved; preserve rationale/history; avoid unstable fingerprints producing duplicate debt each run.

---

# R6.8 — KodeCI + KodeBuild foundation

## Objective

Convert repository workflows/builds into structured evidence consumable by Health, Tests, Regression, VisualQA and later release tooling.

## In scope

- normalized CI check IDs/statuses;
- build manifest tied to source SHA, Python version, platform, dependency inputs and artifact hashes;
- Python package build validation;
- Windows + Ubuntu build/test matrix;
- failed/cancelled/skipped distinction;
- lint/compile/tests/regression/security/visual hooks as available;
- secrets-free logs/manifests;
- `.kodepoia/workflows/` and `.kodepoia/releases/` evidence where applicable;
- workflow updates without weakening R0/Python/UI gates.

## Out of scope

Store publishing, signing certificates, installers/update channels, macOS/iOS claims from Windows/Ubuntu CI and generated app framework builds belonging to later phases.

## Expected deliverables / gates

Structured CI/build module(s), build-manifest schema, deterministic package-build tests, source/artifact hash evidence, documented unavoidable non-byte-reproducible fields, Windows+Ubuntu success, skipped/cancelled never PASS, secret redaction, final-head workflows green, merge + normalization.

## Manual intervention

**CONDITIONAL.** Trigger only if GitHub-hosted Windows cannot authoritatively prove a Windows-specific build behavior/artifact required by the DoD or a runner limitation conflicts with the accepted local environment.

If triggered:

```powershell
git fetch origin
git checkout <R6_8_FINAL_HEAD>
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,ui,code]"
powershell -ExecutionPolicy Bypass -File .\scripts\r6_8_accept_local.ps1
```

Expected: build manifest, source SHA, Python/platform, artifact names/sizes/hashes, tests, `acceptance_completed=true`, zero blocking failures. Preserve logs/manifest on failure; never edit hashes or reuse artifacts from another SHA; do not merge until reviewed if this conditional gate triggers.

## Risks

Do not remove/narrow checks or create self-referential acceptance. Build evidence must remain tied to exact source SHA.

---

# R6.9 — KodeAppSecurity baseline

## Objective

Create a platform-aware application-security baseline for products Kodepoia creates and for applicable Kodepoia surfaces. The frozen architecture requires threat modeling, input/auth/network validation, dependency security, secure storage and useful fuzzing where applicable.

OWASP ASVS 5.0.0 is used as a current catalogue for applicable web/API/auth/session/security controls only.

## In scope / deliverables

- structured threat model: assets, trust boundaries, entry points, threats, mitigations, residual risk;
- stable requirement/check IDs;
- path/input/network/auth/session checks only for present surfaces;
- dependency-vulnerability evidence with timestamp/provenance;
- secure-storage expectations where applicable;
- deterministic fuzz/property tests for structured inputs where useful;
- report/schema + Health `security` adapter;
- governed diagnostic persistence;
- no mandatory remote security SaaS and no arbitrary scanner command injection.

## Out of scope

Third-party penetration testing, exploit development, store certification and cloud/backend implementation.

## Acceptance gates

Threat model completeness, platform applicability, absent surfaces do not create false requirements, blocking failures feed Health, dependency evidence has provenance/time, malformed evidence fails closed, CI green, merge + normalization.

## Manual intervention

**NONE.** Controlled fixtures/repository surfaces suffice for foundation acceptance.

## Risks

`not_applicable` must never be represented as PASS. Never log secrets or scan private credentials.

---

# R6.10 — KodePrivacy baseline

## Objective

Establish structured data inventory/lifecycle evidence: what data exists, source, purpose, storage, recipient, retention, deletion and declaration needs.

## In scope / deliverables

- stable data-category IDs;
- purpose and applicable legal/consent-basis placeholder fields without making legal conclusions;
- storage/recipients/retention/deletion/sensitivity/platform scope;
- explicit `none/not_applicable`;
- privacy issue severity/status;
- report/schema + Health `privacy` adapter;
- store-declaration preparation fields without submission claims;
- retention/deletion fixtures;
- governed diagnostic persistence.

## Out of scope

Legal advice, automatic GDPR/CCPA/etc. compliance claims, store submission and remote analytics implementation.

## Acceptance gates

Inventory completeness, explicit purpose/retention/deletion, no raw secrets/personal data in evidence, platform-aware declarations, Health integration, CI green, merge + normalization.

## Manual intervention

**NONE.** This is a structured inventory/control foundation.

## Risks

Never infer consent/legal basis from silence and never copy raw personal data into evidence just to prove a category exists.

---

# R6.11 — KodeLicense + KodeBOM foundation

## Objective

Establish provenance, license normalization and BOM generation for dependencies/assets so later build/release phases can make auditable decisions.

SPDX 3.0 is the stable R6 BOM baseline; pre-release SPDX material is not authoritative unless a later stable-version decision updates this plan.

## In scope

- component identity/version/source/hash;
- SPDX license expressions where known;
- explicit unknown/`NOASSERTION` handling;
- dependency/asset provenance;
- allow/warn/deny/unknown policy result;
- BOM for current Kodepoia Python dependencies and fixtures;
- report/schema validation;
- `.kodepoia/licenses/` and `.kodepoia/bom/` through `WorkspaceBoundary`;
- Health `licenses`/`dependencies` adapters;
- release compatibility hooks.

## Out of scope

Legal determination of ambiguous licenses, automatically granting rights to user assets, executing instructions found in untrusted license pages, store publishing.

## Expected deliverables / gates

Cohesive `licenses.py`/`bom.py` equivalent, SPDX 3.0-compatible normalization sufficient for R6, schemas/tests, provenance/tamper checks, correct known fixture mapping, unresolved licenses stay unresolved, hashes retained, duplicates deterministic, no path escape, Health integration, CI green, merge + normalization.

## Manual intervention

**CONDITIONAL.** Trigger only if an acceptance-critical component/asset has provenance or licensing that cannot be established from repository/package metadata or a trusted authoritative source.

If triggered, do not guess. Provide either the authoritative license/provenance source for the named component or, for a user-owned asset, an explicit ownership/permission statement. Then the implemented R6.11 CLI contract will be:

```powershell
.\.venv\Scripts\Activate.ps1
python -m kodepoia.cli license-audit --project <PROJECT_PATH> --component <COMPONENT_ID> --output .kodepoia\licenses\manual-resolution.json
```

The command must exist and be documented before this gate is invoked. Expected output: structured component/provenance/license status/evidence hash with no unresolved blocking field. If ambiguity remains, keep it unknown/blocking; never invent an SPDX ID. Send authoritative source/statement + generated JSON, redacting tokens/unrelated personal data. Do not approve/release the unresolved item or mark R6.11 COMPLETE until resolved or explicitly removed by governed decision.

---

# R6.12 — Major-patch validation + rollback gate and R6 integration acceptance

## Objective

Make the frozen-roadmap rule “every major patch has validation and rollback” enforceable, then run final integrated R6 acceptance.

## In scope

- deterministic major-patch classification from changed scope/risk rather than model opinion;
- manifest tied to base/head SHAs;
- validation matrix selected from changed domains/platforms: tests, regression, visual, accessibility, localization, debt, build, security, privacy, license/BOM, health/budget as applicable;
- mandatory explicit rollback strategy for every major patch;
- SafeChange snapshot for sensitive mutable project changes;
- controlled rollback rehearsal;
- missing/partial/skipped/cancelled required evidence blocks acceptance;
- final integrated R6 fixture/report enumerating R6.1–R6.12 evidence.

## Out of scope

R7 implementation, release-channel updater, destructive production rollback tests and any weakening of Guardian approvals.

## Expected deliverables

- `src/kodepoia/quality/patch_gate.py` or governed equivalent;
- major-patch manifest/report schema;
- classification/evidence/rollback tests;
- protected orchestrator integration;
- `scripts/r6_12_accept_local.ps1` if conditional local gate triggers;
- `R6_12_ACCEPTANCE.md` and final plan/status/continuity normalization.

## Acceptance gates

1. deterministic major/minor classification;
2. major patch cannot PASS without rollback plan;
3. required gates selected by relevant domains/platform targets;
4. missing/skipped/cancelled required checks block acceptance;
5. controlled rollback restores expected state/hashes;
6. SafeChange/Audit used where required;
7. no arbitrary model shell/path fields;
8. all R6.1–R6.11 regression suites green;
9. final R0/Python Core/KodeStudio green;
10. triggered manual/local gates complete;
11. PR merge + normalization records R6.1–R6.12 COMPLETE;
12. only then can R6 become COMPLETE and R7 planning begin.

## Manual intervention

**CONDITIONAL.** Trigger if the final integration fixture uses a hardware-local capability unavailable to hosted CI (for example the real-render VisualQA path) or Guardian policy explicitly requires user approval for a sensitive local operation.

If triggered:

```powershell
git fetch origin
git checkout <R6_12_FINAL_HEAD>
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,ui,code]"
powershell -ExecutionPolicy Bypass -File .\scripts\r6_12_accept_local.ps1
```

Expected: base/head SHA, classification/reasons, required-gate list, PASS evidence IDs, rollback-plan ID, snapshot/rollback evidence where applicable, AuditLog verification where applicable, `failed=0`, `acceptance_completed=true`.

If rollback rehearsal fails, stop and preserve the pre-test snapshot/evidence. Never repeatedly mutate an unrestored fixture or downgrade an unavailable required gate. Send terminal summary + final integration JSON + specifically required local reports, with secrets redacted. Do not mark R6 COMPLETE/start R7/merge final implementation until reviewed.

## Risks

Avoid circular validation where patch gate trusts its own summary without validating underlying evidence. The gate must itself remain revertible and never bypass Guardian/SafeChange/CI.

---

# Manual-intervention forecast for the remainder of R6

The user is informed before each applicable manual gate:

- **R6.4 — REQUIRED:** SATISFIED and accepted on head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`; no further action unless regression.
- **R6.5 — REQUIRED:** IN PROGRESS; real interactive Windows keyboard-only + visible/unobscured focus + Narrator checklist will be requested only after final-head hosted CI. Successful integrated result must be 15/15 PASS.
- **R6.8 — CONDITIONAL:** local Windows build evidence only if hosted CI cannot authoritatively meet build/reproducibility DoD.
- **R6.11 — CONDITIONAL:** provenance/license evidence only if an acceptance-critical component remains unresolved.
- **R6.12 — CONDITIONAL:** local integration/approval only if final selected gates require hardware-local execution or explicit approval.
- **R6.6, R6.7, R6.9, R6.10 — NONE** currently planned.

Before asking the user to run a manual gate, its acceptance document and user-facing instructions must identify the exact final implementation head and confirm final implementation-specific commands, expected output, recovery and evidence requirements.

# R6 completion rule

R6 is COMPLETE only when:

1. R6.1 through R6.12 are COMPLETE with all required evidence;
2. no REQUIRED/triggered CONDITIONAL manual gate remains pending;
3. R6.12 integrated gate passes;
4. final implementation-head R0, Python Core Windows+Ubuntu and KodeStudio UI Smoke succeed;
5. final implementation PR is merged;
6. `R6_PLAN.md`, `R6_STATUS.md` and `KODEPOIA_CONTINUITY.md` are synchronized on normalized `main`;
7. only then may R7 planning begin under the permanent phase-start planning rule.

# Change log

- 2026-08-22: retroactive plan created by explicit user request before R6.4; R6.1–R6.3 recorded from already accepted evidence; R6.4–R6.12 structure frozen.
- 2026-08-22: planning head `8fbad7c13dd65f9dcd49a03b33a3174fcf28d18a` passed R0 `32563057993`/#639, Python Core `32563057956`/#613 and UI Smoke `32563057903`/#580; PR #37 merged as `0a91064608507966a47921df8fb36e5f25477141`.
- 2026-08-22: post-plan normalization PR #38 merged as `e96e7c3b168975869c911f880044b7ef8e322157`; R6.4 started from that normalized `main` on `feature/r6-4-visualqa`.
- 2026-08-22: R6.4 accepted on final head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41` after R0 #666, Python Core #640, UI Smoke #607 and required Windows/Godot/Radeon hardware acceptance all passed; PR #39 merged as `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`; post-merge normalization PR #40 merged as `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`.
- 2026-08-22: R6.5 started from normalized main `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1` on `feature/r6-5-accessibility`, PR #41. Manual classification remains REQUIRED. Initial CI corrected a test expectation for existing `WorkspaceViolation`, identified narrow Qt-owned `QTabBar` scroll controls, and hardened PySide focus-policy conversion. R6.5 remains IN PROGRESS; R6.6 remains blocked.
