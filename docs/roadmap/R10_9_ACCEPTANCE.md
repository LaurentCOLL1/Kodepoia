# R10.9 — Acceptance record

Status: **HOSTED IMPLEMENTATION CANDIDATE — CANDIDATE GATES PENDING**  
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

## Manual state

Frozen state: **NONE**.

No local/manual Blender run is required for R10.9. The implementation uses the already accepted R10.2 Blender process boundary and a fixed Decimate surface; deterministic hosted fixtures are authoritative for the R10.9 preservation/lineage contract.

## Acceptance ordering

1. Run R0 + full Python Core + UI Smoke on the implementation candidate head.
2. If all succeed, bind candidate SHA/run IDs and test totals into this file exactly once.
3. Run fresh R0 + full Python Core + UI Smoke on that final documented head.
4. Merge the implementation PR with `expected_head_sha`.
5. Create exactly one continuity-only post-merge normalization.
6. Run R0 + full Python Core + UI Smoke on that normalization head and merge it.
7. Only that merge makes R10.9 **COMPLETE + NORMALIZED** and authorizes R10.10.
