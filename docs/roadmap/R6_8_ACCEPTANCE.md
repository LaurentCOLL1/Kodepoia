# R6.8 — KodeCI + KodeBuild foundation — Acceptance

**Status:** IN PROGRESS  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Manual intervention:** CONDITIONAL — NOT YET TRIGGERED

R6.8 is complete only after its exact final implementation head passes the existing gates plus the new Windows+Ubuntu package-build jobs, required package/evidence artifacts are inspectable, the conditional local gate is explicitly evaluated, the implementation PR is merged and post-merge plan/status/continuity normalization is complete.

## Acceptance matrix

| Gate | Required | Current |
| --- | --- | --- |
| Stable CI check IDs | yes | IMPLEMENTED |
| queued/in-progress/pass/fail/cancelled/skipped/unknown semantics | yes | IMPLEMENTED |
| required skipped/cancelled never PASS | yes | IMPLEMENTED |
| CI source SHA binding | yes | IMPLEMENTED |
| CI derived counts/blockers + evidence hash | yes | IMPLEMENTED |
| CI R6.3 adapter | yes | IMPLEMENTED |
| `.kodepoia/workflows/` confinement | yes | IMPLEMENTED |
| Build source SHA/platform/Python/backend identity | yes | IMPLEMENTED |
| source-input SHA-256 | yes | IMPLEMENTED |
| dependency-input SHA-256 | yes | IMPLEMENTED |
| artifact name/size/SHA-256 | yes | IMPLEMENTED |
| wheel structural validation | yes | IMPLEMENTED |
| sdist structural validation | yes | IMPLEMENTED |
| missing/invalid required artifact blocks | yes | IMPLEMENTED |
| recursive secret redaction | yes | IMPLEMENTED |
| build derived fields + evidence hash | yes | IMPLEMENTED |
| `.kodepoia/releases/` confinement | yes | IMPLEMENTED |
| Health `build` adapter | yes | IMPLEMENTED |
| stable R6.3 build cases | yes | IMPLEMENTED |
| CI/build JSON Schemas | yes | IMPLEMENTED |
| existing R0/Python/UI semantics preserved | yes | IMPLEMENTED |
| package build on Ubuntu hosted | yes | PENDING FINAL HEAD |
| package build on Windows hosted | yes | PENDING FINAL HEAD |
| package/evidence upload on both platforms | yes | PENDING FINAL HEAD |
| hosted artifacts inspected | yes | PENDING FINAL HEAD |
| conditional local Windows gate explicitly evaluated | yes | PENDING FINAL HEAD |
| R0 final head Windows+Ubuntu | yes | PENDING FINAL HEAD |
| Python Core final head Windows+Ubuntu | yes | PENDING FINAL HEAD |
| KodeStudio UI Smoke final head | yes | PENDING FINAL HEAD |
| implementation PR merge | yes | PENDING |
| post-merge normalization | yes | PENDING |

## Hosted evidence requirements

The final Python Core workflow must show, on the exact implementation head:

- `python-core-ubuntu-latest` SUCCESS;
- `python-core-windows-latest` SUCCESS;
- integrated `kodestudio-ui-windows` SUCCESS;
- `package-build-ubuntu-latest` SUCCESS;
- `package-build-windows-latest` SUCCESS.

The two package-build jobs must each build and structurally validate a wheel and sdist, emit source-SHA-bound CI/build manifests and upload the package + latest manifests as GitHub Actions artifacts.

## Conditional manual gate decision

Default state: **NOT TRIGGERED**.

If hosted Windows successfully builds, validates, hashes and uploads the required Windows package artifacts/manifests, that hosted result satisfies the Windows behavior required by R6.8 and no user-side run is invented.

Only if hosted Windows cannot prove an acceptance-critical Windows package/build property may this gate become TRIGGERED. In that case R6.8 remains incomplete until an exact-head local runner/evidence contract is implemented and the user receives exact prerequisites, commands/actions, expected output, error recovery, evidence requirements and do-not-do-yet instructions.

## Failure recovery

- Do not convert skipped/cancelled required checks to PASS.
- Do not suppress a missing wheel/sdist or mark an unvalidated archive as valid.
- Do not compare Windows/Ubuntu artifact bytes and call different hashes a failure without a documented deterministic-build requirement.
- Do not log or persist secrets to make provenance richer.
- Do not remove existing R0/Python/UI checks to make the new build matrix pass.
- Do not add arbitrary model-supplied build commands, paths or executables.

## Completion record

PENDING final-head hosted CI, artifact inspection, conditional-gate decision, merge and normalization.
