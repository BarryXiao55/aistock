"""Range validation rule."""

import pandas as pd

from aistock.validation.interface import ValidationRule, ValidationResult


class RangeRule(ValidationRule):
    """值域验证规则 - 检查列值是否在指定范围内"""

    name = "range"
    description = "检查列值是否在指定范围内"

    def __init__(self, column: str, min_value: float | None = None, max_value: float | None = None):
        """
        初始化值域规则。

        Args:
            column: 要检查的列名
            min_value: 最小值（可选）
            max_value: 最大值（可选）
        """
        self.column = column
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, data: pd.DataFrame, context: dict | None = None) -> ValidationResult:
        """执行值域验证"""
        if self.column not in data.columns:
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Column '{self.column}' not found",
                details={"column": self.column, "available_columns": list(data.columns)},
            )

        # 检查值域
        violations = []
        column_data = data[self.column].dropna()

        if self.min_value is not None:
            below_min = column_data[column_data < self.min_value]
            if len(below_min) > 0:
                violations.append({
                    "type": "below_min",
                    "count": len(below_min),
                    "min_value": self.min_value,
                    "sample_values": below_min.unique().tolist()[:5],
                })

        if self.max_value is not None:
            above_max = column_data[column_data > self.max_value]
            if len(above_max) > 0:
                violations.append({
                    "type": "above_max",
                    "count": len(above_max),
                    "max_value": self.max_value,
                    "sample_values": above_max.unique().tolist()[:5],
                })

        if not violations:
            return ValidationResult(
                rule_name=self.name,
                passed=True,
                message=f"Column '{self.column}' values are within range [{self.min_value}, {self.max_value}]",
                details={
                    "column": self.column,
                    "min_value": self.min_value,
                    "max_value": self.max_value,
                    "actual_min": float(column_data.min()) if len(column_data) > 0 else None,
                    "actual_max": float(column_data.max()) if len(column_data) > 0 else None,
                },
            )
        else:
            total_violations = sum(v["count"] for v in violations)
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Column '{self.column}' has {total_violations} values out of range",
                details={
                    "column": self.column,
                    "min_value": self.min_value,
                    "max_value": self.max_value,
                    "violations": violations,
                },
            )


class AcceptedValuesRule(ValidationRule):
    """枚举值验证规则 - 检查列值是否在预定义列表中"""

    name = "accepted_values"
    description = "检查列值是否在预定义列表中"

    def __init__(self, column: str, accepted_values: list):
        """
        初始化枚举值规则。

        Args:
            column: 要检查的列名
            accepted_values: 接受的值列表
        """
        self.column = column
        self.accepted_values = set(accepted_values)

    def validate(self, data: pd.DataFrame, context: dict | None = None) -> ValidationResult:
        """执行枚举值验证"""
        if self.column not in data.columns:
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Column '{self.column}' not found",
                details={"column": self.column, "available_columns": list(data.columns)},
            )

        # 检查枚举值
        column_data = data[self.column].dropna()
        unique_values = set(column_data.unique())
        invalid_values = unique_values - self.accepted_values

        if not invalid_values:
            return ValidationResult(
                rule_name=self.name,
                passed=True,
                message=f"Column '{self.column}' values are all accepted",
                details={
                    "column": self.column,
                    "accepted_count": len(self.accepted_values),
                    "actual_count": len(unique_values),
                },
            )
        else:
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Column '{self.column}' has {len(invalid_values)} invalid values",
                details={
                    "column": self.column,
                    "invalid_values": list(invalid_values)[:10],
                    "invalid_count": len(invalid_values),
                },
            )
