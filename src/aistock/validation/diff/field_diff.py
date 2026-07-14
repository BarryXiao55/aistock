"""Field-level diff detection."""

from typing import Any

import pandas as pd
import numpy as np

from aistock.validation.diff.interface import (
    DiffDetector, DataDiff, DiffResult, DiffType, DiffSeverity,
)


class FieldDiffDetector(DiffDetector):
    """字段级差异检测器"""

    name = "field_diff"
    description = "检测字段级差异（值不同）"

    def __init__(self, tolerance: float = 1e-6):
        """
        初始化字段级差异检测器。

        Args:
            tolerance: 数值比较容差
        """
        self.tolerance = tolerance

    def detect(
        self,
        source_df: pd.DataFrame,
        target_df: pd.DataFrame,
        key_columns: list[str],
        compare_columns: list[str] | None = None,
    ) -> DiffResult:
        """执行字段级差异检测"""
        diffs = []

        # 验证主键列
        for col in key_columns:
            if col not in source_df.columns:
                raise ValueError(f"Column '{col}' not found in source DataFrame")
            if col not in target_df.columns:
                raise ValueError(f"Column '{col}' not found in target DataFrame")

        # 确定要比较的列
        if compare_columns is None:
            compare_columns = [col for col in source_df.columns if col not in key_columns]

        # 构建主键索引
        source_indexed = source_df.set_index(key_columns)
        target_indexed = target_df.set_index(key_columns)

        # 找到共同的主键
        common_keys = set(source_indexed.index) & set(target_indexed.index)

        # 逐行比较
        for key in common_keys:
            source_row = source_indexed.loc[key]
            target_row = target_indexed.loc[key]

            # 如果有重复行，取第一行
            if isinstance(source_row, pd.DataFrame):
                source_row = source_row.iloc[0]
            if isinstance(target_row, pd.DataFrame):
                target_row = target_row.iloc[0]

            # 比较每个字段
            for col in compare_columns:
                if col not in source_df.columns or col not in target_df.columns:
                    continue

                source_val = source_row[col] if col in source_row.index else None
                target_val = target_row[col] if col in target_row.index else None

                # 比较值
                if not self._values_equal(source_val, target_val):
                    severity = self._classify_severity(source_val, target_val)
                    diffs.append(DataDiff(
                        diff_type=DiffType.VALUE,
                        severity=severity,
                        source_index=None,
                        target_index=None,
                        column=col,
                        source_value=source_val,
                        target_value=target_val,
                        description=f"Value mismatch in column '{col}' for key {key}",
                        details={
                            "key": key,
                            "column": col,
                            "source_value": str(source_val),
                            "target_value": str(target_val),
                        },
                    ))

        return DiffResult(
            diffs=diffs,
            source_count=len(source_df),
            target_count=len(target_df),
            structural_diffs=0,
            value_diffs=len(diffs),
            missing_diffs=0,
            total_diffs=len(diffs),
        )

    def _values_equal(self, val1: Any, val2: Any) -> bool:
        """比较两个值是否相等"""
        # 处理 NaN
        if pd.isna(val1) and pd.isna(val2):
            return True
        if pd.isna(val1) or pd.isna(val2):
            return False

        # 数值比较（使用容差）
        if isinstance(val1, (int, float, np.number)) and isinstance(val2, (int, float, np.number)):
            return abs(float(val1) - float(val2)) <= self.tolerance

        # 字符串比较（忽略大小写和空格）
        if isinstance(val1, str) and isinstance(val2, str):
            return val1.strip().lower() == val2.strip().lower()

        # 其他类型直接比较
        return val1 == val2

    def _classify_severity(self, val1: Any, val2: Any) -> DiffSeverity:
        """分类差异严重程度"""
        # 数值差异
        if isinstance(val1, (int, float, np.number)) and isinstance(val2, (int, float, np.number)):
            diff = abs(float(val1) - float(val2))
            if diff > 1000:
                return DiffSeverity.CRITICAL
            elif diff > 100:
                return DiffSeverity.HIGH
            elif diff > 10:
                return DiffSeverity.MEDIUM
            else:
                return DiffSeverity.LOW

        # 字符串差异
        if isinstance(val1, str) and isinstance(val2, str):
            if val1.strip().lower() == val2.strip().lower():
                return DiffSeverity.LOW  # 仅大小写或空格差异
            return DiffSeverity.MEDIUM

        # 其他类型
        return DiffSeverity.MEDIUM
