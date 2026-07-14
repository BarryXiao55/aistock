"""JQData data mapper --- raw fields to internal schema columns."""

import pandas as pd


# JQData 日线数据列名映射
JQDATA_DAILY_COLUMN_MAP = {
    "open": "open",
    "close": "close",
    "high": "high",
    "low": "low",
    "volume": "volume",
    "money": "amount",
    "trade_date": "trade_date",
}


def map_daily_columns(df: pd.DataFrame) -> pd.DataFrame:
    """映射日线数据列名"""
    # JQData 返回的列名需要映射
    df = df.rename(columns=JQDATA_DAILY_COLUMN_MAP)

    # 确保日期格式正确
    if "trade_date" in df.columns:
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

    # 添加 asset_type 列
    df["asset_type"] = "stock"

    return df


def unify_code(code: str, market: str = "sz") -> str:
    """
    统一代码格式。

    JQData 返回的代码格式: "000001.XSHE"
    内部格式: "000001.SZ"
    """
    if "." in code:
        # 转换 JQData 格式: "000001.XSHE" -> "000001.SZ"
        parts = code.split(".")
        if len(parts) == 2:
            jqmarket = parts[1].upper()
            if jqmarket == "XSHE":
                return f"{parts[0]}.SZ"
            elif jqmarket == "XSHG":
                return f"{parts[0]}.SH"
            elif jqmarket == "XBJ":
                return f"{parts[0]}.BJ"
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


def to_jqcode(code: str) -> str:
    """
    转换为 JQData 代码格式。

    内部格式: "000001.SZ"
    JQData 格式: "000001.XSHE"
    """
    if "." not in code:
        return code

    parts = code.split(".")
    stock_code = parts[0]
    market = parts[1].upper()

    if market == "SZ":
        return f"{stock_code}.XSHE"
    elif market == "SH":
        return f"{stock_code}.XSHG"
    elif market == "BJ":
        return f"{stock_code}.XBJ"
    else:
        return code
