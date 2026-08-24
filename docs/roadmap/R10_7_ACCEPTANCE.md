# R10.7 — Acceptance record

Status: **CORRECTED HOSTED GATES PENDING**  
Manual intervention: **TRIGGERED — first local attempt rejected; corrected candidate must pass hosted gates before re-test**

## Definition of Done

R10.7 requires one exact head with:

- R0 Repository Guard SUCCESS;
- full Python Core SUCCESS on Ubuntu/Windows with R7/R8/R9 integrated acceptance still PASS;
- KodeStudio UI Smoke SUCCESS;
- canonical animation/retarget recipe identity;
- deterministic frame/FPS/duration/loop/root-motion policy;
- explicit injective semantic mapping with required target coverage and no fuzzy authority;
- objective rest-pose compatibility measurements;
- explicit `explicit_keys_only` sampling policy and fail-closed constraint/driver behavior;
- bounded Blender 5.2 layered Action/ActionSlot/F-Curve/NLA organization and key budget;
- immutable parent `.blend`, verified derived `.blend` and parent→derived SHA lineage;
- static offline bootstrap with no arbitrary driver/script/network/dynamic-code surface.

## Hosted fixture expectations

Tests must cover:

- stable `RigSemanticProfile` identity;
- quaternion normalization and invalid frame/key rejection;
- duplicate/ambiguous/unknown mapping rejection;
- required target mapping and key budget enforcement;
- PASS report for the canonical retarget fixture;
- BLOCK for incompatible rest pose, unsupported constraints/drivers, invalid NLA/export readiness and root-motion failure;
- WARN-only semantics for optional unmapped deform bones;
- runner result-digest tamper rejection and source immutability;
- static bootstrap import/surface inspection;
- explicit Blender 5.2 Action slot/layer/keyframe-strip/channelbag/F-Curve construction;
- valid recipe/report/local-evidence schemas and bounded local acceptance script with surfaced manifest blockers/process state.

## Hosted candidate 0a49d3ad — PASS, then rejected locally

Exact implementation source SHA:

`0a49d3ad15c3e263652be5776f28f959562feaef`

Hosted gates:

- R0 Repository Guard #1257 / `32670538729`: SUCCESS;
- Python Core #1231 / `32670538733`: SUCCESS; Ubuntu `813 passed, 7 skipped, 46 warnings`, R7/R8/R9 integrated acceptance PASS; Windows Python and Ubuntu/Windows package builds SUCCESS;
- KodeStudio UI Smoke #1198 / `32670538746`: SUCCESS.

The frozen CONDITIONAL decision was **TRIGGERED** because prior R10.2/R10.6 evidence did not execute the new Blender Action/F-Curve/NLA seam.

### Rejected local evidence

The exact local execution on Windows / Blender 5.2.0 returned exit code 17 and is permanently archived as:

`docs/roadmap/R10_7_LOCAL_ACCEPTANCE_REJECTED_0a49d3ad.json`

Identity supplied and independently checked from the submitted file:

- bytes: `897`;
- SHA-256: `59ce89901c9df64c9ba54b353323acad47884e4c3c20fa5328f3f51b2a93992b`;
- evidence digest: `604e4d26f7c2fa3c4266eda4055e462ffafd3ef63baab013cefe2cde1c1368ea`;
- source SHA: `0a49d3ad15c3e263652be5776f28f959562feaef`;
- runtime: Blender `5.2.0`, Windows, background `true`, online access `false`;
- geometry PASS;
- source rig PASS;
- target rig PASS;
- animation BLOCK;
- top-level blockers: `animation_retarget_failed`, `animation_rules_incomplete`;
- no animation artifact and no animation report digest were produced.

This evidence is **REJECTED**, not a partial PASS. It proves the failure is isolated to the animation runtime seam while the preceding governed geometry and rig fixture chain succeeds.

## Corrective action after rejected local evidence

The rejected bootstrap created an empty Action, assigned it directly to target `AnimData`, and then relied on `PoseBone.keyframe_insert()` to infer Blender's layered animation structure. That assumption was not established by prior evidence.

The corrected bootstrap follows the Blender 5.2 layered API explicitly:

1. create the Kodepoia Action;
2. create exactly one Action Slot for the target armature object;
3. create one Action Layer;
4. create one `KEYFRAME` Action strip;
5. create/ensure the slot Channelbag;
6. create deterministic F-Curves for each mapped pose-bone channel and insert bounded keyframe points;
7. assign both `animation_data.action` and `animation_data.action_slot`;
8. create one NLA track/strip and explicitly bind `strip.action_slot`;
9. clear the active Action only after NLA binding;
10. verify Action+slot identity before saving the derived `.blend`.

The local acceptance output is also hardened to expose the underlying animation manifest blockers and process facts on any further failure. Failure payloads preserve recipe/input lineage whenever the job was readable, preventing an execution exception from being obscured by secondary digest mismatch noise.

## Corrected-candidate ordering

The correction must now satisfy, in order:

1. exact-head R0 Repository Guard;
2. exact-head full Python Core;
3. exact-head KodeStudio UI Smoke;
4. only after all three succeed, rerun `scripts/r10_7_local_acceptance.py` on that immutable corrected source SHA using Blender 5.2.x;
5. if local evidence is not PASS, stop again before R10.8 and preserve the new evidence unchanged;
6. if local evidence is PASS, bind it canonically in this acceptance record, rerun the three final gates on the final documented head, merge PR #143 with expected SHA, then perform exactly one continuity-only post-merge normalization with the same gates.

Only after the normalization merge is R10.7 **COMPLETE + NORMALIZED** and R10.8 authorized.
