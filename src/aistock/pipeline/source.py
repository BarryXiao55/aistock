"""SourceNode abstract interface."""

import time
from abc import ABC, abstractmethod

import pandas as pd

from aistock.exceptions import SourceRateLimited, SourceUnavailable


class SourceNode(ABC):
    """数据源抽象接口 --- 每个数据源插件实现此接口"""

    name: str = ""
    retry_max: int = 3
    retry_delay_s: float = 5.0
    _ctx = None  # 由 PipelineRunner 在 fetch 前注入

    @abstractmethod
    def supports(self, asset_type: str, schema: type) -> bool:
        """声明能力：该源是否支持此品种+数据模型"""
        ...

    @abstractmethod
    def fetch(self, spec) -> pd.DataFrame:
        """执行下载，返回与内部 Schema 字段对齐的 DataFrame"""
        ...

    def fetch_with_retry(self, spec) -> pd.DataFrame:
        """基类提供重试模板，子类可覆盖"""
        last_exc = None
        for attempt in range(self.retry_max):
            try:
                return self.fetch(spec)
            except SourceRateLimited as e:
                time.sleep(self.retry_delay_s * (2**attempt))
                last_exc = e
            except SourceUnavailable:
                raise  # 不可达不重试，交给 Runner 降级
        raise last_exc if last_exc else RuntimeError("retry exhausted")

    def check_health(self) -> bool:
        """健康检查：数据源当前是否可连通"""
        return True

    @property
    def ctx(self):
        return self._ctx

    @ctx.setter
    def ctx(self, value):
        self._ctx = value
