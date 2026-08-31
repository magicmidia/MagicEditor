#Requires -Version 5.1
<#
.SYNOPSIS
  Smoke-check dist/MagicEditor.exe can start (or report environment limits).
#>
[CmdletBinding()]
param(
    [string]$ExePath = ""
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
if (-not $ExePath) {
    $ExePath = Join-Path $Root "dist\MagicEditor.exe"
}

if (-not (Test-Path $ExePath)) {
    Write-Error "Missing $ExePath — run scripts/build.ps1 -Exe first"
    exit 2
}

$env:QT_QPA_PLATFORM = "offscreen"
Write-Host "Smoke: launching $ExePath (offscreen, 8s max)..."

$p = Start-Process -FilePath $ExePath -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 5
if (-not $p.HasExited) {
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    Write-Host "OK: process stayed up (killed after smoke window)" -ForegroundColor Green
    exit 0
}
if ($p.ExitCode -eq 0) {
    Write-Host "OK: process exited cleanly" -ForegroundColor Green
    exit 0
}
Write-Warning "Process exited with code $($p.ExitCode)"
exit 1
