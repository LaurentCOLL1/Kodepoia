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
6. **R6.6 — KodeLocalization + pseudo-localization foundation** — NEXT / NOT STARTED — manual `NONE`.
7. **R6.7 — KodeTechnicalDebt foundation** — PLANNED — manual `NONE`.
8. **R6.8 — KodeCI + KodeBuild foundation** — PLANNED — manual `CONDITIONAL`.
9. **R6.9 — KodeAppSecurity baseline** — PLANNED — manual `NONE`.
10. **R6.10 — KodePrivacy baseline** — PLANNED — manual `NONE`.
11. **R6.11 — KodeLicense + KodeBOM foundation** — PLANNED — manual `CONDITIONAL`.
12. **R6.12 — Major-patch validation + rollback gate and R6 integration acceptance** — PLANNED — manual `CONDITIONAL`.

The exact objective, implementation contract, acceptance gates, rollback/recovery, risks and manual procedures remain authoritative in `R6_PLAN.md`.

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

## Accepted R6.4 evidence

Accepted implementation head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`.

Hosted final-head evidence:

- R0 Repository Guard `32564304755` / #666 — SUCCESS Windows + Ubuntu;
- Python Core `32564304757` / #640 — SUCCESS Windows + Ubuntu, PowerShell validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32564304798` / #607 — SUCCESS Windows.

Required hardware-local evidence on the exact same head:

- Windows `Windows-11-10.0.26220-SP0`;
- Python `3.12.4`;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- rendering method `gl_compatibility`;
- rendering driver `opengl3`;
- video adapter `AMD Radeon RX 6750 XT`;
- baseline/current SHA-256 both `98dca538d872e8f883b4de4e9b92b741091365f15d193bac1127801277ca567a`;
- changed ratio `0.0`, perceptual distance ratio `0.0`;
- policy SHA-256 `a2dbb4532c50e522639a1b1a264420d2f491d17e7b2350d500ddf415bd70014e`;
- evidence SHA-256 `4c0375391d8f0e1b54c8c949b264ec70d6c9a18f10798a52a72d79ac18daab56`;
- VisualQA PASS;
- R6.3 hook `visual:godot-real-render` PASS;
- AuditLog chain valid;
- summary `8 PASS / 0 FAIL / 8`, `acceptance_completed=true`.

PR #39 merged as `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`; post-merge normalization PR #40 merged as `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`.

## Accepted R6.5 evidence

Accepted implementation head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`.

Hosted final-head evidence:

- R0 Repository Guard `32567824374` / #710 — SUCCESS Windows + Ubuntu;
- Python Core `32567824373` / #684 — SUCCESS Windows + Ubuntu, compilation, PowerShell runner syntax, full pytest and integrated KodeStudio accessibility UI smoke;
- KodeStudio UI Smoke `32567824370` / #651 — SUCCESS Windows.

Required interactive Windows evidence on the exact same head:

- Windows `Windows-11-10.0.26220-SP0`;
- Python `3.12.4`;
- KodeStudio main automated report: `343/343` applicable checks PASS, `0` failed, `0` warnings, `0` unknown, `0` blockers, evidence SHA-256 `9244424a8addb921822bae80de2d7c1a95733a10f04775dc7ec8b55194041920`;
- Project Wizard automated report: `318/318` applicable checks PASS, `0` failed, `0` warnings, `0` unknown, `0` blockers, evidence SHA-256 `e824358a8068d871f59fdbcc55092b300b572d34548d76b0c379973002ea2d91`;
- keyboard manual checks `5/5` PASS;
- visible/unobscured focus checks `2/2` PASS;
- Windows Narrator checks `6/6` PASS;
- manual total `13/13` PASS, `0` blocking failures;
- integrated summary `15 PASS / 0 FAIL / 15`;
- `metadata.acceptance_completed=true`;
- final local evidence `.kodepoia/diagnostics/accessibility/r6-5-local-acceptance.json`.

PR #41 merged as `db1a1ab78eb2ac7d90f75ab294074dec0238268c` after the hosted and required local evidence were reviewed, without changing the tested implementation head.

Accepted R6.5 scope includes structured accessibility evidence, explicit applicability/N/A semantics, anti-tamper report hashing, `WorkspaceBoundary` confinement, R6.3 hooks, deterministic contrast/target-size helpers, KodeStudio/Project Wizard accessible metadata, QAccessible name/role/state inspection, keyboard-focus audit, dynamic-control registration, Windows UI CI and a source-head-bound real keyboard/focus/Narrator acceptance contract.

The local run emitted non-blocking Qt font-directory / `propagateSizeHints()` notices, but both structured accessibility reports contained zero warnings, zero unknowns and zero blockers. They do not reopen R6.5; if still relevant they may be tracked later as technical debt.

**R6.1 = COMPLETE. R6.2 = COMPLETE. R6.3 = COMPLETE. R6.4 = COMPLETE. R6.5 = COMPLETE. R6 remains IN PROGRESS. R6.6 is NEXT / NOT STARTED.**

## Manual-intervention forecast

- R6.4 `REQUIRED`: SATISFIED and accepted; no further user action required unless a regression is demonstrated.
- R6.5 `REQUIRED`: SATISFIED and accepted; no further user action required unless a regression is demonstrated.
- R6.8 `CONDITIONAL`: local Windows build evidence only if hosted CI cannot satisfy build/reproducibility DoD.
- R6.11 `CONDITIONAL`: provenance/license evidence only if an acceptance-critical component remains ambiguous.
- R6.12 `CONDITIONAL`: local integration/user approval only if final selected gates require it.
- R6.6, R6.7, R6.9 and R6.10 currently require no user-side acceptance execution.

## Completion rule

R6 cannot be COMPLETE until R6.1–R6.12 are COMPLETE with all required CI/manual evidence, R6.12 integrated acceptance passes, and `R6_PLAN.md`, this file and continuity are synchronized on normalized `main`. Do not start R7 before that.
