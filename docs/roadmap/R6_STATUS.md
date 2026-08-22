# R6 — Quality / Health / Budget / CI — Status

**Phase:** R6  
**Status:** IN PROGRESS  
**Started:** 2026-08-22  
**Detailed phase plan:** `docs/roadmap/R6_PLAN.md` — ACCEPTED  
**Architecture:** v1.0 frozen

R1–R5 remain COMPLETE. R6 remains active and must not be marked COMPLETE before R6.12 integrated acceptance and final normalization.

## Detailed R6 plan acceptance

The exhaustive R6 plan was reconstructed and accepted before R6.4 because R6.1–R6.3 predated the permanent `RX_PLAN.md` rule.

- planning head `8fbad7c13dd65f9dcd49a03b33a3174fcf28d18a`;
- R0 #639 `32563057993` — SUCCESS Windows + Ubuntu;
- Python Core #613 `32563057956` — SUCCESS Windows + Ubuntu, PowerShell validation and integrated KodeStudio smoke;
- UI Smoke #580 `32563057903` — SUCCESS Windows;
- planning PR #37 merge `0a91064608507966a47921df8fb36e5f25477141`;
- planning normalization PR #38 merge `e96e7c3b168975869c911f880044b7ef8e322157`.

## Frozen subdivision structure

1. **R6.1 — KodeHealth foundation** — COMPLETE — manual `NONE` — PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.
2. **R6.2 — KodeBudget foundation** — COMPLETE — manual `NONE` — PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`.
3. **R6.3 — KodeTests + KodeRegression foundation** — COMPLETE — manual `NONE` — PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`.
4. **R6.4 — KodeVisualQA foundation** — COMPLETE — manual `REQUIRED` SATISFIED — PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`.
5. **R6.5 — KodeAccessibility foundation** — COMPLETE — manual `REQUIRED` SATISFIED — PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`.
6. **R6.6 — KodeLocalization + pseudo-localization foundation** — COMPLETE — manual `NONE` — PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 merge `c5edd3c80ad9afec25997f1372d5f98ac861becc`.
7. **R6.7 — KodeTechnicalDebt foundation** — COMPLETE — manual `NONE` — accepted head `0da49c7526b54f562827d63477b7ce8f1865de43`; PR #45 merge `3986b056654b25a73e45e5135ca3110a920c4bf5`.
8. **R6.8 — KodeCI + KodeBuild foundation** — NEXT / NOT STARTED — manual `CONDITIONAL`.
9. **R6.9 — KodeAppSecurity baseline** — PLANNED — manual `NONE`.
10. **R6.10 — KodePrivacy baseline** — PLANNED — manual `NONE`.
11. **R6.11 — KodeLicense + KodeBOM foundation** — PLANNED — manual `CONDITIONAL`.
12. **R6.12 — Major-patch validation + rollback gate and R6 integration acceptance** — PLANNED — manual `CONDITIONAL`.

No subdivision may be silently added, removed, merged, split or renumbered.

## Accepted evidence summary

### R6.1

Accepted head `802de4ba3110ace657c4e16306a0ca29850ce2bd`; R0 `32561211168`, Python Core `32561211156`, UI Smoke `32561211167` SUCCESS.

### R6.2

Accepted head `8ac3772e98c70260c320519a214bb25b6cedbb38`; R0 #603 `32561719921`, Python Core #577 `32561719925`, UI Smoke #544 `32561720008` SUCCESS.

### R6.3

Accepted head `7150237c263dd3ac96af4662d74909e05f3cf991`; R0 #622 `32562032986`, Python Core #596 `32562032998`, UI Smoke #563 `32562032982` SUCCESS.

### R6.4

Accepted head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`; R0 #666, Python Core #640 and UI Smoke #607 SUCCESS; required real Windows/Godot/Radeon gate `8 PASS / 0 FAIL / 8`; normalization #40 `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`.

### R6.5

Accepted head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`; R0 #710, Python Core #684 and UI Smoke #651 SUCCESS; required Windows accessibility gate `15 PASS / 0 FAIL / 15`; normalization #42 `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`.

### R6.6

Accepted head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; R0 #733 `32570001461`, Python Core #707 `32570001514`, UI Smoke #674 `32570001491` SUCCESS; PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`; manual NONE.

### R6.7

Accepted implementation head `0da49c7526b54f562827d63477b7ce8f1865de43`.

Final hosted evidence on that exact head:

- R0 Repository Guard #756 `32570711736` — SUCCESS Windows + Ubuntu;
- Python Core #730 `32570711738` — SUCCESS Windows + Ubuntu, PowerShell syntax, full pytest and integrated KodeStudio UI smoke;
- KodeStudio UI Smoke #697 `32570711732` — SUCCESS Windows.

Accepted scope includes stable debt IDs/fingerprints, OPEN/ACCEPTED/RESOLVED lifecycle, deterministic priority, structured provenance/references, anti-tamper evidence, `WorkspaceBoundary` confinement, Health `technical_debt` adapter and stable R6.3 cases where newly introduced blocking debt becomes a regression.

Development CI found one fixture expectation error: `4 × 4 × 3 ÷ 2 = 24`, not 30. Only the test expectation changed; the deterministic formula did not. Hosted logs also reproduced non-blocking debt candidates (`PytestCollectionWarning` on imported `Test*` symbols and Pillow `Image.getdata()` deprecation); these are provenance-backed observations, not fabricated scanner results.

PR #45 merged as `3986b056654b25a73e45e5135ca3110a920c4bf5`. Manual intervention: **NONE**.

**R6.1–R6.7 = COMPLETE. R6.8 = NEXT / NOT STARTED until this post-merge normalization is CI-green and merged. R6 remains IN PROGRESS.**

## Manual-intervention forecast

- R6.4 `REQUIRED`: SATISFIED.
- R6.5 `REQUIRED`: SATISFIED.
- R6.6 `NONE`: COMPLETE.
- R6.7 `NONE`: COMPLETE.
- R6.8 `CONDITIONAL`: trigger a local Windows build gate only if hosted Windows cannot authoritatively satisfy an acceptance-critical build/provenance requirement. If hosted Windows builds and validates the required artifacts with exact source/artifact hashes, the condition is **NOT TRIGGERED**.
- R6.9 and R6.10: `NONE` currently planned.
- R6.11 `CONDITIONAL`: only for unresolved acceptance-critical license/provenance ambiguity.
- R6.12 `CONDITIONAL`: only if selected final gates require local hardware execution or explicit approval.

## Completion rule

R6 cannot be COMPLETE until R6.1–R6.12 are COMPLETE with all required evidence, R6.12 integrated acceptance passes, and `R6_PLAN.md`, this file and continuity are synchronized on normalized `main`. Do not start R7 before that.