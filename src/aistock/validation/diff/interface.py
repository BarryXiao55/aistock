"""Data diff detection interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import pandas as pd


class DiffType(Enum):
    """差异类型"""
    STRUCTURAL = "structural"      # 结构差异（Schema 不一致）
    VALUE = "value"                # 值差异（同一字段值不同）
    MISSING = "missing"            # 缺失差异（记录在某源中缺失）
    TEMPORAL = "temporal"          # 时序差异（数据更新时间不同步）
    GRANULARITY = "granularity"    # 粒度差异（数据聚合级别不同）


class DiffSeverity(Enum):
    """差异严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DataDiff:
    """数据差异"""
    diff_type: DiffType
    severity: DiffSeverity
    source_index: int | None
    target_index: int | None
    column: str | None
    source_value: Any
    target_value: Any
    description: str
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "diff_type": self.diff_type.value,
            "severity": self.severity.value,
            "source_index": self.source_index,
            "target_index": self.target_index,
            "column": self.column,
            "source_value": str(self.source_value) if self.source_value is not None else None,
            "target_value": str(self.target_value) if self.target_value is not None else None,
            "description": self.description,
            "details": self.details,
        }


@dataclass
class DiffResult:
    """差异检测结果"""
    diffs: list[DataDiff]
    source_count: int
    target_count: int
    structural_diffs: int
    value_diffs: int
    missing_diffs: int
    total_diffs: int

    @property
    def diff_rate(self) -> float:
        """差异率"""
        total_records = self.source_count + self.target_count
        if total_records == 0:
            return 0.0
        return self.total_diffs / total_records

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "diffs": [diff.to_dict() for diff in self.diffs],
            "source_count": self.source_count,
            "target_count": self.target_count,
            "structural_diffs": self.structural_diffs,
            "value_diffs": self.value_diffs,
            "missing_diffs": self.missing_diffs,
            "total_diffs": self.total_diffs,
            "diff_rate": self.diff_rate,
        }

    def get_diffs_by_type(self, diff_type: DiffType) -> list[DataDiff]:
        """按类型获取差异"""
        return [diff for diff in self.diffs if diff.diff_type == diff_type]

    def get_diffs_by_severity(self, severity: DiffSeverity) -> list[DataDiff]:
        """按严重程度获取差异"""
        return [diff for diff in self.diffs if diff.severity == severity]


class DiffDetector(ABC):
    """差异检测抽象接口"""

    name: str = ""
    description: str = ""

    @abstractmethod
    def detect(
        self,
        source_df: pd.DataFrame,
        target_df: pd.DataFrame,
        key_columns: list[str],
        compare_columns: list[str] | None = None,
    ) -> DiffResult:
        """
        执行差异检测。

        Args:
            source_df: 源表 DataFrame
            target_df: 目标表 DataFrame
            key_columns: 主键列（用于匹配记录）
            compare_columns: 要比较的列（None 表示所有列）

        Returns:
            DiffResult: 差异检测结果
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
