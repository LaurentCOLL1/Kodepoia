# R6.7 — KodeTechnicalDebt foundation — Acceptance

**Status:** COMPLETE  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Manual intervention:** NONE — no user-side gate required  
**Accepted implementation head:** `0da49c7526b54f562827d63477b7ce8f1865de43`  
**Implementation PR:** #45  
**Implementation merge:** `3986b056654b25a73e45e5135ca3110a920c4bf5`

R6.7 is accepted. All authoritative hosted gates passed on the exact final implementation head before PR #45 was merged without changing that head.

## Accepted scope

- stable debt IDs;
- stable SHA-256 duplicate fingerprints independent of lifecycle timestamps/state;
- categories, severity, impact, probability and effort;
- deterministic priority `severity_weight × impact × probability ÷ effort`, bounded to 100;
- structured owner/scope/source/provenance and file/symbol/test/requirement/issue references;
- timezone-aware first-seen/last-seen/review/expiry/resolution fields;
- explicit `OPEN`, `ACCEPTED`, `RESOLVED` lifecycle invariants;
- accepted debt requires rationale and remains visible/penalized rather than becoming resolved;
- resolved debt remains historical and requires `resolved_at`;
- accepted/resolved debt cannot remain blocking;
- duplicate IDs/fingerprints rejected;
- derived counts, blockers, active ranking and debt penalty;
- canonical SHA-256 anti-tamper report evidence;
- `technical-debt-report-v1` schema;
- `.kodepoia/diagnostics/technical_debt/` confinement through `WorkspaceBoundary`;
- KodeHealth `technical_debt` metric adapter;
- stable R6.3 `technical-debt:<id>` cases;
- newly introduced blocking debt becomes an added FAIL and therefore a regression under R6.3;
- known repository debt observations recorded with real provenance rather than pretending an unexecuted scanner ran.

## Acceptance matrix — final result

Every required deterministic/model/schema/confinement/Health/R6.3 gate is PASS. Manual intervention was not required.

## Final-head hosted evidence

Exact accepted head:

`0da49c7526b54f562827d63477b7ce8f1865de43`

- **R0 Repository Guard** run `32570711736` / #756 — SUCCESS Windows + Ubuntu.
- **Python Core** run `32570711738` / #730 — SUCCESS:
  - Ubuntu pytest SUCCESS;
  - Windows pytest SUCCESS;
  - Windows PowerShell syntax validation SUCCESS;
  - integrated KodeStudio UI smoke SUCCESS.
- **KodeStudio UI Smoke** run `32570711732` / #697 — SUCCESS Windows.

## Development findings

The first diagnostic implementation run exposed one incorrect fixture expectation: a critical item with impact 4, probability 3 and effort 2 evaluates to `4 × 4 × 3 ÷ 2 = 24`, not 30. The test expectation was corrected; the deterministic formula was unchanged.

The same hosted pytest log reproduced two existing non-blocking technical-debt candidates with real provenance:

- `PytestCollectionWarning` caused by imported quality classes named `Test*`;
- Pillow `Image.Image.getdata()` deprecation warnings in VisualQA, with removal announced for Pillow 14.

R6.5's local Qt font-directory / `propagateSizeHints()` notices remain environment-specific candidate debt only. These observations are documented in `R6_7_KNOWN_DEBT.md`; R6.7 does not falsely claim a scanner executed or that these debts were remediated.

## Rollback / anti-regression

R6.7 is additive. A rollback removes the technical-debt module/schema/tests/docs and quality exports without mutating R6.1–R6.6 evidence. Project-local debt history is not silently deleted.

Later work must not:

- treat accepted debt as resolved;
- change fingerprints merely to avoid duplicate detection;
- omit provenance/source to manufacture evidence;
- hide new blocking debt from R6.3;
- weaken derived-field/evidence-hash validation;
- bypass `WorkspaceBoundary`;
- claim an unexecuted scanner or remediation as evidence.

## Completion record

- accepted head `0da49c7526b54f562827d63477b7ce8f1865de43`;
- PR #45;
- implementation merge `3986b056654b25a73e45e5135ca3110a920c4bf5`;
- R0 #756 PASS;
- Python Core #730 PASS;
- UI Smoke #697 PASS;
- manual gate NONE;
- R6.7 **COMPLETE**;
- R6.8 **NEXT / NOT STARTED** until this post-merge normalization is CI-green and merged.
