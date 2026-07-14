"""Tushare futures data mapper --- raw fields to internal schema columns."""

import pandas as pd


# Tushare 期货数据列名映射
TUSHARE_FUTURES_COLUMN_MAP = {
    "ts_code": "raw_code",
    "trade_date": "trade_date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "settle": "settle",
    "vol": "volume",
    "oi": "open_interest",
    "exchange": "exchange",
}


def map_futures_columns(df: pd.DataFrame) -> pd.DataFrame:
    """映射期货数据列名"""
    df = df.rename(columns=TUSHARE_FUTURES_COLUMN_MAP)

    # 确保日期格式正确
    if "trade_date" in df.columns:
        df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d").dt.date

    # 添加 asset_type 列
    df["asset_type"] = "future"

    return df


def unify_futures_code(ts_code: str) -> str:
    """
    统一期货合约代码格式。

    Tushare 格式: "IF2501.CFFEX"
    内部格式: "IF2501"
    """
    if "." in ts_code:
        return ts_code.split(".")[0]
    return ts_code
