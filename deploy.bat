@echo off
rem Lance deploy.ps1 sans avoir a modifier la politique d execution de PowerShell.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy.ps1" %*
if errorlevel 1 pause
