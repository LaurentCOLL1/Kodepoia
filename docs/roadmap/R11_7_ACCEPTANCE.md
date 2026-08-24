# R11.7 — Acceptance

Status: **IMPLEMENTATION ACCEPTED; FINAL EXACT-HEAD GATES PENDING**  
Manual intervention: **CONDITIONAL — NOT TRIGGERED**

## Branch point and scope

- Base normalized `main`: `956fbf296a1ffc312fdd1e17e20ec39fb7fe20cc`.
- Branch: `r11/7-facial-performance-lod`.
- R11.7 scope only: facial target metadata adapter, facial performance profile, facial LOD, deterministic curve generation, QA and typed R5 Godot facial animation intent.
- No topology/rig generation, Blender editing, raw Godot resource/script materialization or real runtime playback claim.

## Accepted implementation candidate

Implementation candidate: `1d2347178b804ae46e8696a8fd78e88e8cb2d84b`.

Exact-head hosted gates:
- R0 Repository Guard #1408 / `32748232176`: **SUCCESS**;
- Python Core #1382 / `32748232050`: **SUCCESS**;
- KodeStudio UI Smoke #1349 / `32748231962`: **SUCCESS**.

Python Core Ubuntu: **990 passed / 8 skipped / 46 warnings**; R7/R8/R9 integrated acceptance PASS. Windows Python, KodeStudio internal smoke and both package builds also SUCCESS.

The accepted implementation demonstrates:
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

## Final acceptance ordering

1. Freeze the documentation-bound branch head containing this record.
2. Run fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke on that exact head.
3. Merge PR #169 only if all three are SUCCESS and the PR head has not moved.
4. Create exactly one continuity-only post-merge normalization branch from resulting `main`.
5. Run fresh R0 + Python + UI on the normalization head and merge only if all three are SUCCESS.
6. Only after that normalization merge is R11.7 **COMPLETE + NORMALIZED** and R11.8 authorized.
