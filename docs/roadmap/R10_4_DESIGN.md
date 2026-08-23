# R10.4 — UV + PBR material pipeline + governed texture lineage

## Status

Implementation candidate. Manual state: **CONDITIONAL, NOT TRIGGERED by this design**.

## Upstream compatibility contract

Blender 5.2 documentation defines glTF's core metallic/roughness PBR channels as Base Color, Metallic, Roughness, baked AO, tangent-space Normal Map and Emissive. The exporter expects normal maps through an Image Texture → Normal Map → Principled BSDF chain and the normal image must be treated as Non-Color data. Blender's color-management API exposes `ColorManagedInputColorspaceSettings.is_data` specifically for non-color data such as normal/displacement maps.

R10.4 therefore uses one fixed Principled BSDF template and only five texture roles: base color, metallic, roughness, tangent-space normal and emissive. Base-color/emissive textures are color data; metallic/roughness/normal textures are data. AO packing/export behavior is intentionally deferred to R10.10's glTF contract rather than inventing a Blender-only graph with ambiguous runtime semantics.

## UV policy

Recipes can keep a declared existing UV map or generate one through bounded Smart Project / Angle Based / Conformal policies. Operators run only after explicit object activation, Edit mode setup and full face selection. Margins and smart-project angle limits are bounded. Blender 5.2 documents these unwrap policies and packing margins; generated UV evidence records loop counts and coordinate bounds.

## Lineage boundary

Recipe data contains **no filesystem paths**. It binds an input `.blend` by SHA-256 and each texture by stable source ID + role + SHA-256 + UV map name. The host runner accepts paths only through trusted bindings under separately configured input/texture roots, verifies confinement, extension and digest, then copies immutable bytes into the staging workspace. Blender sees only staging-local filenames.

The runner never overwrites the R10.3 source `.blend` or a source texture. It writes a new `pbr_output.blend` and re-hashes it before returning a manifest. No R8 Vault promotion happens here.

## Material graph

Each governed material clears the default node graph and creates exactly:

- Material Output;
- Principled BSDF;
- one UV Map + Image Texture pair per declared texture;
- one tangent-space Normal Map node only for the normal role.

No arbitrary node type, node group, shader source, driver, add-on, URL, procedural code or image path is accepted from recipe data.

## Conditional manual gate decision

R10.4's frozen manual state is CONDITIONAL only when a planned bake path or backend-specific behavior cannot be authoritatively validated by hosted/accepted CPU fixtures. **This implementation does not implement or request baking at all.** The manifest fixes `bake.requested=false` and `bake.executed=false`, tests assert the bootstrap has no bake operator, and all material/UV semantics are structural/CPU-verifiable on top of the already accepted real Blender 5.2.0 R10.2 baseline. Therefore the conditional gate is **NOT TRIGGERED** unless exact-head tests expose a new backend-specific blocker.
