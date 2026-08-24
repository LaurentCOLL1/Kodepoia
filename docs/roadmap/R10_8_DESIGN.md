# R10.8 — Human + animal profile pipelines

## Status

Hosted implementation candidate. Frozen manual state: **CONDITIONAL**.

## Frozen objective

R10.8 satisfies the frozen human/animal scope through governed reusable profile pipelines rather than proprietary generators or unbounded procedural code. Version 1 supports the two required profile families:

- `humanoid_biped`;
- `quadruped`.

CI fixtures are synthetic. They prove contract, schema, identity, compatibility and fail-closed QA behavior only; they make no claim about artistic quality, anatomical realism or production-readiness of a specific character/animal asset.

## Profile identity and R8 governance

`OrganicAssetProfile` binds exactly one canonical R8 asset revision through:

- `asset_id`;
- `revision_id`;
- `content_sha256`.

R10.8 deliberately does **not** copy licence assertions, creator/attribution fields or provenance locators into a second authority. The bound `AssetRevision` must remain a READY `model_3d` revision with provenance, while licence decisions remain exclusively governed by the accepted R8 `AssetGovernanceService` / `AssetLicenseEvidence` path. Derived-asset lineage and source requirements therefore stay in R8 rather than being reinterpreted here.

## Coordinate and scale policy

Profiles use the already frozen R10 coordinate basis:

- metric unit scale: `1.0` metre per Blender unit;
- forward: `-Z`;
- up: `Y`.

R10.8 does not expose arbitrary conversion matrices or hidden axis correction. An asset that is not normalized to this basis must be normalized by an earlier/later explicitly governed step rather than through profile metadata side effects.

## Governed pieces, materials and morph inventory

A profile declares stable pieces instead of relying on Blender display-name heuristics:

- exactly one `armature` piece whose object ID matches the governed `armature_id`;
- one or more `mesh` pieces with stable mesh IDs;
- material slots keyed by stable `(piece_id, slot_id)` plus their expected Blender-visible names;
- shape keys keyed by stable `(piece_id, key_id)` plus expected Blender-visible names;
- semantic zones that bind stable piece IDs and stable R10.7 semantic bone IDs.

The runtime-independent inventory protocol records actual piece/object/mesh identities, material-slot names, shape-key names and per-mesh/shape-key vertex counts. The validator can therefore reject missing/mismatched required data and either BLOCK or WARN on unexpected optional inventory according to the explicit QA policy.

Blender 5.2 describes Shape Keys as morph targets/blend shapes and explicitly states that vertices cannot be added or removed inside a Shape Key: the object's topology defines the vertex count/connectivity, while each key stores positions for the existing vertices. R10.8 consequently blocks any declared shape-key inventory whose vertex count differs from its bound mesh.

## R10.6 and R10.7 compatibility

Profiles cryptographically bind both accepted rig layers:

- exact `RigProfile.digest` from R10.6;
- exact `RigSemanticProfile.digest` from R10.7;
- stable `rig_id` and `armature_id`;
- explicit `required_deform_bones`;
- explicit `animation_bones`.

Required deform bones must be deforming bones in both contracts. Animation bones and semantic-zone bones must resolve exactly in the R10.7 semantic profile. No fuzzy/model-generated name matching is authoritative.

Blender 5.2's Python API exposes `EditBone.use_deform` as the flag enabling a bone to deform geometry. R10.8 consumes the already-governed deform distinction from R10.6/R10.7 rather than inventing an independent deform classification.

## QA policy and report

`OrganicProfileQAPolicy` freezes:

- exact/non-exact piece inventory;
- exact/non-exact material-slot inventory;
- exact/non-exact shape-key inventory;
- the maximum explicitly tolerated count of deform bones not assigned to a semantic zone.

`evaluate_organic_profile()` emits deterministic PASS/WARN/BLOCK rules for:

1. exact R8 revision binding;
2. R8 model/provenance/readiness;
3. exact R10.6 rig compatibility;
4. exact R10.7 semantic-rig compatibility;
5. required deform-bone coverage;
6. animation-bone coverage;
7. semantic-zone bone identity;
8. unmapped deform-zone coverage;
9. piece inventory;
10. material-slot inventory;
11. shape-key inventory;
12. shape-key topology;
13. frozen coordinate basis;
14. inventory binding to the exact rig digests.

The report is canonical-digest bound and schema validated.

## Security boundary

R10.8 introduces no Blender bootstrap, dynamic Python, subprocess, network client, `exec`/`eval`, arbitrary operator surface or model-supplied executable path. It is a pure structured-contract/validation layer over accepted R8/R10 data. Existing `WorkspaceBoundary`, `ProcessSandbox`, KillSwitch, Guardian/permissions, SafeChange/Backup/Recovery/Audit and asset governance remain authoritative.

Excluded scope remains excluded: proprietary human/animal generators, unbounded procedural character code, online asset-library installation, arbitrary Blender/Python execution and artistic-quality claims derived from synthetic fixtures.

## Frozen CONDITIONAL evaluation

The R10 plan makes a production/manual asset intervention conditional, not mandatory. No approved amendment currently requires a specific real human or animal production asset for R10.8, and the new functionality is a profile-contract/compatibility layer whose CI acceptance is authoritatively exercised by deterministic synthetic fixtures.

Therefore the hosted candidate evaluates the frozen manual state as:

**CONDITIONAL NOT TRIGGERED**

If a later approved scope amendment makes a specific production asset mandatory, that future condition must define bounded evidence and be evaluated separately; R10.8 does not manufacture production-art PASS from synthetic fixtures.

## Upstream compatibility references

- Blender 5.2 LTS Manual — Shape Keys introduction/workflow.
- Blender Python API 5.2 — `EditBone.use_deform`.

These references establish upstream semantics only. Kodepoia exact-head tests, schemas and governance remain the acceptance authority.
