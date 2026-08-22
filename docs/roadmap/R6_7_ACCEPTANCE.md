# R6.7 — KodeTechnicalDebt foundation — Acceptance

**Status:** IN PROGRESS  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Manual intervention:** NONE

## Acceptance matrix

| Gate | Required | Current |
| --- | --- | --- |
| Stable debt IDs | yes | IMPLEMENTED |
| Stable lifecycle-independent fingerprints | yes | IMPLEMENTED |
| Duplicate IDs/fingerprints rejected | yes | IMPLEMENTED |
| Structured file/symbol/test/requirement references | yes | IMPLEMENTED |
| Deterministic priority formula | yes | IMPLEMENTED |
| impact/probability/effort bounded 1–5 | yes | IMPLEMENTED |
| OPEN/ACCEPTED/RESOLVED invariants | yes | IMPLEMENTED |
| Accepted debt requires rationale | yes | IMPLEMENTED |
| Accepted debt remains visible/penalized | yes | IMPLEMENTED |
| Resolved debt requires resolution timestamp | yes | IMPLEMENTED |
| Blocking only on unresolved OPEN debt | yes | IMPLEMENTED |
| Counts/blockers/ranking/penalty derived | yes | IMPLEMENTED |
| Canonical SHA-256 anti-tamper evidence | yes | IMPLEMENTED |
| `technical-debt-report-v1` schema | yes | IMPLEMENTED |
| Workspace/symlink confinement | yes | IMPLEMENTED |
| Health `technical_debt` adapter | yes | IMPLEMENTED |
| R6.3 stable technical-debt cases | yes | IMPLEMENTED |
| Newly introduced blocking debt = regression | yes | IMPLEMENTED |
| Repository observations preserve provenance | yes | IMPLEMENTED |
| R0 final head Windows+Ubuntu | yes | PENDING |
| Python Core final head Windows+Ubuntu | yes | PENDING |
| KodeStudio UI Smoke final head | yes | PENDING |
| PR merge + normalization | yes | PENDING |

## No-manual-gate rule

R6.7 uses deterministic repository/evidence fixtures and does not require user-side execution. If CI cannot prove a foundation property, R6.7 remains incomplete rather than inventing a manual gate outside the accepted plan.

## Failure recovery

Do not mark accepted debt as resolved to make Health green. Do not change fingerprints to avoid duplicate detection. Do not suppress newly introduced blocking debt from R6.3. Correct the model/fixture or resolve the actual debt with traceable evidence.

## Completion record

PENDING final-head hosted CI, implementation merge and post-merge plan/status/continuity normalization.
