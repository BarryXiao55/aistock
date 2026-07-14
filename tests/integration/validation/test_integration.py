"""Integration tests for CrossValidator."""

import logging
from datetime import date, datetime

import pandas as pd
import pytest

from aistock.validation.interface import ValidationRule, ValidationResult
from aistock.validation.rules.uniqueness import UniqueRule, UniqueCombinationRule
from aistock.validation.rules.nullability import NotNullRule
from aistock.validation.rules.range import RangeRule, AcceptedValuesRule
from aistock.validation.linkage.interface import RecordLinker, LinkageResult
from aistock.validation.linkage.exact_match import ExactMatcher
from aistock.validation.linkage.fuzzy_match import FuzzyMatcher
from aistock.validation.diff.interface import DiffResult, DiffType, DiffSeverity
from aistock.validation.diff.row_diff import RowDiffDetector, StructuralDiffDetector
from aistock.validation.diff.field_diff import FieldDiffDetector
from aistock.validation.diff.classifier import DiffClassifier
from aistock.validation.resolver.interface import ConflictResolver, Conflict, ResolutionResult
from aistock.validation.resolver.strategies import PriorityResolver, TimestampResolver
from aistock.validation.reporting.reporter import ReportGenerator, ValidationReport
from aistock.validation.reporting.monitor import ValidationMonitor, MonitoringConfig, AlertLevel


class TestCrossValidatorIntegration:
    """CrossValidator 集成测试"""

    def test_full_validation_flow(self):
        """测试完整验证流程"""
        # 1. 准备测试数据
        akstock_df = pd.DataFrame({
            "code": ["000001.SZ", "600000.SH", "000002.SZ"],
            "trade_date": [date(2025, 1, 2), date(2025, 1, 2), date(2025, 1, 2)],
            "close": [10.5, 12.3, 8.7],
            "volume": [1000000, 1500000, 800000],
        })

        baostock_df = pd.DataFrame({
            "code": ["000001.SZ", "600000.SH", "000003.SZ"],
            "trade_date": [date(2025, 1, 2), date(2025, 1, 2), date(2025, 1, 2)],
            "close": [10.5, 12.5, 9.1],
            "volume": [1000000, 1500000, 750000],
        })

        # 2. 执行记录链接
        matcher = ExactMatcher()
        linkage_result = matcher.link(akstock_df, baostock_df, ["code"], ["code"])

        assert linkage_result.matched_count == 2  # 000001.SZ 和 600000.SH

        # 3. 执行差异检测
        detector = FieldDiffDetector()
        diff_result = detector.detect(
            akstock_df, baostock_df,
            ["code"], ["close", "volume"]
        )

        # 应该有差异（600000.SH 的 close 和 volume）
        assert diff_result.total_diffs > 0

        # 4. 执行冲突解决
        conflicts = []
        for diff in diff_result.diffs:
            conflicts.append(Conflict(
                column=diff.column,
                source_index=0,
                target_index=0,
                source_value=diff.source_value,
                target_value=diff.target_value,
                details={"source_name": "akstock", "target_name": "baostock"},
            ))

        resolver = PriorityResolver(source_priority={"akstock": 1, "baostock": 2})
        resolution_result = resolver.resolve(conflicts)

        assert resolution_result.resolution_rate == 1.0

        # 5. 生成报告
        generator = ReportGenerator()
        report = generator.generate(
            "akstock", "baostock",
            diff_result=diff_result,
            resolution_result=resolution_result,
        )

        assert report.source_name == "akstock"
        assert report.target_name == "baostock"
        assert "quality_score" in report.summary

        # 6. 检查监控
        monitor = ValidationMonitor()
        alerts = monitor.check(diff_result, resolution_result)

        # 根据差异率可能有告警
        assert isinstance(alerts, list)

    def test_validation_with_multiple_sources(self):
        """测试多数据源验证"""
        # 准备三个数据源的数据
        akstock_df = pd.DataFrame({
            "code": ["000001.SZ", "600000.SH"],
            "close": [10.5, 12.3],
        })

        baostock_df = pd.DataFrame({
            "code": ["000001.SZ", "600000.SH"],
            "close": [10.5, 12.5],
        })

        tushare_df = pd.DataFrame({
            "code": ["000001.SZ", "600000.SH"],
            "close": [10.6, 12.4],
        })

        # 执行差异检测
        detector = FieldDiffDetector()

        diff_ak_bs = detector.detect(akstock_df, baostock_df, ["code"])
        diff_ak_ts = detector.detect(akstock_df, tushare_df, ["code"])

        # 生成报告
        generator = ReportGenerator()
        report_ak_bs = generator.generate("akstock", "baostock", diff_result=diff_ak_bs)
        report_ak_ts = generator.generate("akstock", "tushare", diff_result=diff_ak_ts)

        assert report_ak_bs.source_name == "akstock"
        assert report_ak_ts.source_name == "akstock"

    def test_validation_with_different_schemas(self):
        """测试不同 Schema 的验证"""
        # 日线数据
        daily_df = pd.DataFrame({
            "code": ["000001.SZ"],
            "trade_date": [date(2025, 1, 2)],
            "close": [10.5],
        })

        # 财务数据
        finance_df = pd.DataFrame({
            "code": ["000001.SZ"],
            "report_period": ["2025Q1"],
            "revenue": [1000000],
        })

        # 执行结构差异检测
        detector = StructuralDiffDetector()
        diff_result = detector.detect(daily_df, finance_df, ["code"])

        # 应该有结构差异
        assert diff_result.structural_diffs > 0


class TestValidationRulesIntegration:
    """验证规则集成测试"""

    def test_rule_chain_execution(self):
        """测试规则链执行"""
        df = pd.DataFrame({
            "code": ["A", "B", "C"],
            "value": [10.0, 20.0, 30.0],
            "status": ["active", "inactive", "active"],
        })

        rules = [
            UniqueRule("code"),
            NotNullRule("code"),
            RangeRule("value", min_value=0, max_value=100),
            AcceptedValuesRule("status", ["active", "inactive", "pending"]),
        ]

        results = []
        for rule in rules:
            result = rule.validate(df)
            results.append(result)

        # 所有规则都应通过
        assert all(r.passed for r in results)

    def test_rule_chain_with_failures(self):
        """测试带失败的规则链"""
        df = pd.DataFrame({
            "code": ["A", "A", "C"],  # 重复值
            "value": [10.0, 20.0, 150.0],  # 超出范围
        })

        rules = [
            UniqueRule("code"),
            RangeRule("value", min_value=0, max_value=100),
        ]

        results = []
        for rule in rules:
            result = rule.validate(df)
            results.append(result)

        # 第一个规则失败（重复值）
        assert results[0].passed is False
        # 第二个规则失败（超出范围）
        assert results[1].passed is False


class TestRecordLinkageIntegration:
    """记录链接集成测试"""

    def test_linkage_with_different_algorithms(self):
        """测试不同算法的链接"""
        source_df = pd.DataFrame({
            "code": ["A", "B", "C"],
            "name": ["Apple", "Google", "Microsoft"],
        })
        target_df = pd.DataFrame({
            "symbol": ["A", "B", "D"],
            "company": ["Apple Inc", "Google LLC", "Delta Ltd"],
        })

        # 精确匹配
        exact_matcher = ExactMatcher()
        exact_result = exact_matcher.link(source_df, target_df, ["code"], ["symbol"])
        assert exact_result.matched_count == 2

        # 模糊匹配
        fuzzy_matcher = FuzzyMatcher()
        fuzzy_result = fuzzy_matcher.link(
            source_df, target_df,
            ["name"], ["company"],
            threshold=0.6,
        )
        # 应该有更多匹配
        assert fuzzy_result.matched_count >= 2


class TestDiffDetectionIntegration:
    """差异检测集成测试"""

    def test_comprehensive_diff_detection(self):
        """测试综合差异检测"""
        source_df = pd.DataFrame({
            "code": ["A", "B", "C"],
            "close": [10.0, 20.0, 30.0],
            "volume": [1000, 2000, 3000],
        })

        target_df = pd.DataFrame({
            "code": ["A", "B", "D"],  # C 缺失，D 新增
            "close": [10.0, 21.0, 25.0],  # B 有差异
            "volume": [1000, 2000, 2500],
        })

        # 行级差异检测
        row_detector = RowDiffDetector()
        row_result = row_detector.detect(source_df, target_df, ["code"])
        assert row_result.missing_diffs > 0

        # 字段级差异检测
        field_detector = FieldDiffDetector()
        field_result = field_detector.detect(source_df, target_df, ["code"])
        assert field_result.value_diffs > 0

        # 差异分类
        classifier = DiffClassifier()
        summary = classifier.summarize(field_result)
        assert "by_type" in summary
        assert "by_severity" in summary


class TestConflictResolutionIntegration:
    """冲突解决集成测试"""

    def test_resolution_strategies_comparison(self):
        """测试不同解决策略的比较"""
        conflicts = [
            Conflict(
                column="close",
                source_index=0,
                target_index=0,
                source_value=10.0,
                target_value=12.0,
                source_timestamp=datetime(2025, 1, 2),
                target_timestamp=datetime(2025, 1, 3),
                details={"source_name": "akstock", "target_name": "baostock"},
            )
        ]

        # 优先级策略
        priority_resolver = PriorityResolver(source_priority={"akstock": 1, "baostock": 2})
        priority_result = priority_resolver.resolve(conflicts)
        assert priority_result.resolutions[0].resolved_value == 10.0

        # 时间戳策略
        timestamp_resolver = TimestampResolver()
        timestamp_result = timestamp_resolver.resolve(conflicts)
        assert timestamp_result.resolutions[0].resolved_value == 12.0


class TestReportingIntegration:
    """报告生成集成测试"""

    def test_report_generation_with_all_components(self):
        """测试使用所有组件生成报告"""
        # 准备数据
        source_df = pd.DataFrame({
            "code": ["A", "B"],
            "close": [10.0, 20.0],
        })
        target_df = pd.DataFrame({
            "code": ["A", "B"],
            "close": [10.5, 19.5],
        })

        # 执行差异检测
        detector = FieldDiffDetector()
        diff_result = detector.detect(source_df, target_df, ["code"])

        # 执行冲突解决
        conflicts = []
        for diff in diff_result.diffs:
            conflicts.append(Conflict(
                column=diff.column,
                source_index=0,
                target_index=0,
                source_value=diff.source_value,
                target_value=diff.target_value,
            ))

        resolver = PriorityResolver()
        resolution_result = resolver.resolve(conflicts)

        # 生成报告
        generator = ReportGenerator()
        report = generator.generate(
            "source", "target",
            diff_result=diff_result,
            resolution_result=resolution_result,
        )

        # 验证报告内容
        assert report.report_id.startswith("VR-")
        assert "quality_score" in report.summary
        assert len(report.recommendations) > 0


class TestMonitoringIntegration:
    """监控集成测试"""

    def test_monitoring_with_alerts(self):
        """测试带告警的监控"""
        # 创建高差异率的场景
        diff_result = DiffResult(
            diffs=[],
            source_count=100,
            target_count=100,
            structural_diffs=0,
            value_diffs=0,
            missing_diffs=0,
            total_diffs=30,  # 15% > 10% 警告阈值
        )

        monitor = ValidationMonitor()
        alerts = monitor.check(diff_result, None)

        # 应该有警告
        assert len(alerts) > 0
        assert any(a.level == AlertLevel.WARNING for a in alerts)

        # 获取告警摘要
        summary = monitor.get_alert_summary()
        assert summary["total_alerts"] > 0
