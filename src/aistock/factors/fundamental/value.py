"""Value factors calculation."""

import numpy as np
import pandas as pd
import time

from aistock.factors.interface import (
    FactorCalculator, FactorMetadata, FactorResult,
    FactorCategory, FactorFrequency,
)


class PEFactor(FactorCalculator):
    """PE (Price-to-Earnings) 因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="pe",
            description="市盈率因子，股价与每股收益的比率",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["value", "valuation", "pe"],
            data_requirements=["close", "eps"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算 PE 因子"""
        start_time = time.time()

        required_cols = ["close", "eps"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name="pe",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 计算 PE = 股价 / 每股收益
        # 避免除零
        eps = data["eps"].replace(0, np.nan)
        pe = data["close"] / eps

        result_data = pd.DataFrame({
            "pe": pe,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="pe",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class PBFactor(FactorCalculator):
    """PB (Price-to-Book) 因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="pb",
            description="市净率因子，股价与每股净资产的比率",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["value", "valuation", "pb"],
            data_requirements=["close", "bps"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算 PB 因子"""
        start_time = time.time()

        required_cols = ["close", "bps"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name="pb",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 计算 PB = 股价 / 每股净资产
        # 避免除零
        bps = data["bps"].replace(0, np.nan)
        pb = data["close"] / bps

        result_data = pd.DataFrame({
            "pb": pb,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="pb",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class PSFactor(FactorCalculator):
    """PS (Price-to-Sales) 因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="ps",
            description="市销率因子，市值与营业收入的比率",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["value", "valuation", "ps"],
            data_requirements=["market_cap", "revenue"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算 PS 因子"""
        start_time = time.time()

        required_cols = ["market_cap", "revenue"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name="ps",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 计算 PS = 市值 / 营业收入
        # 避免除零
        revenue = data["revenue"].replace(0, np.nan)
        ps = data["market_cap"] / revenue

        result_data = pd.DataFrame({
            "ps": ps,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="ps",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class DividendYieldFactor(FactorCalculator):
    """股息率因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="dividend_yield",
            description="股息率因子，每股股息与股价的比率",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["value", "income", "dividend"],
            data_requirements=["dividend", "close"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算股息率因子"""
        start_time = time.time()

        required_cols = ["dividend", "close"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name="dividend_yield",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 计算股息率 = 每股股息 / 股价
        # 避免除零
        close = data["close"].replace(0, np.nan)
        dividend_yield = data["dividend"] / close

        result_data = pd.DataFrame({
            "dividend_yield": dividend_yield,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="dividend_yield",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class EarningsYieldFactor(FactorCalculator):
    """盈利收益率因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="earnings_yield",
            description="盈利收益率因子，每股收益与股价的比率（PE 的倒数）",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["value", "valuation", "earnings_yield"],
            data_requirements=["eps", "close"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算盈利收益率因子"""
        start_time = time.time()

        required_cols = ["eps", "close"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name="earnings_yield",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 计算盈利收益率 = 每股收益 / 股价
        # 避免除零
        close = data["close"].replace(0, np.nan)
        earnings_yield = data["eps"] / close

        result_data = pd.DataFrame({
            "earnings_yield": earnings_yield,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="earnings_yield",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )
