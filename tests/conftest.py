"""Shared test fixtures."""

import pytest
from pathlib import Path
from datetime import date
import pandas as pd


@pytest.fixture
def project_root():
    """返回项目根目录"""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_daily_df():
    """5只股票×5天合法日线数据"""
    codes = ["000001.SZ", "600000.SH", "000002.SZ", "600036.SH", "000858.SZ"]
    dates = pd.date_range("2025-01-02", "2025-01-06", freq="B")
    rows = []
    for code in codes:
        for d in dates:
            rows.append({
                "asset_type": "stock",
                "code": code,
                "trade_date": d.date(),
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1000000,
                "amount": 10200000.0,
                "turnover": 0.02,
                "adj_factor": 1.0,
                "is_st": False,
                "is_suspended": False,
            })
    return pd.DataFrame(rows)


@pytest.fixture
def sample_daily_bad_df():
    """包含脏数据的日线数据"""
    rows = [
        # 正常数据
        {
            "code": "000001.SZ",
            "trade_date": date(2025, 1, 2),
            "asset_type": "stock",
            "open": 10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
            "volume": 1000000,
            "amount": 10200000.0,
        },
        # high < low
        {
            "code": "600000.SH",
            "trade_date": date(2025, 1, 2),
            "asset_type": "stock",
            "open": 10.0,
            "high": 9.0,  # 高于 low
            "low": 10.5,  # 低于 high
            "close": 10.2,
            "volume": 1000000,
            "amount": 10200000.0,
        },
        # 负价格
        {
            "code": "000002.SZ",
            "trade_date": date(2025, 1, 2),
            "asset_type": "stock",
            "open": -10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
            "volume": 1000000,
            "amount": 10200000.0,
        },
        # 负成交量
        {
            "code": "600036.SH",
            "trade_date": date(2025, 1, 2),
            "asset_type": "stock",
            "open": 10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
            "volume": -1000,
            "amount": 10200000.0,
        },
    ]
    return pd.DataFrame(rows)
