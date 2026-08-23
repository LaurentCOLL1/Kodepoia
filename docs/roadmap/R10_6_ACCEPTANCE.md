# R10.6 — Acceptance record

Status: **HOSTED IMPLEMENTATION ACCEPTED; LOCAL BLENDER 5.2 EVIDENCE REQUIRED**  
Manual intervention: **CONDITIONAL TRIGGERED**

## Definition of Done

R10.6 requires exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke, deterministic rig-profile identity, hierarchy/deform-set validation, influence/tolerance budgets, malformed weight fixtures, explicit exported-deform set, staging lineage and a real Blender 5.2 deformation fixture because the frozen CONDITIONAL boundary is now triggered.

## Immutable hosted implementation head

`4fb687b232eb7ed113991e81038284cb4a806554`

Exact-head hosted gates:

- R0 Repository Guard #1247 / run `32667542625`: **SUCCESS**.
- Python Core #1221 / run `32667542562`: **SUCCESS**. Ubuntu reported **799 passed / 7 skipped / 46 warnings**. R7 integrated acceptance: PASS. R8 integrated acceptance: PASS. R9 integrated acceptance: PASS. Package-build Ubuntu/Windows, Windows Python and embedded KodeStudio jobs are part of the successful workflow.
- KodeStudio UI Smoke #1188 / run `32667542603`: **SUCCESS**.

Hosted tests prove the default four-influence policy and explicit higher-count opt-in; parent-before-child/connected-rest invariants; control-only weight rejection; deterministic tiny-weight pruning/normalization; create vs imported-existing strategy constraints; PASS/WARN/BLOCK behavior for zero weights, bad sums, over-budget influences, control references, modifier/parent binding and deformation-probe protocol; immutable source + derived SHA lineage; protocol tamper rejection; static offline bootstrap without Blender auto-weight/paint/network/dynamic-code surface; valid schemas and bounded local-acceptance runner.

## CONDITIONAL decision — TRIGGERED

The implementation's required deformation probe evaluates the real Blender Armature modifier after applying a temporary deterministic pose. Hosted unit tests validate the contracts, protocol and validator but do not execute Blender 5.2 itself. The three hosted gates passed, so the frozen R10.6 condition is **TRIGGERED**.

Stop before R10.7. Run the bounded local acceptance against the immutable implementation candidate:

```powershell
python scripts/r10_6_local_acceptance.py `
  --source-sha 4fb687b232eb7ed113991e81038284cb4a806554 `
  --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --output docs\roadmap\R10_6_LOCAL_ACCEPTANCE.json
```

If Blender 5.2 is installed elsewhere, change only the `--blender` path to the actual `blender.exe`. Do not alter the `--source-sha`.

The generated evidence must report `status=pass`, `blockers=[]`, `source_sha=4fb687b232eb7ed113991e81038284cb4a806554`, an accepted Blender 5.2.x runtime, successful geometry fixture/rig manifest and a real deformation-probe PASS. Manual weight painting is forbidden as acceptance evidence.

## After local evidence

Review and bind the returned JSON to the immutable candidate; record its canonical SHA-256, byte count and authoritative runtime/deformation facts here; rerun R0 Repository Guard + full Python Core + KodeStudio UI Smoke on the final documented head; merge PR #141 with that exact expected SHA; perform one continuity-only post-merge normalization with the same three gates. Only then may R10.7 start.
