"""Validation rule interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    """验证结果"""
    rule_name: str
    passed: bool
    message: str
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "rule_name": self.rule_name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
        }


class ValidationRule(ABC):
    """验证规则抽象接口"""

    name: str = ""
    description: str = ""

    @abstractmethod
    def validate(self, data: Any, context: dict | None = None) -> ValidationResult:
        """
        执行验证。

        Args:
            data: 要验证的数据（DataFrame、Series 等）
            context: 验证上下文（可选）

        Returns:
            ValidationResult: 验证结果
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
