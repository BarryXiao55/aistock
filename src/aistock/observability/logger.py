"""Structured JSON logger for pipeline observability."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path


class PipelineLogger:
    """结构化 JSON 日志记录器"""

    def __init__(self, log_dir: str = "logs", retention_days: int = 90):
        self._log_dir = Path(log_dir)
        self._retention_days = retention_days
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file(self, task_id: str) -> Path:
        """获取日志文件路径"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_dir = self._log_dir / today
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / f"task_{task_id}.jsonl"

    def log(self, level: str, step: str, message: str, task_id: str = "", **extra):
        """
        写入一条结构化日志。

        Args:
            level: 日志级别 (INFO, WARNING, ERROR)
            step: 步骤名称 (fetch, clean, store, etc.)
            message: 日志消息
            task_id: 任务 ID
            **extra: 额外的键值对
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "step": step,
            "message": message,
            "task_id": task_id,
        }
        log_entry.update(extra)

        # 写入 JSONL 文件
        log_file = self._get_log_file(task_id)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        # 同时输出到标准日志
        logger = logging.getLogger("aistock")
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(log_level, f"[{step}] {message}")

    def info(self, step: str, message: str, task_id: str = "", **extra):
        """INFO 级别日志"""
        self.log("INFO", step, message, task_id, **extra)

    def warning(self, step: str, message: str, task_id: str = "", **extra):
        """WARNING 级别日志"""
        self.log("WARNING", step, message, task_id, **extra)

    def error(self, step: str, message: str, task_id: str = "", **extra):
        """ERROR 级别日志"""
        self.log("ERROR", step, message, task_id, **extra)

    def cleanup(self):
        """删除超过 retention_days 天之前的日志目录"""
        cutoff_date = datetime.now() - timedelta(days=self._retention_days)

        for day_dir in self._log_dir.iterdir():
            if day_dir.is_dir():
                try:
                    dir_date = datetime.strptime(day_dir.name, "%Y-%m-%d")
                    if dir_date < cutoff_date:
                        # 删除整个目录
                        for file in day_dir.iterdir():
                            file.unlink()
                        day_dir.rmdir()
                except (ValueError, OSError):
                    # 跳过无法解析的目录
                    continue

    def read_logs(self, task_id: str) -> list[dict]:
        """读取指定任务的所有日志"""
        logs = []
        for day_dir in self._log_dir.iterdir():
            if day_dir.is_dir():
                log_file = day_dir / f"task_{task_id}.jsonl"
                if log_file.exists():
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                logs.append(json.loads(line))
        return logs
