"""Growth factors calculation."""

import numpy as np
import pandas as pd
import time

from aistock.factors.interface import (
    FactorCalculator, FactorMetadata, FactorResult,
    FactorCategory, FactorFrequency,
)


class RevenueGrowthFactor(FactorCalculator):
    """营收增长率因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="revenue_growth",
            description="营收增长率因子，营业收入的同比增长率",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["growth", "revenue"],
            data_requirements=["revenue"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算营收增长率因子"""
        start_time = time.time()

        if "revenue" not in data.columns:
            return FactorResult(
                factor_name="revenue_growth",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'revenue' column",
            )

        # 计算营收增长率 = (本期营收 - 上期营收) / 上期营收
        # 假设数据按时间排序，shift(1) 得到上期数据
        revenue = data["revenue"]
        revenue_prev = revenue.shift(1)

        # 避免除零
        revenue_prev = revenue_prev.replace(0, np.nan)
        revenue_growth = (revenue - revenue_prev) / revenue_prev

        result_data = pd.DataFrame({
            "revenue_growth": revenue_growth,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="revenue_growth",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class NetProfitGrowthFactor(FactorCalculator):
    """利润增长率因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="net_profit_growth",
            description="利润增长率因子，净利润的同比增长率",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["growth", "profitability"],
            data_requirements=["net_profit"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算利润增长率因子"""
        start_time = time.time()

        if "net_profit" not in data.columns:
            return FactorResult(
                factor_name="net_profit_growth",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'net_profit' column",
            )

        # 计算利润增长率 = (本期净利润 - 上期净利润) / 上期净利润
        net_profit = data["net_profit"]
        net_profit_prev = net_profit.shift(1)

        # 避免除零
        net_profit_prev = net_profit_prev.replace(0, np.nan)
        net_profit_growth = (net_profit - net_profit_prev) / net_profit_prev

        result_data = pd.DataFrame({
            "net_profit_growth": net_profit_growth,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="net_profit_growth",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class EPSGrowthFactor(FactorCalculator):
    """每股收益增长率因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="eps_growth",
            description="每股收益增长率因子，EPS 的同比增长率",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["growth", "earnings"],
            data_requirements=["eps"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算每股收益增长率因子"""
        start_time = time.time()

        if "eps" not in data.columns:
            return FactorResult(
                factor_name="eps_growth",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'eps' column",
            )

        # 计算 EPS 增长率 = (本期 EPS - 上期 EPS) / 上期 EPS
        eps = data["eps"]
        eps_prev = eps.shift(1)

        # 避免除零
        eps_prev = eps_prev.replace(0, np.nan)
        eps_growth = (eps - eps_prev) / eps_prev

        result_data = pd.DataFrame({
            "eps_growth": eps_growth,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="eps_growth",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class BookValueGrowthFactor(FactorCalculator):
    """净资产增长率因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="book_value_growth",
            description="净资产增长率因子，股东权益的同比增长率",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["growth", "equity"],
            data_requirements=["shareholders_equity"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算净资产增长率因子"""
        start_time = time.time()

        if "shareholders_equity" not in data.columns:
            return FactorResult(
                factor_name="book_value_growth",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'shareholders_equity' column",
            )

        # 计算净资产增长率 = (本期股东权益 - 上期股东权益) / 上期股东权益
        equity = data["shareholders_equity"]
        equity_prev = equity.shift(1)

        # 避免除零
        equity_prev = equity_prev.replace(0, np.nan)
        book_value_growth = (equity - equity_prev) / equity_prev

        result_data = pd.DataFrame({
            "book_value_growth": book_value_growth,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="book_value_growth",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class OperatingCashFlowGrowthFactor(FactorCalculator):
    """经营现金流增长率因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="operating_cash_flow_growth",
            description="经营现金流增长率因子，经营活动现金流的同比增长率",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["growth", "cash_flow"],
            data_requirements=["operating_cash_flow"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算经营现金流增长率因子"""
        start_time = time.time()

        if "operating_cash_flow" not in data.columns:
            return FactorResult(
                factor_name="operating_cash_flow_growth",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'operating_cash_flow' column",
            )

        # 计算经营现金流增长率
        ocf = data["operating_cash_flow"]
        ocf_prev = ocf.shift(1)

        # 避免除零
        ocf_prev = ocf_prev.replace(0, np.nan)
        ocf_growth = (ocf - ocf_prev) / ocf_prev

        result_data = pd.DataFrame({
            "operating_cash_flow_growth": ocf_growth,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="operating_cash_flow_growth",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )
