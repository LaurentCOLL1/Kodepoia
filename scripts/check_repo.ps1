$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$checker = Join-Path $scriptDir 'check_repo.py'
python $checker
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
