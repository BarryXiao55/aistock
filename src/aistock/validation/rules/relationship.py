"""Relationship validation rule."""

import pandas as pd

from aistock.validation.interface import ValidationRule, ValidationResult


class RelationshipRule(ValidationRule):
    """引用完整性验证规则 - 检查外键是否在关联表中存在"""

    name = "relationships"
    description = "检查外键是否在关联表中存在"

    def __init__(self, column: str, reference_df: pd.DataFrame, reference_column: str):
        """
        初始化引用完整性规则。

        Args:
            column: 当前表的外键列名
            reference_df: 关联表 DataFrame
            reference_column: 关联表的主键列名
        """
        self.column = column
        self.reference_df = reference_df
        self.reference_column = reference_column

    def validate(self, data: pd.DataFrame, context: dict | None = None) -> ValidationResult:
        """执行引用完整性验证"""
        # 检查列是否存在
        if self.column not in data.columns:
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Column '{self.column}' not found in source table",
                details={"column": self.column, "available_columns": list(data.columns)},
            )

        if self.reference_column not in self.reference_df.columns:
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Column '{self.reference_column}' not found in reference table",
                details={
                    "reference_column": self.reference_column,
                    "available_columns": list(self.reference_df.columns),
                },
            )

        # 检查引用完整性
        source_values = set(data[self.column].dropna().unique())
        reference_values = set(self.reference_df[self.reference_column].dropna().unique())
        missing_values = source_values - reference_values

        if not missing_values:
            return ValidationResult(
                rule_name=self.name,
                passed=True,
                message=f"All values in '{self.column}' exist in reference table",
                details={
                    "column": self.column,
                    "reference_column": self.reference_column,
                    "source_count": len(source_values),
                    "reference_count": len(reference_values),
                    "missing_count": 0,
                },
            )
        else:
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Found {len(missing_values)} values in '{self.column}' not in reference table",
                details={
                    "column": self.column,
                    "reference_column": self.reference_column,
                    "missing_values": list(missing_values)[:10],
                    "missing_count": len(missing_values),
                },
            )


class CrossReferenceRule(ValidationRule):
    """交叉引用验证规则 - 检查两个表之间的引用完整性"""

    name = "cross_reference"
    description = "检查两个表之间的引用完整性"

    def __init__(
        self,
        source_df: pd.DataFrame,
        source_column: str,
        target_df: pd.DataFrame,
        target_column: str,
        direction: str = "source_to_target",
    ):
        """
        初始化交叉引用规则。

        Args:
            source_df: 源表 DataFrame
            source_column: 源表的列名
            target_df: 目标表 DataFrame
            target_column: 目标表的列名
            direction: 验证方向 "source_to_target" | "target_to_source" | "both"
        """
        self.source_df = source_df
        self.source_column = source_column
        self.target_df = target_df
        self.target_column = target_column
        self.direction = direction

    def validate(self, data: pd.DataFrame | None = None, context: dict | None = None) -> ValidationResult:
        """执行交叉引用验证"""
        # 检查列是否存在
        if self.source_column not in self.source_df.columns:
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Column '{self.source_column}' not found in source table",
                details={"column": self.source_column, "available_columns": list(self.source_df.columns)},
            )

        if self.target_column not in self.target_df.columns:
            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Column '{self.target_column}' not found in target table",
                details={
                    "target_column": self.target_column,
                    "available_columns": list(self.target_df.columns),
                },
            )

        # 检查交叉引用
        source_values = set(self.source_df[self.source_column].dropna().unique())
        target_values = set(self.target_df[self.target_column].dropna().unique())

        # 根据方向检查
        missing_in_target = source_values - target_values if self.direction in ["source_to_target", "both"] else set()
        missing_in_source = target_values - source_values if self.direction in ["target_to_source", "both"] else set()

        if not missing_in_target and not missing_in_source:
            return ValidationResult(
                rule_name=self.name,
                passed=True,
                message="All values match between source and target tables",
                details={
                    "source_column": self.source_column,
                    "target_column": self.target_column,
                    "source_count": len(source_values),
                    "target_count": len(target_values),
                    "missing_in_target": 0,
                    "missing_in_source": 0,
                },
            )
        else:
            issues = []
            if missing_in_target:
                issues.append(f"{len(missing_in_target)} values in source not in target")
            if missing_in_source:
                issues.append(f"{len(missing_in_source)} values in target not in source")

            return ValidationResult(
                rule_name=self.name,
                passed=False,
                message=f"Cross-reference mismatch: {'; '.join(issues)}",
                details={
                    "source_column": self.source_column,
                    "target_column": self.target_column,
                    "missing_in_target": list(missing_in_target)[:10] if missing_in_target else [],
                    "missing_in_source": list(missing_in_source)[:10] if missing_in_source else [],
                    "missing_in_target_count": len(missing_in_target),
                    "missing_in_source_count": len(missing_in_source),
                },
            )
