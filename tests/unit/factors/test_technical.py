"""Test technical factors calculation."""

import numpy as np
import pandas as pd
import pytest

from aistock.factors.interface import FactorCategory, FactorFrequency
from aistock.factors.technical.momentum import (
    Momentum5DFactor, Momentum20DFactor, Momentum60DFactor, MomentumCustomFactor,
)
from aistock.factors.technical.volatility import (
    Volatility20DFactor, ATRFactor, RealizedVolatilityFactor,
)
from aistock.factors.technical.liquidity import (
    TurnoverRateFactor, AmihudFactor, VolumeMomentumFactor,
)
from aistock.factors.technical.indicators import (
    RSIFactor, MACDFactor, BollingerBandsFactor, KDJFactor,
)


@pytest.fixture
def sample_data():
    """创建测试数据"""
    np.random.seed(42)
    n = 100

    # 生成模拟价格数据
    close = 10 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)

    df = pd.DataFrame({
        "trade_date": pd.date_range("2025-01-01", periods=n),
        "open": close + np.random.randn(n) * 0.1,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.random.randint(1000000, 5000000, n),
        "amount": np.random.uniform(10000000, 50000000, n),
        "turnover": np.random.uniform(0.01, 0.1, n),
    })
    df.set_index("trade_date", inplace=True)
    return df


class TestMomentum5DFactor:
    """测试 5 日动量因子"""

    def test_metadata(self):
        """测试元数据"""
        factor = Momentum5DFactor()
        metadata = factor.metadata

        assert metadata.name == "momentum_5d"
        assert metadata.category == FactorCategory.TECHNICAL
        assert metadata.frequency == FactorFrequency.DAILY
        assert "close" in metadata.data_requirements

    def test_calculate(self, sample_data):
        """测试计算"""
        factor = Momentum5DFactor()
        result = factor.calculate(sample_data)

        assert result.factor_name == "momentum_5d"
        assert result.success is True
        assert len(result.data) == len(sample_data)
        assert "momentum_5d" in result.data.columns

    def test_missing_column(self):
        """测试缺失列"""
        factor = Momentum5DFactor()
        data = pd.DataFrame({"volume": [1000, 2000]})
        result = factor.calculate(data)

        assert result.success is False
        assert "Missing" in result.error_message


class TestMomentum20DFactor:
    """测试 20 日动量因子"""

    def test_calculate(self, sample_data):
        """测试计算"""
        factor = Momentum20DFactor()
        result = factor.calculate(sample_data)

        assert result.factor_name == "momentum_20d"
        assert result.success is True
        assert "momentum_20d" in result.data.columns


class TestMomentum60DFactor:
    """测试 60 日动量因子"""

    def test_calculate(self, sample_data):
        """测试计算"""
        factor = Momentum60DFactor()
        result = factor.calculate(sample_data)

        assert result.factor_name == "momentum_60d"
        assert result.success is True
        assert "momentum_60d" in result.data.columns


class TestMomentumCustomFactor:
    """测试自定义动量因子"""

    def test_custom_window(self, sample_data):
        """测试自定义窗口"""
        factor = MomentumCustomFactor(window=10)
        result = factor.calculate(sample_data)

        assert result.factor_name == "momentum_10d"
        assert result.success is True
        assert "momentum_10d" in result.data.columns

    def test_override_window(self, sample_data):
        """测试参数覆盖窗口"""
        factor = MomentumCustomFactor(window=20)
        result = factor.calculate(sample_data, params={"window": 30})

        assert result.factor_name == "momentum_30d"


class TestVolatility20DFactor:
    """测试 20 日波动率因子"""

    def test_calculate(self, sample_data):
        """测试计算"""
        factor = Volatility20DFactor()
        result = factor.calculate(sample_data)

        assert result.factor_name == "volatility_20d"
        assert result.success is True
        assert "volatility_20d" in result.data.columns

    def test_volatility_positive(self, sample_data):
        """测试波动率为正"""
        factor = Volatility20DFactor()
        result = factor.calculate(sample_data)

        # 波动率应该为正数
        valid_values = result.data["volatility_20d"].dropna()
        assert (valid_values >= 0).all()


class TestATRFactor:
    """测试 ATR 因子"""

    def test_calculate(self, sample_data):
        """测试计算"""
        factor = ATRFactor()
        result = factor.calculate(sample_data)

        assert result.factor_name == "atr_14"
        assert result.success is True
        assert "atr_14" in result.data.columns

    def test_custom_window(self, sample_data):
        """测试自定义窗口"""
        factor = ATRFactor(window=20)
        result = factor.calculate(sample_data)

        assert result.factor_name == "atr_20"


class TestRealizedVolatilityFactor:
    """测试已实现波动率因子"""

    def test_calculate(self, sample_data):
        """测试计算"""
        factor = RealizedVolatilityFactor()
        result = factor.calculate(sample_data)

        assert "realized_vol_20d" in result.data.columns
        assert result.success is True


class TestTurnoverRateFactor:
    """测试换手率因子"""

    def test_calculate_with_turnover(self, sample_data):
        """测试使用 turnover 列"""
        factor = TurnoverRateFactor()
        result = factor.calculate(sample_data)

        assert result.factor_name == "turnover_rate"
        assert result.success is True
        assert "turnover_rate" in result.data.columns

    def test_missing_columns(self):
        """测试缺失列"""
        factor = TurnoverRateFactor()
        data = pd.DataFrame({"close": [10.0, 11.0]})
        result = factor.calculate(data)

        assert result.success is False


class TestAmihudFactor:
    """测试 Amihud 因子"""

    def test_calculate(self, sample_data):
        """测试计算"""
        factor = AmihudFactor()
        result = factor.calculate(sample_data)

        assert "amihud_20d" in result.data.columns
        assert result.success is True


class TestVolumeMomentumFactor:
    """测试成交量动量因子"""

    def test_calculate(self, sample_data):
        """测试计算"""
        factor = VolumeMomentumFactor()
        result = factor.calculate(sample_data)

        assert "volume_momentum_20d" in result.data.columns
        assert result.success is True


class TestRSIFactor:
    """测试 RSI 因子"""

    def test_calculate(self, sample_data):
        """测试计算"""
        factor = RSIFactor()
        result = factor.calculate(sample_data)

        assert "rsi_14" in result.data.columns
        assert result.success is True

    def test_rsi_range(self, sample_data):
        """测试 RSI 范围在 0-100"""
        factor = RSIFactor()
        result = factor.calculate(sample_data)

        valid_values = result.data["rsi_14"].dropna()
        assert (valid_values >= 0).all()
        assert (valid_values <= 100).all()


class TestMACDFactor:
    """测试 MACD 因子"""

    def test_calculate(self, sample_data):
        """测试计算"""
        factor = MACDFactor()
        result = factor.calculate(sample_data)

        assert result.factor_name == "macd"
        assert result.success is True
        assert "macd_dif" in result.data.columns
        assert "macd_dea" in result.data.columns
        assert "macd_hist" in result.data.columns

    def test_custom_params(self, sample_data):
        """测试自定义参数"""
        factor = MACDFactor(fast_period=12, slow_period=26, signal_period=9)
        result = factor.calculate(sample_data, params={"fast_period": 10})

        assert result.success is True


class TestBollingerBandsFactor:
    """测试布林带因子"""

    def test_calculate(self, sample_data):
        """测试计算"""
        factor = BollingerBandsFactor()
        result = factor.calculate(sample_data)

        assert result.factor_name == "bollinger_bands"
        assert result.success is True
        assert "bollinger_upper" in result.data.columns
        assert "bollinger_middle" in result.data.columns
        assert "bollinger_lower" in result.data.columns
        assert "bollinger_position" in result.data.columns

    def test_bands_order(self, sample_data):
        """测试布林带顺序"""
        factor = BollingerBandsFactor()
        result = factor.calculate(sample_data)

        # 上轨 > 中轨 > 下轨
        valid_data = result.data.dropna()
        assert (valid_data["bollinger_upper"] >= valid_data["bollinger_middle"]).all()
        assert (valid_data["bollinger_middle"] >= valid_data["bollinger_lower"]).all()


class TestKDJFactor:
    """测试 KDJ 因子"""

    def test_calculate(self, sample_data):
        """测试计算"""
        factor = KDJFactor()
        result = factor.calculate(sample_data)

        assert result.factor_name == "kdj"
        assert result.success is True
        assert "kdj_k" in result.data.columns
        assert "kdj_d" in result.data.columns
        assert "kdj_j" in result.data.columns

    def test_kdj_range(self, sample_data):
        """测试 KDJ 范围"""
        factor = KDJFactor()
        result = factor.calculate(sample_data)

        # K 和 D 值应该在 0-100 范围内
        valid_k = result.data["kdj_k"].dropna()
        valid_d = result.data["kdj_d"].dropna()
        assert (valid_k >= 0).all()
        assert (valid_k <= 100).all()
        assert (valid_d >= 0).all()
        assert (valid_d <= 100).all()
