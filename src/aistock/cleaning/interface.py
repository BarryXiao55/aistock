"""CleaningStep abstract interface."""

from abc import ABC, abstractmethod

import pandas as pd


class CleaningStep(ABC):
    """清洗步骤抽象 --- 一个步骤做一件事"""

    name: str = ""
    requires: list[str] = []

    @abstractmethod
    def clean(self, df: pd.DataFrame, ctx) -> pd.DataFrame:
        """执行清洗，返回处理后的 DataFrame"""
        ...

    def validate(self, df: pd.DataFrame) -> list[str]:
        """后置校验，返回问题描述列表（空列表 = 通过）"""
        return []
