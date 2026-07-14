"""Test EFinance data source."""

import pandas as pd
import pytest

from aistock.sources.efinance.mapper import map_daily_columns, map_realtime_columns, unify_code


class TestEFinanceMapper:
    """测试 EFinance 数据映射"""

    def test_map_daily_columns(self):
        """测试日线列名映射"""
        df = pd.DataFrame({
            "股票代码": ["000001"],
            "股票名称": ["平安银行"],
            "日期": ["2025-01-02"],
            "开盘": [10.0],
            "收盘": [10.5],
            "最高": [10.8],
            "最低": [9.8],
            "成交量": [1000000],
            "成交额": [10500000.0],
            "换手率": [0.05],
        })

        result = map_daily_columns(df)

        assert "code" in result.columns
        assert "trade_date" in result.columns
        assert "open" in result.columns
        assert "close" in result.columns
        assert "asset_type" in result.columns
        assert result["asset_type"].iloc[0] == "stock"

    def test_map_realtime_columns(self):
        """测试实时行情列名映射"""
        df = pd.DataFrame({
            "code": ["000001"],
            "name": ["平安银行"],
            "price": [10.5],
        })

        result = map_realtime_columns(df)

        assert "asset_type" in result.columns
        assert result["asset_type"].iloc[0] == "stock"

    def test_unify_code_sh(self):
        """测试沪市代码转换"""
        assert unify_code("600000") == "600000.SH"
        assert unify_code("600000.SH") == "600000.SH"

    def test_unify_code_sz(self):
        """测试深市代码转换"""
        assert unify_code("000001") == "000001.SZ"
        assert unify_code("000001.SZ") == "000001.SZ"

    def test_unify_code_bj(self):
        """测试北交所代码转换"""
        assert unify_code("830001") == "830001.BJ"


class TestEFinanceClient:
    """测试 EFinance 客户端"""

    def test_client_initialization(self):
        """测试客户端初始化"""
        from aistock.sources.efinance.client import EFinanceClient

        client = EFinanceClient()
        assert client._retry_count == 3
        assert client._retry_delay == 5

    def test_client_with_config(self):
        """测试带配置的客户端"""
        from aistock.sources.efinance.client import EFinanceClient

        config = {
            "retry_count": 5,
            "retry_delay": 10,
        }
        client = EFinanceClient(config)
        assert client._retry_count == 5
        assert client._retry_delay == 10


class TestEFinanceSource:
    """测试 EFinance 数据源"""

    def test_source_initialization(self):
        """测试数据源初始化"""
        from aistock.sources.efinance.downloader import EFinanceSource
        from aistock.schemas.daily import StockDailySchema

        source = EFinanceSource()
        assert source.name == "efinance"
        assert source.supports("stock", StockDailySchema)

    def test_source_supports(self):
        """测试支持的数据类型"""
        from aistock.sources.efinance.downloader import EFinanceSource
        from aistock.schemas.daily import StockDailySchema

        source = EFinanceSource()
        assert source.supports("stock", StockDailySchema)
        assert source.supports("fund", StockDailySchema)
        assert source.supports("futures", StockDailySchema)
        assert not source.supports("index", StockDailySchema)
