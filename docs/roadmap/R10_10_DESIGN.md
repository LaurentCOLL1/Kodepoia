# R10.10 — GLB/glTF export, Blender round-trip + Godot 4.7 acceptance

Status: **IMPLEMENTATION CANDIDATE**  
Frozen manual state: **REQUIRED**

## Objective

R10.10 creates the canonical real-time 3D interchange boundary. It exports only governed, already-QA-bound Blender assets to glTF 2.0, validates the resulting container/document, re-imports it in clean Blender state, and uses the existing R5 `GodotRuntime`/`ProcessSandbox` boundary to certify Godot 4.7 import semantics. GLB is the canonical single-file R8-promotable artifact; typed `GLTF_SEPARATE` remains a bounded multi-file mode and is not misrepresented as one self-contained R8 blob.

## Upstream compatibility facts

Official Blender 5.2 documentation exposes `bpy.ops.export_scene.gltf` controls for GLB/separate glTF, UVs, normals, tangents, materials, skins, deform bones, animation, morph targets and influence count. `bpy.ops.wm.open_mainfile(..., use_scripts=False)` permits staged `.blend` loading without trusting embedded scripts, while the accepted process template remains background/factory/autoexec-disabled/offline. Godot 4.7 imports glTF scenes and its CLI `--import` waits for resource import and exits; R5 already wraps this in a fixed headless `GodotRuntime` call.

## Contracts and execution

`GltfExportProfile` v1 binds exact R8 source asset/revision/content identity, a distinct output AssetId, static/skinned mode, container/scope, QA/evidence digests, export flags, deform-bone/influence policy, required UV/material/bone/shape-key/animation names, a finite standard-extension allowlist, output byte budget, metre units and Y-up. Unknown fields, unsupported extensions, source overwrite and contradictory semantic claims fail before Blender runs.

`GltfExportRunner` layers only on accepted `BlenderRunner`. It verifies the confined source hash, stages a fixed bootstrap, opens with `use_scripts=False`, resolves selected objects only by declared `kodepoia_id`, invokes a fixed glTF exporter policy, inventories bounded outputs, re-imports the primary artifact and records semantic facts. No compression add-on/gltfpack, arbitrary operator/Python, cameras/lights/extras, user settings or online behavior is exposed.

## Structural validation and round-trip

The validator checks GLB magic/version/length/chunk bounds, exactly one first JSON chunk, bounded UTF-8 JSON, `asset.version=2.0`, scene/node/mesh/material/skin/animation/accessor references, POSITION accessors, skin joints, animation channels, extensions and safe external URIs. Round-trip acceptance uses profile-aware semantic checks instead of naive vertex equality, because legitimate glTF export can triangulate or split vertices at discontinuities.

## R8 promotion

A clean GLB produces a deterministic READY derived `MODEL_3D` revision with `EXPORTABLE` reuse, `gltf_export` lineage to the exact source revision and provenance bound to the export evidence digest. No promotion is emitted with blockers. Separate glTF remains a verified multi-file artifact set and is not collapsed into a false single-file revision.

## REQUIRED local acceptance

The local runner builds two synthetic fixtures only inside isolated staging: a static mesh+UV+Principled material, and a rigged mesh+UV+material+two-bone skin+shape key+action. Real Blender 5.2 exports and re-imports both. Kodepoia validates both GLBs, creates a minimal isolated Godot project, reuses R5 `GodotRuntime.require_47()`, runs bounded headless import, then a fixed GDScript semantic scene requiring static mesh/material and rigged mesh/skeleton/bones/AnimationPlayer. A clean run requires the fixed `KODEPOIA_R10_10_GODOT_PASS` marker.

Canonical evidence records runtime versions/executable hashes, GLB hashes/sizes/facts, Blender round-trip facts, Godot import/smoke state and an evidence digest, without persisting personal executable paths or secrets.

## Security invariants

No network or subprocess library exists in Blender bootstrap code; no arbitrary Blender operator/Python/argv/env/URL/Godot script/importer option is supplied by a model; Blender remains under ProcessSandbox/KillSwitch and factory/background/offline/autoexec-disabled policy; Godot reuses accepted R5 runtime; work/output paths remain confined; failed work is preserved and rules are never weakened after failure. R10.11 is forbidden until reviewed REQUIRED evidence is merged and R10.10 is normalized.
