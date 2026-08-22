# R6.6 — KodeLocalization + pseudo-localization foundation — Acceptance

**Status:** IN PROGRESS  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Manual intervention:** NONE

R6.6 is complete only after all deterministic catalog, pseudo-localization, evidence, KodeStudio long-string smoke and final-head CI gates pass and the implementation PR is merged.

## Acceptance matrix

| Gate | Required | State before final-head CI |
| --- | --- | --- |
| Stable locale/message IDs | yes | IMPLEMENTED |
| Duplicate message IDs rejected | yes | IMPLEMENTED |
| `other` form mandatory | yes | IMPLEMENTED |
| Missing source message = blocking FAIL | yes | IMPLEMENTED |
| Source/target form parity | yes | IMPLEMENTED |
| Placeholder parity per form | yes | IMPLEMENTED |
| Target-only key = explicit WARN | yes | IMPLEMENTED |
| Missing fallback = explicit WARN | yes | IMPLEMENTED |
| Wrong fallback = blocking FAIL | yes | IMPLEMENTED |
| Source fallback translation works | yes | IMPLEMENTED |
| Pseudo locale preserves placeholders | yes | IMPLEMENTED |
| Pseudo locale preserves markup/entities | yes | IMPLEMENTED |
| Pseudo locale visibly expands text | yes | IMPLEMENTED |
| Report status/count/blocker derivation | yes | IMPLEMENTED |
| Canonical evidence SHA-256 | yes | IMPLEMENTED |
| Tampered counts/hash rejected | yes | IMPLEMENTED |
| Workspace/symlink escape rejection | yes | IMPLEMENTED |
| R6.3 stable localization hooks | yes | IMPLEMENTED |
| KodeStudio stable message registry | yes | IMPLEMENTED |
| English remains production default | yes | IMPLEMENTED |
| `qps-ploc` KodeStudio smoke | yes | IMPLEMENTED |
| Long navigation strings not clipped by fixed nav width | yes | IMPLEMENTED |
| `localization-report-v1` JSON Schema | yes | IMPLEMENTED |
| R0 final-head Windows + Ubuntu | yes | PENDING |
| Python Core final-head Windows + Ubuntu | yes | PENDING |
| KodeStudio UI Smoke final-head Windows | yes | PENDING |
| PR merge | yes | PENDING |
| Post-merge plan/status/continuity normalization | yes | PENDING |

## Expected CI behavior

- the core localization test suite runs under the normal `pytest` matrix;
- PySide-specific pseudo-localization smoke is skipped where PySide is absent and runs in the Windows UI jobs;
- UI smoke must prove that the registered KodeStudio main-surface strings are pseudo-localized and the navigation width adapts to the expanded content;
- pre-existing R6.5 accessibility smoke must remain green after visible-text routing changes.

## Evidence rules

The accepted implementation head must have:

- R0 Repository Guard SUCCESS on Windows and Ubuntu;
- Python Core SUCCESS on Windows and Ubuntu;
- integrated KodeStudio UI smoke SUCCESS;
- separate KodeStudio UI Smoke SUCCESS on Windows;
- no manual/user-side gate.

Only the exact final implementation head may be cited. Any later commit requires fresh hosted CI evidence.

## Failure recovery

If a catalog validation test fails, do not remove the failing message or weaken placeholder/form checks merely to manufacture PASS. Correct the catalog or validator behavior while preserving stable IDs.

If pseudo-localization corrupts a placeholder or markup token, fix the tokenizer/transformation; do not exempt the affected string by ID.

If KodeStudio long-string smoke fails, correct layout/registration behavior rather than reducing the pseudo expansion until the test passes.

If R6.5 accessibility smoke regresses, R6.6 remains blocked until the regression is corrected.

## Manual intervention

**NONE.** R6.6 acceptance is objective and fully testable in hosted CI.

## Completion record

PENDING final-head CI, merge and post-merge normalization.
