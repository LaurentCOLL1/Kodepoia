# R10.12 — Acceptance record

Status: **IMPLEMENTATION CANDIDATE PENDING EXACT-HEAD GATES**  
Frozen manual intervention: **CONDITIONAL**

## Definition of Done

R10.12 is accepted only after the anti-circular sequence frozen in `R10_PLAN.md` completes:

1. one immutable implementation head contains the adversarial suite, integrated acceptance model/verifier, JSON schema, design and this acceptance contract;
2. that exact implementation head passes R0 Repository Guard + full Python Core + KodeStudio UI Smoke, with R7/R8/R9 integrated acceptance still PASS;
3. the implementation head is then bound as R10.12 `source_sha`/`accepted_head` in the canonical `R10_INTEGRATED_ACCEPTANCE.json`, alongside the immutable R10.1–R10.11 acceptance blobs and reviewed REQUIRED local R10.2/R10.10 evidence;
4. the final documentation/evidence head passes fresh exact-head R0 + full Python Core + KodeStudio UI Smoke;
5. the canonical integrated report verifies as `status=pass`, `blockers=[]`;
6. implementation PR merges and exactly one final continuity-only normalization passes the same gates and merges.

R10 does not become COMPLETE + NORMALIZED, and R11 planning is not authorized, before step 6.

## Required adversarial properties

The dedicated R10.12 suite must fail closed for:

- raw Python/operator/executable/argv/path/environment/URL/script recipe injection;
- non-finite recipe parameters;
- Python/Blender environment injection;
- unexpected Blender command-line surfaces or staging-root escapes;
- remote/absolute/parent-traversal glTF external URIs;
- forged GLB length/chunk structure;
- schema/version drift;
- acceptance-document, required-local-evidence and prior-integrated-report substitution;
- runtime-policy and semantic report digest tampering.

Full Python Core additionally re-runs all accepted R10.1–R10.11 suites, including malformed mesh/UV/material, rig/weight, animation/retarget, LOD/preservation, process timeout/crash/cancellation/output limits, R8 lineage and GLB/Godot acceptance contracts.

## Integrated verifier requirements

The report verifier must bind and independently re-read:

- `docs/roadmap/R10_1_ACCEPTANCE.md` through `R10_12_ACCEPTANCE.md` in strict order;
- `docs/roadmap/R10_2_LOCAL_ACCEPTANCE.json` and `R10_10_LOCAL_ACCEPTANCE.json` by SHA-256 and byte length;
- `docs/roadmap/R7_INTEGRATED_ACCEPTANCE.json`, `R8_INTEGRATED_ACCEPTANCE.json` and `R9_INTEGRATED_ACCEPTANCE.json` by repository identity and their own semantic evidence digests;
- Blender 5.2.x with autoexec disabled/offline mode and Godot 4.7 as the frozen runtime policy.

A passing report cannot contain explicit or derived blockers. Unsatisfied REQUIRED/triggered CONDITIONAL manual state, stale/missing evidence, changed evidence bytes, non-PASS local evidence, changed runtime baseline or non-PASS prior integrated evidence must reject the report.

## Manual-state evaluation

Current evaluation: **CONDITIONAL NOT TRIGGERED**, subject to implementation-gate confirmation.

R10.12 adds deterministic adversarial validation and evidence binding only. It does not change Blender job generation, Blender execution flags, Blender 5.2 semantics, GLB/glTF export semantics, or Godot 4.7 import/smoke behavior. The reviewed REQUIRED local evidence from R10.2 and R10.10 remains the authoritative hardware/runtime proof and is revalidated by the integrated verifier.

If implementation work changes that fact or exposes an authoritative real-runtime seam not covered by those accepted local gates, this state immediately becomes TRIGGERED and work must stop for a new bounded local acceptance command.

## Candidate/final evidence

The immutable implementation SHA and its exact R0/Python/UI run IDs will be recorded here only after that candidate actually passes. `R10_INTEGRATED_ACCEPTANCE.json` will then be generated from that immutable implementation SHA. No placeholder SHA or synthetic PASS is permitted.
