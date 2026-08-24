# R11.9 — Acceptance

Status: **HOSTED IMPLEMENTATION ACCEPTED — REQUIRED LOCAL GATE PRE-GATE BLOCKED / NOT YET RUN**  
Manual intervention: **REQUIRED**

## Branch point and scope

- Base normalized `main`: `e01f18ee5b7fbd7df513e10ad96c1ac35d83d6e5`.
- Branch: `r11/9-godot-cinematic-capture`.
- PR: #173.
- Scope: typed R11.8→Godot assembly intent, existing R5 fixed movie command path, repository synthetic fixture, bounded AVI capture, fixed ffprobe verification, A/V sync facts, exact-head local collector, schemas/tests/docs.
- No private project, arbitrary Godot argv/GDScript, gameplay generation, NLE, plugin/encoder download or automatic runtime installation.

## Hosted implementation acceptance

### Superseded candidate

`13832f63c8513962547845a86de655f2affcdca8` passed R0 #1418 / `32752786958`, Python #1392 / `32752787149`, and UI #1359 / `32752787060`; Ubuntu reported **1016 passed / 8 skipped / 46 warnings** and R7/R8/R9 PASS. It is historical green evidence only.

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
- Frozen-procedure documentation head `a5f1566ea823be5b0a5396663ab83aeffc6c409e`: R0 #1420, Python #1394 and UI #1361 — SUCCESS.
- First corrected pre-gate documentation head `6d01623b9552a5b357423d4f2a3d773dac52fc76`: R0 #1421, Python #1395 and UI #1362 — SUCCESS.

Focused R11.9 tests prove R11.8 shot/digest/timebase binding, typed-only assembly intent, fixed R5 movie argv, failure/timeout/cancel propagation, fixed trusted synthetic fixture, fixed ffprobe query, fail-closed FPS/resolution/stream/size/A-V drift checks, and schema validation.

## First local preflight attempt — NOT A GATE FAILURE

The first user attempt on 2026-08-24 did not enter the real collector gate:

- local HEAD was `a9862b3bf475b259fe154d1e2486116ad04602f3` (R11.5-era local state);
- candidate `087eae19ea03dd544d75a08c1eb348fe187624c5` was not present in the local object database;
- therefore `scripts/r11_9_local_acceptance.py` was also absent from the checked-out worktree;
- Godot 4.7 was not discoverable through `PATH` by `Get-Command`;
- `ffprobe` was discoverable;
- despite the `(.venv)` prompt, the failed script launch identified `C:\Python\Python312\python.exe`, so the corrected procedure now pins execution to `.venv\Scripts\python.exe` and verifies `import kodepoia` before gate start.

This is a **pre-gate prerequisite block**, not FAIL evidence. An exact Git synchronization is permitted before the gate. The no-network rule starts only after the candidate and local runtime paths have been resolved.

## REQUIRED local checkpoint — corrected frozen procedure

Real Godot 4.7 Movie Maker/import/render/audio behavior cannot be established from fake runners or hosted tests. Run the following from the local Kodepoia repository.

Network access is permitted only for the exact Git fetch below. Do not install/update Python packages, Godot, FFmpeg, codecs or plugins as part of the gate.

Paste this as **one PowerShell script block** so a failure stops the remainder instead of producing cascading errors:

```powershell
& {
    $ErrorActionPreference = "Stop"
    $SourceSha = "087eae19ea03dd544d75a08c1eb348fe187624c5"
    $RemoteBranch = "r11/9-godot-cinematic-capture"

    if (git status --porcelain) {
        throw "Working tree is not clean. Stop: do not stash, reset, or discard files for R11.9."
    }

    Write-Host "[PRE-GATE] Fetching only the R11.9 branch so the accepted candidate exists locally..."
    git fetch --no-tags origin $RemoteBranch
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to fetch the R11.9 branch from origin. Stop and return this error."
    }

    git cat-file -e "$SourceSha^{commit}"
    if ($LASTEXITCODE -ne 0) {
        throw "Accepted R11.9 candidate is still unavailable after the branch fetch. Stop and return this error."
    }

    $GodotCmd = Get-Command godot -ErrorAction SilentlyContinue
    if (-not $GodotCmd) { $GodotCmd = Get-Command godot4 -ErrorAction SilentlyContinue }

    if ($GodotCmd) {
        $Godot = $GodotCmd.Source
    } else {
        $SearchRoots = @(
            (Join-Path $env:USERPROFILE "Downloads"),
            (Join-Path $env:USERPROFILE "Desktop"),
            (Join-Path $env:LOCALAPPDATA "Programs"),
            $env:ProgramFiles,
            [Environment]::GetFolderPath("ProgramFilesX86")
        ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique

        $GodotCandidates = @(
            foreach ($Root in $SearchRoots) {
                Get-ChildItem -LiteralPath $Root -Filter "Godot*.exe" -File -Recurse -ErrorAction SilentlyContinue |
                    Where-Object { $_.Name -match '(?i)^Godot.*4\.7' }
            }
        ) | Sort-Object FullName -Unique

        if ($GodotCandidates.Count -eq 0) {
            throw "No existing Godot 4.7 executable was found in PATH or common Windows locations. Stop and report this; do not run the collector."
        }
        if ($GodotCandidates.Count -gt 1) {
            $GodotCandidates | Select-Object FullName | Format-Table -AutoSize
            throw "Multiple Godot 4.7 executables were found. Stop and return the list so one exact executable can be frozen."
        }
        $Godot = $GodotCandidates[0].FullName
    }

    $GodotVersion = (& $Godot --version | Select-Object -First 1).Trim()
    if ($LASTEXITCODE -ne 0 -or $GodotVersion -notmatch '^4\.7(?:\.|-|$)') {
        throw "Resolved Godot is not a working 4.7.x runtime: $GodotVersion"
    }

    $FfprobeCmd = Get-Command ffprobe -ErrorAction SilentlyContinue
    if (-not $FfprobeCmd) {
        throw "Existing ffprobe executable was not found through PATH. Stop and report this; do not install/download during the gate."
    }
    $Ffprobe = $FfprobeCmd.Source

    $VenvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        throw "Expected project venv Python is missing: .venv\Scripts\python.exe. Stop and report this; do not pip install during the gate."
    }
    $Python = (Resolve-Path -LiteralPath $VenvPython).Path
    & $Python -c "import sys, kodepoia; print(sys.executable); print(kodepoia.__file__)"
    if ($LASTEXITCODE -ne 0) {
        throw "Project venv Python cannot import kodepoia. Stop and report this; do not pip install during the gate."
    }

    Write-Host "[PRE-GATE] Candidate available : $SourceSha"
    Write-Host "[PRE-GATE] Godot              : $Godot"
    Write-Host "[PRE-GATE] Godot version      : $GodotVersion"
    Write-Host "[PRE-GATE] ffprobe            : $Ffprobe"
    Write-Host "[PRE-GATE] Python             : $Python"

    Write-Host "[GATE] From this point onward: no fetch/download/install/update."

    git switch --detach $SourceSha
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to detach to the accepted R11.9 candidate."
    }

    $Head = (git rev-parse HEAD).Trim()
    if ($Head -ne $SourceSha) {
        throw "Wrong HEAD: expected $SourceSha, got $Head"
    }
    if (git status --porcelain) {
        throw "Working tree changed while switching to the candidate. Stop."
    }
    if (-not (Test-Path -LiteralPath "scripts/r11_9_local_acceptance.py")) {
        throw "R11.9 collector is missing on the accepted candidate. Stop."
    }

    $Evidence = Join-Path $env:TEMP "KODEPOIA_R11_9_LOCAL_ACCEPTANCE.json"
    Remove-Item $Evidence -ErrorAction SilentlyContinue

    & $Python scripts/r11_9_local_acceptance.py `
      --source-sha $SourceSha `
      --godot "$Godot" `
      --ffprobe "$Ffprobe" `
      --output "$Evidence"
    $CollectorExit = $LASTEXITCODE

    if (-not (Test-Path -LiteralPath $Evidence)) {
        throw "R11.9 collector did not produce its JSON evidence file. Stop and return the console output."
    }

    $EvidenceText = Get-Content $Evidence -Raw
    Write-Output $EvidenceText

    if ($CollectorExit -ne 0) {
        throw "R11.9 local acceptance returned FAIL. Return the complete JSON above; do not edit/convert/retry against a private project."
    }
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
- verifier-accepted audio facts and A/V sync error within the frozen tolerance;
- capture SHA-256/byte count and evidence digest.

The temporary Godot project and AVI are destroyed automatically after verification. Do not attempt to preserve or commit the AVI.

### Failure recovery / stop rules

If pre-gate discovery finds no Godot 4.7, finds more than one candidate, or the project venv is unavailable/unusable, stop and return that result before the collector. If the real gate starts and any version, renderer/movie-writer, timeout/cancel, ffprobe, duration or A/V sync check fails:

1. do not edit generated files;
2. do not convert the AVI;
3. do not run against another/private project;
4. do not install/download a codec, plugin, Godot build, Python package or FFmpeg build during the gate;
5. return the complete generated JSON when present, plus the final PowerShell error line when no JSON is produced;
6. R11.9 remains blocked and R11.10+ remain forbidden.

### Evidence to return

Return the complete JSON printed by the script block. The accepted schema intentionally omits local filesystem paths, usernames, private project names and private media.

## Completion ordering after manual PASS

- Validate returned JSON against the frozen policy and evidence digest.
- Commit only accepted machine-readable evidence/documentation necessary to bind the manual PASS; never commit the AVI or temporary project.
- Re-run R0 + full Python Core + KodeStudio UI Smoke on the exact final evidence-bound head.
- Merge exact accepted R11.9 PR head with expected-SHA protection.
- Perform exactly one continuity-only normalization, re-gate it and merge it.
- Only that normalization merge makes R11.9 COMPLETE + NORMALIZED and authorizes R11.10.

Until the REQUIRED local PASS is returned, **stop at R11.9**.
