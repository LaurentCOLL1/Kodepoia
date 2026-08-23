# R10.7 — Acceptance record

Status: **HOSTED GATES PENDING**  
Manual intervention: **CONDITIONAL — decide only after hosted exact-head gates**

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
- bounded Action/NLA organization and key budget;
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
- valid recipe/report/local-evidence schemas and bounded local acceptance script.

## CONDITIONAL decision

The frozen manual state is CONDITIONAL. Do not trigger local work merely because Blender exists. First require all hosted gates on one immutable implementation head.

If those gates pass but real Blender 5.2 Action/F-Curve/NLA runtime behavior is still not covered by prior accepted R10.2/R10.6 evidence, mark the condition **TRIGGERED**. In that case stop before R10.8 and execute the bounded `scripts/r10_7_local_acceptance.py` on the exact hosted candidate. Required machine-readable evidence must confirm Blender 5.2.x, background/offline mode, geometry/source-rig/target-rig PASS, animation PASS, rest/sampling/FPS/NLA/root-motion rules PASS, and verified animation derivative identity.

If the condition is not triggered, document why accepted evidence already authoritatively covers the runtime behavior. Missing evidence never becomes PASS.

## Merge ordering

After implementation acceptance (and local evidence if triggered), write the exact evidence here, rerun R0 + full Python Core + UI Smoke on the final documented head, merge with expected SHA, then perform exactly one continuity-only post-merge normalization with the same three gates. Only after that normalization merge is R10.7 COMPLETE + NORMALIZED and R10.8 authorized.
