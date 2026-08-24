# R11.7 — Acceptance

Status: **IMPLEMENTATION CANDIDATE — HOSTED GATES PENDING**  
Manual intervention: **CONDITIONAL — NOT TRIGGERED**

## Branch point and scope

- Base normalized `main`: `956fbf296a1ffc312fdd1e17e20ec39fb7fe20cc`.
- Branch: `r11/7-facial-performance-lod`.
- R11.7 scope only: facial target metadata adapter, facial performance profile, facial LOD, deterministic curve generation, QA and typed R5 Godot facial animation intent.
- No topology/rig generation, Blender editing, raw Godot resource/script materialization or real runtime playback claim.

## Required hosted acceptance

The exact implementation candidate must pass:

1. R0 Repository Guard — SUCCESS.
2. Full Python Core — SUCCESS on Ubuntu and Windows, with R7/R8/R9 integrated checks and package builds.
3. KodeStudio UI Smoke — SUCCESS.
4. Focused R11.7 tests demonstrate:
   - strict R10 target metadata shape/digest/range binding;
   - missing/spoofed targets fail closed;
   - deterministic curve generation from R11.6 viseme timelines;
   - explicit bounded clamping and clipping accounting;
   - facial LOD target filtering and critical semantic preservation;
   - key-density/total-key budgets;
   - typed R5 intents with no raw resource/script/path surface;
   - versioned JSON schema validation.

## Manual checkpoint decision

The frozen R11 plan triggers R11.7 manual intervention only for a real R10/Godot facial behavior claim that cannot be proved from accepted metadata/CI.

This candidate makes no such claim. It uses synthetic R10-shaped metadata and deterministic pure-Python curves/intents only. Therefore manual intervention is **NOT TRIGGERED**.

If a later change in this subdivision adds real import/playback/render behavior before merge, the checkpoint must be reclassified as triggered and the exact candidate SHA, repository fixture, command and machine-readable evidence requirements must be frozen before any local run.

## Completion ordering

- Freeze implementation head and run R0 + Python Core + UI Smoke.
- Record immutable candidate/run IDs in this document; re-run all three gates on the final documentation head.
- Merge exact accepted PR head with expected-SHA protection.
- Perform exactly one continuity-only post-merge normalization, re-gate it, and merge it.
- Only that normalization merge makes R11.7 COMPLETE + NORMALIZED and authorizes R11.8.
