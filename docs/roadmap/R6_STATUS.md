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
8. **R6.8 — KodeCI + KodeBuild foundation** — COMPLETE — manual `CONDITIONAL — NOT TRIGGERED` — head `d632669b93fda7b8397b9c3de43d78ca8726323f`; PR #47 merge `d570a3930ee63802882b8682e4532004d4fd81d6`; normalization #48 `92effbde1e432a8fcb6c794038d77367d034bcb0`.
9. **R6.9 — KodeAppSecurity baseline** — NEXT / NOT STARTED — manual `NONE`.
10. **R6.10 — KodePrivacy baseline** — PLANNED — manual `NONE`.
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

Final hosted evidence on that exact head:

- R0 Repository Guard #783 `32571710663` — SUCCESS Windows + Ubuntu;
- Python Core #757 `32571710718` — SUCCESS for all five jobs: core Ubuntu, core Windows, integrated Windows UI, package-build Ubuntu, package-build Windows;
- KodeStudio UI Smoke #724 `32571710650` — SUCCESS Windows.

Accepted R6.8 scope includes structured CI states/source-SHA evidence, hash-protected CI/build manifests, wheel+sdist structural validation, source/dependency/artifact SHA-256 evidence, recursive secret redaction, `WorkspaceBoundary` confinement, Health `build`, R6.3 hooks, a fixed collector with no arbitrary build-command/path surface, and additive Windows+Ubuntu package builds bound to the same exact source SHA recorded in manifests.

Final artifact inspection:

- Ubuntu artifact ID `9475481332`, ZIP SHA-256 `cdeef82ace3e0ca2ef0275b3111bf6d2c8f50213b20e777ddb436477e48261d8`; wheel SHA-256 `35489ed602a9ade3816a4562f5cd751fbfb8924cd8ad780fba5bc7aa26a2a095`; sdist SHA-256 `b803d3f316f46ea461af853240ba8ab8bf3f867e0cff8e88e70f87bf678c1a78`; build/CI PASS, zero blockers.
- Windows artifact ID `9475485133`, ZIP SHA-256 `aae159bd0d8a04ee4cec6c65f7a20f104c4679a9081432640419c4a6e74ccbe5`; wheel SHA-256 `1406f5a2f180b56c611fb3a0cd8a9d23436682903405f52dadc26257c5b676fb`; sdist SHA-256 `42e63403069e61235cefa71ebbc4099b5e717e1528a6eae54ef0673f20e69edd`; build/CI PASS, zero blockers.

Both downloaded bundles contained the expected wheel, sdist, build manifest and CI report; both manifests were bound to `d632669b93fda7b8397b9c3de43d78ca8726323f`.

Manual intervention R6.8: **CONDITIONAL — NOT TRIGGERED.** Hosted Windows fully proved the acceptance-critical package build/validation/hash/upload behavior, so no local user-side run is necessary.

Implementation PR #47 merged as `d570a3930ee63802882b8682e4532004d4fd81d6`. Post-merge normalization PR #48 passed R0 #790, Python Core #764 (including both package-build jobs) and UI Smoke #731, then merged as `92effbde1e432a8fcb6c794038d77367d034bcb0`.

**R6.1–R6.8 = COMPLETE. R6 remains IN PROGRESS. R6.9 = NEXT / NOT STARTED.**

## Manual-intervention forecast

- R6.4 `REQUIRED`: SATISFIED.
- R6.5 `REQUIRED`: SATISFIED.
- R6.6 `NONE`: COMPLETE.
- R6.7 `NONE`: COMPLETE.
- R6.8 `CONDITIONAL`: NOT TRIGGERED; no user action required.
- R6.9 and R6.10: `NONE` currently planned.
- R6.11 `CONDITIONAL`: only for unresolved acceptance-critical license/provenance ambiguity.
- R6.12 `CONDITIONAL`: only if selected final gates require local hardware execution or explicit approval.

## Completion rule

R6 cannot be COMPLETE until R6.1–R6.12 are COMPLETE with all required evidence, R6.12 integrated acceptance passes, and `R6_PLAN.md`, this file and continuity are synchronized on normalized `main`. Do not start R7 before that.