# Uninstall Aistock daily update scheduled task
# Run as Administrator

$taskName = "AistockDailyUpdate"

$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($task) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Task '$taskName' removed" -ForegroundColor Green
} else {
    Write-Host "Task '$taskName' not found" -ForegroundColor Yellow
}
