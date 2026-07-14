"""Validation report generator."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from aistock.validation.diff.interface import DiffResult, DiffType, DiffSeverity
from aistock.validation.resolver.interface import ResolutionResult


@dataclass
class ValidationReport:
    """验证报告"""
    report_id: str
    source_name: str
    target_name: str
    generated_at: datetime
    diff_result: DiffResult | None = None
    resolution_result: ResolutionResult | None = None
    summary: dict = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "report_id": self.report_id,
            "source_name": self.source_name,
            "target_name": self.target_name,
            "generated_at": self.generated_at.isoformat(),
            "diff_result": self.diff_result.to_dict() if self.diff_result else None,
            "resolution_result": self.resolution_result.to_dict() if self.resolution_result else None,
            "summary": self.summary,
            "recommendations": self.recommendations,
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class ReportGenerator:
    """验证报告生成器"""

    def __init__(self):
        """初始化报告生成器"""
        self._report_counter = 0

    def generate(
        self,
        source_name: str,
        target_name: str,
        diff_result: DiffResult | None = None,
        resolution_result: ResolutionResult | None = None,
    ) -> ValidationReport:
        """生成验证报告"""
        self._report_counter += 1
        report_id = f"VR-{datetime.now().strftime('%Y%m%d')}-{self._report_counter:04d}"

        # 生成摘要
        summary = self._generate_summary(diff_result, resolution_result)

        # 生成建议
        recommendations = self._generate_recommendations(diff_result, resolution_result)

        return ValidationReport(
            report_id=report_id,
            source_name=source_name,
            target_name=target_name,
            generated_at=datetime.now(),
            diff_result=diff_result,
            resolution_result=resolution_result,
            summary=summary,
            recommendations=recommendations,
        )

    def _generate_summary(
        self,
        diff_result: DiffResult | None,
        resolution_result: ResolutionResult | None,
    ) -> dict:
        """生成摘要"""
        summary = {}

        if diff_result:
            summary["diff_summary"] = {
                "total_diffs": diff_result.total_diffs,
                "structural_diffs": diff_result.structural_diffs,
                "value_diffs": diff_result.value_diffs,
                "missing_diffs": diff_result.missing_diffs,
                "diff_rate": round(diff_result.diff_rate, 4),
                "source_count": diff_result.source_count,
                "target_count": diff_result.target_count,
            }

            # 按类型统计
            type_counts = {}
            for diff in diff_result.diffs:
                type_name = diff.diff_type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1
            summary["diff_by_type"] = type_counts

            # 按严重程度统计
            severity_counts = {}
            for diff in diff_result.diffs:
                severity_name = diff.severity.value
                severity_counts[severity_name] = severity_counts.get(severity_name, 0) + 1
            summary["diff_by_severity"] = severity_counts

        if resolution_result:
            summary["resolution_summary"] = {
                "total_conflicts": resolution_result.total_conflicts,
                "resolved_count": resolution_result.resolved_count,
                "unresolved_count": resolution_result.unresolved_count,
                "resolution_rate": round(resolution_result.resolution_rate, 4),
            }

            # 按解决方法统计
            method_counts = {}
            for resolution in resolution_result.resolutions:
                method = resolution.resolution_method.split(" ")[0]  # 取方法名
                method_counts[method] = method_counts.get(method, 0) + 1
            summary["resolution_by_method"] = method_counts

        # 计算整体质量评分
        if diff_result and resolution_result:
            quality_score = self._calculate_quality_score(diff_result, resolution_result)
            summary["quality_score"] = quality_score
            summary["quality_grade"] = self._get_quality_grade(quality_score)

        return summary

    def _calculate_quality_score(
        self,
        diff_result: DiffResult,
        resolution_result: ResolutionResult,
    ) -> float:
        """计算质量评分"""
        # 差异率越低越好
        diff_score = max(0, 100 - diff_result.diff_rate * 100)

        # 解决率越高越好
        resolution_score = resolution_result.resolution_rate * 100

        # 加权平均
        quality_score = diff_score * 0.6 + resolution_score * 0.4

        return round(quality_score, 2)

    def _get_quality_grade(self, score: float) -> str:
        """获取质量等级"""
        if score >= 90:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 50:
            return "C"
        else:
            return "D"

    def _generate_recommendations(
        self,
        diff_result: DiffResult | None,
        resolution_result: ResolutionResult | None,
    ) -> list[str]:
        """生成建议"""
        recommendations = []

        if diff_result:
            # 根据差异类型生成建议
            if diff_result.structural_diffs > 0:
                recommendations.append(
                    f"发现 {diff_result.structural_diffs} 个结构差异，建议检查 Schema 定义一致性"
                )

            if diff_result.value_diffs > 0:
                recommendations.append(
                    f"发现 {diff_result.value_diffs} 个值差异，建议检查数据源更新时间"
                )

            if diff_result.missing_diffs > 0:
                recommendations.append(
                    f"发现 {diff_result.missing_diffs} 个缺失记录，建议检查数据完整性"
                )

            # 根据严重程度生成建议
            critical_diffs = [
                d for d in diff_result.diffs if d.severity == DiffSeverity.CRITICAL
            ]
            if critical_diffs:
                recommendations.append(
                    f"发现 {len(critical_diffs)} 个严重差异，需要立即处理"
                )

        if resolution_result:
            # 根据解决率生成建议
            if resolution_result.resolution_rate < 0.8:
                recommendations.append(
                    f"冲突解决率较低 ({resolution_result.resolution_rate:.1%})，建议调整解决策略"
                )

            if resolution_result.unresolved_count > 0:
                recommendations.append(
                    f"有 {resolution_result.unresolved_count} 个冲突未解决，建议人工审查"
                )

        if not recommendations:
            recommendations.append("数据质量良好，无需特别处理")

        return recommendations

    def export_json(self, report: ValidationReport, file_path: str) -> None:
        """导出为 JSON 文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(report.to_json())

    def export_html(self, report: ValidationReport, file_path: str) -> None:
        """导出为 HTML 文件"""
        html_content = self._generate_html(report)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _generate_html(self, report: ValidationReport) -> str:
        """生成 HTML 报告"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>验证报告 - {report.report_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .recommendations {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e9ecef; border-radius: 5px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ font-size: 12px; color: #666; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>验证报告</h1>
        <p><strong>报告ID:</strong> {report.report_id}</p>
        <p><strong>生成时间:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>源数据:</strong> {report.source_name} → <strong>目标数据:</strong> {report.target_name}</p>
    </div>

    <div class="summary">
        <h2>摘要</h2>
"""

        if "quality_score" in report.summary:
            quality_score = report.summary["quality_score"]
            quality_grade = report.summary["quality_grade"]
            html += f"""
        <div class="metric">
            <div class="metric-value">{quality_score}</div>
            <div class="metric-label">质量评分</div>
        </div>
        <div class="metric">
            <div class="metric-value">{quality_grade}</div>
            <div class="metric-label">质量等级</div>
        </div>
"""

        if "diff_summary" in report.summary:
            diff_summary = report.summary["diff_summary"]
            html += f"""
        <div class="metric">
            <div class="metric-value">{diff_summary['total_diffs']}</div>
            <div class="metric-label">总差异数</div>
        </div>
        <div class="metric">
            <div class="metric-value">{diff_summary['diff_rate']:.2%}</div>
            <div class="metric-label">差异率</div>
        </div>
"""

        if "resolution_summary" in report.summary:
            res_summary = report.summary["resolution_summary"]
            html += f"""
        <div class="metric">
            <div class="metric-value">{res_summary['resolution_rate']:.2%}</div>
            <div class="metric-label">解决率</div>
        </div>
"""

        html += """
    </div>

    <div class="recommendations">
        <h2>建议</h2>
        <ul>
"""

        for rec in report.recommendations:
            html += f"            <li>{rec}</li>\n"

        html += """
        </ul>
    </div>
</body>
</html>
"""
        return html
