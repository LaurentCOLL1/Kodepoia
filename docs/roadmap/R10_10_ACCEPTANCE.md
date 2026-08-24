# R10.10 — Acceptance record

Status: **LOCAL REQUIRED ACCEPTED; FINAL EXACT-HEAD GATES SUCCESS**  
Frozen manual intervention: **REQUIRED — SATISFIED**

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

## Hardening after rejected local evidence — HOSTED ACCEPTED

Hardening candidate: `85e2db277ce1cb467aeb9b056700150bc1d67fa7`.

The acceptance fixture now uses Blender 5.2's actual Principled BSDF `Metallic` input instead of the invalid combined name `Metallic IOR Level`. The rigged fixture uses the explicit Blender 5.2 layered Action API (`Action` slot/layer/keyframe strip/channelbag/F-Curves) rather than implicit pose keyframe insertion.

Exact-head hosted gates:
- R0 Repository Guard #1302 / `32707671592`: **SUCCESS**;
- Python Core #1276 / `32707671595`: **SUCCESS**;
- KodeStudio UI Smoke #1243 / `32707671624`: **SUCCESS**.

Python Core Ubuntu: **853 passed / 7 skipped / 46 warnings**; R7/R8/R9 integrated acceptance PASS. Windows Python, KodeStudio smoke and both package builds SUCCESS.

## REQUIRED local acceptance — ACCEPTED

The second REQUIRED local run was executed from exact candidate `85e2db277ce1cb467aeb9b056700150bc1d67fa7` on Windows with Blender **5.2.0 LTS** and Godot **4.7.2.stable.steam.ed1daf0bf**. It returned exit code 0 with `status=pass`, `blockers=[]` and policy `r10.10-local-v1`.

Canonical evidence: `R10_10_LOCAL_ACCEPTANCE.json`.
- evidence file: **2843 bytes**, SHA-256 `da9680219dfd4e3a44683a547481b6584b9ef186ee364f27dfcfe2c0c5c29c9f`;
- canonical evidence digest: `1965ad088a721c9774ea536fe908bffa3f8b07a23ac135c22c339f0d778f6627`;
- Blender: background `true`, online access `false`, return code 0, no timeout/cancel/truncation;
- static GLB: **2832 bytes**, SHA-256 `19a8adfbc4c9ac098a676fbdf52143dc5e445b29228830eab67d271341758308`, glTF 2.0, 1 mesh, 1 material, no skin/animation/morph;
- rigged GLB: **6796 bytes**, SHA-256 `84e9f0a7c7638566962160d6b986073b37528d8bf944d8840c1b6f99f138175f`, glTF 2.0, 1 mesh, 1 material, 1 skin, 1 morph target and 1 animation;
- Blender round-trip preserves `KDP_StaticMaterial`, `KDP_RiggedMaterial`, bones `Root`/`Child`, shape key `Smile` and animation `Wave`;
- Godot executable SHA-256 `12310c74bdda7dcd43f28e971f33047dcecadd436b68169d61ce41009006df38`;
- Godot import return code 0 with no timeout/cancel; semantic smoke return code 0 with `pass_marker=true`.

The evidence digest and raw evidence SHA-256/size were independently recomputed before binding and matched exactly. The earlier FAIL remains preserved and rejected; it is not overwritten or reclassified.

## Final evidence-bound candidates — ACCEPTED

Evidence-bound head `867cae1d3534716ec2f617be64f67206700a252a`:
- R0 #1304 / `32708720158`: **SUCCESS**;
- Python #1278 / `32708720261`: **SUCCESS**;
- UI #1245 / `32708720153`: **SUCCESS**.

Final documentation head `ceff4d2896b5fa1b2f4996fe70682521eca9e1c3`:
- R0 #1305 / `32708920919`: **SUCCESS**;
- Python #1279 / `32708920926`: **SUCCESS**;
- UI #1246 / `32708920982`: **SUCCESS**.

Final frozen head `ea25f9d2327452165cd1c5fdb749240ba4f08ab8`:
- R0 #1306 / `32709108935`: **SUCCESS**;
- Python #1280 / `32709108919`: **SUCCESS**;
- UI #1247 / `32709109055`: **SUCCESS**.

Python Core preserves Ubuntu/Windows coverage, R7/R8/R9 integrated acceptance PASS, KodeStudio smoke and both package builds SUCCESS. No further branch writes are permitted before merge.

## Accepted candidate implementation

- `gltf_contracts.py`, `gltf_validator.py`, `gltf_bootstrap.py`, `gltf_godot_fixture.py`, `gltf_runner.py`;
- `r10-gltf-accept` registered through the existing Blender CLI surface;
- three R10.10 JSON Schemas;
- deterministic contracts/parser/security/evidence tests plus CLI tests;
- `R10_10_DESIGN.md`, rejected evidence, accepted local evidence and this record.

## Final acceptance ordering

1. Preserve both the rejected and accepted local evidence records permanently.
2. Merge PR #149 only from exact accepted head `ea25f9d2327452165cd1c5fdb749240ba4f08ab8`.
3. Create a continuity-only post-merge normalization branch from the resulting `main` merge commit.
4. Run fresh R0 + Python + UI on the normalization head and merge only if all three are SUCCESS.
5. Only after that merge is R10.10 **COMPLETE + NORMALIZED** and R10.11 authorized.

## Manual safety rules

Do not install add-ons/plugins/assets, enable Blender autoexec/online/user preferences, convert through FBX/ESCN, edit bundled fixtures, delete failed evidence before review, or relax sandbox/import/glTF rules after a failure. The REQUIRED manual gate is satisfied; no further local retry is authorized for this candidate.
