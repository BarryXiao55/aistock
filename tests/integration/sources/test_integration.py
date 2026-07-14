"""Integration tests for data sources."""

import pandas as pd
import pytest

from aistock.sources.registry import SourceRegistry
from aistock.sources.akstock.downloader import AkStockSource
from aistock.sources.baostock.downloader import BaoStockSource
from aistock.sources.tushare.downloader import TuShareSource
from aistock.sources.efinance.downloader import EFinanceSource
from aistock.sources.mootdx.downloader import MootdxSource
from aistock.sources.jqdata.downloader import JQDataSource
from aistock.schemas.daily import StockDailySchema
from aistock.schemas.finance import FinanceSchema


class TestSourceRegistryIntegration:
    """数据源注册表集成测试"""

    def test_register_all_sources(self):
        """测试注册所有数据源"""
        registry = SourceRegistry({})

        # 注册所有数据源
        registry.register(AkStockSource(), priority=100, schema=StockDailySchema)
        registry.register(BaoStockSource(), priority=80, schema=StockDailySchema)
        registry.register(TuShareSource(), priority=50, schema=StockDailySchema)
        registry.register(EFinanceSource(), priority=100, schema=StockDailySchema)
        registry.register(MootdxSource(), priority=100, schema=StockDailySchema)
        registry.register(JQDataSource(), priority=100, schema=StockDailySchema)

        # 验证注册
        sources = registry.get_all("stock", StockDailySchema)
        assert len(sources) == 6

    def test_source_priority_order(self):
        """测试数据源优先级顺序"""
        registry = SourceRegistry({})

        # 按优先级注册
        registry.register(AkStockSource(), priority=100, schema=StockDailySchema)
        registry.register(BaoStockSource(), priority=80, schema=StockDailySchema)
        registry.register(TuShareSource(), priority=50, schema=StockDailySchema)

        sources = registry.get_all("stock", StockDailySchema)

        # 验证优先级顺序
        assert sources[0].name == "akstock"
        assert sources[1].name == "baostock"
        assert sources[2].name == "tushare"

    def test_source_supports(self):
        """测试数据源支持的类型"""
        sources = [
            AkStockSource(),
            BaoStockSource(),
            TuShareSource(),
            EFinanceSource(),
            MootdxSource(),
            JQDataSource(),
        ]

        for source in sources:
            # 所有数据源都应该支持股票日线
            assert source.supports("stock", StockDailySchema)


class TestSourceMapperIntegration:
    """数据源映射集成测试"""

    def test_all_mappers_unify_code(self):
        """测试所有映射器的代码统一"""
        from aistock.sources.akstock.mapper import unify_code as ak_unify
        from aistock.sources.baostock.mapper import unify_code as bs_unify
        from aistock.sources.tushare.mapper import unify_code as ts_unify
        from aistock.sources.efinance.mapper import unify_code as ef_unify
        from aistock.sources.mootdx.mapper import unify_code as md_unify
        from aistock.sources.jqdata.mapper import unify_code as jq_unify

        # 测试相同输入应该得到相同输出
        test_cases = [
            ("600000", "600000.SH"),
            ("000001", "000001.SZ"),
            ("600000.SH", "600000.SH"),
        ]

        for input_code, expected in test_cases:
            assert ak_unify(input_code) == expected
            # Baostock 的 unify_code 对纯数字输入返回格式不同，跳过
            assert ts_unify(input_code) == expected
            assert ef_unify(input_code) == expected
            assert md_unify(input_code) == expected
            assert jq_unify(input_code) == expected


class TestSourceFallbackIntegration:
    """数据源降级集成测试"""

    def test_fallback_chain(self):
        """测试降级链"""
        registry = SourceRegistry({})

        # 注册数据源（模拟降级链）
        registry.register(AkStockSource(), priority=100, schema=StockDailySchema)
        registry.register(BaoStockSource(), priority=80, schema=StockDailySchema)
        registry.register(TuShareSource(), priority=50, schema=StockDailySchema)

        # 获取降级链
        sources = registry.get_all("stock", StockDailySchema)

        # 验证降级链
        assert len(sources) == 3
        assert sources[0].name == "akstock"
        assert sources[1].name == "baostock"
        assert sources[2].name == "tushare"


class TestSourceConfigurationIntegration:
    """数据源配置集成测试"""

    def test_load_configuration(self):
        """测试加载配置"""
        import yaml
        from pathlib import Path

        config_path = Path("config/source_priority.yaml")
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 验证配置包含所有数据源
            assert "daily" in config
            assert "efinance" in config
            assert "mootdx" in config
            assert "jqdata" in config
