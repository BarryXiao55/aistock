"""Volatility factors calculation."""

import numpy as np
import pandas as pd
import time

from aistock.factors.interface import (
    FactorCalculator, FactorMetadata, FactorResult,
    FactorCategory, FactorFrequency,
)


class Volatility20DFactor(FactorCalculator):
    """20日波动率因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="volatility_20d",
            description="20日历史波动率因子，年化标准差",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["volatility", "risk"],
            data_requirements=["close"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算20日波动率"""
        start_time = time.time()

        if "close" not in data.columns:
            return FactorResult(
                factor_name="volatility_20d",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'close' column",
            )

        # 计算日收益率
        returns = data["close"].pct_change()

        # 计算20日滚动标准差并年化
        volatility = returns.rolling(window=20).std() * np.sqrt(252)

        result_data = pd.DataFrame({
            "volatility_20d": volatility,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="volatility_20d",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class ATRFactor(FactorCalculator):
    """ATR (Average True Range) 因子"""

    def __init__(self, window: int = 14):
        """
        初始化 ATR 因子。

        Args:
            window: ATR 计算窗口
        """
        self.window = window

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name=f"atr_{self.window}",
            description=f"{self.window}日平均真实波幅 (ATR)",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["volatility", "risk", "atr"],
            data_requirements=["high", "low", "close"],
            parameters={"window": self.window},
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算 ATR"""
        start_time = time.time()

        required_cols = ["high", "low", "close"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name=f"atr_{self.window}",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 使用参数覆盖默认窗口
        window = params.get("window", self.window) if params else self.window

        # 计算 True Range
        high_low = data["high"] - data["low"]
        high_close = np.abs(data["high"] - data["close"].shift(1))
        low_close = np.abs(data["low"] - data["close"].shift(1))

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # 计算 ATR
        atr = true_range.rolling(window=window).mean()

        result_data = pd.DataFrame({
            f"atr_{window}": atr,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name=f"atr_{window}",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class RealizedVolatilityFactor(FactorCalculator):
    """已实现波动率因子"""

    def __init__(self, window: int = 20):
        """
        初始化已实现波动率因子。

        Args:
            window: 计算窗口
        """
        self.window = window

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name=f"realized_vol_{self.window}d",
            description=f"{self.window}日已实现波动率",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["volatility", "risk", "realized"],
            data_requirements=["close"],
            parameters={"window": self.window},
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算已实现波动率"""
        start_time = time.time()

        if "close" not in data.columns:
            return FactorResult(
                factor_name=f"realized_vol_{self.window}d",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'close' column",
            )

        # 使用参数覆盖默认窗口
        window = params.get("window", self.window) if params else self.window

        # 计算对数收益率
        log_returns = np.log(data["close"] / data["close"].shift(1))

        # 计算已实现波动率
        realized_vol = log_returns.rolling(window=window).std() * np.sqrt(252)

        result_data = pd.DataFrame({
            f"realized_vol_{window}d": realized_vol,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name=f"realized_vol_{window}d",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )
