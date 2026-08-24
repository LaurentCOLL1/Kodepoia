# R10.7 — Animation actions/NLA + governed retargeting

## Status

Hosted implementation candidate. Frozen manual state: **CONDITIONAL**.

## Contract model

R10.7 introduces versioned, structured animation/retarget contracts rather than exposing Blender operators, drivers, scripts or fuzzy bone matching.

- `RigSemanticProfile` binds a governed rig/armature identity, exact input `.blend` SHA-256 and explicit semantic-to-actual bone names.
- `AnimationClip` binds clip identity independently of Blender Action display names, FPS, frame range, loop policy, root-motion policy and finite ordered keyframes.
- channels are limited to bone `location`, `rotation_quaternion` and `scale`; quaternion values are normalized by the contract.
- `BoneMapping` is explicit and injective source→target. Unknown/duplicate/ambiguous mappings fail before Blender launch.
- `RetargetRecipe` binds source and target profiles, clip, mappings, required target bones, translation scale and key budget to one canonical digest.

No LLM/fuzzy name match is authoritative. Optional unmapped deform bones are reported as WARN facts; required target bones must be mapped or the recipe is rejected.

## Frozen coordinate and rest-pose policy

R10 v1 inherits the accepted R10.3 coordinate basis: meters, forward `-Z`, up `Y`. Therefore R10.7 does not expose arbitrary axis conversion matrices. Translation normalization is one explicit positive `translation_scale`.

The real Blender bootstrap resolves both armatures by `kodepoia_id`, validates semantic bone IDs/names and measures every mapped rest segment. R10.7 v1 accepts a mapped pair only when:

- maximum rest-direction difference is <= 30 degrees;
- scaled rest-length relative error is <= 0.50.

These are objective compatibility gates, not artistic similarity claims.

## Action, sampling and NLA policy

R10.7 v1 uses **`explicit_keys_only`**. It does not silently bake constraints or drivers. If target pose constraints or animation drivers exist, execution fails closed; a future explicit bake policy would require a later governed change.

The bootstrap:

1. opens the immutable staged rigged `.blend`;
2. verifies source/target semantic profiles and rest compatibility measurements;
3. verifies that the target has no existing active Action/NLA stack, constraints or drivers;
4. encodes requested FPS in scene render FPS/FPS-base;
5. creates exactly one Kodepoia-owned Action with stable clip/recipe custom IDs;
6. inserts only allowlisted mapped transforms;
7. applies explicit root-motion KEEP/ZERO policy;
8. creates exactly one NLA track and one Action strip;
9. clears the active Action while retaining the governed NLA Action identity;
10. saves only `animation_output.blend` in staging and emits machine-readable measurements.

The runner rehashes the staged input, checks recipe/result identity, evaluates the report, verifies output SHA-256/bytes and returns parent→derived lineage. Source clips/rigs remain immutable.

## Quality facts and gates

The report records:

- mapped count, missing required bones and explicit unmapped deform lists;
- maximum rest direction/length incompatibility;
- sampling policy, constraint and driver counts;
- FPS, frame boundaries, duration, loop and key count;
- NLA track/strip count and bound Action identity;
- root-motion translation delta;
- deterministic report digest and blocker list.

A report is `PASS`, `WARN` or `BLOCK`. WARN is reserved for explicit optional unmapped deform bones. Required mappings, rest compatibility, sampling, key budget, frame/FPS/duration, NLA/export-readiness and root-motion rules BLOCK on failure.

## Security boundary

The Blender bootstrap is Kodepoia-owned static code. It has no network/subprocess import, no `exec`/`eval`, no arbitrary driver creation, no Text-block execution, no script operator and no arbitrary Action/NLA/operator surface supplied by a model. Execution remains under accepted `BlenderRunner` / `ProcessSandbox` / KillSwitch / offline / autoexec-disabled controls.

## Upstream Blender 5.2 evidence

Blender 5.2 documents Action manual frame ranges and cyclic intent, `Action.fcurve_ensure_for_datablock`, NLA Action strips, action frame ranges and `use_sync_length`. These docs establish API compatibility only; they do not replace Kodepoia exact-head and, if triggered, real-runtime acceptance.

## CONDITIONAL boundary

Hosted tests can authoritatively validate contracts, security, manifests, lineage and deterministic report rules, but do not execute Blender 5.2's current layered Action/ActionSlot + NLA runtime path. After hosted exact-head gates, evaluate whether accepted R10.2/R10.6 runtime evidence is sufficient. If actual Action/F-Curve/NLA execution remains uncertified, mark the condition **TRIGGERED**, stop before R10.8 and run `scripts/r10_7_local_acceptance.py` on the immutable candidate.

The local runner is bounded and synthetic: it creates two simple governed meshes, sequentially rigs them using accepted R10.6 code, retargets a small clip and emits canonical runtime/geometry/source-rig/target-rig/animation evidence. Video-only evidence is never sufficient.
