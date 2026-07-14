"""Test data diff detection module."""

import pandas as pd
import pytest

from aistock.validation.diff.interface import (
    DiffType, DiffSeverity, DataDiff, DiffResult, DiffDetector,
)
from aistock.validation.diff.row_diff import RowDiffDetector, StructuralDiffDetector
from aistock.validation.diff.field_diff import FieldDiffDetector
from aistock.validation.diff.classifier import DiffClassifier


class TestRowDiffDetector:
    """测试 RowDiffDetector"""

    def test_no_differences(self):
        """测试无差异"""
        source_df = pd.DataFrame({"code": ["A", "B"], "value": [1, 2]})
        target_df = pd.DataFrame({"code": ["A", "B"], "value": [1, 2]})

        detector = RowDiffDetector()
        result = detector.detect(source_df, target_df, ["code"])

        assert result.total_diffs == 0
        assert result.missing_diffs == 0

    def test_missing_in_target(self):
        """测试目标表缺失记录"""
        source_df = pd.DataFrame({"code": ["A", "B", "C"], "value": [1, 2, 3]})
        target_df = pd.DataFrame({"code": ["A", "B"], "value": [1, 2]})

        detector = RowDiffDetector()
        result = detector.detect(source_df, target_df, ["code"])

        assert result.total_diffs == 1
        assert result.missing_diffs == 1
        assert result.diffs[0].diff_type == DiffType.MISSING
        assert result.diffs[0].details["location"] == "missing_in_target"

    def test_missing_in_source(self):
        """测试源表缺失记录"""
        source_df = pd.DataFrame({"code": ["A", "B"], "value": [1, 2]})
        target_df = pd.DataFrame({"code": ["A", "B", "C"], "value": [1, 2, 3]})

        detector = RowDiffDetector()
        result = detector.detect(source_df, target_df, ["code"])

        assert result.total_diffs == 1
        assert result.missing_diffs == 1
        assert result.diffs[0].diff_type == DiffType.MISSING
        assert result.diffs[0].details["location"] == "missing_in_source"

    def test_multiple_differences(self):
        """测试多个差异"""
        source_df = pd.DataFrame({"code": ["A", "B", "C"], "value": [1, 2, 3]})
        target_df = pd.DataFrame({"code": ["A", "D"], "value": [1, 4]})

        detector = RowDiffDetector()
        result = detector.detect(source_df, target_df, ["code"])

        assert result.total_diffs == 3  # B, C missing in target; D missing in source
        assert result.missing_diffs == 3

    def test_missing_key_column(self):
        """测试缺失主键列"""
        source_df = pd.DataFrame({"code": ["A"], "value": [1]})
        target_df = pd.DataFrame({"symbol": ["A"], "value": [1]})

        detector = RowDiffDetector()
        with pytest.raises(ValueError, match="not found"):
            detector.detect(source_df, target_df, ["code"])


class TestStructuralDiffDetector:
    """测试 StructuralDiffDetector"""

    def test_no_structural_differences(self):
        """测试无结构差异"""
        source_df = pd.DataFrame({"code": ["A"], "value": [1]})
        target_df = pd.DataFrame({"code": ["A"], "value": [1]})

        detector = StructuralDiffDetector()
        result = detector.detect(source_df, target_df, ["code"])

        assert result.total_diffs == 0
        assert result.structural_diffs == 0

    def test_column_missing_in_target(self):
        """测试目标表缺失列"""
        source_df = pd.DataFrame({"code": ["A"], "value": [1], "extra": [10]})
        target_df = pd.DataFrame({"code": ["A"], "value": [1]})

        detector = StructuralDiffDetector()
        result = detector.detect(source_df, target_df, ["code"])

        assert result.total_diffs == 1
        assert result.structural_diffs == 1
        assert result.diffs[0].diff_type == DiffType.STRUCTURAL
        assert result.diffs[0].column == "extra"

    def test_column_missing_in_source(self):
        """测试源表缺失列"""
        source_df = pd.DataFrame({"code": ["A"], "value": [1]})
        target_df = pd.DataFrame({"code": ["A"], "value": [1], "extra": [10]})

        detector = StructuralDiffDetector()
        result = detector.detect(source_df, target_df, ["code"])

        assert result.total_diffs == 1
        assert result.structural_diffs == 1
        assert result.diffs[0].column == "extra"

    def test_data_type_mismatch(self):
        """测试数据类型不匹配"""
        source_df = pd.DataFrame({"code": ["A"], "value": [1]})
        target_df = pd.DataFrame({"code": ["A"], "value": ["1"]})

        detector = StructuralDiffDetector()
        result = detector.detect(source_df, target_df, ["code"])

        assert result.total_diffs == 1
        assert result.structural_diffs == 1
        assert result.diffs[0].column == "value"


class TestFieldDiffDetector:
    """测试 FieldDiffDetector"""

    def test_no_field_differences(self):
        """测试无字段差异"""
        source_df = pd.DataFrame({"code": ["A", "B"], "value": [1, 2]})
        target_df = pd.DataFrame({"code": ["A", "B"], "value": [1, 2]})

        detector = FieldDiffDetector()
        result = detector.detect(source_df, target_df, ["code"])

        assert result.total_diffs == 0
        assert result.value_diffs == 0

    def test_value_difference(self):
        """测试值差异"""
        source_df = pd.DataFrame({"code": ["A", "B"], "value": [1, 2]})
        target_df = pd.DataFrame({"code": ["A", "B"], "value": [1, 3]})

        detector = FieldDiffDetector()
        result = detector.detect(source_df, target_df, ["code"])

        assert result.total_diffs == 1
        assert result.value_diffs == 1
        assert result.diffs[0].diff_type == DiffType.VALUE
        assert result.diffs[0].column == "value"

    def test_multiple_column_differences(self):
        """测试多列差异"""
        source_df = pd.DataFrame({"code": ["A"], "value1": [1], "value2": [2]})
        target_df = pd.DataFrame({"code": ["A"], "value1": [10], "value2": [20]})

        detector = FieldDiffDetector()
        result = detector.detect(source_df, target_df, ["code"])

        assert result.total_diffs == 2
        assert result.value_diffs == 2

    def test_numeric_tolerance(self):
        """测试数值容差"""
        source_df = pd.DataFrame({"code": ["A"], "value": [1.0]})
        target_df = pd.DataFrame({"code": ["A"], "value": [1.0000001]})

        detector = FieldDiffDetector(tolerance=1e-6)
        result = detector.detect(source_df, target_df, ["code"])

        # 在容差范围内，应该没有差异
        assert result.total_diffs == 0

    def test_string_case_insensitive(self):
        """测试字符串大小写不敏感"""
        source_df = pd.DataFrame({"code": ["A"], "name": ["Apple"]})
        target_df = pd.DataFrame({"code": ["A"], "name": ["apple"]})

        detector = FieldDiffDetector()
        result = detector.detect(source_df, target_df, ["code"])

        # 大小写差异应该被忽略（_values_equal 忽略大小写）
        assert result.total_diffs == 0

    def test_missing_key_column(self):
        """测试缺失主键列"""
        source_df = pd.DataFrame({"code": ["A"], "value": [1]})
        target_df = pd.DataFrame({"symbol": ["A"], "value": [1]})

        detector = FieldDiffDetector()
        with pytest.raises(ValueError, match="not found"):
            detector.detect(source_df, target_df, ["code"])


class TestDiffClassifier:
    """测试 DiffClassifier"""

    def test_classify_severity(self):
        """测试分类严重程度"""
        classifier = DiffClassifier()

        # 测试结构差异
        diff_structural = DataDiff(
            diff_type=DiffType.STRUCTURAL,
            severity=DiffSeverity.MEDIUM,
            source_index=None,
            target_index=None,
            column="test",
            source_value=None,
            target_value=None,
            description="test",
        )
        assert classifier.classify(diff_structural) == DiffSeverity.HIGH

        # 测试缺失差异
        diff_missing = DataDiff(
            diff_type=DiffType.MISSING,
            severity=DiffSeverity.MEDIUM,
            source_index=None,
            target_index=None,
            column=None,
            source_value=None,
            target_value=None,
            description="test",
        )
        assert classifier.classify(diff_missing) == DiffSeverity.MEDIUM

    def test_prioritize(self):
        """测试优先级排序"""
        classifier = DiffClassifier()

        diffs = [
            DataDiff(DiffType.VALUE, DiffSeverity.LOW, None, None, None, None, None, "low"),
            DataDiff(DiffType.STRUCTURAL, DiffSeverity.HIGH, None, None, None, None, None, "high"),
            DataDiff(DiffType.MISSING, DiffSeverity.CRITICAL, None, None, None, None, None, "critical"),
        ]

        prioritized = classifier.prioritize(diffs)
        assert prioritized[0].severity == DiffSeverity.CRITICAL
        assert prioritized[1].severity == DiffSeverity.HIGH
        assert prioritized[2].severity == DiffSeverity.LOW

    def test_summarize(self):
        """测试生成摘要"""
        classifier = DiffClassifier()

        result = DiffResult(
            diffs=[
                DataDiff(DiffType.VALUE, DiffSeverity.MEDIUM, None, None, "col1", None, None, "test1"),
                DataDiff(DiffType.MISSING, DiffSeverity.HIGH, None, None, None, None, None, "test2"),
            ],
            source_count=10,
            target_count=10,
            structural_diffs=0,
            value_diffs=1,
            missing_diffs=1,
            total_diffs=2,
        )

        summary = classifier.summarize(result)
        assert summary["total_diffs"] == 2
        assert "value" in summary["by_type"]
        assert "missing" in summary["by_type"]
        assert "high" in summary["by_severity"]

    def test_filter_by_type(self):
        """测试按类型过滤"""
        classifier = DiffClassifier()

        diffs = [
            DataDiff(DiffType.VALUE, DiffSeverity.MEDIUM, None, None, None, None, None, "test1"),
            DataDiff(DiffType.MISSING, DiffSeverity.HIGH, None, None, None, None, None, "test2"),
        ]

        filtered = classifier.filter_by_type(diffs, DiffType.VALUE)
        assert len(filtered) == 1
        assert filtered[0].diff_type == DiffType.VALUE

    def test_filter_by_severity(self):
        """测试按严重程度过滤"""
        classifier = DiffClassifier()

        diffs = [
            DataDiff(DiffType.VALUE, DiffSeverity.LOW, None, None, None, None, None, "test1"),
            DataDiff(DiffType.MISSING, DiffSeverity.HIGH, None, None, None, None, None, "test2"),
        ]

        filtered = classifier.filter_by_severity(diffs, DiffSeverity.MEDIUM)
        assert len(filtered) == 1
        assert filtered[0].severity == DiffSeverity.HIGH

    def test_to_dataframe(self):
        """测试转换为 DataFrame"""
        classifier = DiffClassifier()

        diffs = [
            DataDiff(DiffType.VALUE, DiffSeverity.MEDIUM, None, None, "col1", 1, 2, "test"),
        ]

        df = classifier.to_dataframe(diffs)
        assert len(df) == 1
        assert df.iloc[0]["diff_type"] == "value"
        assert df.iloc[0]["column"] == "col1"


class TestDataDiff:
    """测试 DataDiff"""

    def test_to_dict(self):
        """测试转换为字典"""
        diff = DataDiff(
            diff_type=DiffType.VALUE,
            severity=DiffSeverity.MEDIUM,
            source_index=0,
            target_index=1,
            column="test",
            source_value=1,
            target_value=2,
            description="test diff",
            details={"key": "value"},
        )
        d = diff.to_dict()
        assert d["diff_type"] == "value"
        assert d["severity"] == "medium"
        assert d["column"] == "test"


class TestDiffResult:
    """测试 DiffResult"""

    def test_diff_rate(self):
        """测试差异率"""
        result = DiffResult(
            diffs=[],
            source_count=10,
            target_count=10,
            structural_diffs=0,
            value_diffs=0,
            missing_diffs=0,
            total_diffs=5,
        )
        assert result.diff_rate == 0.25  # 5 / (10 + 10)

    def test_diff_rate_zero_total(self):
        """测试零总数的差异率"""
        result = DiffResult(
            diffs=[],
            source_count=0,
            target_count=0,
            structural_diffs=0,
            value_diffs=0,
            missing_diffs=0,
            total_diffs=0,
        )
        assert result.diff_rate == 0.0

    def test_get_diffs_by_type(self):
        """测试按类型获取差异"""
        result = DiffResult(
            diffs=[
                DataDiff(DiffType.VALUE, DiffSeverity.MEDIUM, None, None, None, None, None, "test1"),
                DataDiff(DiffType.MISSING, DiffSeverity.HIGH, None, None, None, None, None, "test2"),
            ],
            source_count=10,
            target_count=10,
            structural_diffs=0,
            value_diffs=1,
            missing_diffs=1,
            total_diffs=2,
        )

        value_diffs = result.get_diffs_by_type(DiffType.VALUE)
        assert len(value_diffs) == 1
        assert value_diffs[0].diff_type == DiffType.VALUE

    def test_to_dict(self):
        """测试转换为字典"""
        result = DiffResult(
            diffs=[],
            source_count=10,
            target_count=10,
            structural_diffs=0,
            value_diffs=0,
            missing_diffs=0,
            total_diffs=0,
        )
        d = result.to_dict()
        assert d["source_count"] == 10
        assert d["total_diffs"] == 0
