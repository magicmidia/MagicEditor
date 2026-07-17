# Build onefile EXE + MSI under dist/ (requires WiX CLI: dotnet tool install -g wix)
$ErrorActionPreference = "Stop"
& "$PSScriptRoot\build.ps1" -Exe -Msi @args
exit $LASTEXITCODE
