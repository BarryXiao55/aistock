"""Quality scorer cleaning step."""

import pandas as pd
from datetime import date, timedelta

from aistock.cleaning.interface import CleaningStep
from aistock.observability.quality import QualityReport, QualityIssue


class QualityScorer(CleaningStep):
    """数据质量评分步骤"""

    name = "quality_scorer"

    def __init__(
        self,
        completeness_weight: float = 0.30,
        consistency_weight: float = 0.25,
        timeliness_weight: float = 0.20,
        accuracy_weight: float = 0.25,
    ):
        """
        初始化质量评分器。

        Args:
            completeness_weight: 完整性权重
            consistency_weight: 一致性权重
            timeliness_weight: 时效性权重
            accuracy_weight: 准确性权重
        """
        self.completeness_weight = completeness_weight
        self.consistency_weight = consistency_weight
        self.timeliness_weight = timeliness_weight
        self.accuracy_weight = accuracy_weight

    def clean(self, df: pd.DataFrame, ctx) -> pd.DataFrame:
        """计算质量评分并添加到 DataFrame"""
        if df.empty:
            return df

        # 计算各维度评分
        completeness = self._calculate_completeness(df)
        consistency = self._calculate_consistency(df)
        timeliness = self._calculate_timeliness(df)
        accuracy = self._calculate_accuracy(df)

        # 计算综合评分
        quality_score = (
            completeness * self.completeness_weight +
            consistency * self.consistency_weight +
            timeliness * self.timeliness_weight +
            accuracy * self.accuracy_weight
        )

        # 添加质量评分列
        df["quality_score"] = quality_score
        df["quality_grade"] = self._get_quality_grade(quality_score)

        # 记录质量问题
        issues = []
        if completeness < 90:
            issues.append(QualityIssue(
                dimension="completeness",
                severity="warning" if completeness >= 70 else "error",
                description=f"Completeness score: {completeness:.1f}%",
                affected_rows=int((1 - completeness / 100) * len(df)),
                suggestion="Check for missing values in critical columns",
            ))

        if consistency < 90:
            issues.append(QualityIssue(
                dimension="consistency",
                severity="warning" if consistency >= 70 else "error",
                description=f"Consistency score: {consistency:.1f}%",
                affected_rows=int((1 - consistency / 100) * len(df)),
                suggestion="Check for data conflicts or duplicates",
            ))

        if timeliness < 90:
            issues.append(QualityIssue(
                dimension="timeliness",
                severity="warning" if timeliness >= 70 else "error",
                description=f"Timeliness score: {timeliness:.1f}%",
                affected_rows=0,
                suggestion="Update data to more recent dates",
            ))

        if accuracy < 90:
            issues.append(QualityIssue(
                dimension="accuracy",
                severity="warning" if accuracy >= 70 else "error",
                description=f"Accuracy score: {accuracy:.1f}%",
                affected_rows=int((1 - accuracy / 100) * len(df)),
                suggestion="Review data validation rules",
            ))

        # 记录日志
        ctx.log.info(
            f"Quality score: {quality_score:.1f} (Grade: {self._get_quality_grade(quality_score)}) "
            f"[C:{completeness:.1f} Co:{consistency:.1f} T:{timeliness:.1f} A:{accuracy:.1f}]"
        )

        return df

    def _calculate_completeness(self, df: pd.DataFrame) -> float:
        """计算完整性评分"""
        if df.empty:
            return 100.0

        # 计算缺失值比例
        total_cells = df.size
        missing_cells = df.isna().sum().sum()
        completeness = (1 - missing_cells / total_cells) * 100

        return min(100.0, max(0.0, completeness))

    def _calculate_consistency(self, df: pd.DataFrame) -> float:
        """计算一致性评分"""
        if df.empty:
            return 100.0

        # 检查重复行
        total_rows = len(df)
        duplicate_rows = df.duplicated().sum()
        consistency = (1 - duplicate_rows / total_rows) * 100 if total_rows > 0 else 100.0

        return min(100.0, max(0.0, consistency))

    def _calculate_timeliness(self, df: pd.DataFrame) -> float:
        """计算时效性评分"""
        if df.empty:
            return 100.0

        # 查找日期列
        date_columns = [col for col in df.columns if "date" in col.lower()]
        if not date_columns:
            return 100.0

        # 使用第一个日期列
        date_col = date_columns[0]
        try:
            dates = pd.to_datetime(df[date_col])
            max_date = dates.max()
            today = pd.Timestamp.now()

            # 计算延迟天数
            delay_days = (today - max_date).days

            # 评分：0天=100分，30天=50分，60天=0分
            if delay_days <= 0:
                timeliness = 100.0
            elif delay_days >= 60:
                timeliness = 0.0
            else:
                timeliness = 100.0 - (delay_days / 60) * 100

            return min(100.0, max(0.0, timeliness))
        except Exception:
            return 100.0

    def _calculate_accuracy(self, df: pd.DataFrame) -> float:
        """计算准确性评分"""
        if df.empty:
            return 100.0

        # 基本准确性检查
        issues = 0
        total_checks = 0

        # 检查价格列
        price_columns = ["open", "high", "low", "close", "settle"]
        for col in price_columns:
            if col in df.columns:
                total_checks += 1
                # 检查负价格
                if (df[col] < 0).any():
                    issues += 1
                # 检查 high < low
                if "low" in df.columns and col == "high":
                    if (df[col] < df["low"]).any():
                        issues += 1

        # 检查成交量
        if "volume" in df.columns:
            total_checks += 1
            if (df["volume"] < 0).any():
                issues += 1

        # 检查持仓量
        if "open_interest" in df.columns:
            total_checks += 1
            if (df["open_interest"] < 0).any():
                issues += 1

        if total_checks == 0:
            return 100.0

        accuracy = (1 - issues / total_checks) * 100
        return min(100.0, max(0.0, accuracy))

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

    def validate(self, df: pd.DataFrame) -> list[str]:
        """后置校验"""
        issues = []

        # 检查质量评分是否存在
        if "quality_score" not in df.columns:
            issues.append("quality_score column not found")

        # 检查质量评分范围
        if "quality_score" in df.columns:
            if (df["quality_score"] < 0).any() or (df["quality_score"] > 100).any():
                issues.append("quality_score out of range (0-100)")

        return issues

    def generate_report(
        self,
        df: pd.DataFrame,
        schema_name: str,
        partition_key: str,
    ) -> QualityReport:
        """生成质量报告"""
        if df.empty:
            return QualityReport(
                schema_name=schema_name,
                partition_key=partition_key,
                total_records=0,
                quality_score=100.0,
                completeness=100.0,
                consistency=100.0,
                timeliness=100.0,
                accuracy=100.0,
            )

        completeness = self._calculate_completeness(df)
        consistency = self._calculate_consistency(df)
        timeliness = self._calculate_timeliness(df)
        accuracy = self._calculate_accuracy(df)

        quality_score = (
            completeness * self.completeness_weight +
            consistency * self.consistency_weight +
            timeliness * self.timeliness_weight +
            accuracy * self.accuracy_weight
        )

        issues = []
        if completeness < 90:
            issues.append(QualityIssue(
                dimension="completeness",
                severity="warning" if completeness >= 70 else "error",
                description=f"Completeness score: {completeness:.1f}%",
                affected_rows=int((1 - completeness / 100) * len(df)),
                suggestion="Check for missing values in critical columns",
            ))

        if consistency < 90:
            issues.append(QualityIssue(
                dimension="consistency",
                severity="warning" if consistency >= 70 else "error",
                description=f"Consistency score: {consistency:.1f}%",
                affected_rows=int((1 - consistency / 100) * len(df)),
                suggestion="Check for data conflicts or duplicates",
            ))

        if timeliness < 90:
            issues.append(QualityIssue(
                dimension="timeliness",
                severity="warning" if timeliness >= 70 else "error",
                description=f"Timeliness score: {timeliness:.1f}%",
                affected_rows=0,
                suggestion="Update data to more recent dates",
            ))

        if accuracy < 90:
            issues.append(QualityIssue(
                dimension="accuracy",
                severity="warning" if accuracy >= 70 else "error",
                description=f"Accuracy score: {accuracy:.1f}%",
                affected_rows=int((1 - accuracy / 100) * len(df)),
                suggestion="Review data validation rules",
            ))

        return QualityReport(
            schema_name=schema_name,
            partition_key=partition_key,
            total_records=len(df),
            quality_score=quality_score,
            completeness=completeness,
            consistency=consistency,
            timeliness=timeliness,
            accuracy=accuracy,
            issues=issues,
        )
