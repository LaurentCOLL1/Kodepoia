# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R5 sont COMPLETE. R6 est IN PROGRESS. R6.1 KodeHealth, R6.2 KodeBudget, R6.3 KodeTests + KodeRegression, R6.4 KodeVisualQA, R6.5 KodeAccessibility et R6.6 KodeLocalization + pseudo-localization sont COMPLETE. `docs/roadmap/R6_PLAN.md` est le plan exhaustif accepté et fige R6.1–R6.12. R6.7 — KodeTechnicalDebt foundation est NEXT / NOT STARTED jusqu'à la fusion de la normalisation post-R6.6.** R6.6 a été accepté sur le head exact `6890b9d37722c74703e8b86f7de11dbfe66821ed` après R0 #733, Python Core #707 et UI Smoke #674, sans intervention manuelle; PR #43 a été fusionnée en `f677cb34eade0549edc951fe11955de2bc0b270d`. Lire `R6_PLAN.md`, `R6_STATUS.md`, `R6_6_ACCEPTANCE.md`, les documents R6.4/R6.5, l'architecture gelée et ce fichier avant reprise. Ne pas rouvrir R1–R6.6 sans régression démontrée/ADR, ne pas renuméroter R6 sans mise à jour gouvernée, et ne pas passer à R7 avant R6 COMPLETE.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
- Source de vérité avant la normalisation R6.6 : implementation merge `f677cb34eade0549edc951fe11955de2bc0b270d`.
- Branche de normalisation active : `feature/r6-6-post-merge-normalization`.
- R1 : COMPLETE.
- R2 : COMPLETE.
- R3 : COMPLETE — hardware-local model acceptance passed.
- R4 : COMPLETE — governed KodeCode acceptance passed.
- R5 : COMPLETE — KodeGodot 4.7.x hardware-local acceptance passed.
- R6 : IN PROGRESS.
- R6.1 : COMPLETE — PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.
- R6.2 : COMPLETE — PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`.
- R6.3 : COMPLETE — PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`.
- R6 plan : ACCEPTED — PR #37 merge `0a91064608507966a47921df8fb36e5f25477141`; normalization #38 `e96e7c3b168975869c911f880044b7ef8e322157`.
- R6.4 : COMPLETE — PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`; normalization #40 `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`; manual REQUIRED SATISFIED.
- R6.5 : COMPLETE — PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`; normalization #42 `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`; manual REQUIRED SATISFIED.
- R6.6 : COMPLETE — accepted head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`; manual NONE.
- R6.7 : NEXT / NOT STARTED — manual NONE.
- R6.8 : PLANNED — manual CONDITIONAL.
- R6.9–R6.12 : PLANNED in `R6_PLAN.md`.
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
- secrets redaction/exclusion from LLM context and persistent memory;
- schema/DataGovernance discipline;
- structured Health/Budget/Test/Regression/VisualQA/Accessibility/Localization evidence;
- platform-aware behavior: non-target platforms must not impose requirements/dependencies/inputs/budgets/tests;
- architecture-foundation changes require ADR;
- no completion from partial CI or wrong-SHA/wrong-environment evidence.

## R5 hardware-local baseline and anti-regression

Accepted local environment:

- Python `3.12.4`;
- Windows 11 build `26220`;
- Godot `4.7.2.stable.steam.ed1daf0bf` at `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- LSP 6005, DAP 6006, debug 6007;
- AMD Radeon RX 6750 XT;
- acceptance `19 PASS / 0 FAIL / 19`, `acceptance_completed=true`.

Rules that must not regress:

1. `ProcessSandbox.run()` drains stdout/stderr with `communicate(timeout=...)`.
2. Long-lived socket services use the background sandbox path when stdio is not protocol; no unread PIPEs.
3. Real Godot Movie Maker capture cannot be replaced with headless/dummy rendering when real-render evidence is required.
4. TCP connection timeout cannot remain a protocol-read timeout after connect.
5. DAP launch supports deferred response sequencing through `configurationDone`.
6. Godot services remain loopback-only; model input cannot expose arbitrary host/argv/command/program/cwd.

## R6 exhaustive structure — frozen

1. R6.1 — KodeHealth — COMPLETE — manual NONE.
2. R6.2 — KodeBudget — COMPLETE — manual NONE.
3. R6.3 — KodeTests + KodeRegression — COMPLETE — manual NONE.
4. R6.4 — KodeVisualQA — COMPLETE — manual REQUIRED SATISFIED.
5. R6.5 — KodeAccessibility — COMPLETE — manual REQUIRED SATISFIED.
6. R6.6 — KodeLocalization + pseudo-localization — COMPLETE — manual NONE.
7. R6.7 — KodeTechnicalDebt — NEXT / NOT STARTED — manual NONE.
8. R6.8 — KodeCI + KodeBuild — PLANNED — manual CONDITIONAL.
9. R6.9 — KodeAppSecurity baseline — PLANNED — manual NONE.
10. R6.10 — KodePrivacy baseline — PLANNED — manual NONE.
11. R6.11 — KodeLicense + KodeBOM — PLANNED — manual CONDITIONAL.
12. R6.12 — major-patch validation + rollback gate + integrated R6 acceptance — PLANNED — manual CONDITIONAL.

Do not silently add/remove/merge/split/renumber R6.N. Update plan + status + continuity in the same work cycle. Architecture changes require ADR.

## Accepted R6.1–R6.3 evidence

### R6.1

- head `802de4ba3110ace657c4e16306a0ca29850ce2bd`;
- PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`;
- R0 `32561211168`, Python Core `32561211156`, UI Smoke `32561211167` — SUCCESS.

### R6.2

- head `8ac3772e98c70260c320519a214bb25b6cedbb38`;
- PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`;
- R0 #603 `32561719921`, Python Core #577 `32561719925`, UI Smoke #544 `32561720008` — SUCCESS.

### R6.3

- head `7150237c263dd3ac96af4662d74909e05f3cf991`;
- PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`;
- R0 #622 `32562032986`, Python Core #596 `32562032998`, UI Smoke #563 `32562032982` — SUCCESS.

## R6.4 — COMPLETE

- accepted head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`;
- R0 #666 `32564304755`, Python Core #640 `32564304757`, UI Smoke #607 `32564304798` — SUCCESS;
- real Windows/Godot/Radeon VisualQA gate `8 PASS / 0 FAIL / 8`, `acceptance_completed=true`;
- evidence SHA-256 `4c0375391d8f0e1b54c8c949b264ec70d6c9a18f10798a52a72d79ac18daab56`;
- PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`;
- normalization #40 `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`.

## R6.5 — COMPLETE

- accepted head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`;
- R0 #710 `32567824374`, Python Core #684 `32567824373`, UI Smoke #651 `32567824370` — SUCCESS;
- automated KodeStudio accessibility 343 applicable PASS, zero blockers, SHA `9244424a8addb921822bae80de2d7c1a95733a10f04775dc7ec8b55194041920`;
- Project Wizard 318 applicable PASS, zero blockers, SHA `e824358a8068d871f59fdbcc55092b300b572d34548d76b0c379973002ea2d91`;
- keyboard 5/5, focus 2/2, Narrator 6/6; integrated `15 PASS / 0 FAIL / 15`, `acceptance_completed=true`;
- PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`;
- normalization #42 `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`.

R6.5 lessons:

- symlink escape correctly raises `WorkspaceViolation`; do not weaken boundary policy;
- only Qt-owned `QTabBar` internal scroll buttons are excluded from application-control discovery;
- focus-policy enum conversion was hardened;
- local Qt font-directory/`propagateSizeHints()` notices did not produce structured accessibility failures and may be considered later technical debt if still relevant.

## R6.6 — COMPLETE

Accepted identity:

- base normalized main `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`;
- branch `feature/r6-6-localization`;
- accepted head `6890b9d37722c74703e8b86f7de11dbfe66821ed`;
- PR #43;
- merge `f677cb34eade0549edc951fe11955de2bc0b270d`;
- manual NONE.

Accepted hosted evidence:

- R0 Repository Guard `32570001461` / #733 — SUCCESS Windows + Ubuntu;
- Python Core `32570001514` / #707 — SUCCESS Windows + Ubuntu, PowerShell syntax and integrated KodeStudio UI smoke;
- KodeStudio UI Smoke `32570001491` / #674 — SUCCESS Windows.

Accepted scope:

- stable locale/message IDs and source locale;
- duplicate-key/form/placeholder validation;
- missing source keys and form/placeholder mismatches block;
- target-only keys and missing fallback are explicit WARN rather than false PASS;
- explicit source fallback;
- deterministic `qps-ploc` pseudo-localization preserving placeholders, markup and entities;
- canonical evidence SHA-256/tamper checks;
- `.kodepoia/diagnostics/localization/` through `WorkspaceBoundary`;
- R6.3 stable localization hooks;
- KodeStudio source-message registry on the registered main surface;
- English production default preserved;
- pseudo-localized long-string navigation/button/window smoke and adaptive nav width;
- R6.5 accessibility smoke remains green.

Development lesson: initial round-trip test object equality distinguished `details=None` from canonical serialized `details={}`. Tests now compare the canonical persisted/hashed representation. No validator/blocker/security rule was relaxed.

## R6.7 next-action contract

Do not begin R6.7 until the R6.6 normalization PR is CI-green and merged. Then create `feature/r6-7-technical-debt` from normalized `main`.

R6.7 must implement, without arbitrary scanner shell execution:

- stable debt IDs and stable duplicate fingerprints;
- category/severity/impact/probability/effort;
- scope/source/provenance/owner and file/symbol/test/requirement references;
- first-seen/last-seen plus explicit open/accepted/resolved lifecycle;
- accepted rationale and optional review/expiry;
- deterministic priority/ranking;
- `.kodepoia/diagnostics/technical_debt/` confinement;
- schema/report anti-tamper checks;
- Health `technical_debt` adapter;
- R6.3 regression semantics for newly introduced blocking debt;
- tests/design/acceptance docs;
- no manual gate.

Known repository observations suitable for representing as debt evidence if still current and verified during R6.7 include Pillow `Image.getdata()` deprecation warnings, pytest collection warnings caused by imported `Test*` symbols, and non-blocking Qt font/size-hint notices. Do not invent a scanner run; label provenance accurately.

## R6.8 manual-gate forecast

R6.8 is **CONDITIONAL**. It should normally be accepted entirely in hosted Windows+Ubuntu CI. A local user gate is triggered only if hosted Windows cannot prove an acceptance-critical Windows package/build artifact behavior.

Before any triggered R6.8 user action:

- implementation head must be frozen;
- hosted CI limitation must be explicitly documented;
- exact command/script must exist;
- instructions must include prerequisites, exact commands, expected output, failure recovery, evidence to send, security/privacy notes and what not to do yet.

If hosted Windows can build and validate the required artifacts with exact source/artifact hashes, the condition is NOT TRIGGERED and no manual intervention should be invented.

## Current external reference baselines

- Localization: stable Unicode CLDR releases are context for locale conventions only; no CLDR dependency or completeness claim in R6.6.
- Accessibility: WCAG 2.2 + WCAG2ICT 2.2 interpretation for non-Web software.
- R6.8 build provenance: current SLSA v1.2 concepts may inform source-SHA/artifact-digest provenance, but no SLSA level may be claimed without separately meeting/proving all requirements.
- AppSecurity: OWASP ASVS 5.0.0 only for applicable surfaces.
- BOM: SPDX 3.0 stable baseline.

## Permanent phase-start planning rule

Adopted via PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9`. For every newly started major phase from R7 onward:

1. create `docs/roadmap/RX_PLAN.md` from `PHASE_PLAN_TEMPLATE.md` before `RX.1`;
2. enumerate every planned `RX.N` with detailed objective/scope/dependencies/implementation/deliverables/acceptance/evidence/rollback/risks;
3. classify each `NONE`, `REQUIRED` or `CONDITIONAL` for manual intervention;
4. pre-document reason/prerequisites/actions/expected output/recovery/evidence/do-not-do-yet/privacy-security for manual gates;
5. planning PR final-head checks pass and plan merges before implementation;
6. keep plan + continuity synchronized;
7. scope renumber/add/remove/merge/split requires explicit rationale and ADR if architecture changes;
8. major phase COMPLETE only when every planned subdivision is COMPLETE or explicitly removed by governed decision.

## Next action

Finish only the **R6.6 post-merge normalization**. Once merged, start **R6.7 KodeTechnicalDebt** from the resulting normalized `main`. Do not start R6.8 before R6.7 is accepted/merged/normalized. Do not start R7.

## Permanent process rules

- Update active phase plan, status and continuity in the same work cycle whenever subdivision/phase status, PR state, acceptance, prerequisites, manual requirements or important defects change.
- Never mark phase/subdivision COMPLETE from partial CI or unsupported claims.
- Use exact accepted head/PR/run/merge evidence.
- Preserve frozen architecture unless ADR authorizes a foundation change.
- No manual acceptance by inference from silence, partial logs/screenshots or wrong-environment evidence.
- Never ask for passwords, tokens, private keys or unrelated personal data; require redaction where logs can contain secrets.
