# R6 — Quality / Health / Budget / CI — Status

**Phase:** R6  
**Status:** IN PROGRESS  
**Started:** 2026-08-22  
**Detailed phase plan:** `docs/roadmap/R6_PLAN.md` — ACCEPTED  
**Architecture:** v1.0 frozen

R1–R5 remain COMPLETE. R6 remains active and must not be marked COMPLETE before R6.12 integrated acceptance and final normalization.

## Frozen subdivision structure

1. **R6.1 — KodeHealth foundation** — COMPLETE — manual `NONE` — PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.
2. **R6.2 — KodeBudget foundation** — COMPLETE — manual `NONE` — PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`.
3. **R6.3 — KodeTests + KodeRegression foundation** — COMPLETE — manual `NONE` — PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`.
4. **R6.4 — KodeVisualQA foundation** — COMPLETE — manual `REQUIRED` SATISFIED — PR #39 merge `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`.
5. **R6.5 — KodeAccessibility foundation** — COMPLETE — manual `REQUIRED` SATISFIED — PR #41 merge `db1a1ab78eb2ac7d90f75ab294074dec0238268c`.
6. **R6.6 — KodeLocalization + pseudo-localization foundation** — COMPLETE — manual `NONE` — PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`.
7. **R6.7 — KodeTechnicalDebt foundation** — COMPLETE — manual `NONE` — head `0da49c7526b54f562827d63477b7ce8f1865de43`; PR #45 merge `3986b056654b25a73e45e5135ca3110a920c4bf5`; normalization #46 `fc7bd4d5803c451b4d343d08bcc212868ad24412`.
8. **R6.8 — KodeCI + KodeBuild foundation** — COMPLETE — manual `CONDITIONAL — NOT TRIGGERED` — head `d632669b93fda7b8397b9c3de43d78ca8726323f`; PR #47 merge `d570a3930ee63802882b8682e4532004d4fd81d6`; normalization #48 `92effbde1e432a8fcb6c794038d77367d034bcb0`; final wording #49 merge `616899291fc3b4dc40695415a5008d6fdd599230`.
9. **R6.9 — KodeAppSecurity baseline** — COMPLETE — manual `NONE` — head `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`; PR #50 merge `f5c135edf0be464a02b4b46d67c14e665f236009`.
10. **R6.10 — KodePrivacy baseline** — NEXT / NOT STARTED — manual `NONE`.
11. **R6.11 — KodeLicense + KodeBOM foundation** — PLANNED — manual `CONDITIONAL`.
12. **R6.12 — Major-patch validation + rollback gate and R6 integration acceptance** — PLANNED — manual `CONDITIONAL`.

No subdivision may be silently added, removed, merged, split or renumbered.

## Accepted evidence summary

### R6.1–R6.3

- R6.1 accepted head `802de4ba3110ace657c4e16306a0ca29850ce2bd`; R0 `32561211168`, Python Core `32561211156`, UI Smoke `32561211167` SUCCESS.
- R6.2 accepted head `8ac3772e98c70260c320519a214bb25b6cedbb38`; R0 #603, Python Core #577, UI Smoke #544 SUCCESS.
- R6.3 accepted head `7150237c263dd3ac96af4662d74909e05f3cf991`; R0 #622, Python Core #596, UI Smoke #563 SUCCESS.

### R6.4–R6.7

- R6.4 accepted head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`; hosted gates SUCCESS; required real Windows/Godot/Radeon gate `8 PASS / 0 FAIL / 8`.
- R6.5 accepted head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`; hosted gates SUCCESS; required Windows accessibility gate `15 PASS / 0 FAIL / 15`.
- R6.6 accepted head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; R0 #733, Python Core #707, UI Smoke #674 SUCCESS; manual NONE.
- R6.7 accepted head `0da49c7526b54f562827d63477b7ce8f1865de43`; R0 #756, Python Core #730, UI Smoke #697 SUCCESS; manual NONE.

### R6.8

Accepted implementation head `d632669b93fda7b8397b9c3de43d78ca8726323f`.

- R0 Repository Guard #783 `32571710663` — SUCCESS Windows + Ubuntu;
- Python Core #757 `32571710718` — SUCCESS for all five jobs: core Ubuntu, core Windows, integrated Windows UI, package-build Ubuntu, package-build Windows;
- KodeStudio UI Smoke #724 `32571710650` — SUCCESS Windows.

Manual R6.8 was `CONDITIONAL — NOT TRIGGERED`. PR #47 merged as `d570a3930ee63802882b8682e4532004d4fd81d6`; normalization #48 merged as `92effbde1e432a8fcb6c794038d77367d034bcb0`; final wording #49 merged as `616899291fc3b4dc40695415a5008d6fdd599230`.

### R6.9

Accepted implementation head `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`.

Final hosted evidence on that exact head:

- R0 Repository Guard #812 `32573265598` — SUCCESS Windows + Ubuntu;
- Python Core #786 `32573265793` — SUCCESS for all five jobs: core Ubuntu, core Windows, integrated Windows UI, package-build Ubuntu and package-build Windows;
- KodeStudio UI Smoke #753 `32573265579` — SUCCESS Windows.

Accepted R6.9 scope includes structured threat assets/boundaries/entry points/threats with cross-reference validation; explicit applicable/N/A semantics; version-qualified ASVS references; source-required measured requirement evidence; point-in-time dependency vulnerability evidence; recursive secret redaction; canonical SHA-256 anti-tamper report; project-confined security persistence; Health SECURITY adapter; stable R6.3 requirement/dependency/threat cases; and no unrestricted scanner/process/network execution path.

The initial Kodepoia threat model covers workspace path traversal, arbitrary process execution, raw secret disclosure, loopback-service exposure and downloaded-code governance bypass. Residual risk defaults UNKNOWN; existing mitigations do not manufacture PASS.

Development CI found one fixture expectation error: a blocking Health metric had aggregate score 75.0 rather than the test's expected 0.0 because five LOW measured threat risks remained part of the aggregate. The metric was already FAIL and blocking. Only the assertion changed; no security rule or scoring formula changed.

PR #50 merged as `f5c135edf0be464a02b4b46d67c14e665f236009`. Manual intervention: **NONE**.

**R6.1–R6.9 = COMPLETE. R6 remains IN PROGRESS. R6.10 = NEXT / NOT STARTED until this post-merge normalization is CI-green and merged.**

## Manual-intervention forecast

- R6.4 `REQUIRED`: SATISFIED.
- R6.5 `REQUIRED`: SATISFIED.
- R6.6 `NONE`: COMPLETE.
- R6.7 `NONE`: COMPLETE.
- R6.8 `CONDITIONAL`: NOT TRIGGERED; no user action required.
- R6.9 `NONE`: COMPLETE; no user action required.
- R6.10 `NONE`: NEXT / NOT STARTED.
- R6.11 `CONDITIONAL`: only for unresolved acceptance-critical license/provenance ambiguity.
- R6.12 `CONDITIONAL`: only if selected final gates require local hardware execution or explicit approval.

## Completion rule

R6 cannot be COMPLETE until R6.1–R6.12 are COMPLETE with all required evidence, R6.12 integrated acceptance passes, and `R6_PLAN.md`, this file and continuity are synchronized on normalized `main`. Do not start R7 before that.
