"""Liquidity factors calculation."""

import numpy as np
import pandas as pd
import time

from aistock.factors.interface import (
    FactorCalculator, FactorMetadata, FactorResult,
    FactorCategory, FactorFrequency,
)


class TurnoverRateFactor(FactorCalculator):
    """换手率因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="turnover_rate",
            description="换手率因子，计算成交量与流通股本的比率",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["liquidity", "turnover"],
            data_requirements=["volume", "turnover"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算换手率"""
        start_time = time.time()

        # 如果已有 turnover 列，直接使用
        if "turnover" in data.columns:
            result_data = pd.DataFrame({
                "turnover_rate": data["turnover"],
            }, index=data.index)
        elif "volume" in data.columns and "float_shares" in data.columns:
            # 使用成交量和流通股本计算
            turnover_rate = data["volume"] / data["float_shares"]
            result_data = pd.DataFrame({
                "turnover_rate": turnover_rate,
            }, index=data.index)
        else:
            return FactorResult(
                factor_name="turnover_rate",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'turnover' or 'volume'/'float_shares' columns",
            )

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="turnover_rate",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class AmihudFactor(FactorCalculator):
    """Amihud 流动性因子"""

    def __init__(self, window: int = 20):
        """
        初始化 Amihud 因子。

        Args:
            window: 计算窗口
        """
        self.window = window

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name=f"amihud_{self.window}d",
            description=f"{self.window}日 Amihud 流动性因子，|收益率|/成交额",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["liquidity", "amihud"],
            data_requirements=["close", "amount"],
            parameters={"window": self.window},
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算 Amihud 流动性因子"""
        start_time = time.time()

        required_cols = ["close", "amount"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name=f"amihud_{self.window}d",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 使用参数覆盖默认窗口
        window = params.get("window", self.window) if params else self.window

        # 计算日收益率的绝对值
        returns = data["close"].pct_change()
        abs_returns = np.abs(returns)

        # 计算 Amihud 因子 = |收益率| / 成交额
        # 避免除零
        amount = data["amount"].replace(0, np.nan)
        amihud = abs_returns / amount

        # 计算滚动平均
        amihud_avg = amihud.rolling(window=window).mean()

        result_data = pd.DataFrame({
            f"amihud_{window}d": amihud_avg,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name=f"amihud_{window}d",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class VolumeMomentumFactor(FactorCalculator):
    """成交量动量因子"""

    def __init__(self, window: int = 20):
        """
        初始化成交量动量因子。

        Args:
            window: 计算窗口
        """
        self.window = window

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name=f"volume_momentum_{self.window}d",
            description=f"{self.window}日成交量动量，当前成交量与历史平均的比值",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["liquidity", "volume", "momentum"],
            data_requirements=["volume"],
            parameters={"window": self.window},
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算成交量动量"""
        start_time = time.time()

        if "volume" not in data.columns:
            return FactorResult(
                factor_name=f"volume_momentum_{self.window}d",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'volume' column",
            )

        # 使用参数覆盖默认窗口
        window = params.get("window", self.window) if params else self.window

        # 计算成交量动量 = 当前成交量 / 历史平均成交量
        volume_avg = data["volume"].rolling(window=window).mean()
        volume_momentum = data["volume"] / volume_avg

        result_data = pd.DataFrame({
            f"volume_momentum_{window}d": volume_momentum,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name=f"volume_momentum_{window}d",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )
