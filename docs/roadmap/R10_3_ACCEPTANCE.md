# R10.3 — Acceptance record

Status: **IMPLEMENTATION CANDIDATE; EXACT-HEAD GATES PENDING**  
Manual intervention: **NONE**

## Frozen acceptance requirements

R10.3 is accepted only if one exact head passes R0 Repository Guard + full Python Core + KodeStudio UI Smoke while prior R7/R8/R9 integrated acceptance remains PASS. Hosted deterministic tests must prove:

- canonical recipe digest stability;
- schema validation for geometry recipes/manifests;
- stable object identity independent of display names;
- undeclared references and unsupported operations block before Blender launch;
- numeric transform/modifier budgets fail closed;
- join/separate identity rules are explicit;
- fake Blender execution produces expected source/evaluated topology statistics and a verified staging `.blend`;
- recipe-result digest tampering and artifact spoofing do not become PASS;
- the static bootstrap exposes no `exec`, `eval`, subprocess or network client surface;
- original source assets are never overwritten or promoted.

## Semantic fixture

The canonical hosted fixture creates one cube, applies scale explicitly, triangulates it using fixed methods, recalculates normals and sets origin. Expected accepted semantics after triangulation are one governed object, 8 vertices, 12 faces/triangles and no remaining modifiers in the fake-runner manifest.

Binary `.blend` byte identity is not a cross-build requirement; semantic statistics + canonical recipe/manifest identity are authoritative.

## Manual state

**NONE.** The previously accepted real Blender 5.2.0 runtime evidence from R10.2 remains the authoritative runtime compatibility baseline. R10.3 adds no new hardware/backend-dependent requirement and does not trigger another local gate.

## Completion sequence

1. Freeze implementation head.
2. Require exact-head R0 + Python Core + UI Smoke.
3. Record immutable gate IDs in this file, producing a final documented head.
4. Require the three gates again on that final documented head.
5. Merge the R10.3 PR using `expected_head_sha`.
6. Perform one continuity-only post-merge normalization with the same exact-head gates.
7. Only after that normalization merge may R10.4 start.
