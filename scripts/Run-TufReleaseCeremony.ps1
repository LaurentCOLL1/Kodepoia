[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$PublicVersion,

    [Parameter(Mandatory = $false)]
    [string]$SourceSha,

    [Parameter(Mandatory = $false)]
    [string]$AssetPath,

    [Parameter(Mandatory = $false)]
    [string]$PrivateCustodyDirectory,

    [Parameter(Mandatory = $false)]
    [string]$ExpectedAssetSha256,

    [Parameter(Mandatory = $false)]
    [Nullable[long]]$ExpectedAssetSize,

    [Parameter(Mandatory = $false)]
    [string]$ExpectedRootSha256,

    [Parameter(Mandatory = $false)]
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Resolve-RequiredValue {
    param(
        [string]$Value,
        [string]$Prompt
    )
    if (-not [string]::IsNullOrWhiteSpace($Value)) {
        return $Value.Trim()
    }
    $answer = Read-Host $Prompt
    if ([string]::IsNullOrWhiteSpace($answer)) {
        throw "Valeur obligatoire manquante : $Prompt"
    }
    return $answer.Trim()
}

function Resolve-PythonCommand {
    $candidates = @(
        @{ File = "python"; Prefix = @() },
        @{ File = "py"; Prefix = @("-3.12") }
    )
    foreach ($candidate in $candidates) {
        try {
            $probeArgs = @($candidate.Prefix) + @("-c", "import sys; assert sys.version_info >= (3, 12)")
            & $candidate.File @probeArgs 2>$null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        }
        catch {
            continue
        }
    }
    throw "Python 3.12+ est introuvable. Activez l'environnement virtuel Kodepoia puis relancez ce fichier."
}

function Resolve-UniquePrivateFile {
    param(
        [string]$Root,
        [string]$FileName,
        [string]$Label
    )
    $matches = @(
        Get-ChildItem -LiteralPath $Root -Recurse -File -Filter $FileName -ErrorAction Stop
    )
    if ($matches.Count -eq 0) {
        throw "$Label privé introuvable sous la racine de garde TUF."
    }
    if ($matches.Count -gt 1) {
        throw "Plusieurs fichiers $FileName ont été trouvés sous la racine de garde. Conservez une seule copie autoritative avant de relancer."
    }
    return $matches[0].FullName
}

function Adopt-ManifestValue {
    param(
        [string]$CurrentValue,
        [string]$ManifestValue,
        [string]$Label
    )
    if ([string]::IsNullOrWhiteSpace($ManifestValue)) {
        return $CurrentValue
    }
    if (-not [string]::IsNullOrWhiteSpace($CurrentValue) -and $CurrentValue.Trim() -ne $ManifestValue.Trim()) {
        throw "$Label fourni ne correspond pas à installer-manifest.json."
    }
    return $ManifestValue.Trim()
}

function Write-RedactedPreflightReport {
    param(
        [string]$ReportPath,
        [string]$SummaryPath,
        [string]$Stage
    )
    try {
        $reportDirectory = Split-Path -Parent $ReportPath
        $summaryDirectory = Split-Path -Parent $SummaryPath
        New-Item -ItemType Directory -Force -Path $reportDirectory | Out-Null
        New-Item -ItemType Directory -Force -Path $summaryDirectory | Out-Null
        $payload = [ordered]@{
            format = "kodepoia-tuf-release-ceremony"
            schema_version = 1
            status = "BLOCKED"
            generation = $null
            checks = @()
            errors_encountered = @(
                [ordered]@{
                    code = "POWERSHELL_PREFLIGHT_BLOCKED"
                    message = "La cérémonie s'est arrêtée pendant le précontrôle : $Stage. Le détail local a été volontairement exclu de ce rapport partageable."
                    auto_fixable = $false
                    resolution = "Consultez le message affiché dans la console locale. Partagez uniquement ce rapport avec ChatGPT et ne partagez jamais les chemins privés, PEM, seeds ou passphrases."
                }
            )
            automatic_fixes = @()
            private_material_in_report = $false
            private_key_paths_in_report = $false
            secret_values_emitted = $false
        }
        $payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
        @(
            "Kodepoia TUF release ceremony: BLOCKED",
            "Précontrôle bloqué à l'étape : $Stage.",
            "Consultez ceremony-report.json et partagez uniquement ce rapport avec ChatGPT."
        ) | Set-Content -LiteralPath $SummaryPath -Encoding UTF8
    }
    catch {
        # The local console remains authoritative if even the shareable report cannot be written.
    }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$reportPath = Join-Path $repoRoot "artifacts\tuf_ceremony\ceremony-report.json"
$summaryPath = Join-Path $repoRoot "artifacts\tuf_ceremony\ceremony-summary.txt"
$currentStage = "initialisation"

Push-Location $repoRoot
try {
    $currentStage = "sélection de l'installateur et de la garde privée"
    $AssetPath = Resolve-RequiredValue $AssetPath "Chemin complet de KodepoiaSetup.exe"
    $PrivateCustodyDirectory = Resolve-RequiredValue $PrivateCustodyDirectory "Racine privée de garde TUF (hors dépôt)"

    $currentStage = "validation de l'installateur"
    $resolvedAsset = (Resolve-Path -LiteralPath $AssetPath).Path
    if ((Get-Item -LiteralPath $resolvedAsset).Name -ne "KodepoiaSetup.exe") {
        throw "L'asset attendu doit s'appeler exactement KodepoiaSetup.exe."
    }

    $currentStage = "validation de installer-manifest.json"
    $manifestPath = Join-Path (Split-Path -Parent $resolvedAsset) "installer-manifest.json"
    $manifestLoaded = $false
    if (Test-Path -LiteralPath $manifestPath -PathType Leaf) {
        $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
        if ([string]$manifest.installer -ne "KodepoiaSetup.exe") {
            throw "installer-manifest.json ne décrit pas KodepoiaSetup.exe."
        }
        $PublicVersion = Adopt-ManifestValue $PublicVersion ([string]$manifest.public_version) "La version publique"
        $SourceSha = Adopt-ManifestValue $SourceSha ([string]$manifest.source_sha) "Le SHA source"
        $ExpectedAssetSha256 = Adopt-ManifestValue $ExpectedAssetSha256 ([string]$manifest.sha256) "Le SHA-256 de l'installateur"
        $manifestLoaded = $true
    }

    $currentStage = "validation de l'identité de release"
    $PublicVersion = Resolve-RequiredValue $PublicVersion "Version publique (ex. 1.1.0-rc6)"
    $SourceSha = Resolve-RequiredValue $SourceSha "SHA source exact (40 caractères)"
    if ($null -eq $ExpectedAssetSize) {
        $ExpectedAssetSize = [long](Get-Item -LiteralPath $resolvedAsset).Length
    }

    $currentStage = "validation de la racine de garde TUF"
    $resolvedCustody = (Resolve-Path -LiteralPath $PrivateCustodyDirectory).Path
    if ($resolvedCustody.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "La racine privée TUF doit être située hors du dépôt Kodepoia."
    }

    $currentStage = "découverte des seeds Snapshot/Timestamp"
    $snapshotSecretFile = Resolve-UniquePrivateFile `
        -Root $resolvedCustody `
        -FileName "TUF_SNAPSHOT_ED25519_SEED_B64.txt" `
        -Label "Seed Snapshot"
    $timestampSecretFile = Resolve-UniquePrivateFile `
        -Root $resolvedCustody `
        -FileName "TUF_TIMESTAMP_ED25519_SEED_B64.txt" `
        -Label "Seed Timestamp"

    $currentStage = "chargement protégé des seeds Snapshot/Timestamp"
    $snapshotSecret = (Get-Content -LiteralPath $snapshotSecretFile -Raw).Trim()
    $timestampSecret = (Get-Content -LiteralPath $timestampSecretFile -Raw).Trim()
    if ([string]::IsNullOrWhiteSpace($snapshotSecret) -or [string]::IsNullOrWhiteSpace($timestampSecret)) {
        throw "Un seed Snapshot/Timestamp privé est vide."
    }

    $currentStage = "détection de Python 3.12+"
    $python = Resolve-PythonCommand
    $arguments = @(
        "scripts/tuf_release_ceremony_safe.py",
        "--public-version", $PublicVersion,
        "--source-sha", $SourceSha,
        "--asset", $resolvedAsset,
        "--offline-key-dir", $resolvedCustody,
        "--report", $reportPath,
        "--summary", $summaryPath
    )

    if (-not [string]::IsNullOrWhiteSpace($ExpectedAssetSha256)) {
        $arguments += @("--expected-asset-sha256", $ExpectedAssetSha256.Trim())
    }
    if ($null -ne $ExpectedAssetSize) {
        $arguments += @("--expected-asset-size", $ExpectedAssetSize.Value.ToString())
    }
    if (-not [string]::IsNullOrWhiteSpace($ExpectedRootSha256)) {
        $arguments += @("--expected-root-sha256", $ExpectedRootSha256.Trim())
    }
    if ($Apply) {
        $arguments += "--apply"
    }

    # The values exist only in this process and child Python process. Never print them.
    $env:TUF_SNAPSHOT_ED25519_SEED_B64 = $snapshotSecret
    $env:TUF_TIMESTAMP_ED25519_SEED_B64 = $timestampSecret
    $snapshotSecret = $null
    $timestampSecret = $null

    Write-Host ""
    Write-Host "=== Kodepoia TUF Release Ceremony ==="
    Write-Host "Version : $PublicVersion"
    Write-Host "Source  : $SourceSha"
    Write-Host "Asset   : $resolvedAsset"
    Write-Host "Manifest: $(if ($manifestLoaded) { 'détecté et vérifié' } else { 'absent - valeurs fournies manuellement' })"
    Write-Host "Mode    : $(if ($Apply) { 'APPLY' } else { 'STAGE/VERIFY' })"
    Write-Host "Les clés/seeds privés ne seront jamais affichés ni écrits dans le rapport."
    Write-Host ""

    $currentStage = "cérémonie TUF Python"
    $pythonArgs = @($python.Prefix) + $arguments
    & $python.File @pythonArgs
    $exitCode = $LASTEXITCODE

    Write-Host ""
    if (Test-Path -LiteralPath $summaryPath -PathType Leaf) {
        Write-Host "--- Résumé ---"
        Get-Content -LiteralPath $summaryPath
    }
    if ($exitCode -eq 0) {
        Write-Host "CEREMONIE TERMINEE AVEC SUCCES"
        Write-Host "Rapport : $reportPath"
    }
    else {
        Write-Host "CEREMONIE BLOQUEE" -ForegroundColor Red
        Write-Host "Rapport sûr pour ChatGPT : $reportPath"
        Write-Host "N'envoyez jamais la racine privée, les PEM, les seeds ou la passphrase."
    }
    exit $exitCode
}
catch {
    Write-RedactedPreflightReport -ReportPath $reportPath -SummaryPath $summaryPath -Stage $currentStage
    Write-Host "CEREMONIE BLOQUEE AVANT SIGNATURE" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Rapport sûr pour ChatGPT : $reportPath"
    Write-Host "Corrigez ce point puis relancez exactement le même fichier."
    exit 1
}
finally {
    Remove-Item Env:TUF_SNAPSHOT_ED25519_SEED_B64 -ErrorAction SilentlyContinue
    Remove-Item Env:TUF_TIMESTAMP_ED25519_SEED_B64 -ErrorAction SilentlyContinue
    Pop-Location
}
