# Build onefile EXE + Portable ZIP under dist/
$ErrorActionPreference = "Stop"
& "$PSScriptRoot\build.ps1" -Exe -Portable @args
exit $LASTEXITCODE
