# R10.4 — Acceptance record

Status: **IMPLEMENTATION ACCEPTED; FINAL DOCUMENTED HEAD PENDING GATES**  
Manual intervention: **CONDITIONAL NOT TRIGGERED**

## Rejected candidate retained for audit

Candidate `d4e8eddb7fb8dd158777fdd37668a737677f7f5b` was **REJECTED** because Python Core #1210 / `32665390336` failed one newly added static test. Production PBR code was not shown to use networking; the test incorrectly rejected the ordinary helper name `input_socket` because it searched for the raw substring `socket`. R0 #1236 was SUCCESS and prior R7/R8/R9 integrated acceptance stayed PASS. The gate was not weakened: the test was replaced by AST-level import inspection that blocks actual `socket`, `http`, `urllib`, `requests`, `ftplib` and `subprocess` imports while retaining explicit bans on `exec`, `eval`, bake and URL-open operator surfaces.

## Accepted immutable implementation head

`edc67ae12f8e15051b91af48d20a5bd2ef2a9629`

Exact-head implementation gates:

- R0 Repository Guard #1237 / `32665514493`: **SUCCESS**.
- Python Core #1211 / `32665514469`: **SUCCESS**.
- KodeStudio UI Smoke #1178 / `32665514503`: **SUCCESS**.

Python Core Ubuntu reported **778 passed / 7 skipped / 46 warnings** and explicitly retained R7, R8 and R9 integrated acceptance as PASS. Package builds on Ubuntu/Windows, Windows Python tests and the embedded Windows UI job also succeeded.

## Accepted behavior

- canonical UV/PBR recipe identity and schemas validate representative documents;
- bounded Smart Project / Angle Based / Conformal / KEEP UV policies are structured and object-ID based;
- material recipes expose only Base Color, Metallic, Roughness, tangent-space Normal and Emissive texture roles;
- Base Color and Emissive remain color data while Metallic, Roughness and Normal are explicitly non-color data;
- tangent-space normal maps use the fixed Image Texture → Normal Map → Principled BSDF path expected by Blender/glTF;
- recipe data carries no filesystem path: the host binds input `.blend` and texture source IDs beneath governed roots and requires exact SHA-256 lineage before immutable staging copies are made;
- original `.blend` and texture sources are never overwritten; only a new staging `pbr_output.blend` is produced and re-hashed;
- recipe/result digest or input-lineage mismatches do not become PASS;
- bootstrap AST contains no network/subprocess imports and the source contains no dynamic-code, bake or URL-open operator surface;
- no R8 Vault promotion occurs in R10.4.

## Upstream compatibility basis

Blender 5.2's glTF manual documents the metal/rough PBR channels and requires tangent-space normal maps to use an Image Texture set to Non-Color feeding a Normal Map node and then Principled BSDF. Blender's Python API documents `ColorManagedInputColorspaceSettings.is_data` for non-color data such as normal/displacement maps. These upstream references corroborate the structural contract; they do not replace Kodepoia exact-head acceptance.

## Manual decision

The frozen **CONDITIONAL** gate is **NOT TRIGGERED**. R10.4 implements and claims no bake path: every manifest fixes `bake.requested=false` and `bake.executed=false`, and the bootstrap is explicitly tested to contain no bake operator. The accepted R10.2 real Blender 5.2.0 local-runtime evidence remains the authoritative runtime baseline. No backend-specific behavior required by this subdivision remains unverified.

## Final documentation gate

This update changes acceptance documentation only after the immutable implementation head was accepted. The resulting final documented head must itself pass R0 Repository Guard + full Python Core + KodeStudio UI Smoke before PR #137 merges. After merge, one continuity-only post-merge normalization with the same exact-head gates remains required before R10.5 may begin.
