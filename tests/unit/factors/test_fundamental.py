"""Test fundamental factors calculation."""

import numpy as np
import pandas as pd
import pytest

from aistock.factors.interface import FactorCategory, FactorFrequency
from aistock.factors.fundamental.value import (
    PEFactor, PBFactor, PSFactor, DividendYieldFactor, EarningsYieldFactor,
)
from aistock.factors.fundamental.quality import (
    ROEFactor, GrossMarginFactor, DebtToEquityFactor,
    CurrentRatioFactor, AssetTurnoverFactor,
)
from aistock.factors.fundamental.growth import (
    RevenueGrowthFactor, NetProfitGrowthFactor, EPSGrowthFactor,
    BookValueGrowthFactor, OperatingCashFlowGrowthFactor,
)


@pytest.fixture
def sample_fundamental_data():
    """创建基本面测试数据"""
    np.random.seed(42)
    n = 4  # 4 个季度

    df = pd.DataFrame({
        "trade_date": pd.date_range("2025-01-01", periods=n, freq="QE"),
        "close": [10.0, 11.0, 12.0, 13.0],
        "eps": [0.5, 0.6, 0.7, 0.8],
        "bps": [5.0, 5.5, 6.0, 6.5],
        "dividend": [0.2, 0.25, 0.3, 0.35],
        "market_cap": [1000000, 1100000, 1200000, 1300000],
        "revenue": [500000, 550000, 600000, 650000],
        "cost_of_goods_sold": [300000, 330000, 360000, 390000],
        "net_profit": [100000, 110000, 120000, 130000],
        "shareholders_equity": [500000, 550000, 600000, 650000],
        "total_liabilities": [300000, 330000, 360000, 390000],
        "current_assets": [400000, 440000, 480000, 520000],
        "current_liabilities": [200000, 220000, 240000, 260000],
        "total_assets": [800000, 880000, 960000, 1040000],
        "operating_cash_flow": [80000, 88000, 96000, 104000],
    })
    df.set_index("trade_date", inplace=True)
    return df


class TestPEFactor:
    """测试 PE 因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = PEFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "pe"
        assert result.success is True
        assert "pe" in result.data.columns

    def test_pe_calculation(self, sample_fundamental_data):
        """测试 PE 计算"""
        factor = PEFactor()
        result = factor.calculate(sample_fundamental_data)

        # PE = close / eps
        expected_pe = sample_fundamental_data["close"] / sample_fundamental_data["eps"]
        pd.testing.assert_series_equal(result.data["pe"], expected_pe, check_names=False)


class TestPBFactor:
    """测试 PB 因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = PBFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "pb"
        assert result.success is True
        assert "pb" in result.data.columns

    def test_pb_calculation(self, sample_fundamental_data):
        """测试 PB 计算"""
        factor = PBFactor()
        result = factor.calculate(sample_fundamental_data)

        # PB = close / bps
        expected_pb = sample_fundamental_data["close"] / sample_fundamental_data["bps"]
        pd.testing.assert_series_equal(result.data["pb"], expected_pb, check_names=False)


class TestPSFactor:
    """测试 PS 因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = PSFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "ps"
        assert result.success is True
        assert "ps" in result.data.columns


class TestDividendYieldFactor:
    """测试股息率因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = DividendYieldFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "dividend_yield"
        assert result.success is True
        assert "dividend_yield" in result.data.columns


class TestEarningsYieldFactor:
    """测试盈利收益率因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = EarningsYieldFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "earnings_yield"
        assert result.success is True
        assert "earnings_yield" in result.data.columns


class TestROEFactor:
    """测试 ROE 因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = ROEFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "roe"
        assert result.success is True
        assert "roe" in result.data.columns

    def test_roe_calculation(self, sample_fundamental_data):
        """测试 ROE 计算"""
        factor = ROEFactor()
        result = factor.calculate(sample_fundamental_data)

        # ROE = net_profit / shareholders_equity
        expected_roe = (
            sample_fundamental_data["net_profit"] /
            sample_fundamental_data["shareholders_equity"]
        )
        pd.testing.assert_series_equal(result.data["roe"], expected_roe, check_names=False)


class TestGrossMarginFactor:
    """测试毛利率因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = GrossMarginFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "gross_margin"
        assert result.success is True
        assert "gross_margin" in result.data.columns


class TestDebtToEquityFactor:
    """测试资产负债率因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = DebtToEquityFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "debt_to_equity"
        assert result.success is True
        assert "debt_to_equity" in result.data.columns


class TestCurrentRatioFactor:
    """测试流动比率因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = CurrentRatioFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "current_ratio"
        assert result.success is True
        assert "current_ratio" in result.data.columns


class TestAssetTurnoverFactor:
    """测试资产周转率因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = AssetTurnoverFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "asset_turnover"
        assert result.success is True
        assert "asset_turnover" in result.data.columns


class TestRevenueGrowthFactor:
    """测试营收增长率因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = RevenueGrowthFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "revenue_growth"
        assert result.success is True
        assert "revenue_growth" in result.data.columns


class TestNetProfitGrowthFactor:
    """测试利润增长率因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = NetProfitGrowthFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "net_profit_growth"
        assert result.success is True
        assert "net_profit_growth" in result.data.columns


class TestEPSGrowthFactor:
    """测试每股收益增长率因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = EPSGrowthFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "eps_growth"
        assert result.success is True
        assert "eps_growth" in result.data.columns


class TestBookValueGrowthFactor:
    """测试净资产增长率因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = BookValueGrowthFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "book_value_growth"
        assert result.success is True
        assert "book_value_growth" in result.data.columns


class TestOperatingCashFlowGrowthFactor:
    """测试经营现金流增长率因子"""

    def test_calculate(self, sample_fundamental_data):
        """测试计算"""
        factor = OperatingCashFlowGrowthFactor()
        result = factor.calculate(sample_fundamental_data)

        assert result.factor_name == "operating_cash_flow_growth"
        assert result.success is True
        assert "operating_cash_flow_growth" in result.data.columns
