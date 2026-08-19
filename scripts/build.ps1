#Requires -Version 5.1
<#
.SYNOPSIS
  Build MagicEditor release artifacts: EXE, Portable ZIP, and/or MSI.

.DESCRIPTION
  Primary EXE is copied to the **repo root** as MagicEditor.exe.
  A copy is also kept under dist/ for portable/MSI packaging.
  Binaries are gitignored - never commit them.

  Targets:
    -Exe       PyInstaller onefile -> ./MagicEditor.exe (+ dist/MagicEditor.exe)
    -Portable  ZIP with exe + README -> dist/MagicEditor-Portable-<ver>-win64.zip
    -Msi       WiX installer -> dist/MagicEditor-<ver>-win64.msi
    -Inno      Inno Setup installer -> dist/MagicEditor-<ver>-win64-setup.exe
    -All       Exe + Portable + Msi + Inno (missing tools warn and skip)

.EXAMPLE
  build.bat
  powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -All
  powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe -Portable
#>
[CmdletBinding()]
param(
    [switch]$Exe,
    [switch]$Onedir,
    [switch]$Portable,
    [switch]$Msi,
    [switch]$Inno,
    [switch]$All,
    [switch]$SkipDeps,
    [switch]$KeepWork,
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root
. (Join-Path $PSScriptRoot "_me_log.ps1")
trap {
    Write-MeLog "ERROR" $_.Exception.Message
    break
}

if ($All) {
    $Exe = $true
    $Portable = $true
    $Msi = $true
    $Inno = $true
}
if (-not ($Exe -or $Onedir -or $Portable -or $Msi -or $Inno)) {
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
$RootExePath = Join-Path $Root "MagicEditor.exe"
$ExePath = $RootExePath
$DistExePath = Join-Path $DistDir "MagicEditor.exe"
$SpecPath = Join-Path $Root "MagicEditor.spec"
$IconPath = Join-Path $Root "resources\icons\app\magiceditor.ico"

Write-Host "MagicEditor build" -ForegroundColor Green
Write-Host "  root     : $Root"
Write-Host "  version  : $ProductVersion"
Write-Host "  icon     : $(if(Test-Path $IconPath){ $IconPath } else { '(missing)' })"
Write-Host "  targets  :$(if($Exe){' exe'})$(if($Portable){' portable'})$(if($Msi){' msi'})$(if($Inno){' inno'})"
Write-Host "  log      : $(Join-Path $Root 'MagicEditor.log')"
Write-MeLog "INFO" "Build start version=$ProductVersion targets=$(if($Exe){'exe '})$(if($Portable){'portable '})$(if($Msi){'msi '})$(if($Inno){'inno'})"

# --- Dependencies -------------------------------------------------------
if (-not $SkipDeps) {
    Write-Step "Installing package + PyInstaller (editable + dev extras)"
    python -m pip install -e ".[dev]" -q
    if ($LASTEXITCODE -ne 0) {
        Write-MeLog "ERROR" "pip install failed (exit $LASTEXITCODE)"
        throw "pip install failed (exit $LASTEXITCODE)"
    }
}

Ensure-Dir $DistDir

# --- EXE onedir (K10 daily cold-start) ----------------------------------
if ($Onedir) {
    $OnedirSpec = Join-Path $Root "MagicEditor-onedir.spec"
    if (-not (Test-Path $OnedirSpec)) {
        throw "Missing MagicEditor-onedir.spec at $OnedirSpec"
    }
    Write-Step "PyInstaller onedir -> dist/MagicEditor/ (daily)"
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & python -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath $DistDir `
        --workpath $WorkDir `
        $OnedirSpec
    $pyiExit = $LASTEXITCODE
    $ErrorActionPreference = $prevEap
    if ($pyiExit -ne 0) {
        throw "PyInstaller onedir failed (exit $pyiExit)"
    }
}

# --- EXE (PyInstaller onefile) ------------------------------------------
if ($Exe -or $Portable -or $Msi) {
    if (-not (Test-Path $SpecPath)) {
        throw "Missing MagicEditor.spec at $SpecPath"
    }

    Write-Step "PyInstaller onefile -> MagicEditor.exe (project root)"
    if (-not (Test-Path $IconPath)) {
        Write-Warning "App icon missing at $IconPath - EXE will use default PyInstaller icon"
    }
    if (-not $KeepWork -and (Test-Path (Join-Path $Root "build"))) {
        Remove-Item -Recurse -Force (Join-Path $Root "build") -ErrorAction SilentlyContinue
    }
    if (Test-Path $RootExePath) {
        Remove-Item -Force $RootExePath -ErrorAction SilentlyContinue
    }

    # PyInstaller logs to stderr; do not treat that as a terminating error.
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & python -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath $Root `
        --workpath $WorkDir `
        $SpecPath
    $pyiExit = $LASTEXITCODE
    $ErrorActionPreference = $prevEap

    if ($pyiExit -ne 0) {
        Write-MeLog "ERROR" "PyInstaller failed (exit $pyiExit)"
        throw "PyInstaller failed (exit $pyiExit)"
    }
    if (-not (Test-Path $RootExePath)) {
        throw "Build failed: $RootExePath not found"
    }

    # Packaging scripts still look under dist\
    if ($Portable -or $Msi -or $Inno) {
        Ensure-Dir $DistDir
        Copy-Item -Force $RootExePath $DistExePath
    }

    $sizeMb = [math]::Round((Get-Item $RootExePath).Length / 1MB, 1)
    Write-Host ("  OK: " + $RootExePath + "  " + [string]$sizeMb + " MB") -ForegroundColor Green
}

# --- Portable ZIP -------------------------------------------------------
if ($Portable) {
    Write-Step "Portable ZIP"
    if (-not (Test-Path $DistExePath)) {
        if (Test-Path $RootExePath) {
            Ensure-Dir $DistDir
            Copy-Item -Force $RootExePath $DistExePath
        } else {
            throw "Portable requires MagicEditor.exe at project root (run with -Exe)"
        }
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
    Write-Host ("  OK: " + $zipPath + "  " + [string]$zMb + " MB") -ForegroundColor Green
}

# --- MSI (WiX) ----------------------------------------------------------
if ($Msi) {
    Write-Step "MSI installer (WiX)"
    if (-not (Test-Path $ExePath)) {
        throw "MSI requires MagicEditor.exe at the project root"
    }

    $wixCmd = Get-Command wix -ErrorAction SilentlyContinue
    if (-not $wixCmd) {
        Write-Host "  WiX CLI not found. Attempting: dotnet tool install -g wix" -ForegroundColor Yellow
        $dotnet = Get-Command dotnet -ErrorAction SilentlyContinue
        if (-not $dotnet) {
            Write-MeLog "WARNING" "MSI skipped: neither wix nor dotnet is available"
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
        Write-MeLog "WARNING" "MSI skipped: WiX CLI still not on PATH"
        Write-Warning "MSI skipped: WiX CLI still not on PATH."
    } else {
        $wxs = Join-Path $Root "packaging\wix\MagicEditor.wxs"
        if (-not (Test-Path $wxs)) {
            throw "Missing WiX source: $wxs"
        }
        $msiOut = Join-Path $DistDir "MagicEditor-$ProductVersion-win64.msi"
        if (Test-Path $msiOut) { Remove-Item -Force $msiOut }

        # WiX 4/5: wix build file.wxs -d Name=Value -o out.msi
        $iconForMsi = if (Test-Path $IconPath) { $IconPath } else { $ExePath }
        & wix build $wxs `
            -d "ProductVersion=$ProductVersion" `
            -d "ExePath=$ExePath" `
            -d "IconPath=$iconForMsi" `
            -o $msiOut `
            -arch x64

        if ($LASTEXITCODE -ne 0) {
            Write-MeLog "ERROR" "wix build failed (exit $LASTEXITCODE)"
            throw "wix build failed (exit $LASTEXITCODE)"
        }
        if (-not (Test-Path $msiOut)) {
            Write-MeLog "ERROR" "MSI not produced: $msiOut"
            throw "MSI not produced: $msiOut"
        }
        $mMb = [math]::Round((Get-Item $msiOut).Length / 1MB, 1)
        Write-MeLog "INFO" "MSI OK: $msiOut ($mMb MB)"
        Write-Host ("  OK: " + $msiOut + "  " + [string]$mMb + " MB") -ForegroundColor Green
    }
}

# --- Inno Setup installer -----------------------------------------------
if ($Inno) {
    Write-Step "Inno Setup installer"
    if (-not (Test-Path $ExePath)) {
        throw "Inno requires MagicEditor.exe at the project root (run with -Exe first)"
    }
    $innoScript = Join-Path $Root "scripts\build_inno.ps1"
    if (-not (Test-Path $innoScript)) {
        throw "Missing $innoScript"
    }
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $innoScript -Version $ProductVersion -ExePath $ExePath
        if ($LASTEXITCODE -ne 0) {
            throw "build_inno.ps1 failed (exit $LASTEXITCODE)"
        }
        Write-MeLog "INFO" "Inno Setup installer built (version $ProductVersion)"
    } catch {
        $msg = "Inno Setup failed: $($_.Exception.Message)"
        Write-MeLog "ERROR" $msg
        if ($All) {
            Write-Warning $msg
            Write-Warning "Install Inno Setup 6 (winget install JRSoftware.InnoSetup) and re-run with -Inno"
            Write-Warning "Note: Inno produces dist\MagicEditor-<ver>-win64-setup.exe  (not .msi - that is WiX)"
        } else {
            throw $msg
        }
    }
}

# --- Summary ------------------------------------------------------------
Write-Step "Done"
if (Test-Path $RootExePath) {
    $mb = [math]::Round((Get-Item $RootExePath).Length / 1MB, 1)
    Write-Host ("  {0,-48} {1,6} MB" -f "MagicEditor.exe (project root)", $mb) -ForegroundColor Green
}
Get-ChildItem $DistDir -File -ErrorAction SilentlyContinue |
    Sort-Object Name |
    ForEach-Object {
        $mb = [math]::Round($_.Length / 1MB, 1)
        Write-Host ("  {0,-48} {1,6} MB" -f $_.Name, $mb)
    }

Write-Host ""
Write-Host "Artifacts are under dist/ (gitignored). Do not commit binaries." -ForegroundColor DarkGray
exit 0
