# R10.11 — CLI + KodeStudio Blender/3D UX design

## Objective

Expose the already accepted R10.1–R10.10 Blender/3D capabilities through one governed
`BlenderService` shared by CLI and KodeStudio. R10.11 is an orchestration and presentation
layer only: it does not add a second Blender execution boundary and it never exposes raw
Python, operators, processes, executable selection, argv, environment variables, URLs or
arbitrary filesystem paths.

Frozen manual intervention: **NONE**.

## Service boundary

`kodepoia.blender3d.service.BlenderService` is the only R10.11 façade used by the new CLI
surface and the KodeStudio Blender/3D page.

Its public inventory is bounded to:

- `status`
- `capabilities`
- `inspect`
- `validate_geometry`
- `qa`
- `rig`
- `animation`
- `lod`
- `export`
- `evidence`

Inputs are stable IDs matching `^[a-z][a-z0-9_.-]{0,63}$`. Recipes and reports are resolved
under fixed Kodepoia-managed metadata roots below `.kodepoia/blender/r10_11`; accepted local
runtime evidence is restricted to the four known R10 IDs `r10.2`, `r10.6`, `r10.7` and
`r10.10`. Missing, malformed, oversized, cancelled and invalid states remain explicit.

Geometry recipe validation reconstructs the accepted R10.3 `GeometryRecipe` contract and
therefore inherits its allowlisted operations, bounded parameters, metres / `-Z` forward /
`Y` up basis and digest semantics.

## CLI

The new entry point is:

`python -m kodepoia.cli blender3d <operation>`

Supported operations are `status`, `capabilities`, `inspect`, `geometry`, `qa`, `rig`,
`animation`, `lod`, `export` and `evidence`. They accept only typed choices and managed IDs.

The existing R10.2 and R10.10 acceptance commands remain unchanged because their explicit
runtime paths belong to already accepted REQUIRED local acceptance procedures. Those legacy
manual commands are not the R10.11 UX surface.

The `blender3d` parser rejects raw process/Python/path options such as `--python`, `--expr`,
`--argv`, `--executable` and `--path`.

## KodeStudio

`kodepoia.kodestudio.blender_panel` adds a Blender/3D page backed only by
`BlenderService`. The page shows:

- accepted runtime evidence;
- accepted capability count and structured inventory;
- managed report kind + stable record ID;
- managed geometry recipe validation;
- allowlisted R10 local evidence;
- read-only structured QA/report details;
- explicit IDLE / RUNNING / CANCELLING / result states.

Operations run through `QRunnable` + `QThreadPool` so the Qt GUI thread remains responsive.
Each active operation receives a thread-safe `BlenderCancellation` token and the Cancel
button remains available while work is active.

A dedicated Blender/3D localization catalog registers all page labels, descriptions and
status strings, including `qps-ploc` pseudo-locale support. Interactive controls are
registered through the existing KodeStudio accessibility contract.

## Security invariants

R10.11 must not:

- import or call `bpy`;
- launch a process or construct Blender/Godot argv;
- accept Python source, expressions, operator names or shell fragments;
- accept arbitrary paths, executable paths, environment variables or URLs;
- install add-ons, assets, models or plugins;
- reinterpret a missing report/evidence record as PASS;
- bypass R10.1 `BlenderExecutableBoundary`, `ProcessSandbox`, KillSwitch, Guardian or prior
  R10 typed contracts.

Actual Blender execution remains owned by the previously accepted runners/boundaries. R10.11
only exposes their governed contracts and persisted evidence through an ID-based UX façade.

## Validation

Acceptance requires the exact candidate head to pass:

1. R0 Repository Guard;
2. full Python Core on Ubuntu and Windows, with R7/R8/R9 integrated acceptance still PASS;
3. KodeStudio UI Smoke;
4. dedicated R10.11 service/CLI/UI tests;
5. pseudo-locale and accessibility registration;
6. non-blocking worker + cancellation state rendering;
7. forbidden raw process/Python/path parser and source tests.

No local Blender or Godot intervention is required for R10.11.
