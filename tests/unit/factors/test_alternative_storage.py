"""Test alternative factors and storage."""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from aistock.factors.interface import FactorCategory, FactorFrequency
from aistock.factors.alternative.fund_flow import (
    NorthFlowNetFactor, NorthFlowMomentumFactor,
    MarginBalanceChangeFactor, MarginRatioFactor,
)
from aistock.factors.alternative.sentiment import (
    LimitUpCountFactor, LimitDownCountFactor,
    AdvanceDeclineRatioFactor, MarketBreadthFactor, VolatilityIndexFactor,
)
from aistock.factors.storage.storage import FactorStorage, FactorQuery
from aistock.factors.storage.normalizer import ZScoreNormalizer, MinMaxNormalizer, RankNormalizer
from aistock.factors.interface import FactorMetadata


@pytest.fixture
def sample_fund_flow_data():
    """创建资金流向测试数据"""
    np.random.seed(42)
    n = 20

    df = pd.DataFrame({
        "trade_date": pd.date_range("2025-01-01", periods=n),
        "buy_amount": np.random.uniform(1000000, 5000000, n),
        "sell_amount": np.random.uniform(1000000, 5000000, n),
        "margin_balance": np.random.uniform(50000000, 100000000, n),
        "short_balance": np.random.uniform(1000000, 5000000, n),
    })
    df.set_index("trade_date", inplace=True)
    return df


@pytest.fixture
def sample_sentiment_data():
    """创建市场情绪测试数据"""
    np.random.seed(42)
    n = 100

    df = pd.DataFrame({
        "trade_date": pd.date_range("2025-01-01", periods=n),
        "close": 10 + np.cumsum(np.random.randn(n) * 0.5),
        "pct_change": np.random.randn(n) * 5,  # 涨跌幅百分比
    })
    df.set_index("trade_date", inplace=True)
    return df


class TestNorthFlowNetFactor:
    """测试北向资金净流入因子"""

    def test_calculate(self, sample_fund_flow_data):
        """测试计算"""
        factor = NorthFlowNetFactor()
        result = factor.calculate(sample_fund_flow_data)

        assert result.factor_name == "north_flow_net"
        assert result.success is True
        assert "north_flow_net" in result.data.columns

    def test_calculation_logic(self, sample_fund_flow_data):
        """测试计算逻辑"""
        factor = NorthFlowNetFactor()
        result = factor.calculate(sample_fund_flow_data)

        expected = sample_fund_flow_data["buy_amount"] - sample_fund_flow_data["sell_amount"]
        pd.testing.assert_series_equal(
            result.data["north_flow_net"], expected, check_names=False
        )


class TestNorthFlowMomentumFactor:
    """测试北向资金动量因子"""

    def test_calculate(self, sample_fund_flow_data):
        """测试计算"""
        factor = NorthFlowMomentumFactor()
        result = factor.calculate(sample_fund_flow_data)

        assert "north_flow_momentum_5d" in result.data.columns
        assert result.success is True


class TestMarginBalanceChangeFactor:
    """测试融资余额变化因子"""

    def test_calculate(self, sample_fund_flow_data):
        """测试计算"""
        factor = MarginBalanceChangeFactor()
        result = factor.calculate(sample_fund_flow_data)

        assert result.factor_name == "margin_balance_change"
        assert result.success is True
        assert "margin_balance_change" in result.data.columns


class TestMarginRatioFactor:
    """测试融资融券比率因子"""

    def test_calculate(self, sample_fund_flow_data):
        """测试计算"""
        factor = MarginRatioFactor()
        result = factor.calculate(sample_fund_flow_data)

        assert result.factor_name == "margin_ratio"
        assert result.success is True
        assert "margin_ratio" in result.data.columns


class TestLimitUpCountFactor:
    """测试涨停板数量因子"""

    def test_calculate(self, sample_sentiment_data):
        """测试计算"""
        factor = LimitUpCountFactor()
        result = factor.calculate(sample_sentiment_data)

        assert result.factor_name == "limit_up_count"
        assert result.success is True
        assert "limit_up_count" in result.data.columns


class TestLimitDownCountFactor:
    """测试跌停板数量因子"""

    def test_calculate(self, sample_sentiment_data):
        """测试计算"""
        factor = LimitDownCountFactor()
        result = factor.calculate(sample_sentiment_data)

        assert result.factor_name == "limit_down_count"
        assert result.success is True
        assert "limit_down_count" in result.data.columns


class TestAdvanceDeclineRatioFactor:
    """测试涨跌比因子"""

    def test_calculate(self, sample_sentiment_data):
        """测试计算"""
        factor = AdvanceDeclineRatioFactor()
        result = factor.calculate(sample_sentiment_data)

        assert result.factor_name == "advance_decline_ratio"
        assert result.success is True
        assert "advance_decline_ratio" in result.data.columns


class TestMarketBreadthFactor:
    """测试市场广度因子"""

    def test_calculate(self, sample_sentiment_data):
        """测试计算"""
        factor = MarketBreadthFactor()
        result = factor.calculate(sample_sentiment_data)

        assert result.factor_name == "market_breadth"
        assert result.success is True
        assert "market_breadth" in result.data.columns

    def test_breadth_range(self, sample_sentiment_data):
        """测试市场广度范围在 0-1"""
        factor = MarketBreadthFactor()
        result = factor.calculate(sample_sentiment_data)

        # 市场广度应该在 0-1 范围内
        assert (result.data["market_breadth"] >= 0).all()
        assert (result.data["market_breadth"] <= 1).all()


class TestVolatilityIndexFactor:
    """测试波动率指数因子"""

    def test_calculate(self, sample_sentiment_data):
        """测试计算"""
        factor = VolatilityIndexFactor()
        result = factor.calculate(sample_sentiment_data)

        assert "volatility_index_20d" in result.data.columns
        assert result.success is True


class TestFactorStorage:
    """测试因子存储"""

    def test_save_and_load(self, sample_fund_flow_data):
        """测试保存和加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FactorStorage(tmpdir)

            # 创建因子数据
            factor_data = pd.DataFrame({
                "factor_value": sample_fund_flow_data["buy_amount"] - sample_fund_flow_data["sell_amount"],
            })

            # 创建元数据
            metadata = FactorMetadata(
                name="test_factor",
                description="Test factor",
                category=FactorCategory.ALTERNATIVE,
                frequency=FactorFrequency.DAILY,
            )

            # 保存
            file_path = storage.save("test_factor", factor_data, metadata)
            assert Path(file_path).exists()

            # 加载
            loaded_data = storage.load("test_factor")
            pd.testing.assert_frame_equal(loaded_data, factor_data)

    def test_exists(self, sample_fund_flow_data):
        """测试存在性检查"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FactorStorage(tmpdir)

            # 不存在
            assert not storage.exists("test_factor")

            # 创建并保存
            factor_data = pd.DataFrame({"value": [1, 2, 3]})
            metadata = FactorMetadata(
                name="test_factor",
                description="Test",
                category=FactorCategory.ALTERNATIVE,
                frequency=FactorFrequency.DAILY,
            )
            storage.save("test_factor", factor_data, metadata)

            # 存在
            assert storage.exists("test_factor")

    def test_list_factors(self, sample_fund_flow_data):
        """测试列出因子"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FactorStorage(tmpdir)

            # 保存多个因子
            for i in range(3):
                factor_data = pd.DataFrame({"value": [i, i + 1]})
                metadata = FactorMetadata(
                    name=f"factor_{i}",
                    description=f"Factor {i}",
                    category=FactorCategory.ALTERNATIVE,
                    frequency=FactorFrequency.DAILY,
                )
                storage.save(f"factor_{i}", factor_data, metadata)

            # 列出因子
            factors = storage.list_factors()
            assert len(factors) == 3
            assert "factor_0" in factors
            assert "factor_1" in factors
            assert "factor_2" in factors

    def test_delete(self, sample_fund_flow_data):
        """测试删除因子"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FactorStorage(tmpdir)

            # 创建并保存
            factor_data = pd.DataFrame({"value": [1, 2, 3]})
            metadata = FactorMetadata(
                name="test_factor",
                description="Test",
                category=FactorCategory.ALTERNATIVE,
                frequency=FactorFrequency.DAILY,
            )
            storage.save("test_factor", factor_data, metadata)
            assert storage.exists("test_factor")

            # 删除
            storage.delete("test_factor")
            assert not storage.exists("test_factor")

    def test_save_with_partition(self, sample_fund_flow_data):
        """测试带分区的保存"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FactorStorage(tmpdir)

            factor_data = pd.DataFrame({"value": [1, 2, 3]})
            metadata = FactorMetadata(
                name="test_factor",
                description="Test",
                category=FactorCategory.ALTERNATIVE,
                frequency=FactorFrequency.DAILY,
            )

            # 保存到分区
            partition_keys = {"year": "2025", "month": "01"}
            file_path = storage.save("test_factor", factor_data, metadata, partition_keys)

            # 验证路径包含分区
            assert "year=2025" in file_path
            assert "month=01" in file_path


class TestFactorQuery:
    """测试因子查询"""

    def test_query_basic(self, sample_fund_flow_data):
        """测试基本查询"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FactorStorage(tmpdir)

            # 保存测试数据
            factor_data = pd.DataFrame({
                "trade_date": pd.date_range("2025-01-01", periods=10),
                "code": ["A"] * 10,
                "value": range(10),
            })
            metadata = FactorMetadata(
                name="test_factor",
                description="Test",
                category=FactorCategory.ALTERNATIVE,
                frequency=FactorFrequency.DAILY,
            )
            storage.save("test_factor", factor_data, metadata)

            # 查询
            query = FactorQuery(storage)
            result = query.query("test_factor")

            assert len(result) == 10

    def test_query_with_date_filter(self, sample_fund_flow_data):
        """测试日期过滤查询"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FactorStorage(tmpdir)

            # 保存测试数据
            factor_data = pd.DataFrame({
                "trade_date": pd.date_range("2025-01-01", periods=10),
                "value": range(10),
            })
            metadata = FactorMetadata(
                name="test_factor",
                description="Test",
                category=FactorCategory.ALTERNATIVE,
                frequency=FactorFrequency.DAILY,
            )
            storage.save("test_factor", factor_data, metadata)

            # 查询
            query = FactorQuery(storage)
            result = query.query(
                "test_factor",
                start_date="2025-01-05",
                end_date="2025-01-08",
            )

            assert len(result) == 4

    def test_query_latest(self, sample_fund_flow_data):
        """测试查询最新数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FactorStorage(tmpdir)

            # 保存测试数据
            factor_data = pd.DataFrame({
                "trade_date": pd.date_range("2025-01-01", periods=10),
                "value": range(10),
            })
            metadata = FactorMetadata(
                name="test_factor",
                description="Test",
                category=FactorCategory.ALTERNATIVE,
                frequency=FactorFrequency.DAILY,
            )
            storage.save("test_factor", factor_data, metadata)

            # 查询最新 3 条
            query = FactorQuery(storage)
            result = query.query_latest("test_factor", n=3)

            assert len(result) == 3
            # 应该是最新的数据
            assert result["trade_date"].max() == pd.Timestamp("2025-01-10")


class TestZScoreNormalizer:
    """测试 Z-Score 标准化"""

    def test_calculate(self, sample_sentiment_data):
        """测试计算"""
        from aistock.factors.technical.momentum import Momentum20DFactor

        base_factor = Momentum20DFactor()
        normalizer = ZScoreNormalizer("momentum_20d", base_factor)

        result = normalizer.calculate(sample_sentiment_data)

        assert result.factor_name == "momentum_20d_zscore"
        assert result.success is True
        assert "momentum_20d_zscore" in result.data.columns

    def test_zscore_properties(self, sample_sentiment_data):
        """测试 Z-Score 属性"""
        from aistock.factors.technical.momentum import Momentum20DFactor

        base_factor = Momentum20DFactor()
        normalizer = ZScoreNormalizer("momentum_20d", base_factor)

        result = normalizer.calculate(sample_sentiment_data)

        # Z-Score 应该均值为 0，标准差为 1
        valid_values = result.data["momentum_20d_zscore"].dropna()
        assert abs(valid_values.mean()) < 0.1
        assert abs(valid_values.std() - 1.0) < 0.1


class TestMinMaxNormalizer:
    """测试 MinMax 标准化"""

    def test_calculate(self, sample_sentiment_data):
        """测试计算"""
        from aistock.factors.technical.momentum import Momentum20DFactor

        base_factor = Momentum20DFactor()
        normalizer = MinMaxNormalizer("momentum_20d", base_factor)

        result = normalizer.calculate(sample_sentiment_data)

        assert result.factor_name == "momentum_20d_minmax"
        assert result.success is True
        assert "momentum_20d_minmax" in result.data.columns

    def test_minmax_range(self, sample_sentiment_data):
        """测试 MinMax 范围在 0-1"""
        from aistock.factors.technical.momentum import Momentum20DFactor

        base_factor = Momentum20DFactor()
        normalizer = MinMaxNormalizer("momentum_20d", base_factor)

        result = normalizer.calculate(sample_sentiment_data)

        valid_values = result.data["momentum_20d_minmax"].dropna()
        assert (valid_values >= 0).all()
        assert (valid_values <= 1).all()


class TestRankNormalizer:
    """测试排名标准化"""

    def test_calculate(self, sample_sentiment_data):
        """测试计算"""
        from aistock.factors.technical.momentum import Momentum20DFactor

        base_factor = Momentum20DFactor()
        normalizer = RankNormalizer("momentum_20d", base_factor)

        result = normalizer.calculate(sample_sentiment_data)

        assert result.factor_name == "momentum_20d_rank"
        assert result.success is True
        assert "momentum_20d_rank" in result.data.columns

    def test_rank_range(self, sample_sentiment_data):
        """测试排名范围在 0-1"""
        from aistock.factors.technical.momentum import Momentum20DFactor

        base_factor = Momentum20DFactor()
        normalizer = RankNormalizer("momentum_20d", base_factor)

        result = normalizer.calculate(sample_sentiment_data)

        valid_values = result.data["momentum_20d_rank"].dropna()
        assert (valid_values >= 0).all()
        assert (valid_values <= 1).all()
