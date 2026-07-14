"""Test Mootdx data source."""

import pandas as pd
import pytest

from aistock.sources.mootdx.mapper import map_daily_columns, unify_code


class TestMootdxMapper:
    """测试 Mootdx 数据映射"""

    def test_map_daily_columns(self):
        """测试日线列名映射"""
        df = pd.DataFrame({
            "open": [10.0],
            "close": [10.5],
            "high": [10.8],
            "low": [9.8],
            "volume": [1000000],
            "amount": [10500000.0],
            "trade_date": ["2025-01-02"],
        })

        result = map_daily_columns(df)

        assert "trade_date" in result.columns
        assert "open" in result.columns
        assert "close" in result.columns
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


class TestMootdxClient:
    """测试 Mootdx 客户端"""

    def test_client_initialization(self):
        """测试客户端初始化"""
        from aistock.sources.mootdx.client import MootdxClient

        client = MootdxClient()
        assert client._retry_count == 3
        assert client._retry_delay == 5

    def test_client_with_config(self):
        """测试带配置的客户端"""
        from aistock.sources.mootdx.client import MootdxClient

        config = {
            "retry_count": 5,
            "retry_delay": 10,
        }
        client = MootdxClient(config)
        assert client._retry_count == 5
        assert client._retry_delay == 10


class TestMootdxSource:
    """测试 Mootdx 数据源"""

    def test_source_initialization(self):
        """测试数据源初始化"""
        from aistock.sources.mootdx.downloader import MootdxSource
        from aistock.schemas.daily import StockDailySchema

        source = MootdxSource()
        assert source.name == "mootdx"
        assert source.supports("stock", StockDailySchema)

    def test_source_supports(self):
        """测试支持的数据类型"""
        from aistock.sources.mootdx.downloader import MootdxSource
        from aistock.schemas.daily import StockDailySchema

        source = MootdxSource()
        assert source.supports("stock", StockDailySchema)
        assert source.supports("index", StockDailySchema)
        assert not source.supports("fund", StockDailySchema)
        assert not source.supports("futures", StockDailySchema)
