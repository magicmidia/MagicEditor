# Compatibility wrapper — builds onefile EXE into dist/
# Prefer: scripts/build.ps1 -Exe | -Portable | -Msi | -All
$ErrorActionPreference = "Stop"
& "$PSScriptRoot\build.ps1" -Exe @args
exit $LASTEXITCODE
