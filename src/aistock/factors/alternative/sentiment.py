"""Market sentiment factors calculation."""

import numpy as np
import pandas as pd
import time

from aistock.factors.interface import (
    FactorCalculator, FactorMetadata, FactorResult,
    FactorCategory, FactorFrequency,
)


class LimitUpCountFactor(FactorCalculator):
    """涨停板数量因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="limit_up_count",
            description="涨停板数量因子，当日涨停股票数量",
            category=FactorCategory.ALTERNATIVE,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["sentiment", "limit_up", "market"],
            data_requirements=["pct_change"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算涨停板数量因子"""
        start_time = time.time()

        if "pct_change" not in data.columns:
            return FactorResult(
                factor_name="limit_up_count",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'pct_change' column",
            )

        # 计算涨停板数量（涨幅 >= 10%）
        # 注意：这里假设 pct_change 是百分比形式
        limit_up = (data["pct_change"] >= 10).sum()

        result_data = pd.DataFrame({
            "limit_up_count": [limit_up] * len(data),
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="limit_up_count",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class LimitDownCountFactor(FactorCalculator):
    """跌停板数量因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="limit_down_count",
            description="跌停板数量因子，当日跌停股票数量",
            category=FactorCategory.ALTERNATIVE,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["sentiment", "limit_down", "market"],
            data_requirements=["pct_change"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算跌停板数量因子"""
        start_time = time.time()

        if "pct_change" not in data.columns:
            return FactorResult(
                factor_name="limit_down_count",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'pct_change' column",
            )

        # 计算跌停板数量（跌幅 <= -10%）
        limit_down = (data["pct_change"] <= -10).sum()

        result_data = pd.DataFrame({
            "limit_down_count": [limit_down] * len(data),
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="limit_down_count",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class AdvanceDeclineRatioFactor(FactorCalculator):
    """涨跌比因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="advance_decline_ratio",
            description="涨跌比因子，上涨股票数与下跌股票数的比率",
            category=FactorCategory.ALTERNATIVE,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["sentiment", "breadth", "market"],
            data_requirements=["pct_change"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算涨跌比因子"""
        start_time = time.time()

        if "pct_change" not in data.columns:
            return FactorResult(
                factor_name="advance_decline_ratio",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'pct_change' column",
            )

        # 计算上涨和下跌股票数
        advance = (data["pct_change"] > 0).sum()
        decline = (data["pct_change"] < 0).sum()

        # 计算涨跌比（避免除零）
        if decline > 0:
            ratio = advance / decline
        else:
            ratio = float("inf") if advance > 0 else 1.0

        result_data = pd.DataFrame({
            "advance_decline_ratio": [ratio] * len(data),
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="advance_decline_ratio",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class MarketBreadthFactor(FactorCalculator):
    """市场广度因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="market_breadth",
            description="市场广度因子，上涨股票数占总股票数的比例",
            category=FactorCategory.ALTERNATIVE,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["sentiment", "breadth", "market"],
            data_requirements=["pct_change"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算市场广度因子"""
        start_time = time.time()

        if "pct_change" not in data.columns:
            return FactorResult(
                factor_name="market_breadth",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'pct_change' column",
            )

        # 计算上涨股票数
        advance = (data["pct_change"] > 0).sum()
        total = len(data)

        # 计算市场广度
        breadth = advance / total if total > 0 else 0.5

        result_data = pd.DataFrame({
            "market_breadth": [breadth] * len(data),
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="market_breadth",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class VolatilityIndexFactor(FactorCalculator):
    """波动率指数因子"""

    def __init__(self, window: int = 20):
        """
        初始化波动率指数因子。

        Args:
            window: 计算窗口
        """
        self.window = window

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name=f"volatility_index_{self.window}d",
            description=f"{self.window}日波动率指数，市场波动率的标准化指标",
            category=FactorCategory.ALTERNATIVE,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["sentiment", "volatility", "index"],
            data_requirements=["close"],
            parameters={"window": self.window},
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算波动率指数因子"""
        start_time = time.time()

        if "close" not in data.columns:
            return FactorResult(
                factor_name=f"volatility_index_{self.window}d",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'close' column",
            )

        # 使用参数覆盖默认窗口
        window = params.get("window", self.window) if params else self.window

        # 计算日收益率
        returns = data["close"].pct_change()

        # 计算滚动波动率
        volatility = returns.rolling(window=window).std() * np.sqrt(252)

        # 标准化波动率指数（简化版本）
        vol_mean = volatility.mean()
        vol_std = volatility.std()
        if vol_std > 0:
            vol_index = (volatility - vol_mean) / vol_std
        else:
            vol_index = pd.Series(0, index=volatility.index)

        result_data = pd.DataFrame({
            f"volatility_index_{window}d": vol_index,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name=f"volatility_index_{window}d",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )
