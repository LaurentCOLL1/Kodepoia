[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string[]]$Model,

    [Parameter(Mandatory = $false)]
    [string]$OllamaUrl = "http://127.0.0.1:11434",

    [Parameter(Mandatory = $false)]
    [string]$Output = ".kodepoia/benchmarks/r3-local-acceptance.json",

    [Parameter(Mandatory = $false)]
    [switch]$ListOnly
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $RepoRoot

try {
    Write-Host "Kodepoia R3 local hardware acceptance" -ForegroundColor Cyan
    Write-Host "Repository: $RepoRoot"

    $uri = [Uri]$OllamaUrl
    $allowedHosts = @("127.0.0.1", "localhost", "::1")
    $normalizedHost = $uri.Host.Trim('[', ']').ToLowerInvariant()
    if ($uri.Scheme -notin @("http", "https") -or $normalizedHost -notin $allowedHosts) {
        throw "R3 acceptance requires a loopback Ollama URL (127.0.0.1, localhost or ::1)."
    }

    $pythonVersionText = (& python --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Python was not found in PATH. Kodepoia requires Python 3.12+."
    }
    if ($pythonVersionText -notmatch '^Python\s+(\d+)\.(\d+)') {
        throw "Unable to parse Python version: $pythonVersionText"
    }
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 12)) {
        throw "Python 3.12+ is required. Found: $pythonVersionText"
    }
    Write-Host "Python: $pythonVersionText" -ForegroundColor Green

    $previousPythonPath = $env:PYTHONPATH
    $srcPath = Join-Path $RepoRoot "src"
    if ([string]::IsNullOrWhiteSpace($previousPythonPath)) {
        $env:PYTHONPATH = $srcPath
    }
    else {
        $env:PYTHONPATH = "$srcPath$([IO.Path]::PathSeparator)$previousPythonPath"
    }

    Write-Host "Checking local Ollama..." -ForegroundColor Cyan
    & python -m kodepoia.cli ollama-status --url $OllamaUrl
    if ($LASTEXITCODE -ne 0) {
        throw "Kodepoia could not reach the local Ollama daemon at $OllamaUrl."
    }

    if ($ListOnly -or -not $Model -or $Model.Count -eq 0) {
        Write-Host ""
        Write-Host "No models were benchmarked." -ForegroundColor Yellow
        Write-Host "Re-run with two or three installed models, for example:"
        Write-Host ".\scripts\r3_accept_local.ps1 -Model modelA,modelB"
        Write-Host "or:"
        Write-Host ".\scripts\r3_accept_local.ps1 -Model modelA,modelB,modelC"
        exit 0
    }

    $distinctModels = @($Model | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
    if ($distinctModels.Count -lt 2 -or $distinctModels.Count -gt 3) {
        throw "R3 acceptance requires exactly two or three distinct installed models."
    }

    $arguments = @(
        "-m", "kodepoia.cli", "r3-accept",
        "--url", $OllamaUrl,
        "--output", $Output
    )
    foreach ($candidate in $distinctModels) {
        $arguments += @("--model", $candidate)
    }

    Write-Host "Running R3 benchmark for: $($distinctModels -join ', ')" -ForegroundColor Cyan
    & python @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Kodepoia r3-accept failed. R3 remains incomplete."
    }

    $reportPath = Join-Path $RepoRoot $Output
    if (-not (Test-Path $reportPath)) {
        throw "Acceptance report was not created: $reportPath"
    }

    $report = Get-Content -Raw -Encoding UTF8 $reportPath | ConvertFrom-Json
    if ($report.metadata.phase -ne "R3-local-acceptance") {
        throw "Unexpected acceptance phase in report."
    }
    if ($report.metadata.acceptance_completed -ne $true) {
        throw "Report does not mark acceptance_completed=true."
    }
    if ($report.metadata.loopback_verified -ne $true) {
        throw "Report does not prove loopback_verified=true."
    }
    if ([int]$report.metadata.candidate_count -ne $distinctModels.Count) {
        throw "Candidate count in report does not match the requested models."
    }

    $summaryNames = @($report.summary.PSObject.Properties.Name)
    foreach ($candidate in $distinctModels) {
        if ($candidate -notin $summaryNames) {
            throw "Report is missing benchmark summary for model: $candidate"
        }
    }

    Write-Host ""
    Write-Host "R3 hardware-local evidence generated and structurally verified." -ForegroundColor Green
    Write-Host "Report: $reportPath" -ForegroundColor Green
    Write-Host "R3 must remain PENDING ACCEPTANCE until this report and benchmark results are reviewed."
}
finally {
    if ($null -ne $previousPythonPath) {
        $env:PYTHONPATH = $previousPythonPath
    }
    else {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    }
    Pop-Location
}
