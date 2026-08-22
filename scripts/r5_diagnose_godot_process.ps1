param(
    [string]$GodotPath = "",
    [double]$TimeoutSeconds = 8.0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

function Resolve-Python {
    $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) { return $venvPython }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $cmd) { throw "Python was not found. Activate/create .venv or install Python 3.12+." }
    return $cmd.Source
}

function Resolve-Godot([string]$Requested) {
    if ($Requested) {
        if (-not (Test-Path $Requested)) { throw "Godot executable not found: $Requested" }
        return (Resolve-Path $Requested).Path
    }
    foreach ($name in @("godot", "godot4")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($null -ne $cmd) { return $cmd.Source }
    }
    throw "Godot was not found on PATH. Re-run with -GodotPath 'C:\path\to\Godot.exe'."
}

if ($TimeoutSeconds -lt 2.0 -or $TimeoutSeconds -gt 30.0) {
    throw "TimeoutSeconds must be between 2 and 30 seconds."
}

$Branch = (& git branch --show-current).Trim()
if ($Branch -ne "agent/r5-6-governed-acceptance") {
    throw "Expected branch agent/r5-6-governed-acceptance, found '$Branch'."
}

$Python = Resolve-Python
$Godot = Resolve-Godot $GodotPath
$Fixture = Join-Path $RepoRoot ".kodepoia\r5-acceptance\project\project.godot"
if (-not (Test-Path $Fixture)) {
    throw "R5 fixture is missing: $Fixture. Run the R5 ProbeOnly helper once before this diagnostic."
}

$env:PYTHONPATH = Join-Path $RepoRoot "src"
$Output = Join-Path $RepoRoot ".kodepoia\benchmarks\r5-godot-process-diagnostic.json"

Write-Host "Kodepoia R5 Godot process diagnostic"
Write-Host "Repository : $RepoRoot"
Write-Host "Branch     : $Branch"
Write-Host "Python     : $Python"
Write-Host "Godot      : $Godot"
Write-Host "Timeout    : $TimeoutSeconds s per case"
Write-Host "Purpose    : isolate cwd vs sanitized environment vs capture mode"

& $Python -m kodepoia.kodegodot.process_diagnostic `
    --repo-root $RepoRoot `
    --godot $Godot `
    --output $Output `
    --timeout $TimeoutSeconds

if ($LASTEXITCODE -ne 0) {
    throw "R5 Godot process diagnostic failed before producing usable evidence. Send the complete PowerShell output."
}
if (-not (Test-Path $Output)) {
    throw "Diagnostic report was not created: $Output"
}

$Report = Get-Content $Output -Raw | ConvertFrom-Json
if ($Report.metadata.phase -ne "R5-godot-process-diagnostic") {
    throw "Unexpected diagnostic phase: $($Report.metadata.phase)"
}

Write-Host ""
Write-Host "Diagnostic summary"
foreach ($case in $Report.cases) {
    $status = if ([bool]$case.passed) { "PASS" } else { "FAIL" }
    Write-Host ("{0,-28} {1,-4} {2,7:N2}s timeout={3} rc={4}" -f `
        $case.name, $status, [double]$case.elapsed_seconds, [bool]$case.timed_out, $case.returncode)
}
Write-Host "Evidence   : $Output"
Write-Host ""
Write-Host "This is diagnostic evidence only. Do NOT run full R5 acceptance yet; send this JSON back for review."
