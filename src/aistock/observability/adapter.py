"""Logger adapter for pipeline compatibility."""

import logging
from typing import Any


class LoggerAdapter:
    """适配器：让 PipelineLogger 兼容标准 logging.Logger 接口"""

    def __init__(self, logger: Any, task_id: str = ""):
        self._logger = logger
        self._task_id = task_id

    def info(self, msg: str, *args, **kwargs):
        """INFO 级别日志"""
        if hasattr(self._logger, "info"):
            # PipelineLogger 需要 step 和 message
            self._logger.info("pipeline", msg, task_id=self._task_id)
        else:
            # 标准 Logger
            self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """WARNING 级别日志"""
        if hasattr(self._logger, "warning"):
            self._logger.warning("pipeline", msg, task_id=self._task_id)
        else:
            self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """ERROR 级别日志"""
        if hasattr(self._logger, "error"):
            self._logger.error("pipeline", msg, task_id=self._task_id)
        else:
            self._logger.error(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        """DEBUG 级别日志"""
        if hasattr(self._logger, "debug"):
            self._logger.debug("pipeline", msg, task_id=self._task_id)
        else:
            self._logger.debug(msg, *args, **kwargs)
