# R10.7 — Acceptance record

Status: **HOSTED IMPLEMENTATION ACCEPTED; LOCAL BLENDER 5.2 ACTION/NLA EVIDENCE REQUIRED**  
Manual intervention: **CONDITIONAL TRIGGERED**

## Definition of Done

R10.7 requires exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke; canonical animation/retarget recipe identity; deterministic frame/FPS/duration/loop/root-motion policy; explicit injective semantic mapping; objective rest-pose compatibility measurements; explicit `explicit_keys_only` sampling policy; bounded Action/NLA organization and key budget; immutable parent `.blend`, verified derivative and lineage; and, because the frozen condition is now triggered, a real Blender 5.2 Action/F-Curve/NLA execution fixture.

## Rejected hosted candidate

Candidate `3fd3c528fc827815b10b13e0d35e591274c7b804` was **REJECTED** even though R0 #1256 and UI #1197 succeeded. Python Core #1230 failed on both Ubuntu and Windows because one new test fixture intended to exercise an out-of-range key changed the first key frame from `1` to `11`, yielding `[11,10]`. The contract correctly rejected the earlier invariant `keyframes must be strictly ordered and unique by frame`, so the test's expected `outside clip frame range` message was unreachable.

The fix changed only the fixture: the second frame is changed from `10` to `11`, preserving `[1,11]` and reaching the intended range gate. No production contract, security boundary or acceptance criterion was weakened.

## Accepted hosted implementation head

Immutable hosted implementation candidate:

`0a49d3ad15c3e263652be5776f28f959562feaef`

Exact-head gates:

- R0 Repository Guard #1257 / run `32670538729`: **SUCCESS**.
- Python Core #1231 / run `32670538733`: **SUCCESS**. Ubuntu reported **813 passed / 7 skipped / 46 warnings**; R7 integrated acceptance PASS, R8 integrated acceptance PASS and R9 integrated acceptance PASS; Windows Python, Ubuntu/Windows package builds and embedded KodeStudio Windows all succeeded.
- KodeStudio UI Smoke #1198 / run `32670538746`: **SUCCESS**.

Hosted tests cover stable semantic-rig identity; quaternion normalization; ordered/in-range key validation; explicit injective mappings; required target coverage; key budgets; rest-pose direction/length compatibility; `explicit_keys_only` policy; constraint/driver blocking; NLA/export-readiness rules; root-motion rules; WARN-only optional unmapped deform semantics; source immutability/lineage; manifest tamper rejection; static offline bootstrap inspection; and recipe/report/local-evidence schemas.

## CONDITIONAL decision — TRIGGERED

R10.2 certified a real Blender 5.2 headless runtime and glTF/bmesh capability. R10.6 certified real Blender 5.2 armature deformation. Neither accepted local gate executed R10.7's new runtime semantics: creation of an Action, pose-bone key insertion/F-Curves, transfer into an NLA Action strip, clearing of the active Action while retaining the governed NLA identity, and measurement of the resulting animation derivative.

Hosted CI uses deterministic fake-runner fixtures for those seams; it does not execute Blender 5.2 itself. Therefore prior local evidence cannot authoritatively certify the new Action/F-Curve/NLA runtime behavior. The frozen **CONDITIONAL is TRIGGERED**.

Stop before R10.8 and run the bounded local fixture on exact hosted candidate `0a49d3ad15c3e263652be5776f28f959562feaef`:

```powershell
git fetch origin
git checkout 0a49d3ad15c3e263652be5776f28f959562feaef

python scripts/r10_7_local_acceptance.py `
  --source-sha 0a49d3ad15c3e263652be5776f28f959562feaef `
  --blender "G:\SteamLibrary\steamapps\common\Blender\blender.exe" `
  --output "docs\roadmap\R10_7_LOCAL_ACCEPTANCE.json"
```

If Blender is installed elsewhere, change only the `--blender` path. Do not alter `--source-sha`.

## Required local evidence

The machine-readable JSON must report:

- `source_sha=0a49d3ad15c3e263652be5776f28f959562feaef`;
- `status=pass`, `blockers=[]`;
- Blender 5.2.x, non-empty platform, `background=true`, `online_access=false`;
- geometry fixture PASS;
- source rig PASS;
- target rig PASS;
- animation manifest PASS;
- PASS rules including mapping coverage, rest-direction compatibility, rest-length compatibility, key budget, NLA track count, NLA strip count and root-motion policy; the animation manifest itself must have no BLOCK/WARN result for the minimal canonical fixture;
- verified `animation_output.blend` filename, non-zero bytes and SHA-256;
- canonical evidence digest.

No manual animation editing, weight painting, driver insertion, constraint tweaking or video-only evidence is accepted. On failure, preserve the JSON exactly and return it without relaxing the bootstrap or Blender preferences.

## Merge ordering

After reviewed local evidence is bound to the immutable candidate, record its canonical SHA-256/bytes and facts here, rerun R0 Repository Guard + full Python Core + KodeStudio UI Smoke on the final documented head, merge PR #143 with expected SHA, then perform exactly one continuity-only post-merge normalization with the same three gates. Only after that normalization merge is R10.7 **COMPLETE + NORMALIZED** and R10.8 authorized.
