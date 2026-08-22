# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R5 sont COMPLETE. R6 est IN PROGRESS. R6.1–R6.7 sont COMPLETE. `docs/roadmap/R6_PLAN.md` est le plan exhaustif accepté et fige R6.1–R6.12. R6.8 — KodeCI + KodeBuild foundation est NEXT / NOT STARTED jusqu'à fusion de la normalisation post-R6.7.** R6.7 a été accepté sur le head exact `0da49c7526b54f562827d63477b7ce8f1865de43` après R0 #756, Python Core #730 et UI Smoke #697; PR #45 a été fusionnée en `3986b056654b25a73e45e5135ca3110a920c4bf5`; aucun gate manuel n'a été requis. Lire `R6_PLAN.md`, `R6_STATUS.md`, `R6_7_DESIGN.md`, `R6_7_ACCEPTANCE.md`, `R6_7_KNOWN_DEBT.md`, l'architecture gelée et ce fichier avant reprise. Ne pas rouvrir R1–R6.7 sans régression démontrée/ADR, ne pas renuméroter R6 sans mise à jour gouvernée et ne pas passer à R7 avant R6 COMPLETE.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
- R1–R5 : COMPLETE.
- R6 : IN PROGRESS.
- R6 plan : ACCEPTED — PR #37 merge `0a91064608507966a47921df8fb36e5f25477141`; normalization #38 `e96e7c3b168975869c911f880044b7ef8e322157`.
- R6.1 : COMPLETE — PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.
- R6.2 : COMPLETE — PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`.
- R6.3 : COMPLETE — PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`.
- R6.4 : COMPLETE — PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`; normalization #40 `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`; manual REQUIRED SATISFIED.
- R6.5 : COMPLETE — PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`; normalization #42 `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`; manual REQUIRED SATISFIED.
- R6.6 : COMPLETE — accepted head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`; manual NONE.
- R6.7 : COMPLETE — accepted head `0da49c7526b54f562827d63477b7ce8f1865de43`; PR #45 merge `3986b056654b25a73e45e5135ca3110a920c4bf5`; manual NONE.
- Normalisation post-R6.7 : branche `feature/r6-7-post-merge-normalization`; elle doit être CI-green et fusionnée avant R6.8.
- R6.8 : NEXT / NOT STARTED — manual CONDITIONAL.
- R6.9–R6.12 : PLANNED.
- R7–R16 : PENDING.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.
- Nontrivial Git/repository/software-engineering must not route to Granite.

## Permanent architecture/security boundaries

Preserve:

- `WorkspaceBoundary` confinement and symlink-escape rejection;
- `ProcessSandbox` + global KillSwitch;
- Guardian + `PermissionSet`;
- structured Tool APIs; no arbitrary model-supplied commands/argv/cwd/host;
- SafeChange before sensitive mutations;
- AuditLog hash chain;
- secrets redaction/exclusion;
- schema/DataGovernance discipline;
- structured Health/Budget/Test/Regression/VisualQA/Accessibility/Localization/TechnicalDebt evidence;
- platform-aware non-target behavior;
- ADR for foundation architecture changes;
- exact-head final CI and no completion from partial/wrong-environment evidence.

## R5 accepted local baseline / anti-regression

- Python 3.12.4; Windows 11 build 26220; Godot `4.7.2.stable.steam.ed1daf0bf`; AMD Radeon RX 6750 XT.
- R5 local acceptance 19/19 PASS.
- `ProcessSandbox.run()` drains PIPEs with `communicate(timeout=...)`.
- Long-lived socket services use sandboxed background execution.
- Real-render Godot evidence cannot be replaced by dummy/headless rendering when real rendering is required.
- DAP sequencing and loopback-only Godot services remain protected.

## Frozen R6 structure

1. R6.1 KodeHealth — COMPLETE — NONE.
2. R6.2 KodeBudget — COMPLETE — NONE.
3. R6.3 KodeTests + KodeRegression — COMPLETE — NONE.
4. R6.4 KodeVisualQA — COMPLETE — REQUIRED SATISFIED.
5. R6.5 KodeAccessibility — COMPLETE — REQUIRED SATISFIED.
6. R6.6 KodeLocalization + pseudo-localization — COMPLETE — NONE.
7. R6.7 KodeTechnicalDebt — COMPLETE — NONE.
8. R6.8 KodeCI + KodeBuild — NEXT / NOT STARTED — CONDITIONAL.
9. R6.9 KodeAppSecurity — PLANNED — NONE.
10. R6.10 KodePrivacy — PLANNED — NONE.
11. R6.11 KodeLicense + KodeBOM — PLANNED — CONDITIONAL.
12. R6.12 major-patch validation/rollback + integrated R6 acceptance — PLANNED — CONDITIONAL.

Do not silently add/remove/merge/split/renumber any R6.N.

## R6.4–R6.7 accepted evidence

### R6.4

- head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`;
- R0 #666, Python Core #640, UI Smoke #607 SUCCESS;
- local VisualQA 8/8 PASS, evidence SHA `4c0375391d8f0e1b54c8c949b264ec70d6c9a18f10798a52a72d79ac18daab56`;
- merge #39 `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`.

### R6.5

- head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`;
- R0 #710, Python Core #684, UI Smoke #651 SUCCESS;
- automated accessibility reports PASS; keyboard/focus/Narrator 13/13 manual PASS; integrated 15/15 PASS;
- merge #41 `db1a1ab78eb2ac7d90f75ab294074dec0238268c`.

### R6.6

- head `6890b9d37722c74703e8b86f7de11dbfe66821ed`;
- R0 #733 `32570001461`, Python Core #707 `32570001514`, UI Smoke #674 `32570001491` SUCCESS;
- stable localization IDs/forms/placeholders/fallback, `qps-ploc`, anti-tamper report, WorkspaceBoundary store, R6.3 hooks, KodeStudio long-string smoke;
- merge #43 `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`.

### R6.7

- accepted head `0da49c7526b54f562827d63477b7ce8f1865de43`;
- R0 #756 `32570711736` SUCCESS Windows + Ubuntu;
- Python Core #730 `32570711738` SUCCESS Windows + Ubuntu, PowerShell validation, pytest and integrated UI smoke;
- UI Smoke #697 `32570711732` SUCCESS Windows;
- stable debt IDs and lifecycle-independent fingerprints;
- OPEN/ACCEPTED/RESOLVED lifecycle with accepted debt visible and distinct from resolved debt;
- deterministic priority and duplicate fingerprint rejection;
- provenance/references, canonical anti-tamper report and WorkspaceBoundary persistence;
- Health `technical_debt` adapter;
- R6.3 stable `technical-debt:<id>` cases; newly introduced blocking debt = regression;
- merge #45 `3986b056654b25a73e45e5135ca3110a920c4bf5`.

R6.7 development finding: one test expected 30 for `4×4×3÷2`; the correct deterministic value is 24, so only the fixture expectation changed. Known non-blocking observations remain provenance-backed: pytest collection warnings for imported `Test*`, Pillow `Image.getdata()` deprecation and earlier Qt environment notices.

## R6.8 implementation contract / conditional manual forecast

R6.8 must convert CI/build activity into structured, source-SHA-bound evidence. Required semantics include explicit queued/in-progress/pass/fail/cancelled/skipped/unknown; skipped/cancelled never PASS; wheel+sdist builds on Windows+Ubuntu; artifact name/size/SHA-256; source/dependency-input digests; recursive secret redaction; `.kodepoia/workflows/` and `.kodepoia/releases/` via `WorkspaceBoundary`; Health `build` and R6.3 hooks; existing R0/Python/UI gates preserved; no unrestricted build command path.

Use current SLSA concepts and GitHub artifact provenance only as reference context. Do not claim a SLSA level merely because provenance fields or attestations exist.

**Manual R6.8 is CONDITIONAL.** Hosted Windows is authoritative if it builds and validates the required Windows/Python artifacts with exact source/artifact hashes. Trigger a local user gate only if a concrete acceptance-critical Windows behavior cannot be proven in hosted CI. If triggered, freeze the exact final head first, document the hosted limitation, then provide prerequisites, exact commands, expected output, error recovery, evidence requirements and what not to do yet.

## External reference baselines

- Unicode CLDR stable releases: locale-data context only for R6.6.
- WCAG 2.2 + WCAG2ICT 2.2: accessibility interpretation.
- SLSA v1.2: provenance concepts for R6.8; no SLSA-level claim without full proof.
- GitHub artifact attestations may link artifacts to repository/workflow/commit provenance, but attestation alone is not a security guarantee and is not automatically a R6.8 completion criterion.
- OWASP ASVS 5.0.0: later applicable AppSecurity surfaces.
- SPDX 3.0: later BOM baseline.

## Permanent phase-start planning rule

PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9` requires every new major phase from R7 onward to create and merge `docs/roadmap/RX_PLAN.md` before `RX.1`, enumerate all RX.N, detail scope/deliverables/acceptance/rollback/manual gates, and keep plan+continuity synchronized.

## Next action

Finish and merge the R6.7 post-merge normalization. Only then create R6.8 from that normalized `main`. Do not start R6.9 or R7.