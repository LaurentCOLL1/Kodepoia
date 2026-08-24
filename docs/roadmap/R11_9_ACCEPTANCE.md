# R11.9 — Acceptance

Status: **ACCEPTED — REQUIRED LOCAL GATE SATISFIED; FINAL EVIDENCE-BOUND RE-GATE REQUIRED BEFORE MERGE**  
Manual intervention: **REQUIRED — SATISFIED**

## Branch point and scope

- Base normalized `main`: `e01f18ee5b7fbd7df513e10ad96c1ac35d83d6e5`.
- Branch: `r11/9-godot-cinematic-capture`.
- PR: #173.
- Scope: typed R11.8→Godot assembly intent, accepted R5 fixed movie command, repository synthetic fixture, bounded AVI capture, ffprobe verification, A/V sync facts, exact-head local collector, schemas/tests/docs.
- No private project, arbitrary Godot argv/GDScript, gameplay generation, NLE, codec/plugin auto-install or media conversion.

## Hosted implementation acceptance

### Superseded candidate

`13832f63c8513962547845a86de655f2affcdca8` passed R0 #1418 / `32752786958`, Python #1392 / `32752787149`, and UI #1359 / `32752787060`; Ubuntu reported **1016 passed / 8 skipped / 46 warnings** and R7/R8/R9 PASS. It is historical green evidence only.

### Accepted implementation/manual candidate

Exact candidate: **`087eae19ea03dd544d75a08c1eb348fe187624c5`**.

- R0 Repository Guard: #1419 / `32753163815` — SUCCESS.
- Full Python Core: #1393 / `32753163940` — SUCCESS.
  - Ubuntu: **1016 passed / 8 skipped / 46 warnings**; R7/R8/R9 integrated checks PASS.
  - Windows Python: SUCCESS.
  - Ubuntu package build: SUCCESS.
  - Windows package build: SUCCESS.
  - internal KodeStudio smoke: SUCCESS.
- KodeStudio UI Smoke: #1360 / `32753163936` — SUCCESS.

Procedure-only documentation heads were also re-gated while prerequisite recovery was hardened:

- `a5f1566ea823be5b0a5396663ab83aeffc6c409e`: R0 #1420, Python #1394, UI #1361 — SUCCESS.
- `6d01623b9552a5b357423d4f2a3d773dac52fc76`: R0 #1421, Python #1395, UI #1362 — SUCCESS.
- `70c2ad9240a91faffa707e5408d58f084b59de47`: R0 #1422, Python #1396, UI #1363 — SUCCESS.
- `977768dd10057991a5eb5c428dcf1c9a54d15aa7`: R0 #1423 / `32756393302`, Python #1397 / `32756393208`, UI #1364 / `32756393325` — SUCCESS.

The final procedure records provider-aware runtime discovery. On Windows, Steam libraries are treated as variable-drive provider locations such as `<drive>:\SteamLibrary\steamapps\common\<Product>\<Executable>` rather than assuming one drive letter. Explicit governed configuration remains preferred over discovery.

## Pre-gate recovery history — not FAIL evidence

Two user attempts stopped before `[GATE]` and therefore are not local acceptance failures:

1. the local clone was still at R11.5 and did not contain the R11.9 candidate/collector; Godot was not in PATH and system Python was selected despite the venv prompt;
2. the targeted branch fetch succeeded, but the generic resolver did not include Steam libraries.

Both were prerequisite discovery issues. No collector evidence was emitted.

## REQUIRED local checkpoint — SATISFIED

The user then executed the real offline gate on exact source SHA **`087eae19ea03dd544d75a08c1eb348fe187624c5`** with the repository synthetic fixture.

Accepted machine-readable evidence: `docs/roadmap/R11_9_LOCAL_ACCEPTANCE.json`.

### Runtime identity

- Platform: Windows.
- Godot executable basename: `godot.windows.opt.tools.64.exe`.
- Godot version: **`4.7.2.stable.steam.ed1daf0bf`**.
- Godot compatible 4.7: `true`.
- Godot executable SHA-256: `12310c74bdda7dcd43f28e971f33047dcecadd436b68169d61ce41009006df38`.
- ffprobe version: **`8.1.1-full_build-www.gyan.dev`**.
- ffprobe executable SHA-256: `a6618e99bb58869ded3c6f37b53aa1a8d701c3591dbb7b5b317d47369c112be2`.

No absolute personal runtime path is part of the accepted evidence.

### Synthetic fixture identity

- `assembly.json`: `384815cdfa94668ca551624015fa0eef0baf41245e4b92cc0d2c67f9eed251a2`.
- `capture.gd`: `3857b8d18348e30c7e823856ff73e106d770bc161d0b23e1677359eab69e1fd5`.
- `capture.tscn`: `dbf6d21ec4e17f8165257b9c63934691752cac4234febfdff84bf2e26e51a5ae`.
- `project.godot`: `e64df3c52d31deea6a5a3a09d83d3fe7d284fd4a909ceabe8bd9418656855c73`.
- `tone.wav`: `047b1640aef3426cbd4b75098f2e606836ffba6a125418b465bd5fd5e0bbece6`.

### Real capture facts

- Command policy: `r11.9.godot.capture.v1`.
- Sequence: `r11.9.synthetic.sequence`.
- Assembly digest: `fb2952dec857d46c73caa17fd2673b33d8f7db270cfe4df87c430f636e7fb053`.
- Status: **PASS**.
- Resolution: **640×360**.
- FPS: **30**.
- Expected/reported frames: **90 / 90**.
- Expected/video/audio/container duration: **3.0 / 3.0 / 3.0 / 3.0 seconds**.
- Audio: **2 channels, 48000 Hz**.
- A/V sync error: **0.0 s**; frozen limit `0.07666666666666666 s`.
- Output bytes: **1,021,734**.
- Output SHA-256: `2f383635f2ee94def1ee832ffd742f0fc2cf41af18ef939078f72746e6e8a194`.
- Evidence digest: **`6afe45e3c9047cfa58b7c617ff671e34e166bd9189a32ea62f1350243955b6f5`**.
- Blockers: `[]`.
- `error_type`: `null`.

The evidence digest is the SHA-256 of canonical JSON with `evidence_digest` omitted. Repository tests recalculate it and validate the evidence against `schemas/r11/r11-9-local-acceptance.schema.json`.

## External compatibility note

Godot Movie Maker documents `--write-movie`, fixed FPS capture and bounded frame exit; R11.9 uses these only through the already accepted R5 sandboxed command policy. Upstream documentation is compatibility evidence, not the acceptance authority. The accepted authority is the exact repository candidate plus the machine-readable local evidence above.

## Final completion ordering

1. Re-run R0 Repository Guard + full Python Core + KodeStudio UI Smoke on the exact final evidence-bound head.
2. Merge PR #173 only with expected-head SHA protection after all three are SUCCESS.
3. Perform exactly one continuity-only post-merge normalization, re-gate it and merge it.
4. Only that normalization merge makes R11.9 **COMPLETE + NORMALIZED** and authorizes R11.10.

Until step 4 completes, **R11.10 remains forbidden**.
