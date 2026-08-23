# R10.6 — Acceptance record

Status: **LOCAL BLENDER EVIDENCE ACCEPTED; FINAL DOCUMENTED HEAD PENDING GATES**  
Manual intervention: **CONDITIONAL TRIGGERED AND SATISFIED**

## Definition of Done

R10.6 requires exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke, deterministic rig-profile identity, hierarchy/deform-set validation, influence/tolerance budgets, malformed weight fixtures, explicit exported-deform set, staging lineage and a real Blender 5.2 deformation fixture because the frozen CONDITIONAL boundary was triggered.

## Original hosted implementation evidence

Immutable implementation head `4fb687b232eb7ed113991e81038284cb4a806554` passed:

- R0 Repository Guard #1247 / `32667542625` — SUCCESS.
- Python Core #1221 / `32667542562` — SUCCESS; Ubuntu **799 passed / 7 skipped / 46 warnings**; R7/R8/R9 integrated acceptance PASS.
- KodeStudio UI Smoke #1188 / `32667542603` — SUCCESS.

The hosted tests proved the frozen four-influence default and explicit higher-count opt-in; hierarchy/connected-rest invariants; control-only weight rejection; deterministic tiny-weight pruning/normalization; create vs imported-existing strategy constraints; PASS/WARN/BLOCK validation for zero weights, bad sums, over-budget influences, control references, modifier/parent binding and deformation-probe protocol; immutable parent/derived SHA lineage; protocol tamper rejection; and the bounded offline local-acceptance path.

## First local attempt — rejected evidence, rig result retained as diagnostic

The first bounded local run against `4fb687b232eb7ed113991e81038284cb4a806554` produced top-level `status=pass`, geometry PASS and rig PASS, but all runtime identity fields were serialized as null. Its uploaded evidence was therefore rejected as final evidence even though the rig/deformation path itself succeeded.

Root cause: `scripts/r10_6_local_acceptance.py` incorrectly read `probe["facts"]`, while `BlenderRunner.run_capability_probe()` exposes runtime identity under `runtime` and execution facts under `probe`. The old schema also required only an object at `runtime`, so it failed to reject null identity fields.

## Collector hardening

Hardening head `3b1263b92d5a1a8f50e03c188a1f2fa6d4bc2880`:

- maps accepted capability-manifest `runtime.version` / `runtime.platform` and `probe.background` / `probe.online_access` correctly;
- fails closed unless Blender is 5.2.x, platform is present, background mode is true and online access is false;
- strengthens `r10-rig-local-acceptance-v1.schema.json` so null runtime identity is invalid;
- adds regression tests for successful mapping and missing-runtime rejection.

Exact-head hardening gates:

- R0 Repository Guard #1249 / `32668952047` — SUCCESS.
- Python Core #1223 / `32668952036` — SUCCESS; Ubuntu **802 passed / 7 skipped / 46 warnings**; R7/R8/R9 integrated acceptance PASS.
- KodeStudio UI Smoke #1190 / `32668952071` — SUCCESS.

## Accepted corrected local Blender 5.2 evidence

Canonical evidence file: `docs/roadmap/R10_6_LOCAL_ACCEPTANCE.json`.

The corrected bounded local run was executed against exact source SHA `3b1263b92d5a1a8f50e03c188a1f2fa6d4bc2880` and is accepted with:

- canonical file bytes: **829**;
- canonical file SHA-256: `06153ac976c4568f6b555365e658e725a67898ddc1ecabf49e95e66e02f0fb4a`;
- internal `evidence_digest`: `fa62fdddcab850857d0520708c3e0fad7b27471730dc106653bc0513e65967a3`, independently recomputed from the canonical payload excluding the digest field;
- `status=pass`, `blockers=[]`;
- runtime: Blender `5.2.0`, platform `windows`, `background=true`, `online_access=false`;
- geometry fixture `status=pass`, recipe `r10.6.local.body`, source blend SHA-256 `98959b098a3a6b8a907b74d9e5ba76c52c8e5fb2b2ed4bb890c8efcced1bb22e`;
- rig `status=pass`, rig ID `r10.6.local.rig`;
- rig profile digest `656129c72f44e7f3fae4f654469184e8cec1b6c4b97dc81ca143c3a1fc17cd0c`;
- rig report digest `7a7770e313aff76db3f1a36bb65003047eec7521b4454d3f6896ff0efdc87452`;
- derived `rig_output.blend` **91,424 bytes**, SHA-256 `1f64a4b951bddddb5f5384c90e178b521ead2df35feb7ea4dc22e41d43b70f8b`.

The local script can return PASS only after the rig report contains a `deformation_probe` rule in state `PASS`; otherwise it appends `deformation_probe_failed` and fails the acceptance. Therefore the accepted local evidence binds a real Blender Armature-modifier deformation result, not merely a schema-valid rig manifest. Manual weight painting was not used as acceptance evidence.

## Final documentation gate

The canonical evidence commit plus this acceptance update intentionally create a new final documented head. That exact head must pass R0 Repository Guard + full Python Core + KodeStudio UI Smoke before PR #141 merges. After merge, perform one continuity-only post-merge normalization and require the same exact-head gates. Only after that normalization merge is R10.6 **COMPLETE + NORMALIZED** and R10.7 authorized.
