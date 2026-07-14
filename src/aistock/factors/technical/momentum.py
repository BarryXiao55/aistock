"""Momentum factors calculation."""

import numpy as np
import pandas as pd

from aistock.factors.interface import (
    FactorCalculator, FactorMetadata, FactorResult,
    FactorCategory, FactorFrequency,
)


class Momentum5DFactor(FactorCalculator):
    """5日动量因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="momentum_5d",
            description="5日动量因子，计算近5个交易日的价格变化率",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["momentum", "trend"],
            data_requirements=["close"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算5日动量"""
        import time
        start_time = time.time()

        if "close" not in data.columns:
            return FactorResult(
                factor_name="momentum_5d",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'close' column",
            )

        # 计算5日动量
        momentum = data["close"] / data["close"].shift(5) - 1

        result_data = pd.DataFrame({
            "momentum_5d": momentum,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="momentum_5d",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class Momentum20DFactor(FactorCalculator):
    """20日动量因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="momentum_20d",
            description="20日动量因子，计算近20个交易日的价格变化率",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["momentum", "trend"],
            data_requirements=["close"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算20日动量"""
        import time
        start_time = time.time()

        if "close" not in data.columns:
            return FactorResult(
                factor_name="momentum_20d",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'close' column",
            )

        # 计算20日动量
        momentum = data["close"] / data["close"].shift(20) - 1

        result_data = pd.DataFrame({
            "momentum_20d": momentum,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="momentum_20d",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class Momentum60DFactor(FactorCalculator):
    """60日动量因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="momentum_60d",
            description="60日动量因子，计算近60个交易日的价格变化率",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["momentum", "trend"],
            data_requirements=["close"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算60日动量"""
        import time
        start_time = time.time()

        if "close" not in data.columns:
            return FactorResult(
                factor_name="momentum_60d",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'close' column",
            )

        # 计算60日动量
        momentum = data["close"] / data["close"].shift(60) - 1

        result_data = pd.DataFrame({
            "momentum_60d": momentum,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="momentum_60d",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class MomentumCustomFactor(FactorCalculator):
    """自定义动量因子"""

    def __init__(self, window: int = 20):
        """
        初始化自定义动量因子。

        Args:
            window: 动量计算窗口（交易日数）
        """
        self.window = window

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name=f"momentum_{self.window}d",
            description=f"{self.window}日动量因子，计算近{self.window}个交易日的价格变化率",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["momentum", "trend", "custom"],
            data_requirements=["close"],
            parameters={"window": self.window},
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算自定义动量"""
        import time
        start_time = time.time()

        # 使用参数覆盖默认窗口
        window = params.get("window", self.window) if params else self.window

        if "close" not in data.columns:
            return FactorResult(
                factor_name=f"momentum_{window}d",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'close' column",
            )

        # 计算动量
        momentum = data["close"] / data["close"].shift(window) - 1

        result_data = pd.DataFrame({
            f"momentum_{window}d": momentum,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name=f"momentum_{window}d",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )
