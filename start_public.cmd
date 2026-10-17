@echo off
rem Double-click to start the Attire Checker and its public Cloudflare address.
rem Runs start_public.ps1 without needing to change Windows' script execution policy.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_public.ps1"
pause
