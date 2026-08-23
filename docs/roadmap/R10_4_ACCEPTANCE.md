# R10.4 — Acceptance record

Status: **IMPLEMENTATION CANDIDATE; EXACT-HEAD GATES PENDING**  
Manual intervention: **CONDITIONAL NOT TRIGGERED**

## Definition of Done

R10.4 requires one exact implementation head with R0 Repository Guard + full Python Core + KodeStudio UI Smoke SUCCESS and prior R7/R8/R9 integrated acceptance still PASS.

Hosted tests must prove canonical recipe identity, bounded UV/material values, unique texture roles, trusted-root path confinement, immutable input/texture SHA-256 lineage, data-vs-color texture semantics, fixed Principled/Normal Map graph evidence, recipe-result tamper rejection, verified derived `.blend`, and absence of dynamic code/network/bake surfaces.

## Manual decision

The frozen CONDITIONAL gate is **NOT TRIGGERED** by the accepted design unless CI reveals that a required operation depends on backend-specific baking. R10.4 performs no bake and does not claim baked AO/normal output. The already reviewed R10.2 Blender 5.2.0 local-runtime probe remains the runtime baseline.

## Completion sequence

Freeze implementation head → exact-head three gates → record immutable evidence → repeat three gates on final documented head → merge PR with expected SHA → continuity-only normalization + exact-head three gates → merge normalization. Only then may R10.5 start.
