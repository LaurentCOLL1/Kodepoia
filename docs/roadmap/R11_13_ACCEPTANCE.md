# R11.13 — Acceptance

Status: **IMPLEMENTED — HOSTED EXACT-HEAD GATES PENDING**  
Manual intervention: **NONE**

## Base and scope

- Base normalized `main`: `3ca78857de17280c758912d35705881f8d31c73a`.
- Branch: `r11/13-cli-kodestudio-ux`.
- Frozen scope: structured R11 CLI groups, KodeStudio Media/Franchise workspace, runtime/evidence/blocker presentation, cancellation through the existing KillSwitch, accessibility and pseudo-localization coverage.

## Acceptance criteria

- All eleven frozen R11 capability groups have typed CLI status surfaces with stable JSON and exit semantics.
- Blocked/unavailable capability state returns an explicit non-zero exit state; missing evidence is never converted into PASS.
- No raw argv/executable/filter graph/model path/script/migration-code option exists in the R11 CLI surface.
- KodeStudio intentionally expands from 9 to 10 main navigation entries and adds five R11 tabs.
- R11 views are read-only for evidence/status and contain no raw command or migration-code editor.
- R11.5 and R11.9 preserved required local evidence is referenced without claiming that a runtime was live-probed by R11.13.
- Refresh does not launch an external runtime.
- Cancel reuses the global KillSwitch boundary.
- New R11 controls pass accessibility audit and pseudo-localize without navigation truncation regression.
- Existing R6 accessibility/localization tests remain green after the intentional navigation-count change.
- Full R0 Repository Guard, Python Core and KodeStudio UI Smoke must pass on one exact candidate head.
- After authoritative run IDs are frozen here, any resulting documentation-only head is re-gated before merge.

## Manual state

**NONE.** R11.13 introduces presentation/workflow bindings only. Accepted R11.5/R11.9 runtime evidence remains authoritative and no new runtime-specific claim is made.

## Completion ordering

Accepted candidate -> record exact run IDs -> re-gate final docs if head changes -> merge with `expected_head_sha` -> exactly one continuity-only post-merge normalization -> exact-head R0/Python/UI -> merge normalization -> only then R11.14 is authorized.
