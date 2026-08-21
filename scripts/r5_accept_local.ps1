param(
    [string]$GodotPath = "",
    [switch]$ProbeOnly,
    [int]$LspPort = 6005,
    [int]$DapPort = 6006,
    [int]$DebugPort = 6007
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

function Resolve-Python {
    $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) { return $venvPython }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $cmd) { throw "Python was not found. Install Python 3.12+ or create .venv." }
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
    throw "Godot was not found on PATH. Re-run with -GodotPath 'C:\path\to\Godot_v4.7.x-stable_win64.exe'."
}

$Python = Resolve-Python
$Godot = Resolve-Godot $GodotPath

$VersionText = & $Python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
$VersionParts = $VersionText.Trim().Split('.')
if ([int]$VersionParts[0] -lt 3 -or ([int]$VersionParts[0] -eq 3 -and [int]$VersionParts[1] -lt 12)) {
    throw "Python 3.12+ is required. Found $VersionText"
}

$GodotVersion = (& $Godot --version | Select-Object -First 1).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($GodotVersion)) {
    throw "Unable to query Godot version from: $Godot"
}
if ($GodotVersion -notmatch '^4\.7(?:\.|$)') {
    throw "Kodepoia R5 requires Godot 4.7.x. Found '$GodotVersion'. Do not continue with another Godot family."
}

foreach ($port in @($LspPort, $DapPort, $DebugPort)) {
    if ($port -lt 1024 -or $port -gt 49151) {
        throw "R5 LSP/DAP/debug ports must be between 1024 and 49151. Found $port."
    }
}
if (@($LspPort, $DapPort, $DebugPort | Select-Object -Unique).Count -ne 3) {
    throw "R5 LSP, DAP and debug ports must be distinct."
}

$Branch = (& git branch --show-current).Trim()
if ($Branch -ne "agent/r5-6-governed-acceptance") {
    throw "Expected branch agent/r5-6-governed-acceptance, found '$Branch'. Do not run R5 acceptance from another branch."
}

$env:PYTHONPATH = Join-Path $RepoRoot "src"
$Output = Join-Path $RepoRoot ".kodepoia\benchmarks\r5-local-acceptance.json"

$Args = @(
    "-m", "kodepoia.kodegodot.accept_cli",
    "--repo-root", $RepoRoot,
    "--godot", $Godot,
    "--output", $Output,
    "--lsp-port", "$LspPort",
    "--dap-port", "$DapPort",
    "--debug-port", "$DebugPort"
)
if ($ProbeOnly) { $Args += "--probe-only" }

Write-Host "Kodepoia R5 local acceptance"
Write-Host "Repository : $RepoRoot"
Write-Host "Branch     : $Branch"
Write-Host "Python     : $VersionText"
Write-Host "Godot      : $Godot"
Write-Host "Godot ver. : $GodotVersion"
Write-Host "Ports      : LSP=$LspPort DAP=$DapPort DEBUG=$DebugPort"

& $Python @Args
$ExitCode = $LASTEXITCODE

if (-not (Test-Path $Output)) {
    throw "R5 report was not created: $Output"
}

$Report = Get-Content $Output -Raw | ConvertFrom-Json
if ($Report.metadata.phase -ne "R5-local-acceptance") {
    throw "Unexpected R5 report phase: $($Report.metadata.phase)"
}

Write-Host "Evidence    : $Output"
Write-Host "Passed      : $($Report.summary.passed)/$($Report.summary.total)"
Write-Host "Failed      : $($Report.summary.failed)"

if ($ProbeOnly) {
    if ($ExitCode -ne 0) {
        throw "R5 probe failed. Send the complete PowerShell output and r5-local-acceptance.json."
    }
    Write-Host "Probe completed. Do not merge R5.6 yet."
    exit 0
}

if ($ExitCode -ne 0 -or -not [bool]$Report.metadata.acceptance_completed -or [int]$Report.summary.failed -ne 0) {
    throw "R5 local acceptance is not complete. Send the complete PowerShell output and r5-local-acceptance.json."
}

Write-Host "R5 LOCAL ACCEPTANCE COMPLETED. Do not edit R5_STATUS.md or merge the PR manually; send the report back for review."
