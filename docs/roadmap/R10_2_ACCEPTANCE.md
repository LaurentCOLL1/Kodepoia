# R10.2 — Acceptance record

Status: **HOSTED IMPLEMENTATION ACCEPTED; MANUAL REQUIRED**  
Manual intervention: **REQUIRED**

## Accepted hosted implementation

Immutable hosted implementation head: `b107c565e0df628eb3308543acd998f94b0b6942`.

Exact-head hosted gates:

- R0 Repository Guard #1225 / `32662882198`: **SUCCESS**.
- Python Core #1199 / `32662882146`: **SUCCESS**.
- KodeStudio UI Smoke #1166 / `32662882152`: **SUCCESS**.

The accepted hosted head includes deterministic fake-runner coverage for success, crash, timeout, cancellation, bounded output, malformed result and artifact-path spoofing; schema validation for probe-result/local evidence; CLI registration; and static bootstrap inspection proving no dynamic-code/network/subprocess surface.

## REQUIRED local gate

The final documented branch head produced by this acceptance update must itself pass R0 + full Python Core + UI Smoke before it is used locally. Once that final SHA is recorded in PR #133, check out **that exact SHA** and run the command below against a legitimate Blender 5.2.x LTS executable.

PowerShell from the repository root:

```powershell
$SourceSha = (git rev-parse HEAD).Trim()
$Blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"

if (-not (Test-Path -LiteralPath $Blender)) {
    throw "Blender 5.2 executable not found at $Blender. Stop and set `$Blender to the legitimate local Blender 5.2.x executable path; do not download/install add-ons or relax the R10 policy."
}
if (Test-Path -LiteralPath ".kodepoia\blender\r10_2_work") {
    throw "R10.2 work directory already exists. Preserve any prior failure evidence and stop; do not delete it blindly."
}

& $Blender --version
python -m pip install -e ".[dev,code]"
python -m kodepoia.cli r10-blender-accept `
  --blender "$Blender" `
  --source-sha "$SourceSha" `
  --work-dir ".kodepoia/blender/r10_2_work" `
  --output ".kodepoia/blender/r10_2_local_acceptance.json"
$AcceptanceExit = $LASTEXITCODE
Write-Host "R10.2 exit code: $AcceptanceExit"
Get-Content ".kodepoia\blender\r10_2_local_acceptance.json"
Get-FileHash ".kodepoia\blender\r10_2_local_acceptance.json" -Algorithm SHA256
(Get-Item ".kodepoia\blender\r10_2_local_acceptance.json").Length
```

Do not continue if `git rev-parse HEAD` differs from the exact final manual candidate SHA recorded in PR #133.

## Required success evidence

Acceptance requires all of the following:

- process/CLI exit code `0`;
- evidence `status=pass` and `blockers=[]`;
- evidence `source_sha` equals the exact final manual candidate SHA;
- Blender version is `5.2.x`;
- `probe.background=true`;
- `probe.online_access=false`;
- `probe.gltf_exporter_available=true`;
- `probe.bmesh_available=true`;
- verified `.blend` and GLB SHA-256 plus non-zero byte sizes;
- `process.timed_out=false`, `cancelled=false`, `crash=false`, `oom=false`.

Send back:

1. the complete canonical `.kodepoia/blender/r10_2_local_acceptance.json` file or its complete text;
2. the console summary printed by `r10-blender-accept`;
3. the SHA-256 and byte size of the evidence JSON;
4. the output of `git rev-parse HEAD` and `blender.exe --version`.

Do not send passwords, tokens, private keys, unrelated files, or unredacted diagnostic paths outside the governed evidence.

## Failure recovery

On any non-zero exit or `status=fail`, preserve the JSON and the entire `.kodepoia/blender/r10_2_work` directory, stop, and return the evidence. Do **not** retry with autoexec enabled, online mode, arbitrary Python flags, relaxed sandbox paths, add-ons, or modified Blender preferences. Cleanup is allowed only after the failed evidence has been reviewed and only for the documented R10.2 temporary workspace.

## Gate ordering

R10.2 remains **IN PROGRESS** until the REQUIRED local evidence is reviewed, accepted, recorded, final exact-head gates succeed, PR #133 merges, and post-merge continuity normalization succeeds. **Do not start R10.3 before that sequence is complete.**
