"""Fund flow factors calculation."""

import numpy as np
import pandas as pd

from aistock.factors.interface import (
    FactorCalculator, FactorMetadata, FactorResult,
    FactorCategory, FactorFrequency,
)


class NorthFlowNetFactor(FactorCalculator):
    """北向资金净流入因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="north_flow_net",
            description="北向资金净流入因子，买入额与卖出额的差值",
            category=FactorCategory.ALTERNATIVE,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["fund_flow", "northbound", "qfii"],
            data_requirements=["buy_amount", "sell_amount"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算北向资金净流入因子"""
        import time
        start_time = time.time()

        required_cols = ["buy_amount", "sell_amount"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name="north_flow_net",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 计算净流入 = 买入额 - 卖出额
        net_flow = data["buy_amount"] - data["sell_amount"]

        result_data = pd.DataFrame({
            "north_flow_net": net_flow,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="north_flow_net",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class NorthFlowMomentumFactor(FactorCalculator):
    """北向资金动量因子"""

    def __init__(self, window: int = 5):
        """
        初始化北向资金动量因子。

        Args:
            window: 计算窗口
        """
        self.window = window

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name=f"north_flow_momentum_{self.window}d",
            description=f"{self.window}日北向资金动量，当前净流入与历史平均的比值",
            category=FactorCategory.ALTERNATIVE,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["fund_flow", "northbound", "momentum"],
            data_requirements=["buy_amount", "sell_amount"],
            parameters={"window": self.window},
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算北向资金动量因子"""
        import time
        start_time = time.time()

        required_cols = ["buy_amount", "sell_amount"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name=f"north_flow_momentum_{self.window}d",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 使用参数覆盖默认窗口
        window = params.get("window", self.window) if params else self.window

        # 计算净流入
        net_flow = data["buy_amount"] - data["sell_amount"]

        # 计算动量 = 当前净流入 / 历史平均净流入
        net_flow_avg = net_flow.rolling(window=window).mean()
        momentum = net_flow / net_flow_avg

        result_data = pd.DataFrame({
            f"north_flow_momentum_{window}d": momentum,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name=f"north_flow_momentum_{window}d",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class MarginBalanceChangeFactor(FactorCalculator):
    """融资余额变化因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="margin_balance_change",
            description="融资余额变化因子，当日融资余额与前一日的差值",
            category=FactorCategory.ALTERNATIVE,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["fund_flow", "margin", "leverage"],
            data_requirements=["margin_balance"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算融资余额变化因子"""
        import time
        start_time = time.time()

        if "margin_balance" not in data.columns:
            return FactorResult(
                factor_name="margin_balance_change",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'margin_balance' column",
            )

        # 计算融资余额变化 = 当日余额 - 前一日余额
        margin_change = data["margin_balance"].diff()

        result_data = pd.DataFrame({
            "margin_balance_change": margin_change,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="margin_balance_change",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class MarginRatioFactor(FactorCalculator):
    """融资融券比率因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="margin_ratio",
            description="融资融券比率因子，融资余额与融券余量的比率",
            category=FactorCategory.ALTERNATIVE,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["fund_flow", "margin", "ratio"],
            data_requirements=["margin_balance", "short_balance"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算融资融券比率因子"""
        import time
        start_time = time.time()

        required_cols = ["margin_balance", "short_balance"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name="margin_ratio",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 计算融资融券比率 = 融资余额 / 融券余量
        # 避免除零
        short_balance = data["short_balance"].replace(0, np.nan)
        margin_ratio = data["margin_balance"] / short_balance

        result_data = pd.DataFrame({
            "margin_ratio": margin_ratio,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="margin_ratio",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )
