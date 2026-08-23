# R10.5 — Acceptance record

Status: **IMPLEMENTATION CANDIDATE; EXACT-HEAD GATES PENDING**  
Manual intervention: **NONE**

## Definition of Done

R10.5 requires one immutable implementation head with R0 Repository Guard, full Python Core and KodeStudio UI Smoke SUCCESS on the exact same head, R7/R8/R9 integrated acceptance still PASS, and deterministic hostile fixtures for profile bounds, malformed geometry facts, topology policy, tangents, UV evidence, budgets, tamper rejection and read-only behavior.

## Required evidence

Hosted tests must prove canonical profile and explicit repair-request identities; unknown/unbounded values rejection; profile-aware boundary severity; blocking of non-finite/degenerate/loose/non-manifold/winding/budget defects; evaluated triangle budgets; required normal-map tangents; no manufactured PASS for requested unavailable overlap evidence; unchanged input `.blend` SHA-256 with no derived `.blend`; profile/input tamper blocking; schema acceptance; and a static/offline/read-only bootstrap without dynamic code, network, save/delete or mesh-edit operator surface.

## Manual state

**NONE.** R10.5 introduces no new hardware/backend-specific acceptance requirement. Blender 5.2 runtime viability is inherited from accepted R10.2 real-runtime evidence.

## Completion sequence

Freeze implementation head → exact-head R0/Python/UI → record immutable evidence here → repeat the three gates on the final documented head → merge with expected SHA → continuity-only normalization with exact-head gates → merge normalization. Only then may R10.6 start.
