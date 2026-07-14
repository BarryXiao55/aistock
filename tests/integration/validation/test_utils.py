"""Test utilities for validation integration tests."""

from datetime import datetime

import pandas as pd

from aistock.validation.diff.interface import DataDiff, DiffType, DiffSeverity
from aistock.validation.resolver.interface import Conflict


def create_test_dataframes():
    """创建测试用的 DataFrame"""
    source_df = pd.DataFrame({
        "code": ["000001.SZ", "600000.SH", "000002.SZ", "600036.SH"],
        "trade_date": [
            pd.Timestamp("2025-01-02"),
            pd.Timestamp("2025-01-02"),
            pd.Timestamp("2025-01-02"),
            pd.Timestamp("2025-01-02"),
        ],
        "close": [10.5, 12.3, 8.7, 15.2],
        "volume": [1000000, 1500000, 800000, 1200000],
    })

    target_df = pd.DataFrame({
        "code": ["000001.SZ", "600000.SH", "000003.SZ"],
        "trade_date": [
            pd.Timestamp("2025-01-02"),
            pd.Timestamp("2025-01-02"),
            pd.Timestamp("2025-01-02"),
        ],
        "close": [10.5, 12.5, 9.1],
        "volume": [1000000, 1500000, 750000],
    })

    return source_df, target_df


def create_conflicts_from_diffs(diffs):
    """从差异列表创建冲突列表"""
    conflicts = []
    for diff in diffs:
        conflicts.append(Conflict(
            column=diff.column,
            source_index=diff.source_index or 0,
            target_index=diff.target_index or 0,
            source_value=diff.source_value,
            target_value=diff.target_value,
            details={"source_name": "source", "target_name": "target"},
        ))
    return conflicts


def assert_valid_report(report):
    """验证报告的有效性"""
    assert report.report_id is not None
    assert report.source_name is not None
    assert report.target_name is not None
    assert report.generated_at is not None
    assert isinstance(report.summary, dict)
    assert isinstance(report.recommendations, list)


def assert_valid_diff_result(result):
    """验证差异结果的有效性"""
    assert result.source_count >= 0
    assert result.target_count >= 0
    assert result.total_diffs >= 0
    assert result.structural_diffs >= 0
    assert result.value_diffs >= 0
    assert result.missing_diffs >= 0
    assert 0 <= result.diff_rate <= 1


def assert_valid_resolution_result(result):
    """验证解决结果的有效性"""
    assert result.total_conflicts >= 0
    assert result.resolved_count >= 0
    assert result.unresolved_count >= 0
    assert 0 <= result.resolution_rate <= 1
