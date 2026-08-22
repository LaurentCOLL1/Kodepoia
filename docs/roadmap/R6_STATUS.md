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
- planning PR #37 merged as `0a91064608507966a47921df8fb36e5f25477141`.

The plan records already accepted R6.1–R6.3 without reopening them and freezes R6.4–R6.12. **R6.4 is now NEXT / NOT STARTED and may begin only from normalized `main` after this post-merge normalization is merged.**

## Complete subdivision structure

1. **R6.1 — KodeHealth foundation** — COMPLETE — manual `NONE` — PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.
2. **R6.2 — KodeBudget foundation** — COMPLETE — manual `NONE` — PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`.
3. **R6.3 — KodeTests + KodeRegression foundation** — COMPLETE — manual `NONE` — PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`.
4. **R6.4 — KodeVisualQA foundation** — NEXT / NOT STARTED — manual `REQUIRED`.
5. **R6.5 — KodeAccessibility foundation** — PLANNED — manual `REQUIRED`.
6. **R6.6 — KodeLocalization + pseudo-localization foundation** — PLANNED — manual `NONE`.
7. **R6.7 — KodeTechnicalDebt foundation** — PLANNED — manual `NONE`.
8. **R6.8 — KodeCI + KodeBuild foundation** — PLANNED — manual `CONDITIONAL`.
9. **R6.9 — KodeAppSecurity baseline** — PLANNED — manual `NONE`.
10. **R6.10 — KodePrivacy baseline** — PLANNED — manual `NONE`.
11. **R6.11 — KodeLicense + KodeBOM foundation** — PLANNED — manual `CONDITIONAL`.
12. **R6.12 — Major-patch validation + rollback gate and R6 integration acceptance** — PLANNED — manual `CONDITIONAL`.

The exact objective, implementation contract, acceptance gates, rollback/recovery, risks and manual procedures are authoritative in `R6_PLAN.md`.

## Accepted R6.1 evidence

Accepted head `802de4ba3110ace657c4e16306a0ca29850ce2bd`.

- hardened focused tests: 9 PASS;
- R0 `32561211168` — SUCCESS Windows + Ubuntu;
- Python Core `32561211156` — SUCCESS Windows + Ubuntu;
- KodeStudio UI Smoke `32561211167` — SUCCESS Windows.

## Accepted R6.2 evidence

Accepted head `8ac3772e98c70260c320519a214bb25b6cedbb38`.

- isolated derivation/evaluation/persistence smoke: PASS;
- R0 `32561719921` / #603 — SUCCESS Windows + Ubuntu;
- Python Core `32561719925` / #577 — SUCCESS Windows + Ubuntu, PowerShell validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32561720008` / #544 — SUCCESS Windows.

## Accepted R6.3 evidence

Accepted head `7150237c263dd3ac96af4662d74909e05f3cf991`.

- isolated baseline/current comparison and persistence smoke: PASS;
- R0 `32562032986` / #622 — SUCCESS Windows + Ubuntu;
- Python Core `32562032998` / #596 — SUCCESS Windows + Ubuntu, PowerShell validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32562032982` / #563 — SUCCESS Windows.

**R6.1 = COMPLETE. R6.2 = COMPLETE. R6.3 = COMPLETE. R6 remains IN PROGRESS.**

## Manual-intervention forecast

- R6.4 `REQUIRED`: real Windows/Godot rendered visual-regression acceptance on the accepted workstation.
- R6.5 `REQUIRED`: real interactive Windows keyboard-only + Narrator accessibility checklist.
- R6.8 `CONDITIONAL`: local Windows build evidence only if hosted CI cannot satisfy build/reproducibility DoD.
- R6.11 `CONDITIONAL`: provenance/license evidence only if an acceptance-critical component remains ambiguous.
- R6.12 `CONDITIONAL`: local integration/user approval only if final selected gates require it.
- R6.6, R6.7, R6.9 and R6.10 currently require no user-side acceptance execution.

## Completion rule

R6 cannot be COMPLETE until R6.1–R6.12 are COMPLETE with all required CI/manual evidence, R6.12 integrated acceptance passes, and `R6_PLAN.md`, this file and continuity are synchronized on normalized `main`. Do not start R7 before that.
