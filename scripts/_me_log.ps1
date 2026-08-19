# Shared build/install log -> repo-root MagicEditor.log
if (-not $script:MeRoot) {
    $script:MeRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
$script:MeLogFile = Join-Path $script:MeRoot "MagicEditor.log"

function Write-MeLog {
    param(
        [ValidateSet("INFO", "WARNING", "ERROR")]
        [string]$Level = "INFO",
        [Parameter(Mandatory = $true)]
        [string]$Message
    )
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "$ts [$Level] build: $Message"
    try {
        Add-Content -LiteralPath $script:MeLogFile -Value $line -Encoding utf8
    } catch {
        # never fail the build because the log file is locked
    }
    switch ($Level) {
        "ERROR" { Write-Host $Message -ForegroundColor Red }
        "WARNING" { Write-Warning $Message }
        default { Write-Host $Message }
    }
}
