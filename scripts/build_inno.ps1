#Requires -Version 5.1
<#
.SYNOPSIS
  Build MagicEditor Inno Setup installer (requires dist/MagicEditor.exe + ISCC).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/build_inno.ps1
  powershell -ExecutionPolicy Bypass -File scripts/build_inno.ps1 -Version 0.9.2
#>
[CmdletBinding()]
param(
    [string]$Version = "",
    [string]$ExePath = "",
    [switch]$SkipGenerate
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root
. (Join-Path $PSScriptRoot "_me_log.ps1")
trap {
    Write-MeLog "ERROR" $_.Exception.Message
    break
}

function Get-ProductVersion {
    param([string]$Override)
    if ($Override) { return $Override.TrimStart("v") }
    $toml = Join-Path $Root "pyproject.toml"
    if (Test-Path $toml) {
        $m = Select-String -Path $toml -Pattern '^\s*version\s*=\s*"([^"]+)"' | Select-Object -First 1
        if ($m) { return $m.Matches.Groups[1].Value }
    }
    return "0.9.2"
}

function Find-ISCC {
    if ($env:ISCC_PATH -and (Test-Path $env:ISCC_PATH)) {
        return $env:ISCC_PATH
    }
    $cmd = Get-Command ISCC -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "${env:LocalAppData}\Programs\Inno Setup 6\ISCC.exe"
    )
    foreach ($p in $candidates) {
        if ($p -and (Test-Path $p)) { return $p }
    }
    return $null
}

$ProductVersion = Get-ProductVersion -Override $Version
$DistDir = Join-Path $Root "dist"
if (-not $ExePath) {
    $ExePath = Join-Path $DistDir "MagicEditor.exe"
}
if (-not (Test-Path $ExePath)) {
    $alt = Join-Path $Root "MagicEditor.exe"
    if (Test-Path $alt) { $ExePath = $alt }
}
if (-not (Test-Path $ExePath)) {
    Write-MeLog "ERROR" "Missing MagicEditor.exe (looked in dist/ and root)"
    throw "Missing MagicEditor.exe. Build with: scripts/build.ps1 -Exe  (looked in dist/ and root)"
}

$IconPath = Join-Path $Root "resources\icons\app\magiceditor.ico"
if (-not (Test-Path $IconPath)) {
    $IconPath = $ExePath
}

$Iss = Join-Path $Root "packaging\inno\MagicEditor.iss"
if (-not (Test-Path $Iss)) {
    throw "Missing $Iss"
}

if (-not $SkipGenerate) {
    Write-Host "==> Generating associations.issinc" -ForegroundColor Cyan
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\generate_inno_associations.ps1")
    if ($LASTEXITCODE -ne 0) { throw "generate_inno_associations.ps1 failed" }
}

$iscc = Find-ISCC
if (-not $iscc) {
    Write-MeLog "WARNING" "ISCC.exe not found - attempting winget install JRSoftware.InnoSetup"
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        & winget install --id JRSoftware.InnoSetup -e --accept-package-agreements --accept-source-agreements
        $iscc = Find-ISCC
    }
}
if (-not $iscc) {
    $msg = "ISCC.exe not found. Install: winget install JRSoftware.InnoSetup  (Inno makes setup.exe, not .msi)"
    Write-MeLog "ERROR" $msg
    throw $msg
}

$outName = "MagicEditor-$ProductVersion-win64-setup"
Write-Host "MagicEditor Inno Setup" -ForegroundColor Green
Write-Host "  version : $ProductVersion"
Write-Host "  exe     : $ExePath"
Write-Host "  iscc    : $iscc"
Write-Host "  output  : dist\$outName.exe"

# Resolve to absolute paths for ISCC defines
$ExeAbs = (Resolve-Path $ExePath).Path
$IconAbs = (Resolve-Path $IconPath).Path

& $iscc `
    "/DMyAppVersion=$ProductVersion" `
    "/DSourceExe=$ExeAbs" `
    "/DSourceIcon=$IconAbs" `
    $Iss

if ($LASTEXITCODE -ne 0) {
    Write-MeLog "ERROR" "ISCC failed (exit $LASTEXITCODE)"
    throw "ISCC failed (exit $LASTEXITCODE)"
}

$setup = Join-Path $DistDir "$outName.exe"
if (-not (Test-Path $setup)) {
    # Fallback: any setup matching pattern
    $found = Get-ChildItem $DistDir -Filter "MagicEditor-*-win64-setup.exe" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($found) { $setup = $found.FullName }
}
if (-not (Test-Path $setup)) {
    throw "Installer not produced under dist/"
}

$mb = [math]::Round((Get-Item $setup).Length / 1MB, 1)
Write-MeLog "INFO" ("Inno OK: {0} ({1} MB)" -f $setup, $mb)
Write-Host ("  OK: {0} ({1} MB)" -f $setup, $mb) -ForegroundColor Green
