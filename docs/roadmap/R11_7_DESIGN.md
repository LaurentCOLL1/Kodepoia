# R11.7 — Facial performance mapping + facial LOD + R10/R5 integration

## Scope

R11.7 maps accepted R11.6 viseme semantics onto previously accepted R10 facial target metadata and emits deterministic R5 animation intent. It does not modify topology, rigs, Blender files, Godot scenes or runtime resources.

## Authority boundaries

- R10 remains authoritative for facial target identity, type, source digest and permitted numeric range.
- R11.6 remains authoritative for `VisemeTimeline` identity and timing.
- R11.7 owns only semantic mappings, facial LOD policy, derived curve identity, QA and typed engine intent.
- R5 remains authoritative for eventual Godot materialization/runtime execution.

Godot 4.7 has a dedicated `blend_shape` animation track for MeshInstance3D blend shapes. R11.7 therefore represents blend-shape and bone-property tracks as typed intent only; it does not emit raw `.tscn`, resource paths, GDScript or arbitrary property strings.

## Contracts

`FacialTargetCatalog` is a strict adapter view over accepted R10 metadata. Every target has:

- stable target id;
- semantic id;
- kind (`blend_shape` or `bone`);
- finite minimum/maximum range;
- exact source digest;
- enclosing rig digest.

`FacialPerformanceProfile` binds one exact target-catalog digest and one exact viseme-set digest. A mapping is `(source_semantic, target_id, weight)`. Unknown targets, catalog digest drift and out-of-range weights fail closed unless the profile explicitly enables bounded clamping.

`FacialLODLevel` defines an allowlist of target ids plus a maximum key density. Required semantics such as mouth opening/closure must still resolve to included targets at every LOD that declares them.

## Curve generation

For each mapped viseme event, R11.7 generates neutral/peak/peak/neutral keys at the R11.6 influence and peak boundaries. Same-time keys are merged deterministically. LOD filtering occurs before curve output. Key decimation is deterministic and bounded by the LOD key-density policy.

Clamping is never silent: when explicitly enabled, clamped peak keys increment `clipped_key_count`; QA can block any clipping.

## R5 intent

`GodotFacialAnimationIntent` contains only identities and bounded facts: curve-set digest, target id/kind, typed track kind, key count and duration. It contains no script, scene/resource path, raw Godot property path or executable payload.

## QA

R11.7 QA checks:

- profile/catalog digest binding;
- missing targets;
- curve values outside R10 ranges;
- total key budget;
- clipping budget;
- non-empty curve requirement.

## Manual checkpoint

R11.7 manual intervention is **CONDITIONAL**. This implementation does not claim real R10/Godot facial playback behavior; all accepted behavior is contract/metadata/curve/intent logic reproduced in hosted CI using synthetic metadata. Therefore the conditional checkpoint is **NOT TRIGGERED**.

A future real render/import/playback claim inside R11.7 would invalidate that decision and require exact-head repository test assets plus machine-readable target/curve/import evidence before merge.
