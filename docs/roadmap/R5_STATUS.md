# R5 — KodeGodot 4.7.x — Status

**Phase:** R5  
**Status:** IN PROGRESS  
**Started:** 2026-08-21

R5 starts from normalized `main` commit `0b03de919721d3a292a00b4a1544100779416a53`. R4 remains COMPLETE and is not reopened.

## Acceptance subdivisions

The frozen R5 scope is implemented incrementally without changing architecture v1.0:

1. **R5.1 — Engine/project foundation** — ACCEPTED AND MERGED.
2. **R5.2 — Scene/resource intelligence** — NEXT / NOT STARTED.
3. **R5.3 — GDScript + Godot LSP/DAP specialization** — NOT STARTED.
4. **R5.4 — 2D/3D domain intelligence and safe edits** — NOT STARTED.
5. **R5.5 — Headless automation/import/export/capture/benchmarks** — NOT STARTED.
6. **R5.6 — Governed orchestration + real Godot acceptance** — NOT STARTED.

## R5.1 — Engine/project foundation — ACCEPTED AND MERGED

PR #22 — `R5.1 protected Godot 4.7 engine/project foundation` — MERGED.  
Merge commit: `47f78db21dfd97ac228548358edce1ac5a73cce3`.

Delivered:
- new `kodepoia.kodegodot` package;
- read-only `project.godot` inspector without evaluating Godot Variant expressions;
- project metadata: config version, name, main scene, renderer, features and asset counts;
- protected Godot runtime backed by R1 `ProcessSandbox` + global kill switch;
- version parsing and explicit Godot 4.7.x compatibility check;
- named GDScript `--check-only --script` operation;
- named headless `--import` operation;
- bounded headless project/scene smoke using `--quit-after` and optional `--scene`;
- workspace confinement for script/scene paths;
- structured `GodotToolAPI` with `additionalProperties=false` and no arbitrary argv/args/flags input;
- implementation-level timeout/frame bounds;
- unit tests for metadata, version compatibility, exact command construction, path escape and Tool API secrecy.

Accepted functional head `041728735d761d1f17abeb38cce86f9b951db36a`:
- R0 Repository Guard `32525599593` — SUCCESS;
- Python Core `32525599591` — SUCCESS Ubuntu + Windows;
- KodeStudio UI Smoke `32525599578` — SUCCESS Windows.

Accepted final documentation head `3d96115eca23086c349c02122bf2df25cb5272e3`:
- R0 Repository Guard `32525764358` — SUCCESS;
- Python Core `32525764337` — SUCCESS Ubuntu + Windows;
- KodeStudio UI Smoke `32525764403` — SUCCESS Windows.

## R5.1 external contract verified against Godot 4.7 docs

Kodepoia intentionally wraps only documented commands rather than relaying arbitrary CLI flags. The Godot 4.7 CLI documents `--version`, `--path`, `--headless`, `--check-only` with `--script`, `--import`, `--quit-after`, `--scene`, `--lsp-port`, `--dap-port`, export options and `--write-movie`. Unknown command-line arguments can be ignored by Godot, so Kodepoia command construction remains allowlisted and method-based.

## Next — R5.2

R5.2 will parse and model Godot 4 text scene/resource structure (`.tscn`/`.tres`), including descriptors, external/internal resources, nodes, connections and string UIDs, while preserving provenance and the R4 safe tool boundary.

## Completion rule

R5 is **not COMPLETE** until all R5.1–R5.6 requirements have implementation, tests, CI evidence and final real-Godot acceptance. R6 must not begin early.
