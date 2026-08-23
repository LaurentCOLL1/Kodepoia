# R10.5 — Acceptance record

Status: **IMPLEMENTATION ACCEPTED; FINAL DOCUMENTED HEAD GATES PENDING**  
Manual intervention: **NONE**

## Definition of Done

R10.5 requires one immutable implementation head with R0 Repository Guard, full Python Core and KodeStudio UI Smoke SUCCESS on the exact same head, R7/R8/R9 integrated acceptance still PASS, and deterministic hostile fixtures for profile bounds, malformed geometry facts, topology policy, tangents, UV evidence, budgets, tamper rejection and read-only behavior.

## Accepted immutable implementation head

`9b8ba987fc3ba6cc37b342d345c2af83f6802e20`

Exact-head gates:

- R0 Repository Guard #1242 / run `32666866880`: **SUCCESS**.
- Python Core #1216 / run `32666866872`: **SUCCESS**. Ubuntu reported **788 passed / 7 skipped / 46 warnings**. R7 integrated acceptance: PASS. R8 integrated acceptance: PASS. R9 integrated acceptance: PASS. Package-build and Windows matrix jobs are part of the successful workflow.
- KodeStudio UI Smoke #1183 / run `32666866877`: **SUCCESS**.

## Accepted scope and evidence

Hosted tests prove canonical profile and explicit repair-request identities; unknown/unbounded values rejection; profile-aware boundary severity; blocking of non-finite/degenerate/loose/non-manifold/winding/budget defects; evaluated triangle budgets; required normal-map tangents; no manufactured PASS for requested unavailable overlap evidence; unchanged input `.blend` SHA-256 with no derived `.blend`; profile/input tamper blocking; schema acceptance; and a static/offline/read-only bootstrap without dynamic code, network, save/delete or mesh-edit operator surface.

The implementation separates measurement from severity decisions: Blender collects source/evaluated facts, while the deterministic Python engine applies `PASS/WARN/BLOCK` profile rules. Boundary edges are not globally errors. Requested UV-overlap verification fails closed when an authoritative bounded measurement is unavailable. Tangent-space normal-map requirements are validated with Blender's `Mesh.calc_tangents(uvmap=...)` API.

`MeshRepairRecipe` is deliberately a typed request contract only. R10.5 v1 allows `recalculate_normals`; the QA validator never executes repair, never mutates source geometry, and never claims a derivative without a governed lineage path and re-validation.

## Manual state

**NONE.** R10.5 introduces no new hardware/backend-specific acceptance requirement. Blender 5.2 runtime viability is inherited from accepted R10.2 real-runtime evidence.

## Final documentation gate

This evidence update creates a new exact final documented head. R0 Repository Guard + full Python Core + KodeStudio UI Smoke must all succeed on that exact SHA before PR merge. The merge must use that SHA as `expected_head_sha`.

## Completion sequence

Final documented head exact gates → merge PR with expected SHA → continuity-only normalization with exact-head gates → merge normalization. Only then may R10.6 start.
