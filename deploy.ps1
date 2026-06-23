# PGRMS (Personal Global Rules Management System) - Windows deployment wrapper.
# Default mode is dry-run. Pass -Apply to write user-global configuration.

param(
    [switch]$Apply,
    [string]$HomeDir = ""
)

$ErrorActionPreference = "Stop"

Write-Host "========================================="
Write-Host "Starting PGRMS Automation Deployment"
if (-not $Apply) {
    Write-Host "Mode: dry-run. Pass -Apply to write user-global files."
} else {
    Write-Host "Mode: apply. User-global files may be overwritten after backup."
}
Write-Host "========================================="

$argsList = @("scripts/pgrms.py", "deploy", "--target", "all")
if ($Apply) {
    $argsList += "--apply"
}
if ($HomeDir -ne "") {
    $argsList += @("--home", $HomeDir)
}
python @argsList

Write-Host "========================================="
Write-Host "PGRMS Deployment Command Completed."
Write-Host "========================================="
