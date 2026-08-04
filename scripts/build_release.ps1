#Requires -Version 5.1
<#
.SYNOPSIS
  Full release kit: clean → optional tests → EXE → Portable → MSI → SHA256SUMS.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/build_release.ps1
  powershell -ExecutionPolicy Bypass -File scripts/build_release.ps1 -SkipTests -Version 0.2.0
#>
[CmdletBinding()]
param(
    [switch]$SkipTests,
    [switch]$SkipDeps,
    [string]$Version = "",
    [switch]$Sign
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root
$Dist = Join-Path $Root "dist"

Write-Host "== MagicEditor release kit ==" -ForegroundColor Cyan

if (-not $SkipTests) {
    Write-Host "Running pytest (core + services, quiet)..." -ForegroundColor Yellow
    $env:TMP = Join-Path $env:TEMP "me-pytest"
    $env:TEMP = $env:TMP
    New-Item -ItemType Directory -Force -Path $env:TMP | Out-Null
    & python -m pytest tests/core tests/services/test_portable.py tests/services/test_file_associations.py tests/services/test_performance_info.py -q --tb=line
    if ($LASTEXITCODE -ne 0) {
        throw "pytest failed (exit $LASTEXITCODE)"
    }
}

$buildArgs = @("-All")
if ($SkipDeps) { $buildArgs += "-SkipDeps" }
if ($Version) { $buildArgs += @("-Version", $Version) }

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "build.ps1") @buildArgs
if ($LASTEXITCODE -ne 0) {
    throw "build.ps1 failed"
}

# Checksums
$sums = Join-Path $Dist "SHA256SUMS.txt"
$lines = @()
Get-ChildItem $Dist -File | Where-Object { $_.Extension -in ".exe", ".msi", ".zip" } | ForEach-Object {
    $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $lines += "$hash  $($_.Name)"
    Write-Host "  $($_.Name)  $hash"
}
$lines -join "`n" | Set-Content -Path $sums -Encoding utf8
Write-Host "Wrote $sums" -ForegroundColor Green

if ($Sign -and $env:ME_SIGN_CERT) {
    Write-Host "Signing with ME_SIGN_CERT..." -ForegroundColor Yellow
    Get-ChildItem $Dist -Filter "*.exe" | ForEach-Object {
        & signtool sign /fd SHA256 /a /f $env:ME_SIGN_CERT $_.FullName
    }
} elseif ($Sign) {
    Write-Warning "ME_SIGN_CERT not set — skip code signing"
}

Write-Host "Release kit done." -ForegroundColor Green
