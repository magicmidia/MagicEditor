@echo off
REM Build MagicEditor.exe (if needed) and compile the Inno Setup installer.
REM Output: dist\MagicEditor-<version>-win64-setup.exe
REM (Inno Setup does NOT produce .msi - that is WiX: scripts\build.ps1 -Msi)
REM
REM Prerequisites:
REM   - Python + project deps (or use -SkipDeps after first install)
REM   - Inno Setup 6 (ISCC.exe)  ->  winget install JRSoftware.InnoSetup
REM
REM Usage:
REM   scripts\setup_Install.bat
REM   scripts\setup_Install.bat -SkipDeps
REM   scripts\setup_Install.bat -Version 0.9.2
setlocal EnableExtensions
cd /d "%~dp0.."
set "LOG=%CD%\MagicEditor.log"

echo.
echo ============================================================
echo  MagicEditor - setup installer (EXE + Inno Setup)
echo  Log: %LOG%
echo ============================================================
echo.
>>"%LOG%" echo %DATE% %TIME% [INFO] build: setup_Install.bat start

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" -Exe -Inno %*
set "EC=%ERRORLEVEL%"

if not "%EC%"=="0" (
    echo.
    echo [ERRO] Falha ao gerar o instalador ^(exit %EC%^).
    echo Detalhes em: %LOG%
    echo.
    echo Se o Inno Setup nao estiver instalado:
    echo   winget install JRSoftware.InnoSetup
    echo.
    echo Inno gera:  dist\MagicEditor-*-win64-setup.exe
    echo MSI ^(WiX^):  powershell -File scripts\build.ps1 -Msi
    echo.
    >>"%LOG%" echo %DATE% %TIME% [ERROR] build: setup_Install.bat failed exit %EC%
    echo Pressione uma tecla para fechar...
    pause >nul
    exit /b %EC%
)

set "FOUND="
for %%F in ("dist\MagicEditor-*-win64-setup.exe") do (
    if exist "%%~fF" set "FOUND=%%~fF"
)

if not defined FOUND (
    echo.
    echo [ERRO] Build terminou sem gerar dist\MagicEditor-*-win64-setup.exe
    echo Inno Setup produz .exe, nao .msi. Veja %LOG%
    echo.
    >>"%LOG%" echo %DATE% %TIME% [ERROR] build: setup exe missing after success exit
    echo Pressione uma tecla para fechar...
    pause >nul
    exit /b 1
)

echo.
echo ============================================================
echo  OK - instalador Inno:
echo  %FOUND%
echo  Log: %LOG%
echo ============================================================
dir /b /o-d "dist\MagicEditor-*-win64-setup.exe" 2>nul
echo.
>>"%LOG%" echo %DATE% %TIME% [INFO] build: setup_Install.bat OK %FOUND%
echo Pressione uma tecla para fechar...
pause >nul
exit /b 0
