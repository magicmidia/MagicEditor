#Requires -Version 5.1
<#
.SYNOPSIS
  Restore Windows default handlers so .bat / .cmd execute again.

  Older MagicEditor installers set MagicEditor.Document as the default.
#>
[CmdletBinding()]
param(
    [switch]$NoElevate
)

$ErrorActionPreference = "Stop"

function Test-IsAdmin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Restore-Native($hivePath, $ext, $progid) {
    $key = Join-Path $hivePath $ext
    if (-not (Test-Path $key)) {
        New-Item -Path $key -Force | Out-Null
    }
    Set-ItemProperty -Path $key -Name "(default)" -Value $progid
    $ow = Join-Path $key "OpenWithProgids"
    if (Test-Path $ow) {
        Remove-ItemProperty -Path $ow -Name "MagicEditor.Document" -ErrorAction SilentlyContinue
    }
}

function Invoke-Restore {
    Restore-Native "HKCU:\Software\Classes" ".bat" "batfile"
    Restore-Native "HKCU:\Software\Classes" ".cmd" "cmdfile"
    if (Test-IsAdmin) {
        Restore-Native "HKLM:\Software\Classes" ".bat" "batfile"
        Restore-Native "HKLM:\Software\Classes" ".cmd" "cmdfile"
        $cap = "HKLM:\Software\MagicEditor\Capabilities\FileAssociations"
        if (Test-Path $cap) {
            Remove-ItemProperty -Path $cap -Name ".bat" -ErrorAction SilentlyContinue
            Remove-ItemProperty -Path $cap -Name ".cmd" -ErrorAction SilentlyContinue
        }
    }
    foreach ($ext in @(".bat", ".cmd")) {
        $base = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\$ext"
        foreach ($leaf in @("UserChoice", "OpenWithProgids", "OpenWithList")) {
            $p = Join-Path $base $leaf
            if (Test-Path $p) {
                Remove-Item -Path $p -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }
    $sig = @"
[DllImport("shell32.dll")] public static extern void SHChangeNotify(int wEventId, uint uFlags, System.IntPtr dwItem1, System.IntPtr dwItem2);
"@
    Add-Type -MemberDefinition $sig -Name Native -Namespace Shell -ErrorAction SilentlyContinue
    [Shell.Native]::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)
}

if (-not $NoElevate -and -not (Test-IsAdmin)) {
    $self = $MyInvocation.MyCommand.Path
    Start-Process -FilePath "powershell.exe" -Verb RunAs -Wait -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $self, "-NoElevate"
    )
    Invoke-Restore
    exit 0
}

Invoke-Restore
Write-Host "Restored .bat -> batfile, .cmd -> cmdfile"
