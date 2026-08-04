@echo off
REM Build MagicEditor.exe at the project root (also copies to dist\ for packaging).
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build.ps1" -Exe %*
set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" (
    echo.
    echo Build failed with exit code %EC%.
    REM Keep window open when double-clicked so the error is readable.
    if /i "%~1"=="" pause
)
exit /b %EC%
