# R8.9 — Godot 4.7 source/import bridge + rebuild verification — Acceptance

**Status:** ACCEPTED / MANUAL REQUIRED SATISFIED / PENDING MERGE  
**Manual intervention:** REQUIRED SATISFIED

## Accepted implementation

- Exact accepted implementation head: `da8b4aedd280dadffcf4099bfa2b902cb70d81a7`.
- PR: #97 — open pending final documentation/continuity gates and merge.
- Base normalized R8.8 main: `ccde847c160d47fdff3fbbd27e82969c0c6b4d90`.
- The implementation head is frozen. Later commits in PR #97 may only record acceptance/continuity evidence unless a demonstrated defect requires a new implementation candidate and a new exact-head local gate.

## Authoritative automated CI on the exact implementation head

- R0 Repository Guard #1071 / `32613177879`: SUCCESS Ubuntu + Windows.
- Python Core #1045 / `32613177848`: SUCCESS 5/5.
- Ubuntu authoritative suite: `565 passed / 5 skipped / 46 warnings`.
- KodeStudio UI Smoke #1012 / `32613177859`: SUCCESS.

The hosted workflows compile/test the complete R8.9 bridge and regression surface. They do not execute the real Godot 4.7 `--import` rebuild, so the frozen CONDITIONAL gate correctly became REQUIRED.

## Required local Godot 4.7 evidence — SATISFIED

The target workstation executed `scripts/r8_9_local_acceptance.py` against the exact accepted implementation head.

Evidence summary:

- generated at `2026-08-23T02:37:35.738827+00:00`;
- expected/executed head: `da8b4aedd280dadffcf4099bfa2b902cb70d81a7`;
- `acceptance_completed=true`;
- Python `3.12.4`;
- platform `Windows-11-10.0.26220-SP0`;
- Godot executable basename `godot.windows.opt.tools.64.exe`;
- Godot engine `4.7.2.stable.steam.ed1daf0bf`;
- summary: `4 passed / 0 failed / 4 total`;
- evidence file SHA-256: `6579babc829022930e5abe889583e32357fa3d7695b1a2713014e32f86e23b7e`;
- evidence file byte length: `2969`.

Accepted step results:

1. `exact_head` — PASS; returned the exact accepted head.
2. `classification` — PASS; `source.svg=source`, `source.svg.import=import_metadata`, `.godot/imported/cache.ctex=generated_cache`, `.import/legacy.cache=generated_cache`.
3. `rebuild` — PASS; report state `ready`, `import_returncode=0`, no issues, 7 generated cache files.
4. `audit_chain` — PASS; tamper-evident audit chain `valid=true`.

Rebuild identity/evidence:

- project SHA-256 `bac971ef0dc7a0c8898cea3a7e5d788b9d33343690f28ca52c3af98b9022c212`, 189 bytes;
- source `source.svg` SHA-256 `d6b791957eb782fbb0b00272b902c025fb4cc3b9d396b850d64a8ffc050c6091`, 154 bytes;
- source asset ID `asset_5fea5ac2e9ee21935f9b2d29577cae04`;
- source revision ID `rev_623284040fb3ef2874d1de017430a318`;
- import settings `source.svg.import` SHA-256 `1b70ea13afe340575035099e25ccceeea41e22153d3700449b2f8c2e66dfbd87`, 1019 bytes;
- manifest digest `aca5eb8dd2c877a17eadd666c29239a3f95c2674c776f86cc5cabafc6b1f47d8`;
- project reference target `source.svg` retained the exact Vault asset/revision identity;
- purged generated cache root: legacy `.import`; regenerated cache count: 7.

The evidence contains no credential, private project file or user asset. The local runner used only its disposable fixture under `.kodepoia/acceptance/r8-9/project`.

## Accepted scope

- Typed source/import/cache classification with `.godot/**` and legacy `.import/**` excluded from source authority.
- `<asset>.import` captured as reproducibility metadata while the original source keeps its Vault/VCS identity.
- Versioned `godot-import-manifest-v1` evidence over project/source/import-settings/Vault references; generated cache bytes are excluded from canonical identity.
- Portability diagnostics reject Vault references to generated cache and expose missing materialized sources.
- Rebuild queries Godot 4.7 capability before mutation, purges only generated cache, invokes only the accepted R5 structured headless import tool, then verifies project/source bytes and regenerated sidecars/cache.
- Missing/incompatible Godot is explicit `UNAVAILABLE`; source and cache remain untouched when capability is unavailable.
- Cache-root symlinks fail closed.
- Exact-head local acceptance reuses accepted R8.7 VCS evidence and the R5 Guardian/Permissions/KodeGodotExecutor boundary; no arbitrary subprocess surface was introduced.

## External semantic cross-check

Godot 4.7 documents `--import` as starting the editor, waiting until resources are imported, then quitting. Godot's import process also treats `<asset>.import` as important versioned import metadata while generated imported resources live under `.godot/imported/`. R8.9's accepted source/sidecar/cache model follows those engine semantics without making generated cache bytes authoritative.

## Merge gate

R8.9 is accepted functionally, but it is not COMPLETE until:

1. this acceptance/continuity evidence is on one final documentation head;
2. R0 Repository Guard, full Python Core and KodeStudio UI Smoke are SUCCESS on that documentation head;
3. PR #97 is merged;
4. post-merge continuity normalization records the merge SHA and final `main` state.

Do not start R8.10 before those steps complete.
