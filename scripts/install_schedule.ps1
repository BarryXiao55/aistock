# Install Aistock daily update scheduled task
# Run as Administrator

$taskName = "AistockDailyUpdate"
$scriptPath = "C:\aiworks\mimo_work\aistock\scripts\daily_update.bat"

# Remove old task if exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Create daily task at 19:00
$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory "C:\aiworks\mimo_work\aistock"
$trigger = New-ScheduledTaskTrigger -Daily -At "19:00"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Aistock daily stock data update at 19:00"

Write-Host "Task '$taskName' created" -ForegroundColor Green
Write-Host "Schedule: Daily at 19:00" -ForegroundColor Cyan
Write-Host "Script: $scriptPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "View task:    Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor Yellow
Write-Host "Run now:      Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Yellow
Write-Host "Remove task:  Unregister-ScheduledTask -TaskName '$taskName'" -ForegroundColor Yellow
