"""Stock minute schema."""

from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass
class StockMinuteSchema:
    """分钟线 Schema"""

    asset_type: str = "stock"
    code: str = ""
    trade_time: datetime | None = None
    frequency: str = "1min"
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0
    amount: float = 0.0

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        """校验 DataFrame 是否符合 Schema 要求"""
        issues = []
        required = {"code", "trade_time", "frequency", "open", "high", "low", "close", "volume", "amount"}
        missing = required - set(df.columns)
        if missing:
            issues.append(f"Missing columns: {missing}")
            return issues

        if (df["high"] < df["low"]).any():
            issues.append("high < low detected")
        if (df[["open", "high", "low", "close"]] < 0).any().any():
            issues.append("Negative price detected")
        return issues

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        """从数据列提取分区键值"""
        if df.empty:
            return {"asset_type": "stock", "frequency": "daily", "year": "1970", "month": "01"}
        dt = df["trade_time"].iloc[0]
        if isinstance(dt, str):
            dt = pd.to_datetime(dt)
        return {
            "asset_type": str(df["asset_type"].iloc[0]),
            "frequency": str(df["frequency"].iloc[0]),
            "year": str(dt.year),
            "month": str(dt.month).zfill(2),
        }
