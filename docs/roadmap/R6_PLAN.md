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

The R6.1–R6.12 subdivision structure is frozen. This plan defines scope, acceptance, evidence, rollback and manual-intervention contracts. It remains authoritative together with `R6_STATUS.md`, subdivision acceptance documents and `docs/continuity/KODEPOIA_CONTINUITY.md`.

R6 may not be marked COMPLETE until every subdivision listed here is COMPLETE with required evidence, or a later recorded roadmap/architecture decision explicitly removes a subdivision from scope.

## Planning acceptance evidence

- planning head `8fbad7c13dd65f9dcd49a03b33a3174fcf28d18a`;
- R0 Repository Guard `32563057993` / #639 — SUCCESS Windows + Ubuntu;
- Python Core `32563057956` / #613 — SUCCESS Windows + Ubuntu, PowerShell syntax and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32563057903` / #580 — SUCCESS Windows;
- PR #37 merged as `0a91064608507966a47921df8fb36e5f25477141`;
- post-plan normalization PR #38 merged as `e96e7c3b168975869c911f880044b7ef8e322157`.

**Planning gate result: PASS. R6.1–R6.10 are COMPLETE. R6.11 is NEXT / NOT STARTED after the R6.10 post-merge normalization PR is CI-green and merged.**

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
- structured Tool APIs, never arbitrary model-supplied commands/argv/cwd/hosts;
- SafeChange snapshots before sensitive mutation;
- AuditLog hash-chain evidence for governed sensitive operations;
- secrets redaction/exclusion from LLM context and persistent evidence;
- schema versioning/DataGovernance;
- platform-aware behavior: non-target platforms must not impose requirements, dependencies, inputs, budgets or tests;
- local-first/offline-capable operation for configured projects;
- ADR requirement for foundation-level architecture change;
- no completion from partial CI, missing evidence, silence or wrong-environment evidence.

Persistent R6 evidence belongs under initialized `.kodepoia/` roots and must be resolved through `WorkspaceBoundary`.

## External-reference baselines

- **Accessibility:** WCAG 2.2 source criteria where applicable; W3C WCAG2ICT 2.2 is informative context for non-Web desktop software. No universal WCAG certification claim.
- **Localization:** Unicode CLDR stable releases are reference context only. R6.6 does not vendor CLDR or claim universal locale coverage.
- **CI/Build provenance:** SLSA v1.2 is reference context for artifact digest/source/build provenance. No SLSA level is claimed.
- **Application security:** OWASP ASVS 5.0.0 is used only as an applicable-control catalogue; references are version-qualified and no global ASVS certification claim is made.
- **Privacy:** GDPR principles and platform store declarations are reference context for explicit purpose/minimisation/retention/deletion and declaration-preparation fields. R6.10 must not make legal conclusions.
- **Software BOM:** SPDX 3.0 is the stable R6 BOM baseline. CycloneDX 1.7 is the current stable CycloneDX line and may be used for optional interoperability/validation; CycloneDX 2.0 is announced for 2026 but is not silently adopted as the R6 baseline.

If a versioned reference materially changes before a future subdivision is implemented, recheck it and record any acceptance-impacting change before coding.

## Complete subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R6.1 | KodeHealth foundation | COMPLETE | NONE | R5 COMPLETE |
| R6.2 | KodeBudget foundation | COMPLETE | NONE | R6.1 |
| R6.3 | KodeTests + KodeRegression foundation | COMPLETE | NONE | R6.1–R6.2 |
| R6.4 | KodeVisualQA foundation | COMPLETE | REQUIRED — SATISFIED | R6.1–R6.3 + accepted R5 Godot automation |
| R6.5 | KodeAccessibility foundation | COMPLETE | REQUIRED — SATISFIED | R6.3–R6.4 |
| R6.6 | KodeLocalization + pseudo-localization foundation | COMPLETE | NONE | R6.3 + R6.5 |
| R6.7 | KodeTechnicalDebt foundation | COMPLETE | NONE | R6.1–R6.6 |
| R6.8 | KodeCI + KodeBuild foundation | COMPLETE | CONDITIONAL — NOT TRIGGERED | R6.1–R6.7 |
| R6.9 | KodeAppSecurity baseline | COMPLETE | NONE | R6.3 + R6.7–R6.8 |
| R6.10 | KodePrivacy baseline | COMPLETE | NONE | R6.7–R6.9 |
| R6.11 | KodeLicense + KodeBOM foundation | NEXT / NOT STARTED | CONDITIONAL | R6.7–R6.10 |
| R6.12 | Major-patch validation + rollback gate and R6 integration acceptance | PLANNED | CONDITIONAL | R6.1–R6.11 |

No subdivision may be silently added, removed, merged, split or renumbered. Scope changes update this plan and continuity in the same work cycle; architecture-changing scope requires an ADR.

---

# R6.1 — KodeHealth foundation — COMPLETE

Accepted scope: all 14 architecture health dimensions with explicit `unknown/pass/warn/fail`, deterministic score/coverage, blockers, validated report JSON and `WorkspaceBoundary` persistence.

Accepted evidence:
- head `802de4ba3110ace657c4e16306a0ca29850ce2bd`;
- PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`;
- R0 `32561211168`, Python Core `32561211156`, UI Smoke `32561211167` — SUCCESS.

Manual intervention: **NONE**.

Anti-regression: preserve exhaustive dimensions, explicit unknown coverage, validation integrity and project confinement.

---

# R6.2 — KodeBudget foundation — COMPLETE

Accepted scope: per-platform FPS/frame-time, CPU/GPU, RAM/VRAM, storage, draw calls, polygons, textures, audio memory/voices, build size, mobile battery/thermal and online network budgets with deterministic target/hard-limit semantics and explicit unknown coverage.

Accepted evidence:
- head `8ac3772e98c70260c320519a214bb25b6cedbb38`;
- PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`;
- R0 #603, Python Core #577, UI Smoke #544 — SUCCESS.

Manual intervention: **NONE**.

Anti-regression: later collectors must not create requirements for non-target platforms or weaken target/hard-limit/unknown semantics.

---

# R6.3 — KodeTests + KodeRegression foundation — COMPLETE

Accepted scope: structured test-run evidence and baseline/current regression comparison by stable ID. FAIL/ERROR→SKIP cannot hide a known failure; removed cases and newly failing cases remain regressions.

Accepted evidence:
- head `7150237c263dd3ac96af4662d74909e05f3cf991`;
- PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`;
- R0 #622, Python Core #596, UI Smoke #563 — SUCCESS.

Manual intervention: **NONE**.

Anti-regression: deleting/skipping a known case must never manufacture an apparent fix.

---

# R6.4 — KodeVisualQA foundation — COMPLETE

Accepted scope: deterministic visual-regression comparison with immutable content-addressed baselines, exact-file/pixel/perceptual evidence, hash-bound masks/policy, PNG diffs, anti-tamper reports, R6.3 hooks, `WorkspaceBoundary`, and governed real-render Godot PNG capture while preserving R5 AVI capture.

Accepted evidence:
- base `e96e7c3b168975869c911f880044b7ef8e322157`;
- accepted head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`;
- PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`;
- normalization #40 `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`;
- R0 #666, Python Core #640, UI Smoke #607 — SUCCESS;
- required Windows/Godot/Radeon gate `8 PASS / 0 FAIL / 8`.

Manual intervention: **REQUIRED — SATISFIED**.

Anti-regression: no auto-baseline replacement, missing-evidence PASS, weakened hashes/masks or headless substitute where real rendering is required.

---

# R6.5 — KodeAccessibility foundation — COMPLETE

Accepted scope: structured accessibility evidence, explicit applicability/N/A, canonical evidence hashing, KodeStudio/Project Wizard checks, Qt accessibility inspection, keyboard focus audit and source-head-bound Windows keyboard/focus/Narrator gate.

Accepted evidence:
- accepted head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`;
- PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`;
- normalization #42 `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`;
- R0 #710, Python Core #684, UI Smoke #651 — SUCCESS;
- required Windows accessibility gate `15 PASS / 0 FAIL / 15`.

Manual intervention: **REQUIRED — SATISFIED**.

Anti-regression: no N/A→PASS, no broad framework exemptions, no wrong-SHA manual evidence and no offscreen substitute for required assistive-technology evidence.

---

# R6.6 — KodeLocalization + pseudo-localization foundation — COMPLETE

Accepted scope: stable message IDs/forms, missing/extra/form/placeholder evidence, explicit fallback, deterministic `qps-ploc`, protected placeholders/markup/entities, canonical anti-tamper reports, `WorkspaceBoundary`, R6.3 hooks and KodeStudio pseudo-localized UI smoke while English remains production default.

Accepted evidence:
- starting main `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`;
- accepted head `6890b9d37722c74703e8b86f7de11dbfe66821ed`;
- PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`;
- normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`;
- R0 #733, Python Core #707, UI Smoke #674 — SUCCESS.

Development finding: two round-trip assertions initially compared `details=None` with canonical serialized `details={}`. Only canonical test comparison was corrected; no localization rule or blocker was weakened.

Manual intervention: **NONE — COMPLETE**.

Anti-regression: pseudo-locale never becomes production default; missing keys/forms/placeholders remain explicit.

---

# R6.7 — KodeTechnicalDebt foundation — COMPLETE

Accepted scope: persistent debt register with stable IDs, category/severity/impact/probability/effort, lifecycle `OPEN/ACCEPTED/RESOLVED`, rationale/history, deterministic priority/fingerprint, canonical anti-tamper report, `WorkspaceBoundary`, Health and R6.3 adapters.

Accepted evidence:
- starting main `c5edd3c80ad9afec25997f1372d5f98ac861becc`;
- accepted head `0da49c7526b54f562827d63477b7ce8f1865de43`;
- PR #45 merge `3986b056654b25a73e45e5135ca3110a920c4bf5`;
- normalization #46 `fc7bd4d5803c451b4d343d08bcc212868ad24412`;
- R0 #756, Python Core #730, UI Smoke #697 — SUCCESS.

Development finding: one test expected priority 30 where the frozen formula produced 24. Only the fixture expectation changed.

Manual intervention: **NONE — COMPLETE**.

Anti-regression: accepted debt is not resolved debt; blocking debt remains visible and cannot be hidden by fingerprint changes.

---

# R6.8 — KodeCI + KodeBuild foundation — COMPLETE

Accepted scope: exact-source-SHA CI evidence, required-state semantics, wheel+sdist manifests, source/dependency/artifact SHA-256 evidence, structural package validation, recursive secret redaction, `WorkspaceBoundary`, Health/R6.3 adapters and additive Windows+Ubuntu package-build jobs with fixed commands and exact-SHA checkout.

Accepted evidence:
- starting main `fc7bd4d5803c451b4d343d08bcc212868ad24412`;
- accepted implementation head `d632669b93fda7b8397b9c3de43d78ca8726323f`;
- PR #47 merge `d570a3930ee63802882b8682e4532004d4fd81d6`;
- R0 #783 `32571710663` — SUCCESS Windows+Ubuntu;
- Python Core #757 `32571710718` — SUCCESS for both core OS jobs, integrated Windows UI and both package-build jobs;
- UI Smoke #724 `32571710650` — SUCCESS Windows;
- both uploaded package bundles independently inspected: wheel, sdist, Build/CI reports PASS, zero blockers, exact source SHA;
- normalization #48 head `0580f930d6dfaa387c1eda1cf8ad56de79cc42b9` passed R0 #790, Python Core #764 and UI Smoke #731 then merged as `92effbde1e432a8fcb6c794038d77367d034bcb0`;
- final normalized-state wording #49 head `beb431d19c487c55b92c86a7a0eead90c7529b6e` passed R0 #797, Python Core #771 including both package-builds and UI Smoke #738, then merged as `616899291fc3b4dc40695415a5008d6fdd599230`.

Manual intervention: **CONDITIONAL — NOT TRIGGERED**. Hosted Windows proved all acceptance-critical R6.8 behavior.

Anti-regression: package builds remain source-SHA-bound; skipped/cancelled required checks never PASS; missing/invalid wheel or sdist remains blocking; no arbitrary model-supplied build command/path.

---

# R6.9 — KodeAppSecurity baseline — COMPLETE

## Accepted scope

R6.9 established a platform-aware application-security evidence baseline for Kodepoia and products it creates without claiming a universal certification.

Accepted scope:

- typed threat model with assets, trust boundaries, entry points, threats, mitigations and residual risk;
- cross-reference/duplicate validation;
- residual risk defaults `UNKNOWN` rather than inferred safe;
- stable requirement IDs;
- explicit `applicable` / `not_applicable`; N/A requires rationale and never becomes PASS;
- measured PASS/WARN/FAIL requires evidence provenance;
- optional OWASP ASVS references pinned as `v5.0.0-x.y.z`;
- dependency-vulnerability evidence with exact component/version, timezone-aware check time and provenance;
- AFFECTED dependencies require advisory IDs and fail the aggregate report;
- secure-storage evidence helper distinguishing OS-backed/no-plaintext from insecure storage;
- recursive secret redaction;
- canonical SHA-256 report with derived status/count/blocker tamper rejection;
- `.kodepoia/diagnostics/security/` persistence through `WorkspaceBoundary`;
- Health `security` adapter and stable R6.3 requirement/dependency/threat cases;
- N/A/WARN/UNKNOWN adapters map to SKIP, never fake PASS;
- `security-report-v1.schema.json`;
- no unrestricted security scanner, process or network execution path.

## Accepted evidence

- starting normalized main `616899291fc3b4dc40695415a5008d6fdd599230`;
- implementation branch `feature/r6-9-appsecurity`;
- accepted implementation head `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`;
- implementation PR #50;
- implementation merge `f5c135edf0be464a02b4b46d67c14e665f236009`;
- R0 Repository Guard #812 `32573265598` — SUCCESS Windows + Ubuntu;
- Python Core #786 `32573265793` — SUCCESS for all five jobs: core Ubuntu, core Windows, integrated Windows UI, package-build Ubuntu, package-build Windows;
- KodeStudio UI Smoke #753 `32573265579` — SUCCESS Windows.

Development diagnostic: initial draft head `85742e808dfb68dbe6e1f5f64c2b4fee5d63b0f3` had exactly one incorrect test expectation: a blocking Health SECURITY metric was expected to score 0.0 while deterministic aggregation correctly yielded 75.0. The metric was already FAIL and blocking. Only the assertion was corrected; no security rule, blocker, scoring formula, applicability, provenance, redaction or threat-risk rule changed. Diagnostic head `0251a62c92230a486abfdd8b151e59a1adb98bb3` then passed R0 #810, Python Core #784 and UI #751 before final acceptance.

External-reference interpretation: OWASP ASVS 5.0.0 is a catalogue only for applicable surfaces. Representative mappings include `v5.0.0-1.2.5` command injection/process construction, `v5.0.0-5.3.2` trusted/validated paths, and `v5.0.0-13.3.1` secrets management. No full ASVS certification claim is made.

Manual intervention: **NONE — COMPLETE**.

Anti-regression: never weaken N/A semantics, provenance, residual-risk UNKNOWN defaults, secret redaction or `WorkspaceBoundary`; never add arbitrary scanner commands/executables/cwd/URLs/model-provided process arguments.

Post-merge normalization: PR #51 head `f42e2d2027c3a3601f22446cbbeee9f702e8458f` passed R0 #819, Python Core #793 five jobs and UI Smoke #760, then merged as `4df229e431d2d54e4268607f38bac4045ac590d1`.

---

# R6.10 — KodePrivacy baseline — COMPLETE

## Objective achieved

Established structured, local-first privacy evidence covering what data exists, source, purpose, storage, recipients, retention, deletion, sensitivity, basis placeholders and store-declaration preparation without making legal conclusions.

## Accepted scope

- stable data-category IDs and provenance;
- explicit disposition `collected`, `none`, `not_applicable`;
- collected source, purpose, storage, recipients, retention and deletion metadata;
- explicit sensitivity including `unknown`;
- `PrivacyBasisState` `unspecified/declared/not_applicable`, with no legal/consent basis inferred from silence;
- declared basis requires provenance;
- explicit `inventory_complete` and `inventory_review_source`; incomplete inventory cannot PASS;
- all-N/A evidence remains UNKNOWN and N/A is score-neutral;
- privacy issue applicability/status/severity; N/A never PASS; measured results require provenance;
- Apple preparation fields for collected/link-to-user/tracking/purposes;
- Google Play preparation fields for collected/shared/optionality/purposes;
- store/platform/data-category/inventory cross-validation;
- N/A store declaration remains R6.3 SKIP even when structurally ready;
- recursive secret/personal-value redaction; no raw personal-data samples required;
- canonical SHA-256 report, derived count/blocker/status/readiness validation and tamper rejection;
- `privacy-report-v1.schema.json`;
- `.kodepoia/diagnostics/privacy/` through `WorkspaceBoundary`;
- Health `privacy` adapter and stable R6.3 cases;
- no remote privacy SaaS, scanner, analytics collector, network collector or store-submission path.

## Accepted evidence

- starting normalized main `4df229e431d2d54e4268607f38bac4045ac590d1`;
- implementation branch `feature/r6-10-privacy`;
- accepted final implementation head `e9363e0e00f592b39a7a094b7520b3d515fb02f0`;
- R0 Repository Guard #844 `32575111465` — SUCCESS Windows + Ubuntu;
- Python Core #818 `32575111540` — SUCCESS for all five jobs: core Ubuntu, core Windows including PowerShell syntax validation, integrated Windows UI, package-build Ubuntu and package-build Windows;
- KodeStudio UI Smoke #785 `32575111597` — SUCCESS Windows;
- implementation PR #52 merged with `expected_head_sha=e9363e0e00f592b39a7a094b7520b3d515fb02f0` as `cefc60266cb191cf0ee5a099e0d8923a2f14745a`.

Development review: first diagnostic head `935d6b4fc7a29ad832df501f605c3648cde05988` passed R0 #830, Python Core #804 and UI #771, but independent review found a potential false-green path around N/A scoring and unproven inventory completeness. The contract was hardened rather than accepted: `inventory_complete=true` now requires review provenance, incomplete inventory remains WARN, N/A inventory/issues/declarations are score-neutral, all-N/A remains UNKNOWN, and N/A store declarations remain R6.3 SKIP. Hardened head `48daa4f82194e1875211f205b99ba19089f42d92` then passed R0 #836, Python Core #810 five jobs and UI #777 before the exact final head was frozen.

External-reference interpretation: GDPR principles and Apple/Google store declarations are reference context only. KodePrivacy does not infer lawful basis, consent requirements, legal compliance, store approval or certification.

Manual intervention: **NONE — COMPLETE**.

Anti-regression: never invent legal/consent basis, never mark inventory complete without provenance, never let N/A inflate score or become PASS, never copy raw personal data into evidence, and never weaken `WorkspaceBoundary`, redaction or declaration/inventory cross-validation.

Post-merge normalization: this documentation-only branch records R6.10 COMPLETE and promotes R6.11 to NEXT / NOT STARTED only after its own exact-head CI is green and merged.

---

# R6.11 — KodeLicense + KodeBOM foundation — NEXT / NOT STARTED

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

Reference recheck on 2026-08-22: SPDX 3.0 remains the current SPDX version and the R6 baseline. CycloneDX 1.7 is the current stable CycloneDX specification (ECMA-424, 2nd Edition) and may be used as an additional interoperability/validation target. CycloneDX 2.0 is announced for 2026 but is not adopted as the R6 baseline without an explicit decision.

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
- **R6.6 — NONE:** COMPLETE.
- **R6.7 — NONE:** COMPLETE.
- **R6.8 — CONDITIONAL:** NOT TRIGGERED; COMPLETE.
- **R6.9 — NONE:** COMPLETE; no user action required.
- **R6.10 — NONE:** COMPLETE; no user action required.
- **R6.11 — CONDITIONAL:** provenance/license evidence only if an acceptance-critical component remains unresolved.
- **R6.12 — CONDITIONAL:** local integration/approval only if final selected gates require hardware-local execution or explicit approval.

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

- 2026-08-22: retroactive plan created before R6.4; R6.1–R6.3 recorded from accepted evidence; R6.4–R6.12 structure frozen.
- 2026-08-22: planning head `8fbad7c13dd65f9dcd49a03b33a3174fcf28d18a` passed R0 #639, Python Core #613 and UI Smoke #580; PR #37 merged as `0a91064608507966a47921df8fb36e5f25477141`; post-plan normalization #38 `e96e7c3b168975869c911f880044b7ef8e322157`.
- 2026-08-22: R6.4 accepted head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`; PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`; normalization #40 `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`.
- 2026-08-22: R6.5 accepted head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`; PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`; normalization #42 `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`.
- 2026-08-22: R6.6 accepted head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`.
- 2026-08-22: R6.7 accepted head `0da49c7526b54f562827d63477b7ce8f1865de43`; PR #45 merge `3986b056654b25a73e45e5135ca3110a920c4bf5`; normalization #46 `fc7bd4d5803c451b4d343d08bcc212868ad24412`.
- 2026-08-22: R6.8 accepted head `d632669b93fda7b8397b9c3de43d78ca8726323f`; PR #47 merge `d570a3930ee63802882b8682e4532004d4fd81d6`; normalization #48 `92effbde1e432a8fcb6c794038d77367d034bcb0`; final wording #49 `616899291fc3b4dc40695415a5008d6fdd599230`.
- 2026-08-22: R6.9 accepted head `1f24b0160cc28a03efdcbbc0aeb841125a1c5351` after R0 #812, Python Core #786 and UI Smoke #753; PR #50 merged as `f5c135edf0be464a02b4b46d67c14e665f236009`; normalization #51 head `f42e2d2027c3a3601f22446cbbeee9f702e8458f` passed R0 #819, Python Core #793 five jobs and UI #760, then merged as `4df229e431d2d54e4268607f38bac4045ac590d1`.
- 2026-08-22: R6.10 accepted head `e9363e0e00f592b39a7a094b7520b3d515fb02f0` after R0 #844, Python Core #818 five jobs and UI Smoke #785; PR #52 merged as `cefc60266cb191cf0ee5a099e0d8923a2f14745a`; post-merge normalization records R6.10 COMPLETE and R6.11 NEXT / NOT STARTED.