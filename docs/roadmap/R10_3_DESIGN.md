# R10.3 — Structured scene/geometry authoring + deterministic transform recipes

## Status

Implementation candidate. Manual intervention: **NONE**.

## Governed recipe boundary

R10.3 introduces `GeometryRecipe` v1. Recipes are structured data only. They carry a stable recipe ID, frozen meters / -Z-forward / Y-up convention, and a maximum of 256 allowlisted operation records. Object IDs are stable machine IDs independent of Blender display names. Every reference must resolve to an object declared earlier in the same recipe; impossible state and unknown fields fail closed before Blender launch.

Allowlisted operations cover scene reset, deterministic cube/plane/cylinder mesh creation, transform assignment, explicit transform apply policy, BMesh triangulation and normal recalculation, bounded Triangulate/Mirror/Solidify/Bevel modifiers, explicit modifier application, join, loose-part separation and origin policy. Numeric transforms and modifier parameters are bounded. Arbitrary operators, Python source, Geometry Nodes, URLs, add-ons, environment, argv and shader/material work are not recipe surfaces.

R8 source inputs remain immutable by architecture. R10.3 never overwrites or promotes source assets. This first geometry executor produces a new staging-only `.blend`. Direct R8 source-file append is intentionally fail-closed until a trusted source-binding resolver can provide lineage-backed staged inputs without exposing model-supplied filesystem paths; this is the meaning of the frozen plan's “where supported” qualifier and does not weaken the R8 boundary.

## Blender execution

`GeometryRunner` layers on the accepted R10.2 `BlenderRunner` and therefore inherits `ProcessSandbox`, KillSwitch, fixed Blender argv, factory startup, disabled autoexec, offline mode, bounded stdout/stderr and timeout semantics.

A static Kodepoia-owned bootstrap interprets only the validated operation catalog. Geometry mutation favors `bpy` data API and BMesh. Context-sensitive Blender operators are wrapped by `activate()`, which restores Object mode, clears selection and sets one explicit active object before transform apply, modifier apply, join, separate or origin operations.

The bootstrap records source and evaluated mesh statistics for every governed object and writes one new `geometry_output.blend` into staging. It emits a bounded machine-readable result that binds the canonical recipe digest. The host re-hashes and size-checks the staged `.blend`; a result-file digest mismatch or artifact spoof becomes FAIL.

## Determinism model

Semantic determinism is defined as stable recipe identity plus equivalent governed object IDs, source/evaluated topology counts, modifier identities and operation manifest for repeated canonical fixtures. Binary `.blend` bytes are evidence but are not required to be byte-identical across Blender builds.

## Blender 5.2 compatibility evidence

Official Blender Python documentation confirms BMesh as the internal mesh-editing API, including explicit conversion between `bpy.types.Mesh` and BMesh and explicit mesh updates after edits. Blender 5.2 documentation also defines Triangulate behavior and bounded split-method choices. R10.3 follows those APIs rather than depending on UI state.

## Security / rollback

- no shell invocation;
- no dynamic Python code or network API in the bootstrap;
- no arbitrary modifier/operator/argv/path surface;
- staging workspace must be empty before execution;
- source assets are never overwritten;
- failed or rejected derived `.blend` files are disposable staging artifacts;
- no R8 Vault promotion occurs in R10.3.
