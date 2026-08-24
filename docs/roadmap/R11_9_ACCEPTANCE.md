# R11.9 — Acceptance

Status: **HOSTED IMPLEMENTATION ACCEPTED — REQUIRED LOCAL GATE FROZEN / NOT YET RUN**  
Manual intervention: **REQUIRED**

## Branch point and scope

- Base normalized `main`: `e01f18ee5b7fbd7df513e10ad96c1ac35d83d6e5`.
- Branch: `r11/9-godot-cinematic-capture`.
- PR: #173.
- Scope: typed R11.8→Godot assembly intent, existing R5 fixed movie command path, repository synthetic fixture, bounded AVI capture, fixed ffprobe verification, A/V sync facts, exact-head local collector, schemas/tests/docs.
- No private project, arbitrary Godot argv/GDScript, gameplay generation, NLE, plugin/encoder download or automatic runtime installation.

## Hosted implementation acceptance

### Superseded candidate

`13832f63c8513962547845a86de655f2affcdca8` passed R0 #1418 / `32752786958`, Python #1392 / `32752787149`, and UI #1359 / `32752787060`; Ubuntu reported **1016 passed / 8 skipped / 46 warnings** and R7/R8/R9 PASS. It is **not** the manual candidate because Web verification of official Godot 4.7 Windows distribution names exposed an over-restrictive collector basename allowlist. That candidate remains historical green evidence only.

### Accepted implementation candidate

Exact manual candidate: **`087eae19ea03dd544d75a08c1eb348fe187624c5`**.

- R0 Repository Guard: #1419 / `32753163815` — SUCCESS.
- Full Python Core: #1393 / `32753163940` — SUCCESS.
  - Ubuntu: **1016 passed / 8 skipped / 46 warnings**; R7/R8/R9 integrated checks PASS.
  - Windows Python: SUCCESS.
  - Ubuntu package build: SUCCESS.
  - Windows package build: SUCCESS.
  - internal KodeStudio smoke: SUCCESS.
- KodeStudio UI Smoke: #1360 / `32753163936` — SUCCESS.

Focused R11.9 tests prove R11.8 shot/digest/timebase binding, typed-only assembly intent, fixed R5 movie argv, failure/timeout/cancel propagation, fixed trusted synthetic fixture, fixed ffprobe query, fail-closed FPS/resolution/stream/size/A-V drift checks, and schema validation.

## REQUIRED local checkpoint — frozen procedure

Real Godot 4.7 Movie Maker/import/render/audio behavior cannot be established from fake runners or hosted tests. Run **only** the following checkpoint against candidate `087eae19ea03dd544d75a08c1eb348fe187624c5`.

### Prerequisites

- Work from the local Kodepoia repository.
- The working tree must be clean before switching SHA.
- Python environment/dependencies already used for Kodepoia must already work. **Do not run pip/install/update during this gate.**
- Godot 4.7 must already be installed. Official names such as `Godot_v4.7-stable_win64.exe` and `Godot_v4.7.1-stable_win64.exe` are accepted; the collector still validates the reported engine version as 4.7.x.
- `ffprobe` must already be installed and callable. **Do not install FFmpeg/ffprobe during this gate.**
- No network access, download, private project, personal recording or private asset is required.

### PowerShell procedure

Run from the Kodepoia repository root:

```powershell
$SourceSha = "087eae19ea03dd544d75a08c1eb348fe187624c5"

if (git status --porcelain) {
    throw "Working tree is not clean. Stop: do not stash, reset, or discard files for R11.9."
}

git cat-file -e "$SourceSha^{commit}"
if ($LASTEXITCODE -ne 0) {
    throw "R11.9 candidate is not available locally. Stop and report this; do not fetch/download during the gate."
}

git switch --detach $SourceSha
$Head = (git rev-parse HEAD).Trim()
if ($Head -ne $SourceSha) {
    throw "Wrong HEAD: expected $SourceSha, got $Head"
}

$GodotCmd = Get-Command godot -ErrorAction SilentlyContinue
if (-not $GodotCmd) { $GodotCmd = Get-Command godot4 -ErrorAction SilentlyContinue }
if (-not $GodotCmd) { $GodotCmd = Get-Command "Godot_v4.7*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1 }
if (-not $GodotCmd) {
    throw "Existing Godot 4.7 executable was not found through PATH. Stop and report the path/location situation; do not install or download anything."
}
$Godot = $GodotCmd.Source

$FfprobeCmd = Get-Command ffprobe -ErrorAction SilentlyContinue
if (-not $FfprobeCmd) {
    throw "Existing ffprobe executable was not found through PATH. Stop and report this; do not install or download anything."
}
$Ffprobe = $FfprobeCmd.Source

$Evidence = Join-Path $env:TEMP "KODEPOIA_R11_9_LOCAL_ACCEPTANCE.json"
Remove-Item $Evidence -ErrorAction SilentlyContinue

python scripts/r11_9_local_acceptance.py `
  --source-sha $SourceSha `
  --godot "$Godot" `
  --ffprobe "$Ffprobe" `
  --output "$Evidence"
$CollectorExit = $LASTEXITCODE

if (-not (Test-Path $Evidence)) {
    throw "R11.9 collector did not produce its JSON evidence file. Stop and return the console output."
}

Get-Content $Evidence -Raw

if ($CollectorExit -ne 0) {
    throw "R11.9 local acceptance returned FAIL. Return the complete JSON above; do not edit, convert, or retry with a private project."
}
```

### Expected PASS

The JSON must have all of the following without manual editing:

- `source_sha = 087eae19ea03dd544d75a08c1eb348fe187624c5`;
- `status = "pass"`;
- `blockers = []`;
- `error_type = null`;
- `runtime.godot_compatible_47 = true` and a Godot 4.7.x version string;
- Godot + ffprobe executable SHA-256 identities;
- five synthetic fixture hashes;
- `assembly.command_policy_id = "r11.9.godot.capture.v1"`;
- capture `status = "pass"`, 640×360, 30 FPS, expected 90 frames/3 s;
- exactly the verifier-accepted audio facts and A/V sync error within the frozen tolerance;
- capture SHA-256/byte count and evidence digest.

The temporary Godot project and AVI are destroyed automatically after verification. **Do not attempt to preserve or commit the AVI.**

### Failure recovery / stop rules

If any prerequisite check, version check, renderer/movie-writer operation, timeout/cancel check, ffprobe verification, duration check or A/V sync check fails:

1. Do not edit generated files.
2. Do not convert the AVI.
3. Do not run against another/private project.
4. Do not install/download a codec, plugin, Godot build or FFmpeg build during the gate.
5. Return the complete generated JSON when present, plus the final PowerShell error line when no JSON is produced.
6. R11.9 remains blocked; R11.10 and later subdivisions remain forbidden.

### Evidence to return

Return **the complete JSON printed by `Get-Content $Evidence -Raw`**. The accepted schema intentionally omits local filesystem paths, usernames, private project names and private media. If an unexpected console line contains a personal path, redact only that console line; do not alter the JSON.

## Completion ordering after manual PASS

- Validate returned JSON against the frozen policy and evidence digest.
- Commit only accepted machine-readable evidence/documentation necessary to bind the manual PASS; never commit the AVI or temporary project.
- Re-run R0 + full Python Core + KodeStudio UI Smoke on the exact final evidence-bound head.
- Merge exact accepted R11.9 PR head with expected-SHA protection.
- Perform exactly one continuity-only normalization, re-gate it and merge it.
- Only that normalization merge makes R11.9 COMPLETE + NORMALIZED and authorizes R11.10.

Until the REQUIRED local PASS is returned, **stop at R11.9**.
