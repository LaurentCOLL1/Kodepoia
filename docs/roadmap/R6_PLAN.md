# Kodepoia — R6 detailed phase plan

**Phase:** R6  
**Roadmap title:** Quality / Health / Budget / CI  
**Status:** IN PROGRESS — PLAN ACCEPTED  
**Phase started:** 2026-08-22  
**Plan reconstructed:** 2026-08-22 by explicit user request after R6.1–R6.3 had already been accepted  
**Plan accepted:** 2026-08-22  
**Accepted planning head:** `8fbad7c13dd65f9dcd49a03b33a3174fcf28d18a`  
**Planning PR:** #37  
**Planning merge:** `0a91064608507966a47921df8fb36e5f25477141`  
**Architecture:** v1.0 frozen  
**Source of truth:** normalized `main`

## Purpose and authority

This file is the exhaustive execution/recovery plan for R6 and is authoritative together with `R6_STATUS.md`, subdivision acceptance documents and `docs/continuity/KODEPOIA_CONTINUITY.md`. The R6.1–R6.12 structure is frozen: no subdivision may be silently added, removed, merged, split or renumbered.

R6 may be marked COMPLETE only when every R6.N is COMPLETE with required evidence, every REQUIRED or triggered CONDITIONAL manual gate is satisfied, R6.12 integrated acceptance passes, implementation and normalization are merged, and plan/status/continuity agree on normalized `main`.

## Permanent phase-wide governance

Every R6 subdivision must preserve:

- `WorkspaceBoundary` confinement and symlink-escape rejection;
- `ProcessSandbox` plus global KillSwitch for execution;
- Guardian + `PermissionSet` authorization/risk gates;
- structured Tool APIs, never arbitrary model-provided command/argv/cwd/host;
- SafeChange snapshots before sensitive mutations where required;
- AuditLog tamper-evident hash chain for governed sensitive operations;
- Secrets redaction/exclusion and OS-backed secret handling;
- schema/DataGovernance versioning and exact-head evidence;
- explicit UNKNOWN/N/A semantics: silence, skipped checks and non-applicable evidence never manufacture PASS;
- platform-aware behavior: non-target platforms do not create requirements;
- local-first/offline-capable operation for configured projects;
- ADR requirement for foundation-level architecture change;
- test-before-trust and rollback/recovery for major patches.

Persistent R6 project evidence belongs under initialized `.kodepoia/` roots and must be resolved through `WorkspaceBoundary`.

## External-reference baselines

- Accessibility: WCAG 2.2 criteria where applicable; WCAG2ICT 2.2 is informative context for non-Web desktop software; no universal certification claim.
- Localization: Unicode CLDR is reference context only; no universal locale coverage claim.
- CI/Build provenance: SLSA v1.2 reference context only; no SLSA level claimed.
- AppSecurity: OWASP ASVS 5.0.0 used only as applicable-control catalogue; no global ASVS certification.
- Privacy: GDPR principles + Apple/Google declarations used only as structured-evidence context; no legal conclusion.
- BOM/licenses: SPDX 3.0 family remains frozen baseline. Patch-level interoperability reference rechecked 2026-08-22 is 3.0.1. CycloneDX 1.7 is optional stable interoperability context, not replacement baseline.

## Complete subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R6.1 | KodeHealth foundation | COMPLETE | NONE | R5 COMPLETE |
| R6.2 | KodeBudget foundation | COMPLETE | NONE | R6.1 |
| R6.3 | KodeTests + KodeRegression foundation | COMPLETE | NONE | R6.1–R6.2 |
| R6.4 | KodeVisualQA foundation | COMPLETE | REQUIRED — SATISFIED | R6.1–R6.3 + R5 Godot automation |
| R6.5 | KodeAccessibility foundation | COMPLETE | REQUIRED — SATISFIED | R6.3–R6.4 |
| R6.6 | KodeLocalization + pseudo-localization foundation | COMPLETE | NONE | R6.3 + R6.5 |
| R6.7 | KodeTechnicalDebt foundation | COMPLETE | NONE | R6.1–R6.6 |
| R6.8 | KodeCI + KodeBuild foundation | COMPLETE | CONDITIONAL — NOT TRIGGERED | R6.1–R6.7 |
| R6.9 | KodeAppSecurity baseline | COMPLETE | NONE | R6.3 + R6.7–R6.8 |
| R6.10 | KodePrivacy baseline | COMPLETE | NONE | R6.7–R6.9 |
| R6.11 | KodeLicense + KodeBOM foundation | COMPLETE | CONDITIONAL — NOT TRIGGERED | R6.7–R6.10 |
| R6.12 | Major-patch validation + rollback gate and R6 integration acceptance | NEXT / NOT STARTED | CONDITIONAL | R6.1–R6.11 |

---

# R6.1 — KodeHealth foundation — COMPLETE

## Objective / accepted scope

Provide one deterministic health model spanning the 14 architecture dimensions: build, tests, warnings, security, dependencies, performance, memory, assets, audio, accessibility, localization, technical debt, licenses and privacy. Preserve `unknown/pass/warn/fail`, score, coverage and blockers without pretending unmeasured dimensions are healthy.

## Accepted implementation

- exhaustive dimension enum and validated HealthMetric/HealthReport contract;
- deterministic aggregation and complete/incomplete coverage semantics;
- blocker propagation;
- JSON round-trip and derived-field tamper rejection;
- atomic latest + snapshot persistence through `WorkspaceBoundary`;
- schema `health-report-v1`.

Evidence: head `802de4ba3110ace657c4e16306a0ca29850ce2bd`; PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`; R0 `32561211168`, Python Core `32561211156`, UI Smoke `32561211167` SUCCESS.

Manual: **NONE**. Anti-regression: unknown coverage and all 14 dimensions must remain explicit.

---

# R6.2 — KodeBudget foundation — COMPLETE

## Objective / accepted scope

Create per-platform technical budgets for FPS/frame-time, CPU/GPU, RAM/VRAM, storage, draw calls, polygons, textures, audio memory/voices, build size, mobile battery/thermal and online network. Distinguish target from hard limit and never invent missing budgets.

## Accepted implementation

- typed metrics/directions/statuses/constraints/observations/results;
- Project DNA derivation only for configured target platforms;
- target miss→WARN, hard breach→FAIL, blocking breach→blocker;
- configured-but-unmeasured→UNKNOWN/reduced coverage;
- no collector/process execution path in the foundation;
- atomic project-confined persistence and schema.

Evidence: head `8ac3772e98c70260c320519a214bb25b6cedbb38`; PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`; R0 #603, Python Core #577, UI #544 SUCCESS.

Manual: **NONE**. Anti-regression: later collectors must preserve target-platform and unknown semantics.

---

# R6.3 — KodeTests + KodeRegression foundation — COMPLETE

## Objective / accepted scope

Normalize test evidence and compare baseline/current results by stable case ID so removed/skipped/failing cases cannot manufacture a regression-free result.

## Accepted implementation

- test case pass/fail/error/skip + run unknown/pass/warn/fail;
- unique IDs, duration/count validation and tamper-resistant serialization;
- regression changes unchanged/regressed/fixed/added/removed;
- FAIL/ERROR→SKIP remains regression; removed case is regression; new failing case is regression;
- report stores through WorkspaceBoundary;
- no second arbitrary test execution path.

Evidence: head `7150237c263dd3ac96af4662d74909e05f3cf991`; PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`; R0 #622, Python #596, UI #563 SUCCESS.

Manual: **NONE**.

---

# R6.4 — KodeVisualQA foundation — COMPLETE

## Objective / accepted scope

Provide deterministic visual regression with immutable content-addressed baselines, exact/pixel/perceptual evidence, mask/policy hashes, PNG diffs, anti-tamper reports and governed real Godot rendering.

## Accepted implementation/evidence

- immutable baseline approval + compare report;
- masks/policies included in evidence hashes;
- R6.3 hooks and WorkspaceBoundary stores;
- real-render Godot PNG capture preserving R5 AVI path and R5 safety constraints;
- accepted head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`;
- PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`; normalization #40 `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`;
- hosted gates SUCCESS plus required Windows/Godot/Radeon gate `8 PASS / 0 FAIL / 8`.

Manual: **REQUIRED — SATISFIED**. Anti-regression: no auto-baseline replacement or headless substitute when real rendering is required.

---

# R6.5 — KodeAccessibility foundation — COMPLETE

## Objective / accepted scope

Create structured accessibility evidence with applicability/N/A, canonical evidence hashing, KodeStudio/Project Wizard checks, Qt accessibility inspection, keyboard focus audit and Windows assistive-technology evidence.

Evidence: head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`; PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`; normalization #42 `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`; hosted gates SUCCESS; manual Windows accessibility `15 PASS / 0 FAIL / 15`.

Manual: **REQUIRED — SATISFIED**. N/A never becomes PASS; wrong-SHA/offscreen evidence cannot replace required real evidence.

---

# R6.6 — KodeLocalization + pseudo-localization foundation — COMPLETE

## Objective / accepted scope

Stable message IDs/forms, missing/extra/form/placeholder evidence, explicit fallback, deterministic `qps-ploc`, protected placeholders/markup/entities, anti-tamper report and KodeStudio pseudo-localized smoke while English stays production default.

Evidence: head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`; R0 #733, Python #707, UI #674 SUCCESS.

Manual: **NONE**. Anti-regression: pseudo-locale never production default; missing forms/placeholders remain explicit.

---

# R6.7 — KodeTechnicalDebt foundation — COMPLETE

## Objective / accepted scope

Persistent debt register with stable IDs, category/severity/impact/probability/effort, OPEN/ACCEPTED/RESOLVED lifecycle, rationale/history, deterministic priority/fingerprint, canonical report, Health/R6.3 adapters and project confinement.

Evidence: head `0da49c7526b54f562827d63477b7ce8f1865de43`; PR #45 merge `3986b056654b25a73e45e5135ca3110a920c4bf5`; normalization #46 `fc7bd4d5803c451b4d343d08bcc212868ad24412`; R0 #756, Python #730, UI #697 SUCCESS.

Manual: **NONE**. Accepted debt is not resolved debt; blockers cannot disappear through fingerprint changes.

---

# R6.8 — KodeCI + KodeBuild foundation — COMPLETE

## Objective / accepted scope

Bind CI/build evidence to exact source SHA and artifact/source/dependency digests; build wheel+sdist manifests; reject skipped/cancelled/missing required checks; validate package structure and add Windows+Ubuntu package-build jobs with fixed governed commands.

Evidence: head `d632669b93fda7b8397b9c3de43d78ca8726323f`; PR #47 merge `d570a3930ee63802882b8682e4532004d4fd81d6`; R0 #783, Python #757 five jobs, UI #724 SUCCESS; package artifacts inspected; normalization #48 `92effbde1e432a8fcb6c794038d77367d034bcb0`; wording #49 `616899291fc3b4dc40695415a5008d6fdd599230`.

Manual: **CONDITIONAL — NOT TRIGGERED**. Anti-regression: package builds stay exact-SHA-bound and no arbitrary model build command/path is introduced.

---

# R6.9 — KodeAppSecurity baseline — COMPLETE

## Objective / accepted scope

Typed threat model, applicable/N/A security requirements, evidence provenance, dependency vulnerability evidence, secure-storage observations, secret redaction, canonical report, Health/R6.3 adapters and WorkspaceBoundary persistence. OWASP ASVS references are versioned applicable-control context only.

Key semantics: residual risk defaults UNKNOWN; N/A never PASS; measured PASS/WARN/FAIL requires evidence; affected dependency blocks; no unrestricted security scanner/process/network path.

Evidence: head `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`; R0 #812, Python #786 five jobs, UI #753 SUCCESS; PR #50 merge `f5c135edf0be464a02b4b46d67c14e665f236009`; normalization #51 `4df229e431d2d54e4268607f38bac4045ac590d1`.

Manual: **NONE**.

---

# R6.10 — KodePrivacy baseline — COMPLETE

## Objective / accepted scope

Structured local-first privacy inventory/lifecycle evidence: collected/none/N/A, source/purpose/storage/recipients/retention/deletion, sensitivity, explicit legal/consent-basis placeholder state, privacy issues, Apple/Google declaration preparation, redaction, canonical evidence and Health/R6.3 integration without legal conclusions.

Hardening semantics: `inventory_complete=true` needs review provenance; incomplete inventory WARN; N/A score-neutral; all-N/A UNKNOWN; N/A declaration SKIP; no personal data fixture required; no remote privacy SaaS/store submission.

Evidence: head `e9363e0e00f592b39a7a094b7520b3d515fb02f0`; R0 #844, Python #818 five jobs, UI #785 SUCCESS; PR #52 merge `cefc60266cb191cf0ee5a099e0d8923a2f14745a`; normalization #53 `36524978a963d8c759d36902bc1ab00989da0549`.

Manual: **NONE**.

---

# R6.11 — KodeLicense + KodeBOM foundation — COMPLETE

## Objective

Establish auditable component provenance, BOM generation and license evidence/policy so future build/release work can make evidence-based decisions without inventing exact versions, license IDs or legal compatibility.

## Accepted deliverables

- `BomComponent` project/package/asset identity with stable ID;
- resolution `resolved/unresolved/not_applicable`, exact version only when resolved;
- purl, source locator, provenance, manifest/source SHA-256 and requirement-group evidence;
- integrity `recorded/mismatch/unknown/not_applicable`; recorded ≠ independently verified; mismatch blocks;
- strict N/A coupling: N/A component requires N/A integrity, applicable component forbids it, all-N/A=UNKNOWN, N/A excluded from scoring/decisions/SPDX packages and R6.3=SKIP;
- optional declared + mandatory concluded license evidence;
- `SPDX_EXPRESSION/NOASSERTION/NONE`, with rationale/provenance for NOASSERTION/NONE;
- standalone `LicenseRef-*` custom text hash; composite expression cannot own one custom-text hash;
- lexical SPDX normalization/guarding without claiming full official parser/list/ontology validation;
- deterministic `KodeBOM.from_pyproject()` using `tomllib` + WorkspaceBoundary, collecting build-system/runtime/all optional dependency groups;
- normalized duplicate package merge while retaining every requirement/group;
- version ranges stay unresolved; current web metadata is never copied onto an unresolved range;
- exact-expression LicensePolicy ALLOW/WARN/DENY/UNKNOWN; default ALLOW forbidden; only DENY blocks;
- canonical BOM + License reports, counts/blockers/status/score, policy fingerprint and SHA-256 anti-tamper checks;
- SPDX family baseline 3.0; patch-level interoperability reference 3.0.1 + JSON-LD context; compact view has `conformance_claim=false`;
- `bom-report-v1` + `license-report-v1` schemas;
- `.kodepoia/bom/` and `.kodepoia/licenses/` atomic stores through WorkspaceBoundary;
- Health dependencies/licenses adapters and stable R6.3 cases;
- real Kodepoia pyproject test proving truthful WARN for unresolved dependency ranges;
- no shell, installer, scanner, arbitrary remote fetch, license-page instruction execution or publisher.

## Review hardening

Initial diagnostic `5d76ba98f0fc715f2e672fc27cc1b99fc015bc8e` was green but review found possible false PASS from N/A. Hardened diagnostic `ad19f69d1d706db657be809698395a2340ec779c` made N/A neutral/UNKNOWN/SKIP and tightened LicenseRef hashing. Both hardened code and schemas/tests passed hosted gates.

Two transient branch-only tool mistakes during evidence handling were fully reverted before final acceptance; final diff contained only nine intended R6.11 files.

## Final evidence

- starting normalized main `36524978a963d8c759d36902bc1ab00989da0549`;
- accepted net-clean head `d0590ed3eda663ad713fc36d962c8dac1df109eb`;
- R0 #885 / `32578903951` SUCCESS Windows+Ubuntu;
- Python Core #859 / `32578903981` SUCCESS all five jobs;
- UI Smoke #826 / `32578903942` SUCCESS Windows;
- PR #54 merged with `expected_head_sha=d0590ed3eda663ad713fc36d962c8dac1df109eb` as `248b1331fe2b26229b932c36aefb83c70065c52a`.

Manual: **CONDITIONAL — NOT TRIGGERED**. A future manual license conclusion is required only if an acceptance-critical real component needs a precise conclusion and trusted authoritative evidence remains ambiguous.

Anti-regression: never infer exact versions/licenses, treat N/A/NOASSERTION/NONE as PASS/ALLOW, call recorded hashes verified, weaken blockers/provenance/WorkspaceBoundary, or claim legal/SPDX conformance.

---

# R6.12 — Major-patch validation + rollback gate and R6 integration acceptance — NEXT / NOT STARTED

## Objective

Make the frozen-roadmap rule **“tout patch majeur doit avoir validation et rollback”** enforceable, then run integrated R6 acceptance and close R6 only when every required evidence source is coherent and exact-head bound.

## Dependencies

R6.12 depends on accepted R6.1–R6.11 and must start only from normalized `main` after this R6.11 post-merge normalization is CI-green and merged. It must consume existing R6 reports rather than replace them.

## Required implementation scope

### 1. Deterministic patch classification

Create typed changed-domain evidence and deterministic major/minor classification. Classification must derive from changed scope/risk signals such as protected-core/security/governance/schema/public API/build/release/platform/large migration/destructive change, not from an unconstrained LLM opinion. The report must explain which rule triggered major classification. Unknown classification evidence fails closed for acceptance-critical patches.

### 2. Exact base/head manifest

Every patch gate must bind to exact non-empty base SHA and head SHA and reject equality, malformed SHAs or evidence produced for another head. Changed paths/domains and platform targets must be canonicalized and deduplicated.

### 3. Validation matrix selection

Select required gates from changed domains/platforms. The matrix may include as applicable:

- KodeTests + KodeRegression;
- KodeVisualQA;
- KodeAccessibility;
- KodeLocalization/pseudo-localization;
- KodeTechnicalDebt;
- KodeCI/KodeBuild/package manifests;
- KodeAppSecurity;
- KodePrivacy;
- KodeLicense/KodeBOM;
- KodeHealth dimensions;
- KodeBudget observations;
- platform-specific/manual evidence only when the affected domain truly requires it.

A required gate may not be silently downgraded to optional. Missing, fail, error, skipped or cancelled required evidence blocks patch acceptance. N/A is permitted only with explicit applicability rationale and may not become PASS.

### 4. Mandatory rollback contract for major patches

Every major patch must carry an explicit rollback strategy describing:

- scope/state to restore;
- snapshot/backup/checkpoint mechanism;
- expected pre-change hashes or state identifiers;
- controlled restore/recovery procedure;
- post-rollback verification;
- audit provenance;
- limitations and conditions where rollback must not run automatically.

A major patch without rollback strategy cannot PASS even when all tests are green.

### 5. Reuse existing safety/recovery primitives

Do **not** create a parallel rollback engine. Reuse and compose:

- `SafeChangeManager` for project-confined snapshots of sensitive mutable paths;
- `BackupManager` for verified archive creation/restore where a full fixture backup is appropriate;
- `RecoveryJournal` for atomic checkpoint/resume state;
- `AuditLog` for append-only tamper-evident patch/rollback events;
- `WorkspaceBoundary`, Guardian and PermissionSet for path/action authorization;
- existing test/regression/health/build evidence stores.

If an existing primitive lacks a narrowly required capability, extend it compatibly with tests rather than bypass it. Foundation-level semantic change requires ADR.

### 6. Controlled rollback rehearsal

Provide a deterministic temporary project fixture that:

1. records original files/hashes;
2. creates required snapshot/backup/checkpoint;
3. applies a representative controlled mutation through allowed test code;
4. executes rollback/recovery in the fixture only;
5. verifies restored file set/content/hashes and audit chain;
6. fails closed on corrupt snapshot/archive, path escape, wrong evidence SHA or incomplete restoration.

Never rehearse destructive rollback against the real repository, user project or production environment.

### 7. Major-patch gate report

Add a versioned canonical report/schema containing at minimum:

- base/head SHAs;
- classification and triggering rules;
- changed domains/platforms;
- required validation matrix;
- underlying evidence IDs/digests/statuses;
- rollback plan/evidence/rehearsal status;
- SafeChange/Backup/Recovery/Audit references when used;
- blockers;
- deterministic overall UNKNOWN/PASS/WARN/FAIL or equivalent gate status;
- canonical evidence SHA-256 with derived-field tamper rejection.

Persist project evidence only within an initialized `.kodepoia/` location through WorkspaceBoundary.

### 8. Integrated R6 acceptance report

Build an integration fixture/report that enumerates R6.1–R6.12 evidence and proves that final R6 status is not derived from prose alone. It must detect:

- missing subdivision evidence;
- stale/wrong-source SHA evidence;
- required manual gate not satisfied;
- blocker in any required R6 domain;
- tampered report hash/count/status;
- skipped/cancelled required CI/build evidence;
- incomplete rollback evidence for a major patch.

R6 integrated PASS requires all mandatory R6.1–R6.12 evidence to be accepted according to each subdivision's semantics.

## Expected deliverables

- patch classification/gate module(s) under the existing Quality/protected architecture;
- report/schema v1 for patch gate and, if separate, R6 integrated acceptance;
- adapters to existing Health/R6.3 where useful without duplicating evidence;
- focused tests covering major/minor, domain selection, wrong SHA, missing/skipped/cancelled evidence, rollback-required semantics, path escape, corrupted backup/snapshot, restore hash verification, AuditLog verification and report tamper rejection;
- controlled temp-fixture rollback rehearsal;
- `docs/roadmap/R6_12_DESIGN.md` and `R6_12_ACCEPTANCE.md`;
- updates to R6_STATUS/PLAN/continuity while IN PROGRESS;
- exact-final-head hosted CI evidence;
- implementation merge + post-merge final R6 normalization.

## Acceptance criteria

1. deterministic major/minor classification with explainable rules;
2. exact base/head SHA binding;
3. required gates selected by relevant domains and target platforms;
4. major patch cannot PASS without rollback strategy;
5. missing/failed/skipped/cancelled required evidence blocks;
6. controlled rollback restores expected state and hashes;
7. SafeChange/Backup/Recovery/Audit reused where applicable and their integrity verified;
8. no arbitrary model command/path/host/process/network field and no Guardian bypass;
9. all R6.1–R6.11 regression suites remain green;
10. integrated R6 report validates every required subdivision and rejects stale/tampered evidence;
11. final R0 Repository Guard Windows+Ubuntu SUCCESS;
12. final Python Core SUCCESS on both cores, integrated Windows UI and both package-build jobs;
13. final KodeStudio UI Smoke SUCCESS Windows;
14. every REQUIRED or triggered CONDITIONAL manual gate is satisfied;
15. implementation PR merged on exact accepted head;
16. post-merge normalization CI-green and merged;
17. only then may R6_STATUS become COMPLETE and R7 planning begin.

## Manual intervention

**CONDITIONAL.** Do not trigger merely because R6.12 deals with rollback. Prefer hosted Windows/Ubuntu and temporary project fixtures. User intervention becomes required only if an acceptance-critical selected gate genuinely needs local hardware/capability unavailable to hosted CI, or Guardian policy requires explicit human approval for a real sensitive operation. If triggered, the final-head acceptance document must first provide reason, prerequisites, exact commands/actions, expected output, recovery, evidence to return and what not to do.

## Failure recovery / anti-regression

- no destructive rehearsal on real project/repository;
- no self-certified gate that trusts only its own summary;
- validate referenced underlying evidence/digests;
- no missing/skipped required gate converted to PASS;
- no rollback plan accepted without verified restore evidence where rehearsal is required;
- no parallel unrestricted snapshot/restore implementation;
- preserve WorkspaceBoundary/Guardian/SafeChange/Audit and exact-head discipline;
- do not mark R6 COMPLETE or start R7 from partial CI.

---

# Manual-intervention forecast

- R6.1 NONE — COMPLETE.
- R6.2 NONE — COMPLETE.
- R6.3 NONE — COMPLETE.
- R6.4 REQUIRED — SATISFIED.
- R6.5 REQUIRED — SATISFIED.
- R6.6 NONE — COMPLETE.
- R6.7 NONE — COMPLETE.
- R6.8 CONDITIONAL — NOT TRIGGERED, COMPLETE.
- R6.9 NONE — COMPLETE.
- R6.10 NONE — COMPLETE.
- R6.11 CONDITIONAL — NOT TRIGGERED, COMPLETE.
- R6.12 CONDITIONAL — not triggered at planning time; trigger only for genuinely non-hosted acceptance-critical capability or explicit human approval.

# R6 completion rule

R6 is COMPLETE only when R6.1–R6.12 are COMPLETE, no required/triggered manual gate remains pending, R6.12 integrated gate passes, exact-final-head R0/Python Core/UI are green, implementation is merged, and final `R6_PLAN.md`, `R6_STATUS.md`, `R6_12_ACCEPTANCE.md` and continuity are synchronized by a CI-green normalization merge. Only then may R7 planning begin, and the permanent rule requires `R7_PLAN.md` to be created and merged before R7.1.

# Change log

- 2026-08-22: retroactive R6 plan created and R6.1–R6.12 structure frozen before R6.4; planning PR #37 merge `0a91064608507966a47921df8fb36e5f25477141`, normalization #38 `e96e7c3b168975869c911f880044b7ef8e322157`.
- 2026-08-22: R6.4 accepted head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`; PR #39; manual gate satisfied.
- 2026-08-22: R6.5 accepted head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`; PR #41; manual gate satisfied.
- 2026-08-22: R6.6 accepted head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; PR #43, normalization #44.
- 2026-08-22: R6.7 accepted head `0da49c7526b54f562827d63477b7ce8f1865de43`; PR #45, normalization #46.
- 2026-08-22: R6.8 accepted head `d632669b93fda7b8397b9c3de43d78ca8726323f`; PR #47, normalization #48/#49; manual conditional not triggered.
- 2026-08-22: R6.9 accepted head `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`; PR #50, normalization #51.
- 2026-08-22: R6.10 accepted head `e9363e0e00f592b39a7a094b7520b3d515fb02f0`; PR #52 merge `cefc60266cb191cf0ee5a099e0d8923a2f14745a`; normalization #53 `36524978a963d8c759d36902bc1ab00989da0549`.
- 2026-08-22: R6.11 accepted net-clean head `d0590ed3eda663ad713fc36d962c8dac1df109eb`; R0 #885, Python #859 five jobs, UI #826 SUCCESS; PR #54 merge `248b1331fe2b26229b932c36aefb83c70065c52a`; manual conditional not triggered. This post-merge normalization records R6.11 COMPLETE and R6.12 NEXT / NOT STARTED.
