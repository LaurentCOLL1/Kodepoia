# R10.5 — Mesh QA design

Status: **IMPLEMENTED CANDIDATE**  
Manual intervention: **NONE**

## Purpose

R10.5 makes Blender mesh readiness measurable before rigging/export. The validator is deliberately read-only: it never edits the source `.blend`, never saves a replacement, and never silently repairs a defect.

The frozen R10 plan remains authoritative. R10.5 covers source/evaluated topology, normals/winding, tangent-space availability, UV facts, transforms and production budgets with deterministic `PASS/WARN/BLOCK` rules.

## Architecture

### 1. Canonical profile

`MeshQAProfile` contains stable profile/object IDs, immutable input `.blend` SHA-256, asset class (`closed_static`, `open_static`, `character`, `animal`), explicit boundary/UV-overlap policy, finite bounded tolerances, and object/triangle/material/texture/shape-key/UV/topology/scale budgets. Profiles reject unknown fields and unbounded values. Profile identity is canonical SHA-256.

### 2. Blender measurement pass

`MeshQARunner` reuses the accepted R10.2 `BlenderRunner`, executable boundary, `ProcessSandbox`, fixed argv and offline/factory-startup/autoexec-disabled policy. The host resolves one governed `.blend` beneath `input_root`, verifies its SHA-256, copies it to empty staging as `input.blend`, and passes only the normalized profile to the static bootstrap. Profile data never carries arbitrary filesystem paths.

The bootstrap opens with `use_scripts=False`, resolves only requested `kodepoia_id` mesh objects, inspects source and depsgraph-evaluated mesh, uses BMesh connectivity for loose/wire/boundary/manifold/winding facts, measures face area and finite coordinates, loop triangles, per-layer UV bounds/triangle-area sums/zero-area UV triangles, O(n) quantized coincident-vertex indicators, material/image/shape-key counts, tangent-space normal-map requirements through `Mesh.calc_tangents(uvmap=...)`, and transform finiteness/non-uniform scale ratio.

No `.blend` is saved. The host re-hashes staged `input.blend` after the process and blocks any unexpected additional `.blend` output.

Official Blender 5.2 basis:
- BMesh connectivity and `BMEdge.is_boundary/is_manifold/is_wire/is_contiguous`: https://docs.blender.org/api/5.2/bmesh.types.html
- `Mesh.calc_loop_triangles()` and `Mesh.calc_tangents(uvmap=...)`: https://docs.blender.org/api/5.2/bpy.types.Mesh.html
- `MeshPolygon.area`: https://docs.blender.org/api/5.2/bpy.types.MeshPolygon.html

### 3. Pure Python decision engine

`evaluate_mesh_qa()` consumes normalized measurements plus the canonical profile. Blender does not decide severity. Every ordered rule records `rule_id`, applicability, value, limit/policy, `PASS/WARN/BLOCK`, and reason. Any BLOCK makes the report `block`; warnings produce `warn`; otherwise it is `pass`. The report is canonically digested.

Boundary edges are profile-aware: a closed static prop can block them while a character/open mesh can explicitly allow or warn. This avoids treating every legitimate seam/boundary as defective.

### 4. UV overlap semantics

Full arbitrary UV-overlap detection is intentionally not performed by the bootstrap because naive pairwise testing is O(n²) and conflicts with the frozen performance-risk constraint. The bootstrap records `not_measured` plus deterministic coverage facts (UV bounds and triangle-area sums).

Profiles default to `overlap_policy=ignore`. If a caller explicitly requests `warn` or `block` while authoritative overlap measurement is unavailable, the engine never manufactures PASS: it returns WARN or BLOCK respectively. A future bounded overlap provider may supply `status=measured` and `overlap_pairs` without changing report semantics.

### 5. Explicit repair subset

`MeshRepairRecipe` is a typed, canonical, allowlisted **request contract**. R10.5 v1 allows only `recalculate_normals`. The QA validator never executes repair recipes. R10.5 intentionally exposes no destructive repair executor because the validator must remain read-only and the frozen R10.3 existing-asset lineage bridge remains fail-closed. No repair is silently applied and no derived asset is falsely claimed. Any future execution must create a new derivative and re-run R10.5 before promotion.

## Rule families

Governed object resolution; source/evaluated finite coordinates; degenerate faces; loose vertices/wire edges; boundary policy; branching/non-manifold edges; winding consistency; duplicate indicators; object/evaluated-triangle/material/texture/shape-key budgets; UV layer/missing/zero-area checks; fail-closed overlap policy; transform finiteness/scale sanity; and normal-map tangent validity.

## Security and invariants

No arbitrary executable/argv/cwd/environment/path/node/operator/network surface; static bootstrap only; no save/delete/modeling operators; no source overwrite; no automatic fix; exact source SHA-256/profile digest binding; missing/tampered measurements block; R7/R8/R9 integrated acceptance remains authoritative.

## Rollback

QA creates only staging JSON and a staging copy of the source. Deleting staging rolls back the run. There is no source mutation to recover.
