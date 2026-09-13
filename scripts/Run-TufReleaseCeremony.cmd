@echo off
setlocal
cd /d "%~dp0.."

if /I "%~1"=="--find-custody" goto FIND_CUSTODY
if /I "%~1"=="find-custody" goto FIND_CUSTODY
if /I "%~1"=="--search-custody" goto FIND_CUSTODY
if /I "%~1"=="search-custody" goto FIND_CUSTODY

goto RUN_CEREMONY

:FIND_CUSTODY
shift
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Find-TufPrivateCustody.ps1" %*
set "EXITCODE=%ERRORLEVEL%"
echo.
if not "%EXITCODE%"=="0" (
  echo La recherche n'a pas trouve une racine TUF unique et complete.
  echo Consultez les indications ci-dessus puis relancez la recherche.
) else (
  echo Recherche terminee. Le chemin affiche peut etre utilise par la ceremonie TUF.
)
echo.
pause
exit /b %EXITCODE%

:RUN_CEREMONY
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-TufReleaseCeremony.ps1" -Apply %*
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
