@echo off
REM Build MagicEditor.exe (if needed) and compile the Inno Setup installer.
REM Output: dist\MagicEditor-<version>-win64-setup.exe
REM
REM Prerequisites:
REM   - Python + project deps (or use -SkipDeps after first install)
REM   - Inno Setup 6 (ISCC.exe)  ->  winget install JRSoftware.InnoSetup
REM
REM Usage:
REM   scripts\setup_Install.bat
REM   scripts\setup_Install.bat -SkipDeps
REM   scripts\setup_Install.bat -Version 0.9.1
setlocal EnableExtensions
cd /d "%~dp0.."

echo.
echo ============================================================
echo  MagicEditor - setup installer (EXE + Inno Setup)
echo ============================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" -Exe -Inno %*
set "EC=%ERRORLEVEL%"

if not "%EC%"=="0" (
    echo.
    echo [ERRO] Falha ao gerar o instalador ^(exit %EC%^).
    echo.
    echo Se o Inno Setup nao estiver instalado:
    echo   winget install JRSoftware.InnoSetup
    echo.
    if /i "%~1"=="" pause
    exit /b %EC%
)

echo.
echo ============================================================
echo  OK - instalador em dist\
echo ============================================================
dir /b /o-d "dist\MagicEditor-*-win64-setup.exe" 2>nul
echo.
if /i "%~1"=="" (
    echo Pressione uma tecla para fechar...
    pause >nul
)
exit /b 0
