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
6. **R6.6 — KodeLocalization + pseudo-localization foundation** — COMPLETE — manual `NONE` — PR #43 merge `f677cb34eade0549edc951fe11955de2bc0b270d`; normalization #44 merge `c5edd3c80ad9afec25997f1372d5f98ac861becc`.
7. **R6.7 — KodeTechnicalDebt foundation** — COMPLETE — manual `NONE` — accepted head `0da49c7526b54f562827d63477b7ce8f1865de43`; PR #45 merge `3986b056654b25a73e45e5135ca3110a920c4bf5`; normalization #46 merge `fc7bd4d5803c451b4d343d08bcc212868ad24412`.
8. **R6.8 — KodeCI + KodeBuild foundation** — IN PROGRESS — manual `CONDITIONAL` — branch `feature/r6-8-ci-build`, PR #47, base `fc7bd4d5803c451b4d343d08bcc212868ad24412`.
9. **R6.9 — KodeAppSecurity baseline** — PLANNED — manual `NONE`.
10. **R6.10 — KodePrivacy baseline** — PLANNED — manual `NONE`.
11. **R6.11 — KodeLicense + KodeBOM foundation** — PLANNED — manual `CONDITIONAL`.
12. **R6.12 — Major-patch validation + rollback gate and R6 integration acceptance** — PLANNED — manual `CONDITIONAL`.

No subdivision may be silently added, removed, merged, split or renumbered.

## Accepted evidence through R6.7

- R6.1 accepted head `802de4ba3110ace657c4e16306a0ca29850ce2bd`; R0 `32561211168`, Python Core `32561211156`, UI Smoke `32561211167` SUCCESS.
- R6.2 accepted head `8ac3772e98c70260c320519a214bb25b6cedbb38`; R0 #603 `32561719921`, Python Core #577 `32561719925`, UI Smoke #544 `32561720008` SUCCESS.
- R6.3 accepted head `7150237c263dd3ac96af4662d74909e05f3cf991`; R0 #622 `32562032986`, Python Core #596 `32562032998`, UI Smoke #563 `32562032982` SUCCESS.
- R6.4 accepted head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`; hosted gates SUCCESS; required real Windows/Godot/Radeon gate `8 PASS / 0 FAIL / 8`; normalization #40 `39ecfef80f17cac1d5a0722866f5b1e046e9d5e1`.
- R6.5 accepted head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`; hosted gates SUCCESS; required Windows accessibility gate `15 PASS / 0 FAIL / 15`; normalization #42 `3c5b871a9f977c2647f13cc7858beb26be1a2ed6`.
- R6.6 accepted head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; R0 #733, Python Core #707, UI Smoke #674 SUCCESS; normalization #44 `c5edd3c80ad9afec25997f1372d5f98ac861becc`.
- R6.7 accepted head `0da49c7526b54f562827d63477b7ce8f1865de43`; R0 #756 `32570711736`, Python Core #730 `32570711738`, UI Smoke #697 `32570711732` SUCCESS; implementation merge #45 `3986b056654b25a73e45e5135ca3110a920c4bf5`; normalization #46 `fc7bd4d5803c451b4d343d08bcc212868ad24412`.

## R6.8 implementation state

R6.8 is active on PR #47 from normalized main `fc7bd4d5803c451b4d343d08bcc212868ad24412`.

Implemented scope:

- `KodeCI` with stable check IDs and explicit `queued`, `in_progress`, `pass`, `fail`, `cancelled`, `skipped`, `unknown` states;
- required FAIL/CANCELLED/SKIPPED never become PASS; required incomplete evidence remains UNKNOWN;
- CI reports bound to exact source Git SHA with canonical SHA-256 evidence and derived-count/blocker tamper checks;
- `.kodepoia/workflows/` persistence through `WorkspaceBoundary` and stable R6.3 CI hooks;
- `KodeBuild` manifests bound to source SHA, platform, Python version and Hatchling backend;
- deterministic source-input digest and explicit dependency-input digest;
- wheel/sdist artifact name, byte size, SHA-256 and archive-structure validation;
- missing/invalid wheel or sdist becomes blocking build failure;
- recursive secret-field/token redaction before persisted metadata;
- `.kodepoia/releases/` persistence through `WorkspaceBoundary`;
- Health `build` adapter and stable R6.3 build hooks;
- JSON Schemas `ci-report-v1` and `build-manifest-v1`;
- fixed `scripts/r6_8_collect_build.py` collector with no arbitrary command/path surface;
- additive `package-build` matrix in Python Core for Ubuntu and Windows using fixed `python -m build` and `actions/upload-artifact@v4`;
- package-build checkout explicitly pinned to the same PR head/source SHA carried by the manifests, avoiding synthetic merge-commit/source-evidence mismatch.

Diagnostic head `fe084cfbe8f3bafddbf6075ad4c8596ba3998b5a` passed:

- R0 #779 `32571588986` — SUCCESS Windows + Ubuntu;
- Python Core #753 `32571588989` — SUCCESS, including `python-core-ubuntu-latest`, `python-core-windows-latest`, integrated Windows UI smoke, `package-build-ubuntu-latest`, and `package-build-windows-latest`;
- KodeStudio UI Smoke #720 `32571588982` — SUCCESS Windows.

On that diagnostic head, both package-build jobs checked out exactly `fe084cfbe8f3bafddbf6075ad4c8596ba3998b5a`, built wheel+sdist, structurally validated both, emitted PASS build/CI evidence and uploaded package/evidence artifacts. This diagnostic demonstrates hosted Windows capability, but final acceptance will use only the later exact head after plan/status/continuity synchronization.

**R6.8 remains IN PROGRESS. PR #47 must not merge until final-head R0/Python/UI/package-build gates and artifact inspection succeed and the conditional manual decision is recorded. R6.9 must not start earlier.**

## Manual-intervention forecast

- R6.4 `REQUIRED`: SATISFIED.
- R6.5 `REQUIRED`: SATISFIED.
- R6.6 `NONE`: COMPLETE.
- R6.7 `NONE`: COMPLETE.
- R6.8 `CONDITIONAL`: current diagnostic evidence indicates hosted Windows can authoritatively build, validate, hash and upload the required package artifacts. The condition is therefore **expected NOT TRIGGERED**, but it will be finalized only after the final R6.8 head repeats this proof.
- R6.9 and R6.10: `NONE` currently planned.
- R6.11 `CONDITIONAL`: only for unresolved acceptance-critical license/provenance ambiguity.
- R6.12 `CONDITIONAL`: only if selected final gates require local hardware execution or explicit approval.

## Completion rule

R6 cannot be COMPLETE until R6.1–R6.12 are COMPLETE with all required evidence, R6.12 integrated acceptance passes, and `R6_PLAN.md`, this file and continuity are synchronized on normalized `main`. Do not start R7 before that.