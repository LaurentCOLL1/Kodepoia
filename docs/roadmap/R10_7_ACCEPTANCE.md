# R10.7 — Acceptance record

Status: **LOCAL BLENDER 5.2 GATE SATISFIED; FINAL DOCUMENTED HEAD PENDING GATES**  
Manual intervention: **CONDITIONAL TRIGGERED → SATISFIED**

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
- static offline bootstrap with no arbitrary driver/script/network/dynamic-code surface;
- real Blender 5.2 local evidence for the Action/F-Curve/NLA runtime seam because the frozen CONDITIONAL was triggered.

## Hosted fixture expectations

Tests cover stable semantic-rig identity, quaternion normalization, ordered/in-range keys, explicit injective mappings, required target coverage, key budgets, rest-pose compatibility, constraint/driver blocking, NLA/export-readiness, root-motion policy, WARN-only optional unmapped deform bones, source immutability/lineage, manifest tamper rejection, static offline bootstrap inspection, layered Action construction, local-evidence schemas, surfaced process blockers, and the exact Blender NLA integer-start creation contract.

## Candidate 0a49d3ad — hosted PASS, local FAIL

Source SHA `0a49d3ad15c3e263652be5776f28f959562feaef` passed R0 #1257 / `32670538729`, Python Core #1231 / `32670538733` with Ubuntu `813 passed / 7 skipped / 46 warnings` and R7/R8/R9 PASS, and UI #1198 / `32670538746`.

Its required local Blender 5.2.0 execution returned exit 17. Canonical rejected evidence:

`docs/roadmap/R10_7_LOCAL_ACCEPTANCE_REJECTED_0a49d3ad.json`

- bytes `897`;
- SHA-256 `59ce89901c9df64c9ba54b353323acad47884e4c3c20fa5328f3f51b2a93992b`;
- evidence digest `604e4d26f7c2fa3c4266eda4055e462ffafd3ef63baab013cefe2cde1c1368ea`;
- Blender 5.2.0 / Windows / background=true / online_access=false;
- geometry PASS, source rig PASS, target rig PASS;
- animation BLOCK, no animation artifact/report.

This first local evidence is permanently **REJECTED**, never partial PASS.

### First corrective action

The bootstrap was changed from implicit `PoseBone.keyframe_insert()` Action inference to Blender 5.2's explicit layered path: Action → Action Slot → Layer → KEYFRAME Action strip → Channelbag/F-Curves, with explicit `animation_data.action_slot` and `NlaStrip.action_slot`. Failure evidence was hardened to surface the animation manifest blockers and process state.

## Candidate da56b8a2 — hosted PASS, second local FAIL

Corrected source SHA `da56b8a20fc7cb5dfa038051305f07f80dafa4d3` passed:

- R0 Repository Guard #1263 / `32683124571`: SUCCESS;
- Python Core #1237 / `32683124604`: SUCCESS; Ubuntu `813 passed / 7 skipped / 46 warnings`, R7/R8/R9 integrated acceptance PASS, Windows Python and Ubuntu/Windows package builds SUCCESS;
- KodeStudio UI Smoke #1204 / `32683124591`: SUCCESS.

The required real Blender 5.2.0 rerun again returned exit 17, but this time the hardened evidence identified the exact runtime exception:

`NlaStrips.new(): error with argument 2, "start" - Function.start expected an int type, not float`

Canonical rejected evidence:

`docs/roadmap/R10_7_LOCAL_ACCEPTANCE_REJECTED_da56b8a2.json`

Identity independently checked from the submitted file:

- bytes `1251`;
- SHA-256 `539581f9cbce75f8876ecdf7451482974b8e50c7571e8375761b2d3ab9957cae`;
- evidence digest `a59fd9032331745507f24f5af546b24e763ef7ffccc45a3761bd28605fffbe99`;
- source SHA `da56b8a20fc7cb5dfa038051305f07f80dafa4d3`;
- Blender 5.2.0 / Windows / background=true / online_access=false;
- geometry PASS, source rig PASS, target rig PASS;
- animation BLOCK;
- process return code 17, not timed out/cancelled/truncated;
- no animation artifact/report;
- internal blockers include the exact `NlaStrips.new` integer-type error plus `animation_execution_failed` and `process_nonzero`.

This second evidence is also permanently **REJECTED**, never partial PASS.

## Second corrective action — Blender NLA start type

Blender's `NlaStrips.new(name, start, action)` creation API requires an integer start frame, while the resulting NLA strip exposes a floating-point `frame_start` property. The governed bootstrap now:

1. keeps the requested clip start as `nla_start = float(...)`;
2. derives only the creation argument as `nla_creation_start = int(math.floor(nla_start))`;
3. calls `NlaStrips.new(..., nla_creation_start, action)`;
4. immediately restores the exact requested value with `strip.frame_start = nla_start`;
5. retains explicit Action Slot binding and the existing action-frame range, repeat and sync-length controls.

A dedicated hosted regression test asserts that no float is passed to `NlaStrips.new` and that the exact float start is preserved after creation. No animation policy, mapping rule, security boundary or acceptance threshold was weakened.

## Accepted hosted implementation candidate

Immutable local candidate:

`21510878f49815b7bb5551da9672a349c3fd817f`

Exact-head hosted gates:

- R0 Repository Guard #1267 / `32683968797`: **SUCCESS**;
- Python Core #1241 / `32683968785`: **SUCCESS**; Ubuntu **814 passed / 7 skipped / 46 warnings**, R7/R8/R9 integrated acceptance PASS, Windows Python and Ubuntu/Windows package builds SUCCESS;
- KodeStudio UI Smoke #1208 / `32683968838`: **SUCCESS**.

## Accepted REQUIRED/CONDITIONAL local Blender evidence

The frozen CONDITIONAL was triggered because prior R10.2/R10.6 local evidence did not execute the new Action/F-Curve/NLA seam. The exact candidate `21510878f49815b7bb5551da9672a349c3fd817f` was executed locally on Windows with legitimate Blender 5.2.0 and produced canonical PASS evidence archived as:

`docs/roadmap/R10_7_LOCAL_ACCEPTANCE.json`

Identity independently verified from the submitted file:

- bytes: `1622`;
- SHA-256: `f2374feadf87ce9c0f3362969aa0f98314842c73f31c2a90b42c9e2ab107a8cf`;
- evidence digest: `3ef6f4b366a3179f36a20ed606fdf25708309ae350df2704176dfee5e3b1f0b7`;
- source SHA: `21510878f49815b7bb5551da9672a349c3fd817f`;
- runtime: Blender `5.2.0`, platform `windows`, background `true`, online access `false`;
- top-level status `pass`, blockers `[]`;
- geometry PASS;
- source rig PASS;
- target rig PASS;
- animation PASS;
- animation process return code `0`, no timeout/cancel/truncation;
- animation output `animation_output.blend`, `92875` bytes, SHA-256 `b0c760d1126305ae618f851adab6cd472e94c99033340458cff32ec957138e0b`;
- recipe digest `a33af267311cdda320636b8aa90b9106e6398edb972e163c36cfd59df287759a`;
- report digest `17a5bc6018a79d846115b5c5a1d9cabafe80659cf4e7879189167c432e116ef5`;
- manifest blockers `[]`;
- all 20 reported acceptance rules PASS: `constraint_free_target`, `driver_free_target`, `duration`, `export_readiness`, `frame_end`, `frame_rate`, `frame_start`, `key_budget`, `loop_policy`, `mapping_ambiguity`, `mapping_coverage`, `nla_strip_count`, `nla_track_count`, `required_target_mapping`, `rest_direction_compatibility`, `rest_length_compatibility`, `root_motion_policy`, `sampling_policy`, `unmapped_source_deform`, `unmapped_target_deform`.

The canonical evidence digest was independently recomputed from canonical JSON excluding the `evidence_digest` field and matched exactly. The file SHA-256/byte size also matched the user's PowerShell output exactly.

Therefore the R10.7 manual state is **CONDITIONAL TRIGGERED → SATISFIED**.

## Final merge ordering

This acceptance update and canonical PASS evidence intentionally create a new final documented head. That exact head must now pass, without modification:

1. R0 Repository Guard;
2. full Python Core with R7/R8/R9 integrated acceptance still PASS;
3. KodeStudio UI Smoke.

If all three succeed, merge PR #143 with expected head SHA. Then perform exactly one continuity-only post-merge normalization, again requiring the same three exact-head gates. Only after that normalization merge is R10.7 **COMPLETE + NORMALIZED** and R10.8 authorized.
