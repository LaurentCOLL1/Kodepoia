# R8.9 — Godot 4.7 source/import bridge + rebuild verification — Candidate acceptance

**Status:** CANDIDATE / PENDING EXACT-HEAD CI + CONDITIONAL REAL-GODOT GATE  
**Manual intervention:** CONDITIONAL — evaluate after exact-head CI

## Implemented scope

- Typed source/import/cache classification with `.godot/**` and legacy `.import/**` permanently excluded from source authority.
- `<asset>.import` captured as reproducibility metadata while the original source keeps its Vault/VCS identity.
- Versioned `godot-import-manifest-v1` evidence over project/source/import-settings/Vault references; generated cache bytes are deliberately excluded.
- Portability diagnostics reject Vault references to generated cache and expose missing materialized sources.
- Rebuild queries Godot 4.7 capability before mutation, purges only generated cache, invokes only the accepted R5 structured headless import tool, then verifies project/source bytes and regenerated sidecars/cache.
- Missing/incompatible Godot is explicit `UNAVAILABLE`; source and cache remain untouched when capability is unavailable.
- Cache-root symlinks fail closed.
- Exact-head local acceptance runner uses the accepted R8.7 VCS status and R5 Guardian/Permissions/KodeGodotExecutor stack against a disposable SVG fixture only.

## Automated acceptance

Before any merge, R0 Repository Guard, full Python Core and KodeStudio UI Smoke must all succeed on the same implementation head. Focused R8.9 tests must prove classification, unavailable-before-purge, source immutability, cache rebuild semantics, manifest schema validation, portability rejection and symlink refusal while all R5 regression tests remain green.

## Conditional real-Godot gate

The frozen R8 plan requires an actual Godot 4.7 import/rebuild on the exact implementation head unless hosted CI can authoritatively execute that path. Existing R5 hardware evidence proves the accepted adapter/workstation baseline but does **not** substitute for R8.9 exact-head evidence.

If hosted CI does not execute Godot 4.7 on this exact head, the gate becomes **REQUIRED** and R8.9 must remain unmerged. On the target workstation, checkout the exact candidate head and run:

```powershell
python scripts/r8_9_local_acceptance.py --repo-root . --godot "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe" --expected-head "<EXACT_R8_9_HEAD>"
```

Required result:

- process exit code `0`;
- `.kodepoia/acceptance/r8-9-local-acceptance.json` exists;
- `metadata.expected_head` equals the exact candidate head;
- `metadata.acceptance_completed=true`;
- summary has `failed=0`;
- rebuild report state is `ready` and engine version is Godot `4.7.x`.

Return/upload only that generated JSON (or its complete console JSON). Do **not** send credentials, private project files, unrelated assets or Godot account data.

R8.10 is forbidden until this gate is either authoritatively NOT TRIGGERED or REQUIRED + SATISFIED, R8.9 is merged, and post-merge continuity normalization is accepted.
