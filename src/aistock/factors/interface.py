"""Factor calculation interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd


class FactorCategory(Enum):
    """因子类别"""
    TECHNICAL = "technical"      # 技术因子
    FUNDAMENTAL = "fundamental"  # 基本面因子
    ALTERNATIVE = "alternative"  # 另类因子


class FactorFrequency(Enum):
    """因子频率"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


@dataclass
class FactorMetadata:
    """因子元数据"""
    name: str
    description: str
    category: FactorCategory
    frequency: FactorFrequency
    version: str = "1.0.0"
    author: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)
    data_requirements: list[str] = field(default_factory=list)
    parameters: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "frequency": self.frequency.value,
            "version": self.version,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "data_requirements": self.data_requirements,
            "parameters": self.parameters,
        }


@dataclass
class FactorResult:
    """因子计算结果"""
    factor_name: str
    data: pd.DataFrame
    metadata: FactorMetadata
    calculation_time: float  # 计算耗时（秒）
    success: bool = True
    error_message: str | None = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "factor_name": self.factor_name,
            "data_shape": self.data.shape if self.data is not None else None,
            "metadata": self.metadata.to_dict(),
            "calculation_time": self.calculation_time,
            "success": self.success,
            "error_message": self.error_message,
        }


class FactorCalculator(ABC):
    """因子计算抽象接口"""

    @property
    @abstractmethod
    def metadata(self) -> FactorMetadata:
        """获取因子元数据"""
        ...

    @abstractmethod
    def calculate(
        self,
        data: pd.DataFrame,
        params: dict | None = None,
    ) -> FactorResult:
        """
        计算因子值。

        Args:
            data: 输入数据 DataFrame
            params: 计算参数（可选）

        Returns:
            FactorResult: 因子计算结果
        """
        ...

    def validate_input(self, data: pd.DataFrame) -> list[str]:
        """
        验证输入数据。

        Args:
            data: 输入数据 DataFrame

        Returns:
            list[str]: 验证问题列表（空列表表示通过）
        """
        return []

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.metadata.name}')>"
