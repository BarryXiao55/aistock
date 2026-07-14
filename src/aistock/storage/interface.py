"""StorageBackend abstract interface."""

from abc import ABC, abstractmethod

import pandas as pd


class StorageBackend(ABC):
    """存储后端抽象"""

    name: str = ""

    @abstractmethod
    def write(self, df: pd.DataFrame, schema: type, partition_keys: dict):
        """全量写入，覆盖已有分区"""
        ...

    @abstractmethod
    def read(self, query):
        """按条件读取"""
        ...

    @abstractmethod
    def upsert(
        self, df: pd.DataFrame, schema: type, partition_keys: dict, on_conflict: list[str]
    ):
        """按主键去重更新（如 trade_date + code），日更新用"""
        ...

    @abstractmethod
    def exists(self, schema: type, partition_keys: dict) -> bool:
        """检查指定分区是否已有数据，避免重复下载"""
        ...
