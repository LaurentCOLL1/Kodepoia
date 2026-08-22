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
6. **R6.6 — KodeLocalization + pseudo-localization foundation** — COMPLETE — manual `NONE` — PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`.
7. **R6.7 — KodeTechnicalDebt foundation** — NEXT / NOT STARTED — manual `NONE`.
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

- R0 `32564304755` / #666 — SUCCESS Windows + Ubuntu;
- Python Core `32564304757` / #640 — SUCCESS Windows + Ubuntu;
- KodeStudio UI Smoke `32564304798` / #607 — SUCCESS Windows;
- required Windows/Godot/Radeon real-render acceptance: `8 PASS / 0 FAIL / 8`, `acceptance_completed=true`;
- PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`;
- post-merge normalization PR #40 merge `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`.

Detailed hashes/renderer evidence remain in `R6_4_ACCEPTANCE.md` and continuity.

## Accepted R6.5 evidence

Accepted implementation head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`.

- R0 `32567824374` / #710 — SUCCESS Windows + Ubuntu;
- Python Core `32567824373` / #684 — SUCCESS Windows + Ubuntu;
- KodeStudio UI Smoke `32567824370` / #651 — SUCCESS Windows;
- required Windows keyboard/focus/Narrator evidence: two automated reports PASS, `13/13` manual PASS, integrated `15 PASS / 0 FAIL / 15`, `acceptance_completed=true`;
- PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`;
- post-merge normalization PR #42 merge `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`.

Detailed accessibility evidence hashes/counts remain in `R6_5_ACCEPTANCE.md` and continuity.

## Accepted R6.6 evidence

Accepted implementation head `6890b9d37722c74703e8b86f7de11dbfe66821ed`.

Final hosted evidence:

- R0 Repository Guard `32570001461` / #733 — SUCCESS Windows + Ubuntu;
- Python Core `32570001514` / #707 — SUCCESS Windows + Ubuntu, PowerShell validation and integrated KodeStudio UI smoke;
- KodeStudio UI Smoke `32570001491` / #674 — SUCCESS Windows.

Accepted scope:

- stable locale/message IDs and duplicate rejection;
- exact message-form and placeholder parity;
- explicit source fallback and target-only-key warnings;
- deterministic `qps-ploc` pseudo-localization preserving placeholders/markup/entities;
- canonical evidence hashing and tamper checks;
- `.kodepoia/diagnostics/localization/` confinement through `WorkspaceBoundary`;
- R6.3 localization hooks;
- KodeStudio stable source-message registry with English production default;
- pseudo-localized Windows long-string/navigation smoke while retaining R6.5 accessibility smoke.

Development CI initially exposed two Python object-equality assertions caused by canonical `details={}` versus in-memory `details=None`. Tests were corrected to compare the canonical serialized evidence used for hashing/persistence; no validation or security rule was weakened.

PR #43 merged as `f677cb34eade0549edc951fe11955de2bc0b270d` after final-head CI passed. Manual intervention was `NONE`.

**R6.1–R6.6 = COMPLETE. R6 remains IN PROGRESS. R6.7 = NEXT / NOT STARTED until this post-merge normalization is merged.**

## Manual-intervention forecast

- R6.4 `REQUIRED`: SATISFIED and accepted.
- R6.5 `REQUIRED`: SATISFIED and accepted.
- R6.6 `NONE`: COMPLETE; no user action required.
- R6.7 `NONE`: no user-side acceptance currently planned.
- R6.8 `CONDITIONAL`: local Windows build evidence only if hosted CI cannot authoritatively satisfy its build/provenance DoD.
- R6.11 `CONDITIONAL`: provenance/license evidence only if an acceptance-critical component remains ambiguous.
- R6.12 `CONDITIONAL`: local integration/user approval only if final selected gates require it.
- R6.9 and R6.10 currently require no user-side acceptance execution.

## Completion rule

R6 cannot be COMPLETE until R6.1–R6.12 are COMPLETE with all required CI/manual evidence, R6.12 integrated acceptance passes, and `R6_PLAN.md`, this file and continuity are synchronized on normalized `main`. Do not start R7 before that.
