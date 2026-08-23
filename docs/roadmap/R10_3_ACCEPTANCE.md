# R10.3 — Acceptance record

Status: **IMPLEMENTATION ACCEPTED; FINAL DOCUMENTED HEAD PENDING GATES**  
Manual intervention: **NONE**

## Accepted immutable implementation head

`5a3042ae4d7214fb8cfe5d2790eae229563d9fc6`

Exact-head implementation gates:

- R0 Repository Guard #1231 / `32664784120`: **SUCCESS**.
- Python Core #1205 / `32664784136`: **SUCCESS**.
- KodeStudio UI Smoke #1172 / `32664784085`: **SUCCESS**.

Python Core Ubuntu reported **772 passed / 7 skipped / 46 warnings** and explicitly retained R7, R8 and R9 integrated acceptance as PASS. Package builds on Ubuntu/Windows and the embedded Windows UI job also succeeded.

## Accepted behavior

- canonical geometry recipe digest is stable;
- recipe/manifest schemas validate representative documents;
- stable machine object IDs are independent of display names;
- undeclared references, unsupported operations, unknown fields and invalid transform/modifier budgets fail closed before Blender launch;
- scene reset, deterministic cube/plane/cylinder creation, transform/apply policy, triangulation, normal recalculation, bounded modifiers, join/separate and origin policy are structured operations rather than arbitrary Python/operator surfaces;
- fake Blender execution records expected source/evaluated topology statistics and verifies a staging-only `.blend` artifact;
- recipe-result digest tampering and artifact identity spoofing cannot become PASS;
- the static bootstrap contains no `exec`, `eval`, subprocess, socket, urllib or requests surface;
- source assets are never overwritten or promoted by R10.3.

## Semantic fixture

The canonical hosted fixture creates one cube, applies scale explicitly, triangulates it using fixed methods, recalculates normals and sets origin. Accepted fake-runner semantics are one governed object, 8 vertices, 12 faces/triangles and no remaining modifiers.

Binary `.blend` byte identity is not a cross-build requirement; semantic statistics + canonical recipe/manifest identity are authoritative.

## R8 source boundary

The frozen plan permits import of declared R8 source meshes “where supported”. R10.3 deliberately does not expose a recipe-level filesystem path. Direct append remains fail-closed until a trusted lineage-backed binding can stage an already-declared R8 revision without granting model/user recipe data an arbitrary path surface. This preserves, rather than weakens, the frozen WorkspaceBoundary/R8 immutability rule.

## Manual state

**NONE.** The accepted real Blender 5.2.0 runtime evidence from R10.2 remains the authoritative runtime compatibility baseline. R10.3 adds no new backend/hardware-dependent requirement and therefore does not trigger another local gate.

## Final documentation gate

This update changes acceptance documentation only after the immutable implementation head was accepted. The resulting final documented head must itself pass R0 Repository Guard + full Python Core + KodeStudio UI Smoke before PR #135 merges. After merge, one continuity-only normalization with the same exact-head gates is still required before R10.4 may begin.
