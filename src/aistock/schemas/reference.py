"""Reference schema."""

from dataclasses import dataclass
from datetime import date


@dataclass
class ReferenceSchema:
    """品种参考信息 Schema"""

    code: str = ""
    name: str = ""
    industry: str = ""
    list_date: date | None = None
    delist_date: date | None = None

    @staticmethod
    def validate(df: "pd.DataFrame") -> list[str]:  # noqa: F821
        """校验 DataFrame 是否符合 Schema 要求"""
        issues = []
        required = {"code", "name", "industry", "list_date"}
        missing = required - set(df.columns)
        if missing:
            issues.append(f"Missing columns: {missing}")
        return issues

    @staticmethod
    def partition_values(df: "pd.DataFrame") -> dict:  # noqa: F821
        """从数据列提取分区键值"""
        return {"asset_type": "reference"}
