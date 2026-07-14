"""Diff classifier for categorizing and prioritizing differences."""

from collections import Counter

import pandas as pd

from aistock.validation.diff.interface import (
    DataDiff, DiffResult, DiffType, DiffSeverity,
)


class DiffClassifier:
    """差异分类器"""

    def __init__(self):
        """初始化差异分类器"""
        self._severity_rules = {
            DiffType.STRUCTURAL: DiffSeverity.HIGH,
            DiffType.MISSING: DiffSeverity.MEDIUM,
            DiffType.VALUE: DiffSeverity.MEDIUM,
            DiffType.TEMPORAL: DiffSeverity.LOW,
            DiffType.GRANULARITY: DiffSeverity.HIGH,
        }

    def classify(self, diff: DataDiff) -> DiffSeverity:
        """分类差异严重程度"""
        # 使用自定义规则
        if diff.severity != DiffSeverity.MEDIUM:
            return diff.severity

        # 使用默认规则
        return self._severity_rules.get(diff.diff_type, DiffSeverity.MEDIUM)

    def prioritize(self, diffs: list[DataDiff]) -> list[DataDiff]:
        """按优先级排序差异"""
        severity_order = {
            DiffSeverity.CRITICAL: 0,
            DiffSeverity.HIGH: 1,
            DiffSeverity.MEDIUM: 2,
            DiffSeverity.LOW: 3,
        }
        return sorted(diffs, key=lambda d: severity_order.get(d.severity, 4))

    def summarize(self, result: DiffResult) -> dict:
        """生成差异摘要"""
        # 按类型统计
        type_counts = Counter(diff.diff_type.value for diff in result.diffs)

        # 按严重程度统计
        severity_counts = Counter(diff.severity.value for diff in result.diffs)

        # 按列统计
        column_counts = Counter(diff.column for diff in result.diffs if diff.column)

        return {
            "total_diffs": result.total_diffs,
            "diff_rate": result.diff_rate,
            "by_type": dict(type_counts),
            "by_severity": dict(severity_counts),
            "by_column": dict(column_counts.most_common(10)),
            "top_issues": [
                {
                    "type": diff.diff_type.value,
                    "severity": diff.severity.value,
                    "column": diff.column,
                    "description": diff.description,
                }
                for diff in self.prioritize(result.diffs)[:5]
            ],
        }

    def filter_by_type(
        self, diffs: list[DataDiff], diff_type: DiffType
    ) -> list[DataDiff]:
        """按类型过滤差异"""
        return [diff for diff in diffs if diff.diff_type == diff_type]

    def filter_by_severity(
        self, diffs: list[DataDiff], min_severity: DiffSeverity
    ) -> list[DataDiff]:
        """按严重程度过滤差异"""
        severity_order = {
            DiffSeverity.LOW: 0,
            DiffSeverity.MEDIUM: 1,
            DiffSeverity.HIGH: 2,
            DiffSeverity.CRITICAL: 3,
        }
        min_level = severity_order.get(min_severity, 0)
        return [
            diff
            for diff in diffs
            if severity_order.get(diff.severity, 0) >= min_level
        ]

    def to_dataframe(self, diffs: list[DataDiff]) -> pd.DataFrame:
        """将差异列表转换为 DataFrame"""
        if not diffs:
            return pd.DataFrame()

        records = []
        for diff in diffs:
            records.append({
                "diff_type": diff.diff_type.value,
                "severity": diff.severity.value,
                "column": diff.column,
                "source_value": str(diff.source_value) if diff.source_value is not None else None,
                "target_value": str(diff.target_value) if diff.target_value is not None else None,
                "description": diff.description,
            })

        return pd.DataFrame(records)
