[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string[]]$SearchRoot,

    [Parameter(Mandatory = $false)]
    [string]$RepositoryRoot
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$SnapshotSeedName = "TUF_SNAPSHOT_ED25519_SEED_B64.txt"
$TimestampSeedName = "TUF_TIMESTAMP_ED25519_SEED_B64.txt"

function Test-PathInside {
    param(
        [string]$Path,
        [string]$Parent
    )
    $resolvedPath = [System.IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
    $resolvedParent = [System.IO.Path]::GetFullPath($Parent).TrimEnd('\', '/')
    if ($resolvedPath.Equals($resolvedParent, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }
    return $resolvedPath.StartsWith(
        $resolvedParent + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase
    )
}

function Get-NearestCustodyRoot {
    param(
        [System.IO.FileInfo]$SnapshotSeed,
        [string]$RepoRoot
    )

    $directory = $SnapshotSeed.Directory
    while ($null -ne $directory) {
        $candidate = $directory.FullName
        if (-not (Test-PathInside -Path $candidate -Parent $RepoRoot)) {
            $timestamp = Get-ChildItem `
                -LiteralPath $candidate `
                -Recurse `
                -File `
                -Filter $TimestampSeedName `
                -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if ($null -ne $timestamp) {
                $pem = Get-ChildItem `
                    -LiteralPath $candidate `
                    -Recurse `
                    -File `
                    -Filter "*.pem" `
                    -ErrorAction SilentlyContinue |
                    Select-Object -First 1
                if ($null -ne $pem) {
                    return $candidate
                }
            }
        }
        $directory = $directory.Parent
    }
    return $null
}

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
else {
    $RepositoryRoot = (Resolve-Path -LiteralPath $RepositoryRoot).Path
}

$roots = @()
if ($null -ne $SearchRoot -and $SearchRoot.Count -gt 0) {
    foreach ($root in $SearchRoot) {
        try {
            $roots += (Resolve-Path -LiteralPath $root -ErrorAction Stop).Path
        }
        catch {
            Write-Warning "Racine de recherche inaccessible ignorée : $root"
        }
    }
}
else {
    $roots = @(
        Get-PSDrive -PSProvider FileSystem |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_.Root) -and (Test-Path -LiteralPath $_.Root) } |
            ForEach-Object { $_.Root }
    )
}

if ($roots.Count -eq 0) {
    Write-Error "Aucun lecteur/répertoire de fichiers accessible n'a été trouvé pour la recherche."
    exit 2
}

$candidates = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)

Write-Host ""
Write-Host "=== Recherche de la racine privée TUF ==="
Write-Host "Recherche par noms de fichiers uniquement ; aucun contenu de clé/seed n'est lu ni affiché."
Write-Host "Le dépôt Kodepoia est explicitement exclu des résultats."
Write-Host ""

foreach ($root in $roots) {
    Write-Host "Recherche sur : $root"
    $snapshotSeeds = @(
        Get-ChildItem `
            -LiteralPath $root `
            -Recurse `
            -File `
            -Filter $SnapshotSeedName `
            -ErrorAction SilentlyContinue
    )
    foreach ($snapshotSeed in $snapshotSeeds) {
        $candidate = Get-NearestCustodyRoot -SnapshotSeed $snapshotSeed -RepoRoot $RepositoryRoot
        if (-not [string]::IsNullOrWhiteSpace($candidate)) {
            [void]$candidates.Add($candidate)
        }
    }
}

if ($candidates.Count -eq 0) {
    Write-Host ""
    Write-Host "Aucune racine privée TUF complète n'a été trouvée." -ForegroundColor Yellow
    Write-Host "Une garde complète doit contenir, sous une même racine :"
    Write-Host "- $SnapshotSeedName"
    Write-Host "- $TimestampSeedName"
    Write-Host "- au moins un fichier .pem"
    Write-Host "Vous pouvez limiter la recherche, par exemple :"
    Write-Host '  .\scripts\Run-TufReleaseCeremony.cmd --find-custody -SearchRoot M:\,G:\'
    exit 2
}

$ordered = @($candidates | Sort-Object)
Write-Host ""
if ($ordered.Count -eq 1) {
    Write-Host "Racine privée TUF trouvée :" -ForegroundColor Green
    Write-Host $ordered[0] -ForegroundColor Green
    Write-Host ""
    Write-Host "Copiez ce chemin lorsque Run-TufReleaseCeremony.cmd demande la racine privée de garde TUF."
    exit 0
}

Write-Host "$($ordered.Count) racines privées TUF possibles ont été trouvées :" -ForegroundColor Yellow
for ($index = 0; $index -lt $ordered.Count; $index++) {
    Write-Host ("[{0}] {1}" -f ($index + 1), $ordered[$index])
}
Write-Host ""
Write-Host "Vérifiez laquelle est l'autorité de production avant de lancer la cérémonie."
Write-Host "Le lanceur refusera ensuite toute clé non autorisée par Root."
exit 3
