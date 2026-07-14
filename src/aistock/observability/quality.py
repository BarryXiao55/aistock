"""Quality scorer data models."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class QualityReport:
    """数据质量评分报告"""
    schema_name: str
    partition_key: str
    total_records: int
    quality_score: float
    completeness: float
    consistency: float
    timeliness: float
    accuracy: float
    issues: list["QualityIssue"] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def quality_grade(self) -> str:
        """质量等级"""
        if self.quality_score >= 90:
            return "A"
        elif self.quality_score >= 70:
            return "B"
        elif self.quality_score >= 50:
            return "C"
        else:
            return "D"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "schema_name": self.schema_name,
            "partition_key": self.partition_key,
            "total_records": self.total_records,
            "quality_score": self.quality_score,
            "quality_grade": self.quality_grade,
            "completeness": self.completeness,
            "consistency": self.consistency,
            "timeliness": self.timeliness,
            "accuracy": self.accuracy,
            "issues": [issue.to_dict() for issue in self.issues],
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass
class QualityIssue:
    """质量问题"""
    dimension: str
    severity: str  # "info" | "warning" | "error"
    description: str
    affected_rows: int
    suggestion: str

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "dimension": self.dimension,
            "severity": self.severity,
            "description": self.description,
            "affected_rows": self.affected_rows,
            "suggestion": self.suggestion,
        }
