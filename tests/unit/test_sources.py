"""Test data source plugins."""

import pytest
from datetime import date

import pandas as pd

from aistock.pipeline.source import SourceNode
from aistock.pipeline.models import FetchSpec
from aistock.schemas.daily import StockDailySchema
from aistock.schemas.finance import FinanceSchema
from aistock.sources.akstock.downloader import AkStockSource
from aistock.sources.akstock.mapper import map_daily_columns, unify_code
from aistock.sources.baostock.downloader import BaoStockSource
from aistock.sources.baostock.mapper import map_daily_columns as bs_map_daily_columns
from aistock.sources.baostock.mapper import unify_code as bs_unify_code
from aistock.sources.tushare.downloader import TuShareSource
from aistock.sources.tushare.mapper import map_daily_columns as ts_map_daily_columns
from aistock.sources.tushare.mapper import unify_code as ts_unify_code
from aistock.sources.registry import SourceRegistry


class TestAkStockMapper:
    """测试 AkShare 数据映射"""

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

    def test_map_daily_columns(self):
        """测试日线列名映射"""
        df = pd.DataFrame({
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
        assert "trade_date" in result.columns
        assert "open" in result.columns
        assert "close" in result.columns
        assert "volume" in result.columns
        assert result["asset_type"].iloc[0] == "stock"


class TestBaoStockMapper:
    """测试 Baostock 数据映射"""

    def test_unify_code_sh(self):
        """测试沪市代码转换"""
        assert bs_unify_code("sh.600000") == "600000.SH"

    def test_unify_code_sz(self):
        """测试深市代码转换"""
        assert bs_unify_code("sz.000001") == "000001.SZ"

    def test_map_daily_columns(self):
        """测试日线列名映射"""
        df = pd.DataFrame({
            "date": ["2025-01-02"],
            "code": ["sh.600000"],
            "open": ["10.00"],
            "high": ["10.80"],
            "low": ["9.80"],
            "close": ["10.50"],
            "volume": ["1000000"],
            "amount": ["10500000"],
            "turn": ["0.05"],
        })
        result = bs_map_daily_columns(df)
        assert "trade_date" in result.columns
        assert "open" in result.columns
        assert result["asset_type"].iloc[0] == "stock"


class TestTuShareMapper:
    """测试 Tushare 数据映射"""

    def test_unify_code(self):
        """测试代码转换"""
        assert ts_unify_code("000001.SZ") == "000001.SZ"
        assert ts_unify_code("600000") == "600000.SH"

    def test_map_daily_columns(self):
        """测试日线列名映射"""
        df = pd.DataFrame({
            "ts_code": ["000001.SZ"],
            "trade_date": ["20250102"],
            "open": [10.0],
            "high": [10.8],
            "low": [9.8],
            "close": [10.5],
            "vol": [1000000],
            "amount": [10500000.0],
        })
        result = ts_map_daily_columns(df)
        assert "trade_date" in result.columns
        assert "volume" in result.columns
        assert result["trade_date"].iloc[0] == date(2025, 1, 2)


class TestAkStockSource:
    """测试 AkShare 数据源"""

    def test_is_source_node(self):
        """测试是否继承自 SourceNode"""
        source = AkStockSource()
        assert isinstance(source, SourceNode)

    def test_name(self):
        """测试数据源名称"""
        source = AkStockSource()
        assert source.name == "akstock"

    def test_supports_stock_daily(self):
        """测试支持股票日线"""
        source = AkStockSource()
        assert source.supports("stock", StockDailySchema)

    def test_supports_index_daily(self):
        """测试支持指数日线"""
        source = AkStockSource()
        assert source.supports("index", StockDailySchema)

    def test_supports_finance(self):
        """测试支持财务数据"""
        source = AkStockSource()
        assert source.supports("stock", FinanceSchema)

    def test_does_not_support_unsupported(self):
        """测试不支持的数据类型"""
        source = AkStockSource()
        assert not source.supports("future", StockDailySchema)


class TestBaoStockSource:
    """测试 Baostock 数据源"""

    def test_is_source_node(self):
        """测试是否继承自 SourceNode"""
        source = BaoStockSource()
        assert isinstance(source, SourceNode)

    def test_name(self):
        """测试数据源名称"""
        source = BaoStockSource()
        assert source.name == "baostock"

    def test_supports_stock_daily(self):
        """测试支持股票日线"""
        source = BaoStockSource()
        assert source.supports("stock", StockDailySchema)

    def test_does_not_support_finance(self):
        """测试不支持财务数据"""
        source = BaoStockSource()
        assert not source.supports("stock", FinanceSchema)


class TestTuShareSource:
    """测试 Tushare 数据源"""

    def test_is_source_node(self):
        """测试是否继承自 SourceNode"""
        source = TuShareSource()
        assert isinstance(source, SourceNode)

    def test_name(self):
        """测试数据源名称"""
        source = TuShareSource()
        assert source.name == "tushare"

    def test_supports_stock_daily(self):
        """测试支持股票日线"""
        source = TuShareSource()
        assert source.supports("stock", StockDailySchema)

    def test_supports_finance(self):
        """测试支持财务数据"""
        source = TuShareSource()
        assert source.supports("stock", FinanceSchema)


class TestSourceRegistry:
    """测试数据源注册表"""

    def test_register_and_get(self):
        """测试注册和获取"""
        registry = SourceRegistry({})
        ak = AkStockSource()
        registry.register(ak, priority=100, schema=StockDailySchema)

        sources = registry.get_all("stock", StockDailySchema)
        assert len(sources) == 1
        assert sources[0].name == "akstock"

    def test_priority_order(self):
        """测试优先级排序"""
        registry = SourceRegistry({})
        ak = AkStockSource()
        bs = BaoStockSource()

        registry.register(ak, priority=100, schema=StockDailySchema)
        registry.register(bs, priority=80, schema=StockDailySchema)

        sources = registry.get_all("stock", StockDailySchema)
        assert len(sources) == 2
        assert sources[0].name == "akstock"
        assert sources[1].name == "baostock"

    def test_primary_source(self):
        """测试获取主数据源"""
        registry = SourceRegistry({})
        ak = AkStockSource()
        bs = BaoStockSource()

        registry.register(ak, priority=100, schema=StockDailySchema)
        registry.register(bs, priority=80, schema=StockDailySchema)

        assert registry.primary == "akstock"
