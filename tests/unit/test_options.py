"""Test options schema and cleaning steps."""

from datetime import date

import pandas as pd
import pytest

from aistock.schemas.options import OptionsSchema
from aistock.cleaning.options import OptionsCleaner
from aistock.schemas import SCHEMA_REGISTRY
from aistock.sources.akstock_options.mapper import parse_option_code


class TestOptionsSchema:
    """测试 OptionsSchema"""

    def test_validate_passes_on_clean_data(self):
        """测试有效数据通过校验"""
        df = pd.DataFrame([{
            "code": "10002556",
            "trade_date": date(2025, 1, 2),
            "open": 0.5,
            "high": 0.6,
            "low": 0.4,
            "close": 0.55,
            "volume": 100000,
            "open_interest": 50000,
            "strike_price": 2800.0,
            "option_type": "call",
            "implied_volatility": 25.0,
            "delta": 0.6,
        }])
        assert OptionsSchema.validate(df) == []

    def test_validate_detects_missing_columns(self):
        """测试检测缺失列"""
        df = pd.DataFrame([{
            "code": "10002556",
            "trade_date": date(2025, 1, 2),
        }])
        issues = OptionsSchema.validate(df)
        assert len(issues) > 0
        assert any("Missing" in i for i in issues)

    def test_validate_detects_high_low_inversion(self):
        """测试检测 high < low"""
        df = pd.DataFrame([{
            "code": "10002556",
            "trade_date": date(2025, 1, 2),
            "open": 0.5,
            "high": 0.4,
            "low": 0.6,
            "close": 0.55,
            "volume": 100000,
            "open_interest": 50000,
            "strike_price": 2800.0,
            "option_type": "call",
        }])
        issues = OptionsSchema.validate(df)
        assert any("high" in i.lower() and "low" in i.lower() for i in issues)

    def test_validate_detects_negative_price(self):
        """测试检测负价格"""
        df = pd.DataFrame([{
            "code": "10002556",
            "trade_date": date(2025, 1, 2),
            "open": -0.5,
            "high": 0.6,
            "low": 0.4,
            "close": 0.55,
            "volume": 100000,
            "open_interest": 50000,
            "strike_price": 2800.0,
            "option_type": "call",
        }])
        issues = OptionsSchema.validate(df)
        assert any("Negative" in i for i in issues)

    def test_validate_detects_invalid_option_type(self):
        """测试检测无效期权类型"""
        df = pd.DataFrame([{
            "code": "10002556",
            "trade_date": date(2025, 1, 2),
            "open": 0.5,
            "high": 0.6,
            "low": 0.4,
            "close": 0.55,
            "volume": 100000,
            "open_interest": 50000,
            "strike_price": 2800.0,
            "option_type": "invalid",
        }])
        issues = OptionsSchema.validate(df)
        assert any("option_type" in i for i in issues)

    def test_validate_detects_invalid_delta(self):
        """测试检测无效 Delta 值"""
        df = pd.DataFrame([{
            "code": "10002556",
            "trade_date": date(2025, 1, 2),
            "open": 0.5,
            "high": 0.6,
            "low": 0.4,
            "close": 0.55,
            "volume": 100000,
            "open_interest": 50000,
            "strike_price": 2800.0,
            "option_type": "call",
            "delta": 1.5,  # 超出范围
        }])
        issues = OptionsSchema.validate(df)
        assert any("delta" in i for i in issues)

    def test_partition_values(self):
        """测试分区键值"""
        df = pd.DataFrame([{
            "code": "10002556",
            "trade_date": date(2025, 1, 15),
            "underlying": "50ETF",
            "option_type": "call",
        }])
        pv = OptionsSchema.partition_values(df)
        assert pv["asset_type"] == "option"
        assert pv["underlying"] == "50ETF"
        assert pv["option_type"] == "call"
        assert pv["year"] == "2025"
        assert pv["month"] == "01"

    def test_in_schema_registry(self):
        """测试注册到 SCHEMA_REGISTRY"""
        assert "options" in SCHEMA_REGISTRY
        assert SCHEMA_REGISTRY["options"] is OptionsSchema


class TestParseOptionCode:
    """测试期权代码解析"""

    def test_parse_call_option(self):
        """测试解析看涨期权"""
        result = parse_option_code("50ETF购1月2800")
        assert result["underlying"] == "50ETF"
        assert result["option_type"] == "call"
        assert result["strike_price"] == 2.8

    def test_parse_put_option(self):
        """测试解析看跌期权"""
        result = parse_option_code("50ETF沽1月2800")
        assert result["underlying"] == "50ETF"
        assert result["option_type"] == "put"
        assert result["strike_price"] == 2.8

    def test_parse_invalid_code(self):
        """测试解析无效代码"""
        result = parse_option_code("INVALID")
        assert result["underlying"] == "INVALID"
        assert result["option_type"] == "call"


class TestOptionsCleaner:
    """测试 OptionsCleaner"""

    def test_marks_option_status(self):
        """测试标记期权状态"""
        df = pd.DataFrame([
            {"code": "10002556", "close": 0.55, "strike_price": 2800.0, "option_type": "call"},
            {"code": "10002557", "close": 3000.0, "strike_price": 2800.0, "option_type": "call"},
            {"code": "10002558", "close": 2600.0, "strike_price": 2800.0, "option_type": "call"},
        ])
        cleaner = OptionsCleaner()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = cleaner.clean(df, ctx)
        assert "option_status" in result.columns
        assert "moneyness" in result.columns

    def test_marks_near_expiry(self):
        """测试标记临近到期"""
        from datetime import date, timedelta
        near_date = date.today() + timedelta(days=5)
        df = pd.DataFrame([{
            "code": "10002556",
            "expiry_date": near_date,
        }])
        cleaner = OptionsCleaner()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = cleaner.clean(df, ctx)
        assert "near_expiry" in result.columns
        assert result["near_expiry"].iloc[0] == True

    def test_calculates_oi_change(self):
        """测试计算持仓量变化"""
        df = pd.DataFrame([
            {"code": "10002556", "trade_date": date(2025, 1, 2), "open_interest": 50000},
            {"code": "10002556", "trade_date": date(2025, 1, 3), "open_interest": 55000},
            {"code": "10002556", "trade_date": date(2025, 1, 4), "open_interest": 52000},
        ])
        cleaner = OptionsCleaner()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = cleaner.clean(df, ctx)
        assert "oi_change" in result.columns
        assert result.iloc[1]["oi_change"] == 5000
        assert result.iloc[2]["oi_change"] == -3000

    def test_calculates_iv_change(self):
        """测试计算隐含波动率变化"""
        df = pd.DataFrame([
            {"code": "10002556", "trade_date": date(2025, 1, 2), "implied_volatility": 25.0},
            {"code": "10002556", "trade_date": date(2025, 1, 3), "implied_volatility": 30.0},
            {"code": "10002556", "trade_date": date(2025, 1, 4), "implied_volatility": 28.0},
        ])
        cleaner = OptionsCleaner()
        ctx = type("Context", (), {"log": type("Logger", (), {"info": lambda s, m: None})()})()
        result = cleaner.clean(df, ctx)
        assert "iv_change" in result.columns
        assert result.iloc[1]["iv_change"] == 5.0
        assert result.iloc[2]["iv_change"] == -2.0

    def test_validate_passes_on_valid_data(self):
        """测试有效数据通过校验"""
        df = pd.DataFrame([{
            "implied_volatility": 25.0,
            "delta": 0.6,
            "strike_price": 2800.0,
        }])
        cleaner = OptionsCleaner()
        issues = cleaner.validate(df)
        assert len(issues) == 0

    def test_validate_detects_invalid_implied_volatility(self):
        """测试检测无效隐含波动率"""
        df = pd.DataFrame([{
            "implied_volatility": 600.0,  # 超出范围
            "delta": 0.6,
            "strike_price": 2800.0,
        }])
        cleaner = OptionsCleaner()
        issues = cleaner.validate(df)
        assert len(issues) > 0
        assert any("implied_volatility" in i for i in issues)

    def test_validate_detects_invalid_delta(self):
        """测试检测无效 Delta"""
        df = pd.DataFrame([{
            "implied_volatility": 25.0,
            "delta": 1.5,  # 超出范围
            "strike_price": 2800.0,
        }])
        cleaner = OptionsCleaner()
        issues = cleaner.validate(df)
        assert len(issues) > 0
        assert any("delta" in i for i in issues)
