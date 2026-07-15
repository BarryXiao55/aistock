"""Logger adapter for pipeline compatibility."""

import logging
from typing import Any


class LoggerAdapter:
    """适配器：让 PipelineLogger 兼容标准 logging.Logger 接口"""

    def __init__(self, logger: Any, task_id: str = ""):
        self._logger = logger
        self._task_id = task_id
        # PipelineLogger 有 step 参数，标准 Logger 没有
        self._is_pipeline_logger = hasattr(logger, "step") or type(logger).__name__ == "PipelineLogger"

    def info(self, msg: str, *args, **kwargs):
        """INFO 级别日志"""
        if self._is_pipeline_logger:
            self._logger.info("pipeline", msg, task_id=self._task_id)
        else:
            self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """WARNING 级别日志"""
        if self._is_pipeline_logger:
            self._logger.warning("pipeline", msg, task_id=self._task_id)
        else:
            self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """ERROR 级别日志"""
        if self._is_pipeline_logger:
            self._logger.error("pipeline", msg, task_id=self._task_id)
        else:
            self._logger.error(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        """DEBUG 级别日志"""
        if self._is_pipeline_logger:
            self._logger.debug("pipeline", msg, task_id=self._task_id)
        else:
            self._logger.debug(msg, *args, **kwargs)
