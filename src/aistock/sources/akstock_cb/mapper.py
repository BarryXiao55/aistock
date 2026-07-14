"""AkShare convertible bond data mapper --- raw fields to internal schema columns."""

import pandas as pd


# AkShare 可转债数据列名映射
AKSTOCK_CB_COLUMN_MAP = {
    "债券代码": "code",
    "债券简称": "name",
    "正股代码": "stock_code",
    "正股简称": "stock_name",
    "转股价": "conversion_price",
    "转股比例": "conversion_ratio",
    "转股价值": "conversion_value",
    "溢价率": "premium_rate",
    "到期日": "maturity_date",
    "票面利率": "coupon_rate",
    "最新价": "close",
    "涨跌幅": "pct_change",
    "成交量": "volume",
    "成交额": "amount",
}


def map_cb_columns(df: pd.DataFrame) -> pd.DataFrame:
    """映射可转债数据列名"""
    df = df.rename(columns=AKSTOCK_CB_COLUMN_MAP)

    # 确保日期格式正确
    if "maturity_date" in df.columns:
        df["maturity_date"] = pd.to_datetime(df["maturity_date"], errors="coerce").dt.date

    # 添加 asset_type 列
    df["asset_type"] = "cb"

    return df


def unify_cb_code(code: str) -> str:
    """
    统一可转债代码格式。

    输入: "123456" 或 "123456.SZ"
    输出: "123456.SZ" (可转债在深圳交易所)
    """
    if "." in code:
        return code

    # 可转债通常在深圳交易所
    return f"{code}.SZ"
