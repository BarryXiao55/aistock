"""Conflict resolution interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd


@dataclass
class Conflict:
    """数据冲突"""
    column: str
    source_index: int
    target_index: int
    source_value: Any
    target_value: Any
    source_timestamp: datetime | None = None
    target_timestamp: datetime | None = None
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "column": self.column,
            "source_index": self.source_index,
            "target_index": self.target_index,
            "source_value": str(self.source_value) if self.source_value is not None else None,
            "target_value": str(self.target_value) if self.target_value is not None else None,
            "source_timestamp": self.source_timestamp.isoformat() if self.source_timestamp else None,
            "target_timestamp": self.target_timestamp.isoformat() if self.target_timestamp else None,
            "details": self.details,
        }


@dataclass
class Resolution:
    """冲突解决结果"""
    conflict: Conflict
    resolved_value: Any
    resolution_method: str
    confidence: float
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "conflict": self.conflict.to_dict(),
            "resolved_value": str(self.resolved_value) if self.resolved_value is not None else None,
            "resolution_method": self.resolution_method,
            "confidence": self.confidence,
            "details": self.details,
        }


@dataclass
class ResolutionResult:
    """冲突解决结果集"""
    resolutions: list[Resolution]
    total_conflicts: int
    resolved_count: int
    unresolved_count: int

    @property
    def resolution_rate(self) -> float:
        """解决率"""
        if self.total_conflicts == 0:
            return 1.0
        return self.resolved_count / self.total_conflicts

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "resolutions": [r.to_dict() for r in self.resolutions],
            "total_conflicts": self.total_conflicts,
            "resolved_count": self.resolved_count,
            "unresolved_count": self.unresolved_count,
            "resolution_rate": self.resolution_rate,
        }


class ConflictResolver(ABC):
    """冲突解决抽象接口"""

    name: str = ""
    description: str = ""

    @abstractmethod
    def resolve(
        self,
        conflicts: list[Conflict],
        context: dict | None = None,
    ) -> ResolutionResult:
        """
        执行冲突解决。

        Args:
            conflicts: 冲突列表
            context: 解决上下文（可选）

        Returns:
            ResolutionResult: 解决结果
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
