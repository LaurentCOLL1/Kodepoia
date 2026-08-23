# R8.9 — Godot 4.7 source/import bridge + rebuild verification — Candidate acceptance

**Status:** BLOCKED PENDING REQUIRED REAL-GODOT EXACT-HEAD EVIDENCE  
**Manual intervention:** REQUIRED

## Implemented scope

- Typed source/import/cache classification with `.godot/**` and legacy `.import/**` permanently excluded from source authority.
- `<asset>.import` captured as reproducibility metadata while the original source keeps its Vault/VCS identity.
- Versioned `godot-import-manifest-v1` evidence over project/source/import-settings/Vault references; generated cache bytes are deliberately excluded.
- Portability diagnostics reject Vault references to generated cache and expose missing materialized sources.
- Rebuild queries Godot 4.7 capability before mutation, purges only generated cache, invokes only the accepted R5 structured headless import tool, then verifies project/source bytes and regenerated sidecars/cache.
- Missing/incompatible Godot is explicit `UNAVAILABLE`; source and cache remain untouched when capability is unavailable.
- Cache-root symlinks fail closed.
- Exact-head local acceptance runner uses the accepted R8.7 VCS status and R5 Guardian/Permissions/KodeGodotExecutor stack against a disposable SVG fixture only.

## Automated acceptance precursor

Implementation head `eaa7c8baa061e82b5dcf069dc5be63b8e88addeb` passed all automated gates:

- R0 Repository Guard #1070 / `32613096619`: SUCCESS;
- Python Core #1044 / `32613096631`: SUCCESS 5/5;
- Ubuntu authoritative suite: `565 passed / 5 skipped / 46 warnings`;
- KodeStudio UI Smoke #1011 / `32613096616`: SUCCESS.

These workflows compile/test the bridge and regression surface but do not execute a real Godot 4.7 `--import` rebuild. Therefore they cannot satisfy the frozen R8.9 real-engine criterion by themselves.

## Required real-Godot gate

The frozen R8 plan requires an actual Godot 4.7 import/rebuild on the exact final candidate head when hosted CI cannot authoritatively execute that path. Existing R5 hardware evidence proves the accepted adapter/workstation baseline but does **not** substitute for R8.9 exact-head evidence.

On the target workstation, checkout the exact final R8.9 candidate head shown in PR #97, then run:

```powershell
python scripts/r8_9_local_acceptance.py --repo-root . --godot "D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe" --expected-head "<FINAL_R8_9_HEAD_FROM_PR_97>"
```

Required result:

- process exit code `0`;
- `.kodepoia/acceptance/r8-9-local-acceptance.json` exists;
- `metadata.expected_head` equals the exact final candidate head;
- `metadata.acceptance_completed=true`;
- summary has `failed=0`;
- rebuild report state is `ready` and engine version is Godot `4.7.x`.

Return/upload only that generated JSON (or its complete console JSON). Do **not** send credentials, private project files, unrelated assets or Godot account data.

## Stop rule

R8.9 remains unmerged. R8.10 and R8.11 are forbidden until this REQUIRED gate is SATISFIED, R8.9 is merged, and post-merge continuity normalization is accepted.
