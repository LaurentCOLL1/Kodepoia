# R11.8 — Acceptance

Status: **IMPLEMENTATION CANDIDATE — HOSTED GATES PENDING**  
Manual intervention: **NONE**

## Branch point and scope

- Base normalized `main`: `c3d091fb88acfc2bd054521fd3c76904eff0b885`.
- Branch: `r11/8-cinematic-timeline`.
- Scope: rational frame timebase, ShotDefinition, SequenceTimeline, allowlisted track/event records, deterministic branches, validation/budgets and canonical schemas.
- No Godot runtime/movie capture; no arbitrary scripted event execution.

## Required hosted acceptance

The exact implementation candidate must pass:

1. R0 Repository Guard — SUCCESS.
2. Full Python Core — SUCCESS on Ubuntu and Windows, including R7/R8/R9 integrated checks and package builds.
3. KodeStudio UI Smoke — SUCCESS.
4. Focused R11.8 tests demonstrate exact rational frame conversion, stable shot/sequence identities, allowlisted event payloads, missing/spoofed refs failure, gaps/overlaps, nested cycle detection, deterministic branches, budgets and schema validation.

## Manual checkpoint

**NONE.** R11.8 timeline semantics are fully testable with synthetic fixtures and exact frame arithmetic; no user-side engine run is required.

## Completion ordering

- Freeze implementation head and run R0 + Python Core + UI Smoke.
- Record immutable candidate/run IDs here and re-run all three gates on the final documentation head.
- Merge exact accepted PR head with expected SHA.
- Perform exactly one continuity-only normalization, gate it, merge it.
- Only that normalization merge makes R11.8 COMPLETE + NORMALIZED and authorizes R11.9.
