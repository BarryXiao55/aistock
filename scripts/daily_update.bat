@echo off
REM Aistock Daily Update - 每日 19:00 自动执行
REM 用法: 双击运行 或 通过计划任务调度

echo [%date% %time%] Starting aistock daily update...

cd /d C:\aiworks\mimo_work\aistock

REM 更新股票日线
python -m aistock.cli update --asset-type stock --schema daily

echo [%date% %time%] Update completed.
