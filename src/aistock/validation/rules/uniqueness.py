"""Uniqueness validation rule."""

import pandas as pd

from aistock.validation.interface import ValidationRule, ValidationResult


class UniqueRule(ValidationRule):
    """唯一性验证规则 - 检查列值是否唯一"""

    name = "unique"
    description = "检查列值是否唯一"

    def __init__(self, column: str):
        """
        初始化唯一性规则。

        Args:
            column: 要检查的列名
        """
        self.column = column

    def validate(self, data: pd.DataFrame, context: dict | None = None) -> ValidationResult:
        """执行唯一性验证"""
        if self.column not in data.columns:
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Column '{self.column}' not found",
                details={"column": self.column, "available_columns": list(data.columns)},
            )

        # 检查唯一性
        duplicated = data[self.column].duplicated()
        duplicated_count = duplicated.sum()

        if duplicated_count == 0:
            return ValidationResult(
                rule_name=self.name,
                passed=True,
                message=f"Column '{self.column}' values are unique",
                details={"column": self.column, "duplicated_count": 0},
            )
        else:
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Column '{self.column}' has {duplicated_count} duplicate values",
                details={
                    "column": self.column,
                    "duplicated_count": int(duplicated_count),
                    "duplicated_values": data[self.column][duplicated].unique().tolist()[:10],
                },
            )


class UniqueCombinationRule(ValidationRule):
    """组合唯一性验证规则 - 检查多列组合是否唯一"""

    name = "unique_combination"
    description = "检查多列组合是否唯一"

    def __init__(self, columns: list[str]):
        """
        初始化组合唯一性规则。

        Args:
            columns: 要检查的列名列表
        """
        self.columns = columns

    def validate(self, data: pd.DataFrame, context: dict | None = None) -> ValidationResult:
        """执行组合唯一性验证"""
        missing_columns = [col for col in self.columns if col not in data.columns]
        if missing_columns:
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Columns not found: {missing_columns}",
                details={"missing_columns": missing_columns, "available_columns": list(data.columns)},
            )

        # 检查组合唯一性
        duplicated = data.duplicated(subset=self.columns, keep=False)
        duplicated_count = duplicated.sum()

        if duplicated_count == 0:
            return ValidationResult(
                rule_name=self.name,
                passed=True,
                message=f"Combination of {self.columns} is unique",
                details={"columns": self.columns, "duplicated_count": 0},
            )
        else:
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Combination of {self.columns} has {duplicated_count} duplicate rows",
                details={
                    "columns": self.columns,
                    "duplicated_count": int(duplicated_count),
                },
            )
