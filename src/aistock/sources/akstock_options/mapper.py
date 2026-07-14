"""AkShare options data mapper --- raw fields to internal schema columns."""

import pandas as pd


# AkShare 期权数据列名映射
AKSTOCK_OPTIONS_COLUMN_MAP = {
    "date": "trade_date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
    "hold": "open_interest",
    "strike_price": "strike_price",
    "type": "option_type",
    "implied_volatility": "implied_volatility",
    "delta": "delta",
    "gamma": "gamma",
    "theta": "theta",
    "vega": "vega",
}


def map_options_columns(df: pd.DataFrame) -> pd.DataFrame:
    """映射期权数据列名"""
    df = df.rename(columns=AKSTOCK_OPTIONS_COLUMN_MAP)

    # 确保日期格式正确
    if "trade_date" in df.columns:
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

    # 标准化期权类型
    if "option_type" in df.columns:
        df["option_type"] = df["option_type"].map({
            "认购": "call",
            "认沽": "put",
            "call": "call",
            "put": "put",
        })

    # 添加 asset_type 列
    df["asset_type"] = "option"

    return df


def parse_option_code(code: str) -> dict:
    """
    解析期权合约代码。

    输入: "50ETF购1月2800"
    输出: {"underlying": "50ETF", "option_type": "call", "strike_price": 2800, ...}
    """
    import re
    from datetime import date

    # 匹配期权代码格式
    match = re.match(r"(.+?)(购|沽|call|put)(\d+月)?(\d+)", code, re.IGNORECASE)
    if not match:
        return {"underlying": code, "option_type": "call", "strike_price": 0, "expiry_date": None}

    underlying = match.group(1)
    type_code = match.group(2)
    month_str = match.group(3)
    strike_str = match.group(4)

    # 解析期权类型
    option_type = "call" if type_code in ["购", "call"] else "put"

    # 解析行权价
    strike_price = float(strike_str) / 1000 if len(strike_str) >= 4 else float(strike_str)

    # 解析到期月（简化处理）
    expiry_date = None
    if month_str:
        import re as re2
        month_match = re2.search(r"(\d+)月", month_str)
        if month_match:
            month = int(month_match.group(1))
            year = date.today().year
            expiry_date = date(year, month, 28)  # 简化为每月28日

    return {
        "underlying": underlying,
        "option_type": option_type,
        "strike_price": strike_price,
        "expiry_date": expiry_date,
    }
