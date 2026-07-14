"""Mootdx data mapper --- raw fields to internal schema columns."""

import pandas as pd


# Mootdx 日线数据列名映射
MOOTDX_DAILY_COLUMN_MAP = {
    "open": "open",
    "close": "close",
    "high": "high",
    "low": "low",
    "volume": "volume",
    "amount": "amount",
    "turnover": "turnover",
    "trade_date": "trade_date",
}


def map_daily_columns(df: pd.DataFrame) -> pd.DataFrame:
    """映射日线数据列名"""
    # Mootdx 返回的列名已经是英文
    # 只需要确保格式正确

    # 确保日期格式正确
    if "trade_date" in df.columns:
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

    # 添加 asset_type 列
    df["asset_type"] = "stock"

    return df


def unify_code(code: str, market: str = "sz") -> str:
    """
    统一代码格式。

    Mootdx 返回的代码格式: "000001"
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
