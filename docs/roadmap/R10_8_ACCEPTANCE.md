# R10.8 — Acceptance record

Status: **HOSTED IMPLEMENTATION CANDIDATE — FINAL EXACT-HEAD GATES PENDING**  
Manual intervention: **CONDITIONAL NOT TRIGGERED**

## Definition of Done

R10.8 requires one exact hosted candidate head with:

- R0 Repository Guard SUCCESS;
- full Python Core SUCCESS on Ubuntu/Windows;
- R7/R8/R9 integrated acceptance still PASS;
- KodeStudio UI Smoke SUCCESS;
- both required profile kinds, `humanoid_biped` and `quadruped`;
- canonical R8 asset-revision binding without duplicating licence authority;
- frozen metre / `-Z` forward / `Y` up coordinate basis;
- stable armature/mesh piece inventory;
- explicit material-slot and shape-key/morph inventory;
- shape-key topology invariant;
- semantic-zone identity bound to governed R10.7 semantic bones;
- exact R10.6 `RigProfile` and R10.7 `RigSemanticProfile` digest compatibility;
- explicit deform-bone and animation-bone coverage;
- deterministic PASS/WARN/BLOCK QA report and report digest;
- JSON Schema validation for profile, inventory and report;
- no dynamic/external execution surface introduced by R10.8.

## Hosted fixture scope

The acceptance fixtures are deliberately synthetic and cover both `humanoid_biped` and `quadruped`. They validate structural contracts, stable identities, provenance binding, rig/animation compatibility, morph topology, QA policy and tamper/failure cases. They do **not** certify artistic quality, anatomical realism, skin/hair/fur quality or a specific production asset.

## R8 governance boundary

R10.8 stores only the exact R8 `asset_id`, `revision_id` and `content_sha256`. The validator requires a READY `model_3d` `AssetRevision` with provenance. Licence assertions, creator/attribution data, BOM decisions and export policy remain in the accepted R8 governance path and are not copied or weakened.

## R10.6 / R10.7 compatibility boundary

The profile binds exact digests for:

- R10.6 `RigProfile`;
- R10.7 `RigSemanticProfile`.

Stable `rig_id` / `armature_id`, required deform bones, semantic zones and animation bones must resolve exactly. Fuzzy bone matching is never authoritative.

## Morph/topology boundary

Blender 5.2 Shape Keys operate over the existing object's vertices; adding/removing vertices in a Shape Key is not allowed. R10.8 therefore records mesh and Shape Key vertex counts and BLOCKs any mismatch.

## CONDITIONAL decision

Frozen state: **CONDITIONAL**.

Current decision: **NOT TRIGGERED**.

Reason: the frozen R10.8 scope requires reusable governed human/animal profile pipelines and synthetic contract fixtures; no approved amendment currently makes a specific production human/animal asset mandatory. Synthetic fixtures are sufficient to authoritatively validate this contract layer and are explicitly not treated as evidence of artistic quality.

## Candidate contents

- `src/kodepoia/blender3d/profile_contracts.py`;
- `src/kodepoia/blender3d/profile_validator.py`;
- `schemas/r10-organic-profile-v1.schema.json`;
- `schemas/r10-organic-profile-inventory-v1.schema.json`;
- `schemas/r10-organic-profile-report-v1.schema.json`;
- `tests/test_blender_r10_8.py`;
- package exports in `src/kodepoia/blender3d/__init__.py`;
- this acceptance record and `R10_8_DESIGN.md`.

## Final ordering

1. Run the three hosted gates on the implementation candidate.
2. If they succeed, bind those results into this acceptance record once.
3. Run fresh R0 + full Python Core + UI Smoke on that final documented head.
4. Merge the R10.8 implementation PR with `expected_head_sha`.
5. Perform exactly one continuity-only post-merge normalization and validate that exact normalization head with the same three gates.
6. Only after the normalization merge is R10.8 **COMPLETE + NORMALIZED** and R10.9 authorized.
