param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$lampRoot = $PSScriptRoot
$lampPython = Join-Path $lampRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $lampPython)) {
    python -m venv (Join-Path $lampRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required.' }
    & $lampPython -m pip install -r (Join-Path $lampRoot 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Could not install the CAD engine.' }
}
$lampAddress = 'http://127.0.0.1:8766'
$lampRunning = $false
try {
    $lampHealth = Invoke-RestMethod -Uri "$lampAddress/api/config" -TimeoutSec 2
    $lampRunning = $lampHealth.app -eq 'lampshade-studio'
} catch { $lampHealth = $null }
if ($lampHealth -and -not $lampRunning) { throw 'Port 8766 is used by another app.' }
if (-not $lampRunning) {
    $lampServer = Join-Path $lampRoot 'server.py'
    $lampProcess = Start-Process -FilePath $lampPython -ArgumentList @('"' + $lampServer + '"') -WorkingDirectory $lampRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $lampRoot 'server.log') -RedirectStandardError (Join-Path $lampRoot 'server-error.log')
    for ($lampAttempt = 0; $lampAttempt -lt 30; $lampAttempt++) {
        try { $lampHealth = Invoke-RestMethod -Uri "$lampAddress/api/config" -TimeoutSec 1; if ($lampHealth.app -eq 'lampshade-studio') { $lampRunning=$true; break } } catch { Start-Sleep -Milliseconds 300 }
    }
    if (-not $lampRunning) { throw 'The design engine did not start. See server-error.log.' }
}
if (-not $NoBrowser) { Start-Process $lampAddress }
