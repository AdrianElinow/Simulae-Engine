$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $scriptDir '..')
Write-Output "Starting NGIN API from $PWD"

# Try running as a package module first
python3 -m NGIN.api
if ($LASTEXITCODE -ne 0) {
    Write-Output "Module run failed (exit $LASTEXITCODE), trying direct script..."
    python3 NGIN/api.py
}
