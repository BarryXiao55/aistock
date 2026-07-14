"""AkShare futures data mapper --- raw fields to internal schema columns."""

import pandas as pd


# AkShare 期货数据列名映射
AKSTOCK_FUTURES_COLUMN_MAP = {
    "date": "trade_date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "settle": "settle",
    "volume": "volume",
    "hold": "open_interest",
}


def map_futures_columns(df: pd.DataFrame) -> pd.DataFrame:
    """映射期货数据列名"""
    df = df.rename(columns=AKSTOCK_FUTURES_COLUMN_MAP)

    # 确保日期格式正确
    if "trade_date" in df.columns:
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

    # 添加 asset_type 列
    df["asset_type"] = "future"

    return df


def parse_futures_code(code: str) -> dict:
    """
    解析期货合约代码。

    输入: "IF2501"
    输出: {"underlying": "IF", "delivery_month": "202501", "expiry_date": ...}
    """
    import re
    from datetime import date

    # 匹配字母和数字
    match = re.match(r"([A-Za-z]+)(\d{4})", code)
    if not match:
        return {"underlying": code, "delivery_month": "", "expiry_date": None}

    underlying = match.group(1)
    month_code = match.group(2)

    # 解析交割月
    year = 2000 + int(month_code[:2])
    month = int(month_code[2:])
    delivery_month = f"{year}{month:02d}"

    # 计算到期日（每月第三个周五）
    import calendar
    from datetime import date, timedelta

    # 获取该月的第三个周五
    first_day = date(year, month, 1)
    first_friday = first_day + timedelta(days=(4 - first_day.weekday()) % 7)
    expiry_date = first_friday + timedelta(weeks=2)

    return {
        "underlying": underlying,
        "delivery_month": delivery_month,
        "expiry_date": expiry_date,
    }
