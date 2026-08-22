# R6 — Quality / Health / Budget / CI — Status

**Phase:** R6  
**Status:** IN PROGRESS  
**Started:** 2026-08-22  
**Detailed phase plan:** `docs/roadmap/R6_PLAN.md` — ACCEPTED

R1–R5 remain COMPLETE. R6 is active under the frozen architecture v1.0.

## Detailed R6 plan acceptance

R6 began before the permanent `RX_PLAN.md` governance rule existed. By explicit user request, the missing detailed R6 plan was reconstructed and accepted before R6.4.

Accepted planning evidence:

- planning head `8fbad7c13dd65f9dcd49a03b33a3174fcf28d18a`;
- R0 Repository Guard `32563057993` / #639 — SUCCESS Windows + Ubuntu;
- Python Core `32563057956` / #613 — SUCCESS Windows + Ubuntu, PowerShell validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32563057903` / #580 — SUCCESS Windows;
- planning PR #37 merged as `0a91064608507966a47921df8fb36e5f25477141`;
- post-plan normalization PR #38 merged as `e96e7c3b168975869c911f880044b7ef8e322157`.

## Complete subdivision structure

1. **R6.1 — KodeHealth foundation** — COMPLETE — manual `NONE` — PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.
2. **R6.2 — KodeBudget foundation** — COMPLETE — manual `NONE` — PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`.
3. **R6.3 — KodeTests + KodeRegression foundation** — COMPLETE — manual `NONE` — PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`.
4. **R6.4 — KodeVisualQA foundation** — COMPLETE — manual `REQUIRED` SATISFIED — PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`.
5. **R6.5 — KodeAccessibility foundation** — COMPLETE — manual `REQUIRED` SATISFIED — PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`.
6. **R6.6 — KodeLocalization + pseudo-localization foundation** — COMPLETE — manual `NONE` — PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`, normalization #44 merge `c5edd3c80ad9afec25997f1372d5f98ac861becc`.
7. **R6.7 — KodeTechnicalDebt foundation** — IN PROGRESS — manual `NONE` — branch `feature/r6-7-technical-debt`, PR #45, base `c5edd3c80ad9afec25997f1372d5f98ac861becc`.
8. **R6.8 — KodeCI + KodeBuild foundation** — PLANNED — manual `CONDITIONAL`.
9. **R6.9 — KodeAppSecurity baseline** — PLANNED — manual `NONE`.
10. **R6.10 — KodePrivacy baseline** — PLANNED — manual `NONE`.
11. **R6.11 — KodeLicense + KodeBOM foundation** — PLANNED — manual `CONDITIONAL`.
12. **R6.12 — Major-patch validation + rollback gate and R6 integration acceptance** — PLANNED — manual `CONDITIONAL`.

The exact objective, implementation contract, acceptance gates, rollback/recovery, risks and manual procedures remain authoritative in `R6_PLAN.md`.

## Accepted R6.1–R6.6 evidence

R6.1 accepted head `802de4ba3110ace657c4e16306a0ca29850ce2bd`; R0 `32561211168`, Python Core `32561211156`, UI Smoke `32561211167` SUCCESS.

R6.2 accepted head `8ac3772e98c70260c320519a214bb25b6cedbb38`; R0 #603 `32561719921`, Python Core #577 `32561719925`, UI Smoke #544 `32561720008` SUCCESS.

R6.3 accepted head `7150237c263dd3ac96af4662d74909e05f3cf991`; R0 #622 `32562032986`, Python Core #596 `32562032998`, UI Smoke #563 `32562032982` SUCCESS.

R6.4 accepted head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`; R0 #666, Python Core #640, UI Smoke #607 SUCCESS; required real Windows/Godot/Radeon gate `8 PASS / 0 FAIL / 8`; PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`; normalization #40 `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`.

R6.5 accepted head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`; R0 #710, Python Core #684, UI Smoke #651 SUCCESS; required Windows accessibility `15 PASS / 0 FAIL / 15`; PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`; normalization #42 `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`.

R6.6 accepted head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; R0 #733 `32570001461`, Python Core #707 `32570001514`, UI Smoke #674 `32570001491` SUCCESS; PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`; manual NONE.

## R6.7 implementation state

R6.7 is active on PR #45 from normalized main `c5edd3c80ad9afec25997f1372d5f98ac861becc`.

Implemented scope:

- stable debt IDs and SHA-256 duplicate fingerprints based on category/summary/scope/references;
- `OPEN`, `ACCEPTED`, `RESOLVED` lifecycle invariants;
- accepted debt requires rationale and remains visible/penalized rather than becoming resolved;
- structured category/severity/impact/probability/effort/owner/scope/source/provenance;
- structured file/symbol/test/requirement/issue references;
- timezone-aware first/last/review/expiry/resolution evidence;
- deterministic priority `severity_weight × impact × probability ÷ effort`, max 100;
- report PASS/WARN/FAIL, derived counts/blockers/ranking/debt penalty;
- canonical SHA-256 anti-tamper evidence;
- `technical-debt-report-v1` schema;
- `.kodepoia/diagnostics/technical_debt/` confinement through `WorkspaceBoundary`;
- KodeHealth `technical_debt` adapter;
- stable R6.3 `technical-debt:<id>` cases where newly added blocking debt becomes an added FAIL/regression;
- known-debt observations documented with actual provenance rather than pretending an unexecuted scanner ran.

Initial CI found one incorrect test expectation: critical severity with impact 4, probability 3 and effort 2 evaluates to `4×4×3÷2 = 24`, not 30. The fixture was corrected; the deterministic formula was not changed.

The same CI logs reproduced existing non-blocking candidates for later register population: pytest collection warnings around imported `Test*` symbols and Pillow `Image.getdata()` deprecation warnings. They are observations, not fabricated scanner results.

A corrected implementation head `ea6b5f478d8e0e01ff61c24f2c3a05f58a97f29d` already passed Python Core Ubuntu+Windows and integrated KodeStudio smoke in diagnostic CI; final authoritative evidence will be taken only from the later head that also includes this status/plan/continuity synchronization.

**R6.7 remains IN PROGRESS and must not merge until final-head R0, Python Core and UI Smoke all succeed. R6.8 must not start earlier.**

## Manual-intervention forecast

- R6.4 `REQUIRED`: SATISFIED.
- R6.5 `REQUIRED`: SATISFIED.
- R6.6 `NONE`: COMPLETE.
- R6.7 `NONE`: no user-side acceptance required.
- R6.8 `CONDITIONAL`: local Windows build evidence only if hosted CI cannot authoritatively satisfy its build/provenance DoD.
- R6.11 `CONDITIONAL`: provenance/license evidence only if acceptance-critical ambiguity remains.
- R6.12 `CONDITIONAL`: local integration/user approval only if selected final gates require it.
- R6.9 and R6.10 currently require no user-side execution.

## Completion rule

R6 cannot be COMPLETE until R6.1–R6.12 are COMPLETE with all required evidence, R6.12 integrated acceptance passes, and `R6_PLAN.md`, this file and continuity are synchronized on normalized `main`. Do not start R7 before that.
