@echo off
setlocal
set "SCRIPT=%~dp0run_app.ps1"

if not exist "%SCRIPT%" (
  echo Startup script not found: "%SCRIPT%"
  exit /b 1
)

where powershell.exe >nul 2>&1
if errorlevel 1 (
  echo Windows PowerShell was not found. Open PowerShell and run run_app.ps1 manually.
  exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
exit /b %ERRORLEVEL%
