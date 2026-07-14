"""Stock daily schema."""

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass
class StockDailySchema:
    """日线行情 Schema"""

    asset_type: str = "stock"
    code: str = ""
    trade_date: date | None = None
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0
    amount: float = 0.0
    turnover: float | None = None
    adj_factor: float = 1.0
    is_st: bool = False
    is_suspended: bool = False

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        """校验 DataFrame 是否符合 Schema 要求"""
        issues = []
        required = {"code", "trade_date", "open", "high", "low", "close", "volume", "amount"}
        missing = required - set(df.columns)
        if missing:
            issues.append(f"Missing columns: {missing}")
            return issues

        if (df["high"] < df["low"]).any():
            issues.append("high < low detected")
        if (df[["open", "high", "low", "close"]] < 0).any().any():
            issues.append("Negative price detected")
        if (df["volume"] < 0).any():
            issues.append("Negative volume detected")
        return issues

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        """从数据列提取分区键值"""
        return {
            "asset_type": str(df["asset_type"].iloc[0]),
            "year": str(df["trade_date"].iloc[0].year),
            "month": str(df["trade_date"].iloc[0].month).zfill(2),
        }
