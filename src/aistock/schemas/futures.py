"""Futures schema."""

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass
class FuturesSchema:
    """期货 Schema"""

    code: str = ""                    # 合约代码 (如 IF2501)
    underlying: str = ""              # 标的物 (如 IF)
    exchange: str = ""                # 交易所 (CFFEX/SHFE/DCE/CZCE)
    trade_date: date | None = None

    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    settle: float = 0.0              # 结算价
    volume: int = 0
    open_interest: int = 0           # 持仓量

    # 期货特有字段
    margin_rate: float = 0.0         # 保证金比例
    contract_multiplier: int = 1     # 合约乘数
    delivery_month: str = ""         # 交割月
    expiry_date: date | None = None  # 到期日

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        """校验期货数据"""
        issues = []
        required = {
            "code", "trade_date", "open", "high", "low", "close",
            "settle", "volume", "open_interest"
        }
        missing = required - set(df.columns)
        if missing:
            issues.append(f"Missing columns: {missing}")
            return issues

        # 检查价格合理性
        if (df["high"] < df["low"]).any():
            issues.append("high < low detected")

        if (df[["open", "high", "low", "close", "settle"]] < 0).any().any():
            issues.append("Negative price detected")

        if (df["volume"] < 0).any():
            issues.append("Negative volume detected")

        if (df["open_interest"] < 0).any():
            issues.append("Negative open_interest detected")

        # 检查保证金比例范围 (0-100%)
        if "margin_rate" in df.columns:
            if (df["margin_rate"] < 0).any() or (df["margin_rate"] > 100).any():
                issues.append("margin_rate out of reasonable range (0-100%)")

        # 检查合约乘数
        if "contract_multiplier" in df.columns:
            if (df["contract_multiplier"] <= 0).any():
                issues.append("Non-positive contract_multiplier detected")

        return issues

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        """从数据列提取分区键值"""
        return {
            "asset_type": "future",
            "exchange": str(df["exchange"].iloc[0]),
            "year": str(df["trade_date"].iloc[0].year),
            "month": str(df["trade_date"].iloc[0].month).zfill(2),
        }
