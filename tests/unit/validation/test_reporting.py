"""Test reporting and monitoring module."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from aistock.validation.diff.interface import DiffResult, DataDiff, DiffType, DiffSeverity
from aistock.validation.resolver.interface import ResolutionResult, Resolution, Conflict
from aistock.validation.reporting.reporter import ReportGenerator, ValidationReport
from aistock.validation.reporting.monitor import (
    ValidationMonitor, MonitoringConfig, Alert, AlertLevel,
)


class TestReportGenerator:
    """测试 ReportGenerator"""

    def test_generate_report(self):
        """测试生成报告"""
        diff_result = DiffResult(
            diffs=[
                DataDiff(DiffType.VALUE, DiffSeverity.MEDIUM, None, None, "close", 10, 12, "test"),
            ],
            source_count=100,
            target_count=100,
            structural_diffs=0,
            value_diffs=1,
            missing_diffs=0,
            total_diffs=1,
        )

        generator = ReportGenerator()
        report = generator.generate("akstock", "baostock", diff_result=diff_result)

        assert isinstance(report, ValidationReport)
        assert report.source_name == "akstock"
        assert report.target_name == "baostock"
        assert report.diff_result == diff_result
        assert "diff_summary" in report.summary

    def test_generate_report_with_resolution(self):
        """测试带解决结果的报告"""
        conflict = Conflict(
            column="close",
            source_index=0,
            target_index=0,
            source_value=10.0,
            target_value=12.0,
        )
        resolution = Resolution(
            conflict=conflict,
            resolved_value=10.0,
            resolution_method="priority",
            confidence=0.9,
        )
        resolution_result = ResolutionResult(
            resolutions=[resolution],
            total_conflicts=1,
            resolved_count=1,
            unresolved_count=0,
        )

        generator = ReportGenerator()
        report = generator.generate(
            "akstock", "baostock",
            resolution_result=resolution_result,
        )

        assert report.resolution_result == resolution_result
        assert "resolution_summary" in report.summary

    def test_quality_score_calculation(self):
        """测试质量评分计算"""
        diff_result = DiffResult(
            diffs=[],
            source_count=100,
            target_count=100,
            structural_diffs=0,
            value_diffs=0,
            missing_diffs=0,
            total_diffs=0,
        )
        resolution_result = ResolutionResult(
            resolutions=[],
            total_conflicts=0,
            resolved_count=0,
            unresolved_count=0,
        )

        generator = ReportGenerator()
        report = generator.generate(
            "akstock", "baostock",
            diff_result=diff_result,
            resolution_result=resolution_result,
        )

        assert report.summary["quality_score"] == 100.0
        assert report.summary["quality_grade"] == "A"

    def test_recommendations_generation(self):
        """测试建议生成"""
        diff_result = DiffResult(
            diffs=[
                DataDiff(DiffType.STRUCTURAL, DiffSeverity.HIGH, None, None, "col1", None, None, "test"),
                DataDiff(DiffType.VALUE, DiffSeverity.MEDIUM, None, None, "col2", 1, 2, "test"),
            ],
            source_count=100,
            target_count=100,
            structural_diffs=1,
            value_diffs=1,
            missing_diffs=0,
            total_diffs=2,
        )

        generator = ReportGenerator()
        report = generator.generate("akstock", "baostock", diff_result=diff_result)

        assert len(report.recommendations) > 0
        assert any("结构差异" in r for r in report.recommendations)

    def test_to_json(self):
        """测试转换为 JSON"""
        generator = ReportGenerator()
        report = generator.generate("akstock", "baostock")

        json_str = report.to_json()
        data = json.loads(json_str)

        assert data["report_id"].startswith("VR-")
        assert data["source_name"] == "akstock"

    def test_export_json(self):
        """测试导出 JSON 文件"""
        generator = ReportGenerator()
        report = generator.generate("akstock", "baostock")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            file_path = f.name

        try:
            generator.export_json(report, file_path)

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert data["report_id"] == report.report_id
        finally:
            Path(file_path).unlink()

    def test_export_html(self):
        """测试导出 HTML 文件"""
        generator = ReportGenerator()
        report = generator.generate("akstock", "baostock")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            file_path = f.name

        try:
            generator.export_html(report, file_path)

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            assert "<!DOCTYPE html>" in content
            assert report.report_id in content
        finally:
            Path(file_path).unlink()


class TestValidationReport:
    """测试 ValidationReport"""

    def test_to_dict(self):
        """测试转换为字典"""
        report = ValidationReport(
            report_id="VR-20250101-0001",
            source_name="akstock",
            target_name="baostock",
            generated_at=datetime.now(),
            summary={"test": "value"},
            recommendations=["rec1", "rec2"],
        )
        d = report.to_dict()

        assert d["report_id"] == "VR-20250101-0001"
        assert d["source_name"] == "akstock"
        assert d["summary"]["test"] == "value"
        assert len(d["recommendations"]) == 2


class TestValidationMonitor:
    """测试 ValidationMonitor"""

    def test_check_diff_rate_warning(self):
        """测试差异率警告"""
        # diff_rate = total_diffs / (source_count + target_count)
        # 需要 25 / (100 + 100) = 12.5% > 10% 警告阈值
        diff_result = DiffResult(
            diffs=[],
            source_count=100,
            target_count=100,
            structural_diffs=0,
            value_diffs=0,
            missing_diffs=0,
            total_diffs=25,
        )

        monitor = ValidationMonitor()
        alerts = monitor.check(diff_result, None)

        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.WARNING
        assert "差异率较高" in alerts[0].message

    def test_check_diff_rate_error(self):
        """测试差异率错误"""
        # diff_rate = total_diffs / (source_count + target_count)
        # 需要 50 / (100 + 100) = 25% > 20% 错误阈值
        diff_result = DiffResult(
            diffs=[],
            source_count=100,
            target_count=100,
            structural_diffs=0,
            value_diffs=0,
            missing_diffs=0,
            total_diffs=50,
        )

        monitor = ValidationMonitor()
        alerts = monitor.check(diff_result, None)

        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.ERROR

    def test_check_resolution_rate_warning(self):
        """测试解决率警告"""
        resolution_result = ResolutionResult(
            resolutions=[],
            total_conflicts=10,
            resolved_count=7,  # 70% < 80% 警告阈值
            unresolved_count=3,
        )

        monitor = ValidationMonitor()
        alerts = monitor.check(None, resolution_result)

        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.WARNING
        assert "解决率较低" in alerts[0].message

    def test_check_critical_diffs(self):
        """测试严重差异检查"""
        diff_result = DiffResult(
            diffs=[
                DataDiff(DiffType.STRUCTURAL, DiffSeverity.CRITICAL, None, None, None, None, None, "test")
                for _ in range(5)
            ],
            source_count=100,
            target_count=100,
            structural_diffs=5,
            value_diffs=0,
            missing_diffs=0,
            total_diffs=5,
        )

        monitor = ValidationMonitor()
        alerts = monitor.check(diff_result, None)

        critical_alerts = [a for a in alerts if a.level == AlertLevel.CRITICAL]
        assert len(critical_alerts) == 1

    def test_alert_callback(self):
        """测试告警回调"""
        callback_alerts = []

        def alert_callback(alert):
            callback_alerts.append(alert)

        config = MonitoringConfig(alert_callbacks=[alert_callback])
        monitor = ValidationMonitor(config)

        # 需要足够的差异数量来触发告警
        diff_result = DiffResult(
            diffs=[],
            source_count=100,
            target_count=100,
            structural_diffs=0,
            value_diffs=0,
            missing_diffs=0,
            total_diffs=25,  # 12.5% > 10% 警告阈值
        )

        monitor.check(diff_result, None)
        assert len(callback_alerts) == 1

    def test_get_alerts(self):
        """测试获取告警"""
        monitor = ValidationMonitor()

        # 添加一些告警
        diff_result = DiffResult(
            diffs=[],
            source_count=100,
            target_count=100,
            structural_diffs=0,
            value_diffs=0,
            missing_diffs=0,
            total_diffs=25,  # 12.5% > 10% 警告阈值
        )
        monitor.check(diff_result, None)

        # 获取所有告警
        all_alerts = monitor.get_alerts()
        assert len(all_alerts) > 0

        # 按级别过滤
        warning_alerts = monitor.get_alerts(level=AlertLevel.WARNING)
        assert all(a.level == AlertLevel.WARNING for a in warning_alerts)

    def test_get_alert_summary(self):
        """测试获取告警摘要"""
        monitor = ValidationMonitor()

        diff_result = DiffResult(
            diffs=[],
            source_count=100,
            target_count=100,
            structural_diffs=0,
            value_diffs=0,
            missing_diffs=0,
            total_diffs=25,  # 12.5% > 10% 警告阈值
        )
        monitor.check(diff_result, None)

        summary = monitor.get_alert_summary()
        assert summary["total_alerts"] > 0
        assert "warning" in summary["by_level"]

    def test_clear_alerts(self):
        """测试清空告警"""
        monitor = ValidationMonitor()

        diff_result = DiffResult(
            diffs=[],
            source_count=100,
            target_count=100,
            structural_diffs=0,
            value_diffs=0,
            missing_diffs=0,
            total_diffs=25,  # 12.5% > 10% 警告阈值
        )
        monitor.check(diff_result, None)

        assert len(monitor.get_alerts()) > 0

        monitor.clear_alerts()
        assert len(monitor.get_alerts()) == 0

    def test_export_alerts(self):
        """测试导出告警"""
        monitor = ValidationMonitor()

        diff_result = DiffResult(
            diffs=[],
            source_count=100,
            target_count=100,
            structural_diffs=0,
            value_diffs=0,
            missing_diffs=0,
            total_diffs=25,  # 12.5% > 10% 警告阈值
        )
        monitor.check(diff_result, None)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            file_path = f.name

        try:
            monitor.export_alerts(file_path)

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert len(data) > 0
            assert "level" in data[0]
        finally:
            Path(file_path).unlink()


class TestAlert:
    """测试 Alert"""

    def test_to_dict(self):
        """测试转换为字典"""
        alert = Alert(
            level=AlertLevel.WARNING,
            message="Test alert",
            timestamp=datetime.now(),
            details={"key": "value"},
        )
        d = alert.to_dict()

        assert d["level"] == "warning"
        assert d["message"] == "Test alert"
        assert d["details"]["key"] == "value"


class TestMonitoringConfig:
    """测试 MonitoringConfig"""

    def test_default_values(self):
        """测试默认值"""
        config = MonitoringConfig()

        assert config.diff_rate_warning == 0.1
        assert config.diff_rate_error == 0.2
        assert config.resolution_rate_warning == 0.8
        assert config.resolution_rate_error == 0.5
        assert config.enable_alerts is True
