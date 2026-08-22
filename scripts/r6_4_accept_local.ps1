param()

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if ([string]::IsNullOrWhiteSpace($env:KODEPOIA_GODOT_EXE)) {
    throw "KODEPOIA_GODOT_EXE is required and must point to the accepted Godot 4.7.x executable."
}
if (-not (Test-Path -LiteralPath $env:KODEPOIA_GODOT_EXE -PathType Leaf)) {
    throw "KODEPOIA_GODOT_EXE does not point to a file: $env:KODEPOIA_GODOT_EXE"
}

Push-Location $RepoRoot
try {
    python -m kodepoia.quality.visual_acceptance --repo-root "." --godot $env:KODEPOIA_GODOT_EXE
    if ($LASTEXITCODE -ne 0) {
        throw "R6.4 local acceptance failed with exit code $LASTEXITCODE. Preserve the printed JSON and generated diff/report; do not replace the baseline or change thresholds."
    }
}
finally {
    Pop-Location
}
