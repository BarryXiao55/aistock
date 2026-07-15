"""AkShare data mapper --- raw fields to internal schema columns."""

import pandas as pd

from aistock.schemas.daily import StockDailySchema


# AkShare 日线数据列名映射 (东方财富中文列名)
AKSTOCK_DAILY_COLUMN_MAP = {
    "日期": "trade_date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "振幅": "amplitude",
    "涨跌幅": "pct_change",
    "涨跌额": "change",
    "换手率": "turnover",
}

# 指数日线数据列名映射 (东方财富英文列名)
INDEX_DAILY_COLUMN_MAP = {
    "date": "trade_date",
    "open": "open",
    "close": "close",
    "high": "high",
    "low": "low",
    "volume": "volume",
    "amount": "amount",
}


def map_daily_columns(df: pd.DataFrame) -> pd.DataFrame:
    """映射日线数据列名"""
    df = df.rename(columns=AKSTOCK_DAILY_COLUMN_MAP)

    # 确保日期格式正确
    if "trade_date" in df.columns:
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

    # 添加 asset_type 列
    df["asset_type"] = "stock"

    return df


def map_index_daily_columns(df: pd.DataFrame) -> pd.DataFrame:
    """映射指数日线数据列名 (东方财富返回英文列名)"""
    df = df.rename(columns=INDEX_DAILY_COLUMN_MAP)

    if "trade_date" in df.columns:
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

    df["asset_type"] = "stock"

    return df


def unify_code(code: str, market: str = "sz") -> str:
    """
    统一股票代码格式。

    AkShare 返回的代码格式: "000001"
    内部格式: "000001.SZ"
    """
    if "." in code:
        return code

    # 根据代码前缀判断交易所
    if code.startswith("6"):
        return f"{code}.SH"
    elif code.startswith(("0", "3")):
        return f"{code}.SZ"
    elif code.startswith("8") or code.startswith("4"):
        return f"{code}.BJ"
    else:
        return f"{code}.{market.upper()}"
