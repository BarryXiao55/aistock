"""Row-level diff detection."""

import pandas as pd

from aistock.validation.diff.interface import (
    DiffDetector, DataDiff, DiffResult, DiffType, DiffSeverity,
)


class RowDiffDetector(DiffDetector):
    """行级差异检测器"""

    name = "row_diff"
    description = "检测行级差异（缺失行、新增行）"

    def detect(
        self,
        source_df: pd.DataFrame,
        target_df: pd.DataFrame,
        key_columns: list[str],
        compare_columns: list[str] | None = None,
    ) -> DiffResult:
        """执行行级差异检测"""
        diffs = []

        # 验证主键列
        for col in key_columns:
            if col not in source_df.columns:
                raise ValueError(f"Column '{col}' not found in source DataFrame")
            if col not in target_df.columns:
                raise ValueError(f"Column '{col}' not found in target DataFrame")

        # 构建主键集合
        source_keys = set(source_df[key_columns].apply(tuple, axis=1))
        target_keys = set(target_df[key_columns].apply(tuple, axis=1))

        # 检测源表中有但目标表中没有的记录
        missing_in_target = source_keys - target_keys
        for key in missing_in_target:
            diffs.append(DataDiff(
                diff_type=DiffType.MISSING,
                severity=DiffSeverity.MEDIUM,
                source_index=None,
                target_index=None,
                column=None,
                source_value=key,
                target_value=None,
                description=f"Record {key} exists in source but not in target",
                details={"key": key, "location": "missing_in_target"},
            ))

        # 检测目标表中有但源表中没有的记录
        missing_in_source = target_keys - source_keys
        for key in missing_in_source:
            diffs.append(DataDiff(
                diff_type=DiffType.MISSING,
                severity=DiffSeverity.MEDIUM,
                source_index=None,
                target_index=None,
                column=None,
                source_value=None,
                target_value=key,
                description=f"Record {key} exists in target but not in source",
                details={"key": key, "location": "missing_in_source"},
            ))

        return DiffResult(
            diffs=diffs,
            source_count=len(source_df),
            target_count=len(target_df),
            structural_diffs=0,
            value_diffs=0,
            missing_diffs=len(diffs),
            total_diffs=len(diffs),
        )


class StructuralDiffDetector(DiffDetector):
    """结构差异检测器"""

    name = "structural_diff"
    description = "检测结构差异（Schema 不一致）"

    def detect(
        self,
        source_df: pd.DataFrame,
        target_df: pd.DataFrame,
        key_columns: list[str],
        compare_columns: list[str] | None = None,
    ) -> DiffResult:
        """执行结构差异检测"""
        diffs = []

        # 检测列差异
        source_columns = set(source_df.columns)
        target_columns = set(target_df.columns)

        # 源表有但目标表没有的列
        missing_in_target = source_columns - target_columns
        for col in missing_in_target:
            diffs.append(DataDiff(
                diff_type=DiffType.STRUCTURAL,
                severity=DiffSeverity.HIGH,
                source_index=None,
                target_index=None,
                column=col,
                source_value="exists",
                target_value=None,
                description=f"Column '{col}' exists in source but not in target",
                details={"column": col, "location": "missing_in_target"},
            ))

        # 目标表有但源表没有的列
        missing_in_source = target_columns - source_columns
        for col in missing_in_source:
            diffs.append(DataDiff(
                diff_type=DiffType.STRUCTURAL,
                severity=DiffSeverity.HIGH,
                source_index=None,
                target_index=None,
                column=col,
                source_value=None,
                target_value="exists",
                description=f"Column '{col}' exists in target but not in source",
                details={"column": col, "location": "missing_in_source"},
            ))

        # 检测数据类型差异
        common_columns = source_columns & target_columns
        for col in common_columns:
            source_dtype = str(source_df[col].dtype)
            target_dtype = str(target_df[col].dtype)
            if source_dtype != target_dtype:
                diffs.append(DataDiff(
                    diff_type=DiffType.STRUCTURAL,
                    severity=DiffSeverity.MEDIUM,
                    source_index=None,
                    target_index=None,
                    column=col,
                    source_value=source_dtype,
                    target_value=target_dtype,
                    description=f"Column '{col}' has different data types",
                    details={
                        "column": col,
                        "source_dtype": source_dtype,
                        "target_dtype": target_dtype,
                    },
                ))

        return DiffResult(
            diffs=diffs,
            source_count=len(source_df),
            target_count=len(target_df),
            structural_diffs=len(diffs),
            value_diffs=0,
            missing_diffs=0,
            total_diffs=len(diffs),
        )
