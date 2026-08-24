# R10.10 — Acceptance record

Status: **HOSTED IMPLEMENTATION CANDIDATE — GATES PENDING; MANUAL REQUIRED NOT YET ACTIVE**  
Frozen manual intervention: **REQUIRED**

## Definition of Done

R10.10 requires exact-head R0 Repository Guard, full Python Core on Ubuntu/Windows with R7/R8/R9 still PASS, KodeStudio UI Smoke, strict typed glTF export/R8 binding, bounded GLB/glTF structural validation, fixed Blender 5.2 export/re-import, semantic material/UV/skin/bone/morph/animation preservation, R8 `gltf_export` lineage only after blockers clear, and real local Blender 5.2.x + Godot 4.7.x evidence with both canonical fixtures passing.

## Candidate implementation

- `gltf_contracts.py`, `gltf_validator.py`, `gltf_bootstrap.py`, `gltf_godot_fixture.py`, `gltf_runner.py`;
- `r10-gltf-accept` registered through the existing Blender CLI surface;
- three R10.10 JSON Schemas;
- deterministic contracts/parser/security/evidence tests plus CLI tests;
- `R10_10_DESIGN.md` and this record.

## Acceptance ordering

1. Freeze implementation candidate and run R0 + full Python Core + UI Smoke.
2. If successful, bind candidate SHA/run IDs/test totals here exactly once.
3. Freeze the documented/manual candidate and run fresh R0 + Python + UI.
4. Only then activate the REQUIRED local checkpoint.
5. Run exactly one `python -m kodepoia.cli r10-gltf-accept ...` from that exact SHA with legitimate local Blender 5.2.x and Godot 4.7.x.
6. Return canonical evidence, console summary, evidence SHA-256/bytes and runtime versions.
7. Review evidence; only a valid clean PASS can be bound, re-gated, merged and normalized.
8. Do not begin R10.11 before that normalization merge.

## Manual safety rules

Do not install add-ons/plugins/assets, enable Blender autoexec/online/user preferences, convert through FBX/ESCN, edit bundled fixtures, delete failed evidence before review, or relax sandbox/import/glTF rules after a failure. The exact manual SHA and PowerShell command will be bound only after hosted exact-head acceptance succeeds.
