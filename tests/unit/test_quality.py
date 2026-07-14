"""Test quality scorer."""

from datetime import date, timedelta

import pandas as pd
import pytest

from aistock.cleaning.quality import QualityScorer
from aistock.observability.quality import QualityReport, QualityIssue
from aistock.pipeline.cleaner import STEPS_BASELINE


class TestQualityScorer:
    """测试 QualityScorer"""

    def test_calculates_completeness(self):
        """测试计算完整性评分"""
        df = pd.DataFrame([
            {"code": "000001.SZ", "close": 10.0, "volume": 1000000},
            {"code": "600000.SH", "close": 15.0, "volume": None},
        ])
        scorer = QualityScorer()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = scorer.clean(df, ctx)
        assert "quality_score" in result.columns
        # 有一个缺失值，完整性应该 < 100%
        assert result["quality_score"].iloc[0] < 100.0

    def test_calculates_consistency(self):
        """测试计算一致性评分"""
        df = pd.DataFrame([
            {"code": "000001.SZ", "close": 10.0},
            {"code": "000001.SZ", "close": 10.0},  # 重复行
        ])
        scorer = QualityScorer()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = scorer.clean(df, ctx)
        assert "quality_score" in result.columns
        # 有重复行，一致性应该 < 100%
        assert result["quality_score"].iloc[0] < 100.0

    def test_calculates_timeliness(self):
        """测试计算时效性评分"""
        # 创建一个有旧日期的数据
        old_date = date.today() - timedelta(days=30)
        df = pd.DataFrame([
            {"code": "000001.SZ", "trade_date": old_date, "close": 10.0},
        ])
        scorer = QualityScorer()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = scorer.clean(df, ctx)
        assert "quality_score" in result.columns
        # 30天前的数据，时效性应该降低
        assert result["quality_score"].iloc[0] < 100.0

    def test_calculates_accuracy(self):
        """测试计算准确性评分"""
        df = pd.DataFrame([
            {"code": "000001.SZ", "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2, "volume": 1000000},
            {"code": "600000.SH", "open": 15.0, "high": 14.5, "low": 15.2, "close": 15.1, "volume": -1000},  # high < low, negative volume
        ])
        scorer = QualityScorer()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = scorer.clean(df, ctx)
        assert "quality_score" in result.columns
        # 有数据质量问题，准确性应该降低
        assert result["quality_score"].iloc[0] < 100.0

    def test_calculates_quality_score(self):
        """测试计算综合质量评分"""
        df = pd.DataFrame([
            {"code": "000001.SZ", "close": 10.0, "volume": 1000000},
            {"code": "600000.SH", "close": 15.0, "volume": 1500000},
        ])
        scorer = QualityScorer()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = scorer.clean(df, ctx)
        assert "quality_score" in result.columns
        # 完美数据，质量评分应该很高
        assert result["quality_score"].iloc[0] >= 90.0

    def test_marks_quality_grade(self):
        """测试标记质量等级"""
        df = pd.DataFrame([
            {"code": "000001.SZ", "close": 10.0, "volume": 1000000},
        ])
        scorer = QualityScorer()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = scorer.clean(df, ctx)
        assert "quality_grade" in result.columns
        assert result["quality_grade"].iloc[0] in ["A", "B", "C", "D"]

    def test_validate_passes_on_valid_data(self):
        """测试有效数据通过校验"""
        df = pd.DataFrame([
            {"quality_score": 95.0},
        ])
        scorer = QualityScorer()
        issues = scorer.validate(df)
        assert len(issues) == 0

    def test_validate_detects_missing_quality_score(self):
        """测试检测缺失质量评分"""
        df = pd.DataFrame([
            {"code": "000001.SZ"},
        ])
        scorer = QualityScorer()
        issues = scorer.validate(df)
        assert len(issues) > 0
        assert any("quality_score" in i for i in issues)

    def test_validate_detects_invalid_quality_score(self):
        """测试检测无效质量评分"""
        df = pd.DataFrame([
            {"quality_score": 150.0},  # 超出范围
        ])
        scorer = QualityScorer()
        issues = scorer.validate(df)
        assert len(issues) > 0
        assert any("quality_score" in i for i in issues)

    def test_generate_report(self):
        """测试生成质量报告"""
        df = pd.DataFrame([
            {"code": "000001.SZ", "close": 10.0, "volume": 1000000},
            {"code": "600000.SH", "close": 15.0, "volume": 1500000},
        ])
        scorer = QualityScorer()
        report = scorer.generate_report(df, "StockDailySchema", "stock/2025/01")
        assert isinstance(report, QualityReport)
        assert report.schema_name == "StockDailySchema"
        assert report.partition_key == "stock/2025/01"
        assert report.total_records == 2
        assert report.quality_score >= 90.0
        assert report.quality_grade == "A"

    def test_generate_report_with_issues(self):
        """测试生成有问题的质量报告"""
        df = pd.DataFrame([
            {"code": "000001.SZ", "close": 10.0, "volume": 1000000},
            {"code": "600000.SH", "close": None, "volume": None},  # 缺失值
        ])
        scorer = QualityScorer()
        report = scorer.generate_report(df, "StockDailySchema", "stock/2025/01")
        assert isinstance(report, QualityReport)
        assert report.quality_score < 100.0
        assert len(report.issues) > 0

    def test_empty_dataframe(self):
        """测试空 DataFrame"""
        df = pd.DataFrame()
        scorer = QualityScorer()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = scorer.clean(df, ctx)
        assert len(result) == 0


class TestQualityReport:
    """测试 QualityReport"""

    def test_quality_grade_a(self):
        """测试质量等级 A"""
        report = QualityReport(
            schema_name="test",
            partition_key="test",
            total_records=100,
            quality_score=95.0,
            completeness=95.0,
            consistency=95.0,
            timeliness=95.0,
            accuracy=95.0,
        )
        assert report.quality_grade == "A"

    def test_quality_grade_b(self):
        """测试质量等级 B"""
        report = QualityReport(
            schema_name="test",
            partition_key="test",
            total_records=100,
            quality_score=75.0,
            completeness=75.0,
            consistency=75.0,
            timeliness=75.0,
            accuracy=75.0,
        )
        assert report.quality_grade == "B"

    def test_quality_grade_c(self):
        """测试质量等级 C"""
        report = QualityReport(
            schema_name="test",
            partition_key="test",
            total_records=100,
            quality_score=55.0,
            completeness=55.0,
            consistency=55.0,
            timeliness=55.0,
            accuracy=55.0,
        )
        assert report.quality_grade == "C"

    def test_quality_grade_d(self):
        """测试质量等级 D"""
        report = QualityReport(
            schema_name="test",
            partition_key="test",
            total_records=100,
            quality_score=30.0,
            completeness=30.0,
            consistency=30.0,
            timeliness=30.0,
            accuracy=30.0,
        )
        assert report.quality_grade == "D"

    def test_to_dict(self):
        """测试转换为字典"""
        report = QualityReport(
            schema_name="test",
            partition_key="test",
            total_records=100,
            quality_score=95.0,
            completeness=95.0,
            consistency=95.0,
            timeliness=95.0,
            accuracy=95.0,
        )
        d = report.to_dict()
        assert d["schema_name"] == "test"
        assert d["quality_score"] == 95.0
        assert d["quality_grade"] == "A"


class TestSTEPS_BASELINE:
    """测试 STEPS_BASELINE 配置"""

    def test_baseline_steps_are_defined(self):
        """测试基线步骤已定义"""
        assert len(STEPS_BASELINE) == 8

    def test_baseline_steps_are_cleaning_steps(self):
        """测试基线步骤都是 CleaningStep 实例"""
        for step in STEPS_BASELINE:
            assert isinstance(step, QualityScorer) or hasattr(step, 'clean')

    def test_baseline_step_names(self):
        """测试基线步骤名称"""
        names = [step.name for step in STEPS_BASELINE]
        assert "quality_scorer" in names
