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

The plan freezes the R6.1–R6.12 subdivision structure and defines objective, scope, deliverables, acceptance, evidence, rollback and manual-intervention contracts for every subdivision. It remains authoritative together with `R6_STATUS.md`, subdivision acceptance documents and `KODEPOIA_CONTINUITY.md`.

R6 may not be marked COMPLETE until every subdivision listed here is COMPLETE with required evidence, or a later recorded roadmap/architecture decision explicitly removes a subdivision from scope.

## Planning acceptance evidence

- accepted planning head `8fbad7c13dd65f9dcd49a03b33a3174fcf28d18a`;
- R0 Repository Guard `32563057993` / #639 — SUCCESS Windows + Ubuntu;
- Python Core `32563057956` / #613 — SUCCESS Windows + Ubuntu, PowerShell syntax validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32563057903` / #580 — SUCCESS Windows;
- PR #37 merged as `0a91064608507966a47921df8fb36e5f25477141`;
- post-plan normalization PR #38 merged as `e96e7c3b168975869c911f880044b7ef8e322157`.

**Planning gate result: PASS. R6.1–R6.8 are COMPLETE. R6.9 is NEXT / NOT STARTED.**

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
- **Localization:** Unicode CLDR stable releases are reference context for locale-data conventions only. R6.6 does not vendor CLDR or claim full locale-formatting coverage.
- **CI/Build provenance:** SLSA v1.2 is reference context for artifact digest/source/build provenance concepts in R6.8. Kodepoia does not claim a SLSA level. GitHub artifact attestations may be used later as supplementary release provenance, but an attestation by itself is not a security guarantee and routine PR/test-build attestation is not an R6.8 completion gate.
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
| R6.6 | KodeLocalization + pseudo-localization foundation | COMPLETE | NONE | R6.3 + R6.5 |
| R6.7 | KodeTechnicalDebt foundation | COMPLETE | NONE | R6.1–R6.6 |
| R6.8 | KodeCI + KodeBuild foundation | COMPLETE | CONDITIONAL — NOT TRIGGERED | R6.1–R6.7 |
| R6.9 | KodeAppSecurity baseline | NEXT / NOT STARTED | NONE | R6.3 + R6.7–R6.8 |
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

## Accepted scope

Structured accessibility evidence and deterministic KodeStudio/Project Wizard checks, explicit applicability/N/A semantics, canonical evidence hashing, `WorkspaceBoundary` confinement, R6.3 hooks, explicit contrast/target-size helpers, Qt accessible metadata/QAccessible inspection, keyboard focus audit, dynamic-control registration and a source-head/hash-bound real Windows keyboard/focus/Narrator gate.

## Accepted evidence

- base normalized main `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`;
- head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`;
- PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`;
- post-merge normalization PR #42 merge `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`;
- R0 `32567824374`/#710, Python Core `32567824373`/#684, UI Smoke `32567824370`/#651 — SUCCESS;
- required Windows automated accessibility reports: main 343 applicable PASS; wizard 318 applicable PASS; zero failures/warnings/unknown/blockers;
- human keyboard 5/5, focus 2/2, Narrator 6/6;
- integrated `15 PASS / 0 FAIL / 15`, `acceptance_completed=true`.

Manual intervention: **REQUIRED — SATISFIED**.

Anti-regression: no missing/N/A evidence to PASS, no weakened hashes, no broad framework exemptions, no registry bypass, no offscreen substitute for a required assistive-technology gate, no wrong-SHA manual evidence.

---

# R6.6 — KodeLocalization + pseudo-localization foundation — COMPLETE

## Objective and accepted scope

R6.6 established deterministic localization contracts before later phases multiply UI surfaces. The foundation is structural rather than a professional translation/cultural-certification effort.

Accepted scope:

- stable locale/message IDs independent of visible copy;
- duplicate message-ID rejection;
- mandatory `other` message form;
- missing/extra-key evidence;
- exact source/target message-form parity;
- Python-format placeholder parity per form;
- explicit source-locale fallback semantics;
- deterministic `qps-ploc` pseudo-localization;
- protection of `{placeholder}`, `<markup>` and `&entity;` tokens;
- deterministic visible expansion and `⟦...⟧` markers;
- canonical report/status/count/blocker SHA-256 evidence with tamper rejection;
- `.kodepoia/diagnostics/localization/` persistence through `WorkspaceBoundary`;
- R6.3 stable `localization:<rule>:<target>` hooks;
- KodeStudio English source-message registry for the registered main surface;
- English remains production default;
- pseudo-localized KodeStudio navigation/button/window smoke and adaptive navigation width for expanded strings;
- preservation of R6.5 accessibility smoke after visible text routing changes.

Out of scope: professional translation, cultural certification, voice localization, universal font/script certification, store metadata translation and a claim that every future Project Wizard/user-facing string has already been migrated.

## Accepted deliverables

- `src/kodepoia/quality/localization.py`;
- `src/kodepoia/kodestudio/localization.py`;
- localization integration in `src/kodepoia/kodestudio/app.py`;
- `schemas/localization-report-v1.schema.json`;
- `tests/test_r6_6_localization.py`;
- `tests/test_r6_6_localization_ui.py`;
- `docs/roadmap/R6_6_DESIGN.md`;
- `docs/roadmap/R6_6_ACCEPTANCE.md`;
- Windows UI workflow coverage in Python Core and KodeStudio UI Smoke.

## Accepted evidence

- starting normalized main `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`;
- implementation branch `feature/r6-6-localization`;
- accepted head `6890b9d37722c74703e8b86f7de11dbfe66821ed`;
- implementation PR #43;
- implementation merge `f677cb34eade0549edc951fe11955de2bc0b270d`;
- R0 Repository Guard `32570001461` / #733 — SUCCESS Windows + Ubuntu;
- Python Core `32570001514` / #707 — SUCCESS Windows + Ubuntu, PowerShell syntax and integrated KodeStudio UI smoke;
- KodeStudio UI Smoke `32570001491` / #674 — SUCCESS Windows.

The first draft head produced two round-trip test assertion failures because Python object equality distinguished `details=None` from canonical serialized `details={}`. Tests were corrected to compare the canonical persisted/hashed representation. No localization rule, blocker, fallback/placeholder check or `WorkspaceBoundary` protection was weakened.

Manual intervention: **NONE — COMPLETE**.

Rollback/risk: pseudo-locale must never become production default; stable IDs should survive copy changes; missing keys/forms/placeholders remain explicit; rollback restores accepted English UI without touching R6.1–R6.5 evidence.

---

# R6.7 — KodeTechnicalDebt foundation — COMPLETE

## Objective and accepted scope

R6.7 created a persistent structured technical-debt register so debt is observable, prioritized and linked to code/requirements/tests rather than informal comments.

Accepted scope:

- stable debt IDs;
- category/severity/impact/probability/effort;
- owner/scope/source/provenance;
- structured file/symbol/test/requirement/issue references;
- timezone-aware first-seen/last-seen/review/expiry/resolution evidence;
- explicit `OPEN`, `ACCEPTED`, `RESOLVED` lifecycle;
- accepted debt requires rationale and remains visible/penalized rather than becoming resolved;
- resolved debt remains historical and requires `resolved_at`;
- accepted/resolved debt cannot remain blocking;
- deterministic priority `severity_weight × impact × probability ÷ effort`, bounded to 100;
- stable duplicate fingerprinting based on debt identity rather than volatile timestamps/state;
- duplicate IDs/fingerprints rejected;
- derived counts, blockers, ranking and debt penalty;
- canonical SHA-256 anti-tamper evidence;
- `.kodepoia/diagnostics/technical_debt/` persistence through `WorkspaceBoundary`;
- Health `technical_debt` adapter;
- stable R6.3 `technical-debt:<id>` cases;
- newly introduced blocking debt becomes an added FAIL and therefore a regression;
- repository-observed debt can be recorded with actual provenance without claiming an unexecuted scanner.

## Accepted deliverables

- `src/kodepoia/quality/technical_debt.py`;
- `schemas/technical-debt-report-v1.schema.json`;
- `tests/test_r6_7_technical_debt.py`;
- quality exports;
- `docs/roadmap/R6_7_DESIGN.md`;
- `docs/roadmap/R6_7_ACCEPTANCE.md`;
- `docs/roadmap/R6_7_KNOWN_DEBT.md`.

## Accepted evidence

- starting normalized main `c5edd3c80ad9afec25997f1372d5f98ac861becc`;
- implementation branch `feature/r6-7-technical-debt`;
- accepted head `0da49c7526b54f562827d63477b7ce8f1865de43`;
- implementation PR #45;
- implementation merge `3986b056654b25a73e45e5135ca3110a920c4bf5`;
- post-merge normalization PR #46 merge `fc7bd4d5803c451b4d343d08bcc212868ad24412`;
- R0 Repository Guard `32570711736` / #756 — SUCCESS Windows + Ubuntu;
- Python Core `32570711738` / #730 — SUCCESS Windows + Ubuntu, PowerShell syntax, full pytest and integrated KodeStudio UI smoke;
- KodeStudio UI Smoke `32570711732` / #697 — SUCCESS Windows.

Development CI found one incorrect test expectation: critical severity with impact 4, probability 3 and effort 2 evaluates to `4 × 4 × 3 ÷ 2 = 24`, not 30. The fixture expectation was corrected; the deterministic formula was unchanged.

The same hosted logs reproduced non-blocking debt candidates with actual provenance: imported quality classes named `Test*` causing `PytestCollectionWarning`, and Pillow `Image.Image.getdata()` deprecation warnings in VisualQA. R6.5 Qt font/size-hint notices remain environment-specific candidate debt. These observations are not fabricated scanner results and are not falsely marked remediated.

Manual intervention: **NONE — COMPLETE**.

Rollback/risk: never treat accepted debt as resolved, never change fingerprints merely to avoid duplicate detection, preserve rationale/history, keep blocking debt visible to R6.3, keep derived fields/hash validation and `WorkspaceBoundary` confinement intact.

---

# R6.8 — KodeCI + KodeBuild foundation — COMPLETE

## Objective and accepted scope

R6.8 converted repository CI and Python package builds into structured, exact-source-SHA-bound evidence consumable by Health, Tests/Regression and later release tooling, without weakening any existing R0/Python/UI gate or adding an unrestricted build execution path.

Accepted scope:

- stable CI check IDs;
- explicit `queued`, `in_progress`, `pass`, `fail`, `cancelled`, `skipped`, `unknown` semantics;
- required FAIL/CANCELLED/SKIPPED never PASS; required incomplete evidence remains UNKNOWN;
- exact 40-character source Git SHA binding;
- canonical CI evidence SHA-256 with derived count/blocker tamper rejection;
- R6.3 stable CI hooks;
- `.kodepoia/workflows/<workflow>/` persistence through `WorkspaceBoundary`;
- build manifests with source SHA, platform, Python version and Hatchling backend;
- deterministic source-input digest plus explicit dependency-input digest;
- package artifact name, kind, byte size, SHA-256 and structural validation;
- required wheel + sdist presence; missing/invalid required package is blocking;
- recursive sensitive-field and common token/Bearer redaction before persisted metadata;
- `.kodepoia/releases/<platform>/` persistence through `WorkspaceBoundary`;
- Health `build` adapter and stable R6.3 `build:<platform>:<kind>` hooks;
- `ci-report-v1` and `build-manifest-v1` schemas;
- fixed evidence collector `scripts/r6_8_collect_build.py` with no arbitrary model-supplied command/executable/cwd/output path;
- additive Windows+Ubuntu `package-build` matrix in Python Core using fixed `python -m build --wheel --sdist --outdir dist` and `actions/upload-artifact@v4`;
- package job checkout explicitly pinned to `${{ github.event.pull_request.head.sha || github.sha }}` so the built bytes and evidence source SHA identify the same revision;
- exact per-platform package and GitHub Actions bundle hashes;
- no false requirement that Windows and Ubuntu archives be byte-identical.

Out of scope: store publishing, signing certificates, installers/update channels, unsupported macOS/iOS claims, generated-app framework builds and any arbitrary model-supplied build command.

## Accepted deliverables

- `src/kodepoia/quality/ci.py`;
- `src/kodepoia/quality/build.py`;
- `scripts/r6_8_collect_build.py`;
- `schemas/ci-report-v1.schema.json`;
- `schemas/build-manifest-v1.schema.json`;
- `tests/test_r6_8_ci_build.py`;
- quality exports;
- `build>=1.2,<2` development build frontend;
- additive package-build jobs in `.github/workflows/python-core.yml`;
- `docs/roadmap/R6_8_DESIGN.md`;
- `docs/roadmap/R6_8_ACCEPTANCE.md`.

## Accepted implementation identity and CI

- starting normalized main `fc7bd4d5803c451b4d343d08bcc212868ad24412`;
- accepted implementation head `d632669b93fda7b8397b9c3de43d78ca8726323f`;
- implementation PR #47;
- implementation merge `d570a3930ee63802882b8682e4532004d4fd81d6`;
- post-merge normalization PR #48 merge `92effbde1e432a8fcb6c794038d77367d034bcb0`;
- R0 Repository Guard `32571710663` / #783 — SUCCESS Windows + Ubuntu;
- Python Core `32571710718` / #757 — SUCCESS for `python-core-ubuntu-latest`, `python-core-windows-latest`, integrated `kodestudio-ui-windows`, `package-build-ubuntu-latest`, `package-build-windows-latest`;
- KodeStudio UI Smoke `32571710650` / #724 — SUCCESS Windows.

Both package jobs explicitly checked out `d632669b93fda7b8397b9c3de43d78ca8726323f`.

Ubuntu final package evidence:

- Ubuntu 24.04.4; Python 3.12.14;
- wheel 168,238 bytes, SHA-256 `35489ed602a9ade3816a4562f5cd751fbfb8924cd8ad780fba5bc7aa26a2a095`, validated;
- sdist 247,776 bytes, SHA-256 `b803d3f316f46ea461af853240ba8ab8bf3f867e0cff8e88e70f87bf678c1a78`, validated;
- build evidence `57e11b0a66e1f40d9984ae7aeacbe3874df5ce7b005657a72e6e603a63f983d8`;
- CI evidence `1a9f0e6dc0c099d5a7d9336d97a1e53ec40563cce90ba2a8c56e80b2eeb58869`;
- Actions bundle ID `9475481332`, ZIP SHA-256 `cdeef82ace3e0ca2ef0275b3111bf6d2c8f50213b20e777ddb436477e48261d8`.

Windows final package evidence:

- hosted Windows Server 2025; Python 3.12.10;
- wheel 169,444 bytes, SHA-256 `1406f5a2f180b56c611fb3a0cd8a9d23436682903405f52dadc26257c5b676fb`, validated;
- sdist 249,797 bytes, SHA-256 `42e63403069e61235cefa71ebbc4099b5e717e1528a6eae54ef0673f20e69edd`, validated;
- build evidence `248d49db9badfea775d18ca4087eb56ba053c961f888d5641dc42e62c6d8f419`;
- CI evidence `47ffad9f7f1d2c7af14efdc0f71e065b6b556046404069f2f02ef8b353024160`;
- Actions bundle ID `9475485133`, ZIP SHA-256 `aae159bd0d8a04ee4cec6c65f7a20f104c4679a9081432640419c4a6e74ccbe5`.

Both downloaded Actions bundles were independently inspected and contained wheel, sdist, build manifest and CI report. Both reports were PASS with zero blockers and exact source-SHA binding.

## Reproducibility and provenance interpretation

R6.8 does not claim cross-platform byte-identical archives. The immutable source identity is the exact Git SHA, while per-platform source/dependency/artifact digests record the bytes observed by each runner/toolchain. Different Windows/Ubuntu archive hashes are retained as evidence and are not mislabeled as regressions without a future explicit reproducible-build contract.

SLSA provenance concepts were used as reference context only. No SLSA level is claimed. GitHub artifact attestations were not made a mandatory routine PR-build gate because they are provenance evidence, not an artifact-safety guarantee, and frequent automated test builds do not require such attestations for this foundation.

## Manual intervention

**CONDITIONAL — NOT TRIGGERED.**

Hosted Windows on the exact final implementation head successfully checked out the correct SHA, built wheel+sdist, structurally validated both, recorded source/dependency/artifact hashes, emitted PASS/no-blocker CI/build evidence, uploaded the bundle and allowed independent bundle inspection. No acceptance-critical Windows behavior remained unproven; a user-local run would therefore add no required evidence.

## Post-merge normalization evidence

PR #48 head `0580f930d6dfaa387c1eda1cf8ad56de79cc42b9` passed R0 #790 `32572054011`, Python Core #764 `32572054001` including both package-build jobs, and KodeStudio UI Smoke #731 `32572054015`, then merged as `92effbde1e432a8fcb6c794038d77367d034bcb0`.

## Rollback / anti-regression

Do not remove or narrow existing R0/Python/UI checks. Package-build checkout must remain bound to the source SHA recorded in evidence. Required skipped/cancelled checks never PASS. Missing/invalid wheel/sdist remains blocking. Do not persist secrets. Do not add arbitrary model build commands/paths. Do not manufacture cross-platform byte reproducibility claims.

---

# R6.9 — KodeAppSecurity baseline — NEXT / NOT STARTED

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
- **R6.6 — NONE:** COMPLETE; no user action required.
- **R6.7 — NONE:** COMPLETE; no user action required.
- **R6.8 — CONDITIONAL:** NOT TRIGGERED; hosted Windows proved the final acceptance-critical package build/provenance behavior, so no user action is required.
- **R6.9 — NONE:** NEXT / NOT STARTED.
- **R6.10 — NONE:** PLANNED.
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

- 2026-08-22: retroactive plan created by explicit user request before R6.4; R6.1–R6.3 recorded from already accepted evidence; R6.4–R6.12 structure frozen.
- 2026-08-22: planning head `8fbad7c13dd65f9dcd49a03b33a3174fcf28d18a` passed R0 #639, Python Core #613 and UI Smoke #580; PR #37 merged as `0a91064608507966a47921df8fb36e5f25477141`.
- 2026-08-22: post-plan normalization PR #38 merged as `e96e7c3b168975869c911f880044b7ef8e322157`.
- 2026-08-22: R6.4 accepted on head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`; PR #39 merged as `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`; PR #40 normalized main to `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`.
- 2026-08-22: R6.5 accepted on head `06fd66af4b3a85da24b98ea2a5fbb2685358c540` after R0 #710, Python Core #684, UI Smoke #651 and required Windows keyboard/focus/Narrator `15 PASS / 0 FAIL / 15`; PR #41 merged as `db1a1ab78eb2ac7d90f75ab294074dec0238268c`; PR #42 normalized main to `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`.
- 2026-08-22: R6.6 accepted on head `6890b9d37722c74703e8b86f7de11dbfe66821ed` after R0 #733, Python Core #707 and UI Smoke #674; PR #43 merged as `f677cb34eade0549edc951fe11955de2bc0b270d`; PR #44 normalized main to `c5edd3c80ad9afec25997f1372d5f98ac861becc`.
- 2026-08-22: R6.7 accepted on head `0da49c7526b54f562827d63477b7ce8f1865de43` after R0 #756, Python Core #730 and UI Smoke #697; PR #45 merged as `3986b056654b25a73e45e5135ca3110a920c4bf5`; PR #46 normalized main to `fc7bd4d5803c451b4d343d08bcc212868ad24412`.
- 2026-08-22: R6.8 accepted on head `d632669b93fda7b8397b9c3de43d78ca8726323f` after R0 #783, Python Core #757 including Ubuntu+Windows package builds, UI Smoke #724 and downloaded artifact inspection; manual CONDITIONAL gate NOT TRIGGERED; PR #47 merged as `d570a3930ee63802882b8682e4532004d4fd81d6`; post-merge normalization PR #48 passed R0 #790, Python Core #764 and UI Smoke #731 then merged as `92effbde1e432a8fcb6c794038d77367d034bcb0`. R6.8 COMPLETE; R6.9 NEXT / NOT STARTED.
