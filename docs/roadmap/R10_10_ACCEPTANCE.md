# R10.10 — Acceptance record

Status: **LOCAL REQUIRED ATTEMPT REJECTED; HARDENING HOSTED GATES PENDING**  
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

## First documented/manual candidate — HOSTED ACCEPTED, LOCAL REJECTED

Documented/manual candidate: `64e21eca32be4fc47944962b57f341b7ed2dbf09`.

Exact-head hosted gates:
- R0 Repository Guard #1301 / `32692800763`: **SUCCESS**;
- Python Core #1275 / `32692800872`: **SUCCESS**;
- KodeStudio UI Smoke #1242 / `32692800747`: **SUCCESS**.

Python Core Ubuntu: **852 passed / 7 skipped / 46 warnings**; R7/R8/R9 integrated acceptance PASS. Windows Python and both package builds SUCCESS.

The REQUIRED local run on Windows with Blender **5.2.0 LTS** and Godot **4.7.2 stable Steam** returned exit code 2 and canonical evidence `status=fail`. The evidence is preserved as `R10_10_LOCAL_ACCEPTANCE_REJECTED_64e21eca.json`, **952 bytes**, SHA-256 `37b5be2bdc6d1b93320e0ce453d3612643c4c729ecf304bd021169421c409a58`, evidence digest `17ce1fb01a96fa5ddcc061f48af79c85a747824211e43460f2ab767cb0997f18`. Blender itself was correctly background/offline and returned 17; no static or rigged GLB was produced, so Godot correctly remained unexecuted. Blockers: `acceptance_bootstrap_exception`, `acceptance_glb_validation_failed`, `blender_acceptance_failed`, `process_nonzero`.

## Hardening after rejected local evidence

Source review found the acceptance fixture addressed a nonexistent Blender 5.2 Principled BSDF socket named `Metallic IOR Level`. Blender 5.2 exposes `Metallic` and `IOR Level` as distinct inputs; the fixture now sets the intended `Metallic` input. The rigged fixture is also hardened to use the explicit Blender 5.2 layered Action API (`Action` slot/layer/keyframe strip/channelbag/F-Curves) already accepted in R10.7, instead of relying on implicit pose keyframe insertion to infer the action structure.

A regression test now requires the Blender 5.2 `Metallic` socket contract, forbids the invalid combined socket name, and requires explicit layered Action construction. The manual checkpoint is inactive again until R0 + full Python Core + UI Smoke succeed on the new hardening head.

## Accepted candidate implementation

- `gltf_contracts.py`, `gltf_validator.py`, `gltf_bootstrap.py`, `gltf_godot_fixture.py`, `gltf_runner.py`;
- `r10-gltf-accept` registered through the existing Blender CLI surface;
- three R10.10 JSON Schemas;
- deterministic contracts/parser/security/evidence tests plus CLI tests;
- `R10_10_DESIGN.md` and this record.

## Acceptance ordering

1. Preserve every rejected local evidence file and failure workdir; never reclassify a FAIL as PASS.
2. Harden only the demonstrated runtime incompatibility without relaxing policy.
3. Freeze the new hardening candidate and run R0 + full Python Core + UI Smoke on its exact head.
4. Only if all three succeed does the REQUIRED local checkpoint become active again on that new SHA.
5. Run exactly one `python -m kodepoia.cli r10-gltf-accept ...` from that exact SHA with legitimate local Blender 5.2.x and Godot 4.7.x.
6. Return canonical evidence, console summary, evidence SHA-256/bytes and runtime versions.
7. Review evidence; only a valid clean PASS can be bound, re-gated, merged and normalized.
8. Do not begin R10.11 before that normalization merge.

## Manual success contract

The local evidence must have `schema=kodepoia.r10.gltf_local_acceptance`, `version=1`, the exact documented source SHA, `status=pass`, `blockers=[]`, a valid canonical `evidence_digest`, Blender 5.2.x with `background=true` and `online_access=false`, Godot 4.7 compatibility, Godot import return code 0, semantic smoke return code 0 with `KODEPOIA_R10_10_GODOT_PASS`, and non-empty SHA-256-bound `static.glb` + `rigged.glb` artifacts.

## Manual safety rules

Do not install add-ons/plugins/assets, enable Blender autoexec/online/user preferences, convert through FBX/ESCN, edit bundled fixtures, delete failed evidence before review, or relax sandbox/import/glTF rules after a failure. If a runtime path is unavailable, stop and report it instead of substituting another version or download route.
