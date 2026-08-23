# R10.6 — Armatures, skinning and weight validation

Status: **IMPLEMENTED CANDIDATE**  
Manual intervention: **CONDITIONAL — runtime deformation decision pending hosted gates**

## Purpose

R10.6 adds governed armature/skin contracts suitable for downstream real-time export without coupling semantic rig identity to Blender display names. It builds on normalized R10.5 mesh QA and the accepted R10.2 process boundary.

## Canonical rig contract

`RigProfile` version 1 binds one immutable input `.blend` SHA-256 to:

- a stable `rig_id` and `armature_id`;
- ordered semantic bones with parent, rest head/tail, `deform` vs control role and connected state;
- governed mesh IDs;
- `create` or `validate_existing` mode;
- allowlisted weight strategy per mesh: `explicit`, deterministic `nearest_deform_bone`, or `existing` only for imported-rig validation;
- influence profile: four influences by default, explicit opt-in up to eight, normalization tolerance, tiny-weight threshold and bounded deformation-probe requirement.

Profiles reject unknown fields, duplicate IDs, cycles/forward parent references, malformed connected rest positions, unknown/control-only explicit weight references and implicit >4 influence profiles. Canonical SHA-256 identifies the full profile.

## Creation and binding

The static bootstrap opens only staged `input.blend` with scripts disabled. `create` mode creates one armature, enters Edit Mode only to create the fixed profile bones, then records semantic IDs as bone properties and sets `Bone.use_deform` explicitly. Mesh binding creates only vertex groups named after governed deform bones, a fixed Armature modifier and armature parent while restoring the mesh world matrix.

`explicit` assignments are host-normalized after pruning values below the profile threshold. They are not silently truncated to the influence budget: an over-budget vertex is allowed to reach validation and BLOCK there. `nearest_deform_bone` is a Kodepoia-owned deterministic strategy: each vertex is transformed into armature space, distance to each governed rest-bone segment is computed, ties are resolved by semantic bone ID, and the nearest deform bone receives weight 1.0. Blender's automatic-weight operator is deliberately not used as an acceptance oracle.

`validate_existing` performs no rig creation/weight assignment. It requires an existing governed armature whose bones carry stable `kodepoia_bone_id` properties and validates existing groups/modifier/parent relationships.

## Weight and hierarchy validation

The result records semantic bone hierarchy/deform set and, for every mesh: weighted/zero-weight vertices, invalid/control references, normalization failures, influence overflows/max observed influences, tiny-weight count, orphan groups, Armature modifier binding, parent binding and a bounded pose/deformation probe.

The pure Python validator emits deterministic `PASS/WARN/BLOCK`. Zero weights, invalid/control references, bad sums, influence overflow, missing modifier/parent and required deformation-probe failure BLOCK. Tiny weights and orphan unrelated groups WARN. The exporter-facing deform set is therefore explicit and machine-readable.

## Deformation probe

For a weighted deform bone, the bootstrap temporarily applies a small fixed Z rotation, evaluates the mesh through the depsgraph, counts vertices moved beyond `1e-7`, restores the original pose and records pass/fail. The saved derivative is written only after restoration. This tests actual Armature modifier deformation rather than accepting hierarchy/weights by appearance alone.

Because hosted CI does not provide the accepted Blender 5.2 runtime, this probe is the R10.6 CONDITIONAL boundary. Hosted gates first validate all deterministic contracts, fake-protocol behavior and static bootstrap invariants. If those gates pass, a bounded local `scripts/r10_6_local_acceptance.py` run is required to authoritatively validate the real Blender deformation path before R10.6 can merge. Manual weight painting is never acceptance evidence.

## Local probe design

The local runner reuses the accepted `BlenderExecutableBoundary`, `ProcessSandbox`, R10.2 capability probe, R10.3 `GeometryRunner` and the R10.6 `RigRunner`. It creates a governed cube fixture, binds a one-bone rig with deterministic nearest-bone weighting, requires the real deformation probe to PASS, then emits one canonical JSON evidence file containing runtime, fixture, profile/report and output digests.

## Lineage and rollback

Input `.blend` is copied to empty staging and re-hashed after execution. Source is never overwritten. The only Blender derivative is fixed `rig_output.blend`, independently hashed and bound in the manifest as `parent_sha256 -> derived_sha256`. Direct durable R8 append remains fail-closed until a trusted lineage-backed binding is supplied; the manifest never invents a Vault identity.

Rollback means discarding staging/derived output. Imported-source validation never rewrites the source. Any future repair must be explicit and followed by R10.5/R10.6 revalidation.

## Official Blender 5.2 compatibility basis

- Armature modifier / Vertex Groups define per-bone deformation influence.
- `Bone.use_deform` excludes control-only bones from deformation.
- Edit bones have explicit parent/connected relationships.

No proprietary auto-rig, Rigify/add-on, network/model download, arbitrary operator, script path or manual painting surface is introduced.
