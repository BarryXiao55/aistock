# 卸载 Aistock 每日更新计划任务
# 以管理员身份运行此脚本

$taskName = "AistockDailyUpdate"

$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($task) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "计划任务 '$taskName' 已删除" -ForegroundColor Green
} else {
    Write-Host "计划任务 '$taskName' 不存在" -ForegroundColor Yellow
}
