$lampPidFile = Join-Path $PSScriptRoot '.server.pid'
if (Test-Path -LiteralPath $lampPidFile) {
    $lampProcessId = [int](Get-Content -LiteralPath $lampPidFile)
    $lampProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $lampProcessId"
    $lampExpected = Join-Path $PSScriptRoot 'server.py'
    if ($lampProcess -and $lampProcess.CommandLine.Replace('\','/').Contains($lampExpected.Replace('\','/'))) {
        Stop-Process -Id $lampProcessId
        Remove-Item -LiteralPath $lampPidFile
    }
}
