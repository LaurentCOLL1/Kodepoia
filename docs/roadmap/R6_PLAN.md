# Kodepoia — R6 detailed phase plan

**Phase:** R6  
**Roadmap title:** Quality / Health / Budget / CI  
**Status:** IN PROGRESS  
**Phase started:** 2026-08-22  
**Plan reconstructed:** 2026-08-22 by explicit user request, after R6.1–R6.3 had already been accepted  
**Architecture:** v1.0 frozen  
**Source of truth after this planning PR merges:** normalized `main`

## Purpose of this document

This is the exhaustive recovery and execution plan for R6. It is a retroactive exception to the normal phase-start planning rule because R6.1–R6.3 were already complete when the permanent `RX_PLAN.md` governance rule was introduced. The user explicitly requested that R6 be brought under the same planning discipline before R6.4 starts.

This file therefore does two things:

1. records R6.1–R6.3 exactly as already accepted, without reopening or redefining them;
2. freezes the remaining R6 subdivision structure before any R6.4 implementation begins.

R6 may not be marked COMPLETE until every subdivision in this file is COMPLETE with its required acceptance evidence, or a later recorded roadmap/architecture decision explicitly removes a subdivision from scope.

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

The frozen architecture further requires that quality remain connected to the protected execution cycle: request → plan/context → Guardian → snapshot when required → governed executor → tests/verifier → Health/Budget/Regression → commit or correction. R6 must not create any direct model-to-shell, arbitrary command, unrestricted host-path, or governance bypass.

## Explicitly out of scope for R6

The architecture lists additional quality capabilities such as KodeAudioQA, KodeDeviceLab, KodeAssetDoctor, KodeTextureOptimizer, KodeLOD and KodeShaderProfiler. They are not named in the frozen R6 roadmap and are therefore not silently pulled into this phase. They remain for later roadmap phases or the subsystem phases that naturally own them.

Likewise, R6 does not perform store release/signing, Android/iOS device certification, full desktop application generation, ComfyUI integration, Blender integration, audio/voice production, or backend/live-ops activation. Those belong to later phases.

## Phase-wide architecture and governance boundaries

Every R6 subdivision must preserve all previously accepted boundaries:

- `WorkspaceBoundary` for project path confinement;
- `ProcessSandbox` and the global KillSwitch for process execution;
- Guardian and `PermissionSet` for authorization and risk policy;
- structured Tool APIs instead of model-supplied arbitrary commands;
- SafeChange snapshots before sensitive mutations;
- AuditLog hash-chain evidence for governed sensitive operations;
- Secrets redaction and secrets exclusion from model context / persistent memory;
- DataGovernance and schema-version discipline;
- platform-aware behavior: non-target platforms must not impose requirements, inputs, budgets, dependencies or test obligations;
- local-first/offline-capable behavior for already configured projects;
- no architecture-foundation modification without ADR;
- no phase/subdivision completion from partial CI or unsupported inference.

All persistent R6 project evidence must remain under the initialized `.kodepoia/` tree and must be resolved through `WorkspaceBoundary`. The project initializer already reserves `health/`, `budgets/`, `tests/`, `visual_tests/`, `licenses/`, `bom/`, `workflows/`, `diagnostics/` and `releases/`; R6 should reuse those locations instead of inventing ungoverned storage roots.

## Current external-reference baselines

These are current reference baselines used only to inform implementation and acceptance where applicable. They do not override the frozen architecture and must be rechecked if a later implementation depends materially on current external requirements.

- Accessibility: W3C WCAG 2.2 is the current W3C Recommendation baseline. Use it as a testable reference for applicable UI/web semantics, keyboard/focus, target sizing and related accessibility behavior; do not force web-only requirements onto non-web products.
- Application security: OWASP ASVS 5.0.0 is the current stable ASVS release. Use it as a requirement catalogue where a generated product exposes web/API/auth/session/security surfaces, while keeping platform-aware applicability.
- Software BOM: SPDX 3.0 is the current stable SPDX specification baseline. SPDX 3.1 RC1 is pre-release/testing material and must not replace the stable baseline for authoritative R6 acceptance unless it becomes stable and a recorded decision updates the plan.

## Global prerequisites before R6.4

Before R6.4 implementation begins:

1. R1–R5 remain COMPLETE without demonstrated regression.
2. R6.1, R6.2 and R6.3 remain COMPLETE with their accepted heads/PRs/CI evidence below.
3. This `R6_PLAN.md` planning PR must pass the normal final-head GitHub checks and be merged to normalized `main`.
4. R6.4 must branch only from that normalized `main`.
5. No previously accepted R5 hardware-local workaround may be regressed, especially process pipe draining, background service handling, Movie Maker real-render constraints, socket timeout handling, DAP sequencing and loopback-only service exposure.

## Complete subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R6.1 | KodeHealth foundation | COMPLETE | NONE | R5 COMPLETE |
| R6.2 | KodeBudget foundation | COMPLETE | NONE | R6.1 |
| R6.3 | KodeTests + KodeRegression foundation | COMPLETE | NONE | R6.1–R6.2 |
| R6.4 | KodeVisualQA foundation | PLANNED | REQUIRED | R6.1–R6.3 + accepted R5 Godot automation |
| R6.5 | KodeAccessibility foundation | PLANNED | REQUIRED | R6.3–R6.4 |
| R6.6 | KodeLocalization + pseudo-localization foundation | PLANNED | NONE | R6.3 + R6.5 |
| R6.7 | KodeTechnicalDebt foundation | PLANNED | NONE | R6.1–R6.6 |
| R6.8 | KodeCI + KodeBuild foundation | PLANNED | CONDITIONAL | R6.1–R6.7 |
| R6.9 | KodeAppSecurity baseline | PLANNED | NONE | R6.3 + R6.7–R6.8 |
| R6.10 | KodePrivacy baseline | PLANNED | NONE | R6.7–R6.9 |
| R6.11 | KodeLicense + KodeBOM foundation | PLANNED | CONDITIONAL | R6.7–R6.10 |
| R6.12 | Major-patch validation + rollback gate and R6 integration acceptance | PLANNED | CONDITIONAL | R6.1–R6.11 |

No subdivision may be silently added, removed, merged, split or renumbered. Any scope change must update this file and continuity in the same work cycle. Architecture-changing scope requires an ADR before implementation.

---

# R6.1 — KodeHealth foundation — COMPLETE

## Objective and accepted scope

R6.1 established the structured health contract required by the frozen architecture: all 14 architecture health dimensions, explicit `unknown/pass/warn/fail` states, deterministic score/coverage aggregation, blocking failures, exhaustive report validation and project-confined persistence.

Accepted modules/evidence include:

- `src/kodepoia/quality/health.py`;
- `schemas/health-report-v1.schema.json`;
- `tests/test_r6_1_health.py`;
- `.kodepoia/health/` persistence through `WorkspaceBoundary`;
- atomic `latest.json` plus timestamped evidence snapshots;
- rejection of `.kodepoia` symlink escape;
- serialized `blockers` and `unknown_dimensions` consistency validation.

## Acceptance record

- accepted implementation head: `802de4ba3110ace657c4e16306a0ca29850ce2bd`;
- PR #30 merge: `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`;
- isolated hardened focused tests: 9 PASS;
- R0 Repository Guard `32561211168` — SUCCESS Windows + Ubuntu;
- Python Core `32561211156` — SUCCESS Windows + Ubuntu, PowerShell validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32561211167` — SUCCESS Windows.

## Manual intervention

**NONE.** R6.1 was authoritatively accepted without user-side execution.

## Rollback / regression protection

R6.1 must not be reopened without a demonstrated regression or an architecture-changing ADR. Later health integrations may add producers of health observations, but must not weaken exhaustive dimensions, explicit unknown coverage, validation integrity or WorkspaceBoundary confinement.

---

# R6.2 — KodeBudget foundation — COMPLETE

## Objective and accepted scope

R6.2 established architecture-aligned per-platform budget contracts without changing Project DNA. It covers FPS/frame time, CPU/GPU, RAM/VRAM, storage, draw calls, polygons, textures, audio memory/voices, build size, mobile battery/thermal and online network budgets.

Accepted behavior includes:

- per-platform `at_least` / `at_most` constraints;
- target versus hard-limit semantics;
- deterministic `pass/warn/fail/unknown` evaluation;
- Project DNA derivation for FPS, frame time, RAM, VRAM and build size;
- explicit configured-but-unmeasured coverage;
- rejection of duplicate/unconfigured observations;
- blocking hard-limit failures;
- validated report round-trip and derived-field tamper detection;
- `.kodepoia/budgets/` persistence through `WorkspaceBoundary`;
- `schemas/budget-report-v1.schema.json`.

## Acceptance record

- accepted implementation head: `8ac3772e98c70260c320519a214bb25b6cedbb38`;
- PR #32 merge: `65510a9b116d9c48b185a0edb51d99e5b951200a`;
- isolated derivation/evaluation/persistence smoke: PASS;
- R0 Repository Guard `32561719921` / #603 — SUCCESS Windows + Ubuntu;
- Python Core `32561719925` / #577 — SUCCESS Windows + Ubuntu, PowerShell validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32561720008` / #544 — SUCCESS Windows.

## Manual intervention

**NONE.** R6.2 defined/evaluated structured budget observations; it did not require hardware profiling for foundation acceptance.

## Rollback / regression protection

Later performance collectors may feed R6.2 but must not reinterpret Project DNA into requirements for non-target platforms or weaken target/hard-limit distinction and explicit unknown coverage.

---

# R6.3 — KodeTests + KodeRegression foundation — COMPLETE

## Objective and accepted scope

R6.3 established stable structured test-run evidence and baseline/current regression comparison.

Accepted KodeTests behavior:

- stable unique test case IDs;
- `pass/fail/error/skip` observations;
- deterministic run `unknown/pass/warn/fail` aggregation;
- validated counts and total duration;
- atomic `.kodepoia/tests/runs/` persistence through `WorkspaceBoundary`;
- `test-run-report-v1` schema.

Accepted KodeRegression behavior:

- matching-suite baseline/current comparison by stable test ID;
- `unchanged/regressed/fixed/added/removed` classification;
- PASS→FAIL/ERROR, PASS→SKIP, FAIL→ERROR and removed cases treated as regressions;
- FAIL/ERROR→SKIP cannot hide a known failure;
- added failing/error tests fail regression comparison;
- derived-field tamper detection;
- `.kodepoia/tests/regression/` persistence through `WorkspaceBoundary`;
- `regression-report-v1` schema;
- no new arbitrary command execution path.

## Acceptance record

- accepted implementation head: `7150237c263dd3ac96af4662d74909e05f3cf991`;
- PR #34 merge: `6657b258f2396b3d6a3850153b1ffaae1951104d`;
- isolated baseline/current comparison and persistence smoke: PASS;
- R0 Repository Guard `32562032986` / #622 — SUCCESS Windows + Ubuntu;
- Python Core `32562032998` / #596 — SUCCESS Windows + Ubuntu, PowerShell validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32562032982` / #563 — SUCCESS Windows.

## Manual intervention

**NONE.** R6.3 consumes structured observations produced by governed executors/CI and does not directly execute arbitrary test commands.

## Rollback / regression protection

Later integrations must preserve stable IDs and must never allow deleting/skipping tests to manufacture an apparent regression fix.

---

# R6.4 — KodeVisualQA foundation

## Objective and rationale

Create a deterministic visual-regression contract capable of comparing a current render/capture against a named approved baseline while distinguishing exact identity, harmless encoding/noise differences, acceptable tolerance and blocking visual regression. R6.4 bridges accepted R5 capture automation with R6.3 regression evidence.

The foundation must be useful for Godot captures immediately but remain engine-neutral at the report/evaluation layer so later desktop/web/media adapters can reuse it.

## In scope

- baseline identity and immutable baseline metadata;
- current capture metadata;
- image size/format validation;
- deterministic pixel-difference statistics;
- perceptual comparison metric(s) that are reproducible and dependency-controlled;
- optional ignore/mask regions declared by structured policy, never model-invented during evaluation;
- pass/warn/fail thresholds with explicit reasons;
- visual diff artifact generation;
- missing baseline/current artifact handling;
- baseline approval provenance;
- deterministic report serialization;
- persistence under `.kodepoia/visual_tests/` with baseline/run/diff separation;
- integration hooks to R6.3 without replacing generic regression logic;
- focused fixtures that prove changed pixels, resolution mismatch, threshold boundary behavior and tamper detection;
- one real hardware-local Godot capture comparison on the already accepted Windows/Godot workstation.

## Out of scope

- AI aesthetic judgement;
- automatic baseline replacement after failure;
- Blender/ComfyUI visual pipelines;
- full DeviceLab matrix;
- shader/LOD/texture optimization diagnosis;
- audio QA;
- store screenshot compliance.

## Expected implementation

Planned files/modules:

- `src/kodepoia/quality/visual.py`;
- export surface updates in `src/kodepoia/quality/__init__.py`;
- `schemas/visual-report-v1.schema.json`;
- `tests/test_r6_4_visualqa.py`;
- `docs/roadmap/R6_4_DESIGN.md`;
- `docs/roadmap/R6_4_ACCEPTANCE.md`;
- `scripts/r6_4_accept_local.ps1` for the required real-render acceptance gate.

Planned storage:

- `.kodepoia/visual_tests/baselines/` — approved immutable reference artifacts + metadata;
- `.kodepoia/visual_tests/runs/` — current captures and normalized reports;
- `.kodepoia/visual_tests/diffs/` — generated diff images/diagnostics.

All paths must be resolved through `WorkspaceBoundary`; symlink escape must be rejected. The visual evaluator must never receive arbitrary process arguments. Godot capture remains delegated to the already governed KodeGodot APIs/acceptance path.

## Acceptance gates / Definition of Done

1. deterministic unit/fixture comparisons pass on Windows and Ubuntu;
2. exact baseline match = PASS;
3. configured tolerance boundary is deterministic;
4. changed image above blocking threshold = FAIL;
5. resolution/channel/format incompatibility is explicit and cannot silently normalize away evidence;
6. baseline IDs/hashes and current IDs/hashes are preserved;
7. serialized derived metrics cannot be tampered without validation failure;
8. mask/ignore regions are policy data and are hash-bound into evidence;
9. persistence is confined to `.kodepoia/visual_tests/`;
10. R0, Python Core and KodeStudio smoke remain green;
11. real Godot rendered capture on the accepted workstation produces a baseline/current/diff/report chain;
12. R6.4 PR merges only after CI and required local evidence are both accepted;
13. post-merge status/continuity normalization records exact evidence.

## Manual intervention

**REQUIRED.**

### Reason

GitHub-hosted CI can validate the comparison engine with deterministic fixtures, but it cannot authoritatively prove the same real-render Godot path on the already accepted Windows workstation / Radeon RX 6750 XT environment. R5 showed that real Movie Maker rendering cannot be substituted by headless/dummy output when rendered-frame evidence is required.

### Prerequisites

- R6.4 implementation PR final head identified;
- local Kodepoia clone clean and checked out to that exact head;
- Python 3.12.x environment;
- Godot `4.7.2.stable.steam.ed1daf0bf` still available at `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe` or the implementation-approved equivalent path;
- no unrelated local modifications to acceptance fixtures.

### Planned exact command contract

The subdivision must deliver this copy-paste workflow:

```powershell
git fetch origin
git checkout <R6_4_ACCEPTED_HEAD>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,ui]"
$env:KODEPOIA_GODOT_EXE="D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
powershell -ExecutionPolicy Bypass -File .\scripts\r6_4_accept_local.ps1
```

The actual accepted head placeholder will be replaced with the final PR SHA when this gate is reached.

### Expected output

The script must print a machine-readable summary containing at minimum:

- `acceptance_completed=true`;
- Godot version detected;
- renderer/device evidence when available;
- baseline hash;
- current capture hash;
- diff artifact path;
- visual report path;
- visual status PASS;
- passed/failed/total gate counts with `failed=0`.

### Failure recovery

- do not update/approve a baseline merely to make a failure disappear;
- preserve the generated report/diff;
- if Godot path/version changed, stop and report the exact version/path;
- if capture is blank/headless/dummy, stop and report logs; do not accept it as rendered evidence;
- if the script errors, provide the full final command output with secrets redacted.

### Evidence to send back

Send the complete terminal summary plus the generated JSON report and, if requested by the acceptance document, the diff image/capture metadata. Do not send passwords, tokens, unrelated files or private keys.

### Do not do yet

Do not merge the R6.4 implementation PR, replace the baseline, modify thresholds, or move to R6.5 until the local evidence has been reviewed and accepted.

## Rollback / recovery

R6.4 must remain additive. Reverting its PR removes the visual evaluator/schemas/tests without mutating approved R6.1–R6.3 evidence. Baseline creation/approval must be explicit and never rewritten by a failed comparison.

## Risks and regression traps

- nondeterministic renderer output;
- color-space/gamma differences;
- anti-aliasing/driver differences;
- accidental baseline auto-update;
- huge diff artifacts;
- masking too much of the image;
- treating missing evidence as PASS;
- reintroducing R5 headless/dummy capture mistakes.

---

# R6.5 — KodeAccessibility foundation

## Objective and rationale

Create an accessibility evidence model and automated baseline checks for Kodepoia/generated UI surfaces, plus a real interactive Windows validation path for keyboard/focus/accessibility semantics that hosted CI cannot fully prove.

WCAG 2.2 is used as a current testable reference where criteria are applicable, especially keyboard/focus/target semantics. This is not a claim that every desktop/game surface is a web page, and platform-specific adapters may add their own rules later.

## In scope

- structured accessibility checks with stable rule IDs;
- severity/status/evidence model;
- keyboard reachability/focus-order/focus-visible checks for supported KodeStudio widgets where automatable;
- accessible-name/role/state presence checks where PySide exposes them;
- minimum contrast/target-size checks only where deterministic data is available;
- explicit `not_applicable` with reason instead of false PASS;
- report/schema persistence under `.kodepoia/tests/accessibility/` or another plan-approved child of `.kodepoia/tests/`;
- mapping of checks to applicable reference criteria without pretending full WCAG conformance;
- real keyboard-only and Windows Narrator smoke of KodeStudio on the accepted workstation.

## Out of scope

- certification of every future generated application;
- mobile TalkBack/VoiceOver testing;
- console accessibility certification;
- full cognitive/user research;
- game-specific accessibility feature design beyond the foundation checks.

## Expected implementation

- `src/kodepoia/quality/accessibility.py`;
- `schemas/accessibility-report-v1.schema.json`;
- `tests/test_r6_5_accessibility.py`;
- KodeStudio smoke extensions using deterministic widget introspection;
- `scripts/r6_5_accept_local.ps1` plus a short manual Narrator/keyboard checklist recorded into machine-readable evidence;
- design/acceptance docs.

## Acceptance gates / Definition of Done

- stable rule IDs and applicability semantics;
- deterministic automated fixtures on Windows + Ubuntu where supported;
- no inaccessible-name/focus rule can silently disappear between baseline/current evidence;
- structured report round-trip/tamper validation;
- R6.3 regression integration for accessibility rule regressions;
- hosted CI green;
- required local interactive keyboard/Narrator checklist complete with zero blocking failures;
- PR merge + post-merge normalization.

## Manual intervention

**REQUIRED.**

### Reason

Hosted CI can inspect widgets but cannot provide authoritative human-observable keyboard navigation and Windows Narrator behavior in a real interactive desktop session.

### Prerequisites

- exact final R6.5 PR head checked out locally;
- Windows interactive desktop session;
- PySide UI dependencies installed;
- Windows Narrator available;
- no need to expose any credential or personal data.

### Planned exact command contract

```powershell
git fetch origin
git checkout <R6_5_ACCEPTED_HEAD>
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,ui]"
powershell -ExecutionPolicy Bypass -File .\scripts\r6_5_accept_local.ps1
```

The script will launch/prepare the acceptance fixture and print the exact checklist. The required UI actions will include: navigate the defined KodeStudio acceptance screen using keyboard only; verify visible focus is never lost/obscured; activate primary controls without mouse; enable Narrator with `Win+Ctrl+Enter`; traverse the same controls and confirm the announced names/roles match the acceptance manifest; then return to the script to record PASS/FAIL for each item.

### Expected output

- machine-readable accessibility report path;
- checklist IDs and PASS/FAIL state;
- `blocking_failures=0`;
- `acceptance_completed=true`.

### Failure recovery

If focus becomes trapped, a control is unnamed, Narrator output is wrong, or the app crashes, record the exact checklist ID and stop acceptance. Do not mark the item PASS based on intended behavior.

### Evidence to send back

Send terminal summary and generated JSON checklist/report. A screenshot may supplement but not replace the checklist evidence. No audio recording is required unless the acceptance document later explicitly requests one.

### Do not do yet

Do not merge R6.5 or proceed to R6.6 until the required local checklist is reviewed.

## Rollback / risks

Accessibility metadata changes must not break KodeStudio behavior. Avoid brittle rules tied to incidental widget geometry, and never claim unsupported cross-platform conformance from Windows-only evidence.

---

# R6.6 — KodeLocalization + pseudo-localization foundation

## Objective and rationale

Establish a deterministic localization contract before later desktop/mobile/release phases multiply UI surfaces. The foundation focuses on extractable message IDs, locale catalogs, placeholder integrity and pseudo-localization, not human-quality translation certification.

## In scope

- locale/message catalog model with stable IDs;
- source/default locale declaration;
- missing/extra/duplicate key detection;
- placeholder/token parity;
- plural/select structure validation where supported;
- pseudo-localization modes that expand text and preserve placeholders/markup;
- detection of hard-coded user-visible strings in explicitly registered surfaces where feasible;
- locale fallback policy;
- structured localization report and schema;
- persistence under `.kodepoia/tests/localization/`;
- regression integration;
- KodeStudio fixture demonstrating long pseudo-localized strings without silent truncation of critical labels.

## Out of scope

- professional translation of all future languages;
- linguistic/cultural certification;
- voice localization;
- font-family global coverage and shaping for all scripts beyond deterministic fixture coverage;
- store metadata translation.

## Expected implementation

- `src/kodepoia/quality/localization.py`;
- `schemas/localization-report-v1.schema.json`;
- `tests/test_r6_6_localization.py`;
- pseudo-locale fixture/catalogs;
- KodeStudio smoke additions;
- design/acceptance docs.

## Acceptance gates / Definition of Done

- stable IDs and deterministic catalog serialization;
- missing placeholders = FAIL;
- pseudo-localization never mutates placeholder identity;
- unknown locale/fallback behavior explicit;
- no target-platform pollution;
- report round-trip/tamper validation;
- Windows + Ubuntu tests and KodeStudio smoke green;
- PR merge and continuity normalization.

## Manual intervention

**NONE.** R6.6 foundation acceptance is structural/pseudo-localized and can be objectively tested in CI. Human translation quality may become a later release-specific manual task but is not required to accept this foundation.

## Rollback / risks

Avoid replacing existing user-facing strings in a way that destabilizes tests without migration. Pseudo-localization must not be accidentally shipped as the default locale.

---

# R6.7 — KodeTechnicalDebt foundation

## Objective and rationale

Create a persistent, structured technical-debt register so debt is observable, prioritized and linked to code/requirements/tests instead of remaining informal comments. This also provides the maintenance bridge to later KodeVersions/KodeMigration work.

## In scope

- stable debt item IDs;
- category/severity/impact/probability/effort fields;
- owner/scope/source/provenance;
- file/symbol/test/requirement references where available;
- first-seen/last-seen/resolved lifecycle;
- accepted-debt rationale and optional expiry/review date;
- deterministic score/ranking policy;
- duplicate detection by stable fingerprint where appropriate;
- persistence under `.kodepoia/diagnostics/technical_debt/` or another plan-approved governed location;
- structured report/schema;
- health `technical_debt` observation adapter;
- regression behavior for newly introduced blocking debt.

## Out of scope

- automatic code rewriting to remove all debt;
- dependency licensing/BOM (R6.11);
- architecture changes without ADR;
- arbitrary static-analysis command execution from model text.

## Expected implementation

- `src/kodepoia/quality/technical_debt.py`;
- schema and focused tests;
- debt-store persistence through `WorkspaceBoundary`;
- optional ingestion adapters for known Kodepoia diagnostics, never arbitrary shell commands;
- design/acceptance docs.

## Acceptance gates

Stable IDs, lifecycle validation, deterministic ranking, explicit accepted-debt state, WorkspaceBoundary confinement, Health integration, serialization tamper checks, full CI and merge.

## Manual intervention

**NONE.** The foundation can be accepted using deterministic fixtures and repository data.

## Rollback / risks

Do not treat accepted debt as resolved. Do not allow changing severity/rationale without evidence/history. Avoid unstable fingerprints that duplicate every run.

---

# R6.8 — KodeCI + KodeBuild foundation

## Objective and rationale

Turn the existing repository workflows into a structured CI/build contract that produces reproducible evidence consumable by KodeHealth, KodeTests, KodeRegression and later release tooling.

## In scope

- normalized CI check identities and statuses;
- deterministic build manifest (source SHA, Python version, platform, dependency inputs, produced artifacts/hashes);
- Python package build validation for current Kodepoia;
- Windows + Ubuntu build/test matrix;
- artifact hash evidence;
- failed/cancelled/skipped distinction;
- integration of lint/compile/tests/regression/security/visual hooks as they become available;
- no secrets in logs/manifests;
- persistence under `.kodepoia/workflows/` and `.kodepoia/releases/` for project-managed evidence where applicable;
- repository workflow updates without disabling existing R0/Python/UI gates.

## Out of scope

- store publishing;
- code signing with user certificates;
- installers/update channels (later release phases);
- macOS/iOS build claims from Windows/Ubuntu CI;
- generated application framework builds belonging to R12+.

## Expected implementation

- `src/kodepoia/quality/ci.py` and/or `src/kodepoia/build/` only if consistent with existing package layout;
- build manifest schema;
- deterministic package build tests;
- workflow updates kept minimal and auditable;
- focused acceptance docs.

## Acceptance gates

- source SHA/artifact hash manifest reproducible for same inputs where byte reproducibility is technically supported, otherwise deterministic normalized metadata with the non-reproducible field explicitly documented;
- Windows + Ubuntu package build succeeds;
- existing test/regression/visual hooks represented without weakening gates;
- cancelled/skipped jobs cannot count as PASS;
- secrets redaction verified;
- final-head workflows all green;
- merge/post-merge normalization.

## Manual intervention

**CONDITIONAL.**

### Trigger condition

User-side local execution is required only if GitHub-hosted Windows CI cannot authoritatively reproduce a Windows-specific build behavior/artifact needed by the R6.8 DoD, or if a runner limitation produces evidence that differs from the accepted local Windows environment.

### Planned local command contract if triggered

```powershell
git fetch origin
git checkout <R6_8_ACCEPTED_HEAD>
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,ui,code]"
powershell -ExecutionPolicy Bypass -File .\scripts\r6_8_accept_local.ps1
```

### Expected output

Build manifest JSON, source SHA, Python version, platform, artifact names/sizes/hashes, test status and `acceptance_completed=true` with zero blocking failures.

### Failure recovery / evidence

Preserve the manifest/logs and report the exact failing build step. Do not manually edit artifact hashes or copy an artifact from a different SHA. Send the generated manifest and terminal summary only; redact secrets.

### Do not do yet

If the conditional gate triggers, do not merge R6.8 until the local result is reviewed.

## Rollback / risks

Workflow changes must not accidentally remove checks, narrow platform coverage or create self-referential acceptance. Build evidence must remain tied to exact source SHA.

---

# R6.9 — KodeAppSecurity baseline

## Objective and rationale

Create a platform-aware security baseline for products Kodepoia creates and for Kodepoia's own applicable surfaces. The frozen architecture requires threat modeling, input/auth/network validation, dependency security, secure storage and useful fuzzing where appropriate.

OWASP ASVS 5.0.0 is a current external requirement catalogue for applicable web/API/auth/security controls, but non-web projects only receive relevant controls.

## In scope

- structured threat model: assets, trust boundaries, entry points, threats, mitigations, residual risk;
- stable security requirement/check IDs;
- input/path/network/auth/session controls only when the target actually has those surfaces;
- dependency vulnerability evidence adapter with provenance and timestamp;
- secure-storage expectation checks for secrets/config where applicable;
- deterministic fuzz/property tests for parsers/structured inputs where useful;
- report/schema and Health `security` adapter;
- persistence under `.kodepoia/diagnostics/security/` or plan-approved governed storage;
- no remote mandatory security SaaS.

## Out of scope

- penetration testing against third-party systems;
- exploit development;
- store compliance certification;
- cloud auth/backend implementation belonging to later phases.

## Acceptance gates

Threat-model completeness on fixtures, platform applicability, no false requirements for absent auth/network surfaces, blocking security failures represented in Health, dependency evidence timestamp/provenance, no arbitrary scanner command injection, full CI green and merge.

## Manual intervention

**NONE.** Foundation acceptance uses controlled fixtures/repository surfaces and does not require testing a private external service or credentialed production environment.

## Rollback / risks

Security checks must fail closed for malformed evidence, but `not_applicable` must remain distinct from PASS. Do not log secrets or vulnerability-scan private credentials.

---

# R6.10 — KodePrivacy baseline

## Objective and rationale

Establish a structured data inventory and lifecycle model so generated products can state what data they collect/store, why, how long, where it lives, how it is deleted and what declarations are required.

## In scope

- stable data-category IDs;
- source, purpose, legal/consent basis placeholder fields where applicable, storage location, recipients, retention, deletion mechanism, sensitivity and project/platform scope;
- explicit `none`/`not_applicable` instead of missing data;
- privacy issue severity/status;
- report/schema and Health `privacy` adapter;
- store-declaration preparation fields without pretending final store submission;
- deletion/retention fixture tests;
- persistence under `.kodepoia/diagnostics/privacy/` or another governed path.

## Out of scope

- legal advice;
- automatic claim of GDPR/CCPA/etc. compliance;
- store submission;
- remote analytics implementation.

## Acceptance gates

Inventory completeness validation, explicit purpose/retention/deletion fields, no secret values stored in privacy reports, platform-aware declarations, Health integration, full CI and merge.

## Manual intervention

**NONE.** The foundation is a structured inventory/control system. Future product-specific legal/store review may require humans but is outside R6.10 acceptance.

## Rollback / risks

Never infer consent/legal basis from silence. Never put raw personal data into diagnostic evidence merely to prove a category exists.

---

# R6.11 — KodeLicense + KodeBOM foundation

## Objective and rationale

Establish provenance, license normalization and BOM generation for Kodepoia dependencies/assets so later build/release phases can make auditable compliance decisions.

SPDX 3.0 is the stable external BOM baseline for R6 acceptance. Pre-release SPDX 3.1 material may be evaluated experimentally but must not become the authoritative format during R6 without an explicit recorded update after stable release.

## In scope

- normalized component identity/version/source/hash fields;
- SPDX license expressions where known;
- `NOASSERTION`/unknown state handling without converting uncertainty into approval;
- dependency and asset provenance records;
- license-policy results: allow/warn/deny/unknown according to explicit project policy;
- BOM generation for current Kodepoia Python dependencies and deterministic fixtures;
- report/schema validation;
- `.kodepoia/licenses/` and `.kodepoia/bom/` persistence through `WorkspaceBoundary`;
- Health `licenses` and `dependencies` observation adapters;
- compatibility hooks for later release tooling.

## Out of scope

- legal determination of ambiguous custom licenses;
- automatically granting rights for user-provided assets;
- downloading license texts from arbitrary untrusted locations as executable instructions;
- store publishing.

## Expected implementation

- `src/kodepoia/quality/licenses.py` and `src/kodepoia/quality/bom.py` or a cohesive equivalent;
- SPDX 3.0-compatible generation/normalization layer sufficient for the R6 scope;
- schemas and focused tests;
- provenance/tamper checks;
- design/acceptance docs.

## Acceptance gates

Known dependency fixture → correct normalized component/license record; unknown/custom license stays unresolved; hash/provenance retained; duplicate component handling deterministic; BOM round-trip/schema validation; no path escape; Health integration; CI green and merge.

## Manual intervention

**CONDITIONAL.**

### Trigger condition

Manual input is required only when authoritative acceptance encounters a component/asset whose license or provenance cannot be established from repository metadata, package metadata or a trusted source, and the item is required for the R6.11 fixture/acceptance path.

### Exact user action if triggered

Do not guess the license. Provide one of the following for the exact component identified by R6.11:

1. the authoritative source page/file containing the license/provenance statement; or
2. if it is a user-created/user-owned asset, a short explicit provenance statement naming the asset and confirming ownership/permission for the intended project use.

Then run the planned resolver against that exact component:

```powershell
.\.venv\Scripts\Activate.ps1
python -m kodepoia.cli license-audit --project <PROJECT_PATH> --component <COMPONENT_ID> --output .kodepoia\licenses\manual-resolution.json
```

The command name/arguments are part of the intended R6.11 contract and must exist before the conditional gate can be invoked.

### Expected output

A structured component record with provenance source, normalized license status, evidence hash and no unresolved blocking field for the acceptance fixture.

### Failure recovery

If the license remains unclear, keep the item `unknown`/blocking according to policy. Do not invent an SPDX identifier or paste a third-party license from an unrelated package.

### Evidence to send back

Send the authoritative source reference/provenance statement plus the generated `manual-resolution.json`. Redact account tokens or unrelated personal data.

### Do not do yet

Do not approve/release the unresolved component or mark R6.11 COMPLETE until the ambiguity is resolved or the component is explicitly removed from the acceptance scope by recorded decision.

## Rollback / risks

License policy changes must be explicit and versioned. BOM generation must not silently omit transitive/runtime components it claims to cover.

---

# R6.12 — Major-patch validation + rollback gate and R6 integration acceptance

## Objective and rationale

Satisfy the frozen-roadmap rule that every major patch has validation and rollback. R6.12 turns R6.1–R6.11 into an enforceable cross-cutting gate rather than a collection of disconnected tools, then performs final R6 integration acceptance.

## In scope

- deterministic definition/classification of a `major patch` based on affected scope/risk rather than model opinion;
- patch manifest tied to source/base/head SHAs;
- required validation matrix derived from changed domains: tests, regression, visual, accessibility, localization, debt, build, security, privacy, license/BOM, health/budget as applicable;
- explicit rollback strategy requirement before major patch acceptance;
- SafeChange snapshot requirement for sensitive mutable project changes;
- rollback rehearsal on controlled fixtures;
- refusal to accept missing/partial required evidence;
- final integrated R6 acceptance fixture demonstrating the full gate;
- R6 completion report that enumerates all R6.1–R6.12 evidence.

## Out of scope

- R7 Research implementation;
- release-channel updater implementation beyond proving rollback contract;
- destructive production rollback tests;
- weakening Guardian approval requirements.

## Expected implementation

- `src/kodepoia/quality/patch_gate.py` or equivalent governed orchestrator component;
- major-patch manifest/report schema;
- tests covering classification, evidence requirements, missing evidence, failed rollback and successful controlled rollback;
- orchestrator integration only through existing protected boundaries;
- `scripts/r6_12_accept_local.ps1` only if a hardware/local conditional gate is triggered;
- `docs/roadmap/R6_12_ACCEPTANCE.md` and final R6 status/continuity normalization.

## Acceptance gates / Definition of Done

1. major/minor classification deterministic and test-covered;
2. a major patch cannot PASS without an explicit rollback plan;
3. required evidence is selected by changed domains/platform targets, not universally imposed on irrelevant platforms;
4. missing/skipped/cancelled required checks block acceptance;
5. rollback rehearsal on controlled fixture restores expected state and verifies hashes;
6. SafeChange/Audit integration used where mutation is sensitive;
7. no arbitrary model-supplied shell command/path fields introduced;
8. all R6.1–R6.11 focused and regression suites remain green;
9. final R0/Python Core/KodeStudio checks green on final head;
10. any triggered manual/hardware-local gate completed;
11. PR merged and post-merge normalization records R6.1–R6.12 as COMPLETE;
12. only then may R6 itself become COMPLETE and R7 planning start.

## Manual intervention

**CONDITIONAL.**

### Trigger condition

Manual execution is required if the selected final integration fixture exercises a hardware-local capability that hosted CI cannot authoritatively reproduce (for example the R6.4 real-render visual path), or if a major-patch policy explicitly requires user approval for a sensitive local operation under Guardian/PermissionSet.

### Planned command contract if triggered

```powershell
git fetch origin
git checkout <R6_12_ACCEPTED_HEAD>
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,ui,code]"
powershell -ExecutionPolicy Bypass -File .\scripts\r6_12_accept_local.ps1
```

The script must not ask for arbitrary command strings. It must execute only predefined governed acceptance operations.

### Expected output

- exact base/head SHA;
- major-patch classification and reasons;
- required gate list;
- each gate PASS with evidence path/ID;
- rollback plan ID;
- snapshot/rollback rehearsal evidence when applicable;
- AuditLog chain verification where applicable;
- `failed=0` and `acceptance_completed=true`.

### Failure recovery

If rollback rehearsal fails, stop immediately and preserve the pre-test snapshot/evidence. Do not repeatedly mutate the same fixture without restoring a known state. If a required gate is unavailable, R6.12 remains incomplete rather than downgrading that gate.

### Evidence to send back

Complete terminal summary plus final integration JSON report and any specifically requested local report from the triggered hardware gate. Redact secrets.

### Do not do yet

Do not mark R6 COMPLETE, start R7 planning, or merge the final implementation PR until the triggered local evidence and all authoritative CI are accepted.

## Rollback / risks

The final gate itself must be revertible and must never become a mechanism for bypassing Guardian, SafeChange or existing CI. Beware circular validation where the patch gate accepts its own summary without verifying underlying evidence.

---

# Manual-intervention forecast for the remainder of R6

The user must be told early about these expected gates:

- **R6.4 — REQUIRED:** one real Windows/Godot rendered visual-regression acceptance run on the accepted workstation.
- **R6.5 — REQUIRED:** one real interactive Windows keyboard-only + Narrator accessibility checklist.
- **R6.8 — CONDITIONAL:** local Windows build evidence only if GitHub-hosted CI cannot authoritatively satisfy the build/reproducibility DoD.
- **R6.11 — CONDITIONAL:** provenance/license input only if an acceptance-critical component remains ambiguous after trusted metadata/source resolution.
- **R6.12 — CONDITIONAL:** local integration/approval only if the final major-patch fixture selects a hardware-local or user-approval-required gate.

No manual intervention is currently planned for R6.6, R6.7, R6.9 or R6.10.

When each manual subdivision is reached, the exact accepted head SHA and any final implementation-specific command details must be inserted into its acceptance document before the user is asked to run anything.

# R6 completion rule

R6 is COMPLETE only when:

1. R6.1 through R6.12 are all COMPLETE with their required evidence;
2. no required manual gate remains pending;
3. the final R6.12 integration gate passes;
4. R0 Repository Guard, Python Core Windows + Ubuntu and KodeStudio UI Smoke are successful on the final implementation head;
5. the final implementation PR is merged;
6. post-merge `R6_STATUS.md`, this `R6_PLAN.md` and `KODEPOIA_CONTINUITY.md` are synchronized on normalized `main`;
7. only after that may R7 planning begin under the permanent phase-start planning rule.

# Change log for this plan

- 2026-08-22: retroactive plan created by explicit user request before R6.4. R6.1–R6.3 recorded from already accepted evidence; R6.4–R6.12 structure frozen for the remainder of R6.
