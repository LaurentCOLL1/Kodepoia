# R10.12 — Acceptance record

Status: **IMPLEMENTATION HEAD ACCEPTED — FINAL INTEGRATED EVIDENCE PENDING**  
Frozen manual intervention: **CONDITIONAL — NOT TRIGGERED**

## Definition of Done

R10.12 is accepted only after the anti-circular sequence frozen in `R10_PLAN.md` completes:

1. one immutable implementation head contains the adversarial suite, integrated acceptance model/verifier, JSON schema, design and this acceptance contract;
2. that exact implementation head passes R0 Repository Guard + full Python Core + KodeStudio UI Smoke, with R7/R8/R9 integrated acceptance still PASS;
3. the implementation head is then bound as R10.12 `source_sha`/`accepted_head` in the canonical `R10_INTEGRATED_ACCEPTANCE.json`, alongside the immutable R10.1–R10.11 acceptance blobs, normalized continuity and reviewed REQUIRED local R10.2/R10.10 evidence;
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
- acceptance-document, normalized-continuity, required-local-evidence and prior-integrated-report substitution;
- runtime-policy and semantic report digest tampering.

Full Python Core additionally re-runs all accepted R10.1–R10.11 suites, including malformed mesh/UV/material, rig/weight, animation/retarget, LOD/preservation, process timeout/crash/cancellation/output limits, R8 lineage and GLB/Godot acceptance contracts.

## Integrated verifier requirements

The report verifier must bind and independently re-read:

- `docs/roadmap/R10_1_ACCEPTANCE.md` through `R10_12_ACCEPTANCE.md` in strict order;
- normalized `docs/continuity/KODEPOIA_CONTINUITY.md`, so exact-head facts intentionally stored in PR/continuity metadata remain verifiable without retroactively rewriting prior acceptance documents;
- `docs/roadmap/R10_2_LOCAL_ACCEPTANCE.json` and `R10_10_LOCAL_ACCEPTANCE.json` by SHA-256 and byte length;
- `docs/roadmap/R7_INTEGRATED_ACCEPTANCE.json`, `R8_INTEGRATED_ACCEPTANCE.json` and `R9_INTEGRATED_ACCEPTANCE.json` by repository identity and their own semantic evidence digests;
- Blender 5.2.x with autoexec disabled/offline mode and Godot 4.7 as the frozen runtime policy.

Each accepted subdivision head must appear in either its immutable acceptance document or the immutable normalized continuity. A passing report cannot contain explicit or derived blockers. Unsatisfied REQUIRED/triggered CONDITIONAL manual state, stale/missing evidence, changed evidence bytes, non-PASS local evidence, changed runtime baseline or non-PASS prior integrated evidence must reject the report.

## Implementation-candidate history

Historical implementation candidate `314f73a787df138a1525ddb9d6c894b95022f973`:

- R0 Repository Guard #1328 / `32716816926`: repository validation succeeded;
- Python Core #1302 / `32716816964`: **REJECTED** because one new test incorrectly compared the current repository bytes of `R10_2_LOCAL_ACCEPTANCE.json` with the historical transfer SHA-256 recorded during R10.2; Ubuntu otherwise reported **905 passed / 8 skipped / 46 warnings**, and R7/R8/R9 integrated acceptance PASS;
- KodeStudio UI Smoke #1269 / `32716817062` was not used to accept this rejected head.

The corrective change does not weaken evidence verification. It distinguishes the immutable SHA-256/byte identity of the evidence file currently present in the repository from its historically recorded transfer digest, while preserving the original historical digest in R10.2 documentation/continuity.

Accepted immutable implementation head: **`2f1db59c8ffa8da28d7afd994e8203a126d4f478`**.

Exact-head gates on `2f1db59c8ffa8da28d7afd994e8203a126d4f478`:

- R0 Repository Guard #1329 / `32716992444`: **SUCCESS**;
- Python Core #1303 / `32716992453`: **SUCCESS**; Ubuntu **906 passed / 8 skipped / 46 warnings**; Windows Python SUCCESS; KodeStudio smoke SUCCESS; Ubuntu/Windows package builds SUCCESS; R7/R8/R9 integrated acceptance PASS;
- KodeStudio UI Smoke #1270 / `32716992458`: **SUCCESS**.

This immutable implementation head is the only R10.12 `source_sha`/`accepted_head` authorized for the canonical integrated report.

## Manual-state evaluation

Final implementation evaluation: **CONDITIONAL NOT TRIGGERED**.

R10.12 adds deterministic adversarial validation and evidence binding only. It does not change Blender job generation, Blender execution flags, Blender 5.2 semantics, GLB/glTF export semantics, or Godot 4.7 import/smoke behavior. The reviewed REQUIRED local evidence from R10.2 and R10.10 remains the authoritative hardware/runtime proof and is revalidated by the integrated verifier.

The rejected candidate exposed only a repository-evidence identity assertion error and no new authoritative Blender/Godot runtime seam. No new manual Blender/Godot intervention is required.

## Final integrated evidence

`R10_INTEGRATED_ACCEPTANCE.json` must now be generated from the immutable implementation head above plus immutable repository evidence. No placeholder SHA, synthetic PASS, or future final-documentation head may replace `2f1db59c8ffa8da28d7afd994e8203a126d4f478` as the R10.12 accepted implementation head.
