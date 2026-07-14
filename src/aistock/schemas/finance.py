"""Finance schema."""

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass
class FinanceSchema:
    """财务数据 Schema"""

    code: str = ""
    report_period: str = ""
    report_type: str = ""
    pub_date: date | None = None
    total_assets: float = 0.0
    total_liabilities: float = 0.0
    shareholders_equity: float = 0.0
    revenue: float = 0.0
    net_profit: float = 0.0
    eps: float = 0.0
    bps: float = 0.0
    roe: float = 0.0
    pe_ttm: float = 0.0
    pb: float = 0.0

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        """校验 DataFrame 是否符合 Schema 要求"""
        issues = []
        required = {
            "code", "report_period", "pub_date", "total_assets",
            "shareholders_equity", "revenue", "net_profit", "eps",
        }
        missing = required - set(df.columns)
        if missing:
            issues.append(f"Missing columns: {missing}")
            return issues

        if (df["total_assets"] < 0).any():
            issues.append("Negative total_assets")
        if (df["revenue"] < 0).any():
            issues.append("Negative revenue")

        valid_period = df["report_period"].str.match(r"^\d{4}Q[1-4]$")
        if not valid_period.all():
            issues.append("Invalid report_period format")
        return issues

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        """从数据列提取分区键值"""
        return {
            "asset_type": "stock",
            "report_period": str(df["report_period"].iloc[0]),
        }
