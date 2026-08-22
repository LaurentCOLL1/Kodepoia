param()

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PythonExe = (Get-Command python -ErrorAction Stop).Source
$StudioProcess = $null
$OldQtPlatform = $env:QT_QPA_PLATFORM

Push-Location $RepoRoot
try {
    $Head = (& git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Head)) {
        throw "Unable to resolve the current Git HEAD."
    }

    Write-Host "R6.5 KodeAccessibility local acceptance"
    Write-Host "Source head: $Head"
    Write-Host "Preparing deterministic accessibility reports and manual checklist..."

    $PrepareLines = & $PythonExe -m kodepoia.quality.accessibility_acceptance `
        --repo-root "." --head $Head --prepare
    $PrepareExit = $LASTEXITCODE
    $PrepareText = $PrepareLines -join [Environment]::NewLine
    Write-Host $PrepareText
    if ($PrepareExit -ne 0) {
        throw "R6.5 automated accessibility preparation failed. Preserve the JSON output."
    }
    $Prepare = $PrepareText | ConvertFrom-Json

    Write-Host ""
    Write-Host "Launching KodeStudio in a real interactive Windows session..."
    Write-Host "The script does NOT simulate Narrator and does NOT activate the emergency stop."
    Write-Host "For Narrator checks, use Win+Ctrl+Enter. Speech Recap is Narrator+Alt+X."
    Write-Host "Answer each check from what you actually observe; do not infer PASS."
    Write-Host ""

    Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
    $StudioProcess = Start-Process -FilePath $PythonExe `
        -ArgumentList @("-m", "kodepoia.kodestudio.app") -PassThru
    Start-Sleep -Seconds 2
    if ($StudioProcess.HasExited) {
        throw "KodeStudio exited before the manual accessibility checks could begin."
    }

    $Responses = [ordered]@{}
    foreach ($Check in $Prepare.manual_checks) {
        Write-Host ""
        Write-Host "[$($Check.id)] $($Check.category.ToUpperInvariant())"
        Write-Host "Action:   $($Check.instruction)"
        Write-Host "Expected: $($Check.expected)"
        do {
            $Answer = (Read-Host "Observed result [P]ASS / [F]AIL").Trim().ToLowerInvariant()
        } while ($Answer -notin @("p", "pass", "f", "fail"))

        if ($Answer -in @("p", "pass")) {
            $Status = "pass"
            $Note = ""
        }
        else {
            $Status = "fail"
            $Note = Read-Host "Short failure note (what was missing, wrong, hidden, or unreachable)"
        }
        $Responses[$Check.id] = [ordered]@{
            status = $Status
            note = $Note
        }
    }

    $EvidenceRoot = Join-Path $RepoRoot ".kodepoia\diagnostics\accessibility"
    New-Item -ItemType Directory -Path $EvidenceRoot -Force | Out-Null
    $ResponsePath = Join-Path $EvidenceRoot "r6-5-manual-responses.json"
    $ResponsePayload = [ordered]@{
        schema_version = 1
        source_head = $Head
        responses = $Responses
    }
    $Json = $ResponsePayload | ConvertTo-Json -Depth 10
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText(
        $ResponsePath,
        $Json + [Environment]::NewLine,
        $Utf8NoBom
    )

    Write-Host ""
    Write-Host "Finalizing R6.5 evidence..."
    $FinalizeLines = & $PythonExe -m kodepoia.quality.accessibility_acceptance `
        --repo-root "." --head $Head --finalize --responses $ResponsePath
    $FinalizeExit = $LASTEXITCODE
    $FinalizeText = $FinalizeLines -join [Environment]::NewLine
    Write-Host $FinalizeText
    if ($FinalizeExit -ne 0) {
        throw "R6.5 local acceptance failed. Preserve the printed JSON and do not edit responses to manufacture PASS."
    }

    Write-Host ""
    Write-Host "R6.5 local acceptance completed. You may disable Narrator with Win+Ctrl+Enter if desired."
}
finally {
    if ($null -ne $StudioProcess -and -not $StudioProcess.HasExited) {
        Stop-Process -Id $StudioProcess.Id -ErrorAction SilentlyContinue
    }
    if ($null -eq $OldQtPlatform) {
        Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
    }
    else {
        $env:QT_QPA_PLATFORM = $OldQtPlatform
    }
    Pop-Location
}
