# Build EXE + Portable ZIP + MSI (MSI skipped with warning if WiX missing)
$ErrorActionPreference = "Stop"
& "$PSScriptRoot\build.ps1" -All @args
exit $LASTEXITCODE
