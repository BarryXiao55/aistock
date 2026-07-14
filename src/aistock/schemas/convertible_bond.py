"""Convertible bond schema."""

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass
class ConvertibleBondSchema:
    """可转债 Schema"""

    code: str = ""                    # 转债代码
    bond_code: str = ""               # 债券代码
    stock_code: str = ""              # 正股代码
    trade_date: date | None = None
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0
    amount: float = 0.0

    # 可转债特有字段
    conversion_price: float = 0.0     # 转股价格
    conversion_ratio: float = 0.0     # 转股比例
    conversion_value: float = 0.0     # 转股价值
    premium_rate: float = 0.0         # 溢价率
    maturity_date: date | None = None # 到期日
    coupon_rate: float = 0.0          # 票面利率

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        """校验可转债数据"""
        issues = []
        required = {
            "code", "trade_date", "open", "high", "low", "close",
            "volume", "amount", "conversion_price"
        }
        missing = required - set(df.columns)
        if missing:
            issues.append(f"Missing columns: {missing}")
            return issues

        # 检查价格合理性
        if (df["high"] < df["low"]).any():
            issues.append("high < low detected")

        if (df[["open", "high", "low", "close"]] < 0).any().any():
            issues.append("Negative price detected")

        if (df["volume"] < 0).any():
            issues.append("Negative volume detected")

        # 检查转股价格合理性
        if (df["conversion_price"] <= 0).any():
            issues.append("Non-positive conversion_price detected")

        # 检查溢价率范围（通常 -50% 到 500%）
        if "premium_rate" in df.columns:
            if (df["premium_rate"] < -50).any() or (df["premium_rate"] > 500).any():
                issues.append("premium_rate out of reasonable range (-50% to 500%)")

        return issues

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        """从数据列提取分区键值"""
        return {
            "asset_type": "cb",
            "year": str(df["trade_date"].iloc[0].year),
            "month": str(df["trade_date"].iloc[0].month).zfill(2),
        }
