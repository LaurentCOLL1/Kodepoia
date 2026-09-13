@echo off
setlocal EnableExtensions

set "CALLER_CWD=%CD%"
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "CANDIDATE_ROOT=%%~fI"
set "REPO_ROOT="

rem Prefer the root derived from the launcher location. If a local copy or
rem unusual invocation makes %%~dp0 resolve unexpectedly, fall back to the
rem directory from which the operator launched the command.
if exist "%CANDIDATE_ROOT%\scripts\Run-TufReleaseCeremony.ps1" set "REPO_ROOT=%CANDIDATE_ROOT%"
if not defined REPO_ROOT if exist "%CALLER_CWD%\scripts\Run-TufReleaseCeremony.ps1" set "REPO_ROOT=%CALLER_CWD%"
if not defined REPO_ROOT set "REPO_ROOT=%CANDIDATE_ROOT%"

cd /d "%REPO_ROOT%"

set "FINDER=%SCRIPT_DIR%Find-TufPrivateCustody.ps1"
if not exist "%FINDER%" if exist "%REPO_ROOT%\scripts\Find-TufPrivateCustody.ps1" set "FINDER=%REPO_ROOT%\scripts\Find-TufPrivateCustody.ps1"
if not exist "%FINDER%" if exist "%CALLER_CWD%\scripts\Find-TufPrivateCustody.ps1" set "FINDER=%CALLER_CWD%\scripts\Find-TufPrivateCustody.ps1"

set "CEREMONY=%SCRIPT_DIR%Run-TufReleaseCeremony.ps1"
if not exist "%CEREMONY%" if exist "%REPO_ROOT%\scripts\Run-TufReleaseCeremony.ps1" set "CEREMONY=%REPO_ROOT%\scripts\Run-TufReleaseCeremony.ps1"
if not exist "%CEREMONY%" if exist "%CALLER_CWD%\scripts\Run-TufReleaseCeremony.ps1" set "CEREMONY=%CALLER_CWD%\scripts\Run-TufReleaseCeremony.ps1"

if /I "%~1"=="--find-custody" goto FIND_CUSTODY
if /I "%~1"=="find-custody" goto FIND_CUSTODY
if /I "%~1"=="--search-custody" goto FIND_CUSTODY
if /I "%~1"=="search-custody" goto FIND_CUSTODY

goto RUN_CEREMONY

:FIND_CUSTODY
if not exist "%FINDER%" (
  echo.
  echo ERREUR: le helper de recherche TUF est introuvable.
  echo Chemin essaye: "%FINDER%"
  echo Verifiez que scripts\Find-TufPrivateCustody.ps1 existe et mettez le depot a jour.
  echo Cette erreur concerne l'outillage local, pas l'absence d'une garde TUF.
  echo.
  pause
  exit /b 2
)
rem Do not use SHIFT + %%* here: Windows CMD documents that SHIFT does not
rem modify %%*. Forward only the arguments that follow the discovery verb.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%FINDER%" %2 %3 %4 %5 %6 %7 %8 %9
set "EXITCODE=%ERRORLEVEL%"
echo.
if not "%EXITCODE%"=="0" (
  echo La recherche TUF a echoue ou n'a pas trouve une racine unique et complete.
  echo Consultez les indications ci-dessus puis relancez la recherche.
) else (
  echo Recherche terminee. Le chemin affiche peut etre utilise par la ceremonie TUF.
)
echo.
pause
exit /b %EXITCODE%

:RUN_CEREMONY
if not exist "%CEREMONY%" (
  echo.
  echo ERREUR: le script de ceremonie TUF est introuvable.
  echo Chemin essaye: "%CEREMONY%"
  echo Verifiez que scripts\Run-TufReleaseCeremony.ps1 existe et mettez le depot a jour.
  echo.
  pause
  exit /b 2
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%CEREMONY%" -Apply %*
set "EXITCODE=%ERRORLEVEL%"
echo.
if not "%EXITCODE%"=="0" (
  echo La ceremonie est bloquee. Consultez artifacts\tuf_ceremony\ceremony-report.json
  echo N'envoyez jamais de cles, seeds ou passphrases a ChatGPT.
) else (
  echo La ceremonie complete est terminee avec succes.
)
echo.
pause
exit /b %EXITCODE%
