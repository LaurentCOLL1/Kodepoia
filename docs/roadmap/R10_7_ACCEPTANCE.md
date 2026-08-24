# R10.7 — Acceptance record

Status: **SECOND LOCAL ATTEMPT REJECTED; NLA INTEGER-START FIX HOSTED GATES PENDING**  
Manual intervention: **TRIGGERED — do not rerun locally until the new exact head passes hosted gates**

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
- real Blender 5.2 local evidence for the new Action/F-Curve/NLA runtime seam because the frozen CONDITIONAL is TRIGGERED.

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

## New-candidate ordering

The branch head containing the NLA integer-start fix, dedicated regression test, both permanently rejected local evidence files and this acceptance update must now satisfy, in order:

1. exact-head R0 Repository Guard;
2. exact-head full Python Core;
3. exact-head KodeStudio UI Smoke;
4. only after all three succeed, freeze that exact SHA as the next local candidate;
5. rerun `scripts/r10_7_local_acceptance.py` on that exact SHA using Blender 5.2.x;
6. if local evidence is not PASS, stop again before R10.8 and preserve it unchanged;
7. if local evidence is PASS, bind it canonically here, rerun the three final gates on the final documented head, merge PR #143 with expected SHA, then perform exactly one continuity-only post-merge normalization with the same gates.

Only after that normalization merge is R10.7 **COMPLETE + NORMALIZED** and R10.8 authorized.
