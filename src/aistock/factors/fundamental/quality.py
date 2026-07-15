"""Quality factors calculation."""

import numpy as np
import pandas as pd
import time

from aistock.factors.interface import (
    FactorCalculator, FactorMetadata, FactorResult,
    FactorCategory, FactorFrequency,
)


class ROEFactor(FactorCalculator):
    """ROE (Return on Equity) 因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="roe",
            description="净资产收益率因子，净利润与股东权益的比率",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["quality", "profitability", "roe"],
            data_requirements=["net_profit", "shareholders_equity"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算 ROE 因子"""
        start_time = time.time()

        required_cols = ["net_profit", "shareholders_equity"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name="roe",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 计算 ROE = 净利润 / 股东权益
        # 避免除零
        shareholders_equity = data["shareholders_equity"].replace(0, np.nan)
        roe = data["net_profit"] / shareholders_equity

        result_data = pd.DataFrame({
            "roe": roe,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="roe",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class GrossMarginFactor(FactorCalculator):
    """毛利率因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="gross_margin",
            description="毛利率因子，毛利润与营业收入的比率",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["quality", "profitability", "margin"],
            data_requirements=["revenue", "cost_of_goods_sold"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算毛利率因子"""
        start_time = time.time()

        required_cols = ["revenue", "cost_of_goods_sold"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name="gross_margin",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 计算毛利率 = (营业收入 - 营业成本) / 营业收入
        # 避免除零
        revenue = data["revenue"].replace(0, np.nan)
        gross_margin = (data["revenue"] - data["cost_of_goods_sold"]) / revenue

        result_data = pd.DataFrame({
            "gross_margin": gross_margin,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="gross_margin",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class DebtToEquityFactor(FactorCalculator):
    """资产负债率因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="debt_to_equity",
            description="资产负债率因子，总负债与股东权益的比率",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["quality", "leverage", "debt"],
            data_requirements=["total_liabilities", "shareholders_equity"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算资产负债率因子"""
        start_time = time.time()

        required_cols = ["total_liabilities", "shareholders_equity"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name="debt_to_equity",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 计算资产负债率 = 总负债 / 股东权益
        # 避免除零
        shareholders_equity = data["shareholders_equity"].replace(0, np.nan)
        debt_to_equity = data["total_liabilities"] / shareholders_equity

        result_data = pd.DataFrame({
            "debt_to_equity": debt_to_equity,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="debt_to_equity",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class CurrentRatioFactor(FactorCalculator):
    """流动比率因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="current_ratio",
            description="流动比率因子，流动资产与流动负债的比率",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["quality", "liquidity", "current_ratio"],
            data_requirements=["current_assets", "current_liabilities"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算流动比率因子"""
        start_time = time.time()

        required_cols = ["current_assets", "current_liabilities"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name="current_ratio",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 计算流动比率 = 流动资产 / 流动负债
        # 避免除零
        current_liabilities = data["current_liabilities"].replace(0, np.nan)
        current_ratio = data["current_assets"] / current_liabilities

        result_data = pd.DataFrame({
            "current_ratio": current_ratio,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="current_ratio",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class AssetTurnoverFactor(FactorCalculator):
    """资产周转率因子"""

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="asset_turnover",
            description="资产周转率因子，营业收入与总资产的比率",
            category=FactorCategory.FUNDAMENTAL,
            frequency=FactorFrequency.QUARTERLY,
            version="1.0.0",
            tags=["quality", "efficiency", "turnover"],
            data_requirements=["revenue", "total_assets"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算资产周转率因子"""
        start_time = time.time()

        required_cols = ["revenue", "total_assets"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name="asset_turnover",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 计算资产周转率 = 营业收入 / 总资产
        # 避免除零
        total_assets = data["total_assets"].replace(0, np.nan)
        asset_turnover = data["revenue"] / total_assets

        result_data = pd.DataFrame({
            "asset_turnover": asset_turnover,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="asset_turnover",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )
