# R10.9 — Acceptance record

Status: **HOSTED IMPLEMENTATION CANDIDATE ACCEPTED — FINAL EXACT-HEAD GATES PENDING**  
Manual intervention: **NONE**

## Definition of Done

R10.9 requires:
- exact-head R0 Repository Guard SUCCESS;
- full Python Core SUCCESS on Ubuntu/Windows;
- R7/R8/R9 integrated acceptance PASS;
- KodeStudio UI Smoke SUCCESS;
- deterministic static and skinned LOD fixtures;
- explicit triangle ratios and absolute budgets;
- monotonic detail reduction;
- material/UV/normal preservation checks;
- explicit Shape Key policy with no silent topology claim;
- skinned vertex-group/normalization/influence preservation checks;
- bounded extent and surface-area proxy metrics;
- verified derivative SHA-256/size;
- deterministic R8 `lod_variant` lineage for every accepted tier;
- no variant revision emitted when any BLOCK exists;
- immutable source `.blend`;
- fixed offline Blender bootstrap with no dynamic/network/process escape;
- JSON Schema validation for profile, report and runner manifest.

## Candidate files

- `src/kodepoia/blender3d/lod_contracts.py`
- `src/kodepoia/blender3d/lod_validator.py`
- `src/kodepoia/blender3d/lod_bootstrap.py`
- `src/kodepoia/blender3d/lod_runner.py`
- `schemas/r10-lod-profile-v1.schema.json`
- `schemas/r10-lod-report-v1.schema.json`
- `schemas/r10-lod-manifest-v1.schema.json`
- `tests/test_blender_r10_9.py`
- package exports in `src/kodepoia/blender3d/__init__.py`
- this record and `R10_9_DESIGN.md`

## Hosted implementation candidate acceptance

Accepted implementation candidate: `fa64f49776a29ece4d06cd05f508632129ee863d`.

Exact-head hosted gates:
- R0 Repository Guard #1295 / run `32690770568`: **SUCCESS**;
- Python Core #1269 / run `32690770644`: **SUCCESS**;
- KodeStudio UI Smoke #1236 / run `32690770565`: **SUCCESS**.

Python Core evidence:
- Ubuntu: **837 passed / 7 skipped / 46 warnings**;
- R7 integrated acceptance: **PASS**;
- R8 integrated acceptance: **PASS**;
- R9 integrated acceptance: **PASS**;
- Windows Python Core: **SUCCESS**;
- Ubuntu package build: **SUCCESS**;
- Windows package build: **SUCCESS**;
- integrated KodeStudio Windows smoke inside Python Core: **SUCCESS**.

The candidate therefore satisfies the hosted implementation acceptance. This documentation commit is the only planned post-candidate write on the implementation branch; fresh R0/Python/UI gates are required on its exact resulting SHA before merge.

## Manual state

Frozen state: **NONE**.

No local/manual Blender run is required for R10.9. The implementation uses the already accepted R10.2 Blender process boundary and a fixed Decimate surface; deterministic hosted fixtures are authoritative for the R10.9 preservation/lineage contract.

## Acceptance ordering

1. Candidate gates above are accepted.
2. This file binds candidate SHA/run IDs and test totals exactly once.
3. Run fresh R0 + full Python Core + UI Smoke on this final documented head.
4. Merge the implementation PR with `expected_head_sha`.
5. Create exactly one continuity-only post-merge normalization.
6. Run R0 + full Python Core + UI Smoke on that normalization head and merge it.
7. Only that merge makes R10.9 **COMPLETE + NORMALIZED** and authorizes R10.10.
