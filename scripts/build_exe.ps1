# Build MagicEditor.exe at the repository root.
# Usage: pwsh -File scripts/build_exe.ps1

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Write-Host "==> Installing package + PyInstaller..."
python -m pip install -e ".[dev]" -q

Write-Host "==> Cleaning previous build artifacts..."
if (Test-Path "$Root\build") { Remove-Item -Recurse -Force "$Root\build" }
# Keep work dir clean; exe is written to root via --distpath .
if (Test-Path "$Root\MagicEditor.exe") {
    Remove-Item -Force "$Root\MagicEditor.exe"
}

Write-Host "==> Running PyInstaller (onefile, windowed)..."
python -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath "$Root" `
    --workpath "$Root\build\pyinstaller" `
    "$Root\MagicEditor.spec"

if (-not (Test-Path "$Root\MagicEditor.exe")) {
    Write-Error "Build failed: MagicEditor.exe not found at repo root."
    exit 1
}

$size = (Get-Item "$Root\MagicEditor.exe").Length / 1MB
Write-Host ("==> OK: {0}\MagicEditor.exe ({1:N1} MB)" -f $Root, $size)
