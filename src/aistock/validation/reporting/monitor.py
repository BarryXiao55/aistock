"""Monitoring and alerting for validation."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable

from aistock.validation.diff.interface import DiffResult, DiffSeverity
from aistock.validation.resolver.interface import ResolutionResult


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """告警信息"""
    level: AlertLevel
    message: str
    timestamp: datetime
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }


@dataclass
class MonitoringConfig:
    """监控配置"""
    diff_rate_warning: float = 0.1      # 差异率警告阈值
    diff_rate_error: float = 0.2        # 差异率错误阈值
    resolution_rate_warning: float = 0.8  # 解决率警告阈值
    resolution_rate_error: float = 0.5    # 解决率错误阈值
    critical_diff_count: int = 5         # 严重差异数量阈值
    enable_alerts: bool = True
    alert_callbacks: list[Callable] = field(default_factory=list)


class ValidationMonitor:
    """验证监控器"""

    def __init__(self, config: MonitoringConfig | None = None):
        """
        初始化监控器。

        Args:
            config: 监控配置
        """
        self.config = config or MonitoringConfig()
        self._alerts: list[Alert] = []
        self._history: list[dict] = []

    def check(
        self,
        diff_result: DiffResult | None,
        resolution_result: ResolutionResult | None,
    ) -> list[Alert]:
        """检查验证结果并生成告警"""
        alerts = []

        if diff_result:
            alerts.extend(self._check_diff_result(diff_result))

        if resolution_result:
            alerts.extend(self._check_resolution_result(resolution_result))

        # 记录告警
        self._alerts.extend(alerts)

        # 触发回调
        if self.config.enable_alerts:
            for alert in alerts:
                for callback in self.config.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception:
                        pass  # 忽略回调错误

        return alerts

    def _check_diff_result(self, diff_result: DiffResult) -> list[Alert]:
        """检查差异结果"""
        alerts = []

        # 检查差异率
        if diff_result.diff_rate >= self.config.diff_rate_error:
            alerts.append(Alert(
                level=AlertLevel.ERROR,
                message=f"差异率过高: {diff_result.diff_rate:.2%}",
                timestamp=datetime.now(),
                details={
                    "diff_rate": diff_result.diff_rate,
                    "threshold": self.config.diff_rate_error,
                    "total_diffs": diff_result.total_diffs,
                },
            ))
        elif diff_result.diff_rate >= self.config.diff_rate_warning:
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                message=f"差异率较高: {diff_result.diff_rate:.2%}",
                timestamp=datetime.now(),
                details={
                    "diff_rate": diff_result.diff_rate,
                    "threshold": self.config.diff_rate_warning,
                    "total_diffs": diff_result.total_diffs,
                },
            ))

        # 检查严重差异
        critical_diffs = [
            d for d in diff_result.diffs if d.severity == DiffSeverity.CRITICAL
        ]
        if len(critical_diffs) >= self.config.critical_diff_count:
            alerts.append(Alert(
                level=AlertLevel.CRITICAL,
                message=f"发现 {len(critical_diffs)} 个严重差异",
                timestamp=datetime.now(),
                details={
                    "critical_count": len(critical_diffs),
                    "threshold": self.config.critical_diff_count,
                },
            ))

        return alerts

    def _check_resolution_result(self, resolution_result: ResolutionResult) -> list[Alert]:
        """检查解决结果"""
        alerts = []

        # 检查解决率
        if resolution_result.resolution_rate <= self.config.resolution_rate_error:
            alerts.append(Alert(
                level=AlertLevel.ERROR,
                message=f"解决率过低: {resolution_result.resolution_rate:.2%}",
                timestamp=datetime.now(),
                details={
                    "resolution_rate": resolution_result.resolution_rate,
                    "threshold": self.config.resolution_rate_error,
                    "unresolved_count": resolution_result.unresolved_count,
                },
            ))
        elif resolution_result.resolution_rate <= self.config.resolution_rate_warning:
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                message=f"解决率较低: {resolution_result.resolution_rate:.2%}",
                timestamp=datetime.now(),
                details={
                    "resolution_rate": resolution_result.resolution_rate,
                    "threshold": self.config.resolution_rate_warning,
                    "unresolved_count": resolution_result.unresolved_count,
                },
            ))

        return alerts

    def get_alerts(
        self,
        level: AlertLevel | None = None,
        since: datetime | None = None,
    ) -> list[Alert]:
        """获取告警列表"""
        alerts = self._alerts

        if level:
            alerts = [a for a in alerts if a.level == level]

        if since:
            alerts = [a for a in alerts if a.timestamp >= since]

        return alerts

    def get_alert_summary(self) -> dict:
        """获取告警摘要"""
        summary = {
            "total_alerts": len(self._alerts),
            "by_level": {},
        }

        for alert in self._alerts:
            level = alert.level.value
            summary["by_level"][level] = summary["by_level"].get(level, 0) + 1

        return summary

    def clear_alerts(self) -> None:
        """清空告警"""
        self._alerts.clear()

    def export_alerts(self, file_path: str) -> None:
        """导出告警到 JSON 文件"""
        alerts_data = [alert.to_dict() for alert in self._alerts]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(alerts_data, f, indent=2, ensure_ascii=False)
