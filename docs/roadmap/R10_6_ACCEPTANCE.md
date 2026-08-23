# R10.6 — Acceptance record

Status: **HOSTED IMPLEMENTATION ACCEPTED; FIRST LOCAL EVIDENCE REJECTED; COLLECTOR HARDENING IN PROGRESS**  
Manual intervention: **CONDITIONAL TRIGGERED — rerun required after hardening gates**

## Definition of Done

R10.6 requires exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke, deterministic rig-profile identity, hierarchy/deform-set validation, influence/tolerance budgets, malformed weight fixtures, explicit exported-deform set, staging lineage and a real Blender 5.2 deformation fixture when the frozen CONDITIONAL boundary is triggered.

## Hosted implementation evidence

Immutable implementation head `4fb687b232eb7ed113991e81038284cb4a806554` passed:

- R0 Repository Guard #1247 / `32667542625` — SUCCESS.
- Python Core #1221 / `32667542562` — SUCCESS; Ubuntu **799 passed / 7 skipped / 46 warnings**; R7/R8/R9 integrated acceptance PASS.
- KodeStudio UI Smoke #1188 / `32667542603` — SUCCESS.

The hosted tests prove the frozen four-influence default and explicit higher-count opt-in; hierarchy/connected-rest invariants; control-only weight rejection; deterministic tiny-weight pruning/normalization; create vs imported-existing strategy constraints; PASS/WARN/BLOCK validation for zero weights, bad sums, over-budget influences, control references, modifier/parent binding and deformation-probe protocol; immutable parent/derived SHA lineage; protocol tamper rejection; and the bounded offline local-acceptance path.

## First local attempt — rejected evidence, implementation result retained as diagnostic

The first bounded local run was executed against the immutable implementation head `4fb687b232eb7ed113991e81038284cb4a806554` using the user's local Blender executable. The uploaded evidence file is **820 bytes** with file SHA-256 `2f2fac99e933db667f1f7dad3118cdeebe736106cff19b4886f5909122af1f93` and internally consistent `evidence_digest=4ff18deab62020708d48e6fcb83090a717b83537270d65e0829843e5dfc5b94f`.

Useful diagnostic facts from that attempt:

- top-level `status=pass`, `blockers=[]`;
- geometry fixture `status=pass`, blend SHA-256 `46ac3bc526ac6d3a156c91902d2fd74b27d0338df086d57ba2eda0bf75c54ce7`;
- rig `status=pass`, profile digest `aa3a47b89c9d45f7d1e54bbdbc8fab76b998f862323846988c88bf983a48b266`;
- rig report digest `4d0120df9a368555b3163956ab7c863abf57564dcb92bb2f6dd0a555a874fc02`;
- derived `rig_output.blend` 91,424 bytes / SHA-256 `9d1174c5864bbdadc0ca586b42fe9efaa2d071901215e0049a7ea0b170ab9da3`.

This evidence is **not accepted as final local evidence** because all runtime identity fields were serialized as null. Root cause: `scripts/r10_6_local_acceptance.py` incorrectly read `probe["facts"]`, while the accepted `BlenderRunner.run_capability_probe()` manifest exposes runtime identity under `runtime` and probe facts under `probe`. The old JSON schema was also too weak because it required only an object at `runtime` and therefore did not reject null identity fields.

## Corrective hardening

The hardening candidate must:

1. map `runtime.version` -> `runtime.blender_version` and `runtime.platform` -> `runtime.platform`;
2. map `probe.background` and `probe.online_access` into the local evidence;
3. fail closed if the runtime is not Blender 5.2.x, platform is missing, background mode is not confirmed true, or offline mode is not confirmed false;
4. strengthen `r10-rig-local-acceptance-v1.schema.json` so null runtime evidence is invalid;
5. add regression tests for both successful mapping and missing-runtime rejection.

## Completion sequence

Freeze the collector-hardening head -> exact-head R0/Python/UI -> rerun `scripts/r10_6_local_acceptance.py` locally on **that new immutable head** -> review the new canonical evidence and require non-null Blender 5.2 runtime facts plus `status=pass`, no blockers and PASS deformation evidence -> commit/bind accepted local evidence -> rerun all three gates on the final documented head -> merge with expected SHA -> continuity-only normalization with exact-head gates -> merge normalization. Only then may R10.7 start.
