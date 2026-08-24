# R10.9 — LOD generation, preservation checks + variant lineage

Status: **IMPLEMENTATION CANDIDATE**

## Frozen objective

R10.9 generates controlled lower-detail derivatives while proving that material, UV, normal, shape-key and skinning semantics remain within explicit governed budgets. Source meshes are immutable and every accepted tier is a separate R8 derived revision.

## Architecture

The implementation adds four bounded components:

1. `LODProfile` / `LODTier` / `LODPreservationPolicy` define source identity, static-vs-skinned mode, exact triangle targets, preservation limits and R8 output asset IDs.
2. `LOD_BOOTSTRAP_SOURCE` is a fixed offline Blender script. It resolves one governed mesh through `kodepoia_id`, re-opens the immutable staged source for each tier, applies only Blender's `DECIMATE` modifier in `COLLAPSE` mode, measures the result and writes one `.blend` derivative per tier.
3. `evaluate_lod_measurements()` converts measurements into deterministic PASS/WARN/BLOCK rules.
4. `LODRunner` composes the accepted Blender process boundary, verifies staged input and every derivative digest, and emits promotion-ready R8 `AssetRevision` identities only when no BLOCK remains.

No caller supplies arbitrary Python, Blender operator names, argv, environment, URLs or output paths.

## Blender 5.2 semantics used

The Blender 5.2 LTS manual defines Decimate Collapse ratio as the proportion of triangles retained and notes that vertex groups can influence collapse. R10.9 therefore validates observed triangle ratios against explicit tolerance rather than assuming exact polygon counts.

The same manual exposes material/UV/seam delimitation for planar decimation. R10.9 deliberately does not generalize those planar controls to Collapse mode; instead it checks post-operation material-slot and UV-layer identity.

Blender Shape Keys use a fixed mesh vertex topology. Because Collapse changes topology, the default policy is `block_if_present`. `drop_explicit` exists only as an explicit lossy policy and produces WARN evidence; it never silently claims morph preservation.

References:
- https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/decimate.html
- https://docs.blender.org/api/5.2/bpy.types.ShapeKey.html
- https://docs.blender.org/api/5.2/bpy.types.Object.html

## Contracts

### Source identity

A profile binds exact R8 `source_asset_id`, R8 `source_revision_id`, source/content SHA-256, `.blend` input SHA-256, governed mesh object ID, R10.5 mesh-QA profile digest, and R10.6 rig-profile digest when `asset_mode=skinned`.

The source R8 revision must be READY, `model_3d`, provenance-bearing and content-identical to the staged `.blend`.

### Tier contract

Each tier declares a stable `tier_id`, separate R8 `output_asset_id`, target triangle ratio and absolute min/max triangle budget. Ratios must be strictly descending. A tier may never overwrite the source asset identity.

### Preservation policy

Mandatory checks include monotonic triangle reduction, triangle budget + ratio tolerance, material-slot order/identity, UV-layer order/identity, finite/non-degenerate normals, Shape Key policy, bounded axis-aligned extent drift and bounded surface-area drift.

Skinned tiers additionally require all governed deform vertex-group names, zero unweighted vertices, bounded weight-sum error and bounded influence count. Static tiers may not silently gain skin groups.

## Shape Key policy

`block_if_present` is fail-closed and is the default acceptance pattern for topology-changing LOD generation. `drop_explicit` permits an explicit lossy derivative. Source Shape Keys remain visible in the source measurement, output Shape Keys must be absent, and the report is WARN rather than PASS. This is never interpreted as morph preservation.

## R8 variant lineage

For every non-blocked tier, `make_lod_variant_revision()` creates a deterministic derived R8 revision with role `derived`, kind `model_3d`, preservation `evictable_derived`, provenance `transform`, lineage relation `lod_variant`, exact parent `source_revision_id`, and stable transform ID `blender.lod.v1.<profile>.<tier>`.

No Vault mutation is performed by the Blender bootstrap. Promotion remains governed by R8.

## Security / boundedness

The bootstrap imports no network or subprocess modules; contains no `exec`/`eval`, driver creation, text-block execution or URL opening; opens only the fixed staged `input.blend`; resolves only a typed `kodepoia_id`; creates fixed `lod_<tier_id>.blend` outputs under staging; and runs through the accepted `BlenderRunner` / `ProcessSandbox` boundary.

## Acceptance fixture scope

Hosted fixtures are synthetic: one static LOD profile, one skinned LOD profile, shape-key fail-closed and explicit-drop cases, adversarial material/UV/normal/silhouette/weight failures, runner artifact/profile tamper cases, and R8 source/variant lineage checks. They prove pipeline contracts and failure semantics, not artistic quality.

## Manual intervention

**NONE**, per frozen R10 plan. R10.9 adds no new acceptance seam requiring a local production asset or new executable capability beyond accepted Blender 5.2 runtime/process evidence.
