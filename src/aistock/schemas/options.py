"""Options schema."""

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass
class OptionsSchema:
    """期权 Schema"""

    code: str = ""                    # 期权合约代码
    underlying: str = ""              # 标的物
    option_type: str = ""             # "call" | "put"
    strike_price: float = 0.0         # 行权价
    expiry_date: date | None = None   # 到期日

    trade_date: date | None = None
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0
    open_interest: int = 0

    # 期权特有字段
    implied_volatility: float = 0.0   # 隐含波动率
    delta: float = 0.0                # Delta 值
    gamma: float = 0.0                # Gamma 值
    theta: float = 0.0                # Theta 值
    vega: float = 0.0                 # Vega 值

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        """校验期权数据"""
        issues = []
        required = {
            "code", "trade_date", "open", "high", "low", "close",
            "volume", "open_interest", "strike_price", "option_type"
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

        if (df["open_interest"] < 0).any():
            issues.append("Negative open_interest detected")

        # 检查行权价
        if (df["strike_price"] <= 0).any():
            issues.append("Non-positive strike_price detected")

        # 检查期权类型
        valid_types = {"call", "put"}
        if not df["option_type"].isin(valid_types).all():
            issues.append("Invalid option_type (must be 'call' or 'put')")

        # 检查隐含波动率范围 (0-500%)
        if "implied_volatility" in df.columns:
            if (df["implied_volatility"] < 0).any() or (df["implied_volatility"] > 500).any():
                issues.append("implied_volatility out of reasonable range (0-500%)")

        # 检查 Delta 范围 (-1 到 1)
        if "delta" in df.columns:
            if (df["delta"] < -1).any() or (df["delta"] > 1).any():
                issues.append("delta out of range (-1 to 1)")

        return issues

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        """从数据列提取分区键值"""
        if df.empty:
            return {"asset_type": "option", "underlying": "unknown", "option_type": "call", "year": "1970", "month": "01"}
        td = df["trade_date"].iloc[0]
        if isinstance(td, str):
            td = pd.to_datetime(td).date()
        return {
            "asset_type": "option",
            "underlying": str(df["underlying"].iloc[0]),
            "option_type": str(df["option_type"].iloc[0]),
            "year": str(td.year),
            "month": str(td.month).zfill(2),
        }
