"""Test futures schema and cleaning steps."""

from datetime import date

import pandas as pd
import pytest

from aistock.schemas.futures import FuturesSchema
from aistock.cleaning.futures import FuturesCleaner
from aistock.schemas import SCHEMA_REGISTRY
from aistock.sources.akstock_futures.mapper import parse_futures_code


class TestFuturesSchema:
    """测试 FuturesSchema"""

    def test_validate_passes_on_clean_data(self):
        """测试有效数据通过校验"""
        df = pd.DataFrame([{
            "code": "IF2501",
            "trade_date": date(2025, 1, 2),
            "open": 4000.0,
            "high": 4050.0,
            "low": 3980.0,
            "close": 4020.0,
            "settle": 4015.0,
            "volume": 100000,
            "open_interest": 50000,
            "exchange": "CFFEX",
            "margin_rate": 12.0,
            "contract_multiplier": 300,
        }])
        assert FuturesSchema.validate(df) == []

    def test_validate_detects_missing_columns(self):
        """测试检测缺失列"""
        df = pd.DataFrame([{
            "code": "IF2501",
            "trade_date": date(2025, 1, 2),
        }])
        issues = FuturesSchema.validate(df)
        assert len(issues) > 0
        assert any("Missing" in i for i in issues)

    def test_validate_detects_high_low_inversion(self):
        """测试检测 high < low"""
        df = pd.DataFrame([{
            "code": "IF2501",
            "trade_date": date(2025, 1, 2),
            "open": 4000.0,
            "high": 3950.0,
            "low": 4050.0,
            "close": 4020.0,
            "settle": 4015.0,
            "volume": 100000,
            "open_interest": 50000,
            "exchange": "CFFEX",
        }])
        issues = FuturesSchema.validate(df)
        assert any("high" in i.lower() and "low" in i.lower() for i in issues)

    def test_validate_detects_negative_price(self):
        """测试检测负价格"""
        df = pd.DataFrame([{
            "code": "IF2501",
            "trade_date": date(2025, 1, 2),
            "open": -4000.0,
            "high": 4050.0,
            "low": 3980.0,
            "close": 4020.0,
            "settle": 4015.0,
            "volume": 100000,
            "open_interest": 50000,
            "exchange": "CFFEX",
        }])
        issues = FuturesSchema.validate(df)
        assert any("Negative" in i for i in issues)

    def test_validate_detects_negative_volume(self):
        """测试检测负成交量"""
        df = pd.DataFrame([{
            "code": "IF2501",
            "trade_date": date(2025, 1, 2),
            "open": 4000.0,
            "high": 4050.0,
            "low": 3980.0,
            "close": 4020.0,
            "settle": 4015.0,
            "volume": -100000,
            "open_interest": 50000,
            "exchange": "CFFEX",
        }])
        issues = FuturesSchema.validate(df)
        assert any("volume" in i.lower() for i in issues)

    def test_validate_detects_negative_open_interest(self):
        """测试检测负持仓量"""
        df = pd.DataFrame([{
            "code": "IF2501",
            "trade_date": date(2025, 1, 2),
            "open": 4000.0,
            "high": 4050.0,
            "low": 3980.0,
            "close": 4020.0,
            "settle": 4015.0,
            "volume": 100000,
            "open_interest": -50000,
            "exchange": "CFFEX",
        }])
        issues = FuturesSchema.validate(df)
        assert any("open_interest" in i.lower() for i in issues)

    def test_validate_detects_invalid_margin_rate(self):
        """测试检测无效保证金比例"""
        df = pd.DataFrame([{
            "code": "IF2501",
            "trade_date": date(2025, 1, 2),
            "open": 4000.0,
            "high": 4050.0,
            "low": 3980.0,
            "close": 4020.0,
            "settle": 4015.0,
            "volume": 100000,
            "open_interest": 50000,
            "exchange": "CFFEX",
            "margin_rate": 150.0,  # 超过 100%
        }])
        issues = FuturesSchema.validate(df)
        assert any("margin_rate" in i for i in issues)

    def test_partition_values(self):
        """测试分区键值"""
        df = pd.DataFrame([{
            "code": "IF2501",
            "trade_date": date(2025, 1, 15),
            "exchange": "CFFEX",
        }])
        pv = FuturesSchema.partition_values(df)
        assert pv["asset_type"] == "future"
        assert pv["exchange"] == "CFFEX"
        assert pv["year"] == "2025"
        assert pv["month"] == "01"

    def test_in_schema_registry(self):
        """测试注册到 SCHEMA_REGISTRY"""
        assert "futures" in SCHEMA_REGISTRY
        assert SCHEMA_REGISTRY["futures"] is FuturesSchema


class TestParseFuturesCode:
    """测试期货合约代码解析"""

    def test_parse_if_code(self):
        """测试解析 IF 合约"""
        result = parse_futures_code("IF2501")
        assert result["underlying"] == "IF"
        assert result["delivery_month"] == "202501"
        assert result["expiry_date"] is not None

    def test_parse_cu_code(self):
        """测试解析 CU 合约"""
        result = parse_futures_code("CU2501")
        assert result["underlying"] == "CU"
        assert result["delivery_month"] == "202501"

    def test_parse_invalid_code(self):
        """测试解析无效代码"""
        result = parse_futures_code("INVALID")
        assert result["underlying"] == "INVALID"
        assert result["delivery_month"] == ""


class TestFuturesCleaner:
    """测试 FuturesCleaner"""

    def test_marks_main_contract(self):
        """测试标记主力合约"""
        df = pd.DataFrame([
            {"code": "IF2501", "trade_date": date(2025, 1, 2), "volume": 100000},
            {"code": "IF2502", "trade_date": date(2025, 1, 2), "volume": 150000},
            {"code": "IF2503", "trade_date": date(2025, 1, 2), "volume": 80000},
        ])
        cleaner = FuturesCleaner()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = cleaner.clean(df, ctx)
        assert "is_main_contract" in result.columns
        # IF2502 应该是主力合约
        assert result[result["code"] == "IF2502"]["is_main_contract"].iloc[0] == True

    def test_marks_near_delivery(self):
        """测试标记临近交割月"""
        from datetime import date, timedelta
        near_date = date.today() + timedelta(days=15)
        df = pd.DataFrame([{
            "code": "IF2501",
            "expiry_date": near_date,
        }])
        cleaner = FuturesCleaner()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = cleaner.clean(df, ctx)
        assert "near_delivery" in result.columns
        assert result["near_delivery"].iloc[0] == True

    def test_calculates_oi_change(self):
        """测试计算持仓量变化"""
        df = pd.DataFrame([
            {"code": "IF2501", "trade_date": date(2025, 1, 2), "open_interest": 50000},
            {"code": "IF2501", "trade_date": date(2025, 1, 3), "open_interest": 55000},
            {"code": "IF2501", "trade_date": date(2025, 1, 4), "open_interest": 52000},
        ])
        cleaner = FuturesCleaner()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = cleaner.clean(df, ctx)
        assert "oi_change" in result.columns
        # 第二天增加 5000，第三天减少 3000
        assert result.iloc[1]["oi_change"] == 5000
        assert result.iloc[2]["oi_change"] == -3000

    def test_validate_passes_on_valid_data(self):
        """测试有效数据通过校验"""
        df = pd.DataFrame([{
            "margin_rate": 12.0,
            "contract_multiplier": 300,
            "settle": 4015.0,
            "close": 4020.0,
        }])
        cleaner = FuturesCleaner()
        issues = cleaner.validate(df)
        assert len(issues) == 0

    def test_validate_detects_invalid_margin_rate(self):
        """测试检测无效保证金比例"""
        df = pd.DataFrame([{
            "margin_rate": 150.0,
            "contract_multiplier": 300,
        }])
        cleaner = FuturesCleaner()
        issues = cleaner.validate(df)
        assert len(issues) > 0
        assert any("margin_rate" in i for i in issues)

    def test_validate_detects_large_settle_close_diff(self):
        """测试检测结算价与收盘价差异过大"""
        df = pd.DataFrame([{
            "margin_rate": 12.0,
            "contract_multiplier": 300,
            "settle": 3500.0,  # 比 close 低 12.5%
            "close": 4000.0,
        }])
        cleaner = FuturesCleaner()
        issues = cleaner.validate(df)
        assert len(issues) > 0
        assert any("settle" in i.lower() for i in issues)
