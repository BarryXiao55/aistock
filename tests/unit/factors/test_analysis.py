"""Test factor analysis and optimization."""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from aistock.factors.analysis.analyzer import FactorAnalyzer, FactorAnalysisResult
from aistock.factors.analysis.normalizer import FactorNormalizer
from aistock.factors.analysis.cache import FactorCache


@pytest.fixture
def sample_factor_data():
    """创建因子测试数据"""
    np.random.seed(42)
    n = 100

    # 创建因子值
    factor_values = pd.Series(
        np.random.randn(n),
        index=pd.date_range("2025-01-01", periods=n),
        name="factor",
    )

    # 创建前瞻收益（与因子有一定相关性）
    forward_returns = pd.Series(
        factor_values * 0.1 + np.random.randn(n) * 0.5,
        index=pd.date_range("2025-01-01", periods=n),
        name="returns",
    )

    return factor_values, forward_returns


class TestFactorAnalyzer:
    """测试因子分析器"""

    def test_analyze(self, sample_factor_data):
        """测试分析"""
        factor_values, forward_returns = sample_factor_data
        analyzer = FactorAnalyzer()

        result = analyzer.analyze(factor_values, forward_returns)

        assert isinstance(result, FactorAnalysisResult)
        assert result.factor_name == "analyzed_factor"
        assert -1 <= result.ic_mean <= 1
        assert result.ir is not None
        assert 0 <= result.turnover_mean <= 1
        assert result.max_drawdown <= 0

    def test_analyze_perfect_correlation(self):
        """测试完美相关"""
        # 创建多个资产的数据（每天有多条记录）
        n_assets = 10
        n_days = 10

        factor_values = []
        forward_returns = []
        dates = []

        for day in range(n_days):
            for asset in range(n_assets):
                dates.append(pd.Timestamp("2025-01-01") + pd.Timedelta(days=day))
                factor_values.append(asset + day * 0.1)
                forward_returns.append(asset + day * 0.1)

        factor_values = pd.Series(factor_values, index=dates)
        forward_returns = pd.Series(forward_returns, index=dates)

        analyzer = FactorAnalyzer()
        result = analyzer.analyze(factor_values, forward_returns)

        # 完美正相关
        assert result.ic_mean > 0.9

    def test_analyze_no_correlation(self):
        """测试无相关"""
        np.random.seed(42)
        n = 100
        factor_values = pd.Series(
            np.random.randn(n),
            index=pd.date_range("2025-01-01", periods=n),
        )
        forward_returns = pd.Series(
            np.random.randn(n),
            index=pd.date_range("2025-01-01", periods=n),
        )

        analyzer = FactorAnalyzer()
        result = analyzer.analyze(factor_values, forward_returns)

        # 无相关时 IC 应接近 0
        assert abs(result.ic_mean) < 0.2

    def test_analyze_empty_data(self):
        """测试空数据"""
        factor_values = pd.Series([], dtype=float)
        forward_returns = pd.Series([], dtype=float)

        analyzer = FactorAnalyzer()
        result = analyzer.analyze(factor_values, forward_returns)

        assert result.ic_mean == 0.0
        assert result.ir == 0.0

    def test_analyze_by_group(self, sample_factor_data):
        """测试分组分析"""
        factor_values, forward_returns = sample_factor_data
        groups = pd.Series(
            np.random.choice(["A", "B", "C"], size=len(factor_values)),
            index=factor_values.index,
        )

        analyzer = FactorAnalyzer()
        results = analyzer.analyze_by_group(factor_values, forward_returns, groups)

        assert len(results) == 3
        assert "A" in results
        assert "B" in results
        assert "C" in results

    def test_result_to_dict(self, sample_factor_data):
        """测试结果转换为字典"""
        factor_values, forward_returns = sample_factor_data
        analyzer = FactorAnalyzer()

        result = analyzer.analyze(factor_values, forward_returns)
        d = result.to_dict()

        assert d["factor_name"] == "analyzed_factor"
        assert "ic_mean" in d
        assert "sharpe_ratio" in d


class TestFactorNormalizer:
    """测试因子标准化器"""

    def test_zscore(self):
        """测试 Z-Score 标准化"""
        normalizer = FactorNormalizer()
        data = pd.Series([1, 2, 3, 4, 5])

        result = normalizer.zscore(data)

        # Z-Score 应该均值为 0，标准差为 1
        assert abs(result.mean()) < 0.1
        assert abs(result.std() - 1.0) < 0.1

    def test_zscore_with_params(self):
        """测试 Z-Score 标准化保存参数"""
        normalizer = FactorNormalizer()
        data = pd.Series([1, 2, 3, 4, 5])

        normalizer.zscore(data, factor_name="test")

        params = normalizer.get_params("test")
        assert params is not None
        assert "mean" in params
        assert "std" in params

    def test_minmax(self):
        """测试 MinMax 标准化"""
        normalizer = FactorNormalizer()
        data = pd.Series([1, 2, 3, 4, 5])

        result = normalizer.minmax(data)

        # MinMax 应该在 0-1 范围内
        assert result.min() == 0
        assert result.max() == 1

    def test_rank(self):
        """测试排名标准化"""
        normalizer = FactorNormalizer()
        data = pd.Series([5, 3, 1, 4, 2])

        result = normalizer.rank(data)

        # 排名应该在 0-1 范围内
        assert result.min() > 0
        assert result.max() <= 1

    def test_winsorize(self):
        """测试 Winsorize 标准化"""
        normalizer = FactorNormalizer()
        data = pd.Series([1, 2, 3, 4, 5, 100, -100])

        result = normalizer.winsorize(data, lower_percentile=0.1, upper_percentile=0.9)

        # Winsorize 应该限制极端值
        assert result.min() >= data.quantile(0.1)
        assert result.max() <= data.quantile(0.9)

    def test_save_and_load_params(self, sample_factor_data):
        """测试保存和加载参数"""
        normalizer = FactorNormalizer()
        data = pd.Series([1, 2, 3, 4, 5])

        normalizer.zscore(data, factor_name="test")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            file_path = f.name

        try:
            normalizer.save_params(file_path)

            new_normalizer = FactorNormalizer()
            new_normalizer.load_params(file_path)

            params = new_normalizer.get_params("test")
            assert params is not None
        finally:
            Path(file_path).unlink()


class TestFactorCache:
    """测试因子缓存"""

    def test_set_and_get(self):
        """测试设置和获取"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FactorCache(tmpdir)

            data = pd.DataFrame({"value": [1, 2, 3]})
            cache.set("test_key", data)

            result = cache.get("test_key")
            assert result is not None
            pd.testing.assert_frame_equal(result, data)

    def test_get_nonexistent(self):
        """测试获取不存在的缓存"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FactorCache(tmpdir)

            result = cache.get("nonexistent")
            assert result is None

    def test_delete(self):
        """测试删除缓存"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FactorCache(tmpdir)

            data = pd.DataFrame({"value": [1, 2, 3]})
            cache.set("test_key", data)
            assert cache.get("test_key") is not None

            cache.delete("test_key")
            assert cache.get("test_key") is None

    def test_clear(self):
        """测试清空缓存"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FactorCache(tmpdir)

            # 添加多个缓存
            for i in range(3):
                data = pd.DataFrame({"value": [i]})
                cache.set(f"key_{i}", data)

            # 检查内存缓存数量
            assert len(cache._memory_cache) == 3

            cache.clear()
            assert len(cache._memory_cache) == 0

    def test_cache_decorator(self):
        """测试缓存装饰器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FactorCache(tmpdir)
            call_count = 0

            @cache.cache_decorator()
            def expensive_function(x):
                nonlocal call_count
                call_count += 1
                return x * 2

            # 第一次调用
            result1 = expensive_function(5)
            assert result1 == 10
            assert call_count == 1

            # 第二次调用（应该使用缓存）
            result2 = expensive_function(5)
            assert result2 == 10
            assert call_count == 1  # 没有增加

            # 不同参数的调用
            result3 = expensive_function(10)
            assert result3 == 20
            assert call_count == 2

    def test_repr(self):
        """测试字符串表示"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FactorCache(tmpdir, ttl=60)
            assert "FactorCache" in repr(cache)
            assert "60" in repr(cache)
