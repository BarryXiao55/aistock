"""Record linkage interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class LinkResult:
    """记录链接结果"""
    source_index: int
    target_index: int
    confidence: float
    match_type: str  # "exact" | "fuzzy" | "probabilistic"
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "source_index": self.source_index,
            "target_index": self.target_index,
            "confidence": self.confidence,
            "match_type": self.match_type,
            "details": self.details,
        }


@dataclass
class LinkageResult:
    """链接结果集"""
    links: list[LinkResult]
    source_count: int
    target_count: int
    matched_count: int
    unmatched_source_count: int
    unmatched_target_count: int

    @property
    def match_rate(self) -> float:
        """匹配率"""
        if self.source_count == 0:
            return 0.0
        return self.matched_count / self.source_count

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "links": [link.to_dict() for link in self.links],
            "source_count": self.source_count,
            "target_count": self.target_count,
            "matched_count": self.matched_count,
            "unmatched_source_count": self.unmatched_source_count,
            "unmatched_target_count": self.unmatched_target_count,
            "match_rate": self.match_rate,
        }


class RecordLinker(ABC):
    """记录链接抽象接口"""

    name: str = ""
    description: str = ""

    @abstractmethod
    def link(
        self,
        source_df: pd.DataFrame,
        target_df: pd.DataFrame,
        source_columns: list[str],
        target_columns: list[str],
        threshold: float = 0.8,
    ) -> LinkageResult:
        """
        执行记录链接。

        Args:
            source_df: 源表 DataFrame
            target_df: 目标表 DataFrame
            source_columns: 源表匹配列
            target_columns: 目标表匹配列
            threshold: 匹配阈值 (0-1)

        Returns:
            LinkageResult: 链接结果
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
