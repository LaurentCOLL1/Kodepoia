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

This is the exhaustive execution/recovery plan for R6. It is a retroactive exception to the normal phase-start planning rule because R6.1–R6.3 were already complete when the permanent `RX_PLAN.md` rule was introduced. The user explicitly requested that R6 be brought under the same discipline before R6.4.

The plan freezes the R6.1–R6.12 subdivision structure and defines objective, scope, acceptance, rollback and manual-intervention contracts for every subdivision. It remains authoritative together with `R6_STATUS.md`, subdivision acceptance documents and `KODEPOIA_CONTINUITY.md`.

R6 may not be marked COMPLETE until every subdivision listed here is COMPLETE with required evidence, or a later recorded roadmap/architecture decision explicitly removes a subdivision from scope.

## Planning acceptance evidence

- accepted planning head `8fbad7c13dd65f9dcd49a03b33a3174fcf28d18a`;
- R0 Repository Guard `32563057993` / #639 — SUCCESS Windows + Ubuntu;
- Python Core `32563057956` / #613 — SUCCESS Windows + Ubuntu, PowerShell syntax validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32563057903` / #580 — SUCCESS Windows;
- PR #37 merged as `0a91064608507966a47921df8fb36e5f25477141`;
- post-plan normalization PR #38 merged as `e96e7c3b168975869c911f880044b7ef8e322157`.

**Planning gate result: PASS. R6.1–R6.5 are COMPLETE. R6.6 is NEXT / NOT STARTED.**

## Frozen-roadmap objective

R6 establishes the quality, health, budget and CI foundations required by the frozen roadmap:

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

KodeAudioQA, KodeDeviceLab, KodeAssetDoctor, KodeTextureOptimizer, KodeLOD and KodeShaderProfiler are architecture quality components but are not named in the frozen R6 roadmap and are not silently imported into this phase. Also out of R6: store publishing/signing, Android/iOS device certification, full generated-app framework implementation, ComfyUI, Blender, audio/voice production, backend/live-ops implementation, release channels and updater implementation beyond the rollback contract required by R6.12.

## Phase-wide architecture and governance boundaries

Every R6 subdivision must preserve:

- `WorkspaceBoundary` path confinement and symlink-escape rejection;
- `ProcessSandbox` plus global KillSwitch for process execution;
- Guardian and `PermissionSet` authorization/risk control;
- structured Tool APIs, never arbitrary model-supplied commands;
- SafeChange snapshots before sensitive mutation;
- AuditLog hash-chain evidence for governed sensitive operations;
- secrets redaction/exclusion from LLM context and persistent memory;
- schema versioning/DataGovernance;
- platform-aware behavior: non-target platforms must not impose requirements, dependencies, inputs, budgets or tests;
- local-first/offline-capable operation for configured projects;
- ADR requirement for foundation-level architecture change;
- no completion from partial CI, missing evidence, silence or wrong-environment evidence.

Persistent R6 evidence belongs under initialized `.kodepoia/` roots and must be resolved through `WorkspaceBoundary`.

## External-reference baselines

- **Accessibility:** WCAG 2.2 source criteria where applicable; W3C WCAG2ICT 2.2 is the preferred informative interpretation for non-Web desktop software. No universal WCAG certification claim.
- **Application security:** OWASP ASVS 5.0.0 stable baseline, only for applicable web/API/auth/session/security surfaces.
- **Software BOM:** SPDX 3.0 stable baseline. Pre-release SPDX versions are not authoritative without an explicit later decision.

If a versioned reference materially changes before a future subdivision is implemented, recheck it and record any acceptance-impacting change before coding.

## Complete subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R6.1 | KodeHealth foundation | COMPLETE | NONE | R5 COMPLETE |
| R6.2 | KodeBudget foundation | COMPLETE | NONE | R6.1 |
| R6.3 | KodeTests + KodeRegression foundation | COMPLETE | NONE | R6.1–R6.2 |
| R6.4 | KodeVisualQA foundation | COMPLETE | REQUIRED — SATISFIED | R6.1–R6.3 + accepted R5 Godot automation |
| R6.5 | KodeAccessibility foundation | COMPLETE | REQUIRED — SATISFIED | R6.3–R6.4 |
| R6.6 | KodeLocalization + pseudo-localization foundation | NEXT / NOT STARTED | NONE | R6.3 + R6.5 |
| R6.7 | KodeTechnicalDebt foundation | PLANNED | NONE | R6.1–R6.6 |
| R6.8 | KodeCI + KodeBuild foundation | PLANNED | CONDITIONAL | R6.1–R6.7 |
| R6.9 | KodeAppSecurity baseline | PLANNED | NONE | R6.3 + R6.7–R6.8 |
| R6.10 | KodePrivacy baseline | PLANNED | NONE | R6.7–R6.9 |
| R6.11 | KodeLicense + KodeBOM foundation | PLANNED | CONDITIONAL | R6.7–R6.10 |
| R6.12 | Major-patch validation + rollback gate and R6 integration acceptance | PLANNED | CONDITIONAL | R6.1–R6.11 |

No subdivision may be silently added, removed, merged, split or renumbered. Scope changes update this plan and continuity in the same work cycle; architecture-changing scope requires an ADR.

---

# R6.1 — KodeHealth foundation — COMPLETE

## Accepted scope

Structured KodeHealth contract with all 14 architecture health dimensions, explicit `unknown/pass/warn/fail`, deterministic score/coverage, blockers, validated exhaustive report JSON and project-confined persistence.

## Accepted evidence

- head `802de4ba3110ace657c4e16306a0ca29850ce2bd`;
- PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`;
- 9 focused tests PASS;
- R0 `32561211168`, Python Core `32561211156`, UI Smoke `32561211167` — SUCCESS.

Manual intervention: **NONE**.

Regression protection: do not weaken exhaustive dimensions, explicit unknown coverage, validation integrity or `WorkspaceBoundary` confinement.

---

# R6.2 — KodeBudget foundation — COMPLETE

## Accepted scope

Per-platform budget contracts for FPS/frame time, CPU/GPU, RAM/VRAM, storage, draw calls, polygons, textures, audio memory/voices, build size, mobile battery/thermal and online network; deterministic target/hard-limit semantics and explicit unknown coverage.

## Accepted evidence

- head `8ac3772e98c70260c320519a214bb25b6cedbb38`;
- PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`;
- derivation/evaluation/persistence smoke PASS;
- R0 `32561719921`/#603, Python Core `32561719925`/#577, UI Smoke `32561720008`/#544 — SUCCESS.

Manual intervention: **NONE**.

Regression protection: later collectors may feed R6.2 but must not create requirements for non-target platforms or weaken target/hard-limit/unknown semantics.

---

# R6.3 — KodeTests + KodeRegression foundation — COMPLETE

## Accepted scope

Structured test-run evidence and baseline/current regression comparison by stable IDs. FAIL/ERROR→SKIP cannot hide a known failure; removed cases and newly failing cases remain regressions. Persistence is confined and no arbitrary process execution path was added.

## Accepted evidence

- head `7150237c263dd3ac96af4662d74909e05f3cf991`;
- PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`;
- baseline/current persistence smoke PASS;
- R0 `32562032986`/#622, Python Core `32562032998`/#596, UI Smoke `32562032982`/#563 — SUCCESS.

Manual intervention: **NONE**.

Regression protection: deleting/skipping a known case must never manufacture an apparent fix.

---

# R6.4 — KodeVisualQA foundation — COMPLETE

## Accepted scope

Deterministic visual-regression comparison with immutable content-addressed baselines, exact-file/pixel/perceptual evidence, hash-bound policy/masks, PNG diff artifacts, anti-tamper report validation, R6.3 hooks, `WorkspaceBoundary` confinement and governed real-render Godot PNG capture while preserving accepted R5 AVI capture.

## Accepted evidence

- base normalized main `e96e7c3b168975869c911f880044b7ef8e322157`;
- head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`;
- PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`;
- post-merge normalization PR #40 merge `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`;
- R0 `32564304755`/#666, Python Core `32564304757`/#640, UI Smoke `32564304798`/#607 — SUCCESS;
- required Windows/Godot/Radeon local gate: `8 PASS / 0 FAIL / 8`, `acceptance_completed=true`;
- VisualQA evidence SHA-256 `4c0375391d8f0e1b54c8c949b264ec70d6c9a18f10798a52a72d79ac18daab56`.

Manual intervention: **REQUIRED — SATISFIED**.

Anti-regression: no auto-baseline replacement, no missing-evidence PASS, no weakened hashes/mask policy, no headless substitute where real-render evidence is required, no regression of R5 AVI capture, no arbitrary process/path fields.

---

# R6.5 — KodeAccessibility foundation — COMPLETE

## Objective and accepted scope

R6.5 established structured accessibility evidence and deterministic baseline checks for KodeStudio-supported UI surfaces, plus a real Windows interactive keyboard/focus/Narrator validation path for behavior hosted/offscreen CI cannot authoritatively prove.

Accepted scope includes:

- stable accessibility rule/target IDs;
- severity, status, evidence and applicability;
- explicit `not_applicable` with reason rather than false PASS;
- deterministic aggregate state/counts/blockers;
- canonical evidence SHA-256 and anti-tamper validation;
- project-confined persistence under `.kodepoia/diagnostics/accessibility/` through `WorkspaceBoundary`;
- R6.3 stable accessibility hooks;
- deterministic explicit sRGB contrast and direct-rectangle target-size helpers when source data exists;
- KodeStudio and Project Wizard accessible names/descriptions;
- dynamic budget/requirement control registration;
- QAccessible interface/name/role/state evidence;
- tab-focus audit for visible enabled registered controls;
- explicit N/A for hidden/disabled adaptive controls;
- blocking detection of named application-owned controls bypassing registration;
- narrow exclusion of Qt-owned `QTabBar` internal `ScrollLeftButton`/`ScrollRightButton` children;
- Windows accessibility UI CI;
- source-head/hash-bound 13-item real keyboard/focus/Narrator acceptance contract;
- rejection of wrong-SHA, incomplete, failing, tampered or out-of-workspace manual evidence.

Out of scope: universal WCAG/legal certification, future generated-app certification, mobile/console reader certification, cognitive user research, OCR-based reader emulation and game-specific accessibility feature design beyond this foundation.

## Accepted implementation identity

- starting normalized main `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`;
- implementation branch `feature/r6-5-accessibility`;
- accepted head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`;
- PR #41;
- merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`.

## Hosted final-head evidence

- R0 Repository Guard `32567824374` / #710 — SUCCESS Windows + Ubuntu;
- Python Core `32567824373` / #684 — SUCCESS Windows + Ubuntu, compilation, PowerShell runner syntax, full pytest and integrated accessibility UI smoke;
- KodeStudio UI Smoke `32567824370` / #651 — SUCCESS Windows.

## Required real Windows evidence — SATISFIED

Environment:

- Windows `Windows-11-10.0.26220-SP0`;
- Python `3.12.4`;
- exact source head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`.

Automated reports:

- KodeStudio main: 343 applicable PASS, 0 failed/warnings/unknown/blockers; evidence SHA-256 `9244424a8addb921822bae80de2d7c1a95733a10f04775dc7ec8b55194041920`;
- Project Wizard: 318 applicable PASS, 0 failed/warnings/unknown/blockers; evidence SHA-256 `e824358a8068d871f59fdbcc55092b300b572d34548d76b0c379973002ea2d91`.

Human observations:

- keyboard 5/5 PASS;
- focus visible/not obscured 2/2 PASS;
- Windows Narrator 6/6 PASS;
- manual 13/13 PASS, 0 blocking failures;
- integrated `15 PASS / 0 FAIL / 15`;
- `metadata.acceptance_completed=true`;
- evidence `.kodepoia/diagnostics/accessibility/r6-5-local-acceptance.json`.

The local run emitted Qt font-directory and `propagateSizeHints()` notices, but both structured accessibility reports contained zero warnings, zero unknowns and zero blockers. They are not R6.5 acceptance failures; if still relevant they may be tracked as later technical debt.

Manual intervention: **REQUIRED — SATISFIED**.

Anti-regression: do not convert missing evidence/N/A to PASS, weaken evidence hashing, broaden framework-internal exemptions without evidence, bypass the accessibility registry, substitute offscreen structural checks for a required real assistive-technology gate, or accept incomplete/manual evidence from another SHA.

R6.5 must not be reopened without demonstrated regression or architecture-changing ADR.

---

# R6.6 — KodeLocalization + pseudo-localization foundation — NEXT / NOT STARTED

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

Out of scope: professional translation, cultural certification, voice localization, universal font/script certification and store metadata translation.

Acceptance: stable IDs/serialization, missing placeholders FAIL, pseudo-localization preserves placeholders, fallback explicit, no platform pollution, report tamper validation, Windows + Ubuntu tests and KodeStudio smoke, merge + normalization.

Manual intervention: **NONE**.

Rollback/risk: do not destabilize existing strings without migration; pseudo-locale must never become production default.

---

# R6.7 — KodeTechnicalDebt foundation

## Objective

Create a persistent structured technical-debt register so debt is observable, prioritized and linked to code/requirements/tests instead of informal comments.

## In scope / deliverables

- stable debt IDs;
- category/severity/impact/probability/effort;
- owner/scope/source/provenance;
- file/symbol/test/requirement references;
- first-seen/last-seen/resolved lifecycle;
- accepted-debt rationale with optional review/expiry;
- deterministic ranking and duplicate fingerprinting;
- project-confined persistence under diagnostics;
- report/schema;
- Health `technical_debt` adapter;
- regression semantics for newly introduced blocking debt;
- `src/kodepoia/quality/technical_debt.py`, schema, tests and docs.

Out of scope: automatic code rewriting, License/BOM, architecture changes without ADR and arbitrary static-analysis shell commands supplied by a model.

Acceptance: stable lifecycle/ranking, accepted debt distinct from resolved debt, confinement, Health integration, tamper checks, CI green, merge + normalization.

Manual intervention: **NONE**.

Risk: never treat accepted debt as resolved; preserve rationale/history and avoid unstable fingerprints.

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
- available lint/compile/tests/regression/security/visual hooks;
- secrets-free logs/manifests;
- `.kodepoia/workflows/` and `.kodepoia/releases/` evidence where applicable;
- workflow updates without weakening R0/Python/UI gates.

Out of scope: store publishing, signing certificates, installers/update channels, unsupported macOS/iOS claims and generated-app framework builds belonging to later phases.

Acceptance: structured CI/build modules/schema, source/artifact hashes, deterministic package-build tests, documented unavoidable non-byte-reproducible fields, Windows+Ubuntu success, skipped/cancelled never PASS, secret redaction, merge + normalization.

Manual intervention: **CONDITIONAL** only if hosted Windows cannot authoritatively prove an acceptance-critical Windows build behavior/artifact.

If triggered, the implemented runner must bind evidence to the exact source SHA, preserve artifacts/hashes, emit zero blockers and `acceptance_completed=true`; failed evidence must not be edited or reused from another SHA.

---

# R6.9 — KodeAppSecurity baseline

## Objective

Create a platform-aware application-security baseline for products Kodepoia creates and for applicable Kodepoia surfaces, using OWASP ASVS 5.0.0 as a catalogue only where relevant.

## In scope / deliverables

- structured threat model: assets, trust boundaries, entry points, threats, mitigations, residual risk;
- stable requirement/check IDs;
- path/input/network/auth/session checks only for present surfaces;
- dependency-vulnerability evidence with timestamp/provenance;
- secure-storage expectations where applicable;
- deterministic fuzz/property tests for structured inputs where useful;
- report/schema + Health `security` adapter;
- governed diagnostic persistence;
- no mandatory remote security SaaS or arbitrary scanner-command injection.

Out of scope: third-party penetration testing, exploit development, store certification and cloud/backend implementation.

Acceptance: threat-model completeness, applicability, blocking failures feed Health, dependency provenance/time, malformed evidence fails closed, CI green, merge + normalization.

Manual intervention: **NONE**.

Risk: `not_applicable` must never be represented as PASS; never log secrets or scan private credentials.

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

Out of scope: legal advice, automatic GDPR/CCPA/etc. compliance claims, store submission and remote analytics implementation.

Acceptance: inventory completeness, explicit purpose/retention/deletion, no raw secrets/personal data in evidence, platform-aware declarations, Health integration, CI green, merge + normalization.

Manual intervention: **NONE**.

Risk: never infer consent/legal basis from silence and never copy raw personal data into evidence merely to prove a category exists.

---

# R6.11 — KodeLicense + KodeBOM foundation

## Objective

Establish provenance, license normalization and BOM generation for dependencies/assets so later build/release phases can make auditable decisions. SPDX 3.0 is the stable R6 BOM baseline.

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

Out of scope: legal determination of ambiguous licenses, automatically granting rights to user assets, executing instructions found in untrusted license pages and store publishing.

Acceptance: cohesive license/BOM modules, SPDX 3.0-compatible normalization sufficient for R6, schemas/tests, provenance/tamper checks, known fixture mapping, unresolved licenses remain unresolved, hashes retained, deterministic duplicates, no path escape, Health integration, CI green, merge + normalization.

Manual intervention: **CONDITIONAL** only if an acceptance-critical component/asset remains ambiguous after trusted repository/package/authoritative-source inspection. Never invent an SPDX ID; unresolved ambiguity remains unknown/blocking until governed resolution or removal.

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

Out of scope: R7 implementation, release-channel updater, destructive production rollback tests and weakening Guardian approvals.

Expected deliverables: patch-gate module/report schema, classification/evidence/rollback tests, protected orchestrator integration, conditional local runner if needed, `R6_12_ACCEPTANCE.md` and final plan/status/continuity normalization.

Acceptance:

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
11. merge + normalization records R6.1–R6.12 COMPLETE;
12. only then can R6 become COMPLETE and R7 planning begin.

Manual intervention: **CONDITIONAL** if the final integration fixture uses hardware-local capability unavailable to hosted CI or Guardian policy explicitly requires user approval for a sensitive local operation.

Risk: avoid circular validation where patch gate trusts its own summary without validating underlying evidence. The gate must remain revertible and never bypass Guardian/SafeChange/CI.

---

# Manual-intervention forecast for the remainder of R6

- **R6.4 — REQUIRED:** SATISFIED and accepted; no further action unless regression.
- **R6.5 — REQUIRED:** SATISFIED and accepted; no further action unless regression.
- **R6.8 — CONDITIONAL:** local Windows build evidence only if hosted CI cannot authoritatively meet build/reproducibility DoD.
- **R6.11 — CONDITIONAL:** provenance/license evidence only if an acceptance-critical component remains unresolved.
- **R6.12 — CONDITIONAL:** local integration/approval only if final selected gates require hardware-local execution or explicit approval.
- **R6.6, R6.7, R6.9, R6.10 — NONE** currently planned.

Before any future manual gate, its acceptance document and user-facing instructions must identify the exact final implementation head and confirm final implementation-specific commands/actions, expected output, recovery and evidence requirements.

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
- 2026-08-22: planning head `8fbad7c13dd65f9dcd49a03b33a3174fcf28d18a` passed R0 #639, Python Core #613 and UI Smoke #580; PR #37 merged as `0a91064608507966a47921df8fb36e5f25477141`.
- 2026-08-22: post-plan normalization PR #38 merged as `e96e7c3b168975869c911f880044b7ef8e322157`; R6.4 started from that normalized main.
- 2026-08-22: R6.4 accepted on head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41` after final hosted and required Windows/Godot/Radeon evidence; PR #39 merged as `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`; PR #40 normalized main to `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`.
- 2026-08-22: R6.5 accepted on head `06fd66af4b3a85da24b98ea2a5fbb2685358c540` after R0 #710, Python Core #684, UI Smoke #651 and required Windows keyboard/focus/Narrator `15 PASS / 0 FAIL / 15`; PR #41 merged as `db1a1ab78eb2ac7d90f75ab294074dec0238268c`. R6.5 COMPLETE; R6.6 NEXT / NOT STARTED pending post-merge normalization.
