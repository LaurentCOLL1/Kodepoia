# R10.11 — Acceptance record

Frozen manual intervention: **NONE**.

## Definition of Done

R10.11 is accepted only when one exact implementation head contains the governed
`BlenderService`, bounded `blender3d` CLI, non-blocking KodeStudio Blender/3D page,
localization/accessibility registration, dedicated service/CLI/UI tests and this design
record, and that exact head passes R0 Repository Guard, full Python Core and KodeStudio UI
Smoke.

The pull request metadata is the authoritative place to bind the immutable candidate SHA and
its three exact-head workflow run IDs. This file intentionally does not record its own future
commit SHA/run IDs, avoiding recursive documentation commits after acceptance.

## Required acceptance properties

- CLI and KodeStudio call `BlenderService`, not R10 runners or process APIs directly.
- Service inputs are managed IDs or finite typed choices.
- `blender3d` has no raw Python/expression/operator/executable/argv/path/URL/environment
  passthrough.
- Geometry recipe validation reconstructs the accepted R10.3 typed contract.
- QA, rig/skinning, animation/retarget, LOD and GLB/glTF views report explicit READY/MISSING/
  INVALID/CANCELLED states and never fabricate evidence.
- Runtime/evidence views are restricted to accepted R10 evidence IDs.
- KodeStudio work runs outside the GUI thread through `QRunnable`/`QThreadPool`.
- Cancellation remains available during a worker operation and the UI renders cancelling and
  cancelled/result states.
- Blender/3D controls have explicit accessibility registration and descriptions where
  context is required.
- Dedicated Blender/3D strings support source locale and `qps-ploc`.
- Existing R10.2/R10.10 manual acceptance commands remain intact.
- R7/R8/R9 integrated acceptance remains PASS.

## Manual state

**NONE.** Hosted deterministic tests are authoritative for R10.11. No real Blender/Godot run
is introduced by this subdivision.

## Merge and normalization rule

After the exact implementation head passes all three hosted gates, merge its dedicated PR.
Then create exactly one post-merge continuity-only normalization branch. Validate that
normalization head with the same three gates and merge it before R10.12 is authorized. Do
not create recursive continuity commits solely to write the normalization's own run IDs.
