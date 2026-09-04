param(
    [string]$Version = "1.1.0-rc1",
    [string]$Python = "python",
    [string]$Iscc = ""
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

Write-Host "== Kodepoia Windows standalone build =="
& $Python -m pip install -e ".[ui,code,packaging]"

$BuildRoot = Join-Path $Root "build\windows"
$FinalDist = Join-Path $BuildRoot "KodepoiaStudio.dist"
$InstallerOut = Join-Path $Root "dist\windows"
Remove-Item $BuildRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $InstallerOut -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $BuildRoot | Out-Null
New-Item -ItemType Directory -Force -Path $InstallerOut | Out-Null

$NuitkaArgs = @(
    "-m", "nuitka",
    "--standalone",
    "--assume-yes-for-downloads",
    "--enable-plugin=pyside6",
    "--windows-console-mode=disable",
    "--include-package=kodepoia",
    "--output-dir=$BuildRoot",
    "--output-filename=KodepoiaStudio.exe"
)
if (Test-Path (Join-Path $Root "configs")) {
    $NuitkaArgs += "--include-data-dir=$Root\configs=configs"
}
if (Test-Path (Join-Path $Root "schemas")) {
    $NuitkaArgs += "--include-data-dir=$Root\schemas=schemas"
}
$NuitkaArgs += "src\kodepoia\kodestudio\app_v11_entry.py"

& $Python @NuitkaArgs
if ($LASTEXITCODE -ne 0) {
    throw "Nuitka failed with exit code $LASTEXITCODE"
}

$CandidateDist = Get-ChildItem -Path $BuildRoot -Directory -Filter "*.dist" |
    Where-Object { Test-Path (Join-Path $_.FullName "KodepoiaStudio.exe") } |
    Select-Object -First 1
if (-not $CandidateDist) {
    throw "Standalone KodepoiaStudio distribution was not produced."
}
if ($CandidateDist.FullName -ne $FinalDist) {
    Remove-Item $FinalDist -Recurse -Force -ErrorAction SilentlyContinue
    Move-Item $CandidateDist.FullName $FinalDist
}
$StandaloneExe = Join-Path $FinalDist "KodepoiaStudio.exe"
if (-not (Test-Path $StandaloneExe)) {
    throw "Missing standalone executable: $StandaloneExe"
}

if (-not $Iscc) {
    $Candidates = @(
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
        (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
    ) | Where-Object { $_ -and (Test-Path $_) }
    $Iscc = $Candidates | Select-Object -First 1
}
if (-not $Iscc -or -not (Test-Path $Iscc)) {
    throw "Inno Setup 6 compiler (ISCC.exe) was not found."
}

$Iss = Join-Path $Root "packaging\windows\Kodepoia.iss"
# Inno Setup 6.x accepts the ISPP short form -dNAME=VALUE across the
# supported 6.x line. Keep it instead of the newer long --define form so
# Chocolatey runners pinned to e.g. 6.7.1 remain compatible.
& $Iscc "-dAppVersion=$Version" "-dSourceDir=$FinalDist" $Iss
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE"
}

$Setup = Join-Path $InstallerOut "KodepoiaSetup.exe"
if (-not (Test-Path $Setup)) {
    throw "Expected installer was not produced: $Setup"
}
if ((Get-Item $Setup).Length -le 0) {
    throw "KodepoiaSetup.exe is empty."
}

$Hash = (Get-FileHash $Setup -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host "Installer: $Setup"
Write-Host "SHA-256: $Hash"
@{
    version = $Version
    installer = "KodepoiaSetup.exe"
    sha256 = $Hash
    standalone_executable = "KodepoiaStudio.exe"
    production_signed = $false
} | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $InstallerOut "installer-manifest.json")
