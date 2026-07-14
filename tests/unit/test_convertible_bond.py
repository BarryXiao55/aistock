"""Test convertible bond schema and cleaning steps."""

from datetime import date

import pandas as pd
import pytest

from aistock.schemas.convertible_bond import ConvertibleBondSchema
from aistock.cleaning.convertible_bond import ConvertibleBondCleaner
from aistock.schemas import SCHEMA_REGISTRY


class TestConvertibleBondSchema:
    """测试 ConvertibleBondSchema"""

    def test_validate_passes_on_clean_data(self):
        """测试有效数据通过校验"""
        df = pd.DataFrame([{
            "code": "123456.SZ",
            "trade_date": date(2025, 1, 2),
            "open": 100.0,
            "high": 105.0,
            "low": 98.0,
            "close": 102.0,
            "volume": 100000,
            "amount": 10200000.0,
            "conversion_price": 10.0,
            "conversion_ratio": 10.0,
            "conversion_value": 100.0,
            "premium_rate": 2.0,
        }])
        assert ConvertibleBondSchema.validate(df) == []

    def test_validate_detects_missing_columns(self):
        """测试检测缺失列"""
        df = pd.DataFrame([{
            "code": "123456.SZ",
            "trade_date": date(2025, 1, 2),
        }])
        issues = ConvertibleBondSchema.validate(df)
        assert len(issues) > 0
        assert any("Missing" in i for i in issues)

    def test_validate_detects_high_low_inversion(self):
        """测试检测 high < low"""
        df = pd.DataFrame([{
            "code": "123456.SZ",
            "trade_date": date(2025, 1, 2),
            "open": 100.0,
            "high": 95.0,
            "low": 105.0,
            "close": 102.0,
            "volume": 100000,
            "amount": 10200000.0,
            "conversion_price": 10.0,
        }])
        issues = ConvertibleBondSchema.validate(df)
        assert any("high" in i.lower() and "low" in i.lower() for i in issues)

    def test_validate_detects_negative_price(self):
        """测试检测负价格"""
        df = pd.DataFrame([{
            "code": "123456.SZ",
            "trade_date": date(2025, 1, 2),
            "open": -100.0,
            "high": 105.0,
            "low": 98.0,
            "close": 102.0,
            "volume": 100000,
            "amount": 10200000.0,
            "conversion_price": 10.0,
        }])
        issues = ConvertibleBondSchema.validate(df)
        assert any("Negative" in i for i in issues)

    def test_validate_detects_non_positive_conversion_price(self):
        """测试检测非正转股价格"""
        df = pd.DataFrame([{
            "code": "123456.SZ",
            "trade_date": date(2025, 1, 2),
            "open": 100.0,
            "high": 105.0,
            "low": 98.0,
            "close": 102.0,
            "volume": 100000,
            "amount": 10200000.0,
            "conversion_price": 0,
        }])
        issues = ConvertibleBondSchema.validate(df)
        assert any("conversion_price" in i for i in issues)

    def test_partition_values(self):
        """测试分区键值"""
        df = pd.DataFrame([{
            "code": "123456.SZ",
            "trade_date": date(2025, 1, 15),
        }])
        pv = ConvertibleBondSchema.partition_values(df)
        assert pv["asset_type"] == "cb"
        assert pv["year"] == "2025"
        assert pv["month"] == "01"

    def test_in_schema_registry(self):
        """测试注册到 SCHEMA_REGISTRY"""
        assert "convertible_bond" in SCHEMA_REGISTRY
        assert SCHEMA_REGISTRY["convertible_bond"] is ConvertibleBondSchema


class TestConvertibleBondCleaner:
    """测试 ConvertibleBondCleaner"""

    def test_calculates_conversion_value(self):
        """测试计算转股价值"""
        df = pd.DataFrame([{
            "code": "123456.SZ",
            "close": 102.0,
            "conversion_price": 10.0,
        }])
        cleaner = ConvertibleBondCleaner()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = cleaner.clean(df, ctx)
        assert "conversion_value" in result.columns
        assert result["conversion_value"].iloc[0] == pytest.approx(1020.0)

    def test_calculates_premium_rate(self):
        """测试计算溢价率"""
        df = pd.DataFrame([{
            "code": "123456.SZ",
            "close": 102.0,
            "conversion_value": 100.0,
        }])
        cleaner = ConvertibleBondCleaner()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = cleaner.clean(df, ctx)
        assert "premium_rate" in result.columns
        assert result["premium_rate"].iloc[0] == pytest.approx(2.0)

    def test_marks_high_premium(self):
        """测试标记高溢价率"""
        df = pd.DataFrame([{
            "code": "123456.SZ",
            "close": 200.0,
            "conversion_value": 100.0,
        }])
        cleaner = ConvertibleBondCleaner()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = cleaner.clean(df, ctx)
        assert "high_premium" in result.columns
        # 溢价率 = (200 - 100) / 100 * 100 = 100% > 50%
        assert result["high_premium"].iloc[0] == True

    def test_marks_near_maturity(self):
        """测试标记临近到期"""
        from datetime import date, timedelta
        near_date = date.today() + timedelta(days=30)
        df = pd.DataFrame([{
            "code": "123456.SZ",
            "maturity_date": near_date,
        }])
        cleaner = ConvertibleBondCleaner()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = cleaner.clean(df, ctx)
        assert "near_maturity" in result.columns
        assert result["near_maturity"].iloc[0] == True

    def test_validate_passes_on_valid_data(self):
        """测试有效数据通过校验"""
        df = pd.DataFrame([{
            "conversion_price": 10.0,
            "premium_rate": 5.0,
        }])
        cleaner = ConvertibleBondCleaner()
        issues = cleaner.validate(df)
        assert len(issues) == 0

    def test_validate_detects_non_positive_conversion_price(self):
        """测试检测非正转股价格"""
        df = pd.DataFrame([{
            "conversion_price": 0,
            "premium_rate": 5.0,
        }])
        cleaner = ConvertibleBondCleaner()
        issues = cleaner.validate(df)
        assert len(issues) > 0
        assert any("conversion_price" in i for i in issues)
