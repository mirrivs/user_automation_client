param (
    [string]$pythonPath,
    [string]$scriptPath
)

# Find console session ID
$sessionInfo = query session | Where-Object { $_ -match 'console' -or $_ -match '^\s*\d+\s+console\s+' }
if ($sessionInfo) {
    $sessionId = $sessionInfo -split '\s+' | Where-Object { $_ -match '^\d+$' } | Select-Object -First 1
    
    if ($sessionId) {
        Write-Host "Found console session ID: $sessionId"
        
        $port = 5678
        
        Get-ScheduledTask | Where-Object {$_.TaskName -like "VSCodeDebug*"} | Unregister-ScheduledTask -Confirm:$false -ErrorAction SilentlyContinue
        
        $pythonCommand = "$pythonPath -m debugpy --listen 0.0.0.0:$port --wait-for-client $scriptPath"
        $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-Command `"$pythonCommand`""
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(2)
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
        $taskName = "VSCodeDebug_" + (Get-Random)
        
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force
        Write-Host "Running debug server in session $sessionId via task $taskName on port $port"
        Start-ScheduledTask -TaskName $taskName
        
        Start-Sleep -Seconds 3
        Write-Host "Task $taskName will be removed when debugging is finished"
        
        # Register a cleanup task to run when VS Code exits
        $cleanupCommand = "Unregister-ScheduledTask -TaskName $taskName -Confirm:`$false"
        $cleanupAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-Command `"$cleanupCommand`""
        $cleanupTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddHours(1)
        $cleanupTaskName = "Cleanup_$taskName"
        Register-ScheduledTask -TaskName $cleanupTaskName -Action $cleanupAction -Trigger $cleanupTrigger -Settings $settings -Force
    } else {
        Write-Host "Could not parse session ID from: $sessionInfo"
        exit 1
    }
} else {
    Write-Host "No console session found"
    exit 1
}