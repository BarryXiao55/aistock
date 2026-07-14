"""Nullability validation rule."""

import pandas as pd

from aistock.validation.interface import ValidationRule, ValidationResult


class NotNullRule(ValidationRule):
    """非空验证规则 - 检查列值是否非空"""

    name = "not_null"
    description = "检查列值是否非空"

    def __init__(self, column: str):
        """
        初始化非空规则。

        Args:
            column: 要检查的列名
        """
        self.column = column

    def validate(self, data: pd.DataFrame, context: dict | None = None) -> ValidationResult:
        """执行非空验证"""
        if self.column not in data.columns:
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Column '{self.column}' not found",
                details={"column": self.column, "available_columns": list(data.columns)},
            )

        # 检查空值
        null_count = data[self.column].isna().sum()

        if null_count == 0:
            return ValidationResult(
                rule_name=self.name,
                passed=True,
                message=f"Column '{self.column}' has no null values",
                details={"column": self.column, "null_count": 0},
            )
        else:
            null_percentage = (null_count / len(data)) * 100
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Column '{self.column}' has {null_count} null values ({null_percentage:.2f}%)",
                details={
                    "column": self.column,
                    "null_count": int(null_count),
                    "null_percentage": round(null_percentage, 2),
                    "total_rows": len(data),
                },
            )


class NotNullCombinationRule(ValidationRule):
    """组合非空验证规则 - 检查多列组合是否非空"""

    name = "not_null_combination"
    description = "检查多列组合是否非空"

    def __init__(self, columns: list[str]):
        """
        初始化组合非空规则。

        Args:
            columns: 要检查的列名列表
        """
        self.columns = columns

    def validate(self, data: pd.DataFrame, context: dict | None = None) -> ValidationResult:
        """执行组合非空验证"""
        missing_columns = [col for col in self.columns if col not in data.columns]
        if missing_columns:
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Columns not found: {missing_columns}",
                details={"missing_columns": missing_columns, "available_columns": list(data.columns)},
            )

        # 检查组合空值
        null_mask = data[self.columns].isna().any(axis=1)
        null_count = null_mask.sum()

        if null_count == 0:
            return ValidationResult(
                rule_name=self.name,
                passed=True,
                message=f"Columns {self.columns} have no null combinations",
                details={"columns": self.columns, "null_count": 0},
            )
        else:
            null_percentage = (null_count / len(data)) * 100
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Columns {self.columns} have {null_count} rows with null values ({null_percentage:.2f}%)",
                details={
                    "columns": self.columns,
                    "null_count": int(null_count),
                    "null_percentage": round(null_percentage, 2),
                    "total_rows": len(data),
                },
            )
