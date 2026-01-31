param (
    [string]$pythonPath,
    [string]$scriptPath
)

Write-Host "Starting debug server"

$port = 5678
$workDir = Split-Path $scriptPath
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$shortUser = $currentUser -replace '.*\\', ''

# Check if current user has an active session
$quserOutput = quser 2>&1 | Out-String
if (-not ($quserOutput -match "$shortUser.*Active")) {
    Write-Host ""
    Write-Host "ERROR: User '$currentUser' does not have an active desktop session."
    Write-Host ""
    Write-Host "Current sessions:"
    Write-Host $quserOutput
    Write-Host ""
    Write-Host "To fix: RDP/login as '$currentUser' or run as the user with Active session"
    exit 1
}

# Validate paths
if (-not (Test-Path $pythonPath)) {
    Write-Host "ERROR: Python not found at $pythonPath"
    exit 1
}
if (-not (Test-Path $scriptPath)) {
    Write-Host "ERROR: Script not found at $scriptPath"
    exit 1
}

Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 1

$taskName = "DebugPythonGUI_$port"

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction -Execute $pythonPath `
    -Argument "-m debugpy --listen 0.0.0.0:$port --wait-for-client `"$scriptPath`"" `
    -WorkingDirectory $workDir

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive

Register-ScheduledTask -TaskName $taskName -Action $action -Settings $settings -Principal $principal | Out-Null
Start-ScheduledTask -TaskName $taskName

Write-Host "Waiting for debug server..."

for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        Write-Host "Debug server listening on port $port"
        Write-Host "Ready to attach debugger"
        exit 0
    }
}

Write-Host "ERROR: Debug server failed to start"
exit 1