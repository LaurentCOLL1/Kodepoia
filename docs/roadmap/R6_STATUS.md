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
8. **R6.8 — KodeCI + KodeBuild foundation** — COMPLETE — manual `CONDITIONAL — NOT TRIGGERED` — head `d632669b93fda7b8397b9c3de43d78ca8726323f`; PR #47 merge `d570a3930ee63802882b8682e4532004d4fd81d6`; normalization #48 `92effbde1e432a8fcb6c794038d77367d034bcb0`; final wording #49 `616899291fc3b4dc40695415a5008d6fdd599230`.
9. **R6.9 — KodeAppSecurity baseline** — COMPLETE — manual `NONE` — head `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`; PR #50 merge `f5c135edf0be464a02b4b46d67c14e665f236009`; normalization #51 `4df229e431d2d54e4268607f38bac4045ac590d1`.
10. **R6.10 — KodePrivacy baseline** — COMPLETE — manual `NONE` — head `e9363e0e00f592b39a7a094b7520b3d515fb02f0`; PR #52 merge `cefc60266cb191cf0ee5a099e0d8923a2f14745a`; normalization #53 `36524978a963d8c759d36902bc1ab00989da0549`.
11. **R6.11 — KodeLicense + KodeBOM foundation** — IN PROGRESS — manual `CONDITIONAL — NOT TRIGGERED` — branch `feature/r6-11-license-bom`, starting normalized main `36524978a963d8c759d36902bc1ab00989da0549`.
12. **R6.12 — Major-patch validation + rollback gate and R6 integration acceptance** — PLANNED — manual `CONDITIONAL`.

No subdivision may be silently added, removed, merged, split or renumbered.

## Accepted evidence summary

- R6.1 head `802de4ba3110ace657c4e16306a0ca29850ce2bd`; R0 `32561211168`, Python Core `32561211156`, UI Smoke `32561211167` SUCCESS.
- R6.2 head `8ac3772e98c70260c320519a214bb25b6cedbb38`; R0 #603, Python Core #577, UI Smoke #544 SUCCESS.
- R6.3 head `7150237c263dd3ac96af4662d74909e05f3cf991`; R0 #622, Python Core #596, UI Smoke #563 SUCCESS.
- R6.4 head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`; hosted gates SUCCESS; required Windows/Godot/Radeon `8 PASS / 0 FAIL / 8`.
- R6.5 head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`; hosted gates SUCCESS; required Windows accessibility `15 PASS / 0 FAIL / 15`.
- R6.6 head `6890b9d37722c74703e8b86f7de11dbfe66821ed`; R0 #733, Python Core #707, UI Smoke #674 SUCCESS.
- R6.7 head `0da49c7526b54f562827d63477b7ce8f1865de43`; R0 #756, Python Core #730, UI Smoke #697 SUCCESS.
- R6.8 head `d632669b93fda7b8397b9c3de43d78ca8726323f`; R0 #783, Python Core #757 five jobs, UI Smoke #724 SUCCESS; manual conditional NOT TRIGGERED.
- R6.9 head `1f24b0160cc28a03efdcbbc0aeb841125a1c5351`; R0 #812, Python Core #786 five jobs, UI Smoke #753 SUCCESS; PR #50 merge `f5c135edf0be464a02b4b46d67c14e665f236009`; normalization #51 `4df229e431d2d54e4268607f38bac4045ac590d1`.
- R6.10 head `e9363e0e00f592b39a7a094b7520b3d515fb02f0`; R0 #844 `32575111465`, Python Core #818 `32575111540` all five jobs, UI Smoke #785 `32575111597` SUCCESS; PR #52 merge `cefc60266cb191cf0ee5a099e0d8923a2f14745a`; normalization #53 head `03d1c75547e667ceaa1842b1f39b12500e3ee103` passed R0 #851, Python Core #825 five jobs and UI #792, merged as `36524978a963d8c759d36902bc1ab00989da0549`.

## R6.11 implementation state

R6.11 started only after R6.10 normalized main `36524978a963d8c759d36902bc1ab00989da0549`.

Current implementation contract:

- `BomComponent` with stable ID, project/package/asset kind, resolved/unresolved/N/A state, exact version only when resolved, purl, provenance, SHA-256 evidence and requirements/groups;
- `IntegrityEvidence` distinguishes recorded digest, mismatch, unknown and N/A; recorded never claims independent verification; mismatch blocks;
- optional declared-license assertion plus mandatory concluded-license assertion;
- `LicenseAssertion` distinguishes SPDX expression, NOASSERTION and NONE; NOASSERTION/NONE require rationale+provenance;
- `LicenseRef-*` can carry a custom license-text SHA-256 without pretending to be an SPDX-listed license;
- no free-text license→SPDX inference;
- `KodeBOM.from_pyproject()` inventories build-system, runtime and every optional dependency group through `WorkspaceBoundary` + stdlib `tomllib`;
- duplicate normalized Python packages across groups merge deterministically while retaining each requirement;
- dependency ranges remain unresolved and NOASSERTION; current package-page metadata is not copied onto unresolved ranges;
- explicit inventory completeness/review provenance;
- canonical BOM report with deterministic counts/blockers/status and SHA-256 anti-tamper evidence;
- exact-expression license policy with allow/warn/deny/unknown; unmatched/NOASSERTION remains unknown and default ALLOW is forbidden;
- license report bound to BOM evidence SHA-256 and policy fingerprint;
- SPDX baseline remains 3.0; current serialization reference is 3.0.1 with current JSON-LD context;
- compact SPDX compatibility view explicitly declares `conformance_claim=false`;
- Health `dependencies` and `licenses` adapters;
- stable R6.3 `bom:<id>` / `license:<id>` cases;
- `.kodepoia/bom/` and `.kodepoia/licenses/` atomic stores via `WorkspaceBoundary`;
- schemas `bom-report-v1` and `license-report-v1` plus focused tests, including the current real Kodepoia pyproject;
- no shell, installer, scanner, arbitrary network fetch or publisher path.

Standards recheck on 2026-08-22: SPDX current specification is 3.0.1 while frozen R6 baseline remains the 3.0 family; SPDX explicitly distinguishes `NoAssertionLicense` from missing license information and supports `LicenseRef-*`; CycloneDX 1.7 remains optional current-stable interoperability context and does not replace SPDX.

**R6.1–R6.10 = COMPLETE. R6.11 = IN PROGRESS. R6 remains IN PROGRESS.**

## Manual-intervention forecast

- R6.4 `REQUIRED`: SATISFIED.
- R6.5 `REQUIRED`: SATISFIED.
- R6.6 `NONE`: COMPLETE.
- R6.7 `NONE`: COMPLETE.
- R6.8 `CONDITIONAL`: NOT TRIGGERED.
- R6.9 `NONE`: COMPLETE.
- R6.10 `NONE`: COMPLETE.
- R6.11 `CONDITIONAL`: NOT TRIGGERED; only needed if an acceptance-critical real component needs a specific license conclusion and trusted evidence remains ambiguous.
- R6.12 `CONDITIONAL`: only if selected final gates require local hardware execution or explicit approval.

## Completion rule

R6 cannot be COMPLETE until R6.1–R6.12 are COMPLETE with all required evidence, R6.12 integrated acceptance passes, and `R6_PLAN.md`, this file and continuity are synchronized on normalized `main`. Do not start R7 before that.
