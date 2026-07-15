# 安装 Aistock 每日更新计划任务
# 以管理员身份运行此脚本

$taskName = "AistockDailyUpdate"
$scriptPath = "C:\aiworks\mimo_work\aistock\scripts\daily_update.bat"

# 删除旧任务（如果存在）
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# 创建每日 19:00 执行的任务（周一到周五）
$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory "C:\aiworks\mimo_work\aistock"
$trigger = New-ScheduledTaskTrigger -Daily -At "19:00"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Aistock - 每日 19:00 更新股票日线数据"

Write-Host "计划任务 '$taskName' 已创建" -ForegroundColor Green
Write-Host "执行时间: 每天 19:00" -ForegroundColor Cyan
Write-Host "脚本路径: $scriptPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "查看任务: Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor Yellow
Write-Host "手动运行: Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Yellow
Write-Host "删除任务: Unregister-ScheduledTask -TaskName '$taskName'" -ForegroundColor Yellow
