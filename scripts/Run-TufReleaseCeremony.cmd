@echo off
setlocal
cd /d "%~dp0.."
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
