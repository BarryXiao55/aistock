"""Alternative data schemas."""

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass
class NorthFlowSchema:
    """北向资金 Schema"""

    code: str = ""
    trade_date: date | None = None
    buy_amount: float = 0.0
    sell_amount: float = 0.0
    net_flow: float = 0.0

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        """校验 DataFrame 是否符合 Schema 要求"""
        issues = []
        required = {"code", "trade_date", "buy_amount", "sell_amount", "net_flow"}
        missing = required - set(df.columns)
        if missing:
            issues.append(f"Missing columns: {missing}")
        return issues

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        """从数据列提取分区键值"""
        if df.empty:
            return {"year": "1970", "month": "01"}
        d = df["trade_date"].iloc[0]
        if isinstance(d, str):
            d = pd.to_datetime(d).date()
        return {"year": str(d.year), "month": str(d.month).zfill(2)}


@dataclass
class MarginTradeSchema:
    """融资融券 Schema"""

    code: str = ""
    trade_date: date | None = None
    margin_buy: float = 0.0
    margin_balance: float = 0.0
    short_sell: float = 0.0
    short_balance: float = 0.0

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        """校验 DataFrame 是否符合 Schema 要求"""
        issues = []
        required = {"code", "trade_date", "margin_buy", "margin_balance", "short_sell", "short_balance"}
        missing = required - set(df.columns)
        if missing:
            issues.append(f"Missing columns: {missing}")
        return issues

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        """从数据列提取分区键值"""
        if df.empty:
            return {"year": "1970", "month": "01"}
        d = df["trade_date"].iloc[0]
        if isinstance(d, str):
            d = pd.to_datetime(d).date()
        return {"year": str(d.year), "month": str(d.month).zfill(2)}


@dataclass
class AlternativeSchema:
    """另类数据通用容器 Schema"""

    sub_type: str = ""
    code: str = ""
    trade_date: date | None = None
    data: str = ""

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        """校验 DataFrame 是否符合 Schema 要求"""
        issues = []
        required = {"sub_type", "code", "trade_date", "data"}
        missing = required - set(df.columns)
        if missing:
            issues.append(f"Missing columns: {missing}")
        return issues

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        """从数据列提取分区键值"""
        if df.empty:
            return {"sub_type": "unknown", "year": "1970", "month": "01"}
        d = df["trade_date"].iloc[0]
        if isinstance(d, str):
            d = pd.to_datetime(d).date()
        return {
            "sub_type": str(df["sub_type"].iloc[0]),
            "year": str(d.year),
            "month": str(d.month).zfill(2),
        }


ALTERNATIVE_SCHEMA_MAP: dict[str, type] = {
    "north_flow": NorthFlowSchema,
    "margin_trade": MarginTradeSchema,
}
