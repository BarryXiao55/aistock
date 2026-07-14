"""Baostock data mapper --- raw fields to internal schema columns."""

import pandas as pd


# Baostock 日线数据列名映射
BAOSTOCK_DAILY_COLUMN_MAP = {
    "date": "trade_date",
    "code": "raw_code",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
    "amount": "amount",
    "turn": "turnover",
    "pctChg": "pct_change",
}


def map_daily_columns(df: pd.DataFrame) -> pd.DataFrame:
    """映射日线数据列名"""
    df = df.rename(columns=BAOSTOCK_DAILY_COLUMN_MAP)

    # 确保日期格式正确
    if "trade_date" in df.columns:
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

    # 添加 asset_type 列
    df["asset_type"] = "stock"

    return df


def unify_code(code: str) -> str:
    """
    统一股票代码格式。

    Baostock 返回的代码格式: "sh.600000" 或 "sz.000001"
    内部格式: "600000.SH" 或 "000001.SZ"
    """
    if "." not in code:
        # 已经是内部格式或纯数字
        if code.startswith("6"):
            return f"{code}.SH"
        elif code.startswith(("0", "3")):
            return f"{code}.SZ"
        elif code.startswith("8") or code.startswith("4"):
            return f"{code}.BJ"
        else:
            return f"{code}.SH"

    parts = code.split(".")
    market = parts[0].upper()
    stock_code = parts[1]
    return f"{stock_code}.{market}"
