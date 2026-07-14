"""Integration tests for factor calculation layer."""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from aistock.factors.interface import FactorCategory, FactorFrequency
from aistock.factors.registry import FactorRegistry, get_global_registry
from aistock.factors.technical.momentum import Momentum5DFactor, Momentum20DFactor
from aistock.factors.technical.volatility import Volatility20DFactor, ATRFactor
from aistock.factors.technical.indicators import RSIFactor, MACDFactor
from aistock.factors.fundamental.value import PEFactor, PBFactor
from aistock.factors.fundamental.quality import ROEFactor
from aistock.factors.alternative.fund_flow import NorthFlowNetFactor
from aistock.factors.alternative.sentiment import MarketBreadthFactor
from aistock.factors.storage.storage import FactorStorage, FactorQuery
from aistock.factors.analysis.analyzer import FactorAnalyzer
from aistock.factors.analysis.normalizer import FactorNormalizer
from aistock.factors.analysis.cache import FactorCache


@pytest.fixture
def sample_stock_data():
    """创建股票测试数据"""
    np.random.seed(42)
    n = 100

    close = 10 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)

    df = pd.DataFrame({
        "trade_date": pd.date_range("2025-01-01", periods=n),
        "code": ["000001.SZ"] * n,
        "open": close + np.random.randn(n) * 0.1,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.random.randint(1000000, 5000000, n),
        "amount": np.random.uniform(10000000, 50000000, n),
        "turnover": np.random.uniform(0.01, 0.1, n),
        "eps": np.random.uniform(0.5, 2.0, n),
        "bps": np.random.uniform(5.0, 15.0, n),
        "pct_change": np.random.randn(n) * 5,
    })
    df.set_index("trade_date", inplace=True)
    return df


class TestFactorRegistryIntegration:
    """因子注册表集成测试"""

    def test_register_and_use_factors(self):
        """测试注册和使用因子"""
        registry = FactorRegistry()

        # 注册多个因子
        registry.register("momentum_5d", Momentum5DFactor())
        registry.register("momentum_20d", Momentum20DFactor())
        registry.register("volatility_20d", Volatility20DFactor())
        registry.register("rsi_14", RSIFactor())

        # 验证注册
        assert len(registry) == 4
        assert "momentum_5d" in registry
        assert "rsi_14" in registry

        # 按类别列出
        technical_factors = registry.list_factors(FactorCategory.TECHNICAL)
        assert len(technical_factors) == 4

    def test_factor_calculation_workflow(self, sample_stock_data):
        """测试因子计算工作流"""
        registry = FactorRegistry()
        registry.register("momentum_20d", Momentum20DFactor())
        registry.register("rsi_14", RSIFactor())

        # 计算因子
        momentum_factor = registry.get("momentum_20d")
        momentum_result = momentum_factor.calculate(sample_stock_data)

        rsi_factor = registry.get("rsi_14")
        rsi_result = rsi_factor.calculate(sample_stock_data)

        # 验证结果
        assert momentum_result.success is True
        assert rsi_result.success is True
        assert "momentum_20d" in momentum_result.data.columns
        assert "rsi_14" in rsi_result.data.columns


class TestFactorStorageIntegration:
    """因子存储集成测试"""

    def test_save_and_load_workflow(self, sample_stock_data):
        """测试保存和加载工作流"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FactorStorage(tmpdir)

            # 计算因子
            factor = Momentum20DFactor()
            result = factor.calculate(sample_stock_data)

            # 保存因子
            from aistock.factors.interface import FactorMetadata, FactorCategory, FactorFrequency
            metadata = FactorMetadata(
                name="momentum_20d",
                description="20日动量因子",
                category=FactorCategory.TECHNICAL,
                frequency=FactorFrequency.DAILY,
            )
            storage.save("momentum_20d", result.data, metadata)

            # 加载因子
            loaded_data = storage.load("momentum_20d")
            assert len(loaded_data) == len(sample_stock_data)

            # 查询因子
            query = FactorQuery(storage)
            latest = query.query_latest("momentum_20d", n=5)
            assert len(latest) == 5

    def test_factor_analysis_workflow(self, sample_stock_data):
        """测试因子分析工作流"""
        # 计算因子
        factor = Momentum20DFactor()
        factor_result = factor.calculate(sample_stock_data)

        # 创建前瞻收益（简化）
        forward_returns = sample_stock_data["close"].pct_change().shift(-5)

        # 分析因子
        analyzer = FactorAnalyzer()
        analysis_result = analyzer.analyze(
            factor_result.data["momentum_20d"],
            forward_returns,
        )

        # 验证分析结果
        assert analysis_result.ic_mean is not None
        assert analysis_result.ir is not None
        assert analysis_result.sharpe_ratio is not None


class TestFactorNormalizationIntegration:
    """因子标准化集成测试"""

    def test_normalization_workflow(self, sample_stock_data):
        """测试标准化工作流"""
        # 计算因子
        factor = Momentum20DFactor()
        result = factor.calculate(sample_stock_data)

        # 标准化
        normalizer = FactorNormalizer()

        # Z-Score
        zscore_result = normalizer.zscore(
            result.data["momentum_20d"],
            factor_name="momentum_20d",
        )
        assert abs(zscore_result.mean()) < 0.1

        # MinMax
        minmax_result = normalizer.minmax(result.data["momentum_20d"])
        assert minmax_result.min() >= 0
        assert minmax_result.max() <= 1

        # Rank
        rank_result = normalizer.rank(result.data["momentum_20d"])
        assert rank_result.min() > 0
        assert rank_result.max() <= 1


class TestFactorCacheIntegration:
    """因子缓存集成测试"""

    def test_caching_workflow(self, sample_stock_data):
        """测试缓存工作流"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FactorCache(tmpdir)

            # 计算因子
            factor = Momentum20DFactor()
            result = factor.calculate(sample_stock_data)

            # 缓存结果
            cache.set("momentum_20d", result.data)

            # 从缓存加载
            cached_data = cache.get("momentum_20d")
            assert cached_data is not None
            pd.testing.assert_frame_equal(cached_data, result.data)


class TestFullPipelineIntegration:
    """完整管道集成测试"""

    def test_end_to_end_factor_pipeline(self, sample_stock_data):
        """测试端到端因子管道"""
        # 1. 创建注册表并注册因子
        registry = FactorRegistry()
        registry.register("momentum_20d", Momentum20DFactor())
        registry.register("rsi_14", RSIFactor())

        # 2. 计算所有因子
        results = {}
        for factor_name in registry.list_factors():
            factor = registry.get(factor_name)
            results[factor_name] = factor.calculate(sample_stock_data)

        # 3. 验证所有因子都计算成功
        assert len(results) == 2
        for name, result in results.items():
            assert result.success is True, f"Factor {name} failed"

        # 4. 存储因子
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FactorStorage(tmpdir)

            for name, result in results.items():
                from aistock.factors.interface import FactorMetadata, FactorCategory, FactorFrequency
                metadata = FactorMetadata(
                    name=name,
                    description=f"Factor {name}",
                    category=FactorCategory.TECHNICAL,
                    frequency=FactorFrequency.DAILY,
                )
                storage.save(name, result.data, metadata)

            # 5. 验证存储
            factors = storage.list_factors()
            assert len(factors) == 2

            # 6. 加载并验证
            for factor_name in factors:
                loaded_data = storage.load(factor_name)
                assert len(loaded_data) > 0

    def test_factor_comparison(self, sample_stock_data):
        """测试因子比较"""
        # 计算不同因子
        momentum = Momentum20DFactor()
        rsi = RSIFactor()

        momentum_result = momentum.calculate(sample_stock_data)
        rsi_result = rsi.calculate(sample_stock_data)

        # 分析因子
        analyzer = FactorAnalyzer()
        forward_returns = sample_stock_data["close"].pct_change().shift(-5)

        momentum_analysis = analyzer.analyze(
            momentum_result.data["momentum_20d"],
            forward_returns,
        )
        rsi_analysis = analyzer.analyze(
            rsi_result.data["rsi_14"],
            forward_returns,
        )

        # 比较因子
        assert momentum_analysis.ic_mean is not None
        assert rsi_analysis.ic_mean is not None
