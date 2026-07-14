"""Tushare data mapper --- raw fields to internal schema columns."""

import pandas as pd


# Tushare 日线数据列名映射（Tushare 返回的列名已经是英文）
TUSHARE_DAILY_COLUMN_MAP = {
    "ts_code": "raw_code",
    "trade_date": "trade_date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "vol": "volume",
    "amount": "amount",
    "pct_chg": "pct_change",
}


def map_daily_columns(df: pd.DataFrame) -> pd.DataFrame:
    """映射日线数据列名"""
    df = df.rename(columns=TUSHARE_DAILY_COLUMN_MAP)

    # 确保日期格式正确
    if "trade_date" in df.columns:
        df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d").dt.date

    return df


def unify_code(code: str) -> str:
    """
    统一股票代码格式。

    Tushare 返回的代码格式: "000001.SZ"
    内部格式: "000001.SZ"（相同）
    """
    if "." in code:
        return code

    # 根据代码前缀判断
    if code.startswith("6"):
        return f"{code}.SH"
    elif code.startswith(("0", "3")):
        return f"{code}.SZ"
    elif code.startswith("8") or code.startswith("4"):
        return f"{code}.BJ"
    else:
        return f"{code}.SH"
