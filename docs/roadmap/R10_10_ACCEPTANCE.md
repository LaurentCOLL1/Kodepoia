# R10.10 — Acceptance record

Status: **HOSTED IMPLEMENTATION ACCEPTED; MANUAL REQUIRED PENDING FINAL HOSTED HEAD**  
Frozen manual intervention: **REQUIRED**

## Definition of Done

R10.10 requires exact-head R0 Repository Guard, full Python Core on Ubuntu/Windows with R7/R8/R9 still PASS, KodeStudio UI Smoke, strict typed glTF export/R8 binding, bounded GLB/glTF structural validation, fixed Blender 5.2 export/re-import, semantic material/UV/skin/bone/morph/animation preservation, R8 `gltf_export` lineage only after blockers clear, and real local Blender 5.2.x + Godot 4.7.x evidence with both canonical fixtures passing.

## Hosted implementation candidate — ACCEPTED

Implementation candidate: `1f4f61485016790b854244a5a0a43094b7c98bab`.

Exact-head hosted gates:
- R0 Repository Guard #1300 / `32692671006`: **SUCCESS**;
- Python Core #1274 / `32692671028`: **SUCCESS**;
- KodeStudio UI Smoke #1241 / `32692670992`: **SUCCESS**.

Python Core Ubuntu: **852 passed / 7 skipped / 46 warnings**; R7/R8/R9 integrated acceptance PASS. Windows Python, KodeStudio smoke, Ubuntu package build and Windows package build all SUCCESS.

## Accepted candidate implementation

- `gltf_contracts.py`, `gltf_validator.py`, `gltf_bootstrap.py`, `gltf_godot_fixture.py`, `gltf_runner.py`;
- `r10-gltf-accept` registered through the existing Blender CLI surface;
- three R10.10 JSON Schemas;
- deterministic contracts/parser/security/evidence tests plus CLI tests;
- `R10_10_DESIGN.md` and this record.

## Acceptance ordering

1. Hosted implementation candidate acceptance above is complete.
2. This binding commit becomes the documented/manual candidate head.
3. Run fresh R0 + full Python Core + UI Smoke on that exact head.
4. Only if all three succeed does the REQUIRED local checkpoint become active.
5. Run exactly one `python -m kodepoia.cli r10-gltf-accept ...` from that exact SHA with legitimate local Blender 5.2.x and Godot 4.7.x.
6. Return canonical evidence, console summary, evidence SHA-256/bytes and runtime versions.
7. Review evidence; only a valid clean PASS can be bound, re-gated, merged and normalized.
8. Do not begin R10.11 before that normalization merge.

## Manual success contract

The local evidence must have `schema=kodepoia.r10.gltf_local_acceptance`, `version=1`, the exact documented source SHA, `status=pass`, `blockers=[]`, a valid canonical `evidence_digest`, Blender 5.2.x with `background=true` and `online_access=false`, Godot 4.7 compatibility, Godot import return code 0, semantic smoke return code 0 with `KODEPOIA_R10_10_GODOT_PASS`, and non-empty SHA-256-bound `static.glb` + `rigged.glb` artifacts.

## Manual safety rules

Do not install add-ons/plugins/assets, enable Blender autoexec/online/user preferences, convert through FBX/ESCN, edit bundled fixtures, delete failed evidence before review, or relax sandbox/import/glTF rules after a failure. If a runtime path is unavailable, stop and report it instead of substituting another version or download route.
