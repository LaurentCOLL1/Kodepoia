# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R5 sont COMPLETE. R6 est IN PROGRESS. R6.1–R6.6 sont COMPLETE. Le plan exhaustif `docs/roadmap/R6_PLAN.md` est ACCEPTED et fige R6.1–R6.12. R6.7 — KodeTechnicalDebt foundation est IN PROGRESS sur `feature/r6-7-technical-debt`, PR #45, depuis le main normalisé `c5edd3c80ad9afec25997f1372d5f98ac861becc`.** R6.7 implémente IDs/fingerprints stables, lifecycle OPEN/ACCEPTED/RESOLVED, priorité déterministe, provenance/références, rapport anti-tamper, confinement WorkspaceBoundary, adaptateur KodeHealth et régression R6.3 pour nouvelle dette bloquante. Aucun gate manuel R6.7. Ne pas fusionner #45 avant CI verte du head final; ne pas commencer R6.8 avant merge + normalisation R6.7. Lire `R6_PLAN.md`, `R6_STATUS.md`, `R6_7_DESIGN.md`, `R6_7_ACCEPTANCE.md`, `R6_7_KNOWN_DEBT.md`, l'architecture gelée et ce fichier avant reprise. Ne pas rouvrir R1–R6.6 sans régression démontrée/ADR et ne pas passer à R7 avant R6 COMPLETE.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
- normalized `main` au démarrage R6.7 : `c5edd3c80ad9afec25997f1372d5f98ac861becc`.
- branche active : `feature/r6-7-technical-debt`.
- PR active : #45.
- R1–R5 : COMPLETE.
- R6 : IN PROGRESS.
- R6.1 : COMPLETE — PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.
- R6.2 : COMPLETE — PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`.
- R6.3 : COMPLETE — PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`.
- R6 plan : ACCEPTED — PR #37 merge `0a91064608507966a47921df8fb36e5f25477141`; normalization #38 `e96e7c3b168975869c911f880044b7ef8e322157`.
- R6.4 : COMPLETE — #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`; normalization #40 `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`; manual REQUIRED SATISFIED.
- R6.5 : COMPLETE — #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`; normalization #42 `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`; manual REQUIRED SATISFIED.
- R6.6 : COMPLETE — head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`; manual NONE.
- R6.7 : IN PROGRESS — PR #45 — manual NONE.
- R6.8 : PLANNED — manual CONDITIONAL.
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

- `WorkspaceBoundary` confinement and symlink rejection;
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
- exact-head final CI and no completion from partial evidence.

## R5 accepted local baseline / anti-regression

- Python 3.12.4; Windows 11 build 26220; Godot `4.7.2.stable.steam.ed1daf0bf`; AMD Radeon RX 6750 XT.
- R5 local acceptance 19/19 PASS.
- `ProcessSandbox.run()` drains PIPEs with `communicate(timeout=...)`.
- Long-lived socket services use sandboxed background execution.
- Real-render Godot evidence cannot be replaced by dummy/headless rendering when real rendering is required.
- DAP configuration sequencing and loopback-only Godot services remain protected.

## R6 frozen subdivision structure

1. R6.1 KodeHealth — COMPLETE — NONE.
2. R6.2 KodeBudget — COMPLETE — NONE.
3. R6.3 KodeTests + KodeRegression — COMPLETE — NONE.
4. R6.4 KodeVisualQA — COMPLETE — REQUIRED SATISFIED.
5. R6.5 KodeAccessibility — COMPLETE — REQUIRED SATISFIED.
6. R6.6 KodeLocalization + pseudo-localization — COMPLETE — NONE.
7. R6.7 KodeTechnicalDebt — IN PROGRESS — NONE.
8. R6.8 KodeCI + KodeBuild — PLANNED — CONDITIONAL.
9. R6.9 KodeAppSecurity — PLANNED — NONE.
10. R6.10 KodePrivacy — PLANNED — NONE.
11. R6.11 KodeLicense + KodeBOM — PLANNED — CONDITIONAL.
12. R6.12 major-patch validation/rollback + integrated R6 acceptance — PLANNED — CONDITIONAL.

Do not silently add/remove/merge/split/renumber any R6.N.

## R6.4–R6.6 evidence summary

### R6.4

- head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`;
- R0 #666, Python Core #640, UI Smoke #607 SUCCESS;
- local VisualQA 8/8 PASS, evidence SHA `4c0375391d8f0e1b54c8c949b264ec70d6c9a18f10798a52a72d79ac18daab56`;
- merge #39 `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`.

### R6.5

- head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`;
- R0 #710, Python Core #684, UI Smoke #651 SUCCESS;
- automated accessibility reports PASS and keyboard/focus/Narrator 13/13 manual PASS; integrated 15/15 PASS;
- merge #41 `db1a1ab78eb2ac7d90f75ab294074dec0238268c`.

### R6.6

- head `6890b9d37722c74703e8b86f7de11dbfe66821ed`;
- R0 #733 `32570001461`, Python Core #707 `32570001514`, UI Smoke #674 `32570001491` SUCCESS;
- stable IDs/form/placeholder/fallback checks, `qps-ploc`, hash/tamper report, WorkspaceBoundary store, R6.3 hook, KodeStudio pseudo-localized long-string smoke;
- merge #43 `f677cb34eade0549edc951fe11955de2bc0b270d`;
- normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`.

## R6.7 implementation contract/state

Current implementation includes:

- `src/kodepoia/quality/technical_debt.py`;
- schema `technical-debt-report-v1`;
- focused tests;
- design/acceptance docs and known-debt observation provenance;
- `DebtCategory`, `DebtSeverity`, `DebtState`, structured reference kinds;
- lifecycle rules: OPEN unresolved, ACCEPTED requires rationale and remains penalized, RESOLVED requires `resolved_at` and remains historical;
- accepted/resolved cannot remain blocking;
- priority = `severity_weight × impact × probability ÷ effort`, max 100;
- fingerprint = stable SHA-256 of category + normalized summary + scope + stable references, excluding timestamps/state;
- duplicate ID/fingerprint rejection;
- report PASS/WARN/FAIL + counts/blockers/ranking/debt penalty + canonical evidence hash;
- `.kodepoia/diagnostics/technical_debt/` through WorkspaceBoundary;
- Health `technical_debt` score/status/blocker adapter;
- R6.3 cases `technical-debt:<id>`; new blocking debt is an added FAIL and therefore regression.

Initial diagnostic CI: one fixture incorrectly expected priority 30; formula correctly yields `4×4×3÷2 = 24`, so only the test expectation was corrected. Diagnostic corrected head `ea6b5f478d8e0e01ff61c24f2c3a05f58a97f29d` passed Python Core Ubuntu+Windows and integrated UI smoke. Final authoritative CI must run on the later synchronized head.

Known observations with real provenance, not invented scanner results:

- pytest collection warnings for imported `Test*` quality classes;
- Pillow `Image.getdata()` deprecation warnings in VisualQA, removal announced for Pillow 14;
- R6.5 local Qt font/size-hint notices remain candidate environment debt only.

## R6.8 conditional manual forecast

R6.8 should normally be fully accepted in hosted Windows+Ubuntu CI. Trigger a local user gate only if hosted Windows cannot authoritatively prove an acceptance-critical Windows build/artifact property. If hosted Windows successfully builds and validates required package artifacts with exact source/artifact hashes, the condition is **NOT TRIGGERED** and no manual step should be invented.

If triggered, first freeze the final R6.8 head and document the hosted-CI limitation, then provide exact prerequisites/commands/output/recovery/evidence/do-not-do instructions.

## External reference baselines

- Unicode CLDR stable releases: locale-data context only for R6.6.
- WCAG 2.2 + WCAG2ICT 2.2: accessibility interpretation.
- SLSA v1.2: provenance concepts for R6.8; no SLSA-level claim without full proof.
- OWASP ASVS 5.0.0: later applicable AppSecurity surfaces.
- SPDX 3.0: later BOM baseline.

## Permanent phase-start planning rule

PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9` requires every new major phase from R7 onward to create and merge `docs/roadmap/RX_PLAN.md` before `RX.1`, enumerate all RX.N, detail scope/deliverables/acceptance/rollback/manual gates, and keep plan+continuity synchronized.

## Next action

Complete PR #45 only after final-head R0/Python Core/UI Smoke are all green. Then merge and normalize R6.7, making R6.8 NEXT / NOT STARTED. Do not start R6.8 before that normalization. Do not start R7.
