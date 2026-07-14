"""Test JQData data source."""

import pandas as pd
import pytest

from aistock.sources.jqdata.mapper import map_daily_columns, unify_code, to_jqcode


class TestJQDataMapper:
    """测试 JQData 数据映射"""

    def test_map_daily_columns(self):
        """测试日线列名映射"""
        df = pd.DataFrame({
            "open": [10.0],
            "close": [10.5],
            "high": [10.8],
            "low": [9.8],
            "volume": [1000000],
            "money": [10500000.0],
            "trade_date": ["2025-01-02"],
        })

        result = map_daily_columns(df)

        assert "trade_date" in result.columns
        assert "open" in result.columns
        assert "close" in result.columns
        assert "amount" in result.columns
        assert "asset_type" in result.columns
        assert result["asset_type"].iloc[0] == "stock"

    def test_unify_code_xshe(self):
        """测试 JQData XSHE 格式转换"""
        assert unify_code("000001.XSHE") == "000001.SZ"
        assert unify_code("000001.XSHE") == "000001.SZ"

    def test_unify_code_xshg(self):
        """测试 JQData XSHG 格式转换"""
        assert unify_code("600000.XSHG") == "600000.SH"

    def test_unify_code_xbj(self):
        """测试 JQData XBJ 格式转换"""
        assert unify_code("830001.XBJ") == "830001.BJ"

    def test_unify_code_simple(self):
        """测试简单代码转换"""
        assert unify_code("600000") == "600000.SH"
        assert unify_code("000001") == "000001.SZ"

    def test_to_jqcode_sz(self):
        """测试转换为 JQData SZ 格式"""
        assert to_jqcode("000001.SZ") == "000001.XSHE"

    def test_to_jqcode_sh(self):
        """测试转换为 JQData SH 格式"""
        assert to_jqcode("600000.SH") == "600000.XSHG"

    def test_to_jqcode_bj(self):
        """测试转换为 JQData BJ 格式"""
        assert to_jqcode("830001.BJ") == "830001.XBJ"


class TestJQDataClient:
    """测试 JQData 客户端"""

    def test_client_initialization(self):
        """测试客户端初始化"""
        from aistock.sources.jqdata.client import JQDataClient

        client = JQDataClient()
        assert client._retry_count == 3
        assert client._retry_delay == 5
        assert client._token == ""

    def test_client_with_config(self):
        """测试带配置的客户端"""
        from aistock.sources.jqdata.client import JQDataClient

        config = {
            "token": "test_token",
            "retry_count": 5,
            "retry_delay": 10,
        }
        client = JQDataClient(config)
        assert client._token == "test_token"
        assert client._retry_count == 5
        assert client._retry_delay == 10


class TestJQDataSource:
    """测试 JQData 数据源"""

    def test_source_initialization(self):
        """测试数据源初始化"""
        from aistock.sources.jqdata.downloader import JQDataSource
        from aistock.schemas.daily import StockDailySchema
        from aistock.schemas.finance import FinanceSchema

        source = JQDataSource()
        assert source.name == "jqdata"
        assert source.supports("stock", StockDailySchema)
        assert source.supports("stock", FinanceSchema)

    def test_source_supports(self):
        """测试支持的数据类型"""
        from aistock.sources.jqdata.downloader import JQDataSource
        from aistock.schemas.daily import StockDailySchema
        from aistock.schemas.finance import FinanceSchema

        source = JQDataSource()
        assert source.supports("stock", StockDailySchema)
        assert source.supports("index", StockDailySchema)
        assert source.supports("stock", FinanceSchema)
        assert not source.supports("fund", StockDailySchema)
        assert not source.supports("futures", StockDailySchema)
