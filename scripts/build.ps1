#Requires -Version 5.1
<#
.SYNOPSIS
  Build MagicEditor release artifacts: EXE, Portable ZIP, and/or MSI.

.DESCRIPTION
  Outputs land under dist/ (gitignored). Never commits binaries.

  Targets:
    -Exe       PyInstaller onefile → dist/MagicEditor.exe
    -Portable  ZIP with exe + README → dist/MagicEditor-Portable-<ver>-win64.zip
    -Msi       WiX installer → dist/MagicEditor-<ver>-win64.msi
    -All       Exe + Portable + Msi (Msi skipped with warning if WiX missing)

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -All
  powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe -Portable
  powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Msi
#>
[CmdletBinding()]
param(
    [switch]$Exe,
    [switch]$Portable,
    [switch]$Msi,
    [switch]$All,
    [switch]$SkipDeps,
    [switch]$KeepWork,
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if ($All) {
    $Exe = $true
    $Portable = $true
    $Msi = $true
}
if (-not ($Exe -or $Portable -or $Msi)) {
    # Default: onefile exe (most common for local delivery)
    $Exe = $true
}

function Get-ProductVersion {
    param([string]$Override)
    if ($Override) { return $Override.TrimStart("v") }
    $toml = Join-Path $Root "pyproject.toml"
    if (Test-Path $toml) {
        $m = Select-String -Path $toml -Pattern '^\s*version\s*=\s*"([^"]+)"' | Select-Object -First 1
        if ($m) { return $m.Matches.Groups[1].Value }
    }
    return "0.1.0"
}

function Ensure-Dir([string]$Path) {
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

$ProductVersion = Get-ProductVersion -Override $Version
$DistDir = Join-Path $Root "dist"
$WorkDir = Join-Path $Root "build\pyinstaller"
$ExePath = Join-Path $DistDir "MagicEditor.exe"
$SpecPath = Join-Path $Root "MagicEditor.spec"

Write-Host "MagicEditor build" -ForegroundColor Green
Write-Host "  root     : $Root"
Write-Host "  version  : $ProductVersion"
Write-Host "  targets  :$(if($Exe){' exe'})$(if($Portable){' portable'})$(if($Msi){' msi'})"

# --- Dependencies -------------------------------------------------------
if (-not $SkipDeps) {
    Write-Step "Installing package + PyInstaller (editable + dev extras)"
    python -m pip install -e ".[dev]" -q
    if ($LASTEXITCODE -ne 0) {
        throw "pip install failed (exit $LASTEXITCODE)"
    }
}

Ensure-Dir $DistDir

# --- EXE (PyInstaller onefile) ------------------------------------------
if ($Exe -or $Portable -or $Msi) {
    if (-not (Test-Path $SpecPath)) {
        throw "Missing MagicEditor.spec at $SpecPath"
    }

    Write-Step "PyInstaller onefile → dist/MagicEditor.exe"
    if (-not $KeepWork -and (Test-Path (Join-Path $Root "build"))) {
        Remove-Item -Recurse -Force (Join-Path $Root "build") -ErrorAction SilentlyContinue
    }
    if (Test-Path $ExePath) {
        Remove-Item -Force $ExePath
    }
    # Legacy root exe (old builds) — remove so nobody commits it by mistake
    $legacyRoot = Join-Path $Root "MagicEditor.exe"
    if (Test-Path $legacyRoot) {
        Remove-Item -Force $legacyRoot -ErrorAction SilentlyContinue
    }

    python -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath $DistDir `
        --workpath $WorkDir `
        $SpecPath

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed (exit $LASTEXITCODE)"
    }
    if (-not (Test-Path $ExePath)) {
        throw "Build failed: $ExePath not found"
    }

    $sizeMb = [math]::Round((Get-Item $ExePath).Length / 1MB, 1)
    Write-Host "  OK: $ExePath ($sizeMb MB)" -ForegroundColor Green
}

# --- Portable ZIP -------------------------------------------------------
if ($Portable) {
    Write-Step "Portable ZIP"
    if (-not (Test-Path $ExePath)) {
        throw "Portable requires dist/MagicEditor.exe (run with -Exe or alone)"
    }

    $portableName = "MagicEditor-Portable-$ProductVersion-win64"
    $stage = Join-Path $DistDir "stage-portable"
    if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
    Ensure-Dir $stage

    Copy-Item $ExePath (Join-Path $stage "MagicEditor.exe")
    $readmeSrc = Join-Path $Root "packaging\portable\README-PORTABLE.txt"
    if (Test-Path $readmeSrc) {
        Copy-Item $readmeSrc (Join-Path $stage "README.txt")
    }
    $lic = Join-Path $Root "LICENSE"
    if (Test-Path $lic) {
        Copy-Item $lic (Join-Path $stage "LICENSE")
    }

    $zipPath = Join-Path $DistDir "$portableName.zip"
    if (Test-Path $zipPath) { Remove-Item -Force $zipPath }

    # Compress-Archive needs paths relative; use .NET for clean root entries
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory(
        $stage,
        $zipPath,
        [System.IO.Compression.CompressionLevel]::Optimal,
        $false
    )

    Remove-Item -Recurse -Force $stage
    $zMb = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)
    Write-Host "  OK: $zipPath ($zMb MB)" -ForegroundColor Green
}

# --- MSI (WiX) ----------------------------------------------------------
if ($Msi) {
    Write-Step "MSI installer (WiX)"
    if (-not (Test-Path $ExePath)) {
        throw "MSI requires dist/MagicEditor.exe"
    }

    $wixCmd = Get-Command wix -ErrorAction SilentlyContinue
    if (-not $wixCmd) {
        Write-Host "  WiX CLI not found. Attempting: dotnet tool install -g wix" -ForegroundColor Yellow
        $dotnet = Get-Command dotnet -ErrorAction SilentlyContinue
        if (-not $dotnet) {
            Write-Warning @"
MSI skipped: neither 'wix' nor 'dotnet' is available.

Install WiX v4+ CLI:
  winget install DotNet.SDK.8
  dotnet tool install --global wix
  wix extension add WixToolset.UI.wixext   # optional

Then re-run:
  powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Msi
"@
        } else {
            & dotnet tool install --global wix 2>&1 | Out-Host
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("Path", "User")
            $wixCmd = Get-Command wix -ErrorAction SilentlyContinue
        }
    }

    if (-not $wixCmd) {
        Write-Warning "MSI skipped: WiX CLI still not on PATH."
    } else {
        $wxs = Join-Path $Root "packaging\wix\MagicEditor.wxs"
        if (-not (Test-Path $wxs)) {
            throw "Missing WiX source: $wxs"
        }
        $msiOut = Join-Path $DistDir "MagicEditor-$ProductVersion-win64.msi"
        if (Test-Path $msiOut) { Remove-Item -Force $msiOut }

        # WiX 4/5: wix build file.wxs -d Name=Value -o out.msi
        & wix build $wxs `
            -d "ProductVersion=$ProductVersion" `
            -d "ExePath=$ExePath" `
            -o $msiOut `
            -arch x64

        if ($LASTEXITCODE -ne 0) {
            throw "wix build failed (exit $LASTEXITCODE)"
        }
        if (-not (Test-Path $msiOut)) {
            throw "MSI not produced: $msiOut"
        }
        $mMb = [math]::Round((Get-Item $msiOut).Length / 1MB, 1)
        Write-Host "  OK: $msiOut ($mMb MB)" -ForegroundColor Green
    }
}

# --- Summary ------------------------------------------------------------
Write-Step "Done"
Get-ChildItem $DistDir -File -ErrorAction SilentlyContinue |
    Sort-Object Name |
    ForEach-Object {
        $mb = [math]::Round($_.Length / 1MB, 1)
        Write-Host ("  {0,-48} {1,6} MB" -f $_.Name, $mb)
    }

Write-Host ""
Write-Host "Artifacts are under dist/ (gitignored). Do not commit binaries." -ForegroundColor DarkGray
exit 0
