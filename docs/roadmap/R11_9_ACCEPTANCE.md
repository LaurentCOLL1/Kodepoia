# R11.9 — Acceptance

Status: **IMPLEMENTATION CANDIDATE — HOSTED GATES PENDING**  
Manual intervention: **REQUIRED — NOT YET RUN**

## Branch point and scope

- Base normalized `main`: `e01f18ee5b7fbd7df513e10ad96c1ac35d83d6e5`.
- Branch: `r11/9-godot-cinematic-capture`.
- Scope: typed R11.8→Godot assembly intent, existing R5 fixed movie command path, repository synthetic fixture, bounded AVI capture, fixed ffprobe verification, A/V sync facts, exact-head local collector, schemas/tests/docs.
- No private project, arbitrary Godot argv/GDScript, gameplay generation, NLE, plugin/encoder download or automatic runtime installation.

## Required hosted acceptance before manual execution

The implementation candidate must pass on one exact SHA:

1. R0 Repository Guard — SUCCESS.
2. Full Python Core — SUCCESS on Ubuntu and Windows, including package builds and R7/R8/R9 integrated checks.
3. KodeStudio UI Smoke — SUCCESS.
4. Focused R11.9 tests must prove:
   - R11.8 shot identity/digest/timebase/duration binding;
   - only typed allowlisted Godot track intents are emitted;
   - no raw script/path/argv surface exists in cinematic intent;
   - R5 compiles the exact bounded `--write-movie`/`--fixed-fps`/`--quit-after` command;
   - failure, timeout and cancellation do not become PASS;
   - fixed synthetic fixture cannot inject shell/network/process behavior;
   - ffprobe query is fixed and movie-specific;
   - wrong FPS/resolution/stream shape, oversized output and excessive A/V drift fail closed;
   - versioned JSON schemas accept canonical examples.

## REQUIRED local checkpoint

Real Godot 4.7 Movie Maker/import/render/audio behavior cannot be established from fake runners or hosted schema tests. The frozen R11 plan therefore requires one real local collector run on the exact implementation candidate.

The exact candidate SHA, hosted run IDs, prerequisites and copy-paste command will be frozen in this document after the first hosted gates succeed and before the manual run. The local run will:

- require an exact clean checkout of that candidate SHA;
- require an already-installed Godot 4.7 executable and ffprobe executable;
- perform no network/download/install;
- create only a temporary synthetic Godot fixture;
- capture 90 frames at 30 FPS and 640×360;
- verify exactly one video + one audio stream and frozen duration/sync tolerances;
- output one privacy-minimized JSON evidence file;
- exit non-zero with FAIL evidence if any prerequisite or runtime fact is wrong.

Do **not** substitute a private project, manually edit generated fixture/output, convert a failed movie, install a plugin/codec during the gate, or infer PASS from a playable-but-malformed AVI.

## Evidence required from the manual run

Return the collector's complete JSON text. Accepted evidence must contain:

- exact source SHA;
- `status=pass`, `blockers=[]`;
- Godot 4.7 identity + executable SHA-256;
- ffprobe identity + executable SHA-256;
- synthetic fixture file hashes;
- assembly identity/digest + command policy ID;
- capture SHA-256/bytes/resolution/FPS/frame facts;
- audio sample rate/channels;
- video/audio durations and A/V sync error within frozen tolerances;
- canonical evidence digest.

No local filesystem path, username, private project name or private media belongs in accepted evidence.

## Completion ordering after manual PASS

- Commit only the accepted machine-readable evidence/documentation necessary to bind the manual PASS; do not commit the AVI or temporary fixture.
- Re-run R0 + full Python Core + KodeStudio UI Smoke on that exact final evidence-bound head.
- Merge exact accepted R11.9 PR head with expected-SHA protection.
- Perform exactly one continuity-only normalization, re-gate it and merge it.
- Only that normalization merge makes R11.9 COMPLETE + NORMALIZED and authorizes R11.10.

If the REQUIRED local gate fails or cannot run, stop at R11.9. R11.10 and later subdivisions remain forbidden.
