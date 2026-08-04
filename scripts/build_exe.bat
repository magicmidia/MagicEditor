@echo off
REM Prefer root build.bat — produces MagicEditor.exe at project root.
setlocal
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" -Exe %*
exit /b %ERRORLEVEL%
